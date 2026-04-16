#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import yaml

# Fast imports for CLI responsiveness
try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    # If basic dependencies are missing, we can't do much
    sys.exit(1)

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()

# Original command groups
knowledge_app = typer.Typer(help="Analysis & Auditing", no_args_is_help=True)
ops_app = typer.Typer(help="Operational Status", no_args_is_help=True)
rag_app = typer.Typer(help="RAG & Vectors (LangChain)", no_args_is_help=True)
rag_backend_app = typer.Typer(help="Active RAG backend operations", no_args_is_help=True)
rag_backends_app = typer.Typer(help="Available RAG backends", no_args_is_help=True)

# New command groups (Phase 2) — guarded because some deps (google-auth) may be absent
try:
    from cerebro.commands.setup import setup_app
except ImportError:
    setup_app = None  # type: ignore[assignment]

try:
    from cerebro.commands.metrics import metrics_app
except ImportError:
    metrics_app = None  # type: ignore[assignment]

try:
    from cerebro.commands.gcp import gcp_app
except ImportError:
    gcp_app = None  # type: ignore[assignment]

try:
    from cerebro.commands.strategy import strategy_app
except ImportError:
    strategy_app = None  # type: ignore[assignment]

try:
    from cerebro.commands.content import content_app
except ImportError:
    content_app = None  # type: ignore[assignment]

try:
    from cerebro.commands.testing import testing_app
except ImportError:
    testing_app = None  # type: ignore[assignment]

# Register all command groups
app.add_typer(knowledge_app, name="knowledge")
app.add_typer(ops_app, name="ops")
app.add_typer(rag_app, name="rag")
rag_app.add_typer(rag_backend_app, name="backend")
rag_app.add_typer(rag_backends_app, name="backends")
if setup_app:
    app.add_typer(setup_app, name="setup")
if metrics_app:
    app.add_typer(metrics_app, name="metrics")
if gcp_app:
    app.add_typer(gcp_app, name="gcp")
if strategy_app:
    app.add_typer(strategy_app, name="strategy")
if content_app:
    app.add_typer(content_app, name="content")
if testing_app:
    app.add_typer(testing_app, name="test")


def load_config(config_path: str):
    path = Path(config_path)
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


@app.command("info")
def info():
    """
    Display Cerebro environment information.
    """
    import importlib.util

    from cerebro import __version__
    title = f"[bold]CEREBRO[/bold] - Enterprise Knowledge Platform v{__version__}"
    console.print(Panel(title, border_style="cyan"))

    # Check dependencies
    deps = {"GCP Integration": False, "LangChain/RAG": False, "Code Analysis": False}

    if importlib.util.find_spec("google.cloud"):
        deps["GCP Integration"] = True
    if importlib.util.find_spec("langchain"):
        deps["LangChain/RAG"] = True
    if importlib.util.find_spec("tree_sitter"):
        deps["Code Analysis"] = True

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component")
    table.add_column("Status")

    for k, v in deps.items():
        table.add_row(
            k, "[green]Installed[/green]" if v else "[yellow]Missing[/yellow]"
        )

    console.print(table)


@app.command("version")
def version():
    """
    Display the current version.
    """
    from cerebro import __version__
    console.print(f"Cerebro CLI v{__version__}")


@app.command("dashboard")
def launch_dashboard():
    """Launch the React Dashboard GUI (FastAPI backend + Vite frontend)."""
    from cerebro.launcher import launch_gui
    launch_gui()


@app.command("tui")
def launch_tui():
    """
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
    """
    try:
        from cerebro.tui import get_app
        CerebroApp = get_app()
        app = CerebroApp()
        app.run()
    except ImportError as e:
        console.print(f"[red]Error:[/red] TUI dependencies missing: {e}")
        console.print("Install with: poetry install")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error launching TUI:[/red] {e}")
        raise typer.Exit(1)


@knowledge_app.command("analyze")
def analyze(
    repo_path: str,
    task_context: str = "General Review",
    config_file: str = "./config/repos.yaml",
):
    """
    Extract AST and generate JSONL.
    Usage: cerebro knowledge analyze ./repo "Context"
    """
    # Lazy imports
    from cerebro.core.extraction.analyze_code import (
        HermeticAnalyzer,
        validate_repository_path,
    )

    target = Path(repo_path).expanduser().resolve()
    validate_repository_path(target)

    # Load config to find hooks for this repo
    config = load_config(config_file)
    repo_config = next(
        (
            r
            for r in config.get("repos", [])
            if Path(r.get("path", "")).resolve() == target
        ),
        {},
    )

    if repo_config:
        console.print(
            f"📖 Configuration found for: [cyan]{repo_config.get('name')}[/cyan]"
        )
        if "context" in repo_config:
            task_context = repo_config["context"]

    console.print(f"🔬 Analyzing: [bold]{target.name}[/bold]")
    analyzer = HermeticAnalyzer(config)

    # Pass hooks to analyzer
    result = analyzer.analyze_repo(target, hooks=repo_config.get("hooks"))
    result["metrics"]["task_context"] = task_context

    out = Path("./data/analyzed") / target.name
    out.mkdir(parents=True, exist_ok=True)

    with open(out / "metrics.json", "w") as f:
        json.dump(result["metrics"], f, indent=2)
    with open(out / "artifacts.json", "w") as f:
        json.dump([a.__dict__ for a in result["artifacts"]], f)

    # Append to global JSONL
    jsonl = Path("./data/analyzed/all_artifacts.jsonl")
    mode = "a" if jsonl.exists() else "w"
    with open(jsonl, mode) as f:
        for a in result["artifacts"]:
            doc = {
                "id": f"{target.name}-{a.name}",
                "jsonData": json.dumps(
                    {
                        "title": a.name,
                        "content": a.content,
                        "repo": target.name,
                        "metrics": result["metrics"],
                        "context": task_context,
                    }
                ),
            }
            f.write(json.dumps(doc) + "\n")

    console.print(f"[green]✅ Extracted: {len(result['artifacts'])} artifacts.[/green]")


@knowledge_app.command("batch-analyze")
def batch_analyze(config_file: str = "./config/repos.yaml"):
    """
    Process all repositories defined in the configuration file.
    """
    config = load_config(config_file)
    repos = config.get("repos", [])

    if not repos:
        console.print(
            "[yellow]⚠️  No repositories found in configuration.[/yellow]"
        )
        return

    console.print(f"🚀 Starting batch analysis of {len(repos)} repositories...")

    for repo in repos:
        path = repo.get("path")
        name = repo.get("name")
        priority = repo.get("priority", "medium")

        if not path:
            continue

        console.print(
            f"\n[bold magenta]📦 Processing: {name} ({priority})[/bold magenta]"
        )

        try:
            analyze(path, config_file=config_file)
        except Exception as e:
            console.print(f"[red]❌ Failed to process {name}: {e}[/red]")

    console.print("\n[green]✨ Batch Analysis Complete![/green]")


@knowledge_app.command("summarize")
def summarize(repo_name: str):
    path = Path("./data/analyzed") / repo_name
    if not (path / "metrics.json").exists():
        return
    with open(path / "metrics.json") as f:
        m = json.load(f)

    report = [
        f"# REPORT: {repo_name.upper()}",
        f"Context: {m.get('task_context')}",
        f"LoC: {m.get('loc')}",
    ]
    for h in set(m.get("security_hints", []) + m.get("performance_hints", [])):
        report.append(f"- ⚠️ {h}")
    (path / "EXECUTIVE_REPORT.md").write_text("\n".join(report))
    console.print(f"[green]✅ Report: {path}/EXECUTIVE_REPORT.md[/green]")


@knowledge_app.command("generate-queries")
def generate_queries(
    topic: str = typer.Argument(..., help="Topic for query generation"),
    count: int = typer.Option(50, "--count", help="Number of queries to generate"),
    output: Path = typer.Option("queries.json", "--output", help="Output file"),
):
    """
    Generate search queries for a topic.

    Creates diverse, high-quality queries for testing and knowledge expansion.

    Example:
        cerebro knowledge generate-queries "NixOS configuration" -c 100

    Migrated from: scripts/generate_queries.py
    """
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        from generate_queries import QueryGenerator

        console.print(f"🔍 Generating {count} queries about: [cyan]{topic}[/cyan]")

        generator = QueryGenerator()
        queries = generator.generate(topic, count)

        # Save to file
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w') as f:
            json.dump(queries, f, indent=2)

        console.print(f"[green]✅ Generated {len(queries)} queries → {output}[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@knowledge_app.command("index-repo")
def index_repository(
    repo_path: str = typer.Argument(".", help="Repository path to index"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-indexing"),
    output: str | None = typer.Option(None, "--output", help="Output directory"),
):
    """
    Index a code repository for knowledge base.

    Extracts code structure, documentation, and metadata for indexing.

    Example:
        cerebro knowledge index-repo ~/projects/myapp --force

    Migrated from: scripts/index_repository.py
    """
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        from index_repository import RepositoryIndexer

        repo = Path(repo_path).expanduser().resolve()

        if not repo.exists():
            console.print(f"[red]❌ Repository not found: {repo}[/red]")
            return

        console.print(f"📚 Indexing repository: [cyan]{repo.name}[/cyan]")

        indexer = RepositoryIndexer(output_dir=output)
        result = indexer.index(repo, force=force)

        console.print(f"[green]✅ Indexed {result['files']} files, {result['symbols']} symbols[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@knowledge_app.command("etl")
def etl_docs(
    source: str = typer.Argument(..., help="Documentation source (URL or path)"),
    destination: str = typer.Argument(..., help="ETL destination path"),
    format: str = typer.Option("json", "--format", help="Output format: json, jsonl, markdown"),
):
    """
    ETL pipeline for documentation processing.

    Extracts, transforms, and loads documentation from various sources
    into structured format for indexing.

    Example:
        cerebro knowledge etl https://docs.example.com ./data/docs

    Migrated from: scripts/etl_docs.py
    """
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        from etl_docs import DocumentationETL

        console.print(f"📄 ETL: [cyan]{source}[/cyan] → [green]{destination}[/green]")

        etl = DocumentationETL(format=format)
        result = etl.process(source, destination)

        console.print(f"[green]✅ Processed {result['documents']} documents[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@knowledge_app.command("docs")
def generate_docs(
    project: str = typer.Argument(".", help="Project path"),
    output: str = typer.Option("docs/", "--output", help="Output directory"),
    format: str = typer.Option("markdown", "--format", help="Documentation format"),
):
    """
    Generate project documentation automatically.

    Analyzes code and generates comprehensive documentation with
    API references, guides, and examples.

    Example:
        cerebro knowledge docs ~/projects/myapp -o ./docs

    Migrated from: scripts/generate_docs.py
    """
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
        from generate_docs import DocumentationGenerator

        project_path = Path(project).expanduser().resolve()

        if not project_path.exists():
            console.print(f"[red]❌ Project not found: {project_path}[/red]")
            return

        console.print(f"📖 Generating documentation for: [cyan]{project_path.name}[/cyan]")

        generator = DocumentationGenerator(format=format)
        result = generator.generate(project_path, output)

        console.print(f"[green]✅ Generated {result['pages']} pages → {output}[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@rag_app.command("ingest")
def rag_ingest(source_file: str = "./data/analyzed/all_artifacts.jsonl"):
    """
    Ingest artifacts into the active RAG backend.
    """
    try:
        from cerebro.core.rag.engine import RigorousRAGEngine
    except ImportError:
        console.print("[red]❌ RAG dependencies missing. Run: nix develop --command cerebro rag ingest[/red]")
        return

    engine = RigorousRAGEngine()
    backend = "Vertex AI" if engine._uses_vertex_backend() else "local vector store"
    console.print(f"🧠 [bold]Ingesting artifacts into {backend}...[/bold]")
    try:
        count = engine.ingest(source_file)
        console.print(f"[green]✅ Ingested {count} artifacts.[/green]")
        if engine._uses_vertex_backend():
            console.print("[yellow]ℹ️  Indexing runs asynchronously on Google Cloud.[/yellow]")
            console.print("💡 Monitor at: [link]https://console.cloud.google.com/gen-app-builder/data-stores[/link]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@rag_app.command("init")
def rag_init():
    """
    Initialize backend-specific storage structures for the active RAG backend.
    """
    try:
        from cerebro.core.rag.engine import RigorousRAGEngine
    except ImportError:
        console.print("[red]❌ RAG dependencies missing. Run: nix develop --command cerebro rag init[/red]")
        return

    engine = RigorousRAGEngine()
    console.print("🧱 [bold]Initializing RAG backend...[/bold]")

    try:
        details = engine.initialize_runtime()
        backend = details.get("backend", engine.vector_store_provider.backend_name)
        console.print(f"[green]✅ Backend initialized: {backend}[/green]")

        details_table = Table(title="RAG Backend Initialization")
        details_table.add_column("Key", style="cyan")
        details_table.add_column("Value", style="white")
        for key in sorted(details):
            details_table.add_row(str(key), str(details[key]))
        console.print(details_table)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@rag_app.command("smoke")
def rag_smoke(
    output_format: str = typer.Option("table", "--format", help="Output format: table or json"),
    skip_write_check: bool = typer.Option(
        False,
        "--skip-write-check",
        help="Skip the temporary write/read/delete validation cycle",
    ),
):
    """
    Run a backend smoke test against the active RAG runtime.
    """
    try:
        from cerebro.core.rag.engine import RigorousRAGEngine
    except ImportError:
        console.print("[red]❌ RAG dependencies missing. Run: nix develop --command cerebro rag smoke[/red]")
        return

    engine = RigorousRAGEngine()
    result = engine.run_smoke_test(write_check=not skip_write_check)

    if output_format == "json":
        console.print_json(json.dumps(result))
        return

    summary = Table(title="CEREBRO RAG Smoke Test")
    summary.add_column("Field", style="cyan")
    summary.add_column("Value", style="magenta")
    summary.add_row("Healthy", "yes" if result["healthy"] else "no")
    summary.add_row("Backend", str(result["backend"]))
    summary.add_row("Namespace", str(result.get("namespace") or "-"))
    summary.add_row("Write Check", "yes" if result.get("write_check") else "no")
    summary.add_row(
        "Document Count",
        str(result["document_count"]) if result.get("document_count") is not None else "-",
    )
    summary.add_row("Query Hits", str(result.get("query_hits", 0)))
    if result.get("error"):
        summary.add_row("Error", str(result["error"]))
    console.print(summary)

    steps_table = Table(title="Smoke Steps")
    steps_table.add_column("Step", style="cyan")
    steps_table.add_column("Status", style="white")
    steps_table.add_column("Detail", style="magenta")
    for step in result.get("steps", []):
        steps_table.add_row(
            str(step.get("name", "-")),
            "ok" if step.get("ok") else "fail",
            str(step.get("detail", "")),
        )
    console.print(steps_table)


@rag_app.command("migrate")
def rag_migrate(
    from_provider: str = typer.Option("chroma", "--from-provider", help="Source vector store backend"),
    from_collection: str | None = typer.Option(None, "--from-collection", help="Source collection/table name"),
    from_namespace: str | None = typer.Option(None, "--from-namespace", help="Source namespace override"),
    from_persist_directory: str | None = typer.Option(
        None,
        "--from-persist-directory",
        help="Source local persistence path for embedded backends",
    ),
    from_url: str | None = typer.Option(None, "--from-url", help="Source DSN/URL for remote backends"),
    from_schema: str | None = typer.Option(None, "--from-schema", help="Source SQL schema for pgvector"),
    batch_size: int = typer.Option(200, "--batch-size", help="Documents per migration batch"),
    clear_destination: bool = typer.Option(
        False,
        "--clear-destination",
        help="Clear the active destination namespace before copying data",
    ),
    output_format: str = typer.Option("table", "--format", help="Output format: table or json"),
):
    """
    Migrate stored vectors from a source backend into the active RAG backend.
    """
    try:
        from cerebro.core.rag.engine import RigorousRAGEngine
        from cerebro.providers.vector_store_factory import build_vector_store_provider
        from cerebro.providers.vector_store_factory import resolve_vector_store_provider_alias
        from cerebro.settings import get_settings
    except ImportError:
        console.print("[red]❌ RAG dependencies missing. Run: nix develop --command cerebro rag migrate[/red]")
        return

    settings = get_settings()
    destination_provider_name = resolve_vector_store_provider_alias(settings.vector_store_provider)
    source_provider_name = resolve_vector_store_provider_alias(from_provider)
    same_backend_without_overrides = (
        source_provider_name == destination_provider_name
        and from_collection is None
        and from_namespace is None
        and from_persist_directory is None
        and from_url is None
        and from_schema is None
    )
    if same_backend_without_overrides:
        console.print(
            "[red]❌ Source backend matches the active destination backend with no override. "
            "Provide explicit source parameters or choose a different --from-provider.[/red]"
        )
        return

    engine = RigorousRAGEngine()
    source_provider = build_vector_store_provider(
        provider_name=from_provider,
        persist_directory=from_persist_directory,
        collection_name=from_collection,
        namespace=from_namespace,
        url=from_url,
        schema=from_schema,
    )

    result = engine.migrate_documents(
        source_provider,
        source_namespace=from_namespace,
        batch_size=batch_size,
        clear_destination=clear_destination,
    )

    if output_format == "json":
        console.print_json(json.dumps(result))
        return

    table = Table(title="CEREBRO RAG Migration")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Source Backend", str(result["source_backend"]))
    table.add_row("Destination Backend", str(result["destination_backend"]))
    table.add_row("Source Namespace", str(result.get("source_namespace") or "-"))
    table.add_row("Destination Namespace", str(result.get("destination_namespace") or "-"))
    table.add_row("Source Count", str(result["source_count"]))
    table.add_row("Migrated Count", str(result["migrated_count"]))
    table.add_row("Destination Before", str(result["destination_count_before"]))
    table.add_row("Destination After", str(result["destination_count_after"]))
    table.add_row("Batch Size", str(result["batch_size"]))
    table.add_row("Batches", str(result["batches"]))
    table.add_row("Cleared Destination", "yes" if result["cleared_destination"] else "no")
    console.print(table)


@rag_app.command("status")
def rag_status(
    output_format: str = typer.Option("table", "--format", help="Output format: table or json"),
):
    """
    Show the configured production RAG runtime status.
    """
    try:
        from cerebro.core.rag.engine import get_rag_runtime_status_snapshot
    except ImportError:
        console.print("[red]❌ RAG dependencies missing. Run: nix develop --command cerebro rag status[/red]")
        return

    status = get_rag_runtime_status_snapshot()

    if output_format == "json":
        console.print_json(json.dumps(status))
        return

    table = Table(title="CEREBRO RAG Runtime")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Healthy", "yes" if status["healthy"] else "no")
    table.add_row("Mode", str(status["mode"]))
    table.add_row("Backend", str(status["backend"]))
    table.add_row("LLM Provider", str(status["llm_provider"]))
    table.add_row("Namespace", str(status.get("namespace") or "—"))
    table.add_row("Collection", str(status.get("collection_name") or "—"))
    table.add_row(
        "Document Count",
        str(status["document_count"]) if status.get("document_count") is not None else "—",
    )
    if status.get("error"):
        table.add_row("Error", str(status["error"]))

    console.print(table)

    details = status.get("details") or {}
    if details:
        details_table = Table(title="Vector Store Details")
        details_table.add_column("Key", style="cyan")
        details_table.add_column("Value", style="white")
        for key in sorted(details):
            details_table.add_row(key, str(details[key]))
        console.print(details_table)


@rag_backends_app.command("list")
def rag_backends_list(
    output_format: str = typer.Option("table", "--format", help="Output format: table or json"),
):
    """
    List the vector store backends known by the current CLI build.
    """
    try:
        from cerebro.providers.vector_store_factory import (
            resolve_vector_store_provider_alias,
            supported_vector_store_aliases,
        )
        from cerebro.settings import get_settings
    except ImportError:
        console.print("[red]❌ RAG dependencies missing. Run: nix develop --command cerebro rag backends list[/red]")
        return

    settings = get_settings()
    active_backend = resolve_vector_store_provider_alias(settings.vector_store_provider)
    aliases = supported_vector_store_aliases()
    backends: dict[str, list[str]] = {}
    for alias, canonical in aliases.items():
        backends.setdefault(canonical, []).append(alias)

    payload = [
        {
            "backend": backend,
            "aliases": sorted(backend_aliases),
            "active": backend == active_backend,
        }
        for backend, backend_aliases in sorted(backends.items())
    ]

    if output_format == "json":
        console.print_json(json.dumps(payload))
        return

    table = Table(title="CEREBRO RAG Backends")
    table.add_column("Backend", style="cyan")
    table.add_column("Aliases", style="white")
    table.add_column("Active", style="magenta")
    for item in payload:
        table.add_row(
            item["backend"],
            ", ".join(item["aliases"]),
            "yes" if item["active"] else "no",
        )
    console.print(table)


@rag_backend_app.command("info")
def rag_backend_info(
    output_format: str = typer.Option("table", "--format", help="Output format: table or json"),
):
    """
    Show detailed information for the active RAG backend.
    """
    rag_status(output_format=output_format)


@rag_backend_app.command("health")
def rag_backend_health(
    output_format: str = typer.Option("table", "--format", help="Output format: table or json"),
):
    """
    Report whether the active RAG backend is healthy.
    """
    try:
        from cerebro.core.rag.engine import get_rag_runtime_status_snapshot
    except ImportError:
        console.print("[red]❌ RAG dependencies missing. Run: nix develop --command cerebro rag backend health[/red]")
        return

    status = get_rag_runtime_status_snapshot()
    payload = {
        "healthy": status["healthy"],
        "backend": status["backend"],
        "namespace": status.get("namespace"),
        "collection_name": status.get("collection_name"),
        "document_count": status.get("document_count"),
        "error": status.get("error"),
    }

    if output_format == "json":
        console.print_json(json.dumps(payload))
    else:
        table = Table(title="CEREBRO RAG Backend Health")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Healthy", "yes" if payload["healthy"] else "no")
        table.add_row("Backend", str(payload["backend"]))
        table.add_row("Namespace", str(payload.get("namespace") or "-"))
        table.add_row("Collection", str(payload.get("collection_name") or "-"))
        table.add_row(
            "Document Count",
            str(payload["document_count"]) if payload.get("document_count") is not None else "-",
        )
        if payload.get("error"):
            table.add_row("Error", str(payload["error"]))
        console.print(table)

    if not payload["healthy"]:
        raise typer.Exit(1)


@rag_backend_app.command("init")
def rag_backend_init():
    """
    Initialize storage structures for the active RAG backend.
    """
    rag_init()


@rag_backend_app.command("smoke")
def rag_backend_smoke(
    output_format: str = typer.Option("table", "--format", help="Output format: table or json"),
    skip_write_check: bool = typer.Option(
        False,
        "--skip-write-check",
        help="Skip the temporary write/read/delete validation cycle",
    ),
):
    """
    Run a smoke test against the active RAG backend.
    """
    rag_smoke(
        output_format=output_format,
        skip_write_check=skip_write_check,
    )


@rag_backend_app.command("migrate")
def rag_backend_migrate(
    from_provider: str = typer.Option("chroma", "--from-provider", help="Source vector store backend"),
    from_collection: str | None = typer.Option(None, "--from-collection", help="Source collection/table name"),
    from_namespace: str | None = typer.Option(None, "--from-namespace", help="Source namespace override"),
    from_persist_directory: str | None = typer.Option(
        None,
        "--from-persist-directory",
        help="Source local persistence path for embedded backends",
    ),
    from_url: str | None = typer.Option(None, "--from-url", help="Source DSN/URL for remote backends"),
    from_schema: str | None = typer.Option(None, "--from-schema", help="Source SQL schema for pgvector"),
    batch_size: int = typer.Option(200, "--batch-size", help="Documents per migration batch"),
    clear_destination: bool = typer.Option(
        False,
        "--clear-destination",
        help="Clear the active destination namespace before copying data",
    ),
    output_format: str = typer.Option("table", "--format", help="Output format: table or json"),
):
    """
    Migrate vectors from a source backend into the active backend.
    """
    rag_migrate(
        from_provider=from_provider,
        from_collection=from_collection,
        from_namespace=from_namespace,
        from_persist_directory=from_persist_directory,
        from_url=from_url,
        from_schema=from_schema,
        batch_size=batch_size,
        clear_destination=clear_destination,
        output_format=output_format,
    )


@rag_app.command("query")
def rag_query(
    question: str,
    rerank: bool = typer.Option(False, "--rerank", "-r", help="Rerank citations with cross‑encoder for better relevance"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results to retrieve"),
):
    """
    Query the active RAG backend with grounded generation.
    """
    try:
        from cerebro.core.rag.engine import RigorousRAGEngine
    except ImportError:
        console.print("[red]❌ RAG dependencies missing. Run: nix develop --command cerebro rag query[/red]")
        return

    engine = RigorousRAGEngine()

    with console.status(f"[cyan]Searching: {question}[/cyan]", spinner="dots"):
        result = engine.query_with_metrics(question, k=top_k)

    if result.get("error"):
        console.print(f"[red]❌ {result['answer']}[/red]")
        return

    # Display Answer
    console.print(
        Panel(result["answer"], title="🤖 CEREBRO — Grounded Answer", border_style="green")
    )

    # Display Metrics
    metrics = result["metrics"]
    table = Table(title="RAG Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Hit Rate", metrics["hit_rate_k"])
    table.add_row("Top Source", str(metrics["top_source"])[:80])
    table.add_row("Citations", str(len(metrics.get("citations", []))))
    table.add_row("Est. Cost", f"${metrics.get('cost_estimate_usd', 0.004):.4f}")

    console.print(table)

    # Show top snippet previews if available
    snippets = metrics.get("snippets", [])
    if snippets:
        console.print("\n[bold]🔍 Relevant Excerpts:[/bold]")
        for i, s in enumerate(snippets[:3], 1):
            preview = s[:200] + "..." if len(s) > 200 else s
            console.print(f"  [dim]{i}.[/dim] {preview}")

    if metrics.get("citations"):
        citations = metrics["citations"]
        if rerank:
            try:
                from cerebro.core.rerank_client import CerebroRerankerClient
            except ImportError:
                console.print("[yellow]⚠️  Reranker not available, skipping rerank.[/yellow]")
            else:
                with console.status("[cyan]Reranking citations...[/cyan]", spinner="dots"):
                    client = CerebroRerankerClient()
                    ranked = client.rerank(question, citations, top_k=len(citations))
                citations = [doc for _, _, doc in ranked]

        console.print("\n[bold]📚 Cited Sources:[/bold]")
        for c in citations:
            console.print(f"  • {c}")


@rag_app.command("rerank")
def rag_rerank(
    query: str = typer.Argument(..., help="Search query"),
    documents_file: str = typer.Option("./data/analyzed/all_artifacts.jsonl", "--documents", "-d", help="JSONL file containing documents"),
    top_k: int = typer.Option(10, "--top-k", "-k", help="Number of top results to return"),
):
    """
    Rerank documents using a cross‑encoder model (service or local fallback).
    """
    try:
        from cerebro.core.rerank_client import CerebroRerankerClient
    except ImportError:
        console.print("[red]❌ Reranker not available. Run: nix develop[/red]")
        return

    import json
    from pathlib import Path

    path = Path(documents_file)
    if not path.exists():
        console.print(f"[red]❌ Documents file not found: {path}[/red]")
        return

    # Load documents — support both flat {"content": "..."} and nested {"jsonData": "{...}"}
    documents = []
    with open(path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Flat content field
                text = data.get("content", "")
                # Nested jsonData field (double-encoded JSON)
                if not text and "jsonData" in data:
                    json_data = json.loads(data["jsonData"]) if isinstance(data["jsonData"], str) else data["jsonData"]
                    text = json_data.get("content", "")
                if text:
                    documents.append(text)
            except (json.JSONDecodeError, TypeError):
                console.print(f"[yellow]⚠️  Skipping malformed line {line_num}[/yellow]")

    if not documents:
        console.print("[yellow]⚠️  No documents with content found in the file.[/yellow]")
        return

    console.print(f"🔍 Reranking {len(documents)} documents for: [cyan]{query}[/cyan]")
    with console.status("[cyan]Running cross‑encoder reranker...[/cyan]", spinner="dots"):
        client = CerebroRerankerClient()
        ranked = client.rerank(query, documents, top_k=top_k)

    table = Table(title=f"Reranked Results (Top‑{top_k})")
    table.add_column("Rank", style="dim")
    table.add_column("Score", style="green")
    table.add_column("Document Preview", style="white")

    for i, (idx, score, doc) in enumerate(ranked, 1):
        preview = doc[:200] + "..." if len(doc) > 200 else doc
        table.add_row(str(i), f"{score:.4f}", preview)

    console.print(table)

@ops_app.command("health")
def health():
    """
    Check system health (Credentials, Permissions, APIs, Data Stores).
    """
    import os

    table = Table(title="CEREBRO System Health Check")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    final_project = None

    with console.status("[bold green]Running diagnostics..."):
        # 1. File System Check
        try:
            Path("./data").mkdir(exist_ok=True)
            table.add_row("File System", "[green]OK[/green]", "./data is writable")
        except Exception as e:
            table.add_row("File System", "[red]FAIL[/red]", str(e))

        # 2. Google Cloud Credentials & Project
        project_id = os.getenv("GCP_PROJECT_ID")
        try:
            import google.auth
            creds, detected_project = google.auth.default()

            final_project = project_id or detected_project
            if creds and final_project:
                 table.add_row("GCP Auth", "[green]OK[/green]", f"Project: {final_project}")
            else:
                 table.add_row("GCP Auth", "[red]FAIL[/red]", "No project/creds found")
        except Exception as e:
            table.add_row("GCP Auth", "[red]FAIL[/red]", str(e))

        # 3. Discovery Engine & Data Store (A LEI)
        ds_id = os.getenv("DATA_STORE_ID")
        if ds_id:
            try:
                from google.cloud import discoveryengine_v1beta as discoveryengine
                client = discoveryengine.DataStoreServiceClient()
                parent = f"projects/{final_project}/locations/global/collections/default_collection"
                # Test call to list (cheap)
                client.list_data_stores(parent=parent)
                table.add_row("Discovery Engine API", "[green]OK[/green]", f"Data Store ID: {ds_id}")
            except Exception as e:
                table.add_row("Discovery Engine API", "[red]FAIL[/red]", f"DS ID set but API failed: {str(e)[:50]}...")
        else:
            table.add_row("Discovery Engine API", "[dim]OPTIONAL[/dim]", "DATA_STORE_ID not set. Local RAG remains available.")

        # 4. BigQuery Billing Export (FinOps)
        table.add_row("Billing Audit", "[dim]N/A[/dim]", "Enable BQ Export to monitor credits")

    console.print(table)

    if not ds_id or not final_project:
        console.print("\n[bold yellow]ℹ️  Optional GCP configuration[/bold yellow]")
        console.print("Local RAG works without GCP. To enable Vertex features, configure:")
        console.print("  export GCP_PROJECT_ID='<your-gcp-project-id>'")
        console.print("  export DATA_STORE_ID='<your-data-store-id>'")


@ops_app.command("status")
def status():
    data = Path("./data/analyzed")
    if data.exists():
        for d in data.iterdir():
            if d.is_dir():
                console.print(f"Repo: [cyan]{d.name}[/cyan] [✅ Local]")


if __name__ == "__main__":
    app()
