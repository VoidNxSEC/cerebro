# cerebro metrics

Zero-token repository metrics and tracking. No LLM calls — pure static analysis.

## Commands

### `cerebro metrics scan`

Full scan of all git repositories discovered under `CEREBRO_ARCH_PATH`.

```bash
cerebro metrics scan
cerebro metrics scan --verbose
```

Collects: commit history, contributors, branches, lines of code by language, dependency manifests, regex-based secret pattern detection.

---

### `cerebro metrics watch`

Interactive real-time watcher — live dashboard that refreshes as repos change.

```bash
cerebro metrics watch
```

---

### `cerebro metrics report`

Detailed report for a single repository.

```bash
cerebro metrics report /path/to/repo
```

---

### `cerebro metrics compare`

Compare metrics across two or more repositories side by side.

```bash
cerebro metrics compare /repo-a /repo-b
```

---

### `cerebro metrics check`

Quick health check across all tracked repos.

```bash
cerebro metrics check
```
