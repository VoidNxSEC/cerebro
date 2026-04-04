# Cerebro Documentation

This directory contains the documentation for **Cerebro**, organized around a
standalone, local-first product model with optional vendor-specific integrations.

## Documentation Layout

```text
docs/
  architecture/   System design, ADRs, data flow
  commands/       CLI command reference
  features/       Feature-specific documentation
    intelligence/ Core analysis and intelligence features
    gcp-credits/  Optional GCP-specific workflows
    strategy/     Planning and value documents
  guides/         Setup, cheatsheets, CI/CD, dashboard, shortcuts
  phases/         Historical implementation milestones
  project/        Status, roadmap, audits, execution plans
  i18n/           Portuguese reference material
```

## Reading Order

### Core product

- [Quick Start](guides/QUICK_START.md)
- [CLI Commands](commands/README.md)
- [Architecture Overview](architecture/ARCHITECTURE.md)
- [ADR Summary](architecture/ADR_SUMMARY.md)

### Interfaces and operations

- [Keyboard Shortcuts](guides/KEYBOARD_SHORTCUTS.md)
- [Dashboard Integration](guides/DASHBOARD_INTEGRATION.md)
- [GitLab CI/CD](guides/GITLAB_CI_CD.md)
- [Contributing](guides/CONTRIBUTING_DOCS.md)

### Integration-specific material

- [GCP Credits Overview](features/gcp-credits/README.md)
- [Automation Systems](features/gcp-credits/AUTOMATION_SYSTEMS.md)
- [High-ROI Queries](features/gcp-credits/HIGH_ROI_QUERIES.md)

These integration-specific documents describe optional workflows; they are not
required to use the Cerebro core.

### Planning and status

- [Master Execution Plan](project/MASTER_EXECUTION_PLAN.md)
- [Status](project/STATUS.md)
- [Coverage Gaps](project/COVERAGE_GAP.md)
- [Portfolio Audit](project/PORTFOLIO_AUDIT.md)
