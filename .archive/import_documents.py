#!/usr/bin/env python3
"""
Importa documentos locais para o Data Store do Vertex AI Search.
Fluxo:
1. Cria/Usa um bucket GCS
2. Upload dos arquivos locais para o bucket
3. Trigger de ImportDocuments API do bucket para o Data Store
"""
import os
import sys
import glob
from google.cloud import storage
from google.cloud import discoveryengine_v1beta as discoveryengine
from google.api_core import exceptions
from google.auth import default

def get_config():
    _, project = default()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    data_store_id = os.getenv("DATA_STORE_ID")
    
    if not data_store_id:
        print("❌ DATA_STORE_ID não definido.")
        print("   export DATA_STORE_ID='seu-id'")
        sys.exit(1)
        
    return project, location, data_store_id

def upload_to_gcs(project_id, source_dir):
    """Sobe arquivos locais para um bucket GCS"""
    bucket_name = f"{project_id}-docs-staging"
    storage_client = storage.Client(project=project_id)
    
    # 1. Cria ou pega bucket
    try:
        bucket = storage_client.get_bucket(bucket_name)
        print(f"✅ Usando bucket existente: gs://{bucket_name}")
    except exceptions.NotFound:
        print(f"🔨 Criando bucket: gs://{bucket_name}...")
        bucket = storage_client.create_bucket(bucket_name, location="US") # US multi-region is cheap/easy
    
    # 2. Upload files
    files = glob.glob(os.path.join(source_dir, "*"))
    files = [f for f in files if os.path.isfile(f)]
    
    if not files:
        print(f"❌ Nenhum arquivo encontrado em {source_dir}")
        return None

    print(f"\n📤 Fazendo upload de {len(files)} arquivos...")
    gcs_uris = []
    
    for local_file in files:
        filename = os.path.basename(local_file)
        blob = bucket.blob(filename)
        print(f"   ⬆️  {filename}")
        blob.upload_from_filename(local_file)
        gcs_uris.append(f"gs://{bucket_name}/{filename}")
        
    return gcs_uris, bucket_name

def import_documents(project_id, location, data_store_id, gcs_uri_pattern):
    """Trigger import job"""
    print(f"\n🔄 Iniciando importação no Data Store '{data_store_id}'...")
    
    client_options = None
    if location != "global":
        client_options = {"api_endpoint": f"{location}-discoveryengine.googleapis.com"}
        
    client = discoveryengine.DocumentServiceClient(client_options=client_options)
    
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}/branches/default_branch"
    
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri_pattern],
            data_schema="content" # Tenta inferir o tipo (PDF, HTML, TXT)
        ),
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
    )

    try:
        operation = client.import_documents(request=request)
        print("  ⏳ Job de importação iniciado... (isso roda no server)")
        print(f"  🆔 Operation Name: {operation.operation.name}")
        
        # Esperar conclusão? Para demos sim, pra prod talvez não
        print("  ⏳ Aguardando conclusão...")
        response = operation.result(timeout=300) 
        
        print("\n✅ Importação concluída!")
        if response.error_samples:
             print(f"  ⚠️  Erros de amostra: {response.error_samples}")
        
        print(f"  📄 Documentos processados com sucesso.")
        
    except Exception as e:
        print(f"❌ Erro na importação: {e}")

def main():
    print("="*60)
    print("📥 IMPORTADOR DE DOCUMENTOS -> VERTEX AI SEARCH")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("Uso: python import_documents.py <diretorio_local_com_pdfs_ou_txts>")
        sys.exit(1)
        
    source_dir = sys.argv[1]
    if not os.path.isdir(source_dir):
        print(f"❌ Diretório não encontrado: {source_dir}")
        sys.exit(1)

    project, location, data_store_id = get_config()
    
    # 1. Upload
    res = upload_to_gcs(project, source_dir)
    if not res:
        sys.exit(1)
    _, bucket_name = res
    
    # 2. Import
    # Importa tudo que está no bucket (cuidado se o bucket for compartilhado, mas aqui criamos um dedicado)
    gcs_pattern = f"gs://{bucket_name}/*" 
    import_documents(project, location, data_store_id, gcs_pattern)
    
    print("\n🎉 Tudo pronto! Agora rode 'python test_credits.py' novamente.")

if __name__ == "__main__":
    main()
