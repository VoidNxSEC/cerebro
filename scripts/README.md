# 🧪 Cerebro Testing & Validation

Validation and CI/CD scripts for the Cerebro platform.

## 📁 Scripts Disponíveis

### `validate.sh` - Validação Completa
Executa suite completa de testes com captura de exit codes e logs.

```bash
nix develop -c bash scripts/validate.sh
```

**Output:**
- Log detalhado: `validation_YYYYMMDD_HHMMSS.log`
- Exit code: 0 (sucesso) ou 1 (falha)
- Taxa de sucesso calculada

### `ci-test.sh` - CI Runner Local
Simula ambiente de CI/CD localmente, executando todos os jobs.

```bash
nix develop -c bash scripts/ci-test.sh
```

**Jobs executados:**
1. Import Tests - Valida imports Python
2. CLI Tests - Testa comandos cerebro
3. Syntax Check - Valida sintaxe Python
4. Full Validation - Suite completa

### `report.sh` - Gerador de Relatórios
Gera relatório markdown com métricas de validação.

```bash
nix develop -c bash scripts/report.sh
```

**Output:**
- Relatório: `validation_report_YYYYMMDD_HHMMSS.md`
- Métricas: Total, Passed, Failed, Skipped, Success Rate
- Recomendações automáticas

## 🎯 Workflow Típico

### Desenvolvimento Local
```bash
# 1. Entre no ambiente
nix develop

# 2. Execute validação rápida
cerebro info
cerebro status

# 3. Execute suite completa
bash scripts/validate.sh

# 4. Gere relatório
bash scripts/report.sh
```

### CI/CD Completo
```bash
# Simula CI completo localmente
bash scripts/ci-test.sh
```

## 📊 Métricas Coletadas

### Exit Codes
- `0` - Sucesso
- `1` - Falha no comando
- `127` - Comando não encontrado

### Success Rate
```
Success Rate = (Passed / Total) × 100
```

### Categorias de Teste
1. **Basic Commands** - help, info, version, status
2. **Python Imports** - core, modules, dependencies
3. **GCP Commands** - validate, list (requer auth)
4. **Invalid Commands** - Testa error handling

## 🔧 Configuração CI/CD

### GitHub Actions
Workflow configurado em `.github/workflows/validate.yml`:

```yaml
- on: push, pull_request, workflow_dispatch
- jobs:
  - validate: Suite completa
  - import-tests: Testa imports
  - cli-tests: Testa CLI
  - syntax-check: Valida sintaxe
```

### Artifacts
- Logs de validação (retention: 30 dias)
- Summary reports no GitHub

### Triggers
- Push para main/develop
- Pull requests
- Manual via workflow_dispatch

## 📈 Roadmap

### Fase 1 (Atual)
- [x] Validação básica de comandos
- [x] Testes de import
- [x] CI/CD local
- [x] GitHub Actions workflow

### Fase 2
- [ ] Testes unitários (pytest)
- [ ] Code coverage reports
- [ ] Performance benchmarks
- [ ] Integration tests com GCP

### Fase 3
- [ ] E2E tests
- [ ] Load testing
- [ ] Security scanning
- [ ] Dependency auditing

## 🚨 Troubleshooting

### "cerebro: command not found"
```bash
# Certifique-se de estar no nix develop
nix develop
```

### "Import errors"
```bash
# Force reinstall de dependências
rm -f .venv/.deps_installed
nix develop
```

### "GCP tests skipped"
```bash
# Autentique com GCP
cerebro auth
# ou
gcloud auth application-default login
```

## 📝 Contribuindo

Ao adicionar novos comandos, adicione testes correspondentes em:
1. `validate.sh` - Para smoke tests
2. `.github/workflows/validate.yml` - Para CI/CD
3. Update `report.sh` - Para métricas

---

**Maintained by:** Cerebro Team
**Last updated:** 2026-05-02
