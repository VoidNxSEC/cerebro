# Command: `cerebro knowledge summarize`

## 1. Descrição
Cria Vector DB Local (Chroma) para alta precisão.

**Sintaxe:**
```bash
cerebro knowledge summarize [OPTIONS] [ARGS]
```

## 2. Parâmetros

| Nome | Tipo | Default | Descrição |
|------|------|---------|-----------|| `repo_name` | `str)` | `Required` | - |
| `f"Context` | `{m.get('task_context')}"` | `Required` | - |
| `f"LoC` | `{m.get('loc')}"` | `Required` | - |
| `[]))` | `report.append(f"- ⚠️ {h}")     (path / "EXECUTIVE_REPORT.md").write_text("\n".join(report))     console.print(f"[green✅ Relatório` | `Required` | - |


## 3. Exemplos
```bash
# Exemplo padrão
cerebro knowledge summarize
```

## 4. Saída
* **Formato:** Texto Rich (Console) ou JSON (se aplicável).
* **Logs:** Erros são enviados para stderr.

## 5. Erros Comuns
* `Exit Code 1`: Falha na execução ou dependência ausente.

## 6. Dependências
* Módulo: `src/phantom/cli.py`
* Função: `summarize`

## 7. Testes
* Verifique `tests/test_cli.py` para cobertura.

---
*Gerado automaticamente em pin jan 07 2026 19:41:03 -02*
