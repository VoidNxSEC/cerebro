# 🧠 PHANTOM - Guia de Operação Técnica (v2.6)

Este documento descreve os comandos essenciais para operação do framework PHANTOM, focado em auditoria arquitetural, extração de conhecimento e gestão de créditos GCP.

## 🛠️ 1. Instalação e Ambiente

O PHANTOM utiliza uma arquitetura hermética baseada em **Nix Flakes** e **Poetry**.

```bash
# Entrar no ambiente de desenvolvimento isolado
nix develop

# Sincronizar dependências (Executado automaticamente no shellHook)
# poetry install
```

---

## 🔄 2. Workflow de Auditoria

O fluxo padrão consiste em **Analisar** (extração), **Sintetizar** (relatório) e **Ingerir** (nuvem).

### Passo 1: Análise de Repositório
Extrai artefatos semânticos (AST) e métricas de engenharia.
```bash
phantom knowledge analyze --repo-path ~/dev/meu-projeto --task-context "Foco em Refatoração"
```

### Passo 2: Geração de Relatório Executivo
Sintetiza um documento de alta fidelidade (Magentic Quality) baseado na análise.
```bash
phantom knowledge summarize meu-projeto
```

### Passo 3: Ingestão Cloud
Sincroniza a massa de dados polida com o Google Cloud Storage.
```bash
phantom knowledge ingest
```

---

## 📜 3. Referência de Comandos

### Grupo `knowledge` (Gestão de Inteligência)

| Comando | Parâmetros | Descrição |
| :--- | :--- | :--- |
| `analyze` | `--repo-path`, `--task-context` | Realiza análise profunda de código e extrai métricas. |
| `summarize` | `repo_name`, `--task-context` | Gera o `EXECUTIVE_REPORT.md` para o projeto. |
| `ingest` | `--jsonl-file`, `--bucket` | Faz o upload de artefatos estruturados para o GCS. |

### Grupo `gcp` & `credit` (Operações Cloud)

| Comando | Descrição |
| :--- | :--- |
| `gcp validate` | Valida autenticação, billing e APIs ativas no projeto GCP. |
| `credit loadtest` | Dispara consultas em massa para validação de créditos promocionais. |

---

## 🚀 4. Exemplos Práticos

### Auditoria de Segurança com Contexto
```bash
# Analisar com lente de segurança
phantom knowledge analyze -p ~/dev/webapp -c "Procurar por vazamento de segredos e APIs expostas"

# Gerar relatório dedicado
phantom knowledge summarize webapp
```

### Processamento em Massa para Data Store
```bash
# Analisar projeto core
phantom knowledge analyze -p ./src -c "Mapeamento de arquitetura para documentação"

# Ingestão imediata para o bucket de staging
phantom knowledge ingest ./data/analyzed/all_artifacts.jsonl --bucket meu-bucket-staging
```

## 📁 5. Estrutura de Saída (Schema)

Os resultados são organizados no diretório `./data/analyzed/[repo_name]/`:
- `artifacts.json`: Base de dados técnica (Funções, Classes, Docs).
- `metrics.json`: Estatísticas de LoC, Dependências e Contexto.
- `EXECUTIVE_REPORT.md`: Relatório final pronto para stakeholders.

---
**Foco:** Precisão Arquitetural | **Engine:** PHANTOM AI
