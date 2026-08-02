# GCP Credit Management

GCP Credit Management is **one feature** of the Cerebro platform. It provides tools for
batch query execution, credit monitoring, and search engine management using Google Cloud
Discovery Engine.

## Commands

| Command | Description |
|---------|-------------|
| `cerebro gcp burn` | Execute batch queries for load testing and credit utilization |
| `cerebro gcp monitor` | Monitor GCP credit usage in real-time |
| `cerebro gcp create-engine` | Create a new Discovery Engine search engine |
| `cerebro gcp status` | Check GCP SDK and authentication status |

## Configuration

Set the following environment variables:

```bash
export GCP_PROJECT_ID='<your-gcp-project-id>'
export DATA_STORE_ID='<your-data-store-id>'
```

## Documentation

- [Credit Management Details](CREDIT_BURNER_DETAILED.md)
- [Quick Start Guide](README_SPEEDRUN.md)
- [High-ROI Queries](HIGH_ROI_QUERIES.md)
- [Automation Systems](AUTOMATION_SYSTEMS.md)
