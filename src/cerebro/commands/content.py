"""
Cerebro CLI - Content Commands

Content mining and analysis tools for discovering valuable insights.
Migrated from: scripts/content_gold_miner.py
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

content_app = typer.Typer(help="Content Mining & Analysis", no_args_is_help=True)
console = Console()


@content_app.command("mine")
def mine_content(
    sources: str = typer.Option(..., "--sources", help="Content sources (URLs or file paths, comma-separated)"),
    output: Path = typer.Option("content_analysis.json", "--output", help="Output JSON file"),
    depth: int = typer.Option(2, "--depth", help="Mining depth (1-5)"),
    categories: Optional[str] = typer.Option(None, "--categories", help="Filter by categories"),
    format: str = typer.Option("json", "--format", help="Output format: json, markdown, or html"),
):
    """
    Mine valuable content from various sources.

    Analyzes content to extract key insights, trends, and actionable intelligence.
    Supports URLs, local files, and multiple content types.

    Examples:
        cerebro content mine -s "blog.com,medium.com/@user" -d 3
        cerebro content mine -s "docs/*.md" --categories "tech,career"

    Migrated from: scripts/content_gold_miner.py
    """
    try:
        # Import the original ContentGoldMiner class
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from content_gold_miner import ContentGoldMiner

        source_list = [s.strip() for s in sources.split(',')]
        cats = [c.strip() for c in categories.split(',')] if categories else None

        console.print(Panel.fit(
            f"⛏️  [bold cyan]Content Gold Miner[/bold cyan]\n\n"
            f"Sources: {len(source_list)}\n"
            f"Depth: {depth}\n"
            f"Categories: {cats or 'All'}\n"
            f"Format: {format}",
            border_style="cyan"
        ))

        # Initialize miner
        miner = ContentGoldMiner(depth=depth, categories=cats)

        # Mine content with progress
        console.print("\n⛏️  Mining content...\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing sources...", total=len(source_list))

            results = []
            for source in source_list:
                progress.update(task, description=f"Mining: {source}")
                result = miner.mine(source)
                results.append(result)
                progress.advance(task)

        # Analyze results
        console.print("\n📊 [bold]Mining Results:[/bold]")

        table = Table(show_header=True)
        table.add_column("Source", style="cyan")
        table.add_column("Insights", justify="right", style="green")
        table.add_column("Quality Score", justify="right", style="yellow")
        table.add_column("Actionable Items", justify="right", style="blue")

        total_insights = 0
        for result in results:
            insights = len(result.get('insights', []))
            total_insights += insights
            table.add_row(
                result['source'],
                str(insights),
                f"{result.get('quality_score', 0):.1f}/10",
                str(len(result.get('actionable', [])))
            )

        console.print(table)
        console.print(f"\nTotal insights extracted: [bold green]{total_insights}[/bold green]")

        # Save results
        output.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            import json
            with open(output, 'w') as f:
                json.dump(results, f, indent=2)
        elif format == "markdown":
            md_output = output.with_suffix('.md')
            with open(md_output, 'w') as f:
                f.write(miner.to_markdown(results))
            output = md_output
        elif format == "html":
            html_output = output.with_suffix('.html')
            with open(html_output, 'w') as f:
                f.write(miner.to_html(results))
            output = html_output

        console.print(f"\n💾 Results saved to: {output}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@content_app.command("analyze")
def analyze_content(
    file: Path = typer.Argument(..., help="Content file to analyze"),
    type: str = typer.Option("auto", "--type", help="Content type: auto, blog, article, code, docs"),
    metrics: bool = typer.Option(True, "--metrics/--no-metrics", help="Include detailed metrics"),
):
    """
    Analyze a single content file in detail.

    Provides deep analysis of content quality, readability, SEO,
    and actionable recommendations.

    Example:
        cerebro content analyze article.md --type blog --metrics
    """
    try:
        if not file.exists():
            console.print(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(1)

        # Import analyzer
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from content_gold_miner import ContentAnalyzer

        analyzer = ContentAnalyzer()

        console.print(Panel.fit(
            f"📄 [bold cyan]Content Analysis[/bold cyan]\n\n"
            f"File: {file.name}\n"
            f"Type: {type}\n"
            f"Size: {file.stat().st_size:,} bytes",
            border_style="cyan"
        ))

        # Analyze
        with open(file) as f:
            content = f.read()

        analysis = analyzer.analyze(content, type)

        # Display results
        console.print("\n📊 [bold]Analysis Results:[/bold]\n")

        console.print(f"Quality Score: [green]{analysis['quality_score']:.1f}/10[/green]")
        console.print(f"Readability: {analysis['readability']}")
        console.print(f"Word Count: {analysis['word_count']:,}")
        console.print(f"Reading Time: {analysis['reading_time']} min")

        if metrics:
            console.print("\n📈 [bold]Detailed Metrics:[/bold]")
            for metric, value in analysis.get('metrics', {}).items():
                console.print(f"  • {metric}: {value}")

        # Recommendations
        if analysis.get('recommendations'):
            console.print("\n💡 [bold]Recommendations:[/bold]")
            for i, rec in enumerate(analysis['recommendations'], 1):
                console.print(f"  {i}. {rec}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
