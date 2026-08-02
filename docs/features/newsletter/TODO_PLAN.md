# 🎯 TODO PLAN — Newsletter Pipeline (cerebro × spider-nix × voidnxlabs intel)

> Plano operacional pra transformar a stack `cerebro` em um pipeline de newsletter que **roda sozinho** e produz conteúdo de alto sinal toda quinzena. Cada task tem comando exato, output esperado, dependências, tempo. Sem fluff.

**Última atualização:** 2026-05-03

---

## 🗺️ Como tudo se conecta

```
                               ┌─────────────────────────┐
                               │   SCRIPTS DE QUERY GEN  │
                               │                         │
        personal_moat_builder ─┤                         │
        salary_intel ──────────┤   queries_*.txt         │
        trend_predictor ───────┤   (300-500 queries cada)│
        generate_queries ──────┤                         │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │      batch_burn.py      │
                               │   (10 workers, paralelo)│
                               │   ↓                     │
                               │   Discovery Engine API  │
                               │   ↓                     │
                               │   batch_results_*.json  │
                               └────────────┬────────────┘
                                            │
        ┌───────────────────────────────────┴─────────────────────────────────┐
        │                                                                     │
        ▼                                                                     ▼
┌─────────────────────┐                                       ┌──────────────────────────┐
│ index_repository.py │                                       │  content_gold_miner.py   │
│                     │                                       │  (mina batch_results pra │
│  Repos canônicos →  │                                       │   insights, snippets,    │
│  Discovery DataStore│                                       │   quotes, citações)      │
│  (Tokio, Cockroach, │                                       │                          │
│   Turbo, nixpkgs)   │                                       └────────────┬─────────────┘
└─────────┬───────────┘                                                    │
          │                                                                │
          │     grounded_search.py (RAG queries com citação a arquivo+linha)│
          │                                                                │
          └────────────────────────┬───────────────────────────────────────┘
                                   ▼
                    ┌─────────────────────────────────┐
                    │  newsletter_generator.py (NEW)  │
                    │  pega: source markdown + RAG    │
                    │  output: 00X-edition.md         │
                    └────────────────┬────────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                            ▼
 ┌─────────────────┐       ┌─────────────────┐         ┌─────────────────┐
 │ Newsletter MD   │       │ 5 LinkedIn vars │         │ Twitter threads │
 │ (Substack/blog) │       │ (5 weeks queue) │         │ (curtos)        │
 └─────────────────┘       └─────────────────┘         └─────────────────┘
```

**Mapa script × edição da newsletter:**

| Script existente | Edição alvo | O que extrai |
|---|---|---|
| `personal_moat_builder.py` | #001, #007 | Skill gaps, power combos, niche positioning |
| `index_repository.py` + `grounded_search.py` | #002, #004 | Decisões de arquitetura de codebases canônicos |
| (queries de system design no `generate_queries.py`) | #003 | Banco FAANG / system design |
| `content_gold_miner.py` | #005 | Mineração das próprias queries pra LinkedIn |
| `salary_intel.py` | #006 | Negotiation data + scripts |
| `trend_predictor.py` | #008 | Tech emergente + papers correlacionados |
| Newsletter pipeline + monetization queries | #009 | Newsletter business model |
| **Pipeline completo** | #010 | O sistema rodando, end-to-end |

---

## 📋 FASE 0 — Mapping & Setup (1 dia)

### T01 — Confirmar config Discovery Engine
**Objetivo:** garantir que env vars estão configuradas e batch_burn roda.
```bash
echo "PROJECT_ID=$GCP_PROJECT_ID"
echo "DATA_STORE_ID=$DATA_STORE_ID"
echo "ENGINE_ID=$ENGINE_ID"
gcloud auth list
gcloud config get-value project
```
**Output esperado:** três variáveis preenchidas + auth válida.  
**Time:** 5min  
**Status:** ⬜ pending

### T02 — Smoke test batch_burn
```bash
cd ~/master/cerebro
echo "Como NixOS implementa systemd modules?" > test_query.txt
python scripts/batch_burn.py --file test_query.txt --workers 1
ls -la batch_results_*.json | tail -1
```
**Output esperado:** 1 arquivo `batch_results_*.json` com 1 resposta.  
**Time:** 2min  
**Depende de:** T01  
**Status:** ⬜ pending

### T03 — Lista os 5 codebases canônicos pra indexar primeiro
**Critério de seleção:** alto sinal arquitetural, código de produção, comunidade ativa, < 500MB clonado.

| Repo | Tamanho aprox | Por que |
|---|---|---|
| `tokio-rs/tokio` | ~50MB | Async runtime de referência. Schedulers, mutex, channels. |
| `cockroachdb/cockroach` | ~400MB | Distributed SQL. MVCC, Raft, gossip. (Pesado mas vale) |
| `vercel/turbo` | ~80MB | Build system moderno. Caching, parallelism. |
| `tigerbeetle/tigerbeetle` | ~30MB | Financial DB. State machine, deterministic, zero-alloc. |
| `nixpkgs` (subset: nixos/modules) | ~120MB | NixOS modules canônicos. |

**Output esperado:** decisão registrada neste arquivo. ✅  
**Time:** decisão já tomada. Próximo é clonar.  
**Status:** ✅ done

### T04 — Clonar os 5 repos em workspace dedicado
```bash
mkdir -p ~/master/cerebro/data/codebases
cd ~/master/cerebro/data/codebases
git clone --depth=1 https://github.com/tokio-rs/tokio.git
git clone --depth=1 https://github.com/cockroachdb/cockroach.git
git clone --depth=1 https://github.com/vercel/turbo.git
git clone --depth=1 https://github.com/tigerbeetle/tigerbeetle.git
# nixpkgs subset
git clone --depth=1 --filter=blob:none --sparse https://github.com/NixOS/nixpkgs.git
cd nixpkgs && git sparse-checkout set nixos/modules
```
**Output esperado:** 5 diretórios em `~/master/cerebro/data/codebases/`.  
**Time:** 10–20min (cockroach é grande)  
**Depende de:** T03  
**Status:** ⬜ pending

---

## 📋 FASE 1 — Foundation queries (2–3 dias)

### T10 — Gerar queries de personal moat
```bash
cd ~/master/cerebro
python scripts/personal_moat_builder.py \
  --output queries_personal_moat.txt \
  --github marcosfpina
```
**Output esperado:** ~100 queries em `queries_personal_moat.txt` + `moat_building_strategy.md`.  
**Time:** 1min geração + revisão manual de 10min.  
**Depende de:** T01  
**Status:** ⬜ pending

### T11 — Gerar queries de salary intel
```bash
python scripts/salary_intel.py \
  --output queries_salary_intel.txt \
  --current 180000 \
  --target 400000
```
**Output esperado:** ~80 queries personalizadas.  
**Time:** 1min  
**Depende de:** T01  
**Status:** ⬜ pending

### T12 — Gerar queries de trend prediction
```bash
python scripts/trend_predictor.py \
  --output queries_trend_prediction.txt
```
**Output esperado:** ~150 queries baseadas em GitHub trending + HN dos últimos 30 dias.  
**Time:** 2min (faz API calls)  
**Depende de:** T01  
**Status:** ⬜ pending

### T13 — Burn queries de personal moat
```bash
python scripts/batch_burn.py \
  --file queries_personal_moat.txt \
  --workers 10
```
**Output esperado:** `batch_results_personal_moat_*.json`. ~100 queries × R$0.022 = **R$2.20**.  
**Time:** 10–15min (paralelo).  
**Depende de:** T10, T02  
**Status:** ⬜ pending

### T14 — Burn queries de salary intel
```bash
python scripts/batch_burn.py \
  --file queries_salary_intel.txt \
  --workers 10
```
**Output esperado:** `batch_results_salary_*.json`. ~R$1.76.  
**Time:** 8–10min.  
**Depende de:** T11, T02  
**Status:** ⬜ pending

### T15 — Burn queries de trend prediction
```bash
python scripts/batch_burn.py \
  --file queries_trend_prediction.txt \
  --workers 10
```
**Output esperado:** `batch_results_trends_*.json`. ~R$3.30.  
**Time:** 15min.  
**Depende de:** T12, T02  
**Status:** ⬜ pending

### T16 — Validar saúde dos resultados
```bash
python scripts/monitor_credits.py
ls -la batch_results_*.json | tail -10
# Sample inspection
jq '.results[0]' batch_results_personal_moat_*.json
```
**Output esperado:** queries bem-sucedidas > 95%, custo total < R$10, todos os `.summary` populados.  
**Time:** 5min  
**Depende de:** T13, T14, T15  
**Status:** ⬜ pending

---

## 📋 FASE 2 — Codebase indexing (2–3 dias)

### T20 — Index Tokio
```bash
python scripts/index_repository.py \
  ~/master/cerebro/data/codebases/tokio \
  --project $GCP_PROJECT_ID \
  --data-store $DATA_STORE_ID \
  --batch-size 100 --yes
```
**Output esperado:** "Submitted N batches". Indexação async leva 30–60min.  
**Time:** 5min comando + 30–60min wait.  
**Depende de:** T04  
**Status:** ⬜ pending

### T21 — Index Cockroach
```bash
python scripts/index_repository.py \
  ~/master/cerebro/data/codebases/cockroach \
  --max-docs 5000 --yes
```
**Output esperado:** ~5000 docs (limit aplicado, é repo grande).  
**Time:** 10min + wait.  
**Depende de:** T04  
**Status:** ⬜ pending

### T22 — Index Turbo
```bash
python scripts/index_repository.py \
  ~/master/cerebro/data/codebases/turbo --yes
```
**Time:** 5min + wait.  
**Depende de:** T04  
**Status:** ⬜ pending

### T23 — Index TigerBeetle
```bash
python scripts/index_repository.py \
  ~/master/cerebro/data/codebases/tigerbeetle --yes
```
**Time:** 3min + wait.  
**Depende de:** T04  
**Status:** ⬜ pending

### T24 — Index nixpkgs/nixos/modules
```bash
python scripts/index_repository.py \
  ~/master/cerebro/data/codebases/nixpkgs/nixos/modules --yes
```
**Time:** 5min + wait.  
**Depende de:** T04  
**Status:** ⬜ pending

### T25 — Esperar indexing assíncrono completar
**Como verificar:**
```bash
# Console GCP
xdg-open "https://console.cloud.google.com/gen-app-builder/data-stores"
# Ou via API
gcloud alpha discovery-engine documents list \
  --data-store=$DATA_STORE_ID --location=global | wc -l
```
**Output esperado:** contagem de docs > 10000 (acumulado dos 5 repos).  
**Time:** 30–60min wait.  
**Depende de:** T20, T21, T22, T23, T24  
**Status:** ⬜ pending

### T26 — Smoke test grounded queries
```bash
cd ~/master/cerebro
python scripts/grounded_search.py "How does Tokio implement work-stealing scheduler?"
python scripts/grounded_search.py "How does CockroachDB implement MVCC under network partitions?"
python scripts/grounded_search.py "What's the design of TigerBeetle's deterministic state machine?"
```
**Output esperado:** cada resposta cita arquivos específicos com linha.  
**Time:** 3min.  
**Depende de:** T25  
**Status:** ⬜ pending

---

## 📋 FASE 3 — Newsletter generator (1–2 dias)

### T30 — Build `newsletter_generator.py`
**Especificação:**
- Input: edition number, topic, source-of-truth markdown (anteriores), `batch_results_*.json` relevantes
- Output: `00X-edition.md`
- Lógica:
  1. Lê template estrutural (hook → tese → corpo → math → CTA)
  2. Pega top-K snippets de `batch_results` que casam com keywords da edição
  3. Pra cada seção do template, monta com snippets reais (mantém citações)
  4. Gera versão final em markdown

**Arquivo:** `~/master/cerebro/scripts/newsletter_generator.py`  
**Time:** 4–6h.  
**Status:** ⬜ pending

### T31 — Build `linkedin_variations_generator.py`
**Especificação:**
- Input: newsletter markdown final
- Output: 5 variações conforme `001-linkedin-variations.md` (hot take, story, data, question, carrossel)
- Cada variação tem char count, hashtags, CTA específico

**Arquivo:** `~/master/cerebro/scripts/linkedin_variations_generator.py`  
**Time:** 2–3h.  
**Depende de:** T30  
**Status:** ⬜ pending

### T32 — Validação: regenerar #001 e diff vs original
```bash
python scripts/newsletter_generator.py \
  --edition 001 \
  --topic "knowledge-moat" \
  --output regenerated_001.md
diff <(grep -v "^---" regenerated_001.md) <(grep -v "^---" docs/features/newsletter/001-knowledge-moat.md)
```
**Output esperado:** diff < 30% (alguma variação esperada, mas estrutura+tese intactas).  
**Time:** 30min.  
**Depende de:** T30  
**Status:** ⬜ pending

---

## 📋 FASE 4 — Edition #002 (Codebase Mining) (1 dia)

### T40 — Definir as 5 queries-chave que cortam direto pro coração
```text
1. How does <X> handle concurrency primitives at the lowest level?
2. What's the error propagation strategy from leaf modules to public API?
3. Where is the boundary between sync and async, and how is it crossed?
4. How is shared state managed under contention?
5. What are the performance hotpaths and how are they instrumented?
```
**Output esperado:** template salvo em `scripts/templates/codebase_mining_queries.txt`.  
**Time:** 30min.  
**Status:** ⬜ pending

### T41 — Rodar as 5 queries contra Tokio (grounded)
```bash
for q in $(cat scripts/templates/codebase_mining_queries.txt); do
  python scripts/grounded_search.py "$q (in Tokio codebase)" \
    >> data/edition_002/tokio_responses.json
done
```
**Output esperado:** 5 respostas com citações arquivo+linha.  
**Time:** 5min.  
**Depende de:** T26, T40  
**Status:** ⬜ pending

### T42 — Gerar #002 markdown
```bash
python scripts/newsletter_generator.py \
  --edition 002 \
  --topic "codebase-mining" \
  --source data/edition_002/tokio_responses.json \
  --output docs/features/newsletter/002-codebase-mining.md
```
**Output esperado:** ~1500–2000 palavras, com snippets reais de Tokio.  
**Time:** 10min comando + 1h edit humano.  
**Depende de:** T30, T41  
**Status:** ⬜ pending

### T43 — Gerar 5 LinkedIn variations do #002
```bash
python scripts/linkedin_variations_generator.py \
  --source docs/features/newsletter/002-codebase-mining.md \
  --output docs/features/newsletter/002-linkedin-variations.md
```
**Time:** 5min comando + 30min edit.  
**Depende de:** T31, T42  
**Status:** ⬜ pending

### T44 — Publicar #002
- Newsletter: Substack ou blog
- LinkedIn variation 2 (story) primeiro
**Time:** 20min.  
**Depende de:** T43  
**Status:** ⬜ pending

---

## 📋 FASE 5 — Pipeline automation (3–5 dias)

### T50 — Build `daily_digest.py`
**Especificação:**
- Pega top-3 trends das últimas 24h via `trend_predictor`
- Roda 5 queries grounded sobre eles
- Gera digest 300–500 palavras
- Envia por e-mail (ou ntfy/Telegram)

**Arquivo:** `~/master/cerebro/scripts/daily_digest.py`  
**Time:** 4–6h.  
**Status:** ⬜ pending

### T51 — Build `weekly_newsletter.py`
**Especificação:**
- Cron: domingo 18h
- Compila 7 daily digests da semana
- Estrutura: top news + deep dive + 1 query gold standard
- Salva como rascunho em `docs/features/newsletter/draft_<date>.md`

**Time:** 3h.  
**Status:** ⬜ pending

### T52 — Build `linkedin_post_pipeline.py`
**Especificação:**
- Lê queue de variações (gerado por `linkedin_variations_generator`)
- Posta 1 por dia via API LinkedIn (ou copia pro clipboard pra postar manual)
- Tracking: quais variações foram postadas em qual data

**Time:** 4h (incluindo OAuth do LinkedIn).  
**Status:** ⬜ pending

### T53 — Wire up cron em NixOS systemd timers
```nix
# nixos/services/cerebro-pipeline.nix
{
  systemd.timers.daily-digest = {
    wantedBy = [ "timers.target" ];
    timerConfig = { OnCalendar = "*-*-* 06:00:00"; Persistent = true; };
  };
  systemd.services.daily-digest = {
    serviceConfig.ExecStart = "${pkgs.python313}/bin/python /opt/cerebro/scripts/daily_digest.py";
  };
  # Idem pra weekly_newsletter (domingo 18h)
}
```
**Time:** 2h.  
**Depende de:** T50, T51  
**Status:** ⬜ pending

### T54 — Build `metrics_collector.py`
**Especificação:**
- Daily: scrapes LinkedIn API → views/likes/saves/comments por post
- Weekly: tabela cruzando variação × performance
- Detecta qual ângulo (hot take, story, data, etc.) tá performando melhor
- Output em `data/metrics/<week>.json`

**Time:** 3h.  
**Status:** ⬜ pending

---

## 📋 FASE 6 — Editions #003–#010 (10 weeks, biweekly)

| ID | Edição | Topic | Source script | Status |
|---|---|---|---|---|
| T60 | #003 | Interview hacking | `generate_queries.py` (system design subset) + `grounded_search` | ⬜ |
| T61 | #004 | GitHub intelligence (10 stacks × 3 repos) | `index_repository.py` × 30 + `personal_moat_builder` | ⬜ |
| T62 | #005 | Content arbitrage (LinkedIn factory) | `content_gold_miner.py` + post analytics | ⬜ |
| T63 | #006 | Salary negotiation | `salary_intel.py` results | ⬜ |
| T64 | #007 | Niche moat | `personal_moat_builder.py` results | ⬜ |
| T65 | #008 | Top papers | `trend_predictor.py` + manual paper list | ⬜ |
| T66 | #009 | Newsletter business model | Manual + `content_gold_miner` | ⬜ |
| T67 | #010 | Capstone (system end-to-end) | All of the above + system tour video | ⬜ |

**Cadência:** quinzenal, quartas-feiras 06h BRT.  
**Cada edição:** ~6–8h (4h edit + 2h LinkedIn variations + 1h publish + 1h promo).

---

## 📋 FASE 7 — Open source / handoff (com #010)

### T70 — Open-source o pipeline
**Repo:** `github.com/voidnxlabs/intel-pipeline`  
**Conteúdo:**
- `cerebro/` (este projeto, sem secrets)
- `spider-nix/` (link)
- `scripts/` (todos os generators)
- `nix/` (flakes pra rodar tudo reproduzível)
- `docs/` (newsletter editions + setup guide)
- `LICENSE`: AGPL-3.0 (já está no Cerebro)

**Time:** 1 dia.  
**Status:** ⬜ pending

### T71 — Newsletter #010 — Capstone
**Conteúdo:**
- Tour do pipeline rodando uma quarta inteira
- Arquitetura completa (este `TODO_PLAN.md` aberto)
- Métricas reais de 5 meses (subs, posts, inbound, comp)
- Hand-off: como bifurcar e adaptar pro seu nicho

**Time:** 2–3 dias (incluindo gravação de vídeo).  
**Depende de:** T70 + métricas acumuladas das 9 edições anteriores.  
**Status:** ⬜ pending

---

## 🎯 Critério de "feito" pra cada fase

| Fase | "Feito" significa |
|---|---|
| **F0** | `gcloud auth list` ok, batch_burn cospe um JSON, 5 codebases clonados |
| **F1** | 3 query files gerados, todos batch_burned, batch_results_*.json populados |
| **F2** | 5 codebases indexados, contagem ≥ 10k docs no Discovery, smoke test passa |
| **F3** | `newsletter_generator.py` regenera #001 com diff < 30% do manual |
| **F4** | #002 publicado + 5 variações postadas |
| **F5** | Cron rodando, 7 daily digests + 1 weekly draft sem intervenção humana |
| **F6** | 8 edições publicadas (#003–#010) + métricas mostrando inbound > 0 |
| **F7** | Repo público + #010 publicado + 1 fork de outra pessoa |

---

## 💰 Budget total

| Fase | Custo (R$) | Cumulativo |
|---|---|---|
| F0 | 0,05 | 0,05 |
| F1 | 7,30 | 7,35 |
| F2 | 0 (indexing é grátis) | 7,35 |
| F3 | 0 (dev) | 7,35 |
| F4 | 0,30 | 7,65 |
| F5 | ~5/dia × 30 dias × 6 meses ≈ 900 | ~907 |
| F6 | ~50/edição × 8 edições | ~1.307 |
| F7 | 0 | ~1.307 |

**Total estimado:** R$ 1.500 dos R$ 10.000 disponíveis (sobra **85% de orçamento** pra escalar / repetir / experimentar).

---

## ⏱️ Cronograma sugerido

```
Semana 1:  F0 (1 dia) + F1 (4 dias)        ← foundation pronta
Semana 2:  F2 (3 dias) + F3 (4 dias)       ← indexing + generator
Semana 3:  F4 (#002 publicado) + F5 start  ← primeira edição automatizada
Semana 4–5: F5 cron rodando + métricas    ← pipeline operacional
Semanas 6–25: F6 quinzenal (#003–#010)    ← 5 meses de cadência
Semana 26: F7 (open source + #010)         ← capstone + handoff
```

**Marco intermediário (mês 2):** se #003 for publicado e F5 estiver rodando, pipeline está validado. Daí em diante é só **executar a esteira**.

---

## 🚦 Próxima ação concreta

```bash
# Agora:
cd ~/master/cerebro
echo "$GCP_PROJECT_ID / $DATA_STORE_ID / $ENGINE_ID"   # T01
echo "Como NixOS implementa systemd modules?" > test_query.txt
python scripts/batch_burn.py --file test_query.txt --workers 1   # T02

# Se T02 retornar JSON com resposta:
python scripts/personal_moat_builder.py --output queries_personal_moat.txt --github marcosfpina   # T10
python scripts/salary_intel.py --output queries_salary_intel.txt --current 180000 --target 400000   # T11
python scripts/trend_predictor.py --output queries_trend_prediction.txt   # T12
```

**Quanto tempo isso leva:** 30 minutos pra T01 → T12. Daí você tem 3 query files prontas pra burn (T13–T15).

---

## 🎯 Princípios deste plano

1. **Cada task tem comando exato.** Sem "e então você faz X". Cospe a linha de bash.
2. **Cada task tem output esperado.** Sabe o que checar pra dizer "feito".
3. **Dependências explícitas.** Não roda T13 antes de T10 — `Depende de:` no topo.
4. **Custo conhecido.** Cada burn tem estimativa em R$. Total visível.
5. **Pode parar em qualquer fase.** F1 sozinha já gera 3 batch results valiosos. F2 sozinha já te dá codebase RAG. Cada fase entrega valor.
6. **Pipeline > tasks.** F5 é o ouro: depois dele rodando, F6 é só executar a esteira.

---

*Esse plano vai ser editado conforme execução. Cada task que marca ✅ atualiza este arquivo. Em 6 meses, este arquivo vira o material da edição #010.*
