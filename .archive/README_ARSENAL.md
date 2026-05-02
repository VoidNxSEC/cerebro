# 🔥 ARSENAL DE SCRIPTS - Weaponized Intelligence

**Objetivo:** Transform R$ 10k em créditos GCP → $200k/year em valor de carreira

---

## 📦 SCRIPTS DISPONÍVEIS

### 🎯 TIER S - Maximum ROI (Execute primeiro)

#### 1. **strategy_optimizer.py** ⭐⭐⭐
**O que faz:** Meta-optimizer que analisa situação atual e recomenda MELHOR estratégia de execução.

**Quando usar:** PRIMEIRO script a rodar. Ele te diz o que fazer.

**ROI:** Evita desperdício, maximiza retorno

```bash
python scripts/strategy_optimizer.py
# Output: MASTER_EXECUTION_PLAN.md com plano completo
```

---

#### 2. **salary_intel.py** ⭐⭐⭐
**O que faz:** Gera queries de negotiation ultra-específicas baseado em market data REAL.

**Quando usar:** Quando buscar job OU negociar aumento

**ROI:** R$ 50k-200k (1 negociação bem-sucedida)

**Queries geradas:** ~80

**Custo:** R$ 1.76

```bash
# Básico
python scripts/salary_intel.py

# Com target específico
python scripts/salary_intel.py --current 150000 --target 300000

# Auto-execute batch burn
python scripts/salary_intel.py --execute
```

**Output:**
- `queries_salary_intel.txt` - Queries prontas
- `queries_salary_intel.json` - Metadata

**Sample queries:**
- "Google salary negotiation: levels, bands, e leverage points específicos"
- "Multiple offers: como usar para maximizar final offer sem queimar bridges"
- "Equity negotiation em startup: vesting, strike price, e valuation analysis"

---

#### 3. **content_gold_miner.py** ⭐⭐⭐
**O que faz:** Analisa seus batch_results_*.json e extrai os top 1% insights para viralizar.

**Quando usar:** DEPOIS de processar queries. Transforma outputs em content viral.

**ROI:** 1 post viral = 10k views = 50 recruiter msgs = 5 offers

**Queries geradas:** 0 (analisa existentes)

**Custo:** R$ 0

```bash
# Analisar resultados e gerar content calendar
python scripts/content_gold_miner.py

# Customizar
python scripts/content_gold_miner.py --results-dir . --top-n 50 --output-dir my_content
```

**Output:**
- `content_output/content_calendar_30days.md` - Calendar de posts
- `content_output/gold_insights.json` - Top insights
- `content_output/mining_stats.json` - Estatísticas

**Features:**
- Viral score (0-100) para cada insight
- Categorização automática (technical deep dive, comparison, lessons learned, etc)
- Content ideas prontos para postar
- CTA suggestions

---

#### 4. **trend_predictor.py** ⭐⭐⭐
**O que faz:** Analisa GitHub trending + Hacker News para identificar tech emergente ANTES de mainstream.

**Quando usar:** Ganhar early mover advantage. Ser expert quando tech explode.

**ROI:** 50x (early expertise vale MUITO quando tech vira mainstream)

**Queries geradas:** ~150

**Custo:** R$ 3.30

```bash
# Básico
python scripts/trend_predictor.py

# Auto-execute
python scripts/trend_predictor.py --execute
```

**Output:**
- `queries_trend_prediction.txt` - Queries sobre tech emergente
- `queries_trend_prediction.json` - Metadata com trends detectados

**Como funciona:**
1. Scrape GitHub trending (repos com 100-1000 stars, alto momentum)
2. Scrape Hacker News (posts com >50 points sobre tech nova)
3. Extrai tech names (languages, frameworks, tools)
4. Gera queries deep dive sobre cada tech

**Sample queries:**
- "Zig: overview técnico, use cases, e por que está ganhando tração em 2025"
- "WebAssembly outside browser: casos de uso que vão explodir nos próximos 12 meses"
- "Early signals de tech que vai explodir: pattern recognition"

---

#### 5. **personal_moat_builder.py** ⭐⭐⭐
**O que faz:** Analisa seu perfil (GitHub, skills) e gera queries para construir expertise ÚNICA.

**Quando usar:** Build long-term career moat. Niche expertise que ninguém mais tem.

**ROI:** 200x (expertise única = R$ 200k-500k salary premium)

**Queries geradas:** ~100

**Custo:** R$ 2.20

```bash
# Básico (analisa ~/dev local)
python scripts/personal_moat_builder.py

# Com GitHub
python scripts/personal_moat_builder.py --github seu-username

# Auto-execute
python scripts/personal_moat_builder.py --execute
```

**Output:**
- `queries_personal_moat.txt` - Queries para skills gaps
- `moat_building_strategy.md` - Estratégia completa de 12-24 meses
- `queries_personal_moat.json` - Metadata

**Estratégia:**
1. **Path 1:** Near Expert → Recognized Expert (skills que você já tem 70%)
2. **Path 2:** Power Combos (combinar 2-3 skills em nicho único)
3. **Path 3:** Emerging Tech (early mover em tech nova)

**Sample queries:**
- "Rust: advanced patterns que separam intermediate de expert"
- "NixOS + Kubernetes + Security: arquitetura completa para produção"
- "Como construir personal moat em tech: framework concreto"

---

### 🛠️ TIER A - Core Tools (Já existiam)

#### 6. **generate_queries.py**
**O que faz:** Gera 10k+ queries técnicas automaticamente via templates.

**Quando usar:** Volume. Broad knowledge.

**ROI:** 10x (conhecimento geral)

**Queries geradas:** 10,000

**Custo:** R$ 220

```bash
python scripts/generate_queries.py --count 10000 --output queries.txt
```

---

#### 7. **batch_burn.py**
**O que faz:** Processa queries em paralelo via Discovery Engine.

**Quando usar:** Executar queries geradas.

**Custo:** R$ 0.022 por query

```bash
python scripts/batch_burn.py \
    --file queries.txt \
    --project <your-gcp-project-id> \
    --engine SEU-ENGINE-ID \
    --workers 20
```

**Features:**
- Parallel processing (10-50 workers)
- Progress bar real-time
- Auto-save results JSON
- Cost tracking

---

#### 8. **monitor_credits.py**
**O que faz:** Monitora consumo de créditos via BigQuery em real-time.

**Quando usar:** Acompanhar spending.

```bash
# Real-time
python scripts/monitor_credits.py --project <your-gcp-project-id>

# Snapshot
python scripts/monitor_credits.py --project <your-gcp-project-id> --once
```

---

## 🚀 WORKFLOWS RECOMENDADOS

### Workflow 1: Quick Win (Hoje, 2h)
**Objetivo:** Máximo ROI imediato

```bash
# 1. Get strategy recommendation
python scripts/strategy_optimizer.py

# 2. Generate salary negotiation queries
python scripts/salary_intel.py --current 150000 --target 300000

# 3. Execute
./speedrun.sh burn queries_salary_intel.txt 10

# 4. Monitor
python scripts/monitor_credits.py --once
```

**ROI:** R$ 50k-200k (1 negotiation)

---

### Workflow 2: Content Machine (Semana 1)
**Objetivo:** Visibility → Inbound offers

```bash
# 1. Generate diverse queries
python scripts/generate_queries.py --count 500
python scripts/trend_predictor.py
python scripts/personal_moat_builder.py

# 2. Execute all
for file in queries*.txt; do
    ./speedrun.sh burn $file 20
done

# 3. Mine for content
python scripts/content_gold_miner.py

# 4. Post 1/dia por 30 dias
# (Use content_output/content_calendar_30days.md)
```

**ROI:** 10k-50k views/mês → 5-10 offers

---

### Workflow 3: Moat Building (Mês 1-6)
**Objetivo:** Expertise única, long-term premium

```bash
# 1. Analyze and strategize
python scripts/personal_moat_builder.py
python scripts/trend_predictor.py

# 2. Execute focused queries
./speedrun.sh burn queries_personal_moat.txt 10
./speedrun.sh burn queries_trend_prediction.txt 10

# 3. Document learnings (PKB)
# 4. Build portfolio projects
# 5. Share publicly (blog, talks)
```

**ROI:** R$ 200k-500k salary premium (12-24 meses)

---

### Workflow 4: YOLO (Queimar tudo)
**Objetivo:** Maximum queries, pray for insights

```bash
# Generate 10k queries
python scripts/generate_queries.py --count 10000

# Burn with max workers
./speedrun.sh burn queries.txt 50

# Mine depois
python scripts/content_gold_miner.py
```

**ROI:** R$ 50k-100k (sorte + volume)

---

## 💡 PRO TIPS

### Tip 1: Sempre começar com strategy_optimizer
```bash
python scripts/strategy_optimizer.py
# Leia MASTER_EXECUTION_PLAN.md antes de fazer qualquer coisa
```

### Tip 2: Content mining É OBRIGATÓRIO
```bash
# Depois de QUALQUER batch burn
python scripts/content_gold_miner.py
# Transforma outputs em assets valiosos
```

### Tip 3: Combinar scripts para power combos
```bash
# Trend prediction + Moat building = Early mover em nicho
python scripts/trend_predictor.py
python scripts/personal_moat_builder.py

# Results: Tech emergente + Seu niche = Posicionamento único
```

### Tip 4: Monitorar sempre
```bash
# Em outro terminal
watch -n 60 'python scripts/monitor_credits.py --once'
```

### Tip 5: Auto-execute para speed
```bash
# Todos os scripts tier S suportam --execute
python scripts/salary_intel.py --execute
python scripts/trend_predictor.py --execute
python scripts/personal_moat_builder.py --execute
```

---

## 📊 ROI COMPARISON

| Script | Queries | Cost (BRL) | ROI Potential | Time to Value | Multiple |
|--------|---------|-----------|---------------|---------------|----------|
| salary_intel | 80 | 1.76 | R$ 50k-200k | Immediate | 2000x |
| personal_moat_builder | 100 | 2.20 | R$ 200k-500k | 12-24 months | 200x |
| trend_predictor | 150 | 3.30 | Early mover | 6-12 months | 50x |
| content_gold_miner | 0 | 0 | 5-10 offers | 1-3 months | ∞ |
| generate_queries | 10000 | 220 | R$ 50k-100k | 1-6 months | 10x |

**Recomendação:** Execute Tier S primeiro (ROI 50-2000x) antes de volume (ROI 10x).

---

## ⚡ QUICK START

### Nunca usou? Comece aqui:

```bash
# 1. Strategy (5min)
python scripts/strategy_optimizer.py

# 2. Execute recomendação
# (MASTER_EXECUTION_PLAN.md vai te dizer o que fazer)

# 3. Monitor
python scripts/monitor_credits.py --once
```

---

## 🎯 GOALS & SCRIPTS MAPPING

| Goal | Scripts to Run | Expected Outcome |
|------|---------------|------------------|
| Get job offer ASAP | salary_intel | R$ 50k-200k bump |
| Build visibility | content_gold_miner | 5-10 inbound offers |
| Long-term moat | personal_moat_builder + trend_predictor | R$ 200k-500k premium |
| Learn fast | generate_queries (focused) | Broad knowledge |
| All of the above | strategy_optimizer → follow plan | $200k/year value |

---

**ARSENAL COMPLETO. USE COM SABEDORIA.** 🔥

Cada script foi projetado para ROI máximo. Não queime créditos aleatoriamente.

**Start:** `python scripts/strategy_optimizer.py`
