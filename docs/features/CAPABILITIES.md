# PHANTOM Framework - Capabilities Reference

**Version:** 2.0.0
**Last Updated:** 2026-01-07

## Overview

Este documento descreve todas as capabilities (funcionalidades) do PHANTOM Framework, organizadas por módulo e com detalhamento completo para facilitar a manutenção e extensão do sistema.

---

## Core Capabilities Structure

```
phantom CLI
├── knowledge (Análise e Auditoria)
│   ├── analyze
│   ├── batch-analyze
│   └── summarize
├── ops (Status Operacional)
│   └── status
├── rag (RAG & Vetores)
│   ├── ingest
│   └── query
└── Global Commands
    ├── info
    └── version
```

---

## 1. Knowledge Module

### Purpose
Extração, análise e processamento de conhecimento de repositórios de código.

### Commands

#### `phantom knowledge analyze`
**Description:** Extrai AST e gera JSONL de artifacts estruturados.

**Usage:**
```bash
phantom knowledge analyze <repo_path> [task_context] [--config-file]
```

**Parameters:**
- `repo_path` (required): Caminho para o repositório a ser analisado
- `task_context` (optional): Contexto da tarefa (default: "General Review")
- `config_file` (optional): Arquivo de configuração (default: "./config/repos.yaml")

**Output:**
- `data/analyzed/<repo_name>/metrics.json`: Métricas do repositório
- `data/analyzed/<repo_name>/artifacts.json`: Artifacts extraídos
- `data/analyzed/all_artifacts.jsonl`: Consolidado global

**Hook Support:**
- `pre_analyze`: Executado antes da análise
- `post_analyze`: Executado após a análise

**Capabilities:**
- Parsing AST multi-linguagem (Python, Nix, Rust, Bash, TypeScript, JavaScript)
- Extração de funções, classes e módulos
- Análise de dependências externas
- Heurísticas de segurança e performance
- Execução de hooks customizados

---

#### `phantom knowledge batch-analyze`
**Description:** Processa todos os repositórios definidos na configuração.

**Usage:**
```bash
phantom knowledge batch-analyze [--config-file]
```

**Parameters:**
- `config_file` (optional): Arquivo de configuração (default: "./config/repos.yaml")

**Output:**
- Executa `analyze` para cada repositório configurado
- Logs de progresso e erros

**Features:**
- Processamento em lote
- Suporte a priorização (critical, high, medium, low)
- Tratamento de erros por repositório

---

#### `phantom knowledge summarize`
**Description:** Gera relatório executivo de um repositório analisado.

**Usage:**
```bash
phantom knowledge summarize <repo_name>
```

**Parameters:**
- `repo_name` (required): Nome do repositório previamente analisado

**Output:**
- `data/analyzed/<repo_name>/EXECUTIVE_REPORT.md`

**Report Contents:**
- Contexto da análise
- Lines of Code (LoC)
- Security hints
- Performance hints

---

## 2. RAG Module

### Purpose
Ingestão e consulta de conhecimento via Retrieval Augmented Generation.

### Commands

#### `phantom rag ingest`
**Description:** Cria Vector DB local (ChromaDB) com embeddings VertexAI.

**Usage:**
```bash
phantom rag ingest [--source-file]
```

**Parameters:**
- `source_file` (optional): Arquivo JSONL de entrada (default: "./data/analyzed/all_artifacts.jsonl")

**Dependencies:**
- LangChain
- ChromaDB
- VertexAI Embeddings

**Output:**
- ChromaDB local persistido
- Contagem de chunks indexados

**Features:**
- Embeddings de alta qualidade via VertexAI
- Persistência local para baixa latência
- Chunking inteligente de artifacts

---

#### `phantom rag query`
**Description:** Consulta RAG local com métricas de qualidade.

**Usage:**
```bash
phantom rag query "<question>"
```

**Parameters:**
- `question` (required): Pergunta em linguagem natural

**Output:**
- Resposta gerada
- Métricas de qualidade:
  - Average Confidence
  - Hit Rate (@k=4)
  - Top Source

**Features:**
- Busca vetorial otimizada
- Reranking de resultados
- Métricas de precision/recall

---

## 3. OPS Module

### Purpose
Monitoramento e status operacional do framework.

### Commands

#### `phantom ops status`
**Description:** Exibe status dos repositórios analisados.

**Usage:**
```bash
phantom ops status
```

**Output:**
- Lista de repositórios com status local

**Future Capabilities:**
- Health checks de serviços GCP
- Métricas de uso de créditos
- Status de ingestion pipelines

---

## 4. Global Commands

#### `phantom info`
**Description:** Exibe informações sobre o ambiente e dependências.

**Output:**
- Versão do framework
- Status de componentes:
  - GCP Integration
  - LangChain/RAG
  - Code Analysis

---

#### `phantom version`
**Description:** Exibe versão atual do CLI.

**Output:**
```
Phantom CLI v0.1.0
```

---

## Hook System

### Hook Stages
- `pre_analyze`: Antes da análise de código
- `post_analyze`: Após a análise de código

### Hook Metadata Schema

```yaml
hooks:
  <stage>:
    - description: "Human-readable description"
      command: "shell command to execute"
      allow_failure: false  # Continue on failure (default: false)
      timeout: 120          # Timeout in seconds (default: 120)
      retry: false          # Retry on failure (default: false)
```

### Supported Hook Features
- Command execution no contexto do repositório
- Timeout configurável
- Retry automático
- Failure handling customizado
- Resultado capturado em metrics

### Example Hook Configuration

```yaml
repos:
  - name: my-repo
    path: "./path/to/repo"
    hooks:
      pre_analyze:
        - description: "Run linter"
          command: "ruff check ."
          allow_failure: true
          timeout: 60

      post_analyze:
        - description: "Run tests"
          command: "pytest -v"
          allow_failure: false
          timeout: 300
          retry: true
```

---

## Configuration System

### Configuration File: `config/repos.yaml`

#### Global Settings
```yaml
global:
  workspace_root: "."
  reports_dir: "./data/reports"
  artifacts_dir: "./data/analyzed"
  max_concurrency: 4
  exclude:
    - ".git"
    - ".venv"
    - "node_modules"
```

#### Repository Schema
```yaml
repos:
  - name: string              # Unique identifier
    path: string              # Repository path
    priority: string          # critical | high | medium | low
    description: string       # Short description
    context: |                # Multi-line context for LLM
      Context text here
    hooks:
      pre_analyze: []         # List of hooks
      post_analyze: []        # List of hooks
    options:
      deep_analysis: bool     # Enable deep analysis
      extract_ast: bool       # Extract AST
      security_scan: bool     # Run security checks
      languages: []           # List of languages to analyze
```

---

## Extension Points

### Adding New Capabilities

1. **Add new command to CLI module:**
```python
@app.command("new-command")
def new_command(param: str):
    """Command description"""
    # Implementation
    pass
```

2. **Add new hook stage:**
```python
# In HermeticAnalyzer.analyze_repo()
if hooks and "new_stage" in hooks:
    results = self.run_hooks("new_stage", hooks["new_stage"], repo_path)
```

3. **Add new capability module:**
```python
# In cli.py
new_module_app = typer.Typer(help="New Module Description")
app.add_typer(new_module_app, name="new-module")

@new_module_app.command("action")
def action():
    pass
```

---

## Best Practices

### Hook Development
1. Sempre forneça `description` clara e descritiva
2. Use `allow_failure: true` para hooks não-críticos
3. Configure `timeout` adequado para operações longas
4. Use `retry: true` apenas para operações idempotentes
5. Teste hooks isoladamente antes de adicionar ao pipeline

### Capability Development
1. Mantenha comandos focados em uma única responsabilidade
2. Valide inputs antes de processamento pesado
3. Forneça feedback claro ao usuário (Rich formatting)
4. Use lazy imports para dependências pesadas
5. Documente parâmetros e outputs claramente

### Configuration Management
1. Use YAML para configurações declarativas
2. Forneça defaults sensatos
3. Valide schema antes de processar
4. Documente opções e seus efeitos
5. Separe configurações globais de específicas

---

## Troubleshooting

### Hook Failures
- Verifique logs no console durante execução
- Resultados salvos em `metrics.json` → `hook_results`
- Use `allow_failure: true` para debugging

### Missing Dependencies
- Run `phantom info` para verificar status
- Instale com `poetry install` ou `nix develop`

### RAG Quality Issues
- Aumente número de chunks (`k` parameter)
- Verifique qualidade dos embeddings
- Re-ingest com dados melhores

---

## Future Roadmap

### Planned Capabilities
- [ ] `phantom gcp` - GCP operations module
- [ ] `phantom credit` - Credit management
- [ ] `phantom deploy` - Cloud Run deployment
- [ ] `phantom agents` - Agent orchestration
- [ ] `phantom monitor` - Real-time monitoring

### Hook System Enhancements
- [ ] Parallel hook execution
- [ ] Hook dependencies (requires, provides)
- [ ] Hook templates library
- [ ] Custom hook stages
- [ ] Hook marketplace

---

**Maintainer:** KernelCore
**License:** MIT
**Support:** [GitHub Issues](https://github.com/kernelcore/phantom/issues)
