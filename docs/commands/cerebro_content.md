# cerebro content

Content mining and analysis from external sources.

## Commands

### `cerebro content mine`

Mine valuable content from URLs or local file paths and index it into the knowledge base.

```bash
cerebro content mine --sources "https://example.com/article,./local-doc.md"
cerebro content mine --sources "https://blog.example.com" --depth 3 --format markdown
```

| Flag | Description |
|------|-------------|
| `--sources` | Comma-separated URLs or file paths (required) |
| `--output` | Output file (default: `content_analysis.json`) |
| `--depth` | Mining depth 1–5 (default: 2) |
| `--categories` | Filter by content categories |
| `--format` | Output format: `json`, `markdown`, or `html` (default: `json`) |

---

### `cerebro content analyze`

Analyze a single content file in detail.

```bash
cerebro content analyze ./article.md
cerebro content analyze ./code-sample.py --type code --no-metrics
```

| Argument/Flag | Description |
|---------------|-------------|
| `FILE` | Content file to analyze (required) |
| `--type` | `auto`, `blog`, `article`, `code`, or `docs` (default: `auto`) |
| `--metrics` | Include detailed metrics (default: on) |
