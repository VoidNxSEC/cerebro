# GAPS.md — O que esta faltando ou quebrado

**Data:** 2026-06-27
**Criterio de priorizacao:** Impacto no workflow imediato x esforco de correcao

---

## Resumo

| ID   | Prioridade | Categoria        | Titulo                                         | Esforco |
|------|-----------|------------------|------------------------------------------------|---------|
| G-01 | CRITICO   | Dependencias     | `nats-py` ausente do pyproject.toml            | 5 min   |
| G-02 | ALTO      | Dependencias     | Providers cloud sem grupos opcionais           | 15 min  |
| G-03 | ALTO      | Build            | `poetry lock` desatualizado (pendente)         | 2 min   |
| G-04 | ALTO      | Benchmark        | `psutil` ausente do pyproject.toml             | 2 min   |
| G-05 | MEDIO     | Documentacao     | docs/STATUS.md referencia PHOENIX (Jan 2026)  | ja corrigido neste PR |
| G-06 | MEDIO     | Testes           | tests/tests/ e um diretorio duplicado estale   | 5 min   |
| G-07 | MEDIO     | CLI              | `cerebro knowledge index-repo` usa GCP hardcoded | 30 min |
| G-08 | MEDIO     | Portas           | Dual porta (8009 dev / 8000 docker) nao documentada | ja documentado |
| G-09 | BAIXO     | Build            | `nix build .#default` nao validado             | variavel |
| G-10 | BAIXO     | CLI              | `cerebro strategy optimize --execute` e stub   | 1-2h   |
| G-11 | BAIXO     | CLI              | `cerebro knowledge etl/docs` delegam a scripts GCP | 1-2h |
| G-12 | BAIXO     | API              | TODO em `core/rag/server.py` (confidence = 0.85 hardcoded) | 30 min |

---

## Detalhe dos gaps

---

### G-01 — CRITICO: `nats-py` ausente do pyproject.toml

**Impacto:** Pipeline distribuido com Spectre completamente inoperante. O servidor API sobe com `WARNING: NATS publisher connection failed (non-fatal)`. Qualquer evento `ingest.file.sanitized.v1` publicado pelo Spectre e ignorado.

**Evidencia:**
- `src/cerebro/nats/consumer.py` linha 29: `import nats`
- `src/cerebro/nats/publisher.py` linha 24: `import nats`
- `src/cerebro/nats/streams.py` linhas 51, 66-67: `import nats`
- `src/cerebro/nats/worker.py` linha 80: `from nats.js.api import ...`
- `pyproject.toml`: zero ocorrencias de "nats"
- `flake.nix`: `pkgs.nats-server` e `pkgs.natscli` estao presentes (binarios do servidor, NAO o client Python)

**Correcao:**

```toml
# pyproject.toml — [tool.poetry.dependencies]
nats-py = ">=2.6.0"
```

Ou via CLI:

```sh
nix develop
poetry add nats-py
```

---

### G-02 — ALTO: Providers cloud sem grupos opcionais em pyproject.toml

**Impacto:** `CEREBRO_LLM_PROVIDER=anthropic` (ou groq, gemini, openai) resulta em `ImportError` em runtime. O engine tenta `from cerebro.providers.anthropic.llm import AnthropicProvider` que por sua vez faz `import anthropic` — package nao instalado.

**Providers afetados:**

| Provider         | Package Python         | Instalado por padrao |
|-----------------|------------------------|----------------------|
| anthropic        | `anthropic`            | NAO                  |
| groq             | `groq`                 | NAO                  |
| gemini           | `google-generativeai`  | NAO                  |
| openai_compatible| `openai`               | NAO                  |
| azure            | `langchain-openai`     | grupo azure (existe) |

**Correcao:**

Adicionar ao `pyproject.toml`:

```toml
[tool.poetry.group.anthropic]
optional = true

[tool.poetry.group.anthropic.dependencies]
anthropic = ">=0.40.0"

[tool.poetry.group.groq]
optional = true

[tool.poetry.group.groq.dependencies]
groq = ">=0.11.0"

[tool.poetry.group.gemini]
optional = true

[tool.poetry.group.gemini.dependencies]
google-generativeai = ">=0.8.0"

[tool.poetry.group.openai]
optional = true

[tool.poetry.group.openai.dependencies]
openai = ">=1.30.0"
```

Instalacao:

```sh
poetry install --with anthropic
poetry install --with groq,gemini
```

---

### G-03 — ALTO: `poetry lock` desatualizado

**Impacto:** Justfile TODO explicito: `[ ] poetry lock --no-update`. Se pyproject.toml foi alterado (e foi — name corrigido de `phantom` para `cerebro`), o lock file pode estar inconsistente.

**Evidencia:** Justfile, linha 27: `echo "  [ ] poetry lock --no-update   pending"`

**Correcao:**

```sh
nix develop
poetry lock --no-update
```

---

### G-04 — ALTO: `psutil` ausente do pyproject.toml

**Impacto:** `cerebro benchmark run` falha ao tentar medir uso de RAM (`_get_ram_usage_mb()` em scripts/benchmark.py linha 76-80). O benchmark tem fallback graceful mas a feature de monitoramento de memoria nao funciona.

**Evidencia:** `scripts/benchmark.py` linhas 76-80: `import psutil` sem fallback robusto no contexto do benchmark.

**Correcao:**

```toml
# pyproject.toml — [tool.poetry.dependencies]
psutil = ">=5.9.0"
```

---

### G-05 — MEDIO: docs/STATUS.md referenciava PHOENIX (resolvido neste doc)

**Impacto:** O STATUS.md existente (data 2026-01-03) descrevia o estado de uma versao anterior do projeto (chamada PHOENIX) com creditos GCP Discovery Engine. Nao refletia o estado real do codigo atual.

**Status:** CORRIGIDO — este arquivo substitui o STATUS.md anterior.

---

### G-06 — MEDIO: `tests/tests/` e um diretorio duplicado estale

**Impacto:** Pytest descobre e roda testes duplicados. A configuracao `norecursedirs = ["scripts", "agents", "data", "tests/tests"]` em pyproject.toml ja exclui esse diretorio, mas a existencia causa confusao e potencial divergencia de fixtures.

**Evidencia:**
```
tests/tests/conftest.py
tests/tests/debug_cli.py
tests/tests/integration/test_vertex_limits.py
tests/tests/integration/test_workflow.py
tests/tests/test_analyzer.py
tests/tests/test_cli.py
tests/tests/test_rag.py
tests/tests/unit/core_test.rs   # arquivo .rs dentro de tests Python!
```

**Correcao:**

```sh
rm -rf tests/tests/
```

---

### G-07 — MEDIO: `cerebro knowledge index-repo` hardcoda Discovery Engine (GCP)

**Impacto:** `cerebro knowledge index-repo` delega para `scripts/index_repository.py` que importa `from google.cloud import discoveryengine_v1` — nao funciona localmente sem GCP.

**Evidencia:** `scripts/index_repository.py` linha 17: `from google.cloud import discoveryengine_v1`

**Correcao sugerida:** Reimplementar `index_repository.py` para indexar no backend RAG configurado (ChromaDB por padrao) via `RigorousRAGEngine.ingest()`, removendo a dependencia de GCP.

Esforco estimado: 1 hora.

---

### G-08 — MEDIO: Dual porta nao estava documentada (resolvido neste doc)

**Impacto:** Confusao entre porta 8009 (dev) e 8000 (docker). `cerebro benchmark run` por padrao usa `CEREBRO_API_URL=http://localhost:8009` — correto para dev, errado se testando contra container.

**Status:** DOCUMENTADO em RUNBOOK.md.

---

### G-09 — BAIXO: `nix build .#default` nao validado

**Impacto:** Build reproducivel Nix nao foi testado. `poetry2nix` pode ter overrides ausentes para pacotes com extensoes C (chromadb, torch, tree-sitter).

**Evidencia:** Justfile linha 28: `echo "  [ ] nix build .#default (verify packaging)   pending"`

**Correcao:**

```sh
nix build .#default
```

Se falhar com `overrides needed`, adicionar overrides em `flake.nix` para os pacotes problemáticos.

---

### G-10 — BAIXO: `cerebro strategy optimize --execute` e stub

**Impacto:** A flag `--execute` em `cerebro strategy optimize` tem um `# TODO: Implement execution logic` no codigo. Nao executa nada.

**Evidencia:** `src/cerebro/commands/strategy.py` linha 113.

---

### G-11 — BAIXO: `cerebro knowledge etl/docs` delegam para scripts com deps GCP

**Impacto:** Esses comandos esperam `DocumentationETL` e `DocumentationGenerator` em `scripts/etl_docs.py` e `scripts/generate_docs.py`. O etl_docs usa Google Discovery Engine. O generate_docs nao tem implementacao real.

---

### G-12 — BAIXO: confidence hardcoded em core/rag/server.py

**Impacto:** `src/cerebro/core/rag/server.py` linha 180 tem `confidence=0.85 # TODO: implement proper confidence scoring`. Metrica de confianca e fabricada.

---

## Plano de correcao por sessao

### Sessao 1: Desbloqueio NATS + Cloud Providers (30 min)

```sh
# 1. Adicionar nats-py
poetry add "nats-py>=2.6.0"

# 2. Adicionar psutil
poetry add "psutil>=5.9.0"

# 3. Criar grupos opcionais no pyproject.toml para anthropic, groq, gemini, openai
#    (editar manualmente + poetry lock)

# 4. Atualizar lock
poetry lock --no-update
```

### Sessao 2: Limpeza e validacao (30 min)

```sh
# Remover diretorio duplicado
rm -rf tests/tests/

# Rodar testes
just test-unit

# Smoke test RAG
just test-rag-local

# Validar CLI
just validate-cli-smoke
```

### Sessao 3: Benchmark local (20 min)

```sh
# Subir API
just serve &

# Rodar benchmark rapido
cerebro benchmark run --quick

# Ver resultados
ls docs/benchmarks/
```

---

## O que NAO e gap (funciona como esperado)

- ChromaDB embed + ingest + query — FUNCIONAL
- API /health, /rag/status, /chat — FUNCIONAL
- NATS server + CLI tools — PRESENTES no nix shell
- Todos os vector store backends tem implementacao completa
- LlamaCpp provider usa stdlib, zero deps extras
- Embedding cascade (Jina Code → MPNET → MiniLM) — FUNCIONAL no nix shell
- docker-compose profiles (qdrant, pgvector, opensearch) — CORRETOS
- Healthcheck Docker (porta 8000) — CORRIGIDO
- docker-entrypoint.sh (porta 8000) — CORRIGIDO
- pyproject.toml name (`cerebro`) — CORRIGIDO
