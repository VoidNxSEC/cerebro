# 📚 DOCUMENTAÇÃO COMPLETA - Burn Credits GCP

**Versão:** 1.0
**Data:** 2025-12-29
**Projeto:** gen-lang-client-0530325234
**Créditos Totais:** R$ 10.079,11

---

## 📖 Índice

1. [Visão Geral](#visão-geral)
2. [Contexto e Problema](#contexto-e-problema)
3. [Análise Técnica](#análise-técnica)
4. [Solução Implementada](#solução-implementada)
5. [Guia de Instalação](#guia-de-instalação)
6. [Guia de Uso](#guia-de-uso)
7. [Validação Financeira](#validação-financeira)
8. [Troubleshooting](#troubleshooting)
9. [Arquitetura](#arquitetura)
10. [Referências](#referências)

---

## 1. Visão Geral

### 1.1 Objetivo

Consumir programaticamente R$ 10.079,11 em créditos promocionais do Google Cloud Platform de forma auditável e eficiente, garantindo que:
- ✅ Créditos sejam aplicados corretamente (não cobrar no cartão)
- ✅ Consumo seja rastreável via BigQuery
- ✅ APIs corretas sejam utilizadas

### 1.2 Créditos Disponíveis

| Crédito | Valor | Elegibilidade | Script Principal |
|---------|-------|---------------|------------------|
| GenAI App Builder Trial | R$ 6.432,54 | Discovery Engine APIs | `burn_credits_loadtest.py` |
| Dialogflow CX Trial | R$ 3.646,57 | Dialogflow CX Sessions | `burn_dialogflow_cx.py` |

### 1.3 Resultados Alcançados

- ✅ Identificado método correto para Grounded Generation
- ✅ Validado consumo via SearchServiceClient
- ❌ Descartado GroundedGenerationServiceClient (não implementado)
- ✅ Criados scripts de load test paralelizados
- ✅ Implementada auditoria via BigQuery
- ✅ Setup 100% via CLI (sem console)

---

## 2. Contexto e Problema

### 2.1 Problema Inicial

**Arquivo:** `grounded_generation.py` e `main.py`

```python
# ❌ FALHA: HTTP 501 - Method not found
from google.cloud import discoveryengine_v1beta as discoveryengine

client = discoveryengine.GroundedGenerationServiceClient()
response = client.generate_grounded_content(request)
```

**Erro Observado:**
```
❌ ERRO: Method not found.
```

### 2.2 Hipóteses Testadas

| Hipótese | Teste | Resultado |
|----------|-------|-----------|
| Problema de location (global vs regional) | Testado: global, us, us-central1 | ❌ Todas falharam |
| Versão da API (v1 vs v1beta) | Testado ambas | ❌ Ambas falharam (501) |
| API não habilitada | `gcloud services list --enabled` | ✅ API habilitada |
| Permissões insuficientes | Retornaria 403, não 501 | ❌ Não é permissão |
| Endpoint incorreto | Verificado: discoveryengine.googleapis.com | ✅ Endpoint correto |

**Conclusão:** O método `generate_grounded_content()` existe no SDK Python mas **NÃO está implementado no servidor** Google Cloud (HTTP 501 = Not Implemented).

### 2.3 Correlação com Relatório Técnico

**Relatório fornecido pelo usuário** (baseado em Gemini Deep Research):

- **Seção 3.1:** SearchServiceClient com summary_spec → ✅ FUNCIONA
- **Seção 3.2:** GroundedGenerationServiceClient → ❌ NÃO FUNCIONA
- **Seção 4:** Dialogflow CX → ✅ VALIDADO
- **Seção 5.2:** BigQuery Audit → ✅ IMPLEMENTADO

**Lição:** Relatórios/documentação podem estar desatualizados. Sempre validar com testes práticos.

---

## 3. Análise Técnica

### 3.1 API Correta: SearchServiceClient

**Descoberta:** "Grounded Generation" acontece via `SearchServiceClient` com `content_search_spec.summary_spec`, não via `GroundedGenerationServiceClient`.

#### 3.1.1 Anatomia da Requisição Correta

```python
from google.cloud import discoveryengine_v1beta as discoveryengine

# ✅ Client correto
client = discoveryengine.SearchServiceClient()

# ✅ Serving config path
serving_config = (
    f"projects/{project_id}/locations/{location}/"
    f"collections/default_collection/dataStores/{data_store_id}/"
    f"servingConfigs/default_config"
)

# ✅ Request com Grounded Generation
request = discoveryengine.SearchRequest(
    serving_config=serving_config,
    query="Sua pergunta aqui",
    page_size=10,

    # CRÍTICO: Isto ativa Grounded Generation!
    content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
        # Summary = AI generativa com citações
        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
            summary_result_count=5,
            include_citations=True,
            ignore_adversarial_query=True,
            ignore_non_summary_seeking_query=True,
        ),
        # Snippets extrativos (bonus)
        snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
            return_snippet=True
        ),
    ),
)

response = client.search(request)
```

#### 3.1.2 Por que isso é "Grounded Generation"?

1. **Grounding:** Resposta fundamentada nos documentos do Data Store
2. **Generation:** Usa modelo generativo (Gemini) para sintetizar resposta
3. **Citations:** Retorna fontes/citações dos documentos utilizados

**Diferença vs. Gemini API pura:**
- Gemini API: Resposta sem garantia de fonte
- Grounded Generation: Resposta SEMPRE baseada em documentos específicos

#### 3.1.3 SKUs e Custos

| Operação | SKU | Custo | Elegível para Crédito |
|----------|-----|-------|----------------------|
| Search Standard | Search API Request Count - Standard | $2.50/1k queries | ✅ Sim |
| Search Enterprise | Search API Request Count - Enterprise | $4.00/1k queries | ✅ Sim |
| Grounding (add-on) | Grounded Generation API | $2.50/1k queries | ✅ Sim |

**Nossa configuração:** Search Enterprise ($4.00/1k) + Grounding incluso

### 3.2 Dialogflow CX

#### 3.2.1 Modelo de Cobrança

```python
from google.cloud import dialogflowcx_v3 as dialogflow

client = dialogflow.SessionsClient()

# Cada detect_intent = 1 cobrança
response = client.detect_intent(
    session=session_path,
    query_input=query_input
)
```

**Custos:**
- Text session: ~$0.007 por requisição
- Audio session: ~$0.06 por minuto
- Streaming: Variável

#### 3.2.2 SKUs Elegíveis

- `A1CC-751A-CDCC`: Text session
- Audio processing (vários SKUs)

---

## 4. Solução Implementada

### 4.1 Arquivos Criados

#### 4.1.1 Scripts Principais (Use Estes!)

| Arquivo | Função | Status | Uso |
|---------|--------|--------|-----|
| `test_credits.py` | Teste único (1 query) | ✅ VALIDADO | Validação inicial |
| `burn_credits_loadtest.py` | Load test GenAI paralelo | ✅ PRONTO | Consumo massivo |
| `burn_dialogflow_cx.py` | Load test Dialogflow CX | ✅ PRONTO | Dialogflow sessions |
| `audit_credits_bigquery.py` | Auditoria financeira | ✅ PRONTO | Validação de custos |

#### 4.1.2 Scripts de Setup

| Arquivo | Função | Status |
|---------|--------|--------|
| `setup_bigquery_export.sh` | Setup automático (API REST) | ✅ PRONTO |
| `setup_bigquery_simple.sh` | Setup semi-automático | ✅ PRONTO |
| `check_billing_table.sh` | Verificar status | ✅ PRONTO |

#### 4.1.3 Utilitários

| Arquivo | Função | Status |
|---------|--------|--------|
| `validate_credits.py` | Validar auth e billing | ✅ FUNCIONAL |
| `manage_datastores.py` | CRUD data stores | ✅ FUNCIONAL |
| `import_documents.py` | Upload documentos | ✅ FUNCIONAL |

#### 4.1.4 Deprecated (Não Use!)

| Arquivo | Razão | Substituir Por |
|---------|-------|----------------|
| `main.py` | Usa GroundedGenerationServiceClient | `test_credits.py` |
| `grounded_generation.py` | HTTP 501 error | `burn_credits_loadtest.py` |
| `test_grounded_v1.py` | Apenas diagnóstico | - |

#### 4.1.5 Documentação

| Arquivo | Conteúdo |
|---------|----------|
| `README.md` | Visão geral do projeto |
| `QUICK_START.md` | Guia rápido de uso |
| `RESUMO_EXECUTIVO.md` | Análise técnica detalhada |
| `DOCUMENTATION.md` | Este arquivo (completo) |

### 4.2 Estrutura do Projeto

```
burn-credits/
│
├── 📚 Documentação
│   ├── README.md
│   ├── QUICK_START.md
│   ├── RESUMO_EXECUTIVO.md
│   └── DOCUMENTATION.md
│
├── ✅ Scripts Validados
│   ├── test_credits.py
│   ├── burn_credits_loadtest.py
│   ├── burn_dialogflow_cx.py
│   └── audit_credits_bigquery.py
│
├── 🔧 Setup & Utilitários
│   ├── setup_bigquery_export.sh
│   ├── setup_bigquery_simple.sh
│   ├── check_billing_table.sh
│   ├── validate_credits.py
│   ├── manage_datastores.py
│   └── import_documents.py
│
├── ❌ Deprecated
│   ├── main.py
│   ├── grounded_generation.py
│   └── test_grounded_v1.py
│
├── 📁 Configuração
│   ├── flake.nix
│   ├── .env (gitignored)
│   └── .billing_export.env (auto-gerado)
│
└── 📂 Dados
    └── knowledge_base/
```

---

## 5. Guia de Instalação

### 5.1 Pré-requisitos

- NixOS ou Nix package manager
- Google Cloud SDK (`gcloud`)
- Billing account configurada no projeto
- Python 3.x (fornecido pelo Nix)

### 5.2 Setup Inicial

```bash
# 1. Clone/navegue para o diretório
cd /home/kernelcore/dev/Projects/burn-credits

# 2. Entre no ambiente Nix
nix develop

# 3. Autentique no GCP
gcloud auth login
gcloud auth application-default login

# 4. Configure projeto
gcloud config set project gen-lang-client-0530325234

# 5. Habilite APIs necessárias
gcloud services enable discoveryengine.googleapis.com
gcloud services enable dialogflow.googleapis.com
gcloud services enable bigquery.googleapis.com
```

### 5.3 Configuração de Variáveis

#### 5.3.1 No flake.nix (Recomendado)

```nix
shellHook = ''
  export GOOGLE_CLOUD_PROJECT_ID="gen-lang-client-0530325234"
  export GOOGLE_CLOUD_LOCATION="global"
  export DATA_STORE_ID="ds-app-v4-5e020c93"

  # Para Dialogflow CX (configure depois de criar agent)
  export DIALOGFLOW_AGENT_ID="seu-agent-id"
  export DIALOGFLOW_LOCATION="us-central1"

  # Para BigQuery (auto-detectado por setup scripts)
  export BILLING_EXPORT_DATASET="billing_export"
  export BILLING_EXPORT_TABLE="gcp_billing_export_v1_..."
'';
```

#### 5.3.2 Via .env (Alternativa)

```bash
# .env
export GOOGLE_CLOUD_PROJECT_ID="gen-lang-client-0530325234"
export DATA_STORE_ID="ds-app-v4-5e020c93"
# ... outras vars

# Load com:
source .env
```

### 5.4 Setup BigQuery Export

```bash
# Opção 1: Automático (via API)
./setup_bigquery_export.sh

# Opção 2: Semi-automático (mais compatível)
./setup_bigquery_simple.sh

# Verificar status
./check_billing_table.sh
```

### 5.5 Verificação

```bash
# Valida auth e billing
python validate_credits.py

# Lista data stores
python manage_datastores.py

# Teste básico (1 query)
python test_credits.py
```

**Saída esperada:**
```
✅ QUERY EXECUTADA COM SUCESSO!
💰 CRÉDITO CONSUMIDO:
   • Search Enterprise Edition: $4.00 / 1,000 queries
   • Esta query: ~$0.004
```

---

## 6. Guia de Uso

### 6.1 Fluxo de Validação Segura

#### Passo 1: Teste Inicial

```bash
# 1 query única (custo: $0.004)
python test_credits.py
```

**Verificações:**
- ✅ Código retorna 200 OK?
- ✅ Resposta foi gerada (mesmo que vazia)?
- ⚠️ Erro? Veja [Troubleshooting](#troubleshooting)

#### Passo 2: Aguardar Billing Sync

**Tempo:** 24-48 horas

**Por quê?** Sistema de billing do GCP não é em tempo real.

#### Passo 3: Validar com BigQuery

```bash
# Configure se ainda não fez
source .billing_export.env

# Execute auditoria
python audit_credits_bigquery.py
```

**Interprete:**
```
✅ net_cost_to_wallet = $0.00
   → Crédito aplicado corretamente!
   → Pode escalar com segurança

⚠️  net_cost_to_wallet > $0.00
   → VOCÊ ESTÁ SENDO COBRADO!
   → NÃO escale! Revise arquitetura
```

#### Passo 4: Escalar Consumo

```bash
# Pequeno (100 queries = $0.40)
NUM_QUERIES=100 python burn_credits_loadtest.py

# Médio (500 queries = $2.00)
NUM_QUERIES=500 MAX_WORKERS=10 python burn_credits_loadtest.py

# Total (1,600 queries = $6.40 ≈ todo crédito GenAI)
NUM_QUERIES=1600 MAX_WORKERS=15 python burn_credits_loadtest.py
```

### 6.2 Load Test GenAI App Builder

#### 6.2.1 Configuração Básica

```bash
export DATA_STORE_ID='ds-app-v4-5e020c93'
export NUM_QUERIES=500
export MAX_WORKERS=10

python burn_credits_loadtest.py
```

#### 6.2.2 Parâmetros Avançados

| Variável | Default | Descrição | Recomendação |
|----------|---------|-----------|--------------|
| `NUM_QUERIES` | 100 | Total de queries | 100-1600 |
| `MAX_WORKERS` | 10 | Threads paralelas | 5-15 |
| `AUTO_CONFIRM` | false | Pular confirmação | true (scripts) |
| `SEARCH_QUERY` | (sample) | Query customizada | Opcional |

#### 6.2.3 Exemplo: Queimar R$ 100 de Créditos

```bash
# R$ 100 ≈ $18 USD ≈ 4,500 queries
NUM_QUERIES=4500 MAX_WORKERS=12 python burn_credits_loadtest.py
```

**Tempo estimado:** ~1-2 horas (QPS médio: ~3)

#### 6.2.4 Monitoramento em Tempo Real

Durante execução, você verá:

```
[500/1000] ✅ 498 | ❌ 2 | QPS: 5.23 | Custo: $2.00
            ↑      ↑       ↑           ↑
         Sucesso Falhas Queries/s   $ acumulado
```

**Sinais de Alerta:**
- Falhas > 10%: Reduza MAX_WORKERS
- QPS < 1: Aumente MAX_WORKERS
- Quota exceeded: Pause e retry

### 6.3 Load Test Dialogflow CX

#### 6.3.1 Pré-requisito: Criar Agent

1. Acesse: https://dialogflow.cloud.google.com/cx/
2. Crie um novo Agent
3. Configure intents básicos (ou use template)
4. Copie Agent ID (formato UUID)

#### 6.3.2 Configuração

```bash
export DIALOGFLOW_AGENT_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
export DIALOGFLOW_LOCATION='us-central1'
export NUM_CONVERSATIONS=100
export MAX_WORKERS=5

python burn_dialogflow_cx.py
```

#### 6.3.3 Estimativas

| Conversas | Interações | Custo USD | Custo BRL | Tempo (5 workers) |
|-----------|-----------|-----------|-----------|-------------------|
| 50        | ~150      | $1.05     | R$ 5.78   | ~5 min            |
| 100       | ~300      | $2.10     | R$ 11.55  | ~10 min           |
| 500       | ~1,500    | $10.50    | R$ 57.75  | ~50 min           |
| 10,000    | ~30,000   | $210.00   | R$ 1,155  | ~16 horas         |

#### 6.3.4 Background Execution

```bash
# Executa em background
nohup python burn_dialogflow_cx.py > dialogflow.log 2>&1 &

# Monitor progresso
tail -f dialogflow.log

# Verificar processos
ps aux | grep burn_dialogflow

# Matar se necessário
pkill -f burn_dialogflow_cx.py
```

### 6.4 Auditoria Financeira

#### 6.4.1 Configuração BigQuery

```bash
# Se ainda não configurou
./setup_bigquery_simple.sh

# Load configs
source .billing_export.env

# Ou configure manualmente
export BILLING_EXPORT_DATASET='billing_export'
export BILLING_EXPORT_TABLE='gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX'
```

#### 6.4.2 Executar Auditoria

```bash
# Padrão: últimos 7 dias
python audit_credits_bigquery.py

# Customizar período
AUDIT_DAYS=30 python audit_credits_bigquery.py
```

#### 6.4.3 Interpretação dos Resultados

**Campos Críticos:**

```sql
gross_cost: Custo bruto (antes do crédito)
credit_amount: Valor do crédito aplicado (negativo)
net_cost_to_wallet: O que VOCÊ PAGOU (gross + credit)
```

**Cenários:**

```
Cenário 1: Sucesso Total
  gross_cost = $2.50
  credit_amount = -$2.50
  net_cost_to_wallet = $0.00
  → ✅ Crédito aplicado 100%!

Cenário 2: Cobrança Parcial
  gross_cost = $5.00
  credit_amount = -$2.50
  net_cost_to_wallet = $2.50
  → ⚠️ Você pagou $2.50!
  → Verifique SKU: serviço não elegível?

Cenário 3: Sem Crédito
  gross_cost = $10.00
  credit_amount = $0.00
  net_cost_to_wallet = $10.00
  → ❌ Crédito NÃO aplicado!
  → PARE! Revise arquitetura
```

#### 6.4.4 Query Manual (BigQuery Console)

Se preferir usar o console:

```sql
SELECT
  invoice.month,
  service.description AS service_name,
  sku.description AS sku_name,

  credits.name AS credit_name,

  cost AS gross_cost,
  credits.amount AS credit_amount,
  (cost + IFNULL(credits.amount, 0)) AS net_cost,

  usage_start_time
FROM
  `gen-lang-client-0530325234.billing_export.gcp_billing_export_v1_*`,
  UNNEST(credits) AS credits
WHERE
  (credits.name LIKE '%GenAI App Builder%' OR
   credits.name LIKE '%Dialogflow CX%')
  AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
ORDER BY
  usage_start_time DESC
LIMIT 100
```

---

## 7. Validação Financeira

### 7.1 Modelo de Billing do GCP

#### 7.1.1 Como Funciona

```
[Uso da API] → [Cobrança Bruta] → [Aplicação de Crédito] → [Cobrança Líquida]
      ↓               ↓                    ↓                        ↓
   1 query        +$0.004            -$0.004                   $0.00
```

**IMPORTANTE:** Você SEMPRE é "cobrado" primeiro. O crédito é aplicado depois como "refund".

#### 7.1.2 Latência do Sistema

| Sistema | Latência | Confiabilidade |
|---------|----------|----------------|
| Console Billing | 24-48h | Baixa (agregado) |
| BigQuery Export | 6-24h | Alta (granular) |
| Cloud Billing API | ~1h | Média (via código) |

**Recomendação:** BigQuery Export é a fonte da verdade.

### 7.2 SKUs Elegíveis

#### 7.2.1 GenAI App Builder (R$ 6.432,54)

| SKU ID | Descrição | Custo | Elegível |
|--------|-----------|-------|----------|
| Vertex AI Search: Search API Request Count - Standard | Busca básica | $2.50/1k | ✅ |
| Vertex AI Search: Search API Request Count - Enterprise | Busca + AI | $4.00/1k | ✅ |
| Grounded Generation API | Respostas grounded | $2.50/1k | ✅ |
| Document AI Parser (integrado) | Parsing automático | Variável | ✅ |
| Storage (índice) | Até 10 GiB | Grátis | ✅ |

#### 7.2.2 Dialogflow CX (R$ 3.646,57)

| SKU ID | Descrição | Custo | Elegível |
|--------|-----------|-------|----------|
| A1CC-751A-CDCC | Text session | $0.007/req | ✅ |
| Audio session | Áudio processado | $0.06/min | ✅ |
| Generative Fallbacks | LLM integrado | Variável | ⚠️ Verificar |

### 7.3 Validação Cruzada

#### 7.3.1 Métodos de Validação

```bash
# Método 1: BigQuery (MAIS CONFIÁVEL)
python audit_credits_bigquery.py

# Método 2: Console Web
# https://console.cloud.google.com/billing/

# Método 3: CLI
gcloud billing accounts list
gcloud billing projects describe gen-lang-client-0530325234
```

#### 7.3.2 Checklist de Validação

Antes de escalar, confirme:

- [ ] `test_credits.py` executou com sucesso (200 OK)
- [ ] BigQuery Export configurado
- [ ] Aguardou 24-48h desde primeira query
- [ ] Executou `audit_credits_bigquery.py`
- [ ] `net_cost_to_wallet = $0.00` confirmado
- [ ] SKU observado está na lista de elegíveis
- [ ] Credit name contém "GenAI App Builder" ou "Dialogflow CX"

**Se TODOS checados:** ✅ Pode escalar com segurança!

---

## 8. Troubleshooting

### 8.1 Erros Comuns

#### 8.1.1 "Method not found" (HTTP 501)

**Arquivo afetado:** `grounded_generation.py`, `main.py`

**Sintoma:**
```
❌ ERRO: Method not found.
```

**Causa:** Usando `GroundedGenerationServiceClient.generate_grounded_content()` que não está implementado.

**Solução:**
```bash
# NÃO use:
python grounded_generation.py  # ❌
python main.py                  # ❌

# USE:
python test_credits.py         # ✅
python burn_credits_loadtest.py # ✅
```

#### 8.1.2 "DATA_STORE_ID não configurado"

**Sintoma:**
```
❌ DATA_STORE_ID não configurado!
```

**Solução:**
```bash
# Listar data stores existentes
python manage_datastores.py

# Configurar
export DATA_STORE_ID='ds-app-v4-5e020c93'

# Ou criar novo
python manage_datastores.py
# Escolha 'y' quando perguntado
```

#### 8.1.3 "DIALOGFLOW_AGENT_ID não configurado"

**Sintoma:**
```
❌ DIALOGFLOW_AGENT_ID não configurado!
```

**Solução:**
```bash
# 1. Crie agent em:
# https://dialogflow.cloud.google.com/cx/

# 2. Copie Agent ID (UUID)

# 3. Configure
export DIALOGFLOW_AGENT_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
export DIALOGFLOW_LOCATION='us-central1'
```

#### 8.1.4 "Permission Denied" (HTTP 403)

**Sintoma:**
```
❌ Erro: 403 Permission denied
```

**Causas possíveis:**
1. API não habilitada
2. Service account sem permissões
3. Billing account não vinculada

**Solução:**
```bash
# 1. Habilitar APIs
gcloud services enable discoveryengine.googleapis.com
gcloud services enable dialogflow.googleapis.com

# 2. Verificar permissões
gcloud projects get-iam-policy gen-lang-client-0530325234

# 3. Verificar billing
gcloud billing projects describe gen-lang-client-0530325234
```

#### 8.1.5 "Quota exceeded"

**Sintoma:**
```
❌ Quota exceeded for quota metric 'discoveryengine.googleapis.com/...'
```

**Solução:**
```bash
# Reduzir paralelização
MAX_WORKERS=5 python burn_credits_loadtest.py

# Adicionar delay entre lotes
# Edite o script e adicione: time.sleep(1) no loop

# Verificar quotas
gcloud services list --enabled | grep discovery
# Veja quotas em: https://console.cloud.google.com/iam-admin/quotas
```

#### 8.1.6 BigQuery: "Table not found"

**Sintoma:**
```
❌ Table not found: billing_export.gcp_billing_export_v1_...
```

**Causa:** Tabela ainda não foi criada (latência do GCP)

**Solução:**
```bash
# Verificar status
./check_billing_table.sh

# Listar tabelas manualmente
bq ls billing_export

# Se vazio, aguarde 24-48h ou reconfigure export
./setup_bigquery_simple.sh
```

### 8.2 Problemas de Validação Financeira

#### 8.2.1 net_cost > $0 (Você está sendo cobrado!)

**Diagnóstico:**
```python
# audit_credits_bigquery.py mostrou:
net_cost_to_wallet = $5.00  # ⚠️ PROBLEMA!
```

**Investigação:**
```sql
-- Execute no BigQuery
SELECT
  sku.description,
  credits.name,
  cost,
  credits.amount
FROM `billing_export.gcp_billing_export_v1_*`,
UNNEST(credits) AS credits
WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
```

**Possíveis causas:**
1. SKU consumido não é elegível (compare com seção 7.2)
2. Crédito expirou
3. Crédito já esgotado
4. API errada sendo usada

**Ação:**
```bash
# 1. PARE de consumir imediatamente
# 2. Revise qual script/API usou
# 3. Confirme SKU na lista de elegíveis
# 4. Entre em contato com suporte GCP se necessário
```

#### 8.2.2 Nenhum dado no BigQuery

**Sintoma:**
```
⚠️  NENHUMA TRANSAÇÃO COM CRÉDITO ENCONTRADA
```

**Possíveis causas:**
1. Latência (aguarde 24-48h)
2. Export não configurado
3. Ainda não consumiu nada
4. Crédito não está sendo aplicado

**Diagnóstico:**
```bash
# 1. Verificar se tabela existe
bq ls billing_export

# 2. Ver TODAS as transações (sem filtro de crédito)
bq query --use_legacy_sql=false '
SELECT * FROM `billing_export.gcp_billing_export_v1_*`
WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
LIMIT 10
'

# 3. Se vazio: aguarde ou reconfigure export
```

### 8.3 Problemas de Performance

#### 8.3.1 QPS muito baixo (< 1)

**Sintoma:**
```
[100/1000] QPS: 0.5
```

**Causas:**
- MAX_WORKERS muito baixo
- Rate limiting do servidor
- Latência de rede alta

**Solução:**
```bash
# Aumentar workers
MAX_WORKERS=15 python burn_credits_loadtest.py

# Verificar latência
ping discoveryengine.googleapis.com
```

#### 8.3.2 Taxa de falha alta (> 10%)

**Sintoma:**
```
[500/1000] ✅ 450 | ❌ 50
```

**Causas:**
- Quota exceeded
- Workers demais (race conditions)
- Problema transitório na API

**Solução:**
```bash
# Reduzir workers
MAX_WORKERS=5 python burn_credits_loadtest.py

# Verificar logs de erro no output
# Se persistir: reporte issue
```

---

## 9. Arquitetura

### 9.1 Fluxo de Dados

```
┌─────────────────┐
│  Python Script  │
│  (test_credits) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  discoveryengine.SearchServiceClient│
│  + content_search_spec.summary_spec │
└────────┬───────────────────────────┘
         │
         ▼ HTTPS
┌─────────────────────────────────────┐
│  discoveryengine.googleapis.com     │
│  (Google Cloud Backend)             │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Billing System                     │
│  1. Registra custo bruto            │
│  2. Aplica promotional credit       │
│  3. Calcula net cost                │
└────────┬────────────────────────────┘
         │
         ▼ (6-24h latência)
┌─────────────────────────────────────┐
│  BigQuery Export Table              │
│  - gross_cost                       │
│  - credit_amount                    │
│  - net_cost_to_wallet               │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  audit_credits_bigquery.py          │
│  (Validação Financeira)             │
└─────────────────────────────────────┘
```

### 9.2 Componentes

#### 9.2.1 Frontend (Scripts Python)

| Script | Client | Função |
|--------|--------|--------|
| `test_credits.py` | SearchServiceClient | Teste único |
| `burn_credits_loadtest.py` | SearchServiceClient | Load test paralelo |
| `burn_dialogflow_cx.py` | SessionsClient | Dialogflow sessions |

#### 9.2.2 APIs Google Cloud

| API | Endpoint | Função |
|-----|----------|--------|
| Discovery Engine | discoveryengine.googleapis.com | Search + Grounded Gen |
| Dialogflow CX | {location}-dialogflow.googleapis.com | Chat sessions |
| BigQuery | bigquery.googleapis.com | Data warehouse |
| Cloud Billing | cloudbilling.googleapis.com | Billing management |

#### 9.2.3 Backend (Auditoria)

```
BigQuery Dataset: billing_export
  └── Table: gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX
       ├── Schema: ~50 campos
       ├── Partitioned by: usage_start_time
       └── Updated: Diariamente
```

### 9.3 Segurança

#### 9.3.1 Autenticação

```bash
# Application Default Credentials (ADC)
gcloud auth application-default login

# Usado automaticamente pelos scripts Python via:
from google.auth import default
credentials, project = default()
```

#### 9.3.2 Permissões Necessárias

| Recurso | Role Mínima | Motivo |
|---------|-------------|--------|
| Discovery Engine | `roles/discoveryengine.editor` | Criar/usar data stores |
| Dialogflow CX | `roles/dialogflow.client` | Invocar agents |
| BigQuery | `roles/bigquery.user` | Query dados de billing |
| Billing | `roles/billing.viewer` | Ver billing info |

#### 9.3.3 Secrets Management

**Não commitados no Git:**
- `.env`
- `.billing_export.env`
- Service account keys (não usamos)

**Commitados (OK):**
- `flake.nix` (environment vars não-sensíveis)
- Scripts Python (código público)

---

## 10. Referências

### 10.1 Documentação Oficial Google Cloud

#### 10.1.1 Discovery Engine / Vertex AI Search

- [Overview](https://cloud.google.com/generative-ai-app-builder/docs/overview)
- [Search API Reference](https://cloud.google.com/generative-ai-app-builder/docs/reference/rpc/google.cloud.discoveryengine.v1)
- [Pricing](https://cloud.google.com/generative-ai-app-builder/pricing)

#### 10.1.2 Dialogflow CX

- [Documentation](https://cloud.google.com/dialogflow/cx/docs)
- [Sessions API](https://cloud.google.com/dialogflow/cx/docs/reference/rest/v3/projects.locations.agents.sessions)
- [Pricing](https://cloud.google.com/dialogflow/pricing#dialogflow-cx)

#### 10.1.3 BigQuery

- [Export Billing Data](https://cloud.google.com/billing/docs/how-to/export-data-bigquery)
- [Billing Export Schema](https://cloud.google.com/billing/docs/how-to/export-data-bigquery-tables)
- [Standard SQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql)

#### 10.1.4 Cloud SDK

- [gcloud CLI](https://cloud.google.com/sdk/gcloud/reference)
- [bq CLI](https://cloud.google.com/bigquery/docs/bq-command-line-tool)

### 10.2 Python SDKs

- [google-cloud-discoveryengine](https://googleapis.dev/python/discoveryengine/latest/)
- [google-cloud-dialogflow-cx](https://googleapis.dev/python/dialogflow-cx/latest/)
- [google-cloud-bigquery](https://googleapis.dev/python/bigquery/latest/)

### 10.3 Descobertas Técnicas (Este Projeto)

#### 10.3.1 Issues Identificadas

1. **GroundedGenerationServiceClient não implementado**
   - Status: HTTP 501 em todas locations
   - Testado: v1 e v1beta
   - Conclusão: Use SearchServiceClient

2. **Latência de Billing**
   - Console: 24-48h
   - BigQuery: 6-24h
   - Recomendação: Sempre valide via BigQuery

3. **Data Store vazio funciona**
   - Queries executam mesmo sem documentos
   - Resposta AI é genérica
   - Crédito é consumido normalmente

#### 10.3.2 Best Practices

1. **Sempre valide antes de escalar**
   - 1 query → 48h → BigQuery → Escalar

2. **Use paralelização moderada**
   - MAX_WORKERS=10 é sweet spot
   - >15 pode causar rate limits

3. **Monitor net_cost_to_wallet**
   - Única métrica que importa
   - Se > $0: PARE imediatamente

4. **BigQuery Export é mandatório**
   - Console não é confiável
   - Única forma de auditoria granular

### 10.4 Comunidade e Suporte

- [Google Cloud Community](https://www.googlecloudcommunity.com/)
- [Stack Overflow - google-cloud-platform](https://stackoverflow.com/questions/tagged/google-cloud-platform)
- [Issue Tracker GCP](https://issuetracker.google.com/issues?q=componentid:187143)

### 10.5 Arquivos deste Projeto

| Arquivo | Seção Relevante |
|---------|-----------------|
| `README.md` | Visão geral |
| `QUICK_START.md` | Seção 6 (Guia de Uso) |
| `RESUMO_EXECUTIVO.md` | Seções 2-3 (Problema e Análise) |
| `DOCUMENTATION.md` | Este arquivo (tudo) |

---

## Apêndices

### A. Comandos Úteis

```bash
# === GCP General ===
gcloud config list
gcloud projects list
gcloud services list --enabled

# === Discovery Engine ===
# Via Python (não há CLI dedicado)
python manage_datastores.py

# === Dialogflow CX ===
# Ver agents
gcloud alpha dialogflow agents list --location=us-central1

# === BigQuery ===
# Listar datasets
bq ls

# Listar tabelas
bq ls billing_export

# Schema de tabela
bq show --schema --format=prettyjson billing_export.gcp_billing_export_v1_XXX

# Query interativa
bq query --use_legacy_sql=false 'SELECT * FROM ...'

# === Billing ===
# Ver billing accounts
gcloud billing accounts list

# Ver projeto billing info
gcloud billing projects describe gen-lang-client-0530325234

# === Monitoring ===
# Logs em tempo real
gcloud logging read "resource.type=cloud_function" --limit 50 --format json

# Métricas
gcloud monitoring time-series list \
  --filter='metric.type="serviceruntime.googleapis.com/api/request_count"'
```

### B. Tabela de SKUs Completa

Baseado no CSV fornecido + documentação:

| SKU ID | Descrição | Crédito Elegível | Custo |
|--------|-----------|------------------|-------|
| (Search Standard) | Vertex AI Search - Standard | GenAI App Builder | $2.50/1k |
| (Search Enterprise) | Vertex AI Search - Enterprise | GenAI App Builder | $4.00/1k |
| (Grounded Gen) | Grounded Generation API | GenAI App Builder | $2.50/1k |
| A1CC-751A-CDCC | Dialogflow CX Text Session | Dialogflow CX Trial | $0.007/req |
| (Audio session) | Dialogflow CX Audio | Dialogflow CX Trial | $0.06/min |

### C. Glossário

- **ADC:** Application Default Credentials - método padrão de auth do GCP
- **BQ:** BigQuery
- **CX:** Dialogflow CX (Customer Experience)
- **Data Store:** Índice de documentos no Vertex AI Search
- **Grounded Generation:** Respostas AI fundamentadas em documentos específicos
- **LLM:** Large Language Model
- **QPS:** Queries Per Second
- **RAG:** Retrieval-Augmented Generation
- **SKU:** Stock Keeping Unit - unidade de cobrança
- **Serving Config:** Configuração de como queries são processadas

### D. Changelog

#### v1.0 - 2025-12-29
- ✅ Problema identificado (GroundedGenerationServiceClient)
- ✅ Solução validada (SearchServiceClient)
- ✅ Scripts de load test criados
- ✅ Auditoria BigQuery implementada
- ✅ Setup 100% via CLI
- ✅ Documentação completa

---

**FIM DA DOCUMENTAÇÃO**

Para suporte ou questões, consulte:
1. Esta documentação (DOCUMENTATION.md)
2. QUICK_START.md para referência rápida
3. RESUMO_EXECUTIVO.md para análise técnica
4. Código-fonte dos scripts (bem comentado)
