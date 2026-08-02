# Phase 2: CLI Integration - Implementation Roadmap

**Status**: 📋 **READY TO START**
**Depends On**: Phase 1 (✅ Complete)
**Estimated Duration**: Week 2

---

## 🎯 Objectives

Transform 15 standalone scripts into unified CLI commands organized into logical groups.

---

## 📋 Pre-Implementation Checklist

Before starting Phase 2, verify Phase 1 is complete:

- [x] TUI infrastructure created
- [x] Backend API paths fixed
- [x] WebSocket subscriptions working
- [x] Smart launcher implemented
- [x] Dependencies installed
- [x] Entry points updated

---

## 📂 Scripts to Migrate

### Audit of `scripts/` Directory

Run this to find all scripts:

```bash
ls -la scripts/*.py | grep -v "__" | wc -l
```

**Expected Scripts** (15 total):

1. `batch_burn.py` → `cerebro gcp burn`
2. `monitor_credits.py` → `cerebro gcp monitor`
3. `create_search_engine.py` → `cerebro gcp create-engine`
4. `strategy_optimizer.py` → `cerebro strategy optimize`
5. `salary_intel.py` → `cerebro strategy salary`
6. `personal_moat_builder.py` → `cerebro strategy moat`
7. `trend_predictor.py` → `cerebro strategy trends`
8. `content_gold_miner.py` → `cerebro content mine`
9. `grounded_search.py` → `cerebro test grounded-search`
10. `grounded_generation_test.py` → `cerebro test grounded-gen`
11. `verify_grounded_api.py` → `cerebro test verify-api`
12. `generate_queries.py` → `cerebro knowledge generate-queries`
13. `index_repository.py` → `cerebro knowledge index-repo`
14. `etl_docs.py` → `cerebro knowledge etl`
15. `generate_docs.py` → `cerebro knowledge docs`

---

## 🏗️ Implementation Steps

### Step 1: Create Command Module Structure

Create 4 new command modules:

```bash
touch src/phantom/commands/__init__.py
touch src/phantom/commands/gcp.py
touch src/phantom/commands/strategy.py
touch src/phantom/commands/content.py
touch src/phantom/commands/testing.py
```

**Template for each module**:

```python
"""
Cerebro CLI - [GROUP NAME] Commands

Migrated from standalone scripts in scripts/
"""

import typer
from rich.console import Console
from pathlib import Path

# Create Typer app for this group
[group]_app = typer.Typer(help="[Description]")
console = Console()


@[group]_app.command("command-name")
def command_function(
    param: str = typer.Option(..., help="Parameter description"),
):
    """
    Command description.

    Migrated from: scripts/original_script.py
    """
    try:
        # Implementation here
        console.print("[green]✓[/green] Success")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

### Step 2: Migrate GCP Commands (3 commands)

**File**: `src/phantom/commands/gcp.py`

```python
"""
Cerebro CLI - GCP Commands

Google Cloud Platform credit management and search engine utilities.
"""

import typer
from rich.console import Console

gcp_app = typer.Typer(help="GCP Credits & Search Engine Management")
console = Console()


@gcp_app.command("burn")
def batch_burn(
    queries: int = typer.Option(100, help="Number of queries to execute"),
    workers: int = typer.Option(10, help="Number of parallel workers"),
    engine_id: str = typer.Option(..., help="Search engine ID"),
):
    """
    Execute batch query burn for GCP credit consumption.

    Migrated from: scripts/batch_burn.py
    """
    # TODO: Migrate logic from batch_burn.py
    pass


@gcp_app.command("monitor")
def monitor_credits(
    interval: int = typer.Option(60, help="Update interval in seconds"),
    alert_threshold: float = typer.Option(10.0, help="Alert when credits below this"),
):
    """
    Monitor GCP credit usage in real-time.

    Migrated from: scripts/monitor_credits.py
    """
    # TODO: Migrate logic from monitor_credits.py
    pass


@gcp_app.command("create-engine")
def create_search_engine(
    name: str = typer.Option(..., help="Search engine name"),
    config: str = typer.Option("config.yaml", help="Configuration file"),
):
    """
    Create a new GCP search engine instance.

    Migrated from: scripts/create_search_engine.py
    """
    # TODO: Migrate logic from create_search_engine.py
    pass
```

### Step 3: Migrate Strategy Commands (4 commands)

**File**: `src/phantom/commands/strategy.py`

```python
"""
Cerebro CLI - Strategy Commands

Career strategy, salary intelligence, and trend analysis tools.
"""

import typer
from rich.console import Console

strategy_app = typer.Typer(help="Career Strategy & Intelligence")
console = Console()


@strategy_app.command("optimize")
def optimize_strategy(
    profile: str = typer.Option(..., help="Career profile JSON"),
    market: str = typer.Option("tech", help="Target market"),
):
    """
    Optimize career strategy based on market analysis.

    Migrated from: scripts/strategy_optimizer.py
    """
    # TODO: Migrate logic
    pass


@strategy_app.command("salary")
def salary_intelligence(
    role: str = typer.Option(..., help="Job role"),
    location: str = typer.Option(..., help="Location"),
    experience: int = typer.Option(..., help="Years of experience"),
):
    """
    Gather salary intelligence for target role.

    Migrated from: scripts/salary_intel.py
    """
    # TODO: Migrate logic
    pass


@strategy_app.command("moat")
def build_moat(
    skills: str = typer.Option(..., help="Comma-separated skills"),
    niche: str = typer.Option(..., help="Target niche"),
):
    """
    Build personal competitive moat analysis.

    Migrated from: scripts/personal_moat_builder.py
    """
    # TODO: Migrate logic
    pass


@strategy_app.command("trends")
def predict_trends(
    sector: str = typer.Option("technology", help="Industry sector"),
    horizon: int = typer.Option(12, help="Prediction horizon in months"),
):
    """
    Predict career and technology trends.

    Migrated from: scripts/trend_predictor.py
    """
    # TODO: Migrate logic
    pass
```

### Step 4: Migrate Content Commands (1 command)

**File**: `src/phantom/commands/content.py`

```python
"""
Cerebro CLI - Content Commands

Content mining and analysis tools.
"""

import typer
from rich.console import Console

content_app = typer.Typer(help="Content Mining & Analysis")
console = Console()


@content_app.command("mine")
def mine_content(
    sources: str = typer.Option(..., help="Content sources (URLs or paths)"),
    output: str = typer.Option("output.json", help="Output file"),
    depth: int = typer.Option(2, help="Mining depth"),
):
    """
    Mine valuable content from various sources.

    Migrated from: scripts/content_gold_miner.py
    """
    # TODO: Migrate logic
    pass
```

### Step 5: Migrate Testing Commands (3 commands)

**File**: `src/phantom/commands/testing.py`

```python
"""
Cerebro CLI - Testing Commands

Test utilities for grounded search and generation APIs.
"""

import typer
from rich.console import Console

testing_app = typer.Typer(help="API Testing & Validation", name="test")
console = Console()


@testing_app.command("grounded-search")
def test_grounded_search(
    query: str = typer.Option(..., help="Search query"),
    engine_id: str = typer.Option(..., help="Search engine ID"),
):
    """
    Test grounded search API functionality.

    Migrated from: scripts/grounded_search.py
    """
    # TODO: Migrate logic
    pass


@testing_app.command("grounded-gen")
def test_grounded_generation(
    prompt: str = typer.Option(..., help="Generation prompt"),
    context: str = typer.Option(None, help="Context documents"),
):
    """
    Test grounded generation API.

    Migrated from: scripts/grounded_generation_test.py
    """
    # TODO: Migrate logic
    pass


@testing_app.command("verify-api")
def verify_api(
    endpoint: str = typer.Option(..., help="API endpoint to verify"),
    method: str = typer.Option("GET", help="HTTP method"),
):
    """
    Verify grounded API endpoints.

    Migrated from: scripts/verify_grounded_api.py
    """
    # TODO: Migrate logic
    pass
```

### Step 6: Add Knowledge Commands (4 new)

**File**: `src/phantom/commands/knowledge.py` (modify existing)

Add these commands to the existing `knowledge_app`:

```python
@knowledge_app.command("generate-queries")
def generate_queries(
    topic: str = typer.Option(..., help="Topic for query generation"),
    count: int = typer.Option(50, help="Number of queries to generate"),
):
    """
    Generate search queries for a topic.

    Migrated from: scripts/generate_queries.py
    """
    # TODO: Migrate logic
    pass


@knowledge_app.command("index-repo")
def index_repository(
    repo_path: str = typer.Option(".", help="Repository path"),
    force: bool = typer.Option(False, help="Force re-indexing"),
):
    """
    Index a code repository for knowledge base.

    Migrated from: scripts/index_repository.py
    """
    # TODO: Migrate logic
    pass


@knowledge_app.command("etl")
def etl_docs(
    source: str = typer.Option(..., help="Documentation source"),
    destination: str = typer.Option(..., help="ETL destination"),
):
    """
    ETL pipeline for documentation processing.

    Migrated from: scripts/etl_docs.py
    """
    # TODO: Migrate logic
    pass


@knowledge_app.command("docs")
def generate_docs(
    project: str = typer.Option(".", help="Project path"),
    output: str = typer.Option("docs/", help="Output directory"),
):
    """
    Generate project documentation.

    Migrated from: scripts/generate_docs.py
    """
    # TODO: Migrate logic
    pass
```

### Step 7: Register Command Groups in CLI

**File**: `src/phantom/cli.py`

Add imports and register new groups:

```python
from phantom.commands.gcp import gcp_app
from phantom.commands.strategy import strategy_app
from phantom.commands.content import content_app
from phantom.commands.testing import testing_app

# Register groups
app.add_typer(gcp_app, name="gcp")
app.add_typer(strategy_app, name="strategy")
app.add_typer(content_app, name="content")
app.add_typer(testing_app, name="test")
```

### Step 8: Add Deprecation Warnings to Original Scripts

Add to each script in `scripts/`:

```python
import warnings

def main():
    warnings.warn(
        "This script is deprecated. Use: cerebro [group] [command]\n"
        "Example: cerebro gcp burn --queries 100",
        DeprecationWarning,
        stacklevel=2
    )
    # Original logic here
```

---

## ✅ Validation Checklist

After implementation, verify:

- [ ] All 4 new command modules created
- [ ] All 15 scripts migrated to CLI commands
- [ ] 4 commands added to knowledge group
- [ ] Command groups registered in cli.py
- [ ] `cerebro --help` shows all 7 groups
- [ ] `cerebro gcp --help` shows 3 commands
- [ ] `cerebro strategy --help` shows 4 commands
- [ ] `cerebro content --help` shows 1 command
- [ ] `cerebro test --help` shows 3 commands
- [ ] `cerebro knowledge --help` shows 7 commands (3 original + 4 new)
- [ ] Original scripts have deprecation warnings
- [ ] All commands execute without import errors

---

## 🧪 Testing Commands

```bash
# Test help for all groups
poetry run cerebro --help
poetry run cerebro gcp --help
poetry run cerebro strategy --help
poetry run cerebro content --help
poetry run cerebro test --help
poetry run cerebro knowledge --help

# Test individual commands
poetry run cerebro gcp burn --help
poetry run cerebro strategy optimize --help
poetry run cerebro content mine --help
poetry run cerebro test grounded-search --help
poetry run cerebro knowledge generate-queries --help
```

---

## 📊 Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Scripts migrated | 15 | ⏳ |
| Command groups created | 4 | ⏳ |
| Commands in knowledge group | 7 (3+4) | ⏳ |
| Total commands accessible | 24 | ⏳ |
| Original commands preserved | 9 | ✅ |
| Deprecation warnings added | 15 | ⏳ |

---

## 🚀 Ready to Start

Phase 2 roadmap is complete. Begin with Step 1: Create command module structure.

**Next Action**: Create `src/phantom/commands/gcp.py` and start migrating batch_burn.py

---

**Phase 2 Status**: 📋 **READY**
**Dependencies**: Phase 1 ✅ Complete
**Start Date**: When approved
