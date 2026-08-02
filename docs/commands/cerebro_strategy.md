# cerebro strategy

> **Requires:** A configured LLM provider (`CEREBRO_LLM_PROVIDER` and associated credentials).

Career and technology strategy intelligence powered by the RAG knowledge base.

## Commands

### `cerebro strategy optimize`

Optimize strategy based on ROI analysis across the knowledge base.

```bash
cerebro strategy optimize --goal balanced
cerebro strategy optimize --goal immediate_value --budget 500
cerebro strategy optimize --goal long_term_moat --output strategy.json --execute
```

| Flag | Description |
|------|-------------|
| `--goal` | `immediate_value`, `long_term_moat`, or `balanced` (default) |
| `--budget` | Budget in BRL (default: 10.0) |
| `--output` | Save results to JSON file |
| `--execute` | Execute recommended scripts automatically |

---

### `cerebro strategy salary`

Salary intelligence and negotiation analysis.

```bash
cerebro strategy salary --role "Senior Engineer" --company FAANG --location Remote_Brazil
cerebro strategy salary --role "Staff Engineer" --level E6 --output salary_report.json
```

| Flag | Description |
|------|-------------|
| `--role` | Job role (required) |
| `--company` | Target company or category |
| `--level` | Career level (L3, E4, Senior, Staff…) |
| `--location` | Location or remote status (default: `Remote_Brazil`) |
| `--output` | Save report to file |

---

### `cerebro strategy moat`

Build a personal technical moat strategy based on rare skill combinations in the knowledge base.

```bash
cerebro strategy moat
```

---

### `cerebro strategy trends`

Predict technology trends from the indexed knowledge base.

```bash
cerebro strategy trends
```
