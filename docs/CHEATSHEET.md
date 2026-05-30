# 📋 CHEAT SHEET - Comandos Essenciais

## 🚀 One-Liners Mais Usados

```bash
# Setup completo
export ENGINE_ID=seu-engine-id && ./speedrun.sh all

# Gerar + Queimar (rápido)
./speedrun.sh generate 1000 && ./speedrun.sh burn queries_10k.txt 20

# Monitor em background
./speedrun.sh monitor &

# Status rápido
./speedrun.sh status
```

---

## 🔥 Speedrun Aliases (adicionar ao ~/.bashrc)

```bash
# Phoenix aliases
alias px='cd /home/kernelcore/dev/low-level/phoenix-cloud-run'
alias pxs='./speedrun.sh'
alias pxg='./speedrun.sh generate'
alias pxb='./speedrun.sh burn queries_10k.txt'
alias pxm='./speedrun.sh monitor'
alias pxst='./speedrun.sh status'

# Phantom aliases
alias ph='nix develop --command python phantom.py'
alias phq='ph gcp search'
alias phl='ph gcp datastores-list'
alias pha='ph credit audit'

# Uso:
# px && pxg 5000 && pxb
# phq "como configurar nvidia nixos?"
```

---

## 📊 Discovery Engine - Parâmetros Críticos

### Máximo Custo (Queimar Rápido)
```python
summary_result_count=10          # Máximo docs
model_spec.version="preview"     # Modelo mais caro
use_semantic_chunks=True         # Chunks semânticos
```

### Balance (Custo vs Qualidade)
```python
summary_result_count=5
model_spec.version="stable"
```

### Mínimo Custo (Teste)
```python
summary_result_count=1
# Sem summary_spec (só search básico)
```

---

## 💰 Tabela de Custos

| Operação | Custo/query | R$/query | 1k queries | 10k queries |
|----------|-------------|----------|------------|-------------|
| Search básico | $0.001 | R$ 0.0055 | R$ 5.50 | R$ 55 |
| Search + Summary | $0.004 | R$ 0.022 | R$ 22 | R$ 220 |
| Dialogflow msg | $0.007 | R$ 0.0385 | R$ 38.50 | R$ 385 |

**Meta:** R$ 10,079.11 = ~458,686 queries com RAG

---

## 🎯 Templates de Queries Prontas

### NixOS (seu contexto)
```bash
cat > nixos_queries.txt <<EOF
Como configurar nvidia drivers no NixOS 24.11?
Flake.nix exemplo para development shell Python
Home-manager configuração completa
Debug de rebuild loop no NixOS
NixOS container com PostgreSQL
Systemd service no NixOS
Overlays no Nix para pacotes customizados
EOF
```

### DevOps
```bash
cat > devops_queries.txt <<EOF
CI/CD pipeline com GitHub Actions
Terraform módulo para Kubernetes
Monitoring stack com Prometheus e Grafana
Docker multi-stage build otimizado
Kubernetes deployment com secrets
Ansible playbook para configuração de servidor
EOF
```

### Code Interview
```bash
cat > interview_queries.txt <<EOF
Algoritmo binary search explicação com exemplo Python
System design: URL shortener
LeetCode: Two Sum todas as soluções
Dynamic programming: explicação e padrões
Behavioral interview: conflito com colega
Como demonstrar expertise em Rust no portfolio
EOF
```

---

## 🔧 Scripts Python Standalone

### Query única (copy-paste)
```python
from google.cloud import discoveryengine_v1beta as discoveryengine

client = discoveryengine.SearchServiceClient()
serving_config = "projects/gen-lang-client-0530325234/locations/global/collections/default_collection/engines/SEU-ENGINE/servingConfigs/default_config"

request = discoveryengine.SearchRequest(
    serving_config=serving_config,
    query="como configurar nvidia no nixos?",
    content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
            summary_result_count=10,
            include_citations=True,
            language_code="pt-BR",
        ),
    ),
)

response = client.search(request)
print(response.summary.summary_text if response.summary else "No summary")
```

### Monitor simples (copy-paste)
```python
from google.cloud import bigquery

client = bigquery.Client(project="gen-lang-client-0530325234")
query = """
SELECT COUNT(*) as queries, SUM(cost) as cost
FROM `gen-lang-client-0530325234.billing_export.gcp_billing_export_v1_*`
WHERE service.description = 'Discovery Engine API'
  AND DATE(usage_start_time) >= CURRENT_DATE()
"""

for row in client.query(query).result():
    print(f"Hoje: {row.queries} queries = ${row.cost:.2f} USD")
```

---

## 📁 Estrutura de Arquivos Gerados

```
phoenix-cloud-run/
├── queries_10k.txt                    # Queries geradas
├── batch_results_1234567890.json      # Resultados (BACKUP!)
├── burn.log                           # Logs de execução
└── knowledge/                         # Criar para organizar
    ├── nixos/
    │   ├── queries.txt
    │   └── results.json
    ├── devops/
    └── interview/
```

---

## 🚨 Troubleshooting Rápido

### Erro: "Default credentials not found"
```bash
gcloud auth application-default login
```

### Erro: "Permission denied"
```bash
gcloud projects add-iam-policy-binding gen-lang-client-0530325234 \
    --member="user:seu-email@gmail.com" \
    --role="roles/discoveryengine.admin"
```

### Erro: "Rate limit exceeded"
```bash
# Adicionar delays entre queries
python scripts/batch_burn.py --file queries.txt --rate-limit 2
```

### Erro: "Engine not found"
```bash
# Listar engines
gcloud alpha discovery-engine engines list --location=global

# Criar novo engine
gcloud alpha discovery-engine engines create seu-engine \
    --display-name="Phoenix KB" \
    --location=global \
    --industry-vertical=GENERIC
```

---

## 🎓 Progressão Recomendada

### DIA 1: Validação
```bash
./speedrun.sh setup
./speedrun.sh generate 100
export ENGINE_ID=xxx
./speedrun.sh burn queries_10k.txt 5
./speedrun.sh status
```
**Meta:** Validar pipeline completo

### DIA 2-7: Ramp-up
```bash
./speedrun.sh generate 1000
./speedrun.sh burn queries_10k.txt 10
```
**Meta:** R$ 100-500 consumidos

### DIA 8-30: Scale
```bash
./speedrun.sh generate 10000
./speedrun.sh burn queries_10k.txt 30
```
**Meta:** R$ 2k-5k consumidos

### DIA 31-90: Automation
```bash
# Cron job diário
0 2 * * * cd /home/kernelcore/dev/low-level/phoenix-cloud-run && ./speedrun.sh generate 5000 && ./speedrun.sh burn queries_10k.txt 20
```
**Meta:** R$ 10k completo

---

## 📊 KPIs para Acompanhar

1. **Queries/dia**: Meta 1k-5k
2. **Custo/dia**: Meta R$ 20-100
3. **Taxa de sucesso**: >95%
4. **Queries com citações**: >80%
5. **Tempo médio/query**: <2s

---

## 🔐 Variáveis de Ambiente

```bash
# Adicionar ao ~/.bashrc ou .env
export GOOGLE_CLOUD_PROJECT=gen-lang-client-0530325234
export GOOGLE_CLOUD_LOCATION=global
export ENGINE_ID=seu-engine-id
export DATA_STORE_ID=seu-datastore-id
export BILLING_DATASET=billing_export
export BILLING_TABLE=gcp_billing_export_v1_XXXXX
```

---

## 🎯 Comandos de Emergência

### Parar tudo
```bash
pkill -f batch_burn.py
pkill -f generate_queries.py
```

### Limpar arquivos temporários
```bash
rm -f queries_*.txt batch_results_*.json burn.log
```

### Reset completo
```bash
git clean -fdx
nix develop --command python phantom.py gcp validate
```

### Backup de resultados
```bash
tar -czf results_backup_$(date +%Y%m%d).tar.gz batch_results_*.json
gsutil cp results_backup_*.tar.gz gs://seu-bucket/backups/
```

---

## 💡 Pro Tips

1. **Sempre rode monitor em terminal separado**
   ```bash
   # Terminal 1
   ./speedrun.sh burn queries.txt 20

   # Terminal 2
   watch -n 30 './speedrun.sh status'
   ```

2. **Gere queries enquanto processa**
   ```bash
   ./speedrun.sh burn queries_batch1.txt 20 &
   ./speedrun.sh generate 10000  # Para próximo batch
   ```

3. **Use tmux para sessões longas**
   ```bash
   tmux new -s phoenix
   ./speedrun.sh burn queries_100k.txt 50
   # Ctrl+B D para detach
   # tmux attach -t phoenix para voltar
   ```

4. **Backup automático de resultados**
   ```bash
   # Adicionar ao cron
   0 */6 * * * tar -czf /backup/phoenix_$(date +\%Y\%m\%d_\%H\%M).tar.gz /home/kernelcore/dev/low-level/phoenix-cloud-run/batch_results_*.json
   ```

5. **Log de execução**
   ```bash
   ./speedrun.sh burn queries.txt 20 2>&1 | tee -a phoenix_$(date +%Y%m%d).log
   ```

---

## 🎉 Quick Wins

### Win 1: Primeiro R$ 1 consumido
```bash
./speedrun.sh generate 50
./speedrun.sh burn queries_10k.txt 5
```
**Tempo:** 5min | **Custo:** ~R$ 1

### Win 2: 1k queries processadas
```bash
./speedrun.sh generate 1000
./speedrun.sh burn queries_10k.txt 10
```
**Tempo:** 20min | **Custo:** ~R$ 22

### Win 3: R$ 100 consumidos
```bash
./speedrun.sh generate 5000
./speedrun.sh burn queries_10k.txt 20
```
**Tempo:** 2h | **Custo:** ~R$ 110

---

**ESSE É SEU ARSENAL! Use e abuse. Qualquer dúvida, consulte:**
- `QUICKSTART_KB.md` - Documentação completa
- `README_SPEEDRUN.md` - Guia detalhado
- `CHEATSHEET.md` - Este arquivo
