# 🚀 QUICK START - Guia Rápido de Uso

## 📝 TL;DR - Execute Isso Agora

```bash
# 1. Teste inicial (1 query, seguro)
python test_credits.py

# 2. Se funcionou, queime créditos!
NUM_QUERIES=100 python burn_credits_loadtest.py
```

---

## 🎯 Cenários de Uso

### Cenário 1: "Quero validar que os créditos funcionam"

```bash
# Execute UMA query
python test_credits.py

# ✅ Sucesso = código 200
# ⏰ Aguarde 48h
# 🔍 Valide no BigQuery (veja seção "Validação" abaixo)
```

---

### Cenário 2: "Quero queimar R$ 100 de créditos rapidamente"

```bash
# R$ 100 ≈ $18 USD ≈ 4,500 queries
NUM_QUERIES=4500 MAX_WORKERS=10 python burn_credits_loadtest.py

# Tempo estimado: 1-2 horas
```

---

### Cenário 3: "Quero esgotar TODOS os créditos GenAI"

```bash
# R$ 6.432,54 ≈ 1,600 queries
NUM_QUERIES=1600 MAX_WORKERS=15 python burn_credits_loadtest.py

# ATENÇÃO: Execute em múltiplas sessões se houver rate limits!
```

---

### Cenário 4: "Tenho um Dialogflow CX Agent pronto"

```bash
# Configure
export DIALOGFLOW_AGENT_ID='seu-agent-id-aqui'
export DIALOGFLOW_LOCATION='us-central1'

# Execute
NUM_CONVERSATIONS=100 python burn_dialogflow_cx.py
```

---

## 🔍 Validação Financeira (IMPORTANTE!)

### Setup BigQuery Export (UMA VEZ)

1. Acesse: https://console.cloud.google.com/billing/export
2. Clique "Edit Settings" em "Detailed usage cost"
3. Escolha "Export to BigQuery"
4. Dataset: `billing_export` (crie se não existir)
5. Salve

### Executar Auditoria

```bash
# Configure (pegue o nome da tabela no BigQuery)
export BILLING_EXPORT_DATASET='billing_export'
export BILLING_EXPORT_TABLE='gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX'

# Execute
python audit_credits_bigquery.py
```

### Interpretar Resultados

```
✅ net_cost_to_wallet = $0.00
   → Crédito aplicado corretamente!
   → Continue usando com segurança

⚠️  net_cost_to_wallet > $0.00
   → VOCÊ ESTÁ SENDO COBRADO!
   → PARE e revise a arquitetura
```

---

## 🛠️ Troubleshooting Rápido

### Erro: "DATA_STORE_ID não configurado"

```bash
# Lista data stores disponíveis
python manage_datastores.py

# Ou cria um novo
python manage_datastores.py  # e escolha 'y' quando perguntado

# Configure
export DATA_STORE_ID='ds-app-v4-5e020c93'
```

---

### Erro: "DIALOGFLOW_AGENT_ID não configurado"

```bash
# 1. Crie um agent em:
#    https://dialogflow.cloud.google.com/cx/

# 2. Copie o Agent ID (formato UUID)

# 3. Configure
export DIALOGFLOW_AGENT_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
export DIALOGFLOW_LOCATION='us-central1'
```

---

### Erro: "Method not found" (GroundedGenerationServiceClient)

**Solução:** NÃO use `grounded_generation.py`! Use `test_credits.py` ou `burn_credits_loadtest.py`.

Motivo: `GroundedGenerationServiceClient` não está implementado no servidor Google.

---

### Query retorna vazio / sem resposta AI

**Causa:** Data Store vazio (sem documentos)

**Impacto:** Ainda consome crédito! Resposta AI pode ser genérica.

**Solução (opcional):**
```bash
# Popular com documentos
mkdir -p knowledge_base
# Coloque PDFs/TXTs em knowledge_base/
python import_documents.py knowledge_base/
```

---

## 📊 Monitoramento em Tempo Real

### Durante execução do load test:

```
[100/1000] ✅ 98 | ❌ 2 | QPS: 5.23 | Custo: $0.3920
            ↑      ↑       ↑           ↑
         Sucesso Falhas  Queries/s   $ acumulado
```

**Sinais de Alerta:**
- Muitas falhas (❌ > 10%): Reduce MAX_WORKERS
- QPS muito baixo (< 1): Increase MAX_WORKERS
- Erros de quota: Pause e retry depois

---

## 💡 Dicas de Otimização

### 1. Paralelização Ideal

```bash
# Conservador (seguro)
MAX_WORKERS=5

# Moderado (recomendado)
MAX_WORKERS=10

# Agressivo (teste antes!)
MAX_WORKERS=20
```

### 2. Executar em Background

```bash
# Com nohup
nohup python burn_credits_loadtest.py > burn.log 2>&1 &

# Monitor progresso
tail -f burn.log
```

### 3. Dividir em Lotes

```bash
# Ao invés de 1,600 de uma vez:
for i in {1..4}; do
    NUM_QUERIES=400 python burn_credits_loadtest.py
    sleep 300  # 5 min entre lotes
done
```

---

## 📈 Estimativas de Tempo e Custo

| Queries | Custo (USD) | Custo (BRL) | Tempo (10 workers) |
|---------|-------------|-------------|--------------------|
| 10      | $0.04       | R$ 0.22     | ~2 segundos        |
| 100     | $0.40       | R$ 2.20     | ~20 segundos       |
| 500     | $2.00       | R$ 11.00    | ~2 minutos         |
| 1,000   | $4.00       | R$ 22.00    | ~4 minutos         |
| 1,600   | $6.40       | R$ 35.20    | ~6 minutos         |

*Baseado em QPS médio de ~3 queries/segundo com 10 workers*

---

## 🎯 Workflow Recomendado

```bash
# DIA 1: Validação
python test_credits.py
# ✅ Funcionou? Ótimo!

# DIA 3: Auditoria
python audit_credits_bigquery.py
# ✅ net_cost = $0? Perfeito!

# DIA 3+: Escalando
NUM_QUERIES=500 python burn_credits_loadtest.py
# Monitore, ajuste, repita

# SEMANAL: Monitor
python audit_credits_bigquery.py
# Acompanhe consumo real vs estimado
```

---

## 📞 Referências Rápidas

**Console Principal:**
- Billing: https://console.cloud.google.com/billing/
- Agent Builder: https://console.cloud.google.com/gen-app-builder
- Dialogflow CX: https://dialogflow.cloud.google.com/cx/

**Comandos Úteis:**
```bash
# Ver APIs habilitadas
gcloud services list --enabled | grep -E 'discovery|dialogflow'

# Ver projeto atual
gcloud config get-value project

# Trocar projeto
gcloud config set project SEU_PROJECT_ID
```

---

## ⚡ One-Liner para Queimar Tudo

```bash
# YOLO - Queima TODOS os créditos GenAI de uma vez
# (Não recomendado sem validação prévia!)
NUM_QUERIES=1600 MAX_WORKERS=15 AUTO_CONFIRM=true \
  python burn_credits_loadtest.py
```

**⚠️ USE COM CAUTELA! Valide com BigQuery primeiro!**
