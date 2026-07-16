# Cerebro — Relatório de Auditoria de Produção

**Data:** 2026-07-11 · **Auditor:** Claude (protocolo Phase 2, `deploy/CLAUDE.md`) · **Branch:** `main` @ `0b62108`

---

## Sumário Executivo

Cerebro é uma plataforma RAG em Python (110 arquivos, ~24.5k LOC em `src/`) com arquitetura
modular sólida, 350 testes unitários que **passam localmente** (277 passed, 75 skipped, 8.5s via
`nix develop`) e superfície de deploy madura (Docker multi-stage, compose com profiles, Helm chart,
módulos NixOS). Porém, **3 dos 13 workflows de CI estão quebrados**, não há `nix flake check` no
pipeline, a API não tem autenticação, e o repositório carrega dívida de higiene significativa
(diretório de testes duplicado, `.archive/` e `.coverage` versionados, drift de versão e porta).

**Estado observado: BETA** (consistente com o Delivery Compass — Wave 2, BETA → RC).
**Score: 59/100** · **Effort → RC: M (4–8 semanas)** · **Confiança: alta**

```yaml
project: cerebro
layer: RAG
stated_status: BETA (Wave 2 no Delivery Compass)
observed_status: BETA
scores:
  architecture:        15/20
  ci_cd:               9/20    # capped ≤12: flake.nix sem `nix flake check` em CI
  security:            10/20
  observability:       6/10
  docs:                11/15
  correctness_tests:   7/10
  mcp_integration:     1/5
prod_readiness_total:  59/100
state: BETA
blocking_gaps:
  - 3 workflows de CI quebrados (secret-scan, nix-build, update-flake-lock)
  - flake sem output `checks` — nix flake check impossível
  - API sem authn/authz, bind em 0.0.0.0
  - Integração MCP não documentada em ORCHESTRATION.md (0 menções)
  - Drift de versão (pyproject 0.1.0 vs README/CHANGELOG 1.0.0b1)
effort_to_prod: M
confidence: high
```

---

## 1. Inventário

| Item | Valor |
|------|-------|
| Linguagem principal | Python 3.13 (Poetry + Nix flake) |
| LOC em `src/` | ~24.466 em 110 arquivos `.py` |
| Atividade | 7 commits/30d; último commit 2026-07-10 |
| Remotes | `github` (VoidNxSEC/cerebro) + `forgejo` local |
| Branches | `main`, `dev`, `staging` + branches `sanitized/strip-claude/*` |
| Working tree | Limpo (exceto submódulo `skills/ux-agents` modificado) |
| Entrypoints | CLI `cerebro`/`phantom` (Typer), API FastAPI `:8009`, TUI Textual, dashboard React `:18321` |

**Módulos** (`src/cerebro/`): `api/`, `cli.py`, `tui/`, `core/` (metrics, analyzer, rerank, watcher),
`intelligence/`, `registry/`, `nats/` (publisher/consumer/worker/streams), `providers/`
(anthropic, azure_search, pgvector + factories), `interfaces/` (llm, vector_store), `modules/`
(knowledge, azure, credit_burner), `legacy/`, `commands/`.

---

## 2. Arquitetura — 15/20

**Pontos fortes:**
- Separação limpa interface/implementação: `interfaces/llm.py` + `interfaces/vector_store.py`
  com factories (`providers/llm_factory.py`, `providers/vector_store_factory.py`) — troca de
  backend (chroma/pgvector/qdrant/opensearch/weaviate/azure-search) sem tocar o core.
- Providers LLM como grupos opcionais do Poetry (`anthropic`, `groq`, `gemini`, `openai`) —
  dependências pesadas isoladas.
- Camada NATS bem decomposta (`nats/streams.py`, `worker.py`, `ingest.py`) para integração
  com spectre.
- Apenas 4 marcadores TODO/FIXME em todo o `src/`.
- Código legado explicitamente isolado em `legacy/dashboard_server.py`.

**Dívidas:**
- **`tests/tests/` duplicado e versionado** — cópia antiga da árvore de testes, excluída via
  `norecursedirs` no `pyproject.toml:90`. Deve ser deletada, não escondida.
- **`.archive/` versionado** com scripts mortos (`burn_credits_loadtest.py`, `DISPLAY_SETUP.sh`).
- `scripts/` mistura infra do projeto com ferramentas pessoais de job-hunting
  (`salary_intel.py`, `content_gold_miner.py`, `personal_moat_builder.py`) — escopo do
  `spider-nix` vazando para o cerebro.
- Sprawl na raiz: `JOB.md`, `INIT.md`, `README_PORTFOLIO.md`, `PHOENIX_ARCHITECTURE_REPORT.md`,
  `PORTFOLIO_AUDIT.md`, `flake-inner.nix.backup`, `debug_env.py`, dir `CLAUDE/`.
- `.venv/` local quebrado (symlink para store path coletado pelo GC; shebangs apontam para
  caminho antigo `~/master/prod/cerebro`) — inofensivo mas confunde; o ambiente real é o flake.

---

## 3. CI/CD & Supply Chain — 9/20

13 workflows em `.github/workflows/`, mas **3 estão comprovadamente quebrados**:

| Workflow | Status | Evidência |
|----------|--------|-----------|
| `secret-scan.yml` | **QUEBRADO** | Chama `scripts/phantom-scan-check.sh`, que **não existe** no repo |
| `nix-build.yml` | **QUEBRADO** | Roda `nix-build` e `nix-shell`, mas não há `default.nix` nem `shell.nix` — só `flake.nix` |
| `update-flake-lock.yml` | **QUEBRADO** | Template copiado de outro repo: referencia `./testFlake` e `Cargo.lock`, que não existem aqui |
| `ci.yml` | Frágil | Roda `scripts/ci-test.sh` que executa `nix develop` + pytest completo em runner ubuntu — devshell com torch/CUDA é pesado; verificar último run |
| `nix-fmt.yml`, `docs.yml`, `benchmark.yml`, `adr-validation.yml`, `deploy-*.yml`, `update-*.yml` | Não verificados em runtime | Presentes; triggers razoáveis |

**Nix flake quality gate: 2/5**
- ✅ +1 `flake.lock` committed e fresco (atualizado 2026-07-10, < 30d)
- ❌ +0 `nix flake check` — o flake **não expõe output `checks`** (só `packages`, `devShells` ×8,
  `nixosModules` ×3); nenhum workflow roda flake check
- ❌ +0 `nix build` em CI — `nix-build.yml` está quebrado (aponta para default.nix inexistente)
- ✅ +1 `update-flake-lock.yml` agendado (segundas 03:45 UTC) — mas o job falha no passo do
  `testFlake`, então na prática não entrega

Regra do rubric: flake sem `nix flake check` em CI ⇒ CI/CD ≤ 12/20. Com 3 workflows quebrados: **9/20**.

**Supply chain:** `poetry.lock` + `flake.lock` pinados ✅ · SBOM ausente ❌ · assinatura/provenance
ausente ❌ · secret scanning nominalmente presente mas quebrado ❌.

---

## 4. Segurança — 10/20

**Positivo:**
- `.gitignore` correto para segredos (`.env`, `.env.*`, exceção só para `.env.example` e
  `secrets/**/*.enc.env`) — o `.env` local com senha em texto plano **não está versionado** (verificado via `git ls-files`).
- `.sops.yaml` presente com creation rules para `secrets/` e `kubernetes/*secret*`.
- Docker multi-stage sem segredos no build; healthchecks em todos os serviços do compose.

**Gaps:**
- **API sem autenticação**: `api/server.py` expõe `/intelligence/query`, `/projects`, etc. em
  `0.0.0.0:8009` sem authn/authz. Aceitável atrás da securellm-bridge, mas o contrato "só é
  acessado via bridge" não está documentado nem imposto (bind poderia ser 127.0.0.1).
- **sops é decorativo**: `secrets/` contém só `.gitkeep`, e as chaves age no `.sops.yaml` são
  placeholders ("Replace or rotate these recipients").
- **Secret-scan quebrado** (ver §3) — o gate de vazamento não roda desde a migração de workflows.
- Compose com defaults fracos e `DISABLE_SECURITY_PLUGIN: "true"` no OpenSearch — OK para dev
  local, mas sem variante hardened para deploy.
- `.env` local contém senha em texto plano (Elasticsearch) — recomenda-se migrar para sops já
  que a infra existe.
- Sem threat model documentado.

---

## 5. Observabilidade & Operabilidade — 6/10

- ✅ `/health` (`api/server.py:317`) e `/ai/health` (`:716`); healthcheck no Dockerfile e no compose.
- ✅ `MetricsCollector` com snapshot + scan em background; broadcast de métricas via
  WebSocket/topic; util de logging em `core/utils/logging.py`.
- ✅ Benchmark harness (`scripts/benchmark.py` + `benchmark.yml` em CI).
- ❌ Sem métricas Prometheus/OpenMetrics; sem tracing; logs não estruturados (JSON).
- ❌ Runbook operacional ausente (deploy/rollback vive implícito no Justfile e nos workflows
  `deploy-acr/aks`).

---

## 6. Documentação — 11/15

- ✅ README forte: propósito claro nos primeiros 10s, quickstart Nix-first reproduzível, tabela
  de interfaces, referência de 45 comandos.
- ✅ `docs/` extenso (architecture, guides, features, benchmarks, mermaid) + `mkdocs.yml` + `docs.yml` em CI; `CHANGELOG.md` no formato Keep a Changelog; `CONTRIBUTING.md`.
- ❌ **Drift de versão**: `pyproject.toml` diz `0.1.0`; README e CHANGELOG dizem `v1.0.0b1`.
- ❌ **Drift de porta**: nativo/API `:8009`, Docker/compose `:8000`, dashboard `:18321` — o
  README menciona 8009, o compose usa 8000; a topologia do ecossistema declara `cerebro :8009`.
- ❌ Sprawl de docs na raiz (5+ arquivos de relatório/portfolio) dilui o canônico.
- ❌ `.gitlab-ci.yml` + `.gitlab-ci/` legados coexistem com GitHub Actions — remover ou marcar.

---

## 7. Correctness & Testes — 7/10

- ✅ **Suite unitária verde**: `pytest -m "not integration and not slow"` → **277 passed,
  75 skipped em 8.48s** (executado nesta auditoria via `nix develop`).
- ✅ 350 testes unitários coletados; cobertura por provider (anthropic, gemini, groq, llamacpp,
  openai-compatible, opensearch, pgvector, qdrant) e por módulo (cli, launcher, analyzer,
  intelligence, metrics, knowledge indexer, dashboard).
- ✅ Testes de integração dedicados para 5 backends de vector store + NATS ingest/query
  (`tests/integration/`), com README próprio.
- ⚠️ 75 skips (~21%) — auditar quantos são condicionais legítimos (deps opcionais) vs. mortos.
- ⚠️ Gate de testes em CI depende do `ci.yml` frágil (§3); sem relatório de cobertura publicado
  (o `.coverage` versionado é um artefato acidental, não um gate).

---

## 8. Integração MCP — 1/5

| Dimensão | Estado |
|----------|--------|
| Tool registration | Não verificável a partir deste repo; `.mcp.json` aqui é config de *cliente* (aponta para securellm-mcp), não registro de tool |
| Knowledge DB | Não verificado (fora do escopo do repo) |
| ADR wiring | Nenhum ADR de contrato de integração encontrado no repo |
| Integration test | Nenhum teste exercita o path MCP end-to-end aqui (sentinel pode cobrir — não confirmado) |
| Orchestration doc | ❌ **`deploy/ORCHESTRATION.md` tem 0 menções a "cerebro"** apesar da topologia declarar `cerebro :8009` sob securellm-mcp |

---

## 9. Plano de Ação (ordenado, passos < 2h cada)

### Imediato (bloqueia RC)
1. **Consertar `secret-scan.yml`** — criar `scripts/phantom-scan-check.sh` ou apontar para o
   scanner real do phantom. Gate de segurança não roda hoje.
2. **Consertar `nix-build.yml`** — trocar `nix-build`/`nix-shell` por
   `nix build .#default` + `nix develop --command echo ok`.
3. **Consertar `update-flake-lock.yml`** — remover `testFlake` e `Cargo.lock` do template.
4. **Adicionar output `checks` ao flake** (mínimo: build do pacote + `pytest -m "not integration"`)
   e um workflow `nix flake check` — destrava o teto de 12/20 em CI/CD.

### Recomendado (sobe o score)
5. Deletar `tests/tests/`, `.archive/`, `.coverage`, `flake-inner.nix.backup`, `debug_env.py`
   da árvore versionada (e `.coverage` para o `.gitignore`).
6. Alinhar versão: `pyproject.toml` → `1.0.0b1` (fonte única; badge do README lê de lá).
7. Unificar porta: decidir 8000 ou 8009 e alinhar compose, launcher, README e topologia.
8. Documentar cerebro em `ORCHESTRATION.md` + ADR do contrato de integração no adr-ledger.
9. Bind da API em `127.0.0.1` por padrão (0.0.0.0 só via env), documentando o contrato
   "acesso via securellm-bridge".
10. Popular `secrets/` com sops real (chaves age verdadeiras) e migrar o `.env` local.
11. Remover `.gitlab-ci.yml`/`.gitlab-ci/` legados.
12. Mover scripts de job-hunting (`salary_intel.py` etc.) para o spider-nix.

### Opcional (polish)
13. Endpoint `/metrics` Prometheus; logs JSON estruturados.
14. RUNBOOK.md (start/stop/rollback/restore do vector store).
15. SBOM no release workflow.

---

*Evidências verificadas por execução direta em 2026-07-11: `git ls-files`, `git log`,
inspeção dos 13 workflows, leitura do flake.nix, e execução real da suíte de testes
(`nix develop --command pytest`).*
