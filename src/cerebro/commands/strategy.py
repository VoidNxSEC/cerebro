"""
Cerebro CLI - Strategy Commands

Career strategy, salary intelligence, personal moat, and trend analysis tools.
Migrated from: strategy_optimizer.py, salary_intel.py, personal_moat_builder.py, trend_predictor.py
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

strategy_app = typer.Typer(help="Technology Strategy & Market Intelligence", no_args_is_help=True)
console = Console()



@strategy_app.command("optimize")
def optimize_strategy(
    goal: str = typer.Option(
        "balanced",
        "--goal",
        help="Strategy goal: immediate_value, long_term_moat, or balanced"
    ),
    budget: float = typer.Option(10.0, "--budget", help="Budget in BRL"),
    output: Optional[Path] = typer.Option(None, "--output", help="Output JSON file"),
    execute: bool = typer.Option(False, "--execute", help="Execute recommended scripts"),
):
    """
    Optimize career strategy based on ROI analysis.

    Meta-optimizer that analyzes all available scripts and suggests
    the best execution strategy for maximum ROI.

    Goals:
      - immediate_value: Quick wins, fastest ROI (30 days)
      - long_term_moat: Build unique expertise (12-24 months)
      - balanced: Mix of quick wins + long-term value (6 months)

    Example:
        cerebro strategy optimize --goal immediate_value --budget 5.0

    Migrated from: scripts/strategy_optimizer.py
    """
    try:
        # Import the original StrategyOptimizer class
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from strategy_optimizer import StrategyOptimizer

        optimizer = StrategyOptimizer()

        console.print(Panel.fit(
            f"🎯 [bold cyan]Strategy Optimizer[/bold cyan]\n\n"
            f"Goal: {goal}\n"
            f"Budget: R$ {budget:.2f}",
            border_style="cyan"
        ))

        # Get strategy
        if goal in optimizer.STRATEGIES:
            strategy = optimizer.STRATEGIES[goal]

            # Display strategy
            console.print(f"\n📊 [bold]{strategy['name']}[/bold]")
            console.print(f"Goal: {strategy['goal']}")
            console.print(f"Expected ROI: {strategy['expected_roi']}")
            console.print(f"Total Cost: R$ {strategy['total_cost']:.2f}")

            # Display scripts
            table = Table(title="Recommended Scripts", show_header=True)
            table.add_column("Script", style="cyan")
            table.add_column("ROI Multiple", justify="right", style="green")
            table.add_column("Time to Value", style="yellow")
            table.add_column("Cost (BRL)", justify="right", style="blue")

            for script_name in strategy['scripts']:
                script = optimizer.SCRIPTS[script_name]
                table.add_row(
                    script_name,
                    f"{script['roi_multiple']}x",
                    script['time_to_value'],
                    f"R$ {script['cost_brl']:.2f}"
                )

            console.print(table)

            # Execution plan
            console.print("\n📋 [bold]Execution Plan:[/bold]")
            console.print(f"  {strategy['execution']}")

            # Save to file if requested
            if output:
                result = {
                    "strategy": goal,
                    "timestamp": datetime.now().isoformat(),
                    "details": strategy,
                    "scripts": [optimizer.SCRIPTS[s] for s in strategy['scripts']],
                }
                output.parent.mkdir(parents=True, exist_ok=True)
                with open(output, 'w') as f:
                    json.dump(result, f, indent=2)
                console.print(f"\n💾 Strategy saved to: {output}")

            # Execute if requested
            if execute:
                console.print("\n🚀 Executing strategy...")
                # TODO: Implement execution logic
                console.print("[yellow]Note:[/yellow] Execution not yet implemented")

        else:
            console.print(f"[red]Error:[/red] Unknown goal '{goal}'")
            console.print(f"Available goals: {', '.join(optimizer.STRATEGIES.keys())}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)



@strategy_app.command("salary")
def salary_intelligence(
    role: str = typer.Option(..., "--role", help="Job role (e.g., Senior Engineer, Staff)"),
    company: Optional[str] = typer.Option(None, "--company", help="Target company (FAANG, Unicorns, etc.)"),
    level: Optional[str] = typer.Option(None, "--level", help="Career level (L3, E4, Senior, etc.)"),
    location: str = typer.Option("Remote_Brazil", "--location", help="Location or remote status"),
    output: Optional[Path] = typer.Option(None, "--output", help="Output file"),
    generate_queries: bool = typer.Option(True, "--queries/--no-queries", help="Generate negotiation queries"),
):
    """
    Gather salary intelligence for target role.

    Provides market data, negotiation tactics, and common mistakes
    based on real data from levels.fyi, Glassdoor, and Blind.

    Example:
        cerebro strategy salary -r "Senior Engineer" -c Google -l L4

    Migrated from: scripts/salary_intel.py
    """
    try:
        # Import the original SalaryIntelligence class
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from salary_intel import SalaryIntelligence

        intel = SalaryIntelligence()

        console.print(Panel.fit(
            f"💰 [bold cyan]Salary Intelligence[/bold cyan]\n\n"
            f"Role: {role}\n"
            f"Company: {company or 'All'}\n"
            f"Level: {level or 'All'}\n"
            f"Location: {location}",
            border_style="cyan"
        ))

        # Display salary data
        if company and company in intel.SALARY_DATA:
            data = intel.SALARY_DATA[company]

            table = Table(title=f"{company} Compensation", show_header=True)
            table.add_column("Level", style="cyan")
            table.add_column("Base", style="green")
            table.add_column("Total", style="yellow")

            if isinstance(data, dict) and 'base' not in data:  # Company with levels
                for lvl, comp in data.items():
                    if level and lvl != level:
                        continue
                    table.add_row(
                        lvl,
                        comp.get('base', 'N/A'),
                        comp.get('total', 'N/A')
                    )
            else:  # Simple company data
                table.add_row(company, data.get('base', 'N/A'), data.get('total', 'N/A'))

            console.print(table)

        # Display negotiation tactics
        console.print("\n📋 [bold]Negotiation Tactics:[/bold]")
        for i, tactic in enumerate(intel.NEGOTIATION_TACTICS, 1):
            console.print(f"  {i}. {tactic}")

        # Display common mistakes
        console.print("\n⚠️  [bold red]Common Mistakes to Avoid:[/bold red]")
        for i, mistake in enumerate(intel.COMMON_MISTAKES, 1):
            console.print(f"  {i}. {mistake}")

        # Generate queries if requested
        if generate_queries:
            console.print("\n🔍 [bold]Generating negotiation queries...[/bold]")
            queries = intel.generate_negotiation_queries()
            console.print(f"Generated {len(queries)} queries")

            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                with open(output, 'w') as f:
                    json.dump(queries, f, indent=2)
                console.print(f"💾 Queries saved to: {output}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)



@strategy_app.command("moat")
def build_moat(
    skills: str = typer.Option(..., "--skills", help="Comma-separated skills"),
    niche: str = typer.Option(..., "--niche", help="Target niche or domain"),
    depth: int = typer.Option(3, "--depth", help="Analysis depth (1-5)"),
    output: Optional[Path] = typer.Option(None, "--output", help="Output file"),
):
    """
    Build personal competitive moat analysis.

    Analyzes your skills and identifies unique combinations that create
    defensible expertise and premium positioning in the market.

    Example:
        cerebro strategy moat -s "Rust,WebAssembly,Distributed Systems" -n "Edge Computing"

    Migrated from: scripts/personal_moat_builder.py
    """
    try:
        # Import the original PersonalMoatBuilder class
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from personal_moat_builder import PersonalMoatBuilder

        skills_list = [s.strip() for s in skills.split(',')]
        builder = PersonalMoatBuilder()

        console.print(Panel.fit(
            f"🏰 [bold cyan]Personal Moat Builder[/bold cyan]\n\n"
            f"Skills: {len(skills_list)}\n"
            f"Niche: {niche}\n"
            f"Depth: {depth}",
            border_style="cyan"
        ))

        # Analyze moat
        console.print("\n🔍 Analyzing competitive positioning...")
        analysis = builder.analyze_moat(skills_list, niche, depth)

        # Display results
        console.print("\n📊 [bold]Moat Analysis:[/bold]")
        tree = Tree("Your Competitive Moat")

        for category, items in analysis.items():
            branch = tree.add(f"[cyan]{category}[/cyan]")
            for item in items:
                branch.add(item)

        console.print(tree)

        # Save to file if requested
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w') as f:
                json.dump(analysis, f, indent=2)
            console.print(f"\n💾 Analysis saved to: {output}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)



@strategy_app.command("trends")
def predict_trends(
    sector: str = typer.Option("technology", "--sector", help="Industry sector"),
    horizon: int = typer.Option(12, "--horizon", help="Prediction horizon in months"),
    categories: Optional[str] = typer.Option(None, "--categories", help="Comma-separated categories"),
    output: Optional[Path] = typer.Option(None, "--output", help="Output file"),
):
    """
    Predict career and technology trends.

    Analyzes emerging trends and identifies early mover opportunities
    for building expertise before trends go mainstream.

    ROI: Early mover advantage = 50x multiplier.

    Example:
        cerebro strategy trends -s technology -h 24 -c "AI,WebAssembly"

    Migrated from: scripts/trend_predictor.py
    """
    try:
        # Import the original TrendPredictor class
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
        from trend_predictor import TrendPredictor

        predictor = TrendPredictor()
        cats = [c.strip() for c in categories.split(',')] if categories else None

        console.print(Panel.fit(
            f"📈 [bold cyan]Trend Predictor[/bold cyan]\n\n"
            f"Sector: {sector}\n"
            f"Horizon: {horizon} months\n"
            f"Categories: {cats or 'All'}",
            border_style="cyan"
        ))

        # Predict trends
        console.print("\n🔮 Analyzing trends...")
        predictions = predictor.predict_trends(sector, horizon, cats)

        # Display predictions
        table = Table(title="Trend Predictions", show_header=True)
        table.add_column("Trend", style="cyan")
        table.add_column("Stage", style="yellow")
        table.add_column("Opportunity Score", justify="right", style="green")
        table.add_column("Time to Mainstream", style="blue")

        for trend in predictions:
            table.add_row(
                trend['name'],
                trend['stage'],
                f"{trend['score']}/100",
                trend['time_to_mainstream']
            )

        console.print(table)

        # Save to file if requested
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w') as f:
                json.dump(predictions, f, indent=2)
            console.print(f"\n💾 Predictions saved to: {output}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
