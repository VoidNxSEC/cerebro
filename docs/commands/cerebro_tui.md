# Command: `cerebro tui`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `root` |
| Command | `tui` |
| Function | `launch_tui` |
| Source | `src/cerebro/cli.py:152` |
| Syntax | `cerebro tui` |

## 1. Description
Launch interactive Terminal User Interface (TUI).

Full-featured interface with:
  • Dashboard with system metrics
  • Project management and analysis
  • Intelligence queries with history
  • Script launcher with progress
  • GCP credit monitoring
  • Live log viewer

Keyboard shortcuts:
  q - Quit
  d - Dashboard
  p - Projects
  i - Intelligence
  s - Scripts
  g - GCP Credits
  l - Logs

**Syntax:**
```bash
cerebro tui
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|
| - | - | - | - | - | - | - |

## 3. Examples
```bash
cerebro tui
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `launch_tui`
* Line: `152`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at qui 16 abr 2026 22:56:34 -03*
