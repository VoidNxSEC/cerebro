# Command: `cerebro knowledge analyze`

## 1. Descrição
Extrai AST e gera JSONL.
    Uso: phantom knowledge analyze ./repo "Contexto"

**Sintaxe:**
```bash
cerebro knowledge analyze [OPTIONS] [ARGS]
```

## 2. Parâmetros

| Nome | Tipo | Default | Descrição |
|------|------|---------|-----------|| `repo_path` | `str` | `Required` | - |
| `task_context` | `str` | `"General Review"` | - |
| `config_file` | `str` | `"./config/repos.yaml"` | - |


## 3. Exemplos
```bash
# Exemplo padrão
cerebro knowledge analyze
```

## 4. Saída
* **Formato:** Texto Rich (Console) ou JSON (se aplicável).
* **Logs:** Erros são enviados para stderr.

## 5. Erros Comuns
* `Exit Code 1`: Falha na execução ou dependência ausente.

## 6. Dependências
* Módulo: `src/phantom/cli.py`
* Função: `analyze`

## 7. Testes
* Verifique `tests/test_cli.py` para cobertura.

---
*Gerado automaticamente em pin jan 07 2026 19:41:03 -02*
