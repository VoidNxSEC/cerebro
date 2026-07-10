import json
import uuid
import time
from pathlib import Path
from typing import List, Dict

def transform_docs(input_dir: str = "docs/commands", output_file: str = "data/ingestion/docs_vertex.jsonl"):
    """
    ETL Pipeline:
    1. Extract: Lê arquivos Markdown gerados
    2. Transform: Converte para Schema do Vertex AI Search
    3. Load: Salva JSONL pronto para GCS/BigQuery
    """
    print(f"🏭 Iniciando ETL de Documentação...")
    
    in_path = Path(input_dir)
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not in_path.exists():
        print(f"❌ Diretório não encontrado: {input_dir}")
        return

    documents = []
    
    # Schema base para Vertex AI Search (Unstructured/Generic)
    for md_file in in_path.glob("*.md"):
        if md_file.name == "README.md" or md_file.name == "CONTRIBUTING_DOCS.md":
            continue
            
        content = md_file.read_text(encoding="utf-8")
        
        # Extração de Metadados básicos do conteúdo
        command_name = md_file.stem.replace("_", " ")
        
        # Estrutura do Documento Vertex AI
        doc = {
            "id": f"cmd-{md_file.stem}",
            "structData": {
                "title": f"Comando: {command_name}",
                "category": "cli_reference",
                "file_type": "markdown",
                "source": "self_documentation",
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "url": f"file://{md_file.absolute()}" # Placeholder, idealmente seria URL do GitHub
            },
            "content": {
                "mimeType": "text/plain",
                "uri": f"gs://placeholder-bucket/{md_file.name}" # Será atualizado no upload
            },
            # O conteúdo raw vai aqui para indexação textual direta se usarmos 'jsonData' mode
            # Mas para 'structData' + 'content', o Vertex indexa o arquivo referenciado ou o campo content.
            # Vamos usar um formato híbrido robusto: JSONL com 'jsonData' contendo o texto para indexação inline.
            "jsonData": json.dumps({
                "title": f"CLI Reference: {command_name}",
                "content": content,
                "type": "documentation",
                "tags": ["cli", "reference", "auto-generated"]
            })
        }
        documents.append(doc)

    # Validation & Load
    print(f"🔍 Validando {len(documents)} documentos...")
    
    with open(out_path, "w", encoding="utf-8") as f:
        for doc in documents:
            # Vertex AI requer JSONL com campos específicos
            # Para importação flexível, usamos apenas id e jsonData (inline content)
            entry = {
                "id": doc["id"],
                "jsonData": doc["jsonData"]
            }
            f.write(json.dumps(entry) + "\n")
            
    print(f"✅ ETL Completo! Arquivo gerado: {out_path}")
    print(f"📦 Tamanho: {out_path.stat().st_size / 1024:.2f} KB")

if __name__ == "__main__":
    transform_docs()
