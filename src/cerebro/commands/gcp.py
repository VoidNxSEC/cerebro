"""
Cerebro CLI - optional GCP commands.

Google Cloud integration utilities for billing, search, and operational
workflows. These commands are optional and sit outside the local-first core.
Migrated from: scripts/batch_burn.py, monitor_credits.py, create_search_engine.py
"""

import time
from pathlib import Path

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

# GCP imports (conditional to avoid breaking if not available)
try:
    from google.cloud import bigquery  # noqa: F401
    from google.cloud import discoveryengine_v1beta as discoveryengine  # noqa: F401
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

gcp_app = typer.Typer(help="Optional Google Cloud integration utilities", no_args_is_help=True)
console = Console()

GCP_ENV_HINT = (
    "Re-enter the project through `nix develop --command ...` with the "
    "Google Cloud integration dependencies available."
)



@gcp_app.command("burn")
def batch_burn(
    queries: int = typer.Option(100, "--queries", help="Number of queries to execute"),
    workers: int = typer.Option(10, "--workers", help="Number of parallel workers"),
    project_id: str = typer.Option(..., "--project", help="GCP Project ID"),
    location: str = typer.Option("global", "--location", help="Engine location"),
    engine_id: str = typer.Option(..., "--engine", help="Search engine ID"),
    rate_limit: float | None = typer.Option(None, "--rate-limit", help="Queries per second limit"),
    output: Path | None = typer.Option(None, "--output", help="Output JSON file for results"),
):
    """
    Execute batch queries for load testing and credit utilization.

    This command runs parallel queries against Discovery Engine for
    load testing and GCP credit utilization. Useful for testing and
    batch execution scenarios.

    Example:
        cerebro gcp burn -q 500 -w 20 -p my-project -e my-engine

    Migrated from: scripts/batch_burn.py
    """
    if not GCP_AVAILABLE:
        console.print("[red]Error:[/red] Optional Google Cloud integrations are not available.")
        console.print(f"  {GCP_ENV_HINT}")
        raise typer.Exit(1)

    try:
        # Import the original BatchBurner class
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from batch_burn import BatchBurner, generate_questions

        console.print(Panel.fit(
            f"[bold cyan]Batch Query Execution[/bold cyan]\n\n"
            f"Project: {project_id}\n"
            f"Engine: {engine_id}\n"
            f"Queries: {queries}\n"
            f"Workers: {workers}",
            border_style="cyan"
        ))

        # Generate questions
        console.print("\n📝 Generating questions...")
        questions = generate_questions(queries)

        # Initialize burner
        burner = BatchBurner(
            project_id=project_id,
            location=location,
            engine_id=engine_id,
            workers=workers,
            rate_limit=rate_limit,
        )

        # Execute batch
        console.print(f"\n🚀 Starting batch execution with {workers} workers...\n")
        results = burner.batch_query(questions)

        # Display results
        burner.display_results()

        # Save to file if requested
        if output:
            import json
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w') as f:
                json.dump([vars(r) for r in results], f, indent=2, default=str)
            console.print(f"\n💾 Results saved to: {output}")

        console.print("\n[green]✓[/green] Batch execution completed successfully!")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)



@gcp_app.command("monitor")
def monitor_credits(
    project_id: str = typer.Option(..., "--project", help="GCP Project ID"),
    interval: int = typer.Option(60, "--interval", help="Update interval in seconds"),
    days: int = typer.Option(30, "--days", help="Look back period in days"),
    alert_threshold: float = typer.Option(10.0, "--alert", help="Alert when net cost exceeds this"),
    dataset: str | None = typer.Option(None, "--dataset", help="BigQuery billing dataset"),
    table: str | None = typer.Option(None, "--table", help="BigQuery billing table"),
):
    """
    Monitor Google Cloud credit usage in real-time.

    Displays live dashboard of credit consumption for Discovery Engine
    and Dialogflow APIs with cost tracking and alerts.

    Example:
        cerebro gcp monitor -p my-project -i 30 -d 7

    Migrated from: scripts/monitor_credits.py
    """
    if not GCP_AVAILABLE:
        console.print("[red]Error:[/red] Optional Google Cloud integrations are not available.")
        console.print(f"  {GCP_ENV_HINT}")
        raise typer.Exit(1)

    try:
        # Import the original CreditMonitor class
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from monitor_credits import CreditMonitor

        monitor = CreditMonitor(
            project_id=project_id,
            dataset=dataset,
            table=table,
        )

        console.print(Panel.fit(
            f"💰 [bold cyan]GCP Credit Monitor[/bold cyan]\n\n"
            f"Project: {project_id}\n"
            f"Interval: {interval}s\n"
            f"Period: {days} days\n"
            f"Alert threshold: ${alert_threshold}",
            border_style="cyan"
        ))

        console.print("\n🔍 Starting real-time monitoring... (Press Ctrl+C to stop)\n")

        try:
            with Live(console=console, refresh_per_second=1) as live:
                while True:
                    # Get current status
                    status = monitor.get_credit_status(days=days)

                    # Build display table
                    table = Table(title=f"Credit Status - Last {days} Days", show_header=True)
                    table.add_column("Credit", style="cyan")
                    table.add_column("Queries", justify="right", style="blue")
                    table.add_column("Gross Cost", justify="right", style="yellow")
                    table.add_column("Credits Applied", justify="right", style="green")
                    table.add_column("Net Cost", justify="right", style="red" if status.get("genai") and status["genai"].net_cost > alert_threshold else "white")

                    for name, data in status.items():
                        table.add_row(
                            name.upper(),
                            f"{data.total_queries:,}",
                            f"${data.gross_cost:.2f}",
                            f"${data.credits_applied:.2f}",
                            f"${data.net_cost:.2f}",
                        )

                    # Alert if threshold exceeded
                    alert_msg = ""
                    for name, data in status.items():
                        if data.net_cost > alert_threshold:
                            alert_msg += f"\n⚠️  {name.upper()} net cost (${data.net_cost:.2f}) exceeds threshold (${alert_threshold:.2f})"

                    if alert_msg:
                        table.caption = alert_msg

                    live.update(table)
                    time.sleep(interval)

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Monitoring stopped by user[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)



@gcp_app.command("create-engine")
def create_search_engine(
    name: str = typer.Option(..., "--name", help="Search engine name"),
    project_id: str = typer.Option(..., "--project", help="GCP Project ID"),
    location: str = typer.Option("global", "--location", help="Engine location"),
    data_store: str = typer.Option(..., "--data-store", help="Data store ID"),
    industry: str = typer.Option("GENERIC", "--industry", help="Industry vertical (GENERIC, MEDIA, etc.)"),
    config: Path | None = typer.Option(None, "--config", help="YAML configuration file"),
):
    """
    Create a Discovery Engine search engine for the optional GCP integration.

    Sets up a new search engine instance with specified configuration.
    Supports industry-specific optimization and custom configs.

    Example:
        cerebro gcp create-engine -n my-engine -p my-project -d my-datastore

    Migrated from: scripts/create_search_engine.py
    """
    if not GCP_AVAILABLE:
        console.print("[red]Error:[/red] Optional Google Cloud integrations are not available.")
        console.print(f"  {GCP_ENV_HINT}")
        raise typer.Exit(1)

    try:
        # Import the original function
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from create_search_engine import create_engine

        console.print(Panel.fit(
            f"🔧 [bold cyan]Create Search Engine[/bold cyan]\n\n"
            f"Name: {name}\n"
            f"Project: {project_id}\n"
            f"Location: {location}\n"
            f"Data Store: {data_store}\n"
            f"Industry: {industry}",
            border_style="cyan"
        ))

        # Load config if provided
        config_data = {}
        if config and config.exists():
            import yaml
            with open(config) as f:
                config_data = yaml.safe_load(f)
            console.print(f"\n📄 Loaded configuration from: {config}")

        # Create engine
        console.print("\n🚀 Creating search engine...")

        result = create_engine(
            project_id=project_id,
            location=location,
            engine_id=name,
            data_store_id=data_store,
            industry_vertical=industry,
            **config_data
        )

        console.print("\n[green]✓[/green] Search engine created successfully!")
        console.print(f"\nEngine ID: {result.name}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)



@gcp_app.command("status")
def gcp_status():
    """
    Check the status of the optional Google Cloud integration.
    """
    console.print(Panel.fit("🔍 [bold cyan]Optional GCP Integration Status[/bold cyan]", border_style="cyan"))

    # Check if GCP libraries available
    if GCP_AVAILABLE:
        console.print("[green]✓[/green] GCP libraries installed")
    else:
        console.print("[red]✗[/red] GCP libraries not installed")
        console.print(f"  {GCP_ENV_HINT}")

    # Check authentication
    try:
        from google.auth import default
        credentials, project = default()
        console.print("[green]✓[/green] Authenticated")
        if project:
            console.print(f"  Default project: {project}")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Not authenticated: {e}")
        console.print("  Run inside the project shell: gcloud auth application-default login")
