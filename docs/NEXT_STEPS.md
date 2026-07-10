# 🚀 PRÓXIMOS PASSOS - Phantom Framework

**Versão:** 2.0.0
**Status:** Migração completa, pronto para próxima fase

---

## 📋 Resumo da Situação Atual

### ✅ O Que Está Pronto

- **Arquitetura unificada** - Tudo consolidado no Phantom Framework
- **Core/GCP módulo** - Auth, datastores, search, billing, dialogflow
- **Core/Extraction** - Code analysis, embeddings, ingest
- **Core/RAG** - Server com local LLM
- **Módulo Credit Burner** - Loadtest e audit
- **CLI unificado** - `phantom.py` com comandos organizados
- **Documentação** - Architecture, quick start, guides

### 🚧 O Que Precisa de Atenção

1. **Imports precisam ser testados** - Novos caminhos podem ter issues
2. **flake.nix precisa atualização** - Ainda aponta para estrutura antiga
3. **Tests não existem** - Tudo funcional mas sem testes automatizados
4. **Alguns módulos são placeholders** - knowledge/ e nixos/

---

## 🎯 Recomendações Prioritárias

### Fase 1: Validação Básica (URGENTE)

#### 1.1 Testar CLI Básico

```bash
# Entre no ambiente
nix develop

# Teste comandos básicos
python phantom.py --help
python phantom.py info
python phantom.py version
```

**Possíveis Issues:**
- Import errors devido aos novos caminhos
- Missing dependencies (typer, rich)
- Python path problems

**Fix Esperado:**
```bash
# Se faltar dependências
pip install typer rich

# Se tiver import errors
export PYTHONPATH="${PWD}:${PYTHONPATH}"
```

#### 1.2 Testar Core/GCP

```bash
# Validate setup
python phantom.py gcp validate

# List datastores (deve funcionar se tiver configurado)
python phantom.py gcp datastores-list
```

**Possíveis Issues:**
- Import `from phantom.core.gcp` pode falhar
- Google Cloud SDK não configurado

**Fix Esperado:**
- Adicionar `__init__.py` files se faltarem
- Configurar GCP auth

#### 1.3 Testar Core Modules Diretamente

```bash
# Teste módulos individuais
python -c "from phantom.core import gcp; print(gcp)"
python -c "from phantom.core.gcp import validate_setup; print('OK')"
python -c "from phantom.modules.credit_burner import run_loadtest; print('OK')"
```

### Fase 2: Atualizar Infraestrutura

#### 2.1 Atualizar flake.nix

**Arquivo:** `flake.nix` (root)

**Mudanças Necessárias:**

```nix
# Adicionar phantom CLI ao buildInputs
packages = with pkgs; [
  # ... existing packages

  # Phantom CLI wrapper
  (writeShellScriptBin "phantom" ''
    cd ${self}
    exec ${pkgs.python313}/bin/python ${self}/phantom.py "$@"
  '')
];

# Ou criar derivação própria
packages.phantom = pkgs.python313.pkgs.buildPythonApplication {
  pname = "phantom";
  version = "2.0.0";
  src = ./.;

  propagatedBuildInputs = with pkgs.python313.pkgs; [
    typer
    rich
    google-cloud-discoveryengine
    # ... outras deps
  ];

  format = "other";
  installPhase = ''
    mkdir -p $out/bin
    cp -r phantom $out/lib/
    cp phantom.py $out/bin/phantom
    chmod +x $out/bin/phantom
  '';
};
```

**Benefício:**
- `phantom` disponível globalmente no shell
- Não precisa `python phantom.py` toda vez

#### 2.2 Criar pyproject.toml

**Arquivo:** `pyproject.toml` (root)

```toml
[project]
name = "phantom"
version = "2.0.0"
description = "Knowledge Extraction & Cloud Credit Management"
requires-python = ">=3.11"

dependencies = [
    "typer>=0.9.0",
    "rich>=13.7.0",
    "google-cloud-discoveryengine>=0.11.0",
    "google-cloud-storage>=2.10.0",
    "google-cloud-dialogflow-cx>=1.20.0",
    "google-cloud-bigquery>=3.14.0",
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "chromadb>=0.4.22",
    "sentence-transformers>=2.3.0",
    "transformers>=4.36.0",
    "torch>=2.1.0",
]

[project.scripts]
phantom = "phantom:app"

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["phantom"]
```

**Benefício:**
- Instalação via `pip install -e .`
- Phantom como comando global
- Dependency management limpo

### Fase 3: Testing (Crítico)

#### 3.1 Criar Test Suite Básico

**Estrutura:**

```
phantom/tests/
├── conftest.py              # Pytest fixtures
├── core/
│   ├── test_gcp_auth.py    # Auth validation tests
│   ├── test_datastores.py  # DataStore CRUD tests
│   └── test_search.py      # Search functionality tests
└── modules/
    └── test_credit_burner.py
```

**Exemplo:** `phantom/tests/core/test_gcp_auth.py`

```python
import pytest
from phantom.core.gcp import get_credentials, validate_setup

def test_get_credentials():
    """Test that credentials can be retrieved"""
    creds, project = get_credentials()
    assert creds is not None
    assert project is not None

def test_validate_setup():
    """Test setup validation"""
    status = validate_setup(verbose=False)
    assert status.authenticated is True
```

**Rodar:**

```bash
# Instalar pytest
pip install pytest pytest-cov

# Rodar testes
pytest phantom/tests/

# Com coverage
pytest --cov=phantom phantom/tests/
```

#### 3.2 Smoke Tests

Criar script de smoke test para validar rapidamente:

**Arquivo:** `phantom/scripts/validation/smoke_test.sh`

```bash
#!/usr/bin/env bash
set -e

echo "🧪 Running Phantom Framework smoke tests..."

# Test CLI loads
python phantom.py --help > /dev/null
echo "✅ CLI loads"

# Test imports
python -c "from phantom.core import gcp"
echo "✅ Core imports work"

# Test module imports
python -c "from phantom.modules.credit_burner import run_loadtest"
echo "✅ Module imports work"

# Test GCP validation (may fail if not configured)
python phantom.py gcp validate || echo "⚠️  GCP not configured (expected)"

echo "🎉 Smoke tests passed!"
```

### Fase 4: Expansão de Funcionalidade

#### 4.1 Completar Módulo Knowledge

**Tarefas:**

1. **Import de documentos local**

   ```python
   # phantom/modules/knowledge/import_docs.py
   from phantom.core.gcp import DataStoreManager

   def import_local_files(files: List[Path], datastore_id: str):
       # Upload to GCS
       # Trigger import to datastore
       pass
   ```

2. **Query interface melhorado**

   ```python
   # phantom/modules/knowledge/query.py
   from phantom.core.gcp import VertexAISearch

   def interactive_query(datastore_id: str):
       # REPL for querying knowledge base
       pass
   ```

3. **Adicionar ao CLI**

   ```python
   # phantom.py
   knowledge_app = typer.Typer(help="Knowledge base operations")

   @knowledge_app.command("import")
   def knowledge_import(path: Path, datastore_id: str):
       # ...
   ```

#### 4.2 Completar Módulo NixOS

**Objetivo:** Gerar configuração NixOS para services

**Exemplo:**

```python
# phantom/modules/nixos/service.py

def generate_rag_service() -> str:
    """Generate NixOS service config for RAG server"""
    return '''
    { config, pkgs, ... }:

    {
      systemd.services.phantom-rag = {
        description = "Phantom RAG Server";
        wantedBy = [ "multi-user.target" ];

        serviceConfig = {
          ExecStart = "${pkgs.phantom}/bin/phantom rag serve";
          DynamicUser = true;
          StateDirectory = "phantom-rag";
        };
      };
    }
    '''
```

#### 4.3 Web UI (Opcional, mas bacana)

**Stack sugerido:**
- Backend: FastAPI (já tem no RAG)
- Frontend: HTMX + Alpine.js (leve)
- Styling: Tailwind CSS

**Features:**
- Dashboard de créditos consumidos
- Interface para queries
- Visualização de billing audit
- Real-time metrics

### Fase 5: Production Ready

#### 5.1 CI/CD

**GitHub Actions:** `.github/workflows/test.yml`

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: nixbuild/nix-quick-install-action@v25
      - run: nix develop --command pytest phantom/tests/
```

#### 5.2 Monitoring

**Adicionar telemetria:**

```python
# phantom/core/utils/telemetry.py

import logging
from datetime import datetime

class PhantomTelemetry:
    def log_query(self, cost: float, duration: float):
        # Log to file or service
        pass

    def get_daily_stats(self) -> dict:
        # Aggregate stats
        pass
```

#### 5.3 Documentation Site

**Opções:**
- MkDocs Material
- Docusaurus
- VitePress

**Conteúdo:**
- Getting Started
- API Reference
- Architecture Deep Dive
- Use Case Examples
- Troubleshooting Guide

---

## 🎯 Roadmap Sugerido

### Sprint 1 (Esta Semana)
- [ ] Validar CLI funciona
- [ ] Testar imports de todos os módulos
- [ ] Atualizar flake.nix
- [ ] Criar smoke tests
- [ ] Documentar issues encontrados

### Sprint 2 (Próxima Semana)
- [ ] Criar test suite básico
- [ ] Completar módulo knowledge
- [ ] Adicionar pyproject.toml
- [ ] Testar credit burner end-to-end

### Sprint 3 (2 Semanas)
- [ ] Módulo NixOS service generator
- [ ] Monitoring/telemetry básico
- [ ] CI/CD setup
- [ ] Performance benchmarks

### Sprint 4 (1 Mês)
- [ ] Web UI (se quiser)
- [ ] Documentation site
- [ ] Advanced features
- [ ] Production deployment

---

## 🔧 Troubleshooting Esperado

### Issue 1: Import Errors

**Sintoma:**
```
ModuleNotFoundError: No module named 'phantom'
```

**Fix:**
```bash
export PYTHONPATH="${PWD}:${PYTHONPATH}"
# Ou
pip install -e .
```

### Issue 2: Missing Dependencies

**Sintoma:**
```
ModuleNotFoundError: No module named 'typer'
```

**Fix:**
```bash
pip install -r requirements.txt
# Ou atualizar flake.nix
```

### Issue 3: GCP Auth Fails

**Sintoma:**
```
google.auth.exceptions.DefaultCredentialsError
```

**Fix:**
```bash
gcloud auth application-default login
```

### Issue 4: Old Files Causing Confusion

**Sintoma:**
- Scripts antigos ainda sendo executados

**Fix:**
```bash
# Verificar se .archive/ tem tudo
ls -la .archive/

# Se sim, pode deletar (ou deixar como backup)
```

---

## 💡 Decisões Arquiteturais Pendentes

### 1. Estratégia de Configuração

**Opções:**

A. **YAML Config File**
```yaml
# phantom-config.yaml
gcp:
  project_id: auto-detect
  location: global
  data_store_id: ds-app-v4

credits:
  genai_budget_brl: 6432.54
  dialogflow_budget_brl: 3646.57
```

B. **Environment Variables Only** (atual)

C. **Hybrid** (YAML + ENV overrides)

**Recomendação:** Hybrid - YAML para defaults, ENV para secrets

### 2. Logging Strategy

**Opções:**

A. **Python logging** (simples)
B. **Structlog** (structured logging)
C. **Cloud Logging** (if running on GCP)

**Recomendação:** Structlog para flexibility

### 3. Error Handling

**Atual:** Exceções básicas

**Melhorias:**
- Custom exception hierarchy
- Retry logic para network calls
- Graceful degradation

---

## 📊 Métricas de Sucesso

### Técnicas
- [ ] 100% dos comandos CLI funcionam
- [ ] >80% test coverage
- [ ] Zero duplicação de código (✅ já atingido)
- [ ] Imports funcionam de qualquer lugar

### Funcionais
- [ ] Consegue queimar créditos sem erro
- [ ] Audit via BigQuery funciona
- [ ] RAG server pode ser iniciado
- [ ] Knowledge extraction roda

### Qualidade
- [ ] Documentação completa
- [ ] Código passa linting
- [ ] Type hints em 80%+ do código
- [ ] Performance aceitável

---

## 🎬 Começar AGORA

**Primeira ação recomendada:**

```bash
# 1. Testar se CLI carrega
python phantom.py --help

# 2. Se funcionar, testar gcp validate
python phantom.py gcp validate

# 3. Se tiver issues, documentar e criar issues
# 4. Começar pelos smoke tests
```

**Boa sorte! O framework está pronto para evoluir! 🚀**

---

**Documento criado:** 2026-01-02
**Status:** Recomendações ativas
**Prioridade:** Validação básica URGENTE
