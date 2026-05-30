# Command: `cerebro ops health`

## 1. Descrição
Verifica a saúde do sistema (Credenciais, Permissões, APIs).

**Sintaxe:**
```bash
cerebro ops health [OPTIONS] [ARGS]
```

## 2. Parâmetros

| Nome | Tipo | Default | Descrição |
|------|------|---------|-----------|| - | - | - | - |


## 3. Exemplos
```bash
# Exemplo padrão
cerebro ops health
```

## 4. Saída
* **Formato:** Texto Rich (Console) ou JSON (se aplicável).
* **Logs:** Erros são enviados para stderr.

## 5. Erros Comuns
* `Exit Code 1`: Falha na execução ou dependência ausente.

## 6. Dependências
* Módulo: `src/phantom/cli.py`
* Função: `health`

## 7. Testes
* Verifique `tests/test_cli.py` para cobertura.

---
*Gerado automaticamente em pin jan 07 2026 19:41:03 -02*
