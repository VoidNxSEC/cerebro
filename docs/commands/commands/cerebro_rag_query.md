# Command: `cerebro rag query`

## 1. Descrição
Consulta o RAG Local e exibe métricas de precisão.

**Sintaxe:**
```bash
cerebro rag query [OPTIONS] [ARGS]
```

## 2. Parâmetros

| Nome | Tipo | Default | Descrição |
|------|------|---------|-----------|| `question` | `str` | `Required` | - |


## 3. Exemplos
```bash
# Exemplo padrão
cerebro rag query
```

## 4. Saída
* **Formato:** Texto Rich (Console) ou JSON (se aplicável).
* **Logs:** Erros são enviados para stderr.

## 5. Erros Comuns
* `Exit Code 1`: Falha na execução ou dependência ausente.

## 6. Dependências
* Módulo: `src/phantom/cli.py`
* Função: `rag_query`

## 7. Testes
* Verifique `tests/test_cli.py` para cobertura.

---
*Gerado automaticamente em pin jan 07 2026 19:41:03 -02*
