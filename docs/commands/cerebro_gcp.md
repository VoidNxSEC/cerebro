# cerebro gcp

> **Requires:** `GCP_PROJECT_ID` env var and Google Cloud SDK credentials (`gcloud auth application-default login`).
> These commands are optional — Cerebro works fully offline without them.

Optional Google Cloud integration utilities for Discovery Engine (Vertex AI Search).

## Commands

### `cerebro gcp status`

Show GCP project status, available data stores, and API connectivity.

```bash
export GCP_PROJECT_ID=<your-gcp-project-id>
cerebro gcp status
```

---

### `cerebro gcp create-engine`

Create a Discovery Engine search app backed by an existing data store.

```bash
cerebro gcp create-engine --project <project-id> --engine <engine-id>
```

---

### `cerebro gcp monitor`

Monitor GCP billing for Discovery Engine API usage.

```bash
cerebro gcp monitor --project <project-id>
```

---

### `cerebro gcp burn`

Execute batch queries against a Discovery Engine for load testing.

```bash
cerebro gcp burn --queries 500 --workers 20 --project <project-id> --engine <engine-id>
```

| Flag | Description |
|------|-------------|
| `--queries` | Number of queries to execute (default: 100) |
| `--workers` | Parallel workers (default: 10) |
| `--project` | GCP Project ID (required) |
| `--engine` | Search engine ID (required) |
| `--rate-limit` | Queries per second limit |
| `--output` | Output JSON file for results |
