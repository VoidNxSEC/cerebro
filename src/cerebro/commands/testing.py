"""
Cerebro CLI - Testing Commands

Test utilities for grounded search and generation APIs.
Migrated from: grounded_search.py, grounded_generation_test.py, verify_grounded_api.py
"""

from pathlib import Path
from typing import Optional
import json

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

# GCP imports (conditional)
try:
    from google.cloud import discoveryengine_v1beta as discoveryengine  # noqa: F401
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

testing_app = typer.Typer(help="API Testing & Validation", name="test", no_args_is_help=True)
console = Console()



@testing_app.command("grounded-search")
def test_grounded_search(
    query: str = typer.Option(..., "--query", help="Search query"),
    project_id: str = typer.Option(..., "--project", help="GCP Project ID"),
    engine_id: str = typer.Option(..., "--engine", help="Search engine ID"),
    location: str = typer.Option("global", "--location", help="Engine location"),
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed results"),
):
    """
    Test grounded search API functionality.

    Executes a search query against Discovery Engine and displays
    results with citations and metadata.

    Example:
        cerebro test grounded-search -q "NixOS configuration" -p my-project -e my-engine

    Migrated from: scripts/grounded_search.py
    """
    if not GCP_AVAILABLE:
        console.print("[red]Error:[/red] GCP libraries not installed")
        raise typer.Exit(1)

    try:
        # Import the original test function
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from grounded_search import test_search

        console.print(Panel.fit(
            f"🔍 [bold cyan]Grounded Search Test[/bold cyan]\n\n"
            f"Query: {query}\n"
            f"Project: {project_id}\n"
            f"Engine: {engine_id}",
            border_style="cyan"
        ))

        # Execute search
        console.print("\n🚀 Executing search...\n")
        results = test_search(project_id, location, engine_id, query)

        # Display results
        if results:
            table = Table(title="Search Results", show_header=True)
            table.add_column("Rank", justify="right", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Relevance", justify="right", style="yellow")

            for i, result in enumerate(results[:10], 1):
                table.add_row(
                    str(i),
                    result.get('title', 'N/A')[:60],
                    f"{result.get('relevance_score', 0):.2f}"
                )

            console.print(table)

            if verbose:
                console.print("\n📄 [bold]Detailed Results:[/bold]\n")
                for i, result in enumerate(results[:3], 1):
                    console.print(f"[cyan]Result {i}:[/cyan]")
                    console.print(json.dumps(result, indent=2))
                    console.print()

        else:
            console.print("[yellow]No results found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)



@testing_app.command("grounded-gen")
def test_grounded_generation(
    prompt: str = typer.Option(..., "--prompt", help="Generation prompt"),
    context: Optional[Path] = typer.Option(None, "--context", help="Context documents file"),
    project_id: str = typer.Option(..., "--project", help="GCP Project ID"),
    engine_id: str = typer.Option(..., "--engine", help="Search engine ID"),
    model: str = typer.Option("preview", "--model", help="Model version"),
    output: Optional[Path] = typer.Option(None, "--output", help="Save output to file"),
):
    """
    Test grounded generation API.

    Generates text grounded in provided context using Discovery Engine's
    RAG capabilities with citations.

    Example:
        cerebro test grounded-gen -p "Explain NixOS modules" --project my-project -e my-engine

    Migrated from: scripts/grounded_generation_test.py
    """
    if not GCP_AVAILABLE:
        console.print("[red]Error:[/red] GCP libraries not installed")
        raise typer.Exit(1)

    try:
        # Import the original test function
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from grounded_generation_test import test_generation

        # Load context if provided
        context_docs = None
        if context and context.exists():
            with open(context) as f:
                context_docs = json.load(f)
            console.print(f"📄 Loaded context from: {context}")

        console.print(Panel.fit(
            f"✨ [bold cyan]Grounded Generation Test[/bold cyan]\n\n"
            f"Prompt: {prompt[:60]}...\n"
            f"Project: {project_id}\n"
            f"Model: {model}",
            border_style="cyan"
        ))

        # Execute generation
        console.print("\n🚀 Generating response...\n")
        result = test_generation(project_id, engine_id, prompt, context_docs, model)

        # Display result
        console.print(Panel.fit(
            result['text'],
            title="Generated Response",
            border_style="green"
        ))

        # Display citations
        if result.get('citations'):
            console.print("\n📚 [bold]Citations:[/bold]")
            for i, citation in enumerate(result['citations'], 1):
                console.print(f"  [{i}] {citation}")

        # Save if requested
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            console.print(f"\n💾 Output saved to: {output}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)



@testing_app.command("verify-api")
def verify_api(
    endpoint: str = typer.Option(..., "--endpoint", help="API endpoint to verify"),
    method: str = typer.Option("GET", "--method", help="HTTP method"),
    payload: Optional[Path] = typer.Option(None, "--payload", help="JSON payload file"),
    headers: Optional[str] = typer.Option(None, "--headers", help="Custom headers (JSON string)"),
    expect_status: int = typer.Option(200, "--expect-status", help="Expected HTTP status code"),
):
    """
    Verify grounded API endpoints.

    Tests API endpoints for availability, correct responses,
    and expected behavior. Useful for integration testing.

    Example:
        cerebro test verify-api -e "https://api.example.com/search" -m POST

    Migrated from: scripts/verify_grounded_api.py
    """
    try:

        # Import the original verify function
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from verify_grounded_api import verify_endpoint

        # Load payload if provided
        payload_data = None
        if payload and payload.exists():
            with open(payload) as f:
                payload_data = json.load(f)

        # Parse headers
        headers_dict = json.loads(headers) if headers else {}

        console.print(Panel.fit(
            f"🔍 [bold cyan]API Verification[/bold cyan]\n\n"
            f"Endpoint: {endpoint}\n"
            f"Method: {method}\n"
            f"Expected Status: {expect_status}",
            border_style="cyan"
        ))

        # Verify endpoint
        console.print("\n🚀 Testing endpoint...\n")
        result = verify_endpoint(
            endpoint,
            method=method,
            payload=payload_data,
            headers=headers_dict,
            expect_status=expect_status
        )

        # Display results
        if result['success']:
            console.print("[green]✓[/green] API verification successful!")
            console.print(f"\nStatus Code: [green]{result['status_code']}[/green]")
            console.print(f"Response Time: {result['response_time']:.2f}s")

            if result.get('response'):
                console.print("\n📄 [bold]Response:[/bold]")
                syntax = Syntax(
                    json.dumps(result['response'], indent=2),
                    "json",
                    theme="monokai",
                    line_numbers=True
                )
                console.print(syntax)
        else:
            console.print("[red]✗[/red] API verification failed")
            console.print(f"\nStatus Code: [red]{result['status_code']}[/red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)



@testing_app.command("batch-verify", hidden=True)
def batch_verify(
    config: Path = typer.Argument(..., help="YAML config file with endpoints to test"),
    output: Optional[Path] = typer.Option(None, "--output", help="Save results to file"),
    parallel: int = typer.Option(1, "--parallel", help="Number of parallel tests"),
):
    """
    Verify multiple API endpoints from config file.

    Example config.yaml:
        endpoints:
          - url: https://api.example.com/search
            method: POST
            expect_status: 200
          - url: https://api.example.com/health
            method: GET
            expect_status: 200

    Example:
        cerebro test batch-verify endpoints.yaml -p 5
    """
    try:
        import yaml

        if not config.exists():
            console.print(f"[red]Error:[/red] Config file not found: {config}")
            raise typer.Exit(1)

        # Load config
        with open(config) as f:
            config_data = yaml.safe_load(f)

        endpoints = config_data.get('endpoints', [])

        console.print(Panel.fit(
            f"🔍 [bold cyan]Batch API Verification[/bold cyan]\n\n"
            f"Endpoints: {len(endpoints)}\n"
            f"Parallel: {parallel}",
            border_style="cyan"
        ))

        # TODO: Implement batch verification with parallel execution
        console.print("\n[yellow]Note:[/yellow] Batch verification not yet fully implemented")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
