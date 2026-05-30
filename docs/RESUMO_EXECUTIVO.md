# RESUMO EXECUTIVO: Análise e Solução do Problema de Consumo de Créditos

**Data:** 2025-12-29
**Créditos Totais:** R$ 10.079,11
- GenAI App Builder: R$ 6.432,54
- Dialogflow CX Trial: R$ 3.646,57

---

## 🎯 PROBLEMA IDENTIFICADO

### O que NÃO funciona: `grounded_generation.py`

```python
# ❌ FALHA: HTTP 501 - Method not found
client = discoveryengine.GroundedGenerationServiceClient()
response = client.generate_grounded_content(request)
```

**Root Cause:**
- Método existe no SDK Python ✅
- API `discoveryengine.googleapis.com` habilitada ✅
- **Servidor retorna "501 Method not found"** ❌
- Testado em v1 e v1beta - ambos falham
- Testado em locations: global, us, us-central1 - todos falham

**Conclusão:** API não implementada no servidor ou requer whitelist especial.

---

## ✅ SOLUÇÃO VALIDADA

### O que FUNCIONA: `test_credits.py` + Seu Exemplo

```python
# ✅ SUCESSO: HTTP 200 OK
client = discoveryengine.SearchServiceClient()

request = SearchRequest(
    serving_config=serving_config,
    content_search_spec=SearchRequest.ContentSearchSpec(
        summary_spec=SummarySpec(  # ← ISTO É GROUNDED GENERATION!
            summary_result_count=5,
            include_citations=True,
        )
    )
)

response = client.search(request)
```

**Por que funciona:**
1. `SearchServiceClient` é a API correta e implementada
2. `summary_spec` ativa respostas generativas AI
3. Respostas são "grounded" (fundamentadas nos documentos)
4. Consome o crédito "GenAI App Builder" corretamente
5. Confirmado por: teste real + exemplo fornecido + relatório técnico (Seção 3.1)

---

## 📊 CORRELAÇÃO: Relatório Técnico vs. Realidade

| Item | Relatório | Realidade | Status |
|------|-----------|-----------|--------|
| SearchServiceClient (3.1) | ✅ Recomendado | ✅ FUNCIONA | VALIDADO |
| summary_spec = Grounding | ✅ Correto | ✅ FUNCIONA | VALIDADO |
| GroundedGenerationServiceClient (3.2) | ✅ Documentado | ❌ 501 Error | INVÁLIDO |
| BigQuery Audit (5.2) | ✅ Recomendado | 🔄 Implementado | PENDENTE TESTE |
| Dialogflow CX (Seção 4) | ✅ Correto | 🔄 Implementado | PENDENTE TESTE |

**Lição Aprendida:** Relatório parcialmente correto. Seção 3.2 sobre `GroundedGenerationServiceClient` está **desatualizada ou refere-se a API em preview**.

---

## 🚀 PLANO DE AÇÃO VALIDADO

### 1. Para Consumir Crédito "GenAI App Builder" (R$ 6.432,54)

**Opção A: Testes Manuais**
```bash
# Já funciona!
export DATA_STORE_ID='ds-app-v4-5e020c93'
python test_credits.py

# Customizar query:
SEARCH_QUERY="Sua pergunta aqui" python test_credits.py
```

**Opção B: Load Test Automatizado (RECOMENDADO)**
```bash
# Queimar créditos rapidamente
export DATA_STORE_ID='ds-app-v4-5e020c93'
export NUM_QUERIES=500        # 500 queries = ~$2 USD
export MAX_WORKERS=10         # Paralelização

python burn_credits_loadtest.py
```

**Custos:**
- $4.00 / 1,000 queries (Search Enterprise)
- R$ 6.432,54 ≈ 1,608 queries até esgotar
- 1 query = ~$0.004

---

### 2. Para Consumir Crédito "Dialogflow CX Trial" (R$ 3.646,57)

**Pré-requisito:** Criar Agent no Dialogflow CX
- Console: https://dialogflow.cloud.google.com/cx/
- Copiar Agent ID

**Execução:**
```bash
export DIALOGFLOW_AGENT_ID='seu-agent-id'
export DIALOGFLOW_LOCATION='us-central1'
export NUM_CONVERSATIONS=100   # 100 conversas = ~$2.10 USD
export MAX_WORKERS=5

python burn_dialogflow_cx.py
```

**Custos:**
- ~$0.007 por text session
- R$ 3.646,57 ≈ 93,000 sessões teóricas
- Média 3 mensagens/conversa = ~31,000 conversas

---

### 3. Validação Financeira (CRÍTICO!)

**Problema:** Painel de billing tem latência de 24-48h

**Solução:** BigQuery Export + SQL Audit

```bash
# Passo 1: Configurar Billing Export
# Console: https://console.cloud.google.com/billing/export
# Criar dataset: billing_export
# Ativar "Detailed usage cost to BigQuery"

# Passo 2: Configurar script
export BILLING_EXPORT_DATASET='billing_export'
export BILLING_EXPORT_TABLE='gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX'
export AUDIT_DAYS=7

# Passo 3: Executar auditoria
python audit_credits_bigquery.py
```

**O que valida:**
- `gross_cost`: Quanto foi consumido bruto
- `credit_amount`: Quanto foi coberto pelo crédito (negativo)
- `net_cost_to_wallet`: Quanto VOCÊ PAGOU
- **Se net_cost = $0.00 → Crédito funcionou! 🎉**
- **Se net_cost > $0.00 → Você foi cobrado! ⚠️**

---

## 📁 ARQUIVOS CRIADOS E STATUS

| Arquivo | Status | Função |
|---------|--------|--------|
| `test_credits.py` | ✅ VALIDADO | Query única - SearchServiceClient |
| `burn_credits_loadtest.py` | ✅ PRONTO | Load test GenAI App Builder |
| `burn_dialogflow_cx.py` | ✅ PRONTO | Load test Dialogflow CX |
| `audit_credits_bigquery.py` | ✅ PRONTO | Validação financeira definitiva |
| `grounded_generation.py` | ❌ NÃO USAR | GroundedGenerationServiceClient falha |
| `test_grounded_v1.py` | 🔬 DIAGNÓSTICO | Prova que v1 e v1beta falham |

---

## ⚠️ RISCOS E MITIGAÇÕES

### Risco 1: Consumir crédito errado
**Mitigação:** Use apenas os scripts validados (`test_credits.py`, `burn_credits_loadtest.py`)

### Risco 2: Cobrar no cartão ao invés do crédito
**Mitigação:**
1. Execute POUCAS queries primeiro (10-20)
2. Aguarde 48h
3. Execute `audit_credits_bigquery.py`
4. **VALIDE que `net_cost = $0.00`**
5. Só então escale o load test

### Risco 3: Rate limits
**Mitigação:**
- Comece com `MAX_WORKERS=5`
- Aumente gradualmente se não houver erros
- Monitor logs para "quota exceeded"

### Risco 4: Data Store vazio
**Status:** Seu Data Store `ds-app-v4-5e020c93` está vazio
**Impacto:** Respostas AI podem ser genéricas (mas ainda consomem crédito)
**Solução (opcional):**
```bash
# Popular com documentos
python import_documents.py knowledge_base/
```

---

## 🎯 RECOMENDAÇÃO FINAL

### Fluxo Seguro de Execução:

```bash
# 1. Validação inicial (FAÇA ISSO PRIMEIRO!)
python test_credits.py  # 1 query = $0.004

# 2. Aguarde 48h e valide
# Configure BigQuery Export no console primeiro!
python audit_credits_bigquery.py

# 3. Se net_cost = $0.00, escale!
NUM_QUERIES=1000 python burn_credits_loadtest.py  # $4 USD

# 4. Dialogflow CX (depois de criar agent)
NUM_CONVERSATIONS=500 python burn_dialogflow_cx.py  # ~$10.50 USD

# 5. Monitore regularmente
python audit_credits_bigquery.py
```

### Consumo Estimado para Esgotar Créditos:

**GenAI App Builder (R$ 6.432,54):**
- ~1,600 queries via `burn_credits_loadtest.py`
- Tempo estimado: 2-3h com 10 workers
- Comando: `NUM_QUERIES=1600 MAX_WORKERS=10 python burn_credits_loadtest.py`

**Dialogflow CX (R$ 3.646,57):**
- ~31,000 conversas (3 msgs cada)
- Tempo estimado: Várias horas/dias
- Comando: `NUM_CONVERSATIONS=31000 MAX_WORKERS=5 python burn_dialogflow_cx.py`

---

## 📚 REFERÊNCIAS

**Funcionou:**
- [Google Cloud Discovery Engine Client](https://cloud.google.com/python/docs/reference/discoveryengine/latest)
- SearchServiceClient: test_credits.py:46
- summary_spec: test_credits.py:64-76

**Não Funcionou:**
- GroundedGenerationServiceClient: grounded_generation.py (501 Error)
- Todas locations testadas: global, us, us-central1

**Validações:**
- Exemplo fornecido pelo usuário ✅
- Relatório Técnico Seção 3.1 ✅
- Teste real executado com sucesso ✅

---

## ✅ CHECKLIST DE EXECUÇÃO

- [x] GroundedGenerationServiceClient investigado (não funciona)
- [x] SearchServiceClient validado (FUNCIONA!)
- [x] Data Store verificado (ds-app-v4-5e020c93 existe)
- [x] Script de load test criado (burn_credits_loadtest.py)
- [x] Script Dialogflow CX criado (burn_dialogflow_cx.py)
- [x] Script de auditoria BigQuery criado (audit_credits_bigquery.py)
- [ ] **PENDENTE:** Configurar BigQuery Export no console
- [ ] **PENDENTE:** Executar teste inicial e validar com BigQuery
- [ ] **PENDENTE:** Criar Dialogflow CX Agent
- [ ] **PENDENTE:** Escalar load tests após validação

---

**Próximo Passo Crítico:** Configure o BigQuery Export e execute a primeira validação!
