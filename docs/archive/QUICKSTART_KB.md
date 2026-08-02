# KNOWLEDGE BASE - SPEEDRUN GUIDE

## 🎯 OBJETIVO
Consumir R$ 10k em créditos GCP extraindo valor máximo com Discovery Engine.

## ⚡ QUICK START (5 minutos)

### 1. Indexar seus projetos

```bash
# Via GCS (recomendado para volume)
gsutil -m cp -r ~/dev/* gs://seu-bucket/knowledge/
gsutil -m cp -r ~/projects/* gs://seu-bucket/knowledge/
gsutil -m cp -r ~/.config/nixos/* gs://seu-bucket/knowledge/

# Criar datastore apontando para o bucket
nix develop --command python phantom.py gcp datastores-create knowledge-base \
  --bucket gs://seu-bucket/knowledge
```

### 2. Query básica (queima R$ 0.02 por query)

```bash
nix develop --command python phantom.py gcp search "como configurar nvidia no nixos?"
```

### 3. Batch queries (escala)

```bash
# queries.txt com 100 perguntas
nix develop --command python phantom.py credit loadtest --num-queries 100
```

---

## 🔧 PARÂMETROS COMPLETOS - Discovery Engine

### SearchRequest - Todos os parâmetros disponíveis

```python
from google.cloud import discoveryengine_v1beta as discoveryengine

request = discoveryengine.SearchRequest(
    # REQUIRED
    serving_config="projects/{project}/locations/{location}/collections/default_collection/engines/{engine}/servingConfigs/default_config",
    query="sua pergunta aqui",

    # PAGINATION
    page_size=10,              # Resultados por página (max: 100)
    page_token="token",        # Para próxima página
    offset=0,                  # Skip primeiros N

    # QUERY EXPANSION
    query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
        condition="AUTO"       # AUTO | DISABLED | PINNED
    ),

    # SPELL CORRECTION
    spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
        mode="AUTO"            # AUTO | SUGGESTION_ONLY
    ),

    # CONTENT SEARCH (o importante)
    content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
        # SNIPPET
        snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
            max_snippet_count=5,      # Quantos snippets retornar
            return_snippet=True,       # True/False
            reference_only=False,      # Só referências
        ),

        # SUMMARY (RAG - AQUI QUE QUEIMA CRÉDITO)
        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
            summary_result_count=5,         # Docs para gerar summary (1-10)
            include_citations=True,         # Incluir fontes
            ignore_adversarial_query=True,  # Ignora queries maliciosas
            ignore_non_summary_seeking_query=False,

            # MODEL SPEC
            model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                version="stable"            # stable | preview | gemini-1.5-flash
            ),

            # PROMPT SPEC (customizar prompt)
            model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                preamble="Você é um assistente técnico especializado em NixOS e DevOps. Responda em português."
            ),

            # LANGUAGE
            language_code="pt-BR",          # pt-BR | en | es, etc

            # USE SEMANTIC CHUNKS
            use_semantic_chunks=True,       # Usa chunking semântico
        ),

        # EXTRACTIVE CONTENT (alternativa ao summary)
        extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
            max_extractive_answer_count=1,
            max_extractive_segment_count=3,
            return_extractive_segment_score=True,
        ),

        # SEARCH MODE
        search_result_mode="DOCUMENTS",  # DOCUMENTS | CHUNKS
    ),

    # FACETS (filtros)
    facet_specs=[
        discoveryengine.SearchRequest.FacetSpec(
            facet_key=discoveryengine.SearchRequest.FacetSpec.FacetKey(
                key="category",              # Metadata field
                intervals=[],
                restricted_values=["nix", "python"],
                prefixes=["nixos-"],
                contains=["config"],
            ),
            limit=20,                        # Max facet values
            excluded_filter_keys=["spam"],
            enable_dynamic_position=True,
        )
    ],

    # BOOST (ranking)
    boost_spec=discoveryengine.SearchRequest.BoostSpec(
        condition_boost_specs=[
            discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec(
                condition="category: ANY(nix)",  # Boosting expression
                boost=2.0,                       # Multiplicador (0.0-2.0)
            )
        ]
    ),

    # FILTERS
    filter="category: ANY(nix, python) AND NOT spam",  # SQL-like

    # CANONICAL FILTER (strict filtering)
    canonical_filter="language: en",

    # ORDER BY
    order_by="date DESC",              # date | rating | custom_field

    # USER INFO (para personalização)
    user_info=discoveryengine.UserInfo(
        user_id="user123",
        user_agent="phantom-kb/1.0",
    ),

    # SAFE SEARCH
    safe_search=True,                  # Filter adult content

    # PARAMS (custom key-value)
    params={
        "custom_param": "value"
    },
)

response = client.search(request)

# RESPONSE STRUCTURE
for result in response.results:
    print(f"Document: {result.document.id}")
    print(f"Content: {result.document.derived_struct_data}")
    print(f"Snippet: {result.chunk.content}")

# SUMMARY (RAG result)
if response.summary:
    print(f"Summary: {response.summary.summary_text}")
    for citation in response.summary.summary_with_metadata.citations:
        print(f"Source: {citation.sources}")
```

---

## 💰 OTIMIZAÇÃO DE CUSTOS

### Preços Discovery Engine

| Feature | Preço | Quando usar |
|---------|-------|-------------|
| Search básico | $0.001/query | Busca simples sem RAG |
| Search + Summary (RAG) | $0.004/query | **Máximo valor** |
| Extractive Answers | $0.002/query | Meio termo |
| Recommendations | $0.000625/rec | Não aplicável |

**Para maximizar créditos:** Sempre usar `summary_spec` com `summary_result_count=10`

### Consumo Estimado

```python
# R$ 10k = ~$1,800 USD (câmbio 5.5)
# $1,800 / $0.004 = 450,000 queries com RAG

# Cenários:
# 100 queries/dia = 4,500 dias (12 anos) - LENTO
# 1,000 queries/dia = 450 dias (15 meses) - MODERADO
# 5,000 queries/dia = 90 dias (3 meses) - RÁPIDO ✓
# 10,000 queries/dia = 45 dias (1.5 mês) - TURBO ✓✓
```

---

## 🚀 SCRIPTS PRONTOS

### Script 1: Indexação em massa

```bash
#!/bin/bash
# index_all.sh

BUCKET="gs://seu-bucket/knowledge"
SOURCES=(
    "$HOME/dev"
    "$HOME/projects"
    "$HOME/.config"
    "$HOME/Documents/notes"
    "$HOME/Downloads/courses"
)

for source in "${SOURCES[@]}"; do
    echo "Indexing $source..."
    gsutil -m cp -r "$source" "$BUCKET/"
done

echo "✅ Indexação completa!"
```

### Script 2: Batch queries otimizado

```python
# batch_query.py
from google.cloud import discoveryengine_v1beta as discoveryengine
from concurrent.futures import ThreadPoolExecutor
import time

def query_with_rag(question: str, client, serving_config: str):
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=question,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=10,  # MAX para queimar crédito
                include_citations=True,
                language_code="pt-BR",
                model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                    version="preview"  # Modelo mais caro
                ),
            ),
        ),
    )
    response = client.search(request)
    return {
        "question": question,
        "answer": response.summary.summary_text if response.summary else None,
        "cost": 0.004,  # USD
    }

def batch_process(questions: list[str], workers: int = 10):
    client = discoveryengine.SearchServiceClient()
    serving_config = "projects/{project}/locations/global/collections/default_collection/engines/{engine}/servingConfigs/default_config"

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(
            lambda q: query_with_rag(q, client, serving_config),
            questions
        ))

    total_cost = sum(r["cost"] for r in results)
    print(f"✅ Processed {len(results)} queries")
    print(f"💰 Cost: ${total_cost:.2f} USD")
    return results

# USO
questions = [
    "Como configurar Nvidia no NixOS?",
    "Melhor prática para flake.nix?",
    # ... adicionar 10,000 perguntas
]

results = batch_process(questions, workers=50)
```

### Script 3: Auto-generator de queries

```python
# generate_queries.py
import itertools

TEMPLATES = [
    "Como configurar {tech} no {os}?",
    "Melhor prática para {concept} em {language}?",
    "Debug de {error} em {framework}",
    "Diferença entre {optionA} e {optionB}",
    "Exemplo de {pattern} com {tech}",
    "Performance tuning de {service}",
    "Segurança em {component}",
    "{tech} vs {alternative}: qual escolher?",
]

TECH = ["Docker", "Kubernetes", "Terraform", "Ansible", "Nix"]
OS = ["NixOS", "Ubuntu", "Arch", "Debian"]
LANGUAGES = ["Python", "Rust", "Go", "JavaScript", "Nix"]
ERRORS = ["segfault", "timeout", "OOM", "deadlock", "race condition"]
FRAMEWORKS = ["Django", "FastAPI", "React", "Vue", "Axum"]

def generate_queries(count: int = 10000):
    queries = []

    # Template 1
    for tech, os in itertools.product(TECH, OS):
        queries.append(f"Como configurar {tech} no {os}?")

    # Template 2
    concepts = ["dependency injection", "middleware", "caching", "logging", "testing"]
    for concept, lang in itertools.product(concepts, LANGUAGES):
        queries.append(f"Melhor prática para {concept} em {lang}?")

    # Template 3
    for error, framework in itertools.product(ERRORS, FRAMEWORKS):
        queries.append(f"Debug de {error} em {framework}")

    # ... continuar gerando até 10k

    return queries[:count]

# Gerar 10k queries
queries = generate_queries(10000)
with open("queries_10k.txt", "w") as f:
    f.write("\n".join(queries))

print(f"✅ Generated {len(queries)} queries")
print(f"💰 Estimated cost: ${len(queries) * 0.004} USD")
```

---

## 📊 MONITORAMENTO

### Script 4: Dashboard real-time

```python
# monitor.py
from google.cloud import bigquery
import time

def get_credit_status():
    client = bigquery.Client()

    query = """
    SELECT
        COUNT(*) as total_queries,
        SUM(cost) as total_cost,
        SUM(credits.amount) as credits_used
    FROM `{project}.{dataset}.gcp_billing_export_v1_*`
    WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND service.description = 'Discovery Engine'
        AND credits.id = 'seu-credit-id'
    """

    results = client.query(query).result()
    for row in results:
        return {
            "queries": row.total_queries,
            "cost_usd": row.total_cost,
            "credits_used_brl": row.credits_used * 5.5,
        }

# Loop de monitoramento
while True:
    status = get_credit_status()
    print(f"""
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    💰 CREDIT BURN STATUS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Queries: {status['queries']:,}
    Cost: ${status['cost_usd']:.2f} USD
    Credits: R$ {status['credits_used_brl']:.2f}
    Remaining: R$ {10000 - status['credits_used_brl']:.2f}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    time.sleep(300)  # Update a cada 5min
```

---

## 🎯 PLANO DE EXECUÇÃO (Speedrun)

### Fase 1: Indexação (DIA 1)
```bash
# 1. Criar bucket
gsutil mb -l us-central1 gs://phoenix-knowledge

# 2. Upload bulk
bash index_all.sh

# 3. Criar datastore
python phantom.py gcp datastores-create phoenix-kb --bucket gs://phoenix-knowledge
```

### Fase 2: Teste (DIA 1)
```bash
# Query manual
python phantom.py gcp search "teste"

# Batch pequeno
python batch_query.py --queries 10
```

### Fase 3: SCALE (DIA 2-30)
```bash
# Gerar 10k queries
python generate_queries.py

# Processar em paralelo (50 workers)
python batch_query.py --file queries_10k.txt --workers 50

# Monitorar
python monitor.py
```

---

## 🔥 ATALHOS

```bash
# Alias úteis (.bashrc)
alias pk='nix develop --command python phantom.py'
alias pkq='pk gcp search'
alias pks='pk credit audit'
alias pkb='pk credit loadtest'

# Uso:
pkq "como fazer X?"
pkb --num-queries 1000
pks
```

---

## 📝 QUERIES DE ALTO VALOR

### Carreira
- "Melhores práticas de system design para entrevistas"
- "Como demonstrar expertise em {tech} no LinkedIn"
- "Projetos open source para portfolio de {role}"

### NixOS
- "Configuração completa de {service} no NixOS"
- "Flake.nix para desenvolvimento {language}"
- "Debug de {error} no nixos-rebuild"

### DevOps
- "CI/CD pipeline otimizado para {tech}"
- "Monitoring stack com {tools}"
- "Disaster recovery para {service}"

### Code
- "Refactoring de {pattern} em {language}"
- "Performance optimization para {scenario}"
- "Security best practices em {framework}"

---

## ⚡ MAXIMA VELOCIDADE

Para consumir R$ 10k em **30 dias**:
- 10,000 queries/dia = 333 queries/hora = 5.5 queries/minuto
- Com 50 workers paralelos = 1 query a cada 11 segundos

```python
# Ultra-fast mode
python batch_query.py \
    --file queries_10k.txt \
    --workers 100 \
    --rate-limit 10  # queries/segundo
```

**ATENÇÃO:** Discovery Engine tem rate limits. Testar incrementalmente.

---

## 🎓 EXTRAÇÃO DE VALOR

Salvar todas as respostas:
```python
# Em batch_query.py, adicionar:
import json

with open("knowledge_extracted.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Depois: indexar as próprias respostas de volta!
# Loop de valor: Query → Answer → Index → Query melhor
```

---

**PRÓXIMO PASSO:** Qual você quer executar primeiro?
1. Indexar seus projetos
2. Gerar 10k queries
3. Rodar batch test
4. Setup monitoring
