# 🧠 PHANTOM Framework - Arquitetura Unificada

**Versão:** 2.0
**Data:** 2026-01-02
**Objetivo:** Migração de phoenix-cloud-run para arquitetura modular Phantom

---

## 📋 Visão Geral

O **Phantom Framework** é um framework unificado que combina:

1. **Knowledge Extraction & RAG** (ex-CEREBRO)
2. **GCP Credit Management** (ex-phoenix-cloud-run root)
3. **Multi-Cloud Integrations** (extensível)

### Princípios de Design

- **DRY**: Código duplicado consolidado em módulos core
- **Modularidade**: Componentes independentes e reutilizáveis
- **Extensibilidade**: Fácil adicionar novos módulos/integrações
- **Hermético**: Operações isoladas, testáveis
- **Nix-First**: Ambientes reproduzíveis e declarativos

---

## 🏗️ Nova Estrutura de Diretórios

```
phantom/                              # Root do framework (renomeado de cerebro/)
│
├── core/                            # Núcleo do framework
│   ├── __init__.py
│   │
│   ├── gcp/                        # Google Cloud Platform (UNIFICADO)
│   │   ├── __init__.py
│   │   ├── auth.py                # Autenticação e configuração
│   │   ├── billing.py             # BigQuery billing audit
│   │   ├── datastores.py          # Vertex AI Data Store management
│   │   ├── search.py              # Vertex AI Search / Grounded Generation
│   │   └── dialogflow.py          # Dialogflow CX sessions
│   │
│   ├── extraction/                # Code Knowledge Extraction
│   │   ├── __init__.py
│   │   ├── analyze_code.py       # AST/tree-sitter analysis
│   │   ├── generate_embeddings.py # Vector embeddings
│   │   └── ingest_data.py        # Import to vector DB
│   │
│   ├── rag/                       # RAG Server
│   │   ├── __init__.py
│   │   ├── server.py             # FastAPI server (local LLM)
│   │   ├── retrieval.py          # Vector similarity search
│   │   └── generation.py         # LLM generation with context
│   │
│   └── utils/                     # Utilities compartilhadas
│       ├── __init__.py
│       ├── config.py             # Configuration management
│       ├── logging.py            # Logging setup
│       └── state.py              # State persistence
│
├── modules/                       # Módulos de aplicação
│   │
│   ├── credit_burner/            # GCP Credit Burning Module
│   │   ├── __init__.py
│   │   ├── loadtest.py          # Parallel query load testing
│   │   ├── dialogflow_sessions.py # Dialogflow CX automation
│   │   └── audit.py             # Financial validation via BigQuery
│   │
│   ├── knowledge/                # Knowledge Base Module
│   │   ├── __init__.py
│   │   ├── import_docs.py       # Document import to datastores
│   │   └── query.py             # Knowledge base queries
│   │
│   └── nixos/                    # NixOS Integration Module (futuro)
│       ├── __init__.py
│       └── service.py           # Systemd service generator
│
├── config/                       # Configuration files
│   ├── repos.yaml               # Repository definitions for extraction
│   ├── settings.yaml            # Global settings
│   └── examples/                # Example configs
│       ├── repos.example.yaml
│       └── settings.example.yaml
│
├── scripts/                      # Utility scripts (legacy/standalone)
│   ├── setup/
│   │   ├── setup_bigquery_export.sh
│   │   └── setup_bigquery_simple.sh
│   ├── validation/
│   │   ├── check_billing_table.sh
│   │   └── validate_setup.py
│   └── migration/
│       └── migrate_from_phoenix.sh
│
├── docs/                         # Documentation
│   ├── README.md                # Main overview
│   ├── ARCHITECTURE.md          # This file
│   ├── GETTING_STARTED.md       # Quick start guide
│   ├── modules/
│   │   ├── CREDIT_BURNER.md     # Credit burner module docs
│   │   ├── KNOWLEDGE.md         # Knowledge extraction docs
│   │   └── RAG.md               # RAG server docs
│   └── api/
│       └── API_REFERENCE.md     # API documentation
│
├── tests/                        # Test suite
│   ├── core/
│   │   ├── test_gcp_auth.py
│   │   ├── test_datastores.py
│   │   └── test_search.py
│   ├── modules/
│   │   └── test_credit_burner.py
│   └── integration/
│       └── test_e2e.py
│
├── data/                         # Data directory (gitignored)
│   ├── knowledge_base/
│   ├── vector_db/
│   └── cache/
│
├── .archive/                     # Deprecated files (for reference)
│   ├── main.py                  # Old grounded generation attempt
│   ├── grounded_generation.py
│   └── test_grounded_v1.py
│
├── phantom.py                    # Main CLI entry point
├── flake.nix                     # Nix development environment
├── flake.lock
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Python project metadata
├── .gitignore
└── README.md                     # Project overview
```

---

## 🔄 Mapeamento de Migração

### Arquivos Duplicados → Consolidados

| Arquivo Original | Localização Nova | Módulo Core |
|-----------------|------------------|-------------|
| `manage_datastores.py` (root) | `core/gcp/datastores.py` | `phantom.core.gcp` |
| `manage_datastores.py` (cerebro) | *(removido)* | - |
| `test_credits.py` (root) | `modules/credit_burner/validate.py` | `phantom.modules.credit_burner` |
| `test_credits.py` (cerebro) | *(removido)* | - |
| `validate_credits.py` (root) | `core/gcp/auth.py` | `phantom.core.gcp` |
| `validate_credits.py` (cerebro) | *(removido)* | - |
| `cerebro/src/server.py` | `core/rag/server.py` | `phantom.core.rag` |
| `cerebro/bin/02_analyze_code.py` | `core/extraction/analyze_code.py` | `phantom.core.extraction` |
| `cerebro/bin/03_ingest_data.py` | `core/extraction/ingest_data.py` | `phantom.core.extraction` |
| `cerebro/bin/03_generate_embeddings.py` | `core/extraction/generate_embeddings.py` | `phantom.core.extraction` |

### Scripts de Aplicação → Módulos

| Script Original | Módulo Novo | Responsabilidade |
|----------------|-------------|------------------|
| `burn_credits_loadtest.py` | `modules/credit_burner/loadtest.py` | Parallel load testing |
| `burn_dialogflow_cx.py` | `modules/credit_burner/dialogflow_sessions.py` | Dialogflow automation |
| `audit_credits_bigquery.py` | `modules/credit_burner/audit.py` | BigQuery financial audit |
| `import_documents.py` | `modules/knowledge/import_docs.py` | Document import |
| `cerebro/real.py` | `modules/knowledge/query.py` | Grounded search queries |

### Arquivos Deprecados → Archive

| Arquivo | Motivo | Destino |
|---------|--------|---------|
| `main.py` | HTTP 501 error - API não funciona | `.archive/main.py` |
| `grounded_generation.py` | Mesmo problema | `.archive/grounded_generation.py` |
| `test_grounded_v1.py` | Diagnóstico - não mais necessário | `.archive/test_grounded_v1.py` |

---

## 🧩 Módulos Core

### 1. `phantom.core.gcp`

**Responsabilidade:** Abstração unificada para Google Cloud Platform APIs

**Componentes:**

```python
# core/gcp/auth.py
def get_credentials() -> Credentials
def get_project_id() -> str
def validate_setup() -> SetupStatus

# core/gcp/datastores.py
class DataStoreManager:
    def list() -> List[DataStore]
    def create(config: DataStoreConfig) -> DataStore
    def delete(data_store_id: str) -> None
    def get(data_store_id: str) -> DataStore

# core/gcp/search.py
class VertexAISearch:
    def search(query: str, **kwargs) -> SearchResponse
    def grounded_search(query: str, **kwargs) -> GroundedResponse

# core/gcp/billing.py
class BillingAuditor:
    def query_usage(start_date, end_date) -> UsageReport
    def validate_credits() -> CreditStatus
    def export_report(format: str) -> Path

# core/gcp/dialogflow.py
class DialogflowCXManager:
    def create_session() -> Session
    def detect_intent(session, query) -> Response
    def stream_conversation(session, queries) -> AsyncIterator[Response]
```

### 2. `phantom.core.extraction`

**Responsabilidade:** Code analysis e knowledge extraction

**Componentes:**

```python
# core/extraction/analyze_code.py
class CodeAnalyzer:
    def analyze_python(file_path: Path) -> List[Artifact]
    def analyze_nix(file_path: Path) -> List[Artifact]
    def analyze_repository(repo_path: Path) -> RepositoryKnowledge

# core/extraction/generate_embeddings.py
class EmbeddingGenerator:
    def generate(artifacts: List[Artifact]) -> List[Embedding]
    def store_to_chromadb(embeddings: List[Embedding]) -> None
    def store_to_vertex_ai(embeddings: List[Embedding]) -> None

# core/extraction/ingest_data.py
class DataIngester:
    def ingest_local_files(paths: List[Path]) -> None
    def ingest_from_git(repo_url: str) -> None
    def ingest_to_datastore(data_store_id: str, docs: List[Document]) -> None
```

### 3. `phantom.core.rag`

**Responsabilidade:** Retrieval-Augmented Generation server

**Componentes:**

```python
# core/rag/server.py
class PhantomRAGServer:
    def __init__(model_name: str, db_path: Path)
    def retrieve(query: str, top_k: int) -> List[Artifact]
    def generate(query: str, context: List[Artifact]) -> str

# FastAPI endpoints:
# - POST /query
# - GET /health
# - GET /stats

# core/rag/retrieval.py
class VectorRetriever:
    def similarity_search(query: str, top_k: int) -> List[Result]
    def hybrid_search(query: str, filters: Dict) -> List[Result]

# core/rag/generation.py
class LLMGenerator:
    def generate_with_context(query: str, context: str) -> str
    def stream_generate(query: str, context: str) -> AsyncIterator[str]
```

---

## 🎯 Módulos de Aplicação

### 1. `phantom.modules.credit_burner`

**Objetivo:** Consumir créditos GCP de forma auditável

**Interface CLI:**

```bash
# Validar setup
phantom credit-burner validate

# Load test com queries paralelas
phantom credit-burner loadtest --workers 10 --queries 1000

# Dialogflow CX sessions
phantom credit-burner dialogflow --sessions 100 --conversations 5

# Audit financeiro
phantom credit-burner audit --start-date 2025-12-01
```

### 2. `phantom.modules.knowledge`

**Objetivo:** Gerenciar knowledge base e document import

**Interface CLI:**

```bash
# Importar documentos
phantom knowledge import --source ./docs --datastore my-ds

# Query knowledge base
phantom knowledge query "Como configurar NixOS?"

# List datastores
phantom knowledge datastores list
```

---

## 🔌 CLI Principal: `phantom.py`

**Arquitetura:**

```python
#!/usr/bin/env python3
"""
PHANTOM Framework - Unified CLI
"""
import typer
from phantom.core import gcp, extraction, rag
from phantom.modules import credit_burner, knowledge

app = typer.Typer(name="phantom", help="PHANTOM Framework CLI")

# Subcommands
app.add_typer(credit_burner.cli.app, name="credit-burner")
app.add_typer(knowledge.cli.app, name="knowledge")
app.add_typer(gcp.cli.app, name="gcp")
app.add_typer(rag.cli.app, name="rag")

@app.command()
def init(project_type: str = "full"):
    """Initialize a new Phantom project"""
    # Setup directories, configs, etc.
    pass

@app.command()
def validate():
    """Validate entire Phantom setup"""
    # Check GCP auth, APIs, billing, etc.
    pass

if __name__ == "__main__":
    app()
```

**Uso:**

```bash
phantom --help
phantom validate
phantom gcp datastores list
phantom credit-burner loadtest --workers 5
phantom rag serve --model mistral-7b --port 8000
phantom knowledge query "What is RAG?"
```

---

## 🔧 Configuração Unificada

### `config/settings.yaml`

```yaml
project:
  name: phantom
  version: 2.0.0

gcp:
  project_id: gen-lang-client-0530325234
  location: global
  default_datastore: ds-app-v4-5e020c93

  billing:
    dataset: billing_export
    table: gcp_billing_export

  credits:
    genai_app_builder: 6432.54  # BRL
    dialogflow_cx: 3646.57      # BRL

rag:
  model: TheBloke/Mistral-7B-Instruct-v0.2-GPTQ
  quantization: 4bit
  db_path: ./data/vector_db/chromadb
  top_k: 5

extraction:
  repos_config: ./config/repos.yaml
  output_dir: ./data/extraction
  languages:
    - python
    - nix
    - rust
    - go

modules:
  credit_burner:
    enabled: true
    default_workers: 10

  knowledge:
    enabled: true
    auto_index: true
```

---

## 📦 Dependências Unificadas

### `requirements.txt` (consolidado)

```txt
# Google Cloud
google-cloud-discoveryengine>=0.11.0
google-cloud-storage>=2.10.0
google-cloud-aiplatform>=1.38.0
google-cloud-billing>=1.11.0
google-cloud-bigquery>=3.14.0
google-cloud-dialogflow-cx>=1.20.0
google-auth>=2.25.0

# RAG & Embeddings
fastapi>=0.109.0
uvicorn>=0.27.0
chromadb>=0.4.22
sentence-transformers>=2.3.0
transformers>=4.36.0
torch>=2.1.0
accelerate>=0.26.0
bitsandbytes>=0.41.0

# Code Analysis
tree-sitter>=0.20.4
tree-sitter-languages>=1.10.0
gitpython>=3.1.40
pygments>=2.17.0

# Document Processing
beautifulsoup4>=4.12.0
markdown>=3.5.0
pypdf>=3.17.0

# CLI & Utils
typer>=0.9.0
rich>=13.7.0
pydantic>=2.5.0
pyyaml>=6.0.1
python-dotenv>=1.0.0
tqdm>=4.66.0
```

---

## 🚀 Migration Workflow

### Fase 1: Setup Nova Estrutura ✅

1. Renomear `cerebro/` → `phantom/`
2. Criar diretórios: `core/`, `modules/`, `config/`, `docs/`
3. Mover `.archive/` para arquivos deprecados

### Fase 2: Consolidar Core Modules ⏳

1. Unificar `manage_datastores.py` → `core/gcp/datastores.py`
2. Unificar `validate_credits.py` → `core/gcp/auth.py`
3. Criar `core/gcp/search.py` (SearchServiceClient)
4. Criar `core/gcp/billing.py` (BigQuery audit)
5. Criar `core/gcp/dialogflow.py` (DialogflowCX)

### Fase 3: Migrar Application Modules ⏳

1. `burn_credits_loadtest.py` → `modules/credit_burner/loadtest.py`
2. `burn_dialogflow_cx.py` → `modules/credit_burner/dialogflow_sessions.py`
3. `audit_credits_bigquery.py` → `modules/credit_burner/audit.py`
4. `import_documents.py` → `modules/knowledge/import_docs.py`

### Fase 4: CLI Unificado ⏳

1. Criar `phantom.py` com Typer
2. Implementar subcommands para cada módulo
3. Adicionar auto-complete (zsh/bash)

### Fase 5: Documentação ⏳

1. README.md principal
2. Docs por módulo
3. API reference
4. Migration guide

### Fase 6: Testing & Validation ⏳

1. Unit tests para core modules
2. Integration tests
3. E2E test do credit burner workflow
4. Smoke tests

---

## 🎨 Design Decisions

### Por que Phantom?

- **CEREBRO** era focado em knowledge extraction
- **PHANTOM** abrange todo o framework (knowledge + cloud + integrations)
- Nome curto, memorável, extensível

### Por que não apenas refatorar in-place?

- Evitar breaking changes durante migração
- Permitir rollback fácil
- Documentar processo de transformação
- Criar oportunidade para limpar código legado

### Por que módulos separados?

- **Separation of Concerns**: cada módulo tem responsabilidade única
- **Testabilidade**: módulos testáveis independentemente
- **Reutilização**: core modules podem ser usados em outros projetos
- **Manutenibilidade**: mudanças isoladas não quebram sistema todo

---

## 📊 Métricas de Sucesso

- ✅ Zero duplicação de código (DRY)
- ✅ Todos os workflows originais funcionando
- ✅ CLI unificado e consistente
- ✅ Documentação completa e atualizada
- ✅ Tests com >80% coverage
- ✅ Nix flake validado (`nix flake check`)
- ✅ Performance mantida ou melhorada

---

## 🔮 Futuro / Roadmap

### v2.1 - Multi-Cloud Support
- AWS Bedrock integration
- Azure OpenAI integration
- Local-only mode (sem cloud)

### v2.2 - Enhanced RAG
- Multi-modal RAG (images, PDFs)
- Graph-based retrieval
- Fine-tuning support

### v2.3 - DevOps Integration
- CI/CD pipelines
- Kubernetes deployment
- Terraform modules

### v3.0 - Phantom Platform
- Web UI
- API Gateway
- Multi-user support
- Usage analytics

---

**Autor:** Phantom Team
**Status:** 🚧 Em Desenvolvimento
**Last Updated:** 2026-01-02
