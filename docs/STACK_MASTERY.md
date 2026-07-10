# 🎓 STACK MASTERY GUIDE - GCP Discovery Engine + Phoenix

**Objetivo:** Dominar completamente a stack para queimar R$ 10k em créditos com ROI máximo

---

## 📚 ARCHITECTURE OVERVIEW

### Layer 1: Google Cloud Platform (Foundation)

```
GCP Project (gen-lang-client-0530325234)
└── APIs Enabled
    ├── Discovery Engine API (discoveryengine.googleapis.com)
    ├── Dialogflow CX API (dialogflow.googleapis.com)
    └── BigQuery API (bigquery.googleapis.com)
```

**Créditos disponíveis:**
- GenAI App Builder Trial: R$ 6,432.54 (válido até 2026-05-21)
- Dialogflow CX Trial: R$ 3,646.57 (válido até 2026-11-30)
- **Total: R$ 10,079.11**

### Layer 2: Discovery Engine Components

```
Discovery Engine Architecture:
├── Data Stores (armazenam dados para search)
│   ├── ds-app-v4-5e020c93 ✅ (já existe)
│   └── Tipos: UNSTRUCTURED, STRUCTURED, WEBSITE
│
├── Search Engines/Apps (interface de busca sobre data stores)
│   ├── Precisamos criar!
│   └── Types: SEARCH, CHAT, RECOMMENDATION
│
└── Serving Configs (configurações de como servir resultados)
    └── default_config (criado automaticamente)
```

**Hierarquia de recursos:**
```
projects/{PROJECT_ID}/
  locations/{LOCATION}/              # global, us, eu, etc
    collections/{COLLECTION}/        # default_collection
      dataStores/{DATA_STORE_ID}    # ds-app-v4-5e020c93
      engines/{ENGINE_ID}            # <-- PRECISAMOS CRIAR
        servingConfigs/default_config
```

### Layer 3: Phoenix Framework (Automation)

```
phoenix-cloud-run/
├── scripts/                    # Arsenal de 8 scripts
│   ├── strategy_optimizer.py  # Meta-optimizer (ROI: ∞)
│   ├── salary_intel.py        # Negotiation intel (ROI: 2000x)
│   ├── content_gold_miner.py  # Content mining (ROI: ∞)
│   ├── trend_predictor.py     # Early mover (ROI: 50x)
│   ├── personal_moat_builder.py # Niche expertise (ROI: 200x)
│   ├── generate_queries.py    # Volume queries (ROI: 10x)
│   ├── batch_burn.py          # Query executor
│   └── monitor_credits.py     # Credit tracking
│
├── nix/                       # NixOS integration
│   ├── phoenix-aliases.nix    # 20+ shell functions
│   └── INSTALL.md             # Installation guide
│
└── docs/                      # 12 strategy documents
    ├── EXECUTIVE_SUMMARY.md   # Master roadmap
    ├── HACKS_ROI.md          # High-ROI strategies
    └── ...
```

---

## 🔧 SETUP WORKFLOW (Do Zero à Operação)

### Phase 1: GCP Foundation ✅ COMPLETO

```bash
# 1. Authenticate
gcloud auth application-default login

# 2. Set project
gcloud config set project gen-lang-client-0530325234

# 3. Enable APIs
gcloud services enable discoveryengine.googleapis.com
gcloud services enable dialogflow.googleapis.com
gcloud services enable bigquery.googleapis.com

# 4. Validate
nix develop --command python phantom.py gcp validate
```

**Status atual:** ✅ APIs habilitadas, billing ativo

### Phase 2: Discovery Engine Setup ⚠️ PENDENTE

**Opção A: Console UI (Recomendado para primeiro engine)**

1. Acesse: https://console.cloud.google.com/gen-app-builder/engines
2. Click "Create App" ou "Create Engine"
3. Configurações:
   - **Name:** phoenix-search-engine
   - **Type:** Search (Advanced website indexing and search)
   - **Content:** Generic
   - **Location:** global
   - **Data Store:** Selecione `ds-app-v4-5e020c93`
4. Click "Create"
5. Copie o ENGINE_ID da URL: `projects/.../engines/{ENGINE_ID}`

**Opção B: gcloud CLI**

```bash
# Criar engine via gcloud (se disponível)
gcloud alpha discovery-engine engines create phoenix-search \
  --display-name="Phoenix Search Engine" \
  --location=global \
  --collection=default_collection \
  --solution-type=SOLUTION_TYPE_SEARCH \
  --data-store-ids=ds-app-v4-5e020c93
```

**Opção C: Python SDK (Programático)**

```python
from google.cloud import discoveryengine_v1

client = discoveryengine_v1.EngineServiceClient()

engine = discoveryengine_v1.Engine(
    display_name="Phoenix Search Engine",
    solution_type=discoveryengine_v1.SolutionType.SOLUTION_TYPE_SEARCH,
    data_store_ids=["ds-app-v4-5e020c93"],
    search_engine_config=discoveryengine_v1.Engine.SearchEngineConfig(
        search_tier=discoveryengine_v1.SearchTier.SEARCH_TIER_ENTERPRISE,
    ),
)

parent = "projects/gen-lang-client-0530325234/locations/global/collections/default_collection"

operation = client.create_engine(
    parent=parent,
    engine=engine,
    engine_id="phoenix-search-engine"
)

# Wait for operation to complete (pode levar minutos)
result = operation.result()
print(f"Engine created: {result.name}")
```

### Phase 3: Configurar ENGINE_ID ⚠️ PENDENTE

```bash
# Depois de criar o engine, pegar o ID

# Método 1: Temporário (sessão atual)
export ENGINE_ID=phoenix-search-engine

# Método 2: Permanente (adicionar ao shell)
echo 'export ENGINE_ID=phoenix-search-engine' >> ~/.bashrc
source ~/.bashrc

# Método 3: NixOS (recomendado)
# Adicionar ao home.nix ou configuration.nix:
# environment.variables.ENGINE_ID = "phoenix-search-engine";
```

### Phase 4: Testar Query ⚠️ BLOQUEADO

```bash
# Single query test
nix develop --command python scripts/batch_burn.py \
  --file <(echo "test query") \
  --project gen-lang-client-0530325234 \
  --location global \
  --engine phoenix-search-engine \
  --workers 1

# Ou via alias (depois de instalar nix/phoenix-aliases.nix)
pxq "test query"
```

### Phase 5: Execução (Depois de ENGINE_ID configurado)

```bash
# 1. Generate master plan
python scripts/strategy_optimizer.py

# 2. Execute recommended strategy
python scripts/salary_intel.py --current 150000 --target 300000 --execute

# 3. Mine content
python scripts/content_gold_miner.py

# 4. Monitor credits
python scripts/monitor_credits.py --once
```

---

## 🎯 DISCOVERY ENGINE DEEP DIVE

### Pricing Model

```python
# GenAI App Builder (Vertex AI Search)
SEARCH_TIER_STANDARD = "$1.00 per 1,000 queries"
SEARCH_TIER_ENTERPRISE = "$4.00 per 1,000 queries"

# Com R$ 6,432.54 em créditos
# Assumindo $1 = R$ 5.50 (aproximado)
USD_credits = 6432.54 / 5.50  # ~$1,169.55

# ENTERPRISE tier (melhor qualidade, usamos isso)
queries_enterprise = (1169.55 / 4.00) * 1000  # ~292,388 queries

# Mas na prática:
# - Cada query custa ~R$ 0.022
# - Total de queries: 6432.54 / 0.022 = ~292,000 queries
```

### Query Anatomy

```python
from google.cloud import discoveryengine_v1

# Serving config format:
serving_config = (
    f"projects/{project_id}/"
    f"locations/{location}/"
    f"collections/default_collection/"
    f"engines/{engine_id}/"
    f"servingConfigs/default_config"
)

# Search request:
request = discoveryengine_v1.SearchRequest(
    serving_config=serving_config,
    query="your question here",

    # Content search spec (RAG + summarization)
    content_search_spec=discoveryengine_v1.SearchRequest.ContentSearchSpec(
        summary_spec=discoveryengine_v1.SearchRequest.ContentSearchSpec.SummarySpec(
            summary_result_count=5,        # 1-10 results to summarize
            include_citations=True,        # Add source citations
            ignore_adversarial_query=True, # Safety
            ignore_non_summary_seeking_query=True,
            model_prompt_spec=discoveryengine_v1.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                preamble="You are an expert technical consultant."
            ),
            model_spec=discoveryengine_v1.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                version="stable",  # or "preview"
            ),
        ),
        extractive_content_spec=discoveryengine_v1.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
            max_extractive_answer_count=5,
            max_extractive_segment_count=5,
        ),
    ),

    # Page size
    page_size=10,  # Max results per page
)

# Response structure:
response = search_client.search(request)

# Access summary (RAG answer)
summary = response.summary.summary_text

# Access citations
for reference in response.summary.summary_with_metadata.references:
    print(f"Source: {reference.document}")

# Access individual results
for result in response.results:
    print(result.document.derived_struct_data)
```

### Cost Optimization Hacks

```python
# 1. Batch queries (já fazemos via batch_burn.py)
# 2. Use summary_result_count otimizado (5-7 é sweet spot)
# 3. Avoid duplicate queries (check batch_results_*.json)
# 4. Use parallel workers (10-50 workers)

# Nossa estratégia:
# - 292,000 queries disponíveis
# - Focar em high-ROI (salary_intel: 80 queries = R$ 50k-200k)
# - Sobrar créditos para trends/moat (200-250 queries each)
# - Content mining = R$ 0 (analisa resultados existentes)
```

---

## 🧠 QUERY ENGINEERING MASTERY

### Quality Hierarchy

```
Tier S: Specific + Context + Constraints (ROI: 100-2000x)
├── "Google L5 SWE salary negotiation em 2025: equity, base, signing bonus breakdown"
├── "Rust async: tokio vs async-std trade-offs para high-throughput web service"
└── "NixOS home-manager: declarative config patterns que escalam para 50+ services"

Tier A: Specific + Context (ROI: 20-50x)
├── "Salary negotiation techniques for senior engineers"
├── "Rust async best practices"
└── "NixOS configuration patterns"

Tier B: Generic (ROI: 5-10x)
├── "How to negotiate salary"
├── "Rust async programming"
└── "NixOS setup"
```

### Context Stacking Technique

```python
# BAD: Generic
"Como fazer cache em Rust?"

# GOOD: Context stacked
"""
Rust web service com tokio + axum servindo 5k requests/sec.
Preciso de cache layer para database queries (PostgreSQL).
Requirements:
- P99 latency < 10ms
- TTL configurável por query type
- Invalidation strategy
- Memory limit: 2GB
- Production-ready (error handling, metrics)

Comparar redis vs in-memory (moka/mini-moka).
"""
```

### Template System (usado em generate_queries.py)

```python
TEMPLATES = {
    "tech_deep_dive": [
        "{tech}: arquitetura interna, trade-offs, e quando usar vs alternativas",
        "{tech}: production pitfalls que docs não mencionam",
        "{tech}: performance optimization checklist completo",
    ],

    "career_intel": [
        "{company} {level}: salary bands 2025, negotiation leverage points",
        "{company}: interview process breakdown, preparation timeline",
        "{company}: offer structure analysis (equity, bonus, perks)",
    ],

    "comparison": [
        "{tech1} vs {tech2}: decision matrix baseado em scale, team size, latency req",
        "{tech1} vs {tech2}: migration path, effort estimation, risks",
    ],
}
```

---

## 💰 ROI OPTIMIZATION FRAMEWORK

### Decision Matrix: Qual script rodar?

```python
# Situation 1: Preciso de $ AGORA (30-60 dias)
if goal == "immediate_money":
    run("salary_intel.py")      # ROI: 2000x, Cost: R$ 1.76
    run("content_gold_miner.py") # ROI: ∞, Cost: R$ 0
    # Total: R$ 1.76 → R$ 50k-200k

# Situation 2: Build long-term moat (12-24 meses)
elif goal == "expertise":
    run("personal_moat_builder.py")  # ROI: 200x, Cost: R$ 2.20
    run("trend_predictor.py")        # ROI: 50x, Cost: R$ 3.30
    # Total: R$ 5.50 → R$ 200k-500k premium

# Situation 3: Visibility + inbound offers (3-6 meses)
elif goal == "visibility":
    run("generate_queries.py --count 500")  # R$ 11
    run("content_gold_miner.py")           # R$ 0
    # Post 1/dia → 10k-50k views/mês → 5-10 offers

# Situation 4: YOLO (queimar tudo)
elif goal == "spray_and_pray":
    run("generate_queries.py --count 10000")  # R$ 220
    # Hope for serendipity
```

### Credit Allocation Strategy

```python
BUDGET = 10_000  # BRL

# Tier S allocation (85% do value, 5% do budget)
tier_s = {
    "salary_intel": 1.76,
    "personal_moat_builder": 2.20,
    "trend_predictor": 3.30,
    "content_gold_miner": 0,  # Free
    "strategy_optimizer": 0,  # Free
}
tier_s_cost = 7.26  # R$

# Tier A allocation (10% do value, 10% do budget)
tier_a = {
    "generate_queries_focused": 1000 * 0.022,  # R$ 22
}

# Remaining (volume, experimentation)
remaining = 10_000 - 7.26 - 22  # R$ 9,970.74

# Use for:
# - Retries/refinements
# - A/B testing query templates
# - Emergency salary negotiation prep
# - Trend deep dives que aparecerem
```

---

## 🚀 EXECUTION PLAYBOOKS

### Playbook 1: Job Search Speedrun (30 dias)

```bash
# Day 1: Intel gathering
python scripts/salary_intel.py \
  --current 150000 \
  --target 300000 \
  --execute

# Day 2-3: Study outputs
pxls verbose
pxfind "google"
pxfind "negotiation"
pxfind "levels"

# Day 4-30: Apply strategy
# - Update resume com insights
# - Practice negotiation scripts
# - Target companies com high offers
# - Use leverage points descobertos

# Expected outcome: R$ 50k-200k bump
```

### Playbook 2: Content Empire (90 dias)

```bash
# Week 1: Generate diverse queries
python scripts/generate_queries.py --count 200 --output career.txt
python scripts/generate_queries.py --count 200 --output tech.txt
python scripts/trend_predictor.py
python scripts/personal_moat_builder.py

# Week 2-3: Execute
for file in *.txt; do
    ./speedrun.sh burn $file 20
done

# Week 4: Mine gold
python scripts/content_gold_miner.py

# Week 5-16: Post content
# - Use content_calendar_30days.md
# - 1 post/dia on LinkedIn/Twitter
# - Repurpose top insights

# Expected outcome:
# - 10k-50k views/month
# - 5-10 inbound offers
# - Personal brand boost
```

### Playbook 3: Expertise Moat (12 meses)

```bash
# Month 1: Discovery
python scripts/personal_moat_builder.py
python scripts/trend_predictor.py
# Read moat_building_strategy.md

# Month 2-3: Execute focused learning
./speedrun.sh burn queries_personal_moat.txt 10
./speedrun.sh burn queries_trend_prediction.txt 10

# Month 4-6: Build + document
# - Create portfolio projects
# - Write blog posts (use content_gold_miner.py)
# - Give talks

# Month 7-12: Establish authority
# - Contribute to open source
# - Answer Stack Overflow
# - Publish case studies

# Expected outcome:
# - Recognized expert em 1-2 niches
# - R$ 200k-500k salary premium
# - Inbound offers from top companies
```

---

## 🔧 TROUBLESHOOTING GUIDE

### Issue 1: ENGINE_ID not set

```bash
# Symptom
$ pxq "test"
Error: ENGINE_ID environment variable not set

# Root cause
No Search Engine (App) created yet

# Solution
1. Create engine (via Console, gcloud, or Python SDK)
2. export ENGINE_ID=<engine-id>
3. Add to ~/.bashrc or NixOS config
```

### Issue 2: 403 Permission Denied

```bash
# Symptom
google.api_core.exceptions.PermissionDenied: 403 Permission denied

# Root cause
API not enabled OR billing not linked

# Solution
gcloud services enable discoveryengine.googleapis.com
gcloud alpha billing projects link gen-lang-client-0530325234 \
  --billing-account=010A4F-F7F74E-D2E502
```

### Issue 3: No results returned

```bash
# Symptom
Search returns empty results or poor quality

# Root cause
Data store empty or not indexed

# Solution
1. Check data store has documents
2. Wait for indexing (can take hours)
3. Use better queries (context stacking)
```

### Issue 4: Credit not being consumed

```bash
# Symptom
BigQuery audit shows R$ 0 spent

# Root cause
Using wrong billing account OR promotional credit not applied

# Solution
1. Check promotional credits:
   gcloud billing accounts list
2. Verify credit is active (not expired)
3. Wait 24-48h for billing data to appear
```

---

## 📊 MONITORING & ANALYTICS

### Real-time Monitoring

```bash
# Terminal 1: Run queries
./speedrun.sh all

# Terminal 2: Monitor credits
watch -n 60 'python scripts/monitor_credits.py --once'

# Terminal 3: Track progress
watch -n 10 'ls -lht batch_results_*.json | head -n 3'
```

### Post-execution Analytics

```python
# Analyze all batch results
import json
from pathlib import Path
from collections import Counter

files = Path(".").glob("batch_results_*.json")
all_results = []

for file in files:
    data = json.loads(file.read_text())
    all_results.extend(data.get("results", []))

print(f"Total queries processed: {len(all_results)}")
print(f"Total cost: R$ {len(all_results) * 0.022:.2f}")

# Top topics
topics = []
for r in all_results:
    # Extract keywords from questions
    topics.extend(r['question'].lower().split())

top_topics = Counter(topics).most_common(20)
print("\nTop topics:")
for topic, count in top_topics:
    print(f"  {topic}: {count}")
```

### BigQuery Custom Queries

```sql
-- Query credits consumption over time
SELECT
  DATE(usage_start_time) as day,
  SUM(cost) as daily_cost,
  COUNT(*) as query_count,
  service.description as service
FROM `gen-lang-client-0530325234.billing_export.gcp_billing_export_v1_*`
WHERE
  DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND project.id = 'gen-lang-client-0530325234'
GROUP BY day, service
ORDER BY day DESC
LIMIT 100;

-- Identify most expensive SKUs
SELECT
  sku.description,
  SUM(cost) as total_cost,
  COUNT(*) as usage_count
FROM `gen-lang-client-0530325234.billing_export.gcp_billing_export_v1_*`
WHERE project.id = 'gen-lang-client-0530325234'
GROUP BY sku.description
ORDER BY total_cost DESC
LIMIT 20;
```

---

## 🎓 MASTERY CHECKLIST

### Level 1: Foundation (Week 1)
- [ ] GCP authentication working
- [ ] APIs enabled (Discovery Engine, Dialogflow, BigQuery)
- [ ] Data Store created
- [ ] Search Engine (App) created
- [ ] ENGINE_ID configured
- [ ] First test query successful
- [ ] NixOS aliases installed (pxq, pxb, etc working)

### Level 2: Execution (Week 2-4)
- [ ] strategy_optimizer.py executed
- [ ] MASTER_EXECUTION_PLAN.md reviewed
- [ ] salary_intel.py queries generated and processed
- [ ] content_gold_miner.py executed
- [ ] First batch_results_*.json analyzed
- [ ] Credit monitoring working (monitor_credits.py)
- [ ] R$ 100+ credits consumed

### Level 3: Optimization (Month 2-3)
- [ ] ROI tracking implemented
- [ ] Custom query templates created
- [ ] A/B testing different query styles
- [ ] Content calendar being followed
- [ ] First viral post (1k+ views)
- [ ] R$ 1,000+ credits consumed efficiently

### Level 4: Mastery (Month 4-6)
- [ ] Personal moat identified and building
- [ ] Trend predictions being acted on
- [ ] Inbound offers received
- [ ] Salary bump negotiated (R$ 50k+)
- [ ] All R$ 10k credits consumed strategically
- [ ] ROI documented and measured

### Level 5: Teaching (Month 6+)
- [ ] Can explain stack to others
- [ ] Custom scripts/tools created
- [ ] Process documented
- [ ] Sharing insights publicly
- [ ] Helping others maximize their GCP credits

---

## 📚 REFERENCE LINKS

### Official Docs
- [Vertex AI Search Overview](https://cloud.google.com/generative-ai-app-builder/docs/introduction)
- [Discovery Engine API Reference](https://cloud.google.com/generative-ai-app-builder/docs/reference/rest)
- [Python Client Library](https://cloud.google.com/python/docs/reference/discoveryengine/latest)
- [Pricing Calculator](https://cloud.google.com/generative-ai-app-builder/pricing)

### Phoenix Docs (Internal)
- EXECUTIVE_SUMMARY.md - Master roadmap
- HACKS_ROI.md - High-ROI strategies
- QUERY_MASTERY.md - Query engineering techniques
- scripts/README_ARSENAL.md - All scripts documentation
- nix/INSTALL.md - NixOS aliases installation

### Code References
- scripts/batch_burn.py:45 - Query execution logic
- scripts/salary_intel.py:32 - Salary data structure
- scripts/content_gold_miner.py:67 - Viral scoring algorithm
- nix/phoenix-aliases.nix:12 - pxq function implementation

---

## 🎯 NEXT ACTIONS (Right Now)

1. **Create Search Engine:**
   - Option A: Go to https://console.cloud.google.com/gen-app-builder/engines
   - Option B: Run Python script below

2. **Configure ENGINE_ID:**
   ```bash
   export ENGINE_ID=<your-engine-id>
   echo 'export ENGINE_ID=<your-engine-id>' >> ~/.bashrc
   ```

3. **Test:**
   ```bash
   pxq "test query"
   ```

4. **Execute Strategy:**
   ```bash
   python scripts/strategy_optimizer.py
   # Follow MASTER_EXECUTION_PLAN.md
   ```

---

**Stack Mastery = R$ 10k → $200k/year value** 🔥

Stack mastered. Dinheiro na mesa. Let's execute.
