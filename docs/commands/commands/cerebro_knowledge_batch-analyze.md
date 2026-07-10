# Command: `cerebro knowledge batch-analyze`

## 1. Descrição
Processa todos os repositórios definidos no arquivo de configuração.

**Sintaxe:**
```bash
cerebro knowledge batch-analyze [OPTIONS] [ARGS]
```

## 2. Parâmetros

| Nome | Tipo | Default | Descrição |
|------|------|---------|-----------|| `config_file` | `str` | `"./config/repos.yaml"` | - |


## 3. Exemplos
```bash
# Exemplo padrão
cerebro knowledge batch-analyze
```

## 4. Saída
* **Formato:** Texto Rich (Console) ou JSON (se aplicável).
* **Logs:** Erros são enviados para stderr.

## 5. Erros Comuns
* `Exit Code 1`: Falha na execução ou dependência ausente.

## 6. Dependências
* Módulo: `src/phantom/cli.py`
* Função: `batch_analyze`

## 7. Testes
* Verifique `tests/test_cli.py` para cobertura.

---
*Gerado automaticamente em pin jan 07 2026 19:41:03 -02*
