# 🚀 SPEEDRUN - Guia Rápido de Execução

## TL;DR - 3 Comandos para Queimar R$ 10k

```bash
export ENGINE_ID=seu-engine-id-aqui

./speedrun.sh setup           # Valida ambiente (1min)
./speedrun.sh generate 10000  # Gera 10k queries (30s)
./speedrun.sh burn queries_10k.txt 20  # QUEIMA! (30-60min para 10k queries)
```

---

## 📁 Arquivos Criados

```
phoenix-cloud-run/
├── speedrun.sh                    # 🎯 SCRIPT PRINCIPAL
├── QUICKSTART_KB.md               # 📚 Documentação completa
├── README_SPEEDRUN.md             # 📖 Este arquivo
└── scripts/
    ├── generate_queries.py        # Gerador de 10k+ queries
    ├── batch_burn.py              # Processador paralelo otimizado
    └── monitor_credits.py         # Monitor real-time de créditos
```

---

## ⚡ Quick Commands

### 1. Setup Inicial (1x apenas)

```bash
# Validar ambiente
./speedrun.sh setup

# OU manualmente:
nix develop --command python phantom.py gcp validate
```

**Output esperado:**
- ✅ Autenticado no projeto <your-gcp-project-id>
- ✅ Billing ativo (VoidNx)
- ✅ APIs habilitadas (Discovery Engine, Dialogflow)

### 2. Gerar Queries

```bash
# 10k queries (default)
./speedrun.sh generate

# Custom amount
./speedrun.sh generate 5000

# OU manualmente:
nix develop --command python scripts/generate_queries.py --count 10000 --output queries.txt
```

**Output:**
- `queries_10k.txt` com queries técnicas
- Custo estimado: ~$40 USD (~R$ 220)

### 3. Queimar Créditos

```bash
# IMPORTANTE: Definir ENGINE_ID primeiro!
export ENGINE_ID=seu-discovery-engine-id

# Burn com 20 workers (rápido)
./speedrun.sh burn queries_10k.txt 20

# OU manualmente:
nix develop --command python scripts/batch_burn.py \
    --file queries_10k.txt \
    --workers 20 \
    --project <your-gcp-project-id>
```

**Output:**
- Progress bar em tempo real
- Stats a cada 50 queries
- Arquivo `batch_results_TIMESTAMP.json` com todas as respostas

### 4. Monitorar Consumo

```bash
# Real-time (atualiza a cada 60s)
./speedrun.sh monitor

# Snapshot único
./speedrun.sh status

# OU manualmente:
nix develop --command python scripts/monitor_credits.py --project <your-gcp-project-id> --once
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Credit             ┃ Queries ┃ Gross Cost ┃ Remaining (BRL)┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ GenAI App Builder  │   2,340 │     $9.36  │   R$ 5,890.12  │
│ Dialogflow CX      │     120 │     $0.84  │   R$ 3,642.45  │
│ TOTAL              │   2,460 │    $10.20  │   R$ 9,532.57  │
└────────────────────┴─────────┴────────────┴────────────────┘
```

---

## 🎯 Workflows Recomendados

### Workflow 1: Teste Pequeno (Validar Pipeline)

```bash
# 1. Gerar 100 queries
./speedrun.sh generate 100

# 2. Burn com poucos workers
export ENGINE_ID=seu-engine-id
./speedrun.sh burn queries_10k.txt 5

# 3. Verificar resultados
./speedrun.sh status
```

**Custo:** ~$0.40 USD (~R$ 2.20)
**Tempo:** ~2-5 minutos

### Workflow 2: Scale Moderado (1k queries)

```bash
./speedrun.sh generate 1000
export ENGINE_ID=seu-engine-id
./speedrun.sh burn queries_10k.txt 10
```

**Custo:** ~$4 USD (~R$ 22)
**Tempo:** ~10-20 minutos

### Workflow 3: TURBO (10k queries)

```bash
./speedrun.sh generate 10000
export ENGINE_ID=seu-engine-id
./speedrun.sh burn queries_10k.txt 50  # 50 workers paralelos!

# Em outro terminal, monitorar:
./speedrun.sh monitor
```

**Custo:** ~$40 USD (~R$ 220)
**Tempo:** ~30-60 minutos

### Workflow 4: MEGA BURN (100k queries)

```bash
# Gerar 100k queries
nix develop --command python scripts/generate_queries.py --count 100000 --output mega.txt

# Processar em batches de 10k
split -l 10000 mega.txt batch_
for f in batch_*; do
    nix develop --command python scripts/batch_burn.py --file $f --workers 50
done
```

**Custo:** ~$400 USD (~R$ 2,200)
**Tempo:** ~5-10 horas

---

## 🔧 Customização Avançada

### Ajustar Parâmetros de Query

Editar `scripts/batch_burn.py` linha 95-110:

```python
# MAXIMIZAR CUSTO (default)
summary_result_count=10  # Máximo de docs para summary
model_spec.version="preview"  # Modelo mais avançado

# BALANCE
summary_result_count=5
model_spec.version="stable"

# ECONOMIA (não recomendado)
summary_result_count=1
```

### Customizar Queries Geradas

Editar `scripts/generate_queries.py`:

```python
# Adicionar seus próprios tópicos
TECH = ["Docker", "Kubernetes", "SeuTech"]

# Adicionar templates customizados
TEMPLATES = {
    "custom": [
        "Como {action} {tech} no {context}?",
    ]
}
```

### Rate Limiting

```bash
# Limitar a 5 queries/segundo (evitar throttling)
nix develop --command python scripts/batch_burn.py \
    --file queries.txt \
    --workers 10 \
    --rate-limit 5
```

---

## 📊 Estimativas de Consumo

| Queries | Workers | Tempo Estimado | Custo USD | Custo BRL | % do Total |
|---------|---------|----------------|-----------|-----------|------------|
| 100     | 5       | 2-5 min        | $0.40     | R$ 2.20   | 0.02%      |
| 1,000   | 10      | 10-20 min      | $4.00     | R$ 22.00  | 0.2%       |
| 10,000  | 20      | 1-2 horas      | $40.00    | R$ 220.00 | 2.2%       |
| 50,000  | 50      | 5-10 horas     | $200.00   | R$ 1,100  | 11%        |
| 100,000 | 50      | 10-20 horas    | $400.00   | R$ 2,200  | 22%        |

**Para consumir R$ 10k completo:**
- ~450,000 queries totais
- Com 50 workers: ~90-180 horas (~4-8 dias contínuos)
- Recomendado: Executar em batches ao longo de 30 dias

---

## ⚠️ Troubleshooting

### Erro: "ENGINE_ID not found"

```bash
# Listar engines disponíveis
nix develop --command python phantom.py gcp datastores-list

# Setar o ID
export ENGINE_ID=seu-engine-id-aqui
```

### Erro: "Rate limit exceeded"

```bash
# Reduzir workers ou adicionar rate limit
./speedrun.sh burn queries.txt 5  # Menos workers

# OU
nix develop --command python scripts/batch_burn.py \
    --file queries.txt \
    --workers 10 \
    --rate-limit 2  # 2 queries/segundo
```

### Queries falhando

```bash
# Ver logs detalhados
nix develop --command python scripts/batch_burn.py \
    --file queries.txt \
    --workers 5 2>&1 | tee burn.log

# Checar resultados
cat batch_results_*.json | jq '.results[] | select(.error != null)'
```

### BigQuery não encontra billing table

```bash
# Configurar manualmente
export BILLING_DATASET=seu-dataset
export BILLING_TABLE=sua-tabela

# OU editar .billing_export.env
echo "BILLING_DATASET=billing_export" > .billing_export.env
echo "BILLING_TABLE=gcp_billing_export_v1_XXXXX" >> .billing_export.env
```

---

## 🎓 Próximos Passos

### 1. Extrair Valor das Respostas

```bash
# Todas as respostas estão em batch_results_*.json
cat batch_results_*.json | jq '.results[] | {q: .question, a: .answer}' > knowledge.json

# Indexar de volta no Discovery Engine para queries futuras!
```

### 2. Análise de Qualidade

```python
# Script para avaliar qualidade das respostas
import json

with open("batch_results_TIMESTAMP.json") as f:
    data = json.load(f)

# Queries com mais citações (melhor qualidade)
top_quality = sorted(
    data["results"],
    key=lambda x: len(x["citations"]),
    reverse=True
)[:10]

for r in top_quality:
    print(f"Q: {r['question']}")
    print(f"A: {r['answer'][:200]}...")
    print(f"Sources: {len(r['citations'])}\n")
```

### 3. Dialogflow CX

```bash
# Próxima fase: Consumir os R$ 3,646.57 do Dialogflow
nix develop --command python phantom.py credit dialogflow --num-conversations 1000
```

---

## 📈 Objetivos de Valor

### Curto Prazo (7 dias)
- [ ] Indexar todos os seus projetos
- [ ] Gerar 10k queries relevantes
- [ ] Processar e salvar todas as respostas
- [ ] Consumir ~R$ 500 em créditos

### Médio Prazo (30 dias)
- [ ] Knowledge base completo indexado
- [ ] 50k+ queries processadas
- [ ] Sistema de busca funcionando
- [ ] Consumir ~R$ 3k em créditos

### Longo Prazo (90 dias)
- [ ] 200k+ queries (valor massivo extraído)
- [ ] Automação de queries diárias
- [ ] Integration com projetos reais
- [ ] Consumir R$ 10k completo

---

## 💡 Dicas de Otimização

1. **Paralelização:** Quanto mais workers, mais rápido (mas cuidado com rate limits)
2. **Horários:** Rodar overnight para batches grandes
3. **Monitoramento:** Sempre rodar `monitor` em outro terminal
4. **Backup:** Salvar `batch_results_*.json` - é seu conhecimento!
5. **Iteração:** Use respostas anteriores para gerar queries melhores

---

## 🚨 Checklist Pré-Execução

Antes de rodar batches grandes:

- [ ] `ENGINE_ID` definido
- [ ] Projeto GCP correto (`<your-gcp-project-id>`)
- [ ] Billing ativo e validado
- [ ] Discovery Engine API habilitada
- [ ] BigQuery billing export configurado
- [ ] Espaço em disco suficiente para results (1GB+ para 100k queries)
- [ ] Queries geradas e revisadas
- [ ] Monitor rodando em terminal separado

---

**PRONTO PARA EXECUTAR!** 🔥

Comando mais simples para começar AGORA:

```bash
export ENGINE_ID=seu-engine-id
./speedrun.sh all
```
