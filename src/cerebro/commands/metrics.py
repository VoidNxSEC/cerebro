"""
Metrics CLI Commands

    cerebro metrics scan        — full zero-token scan of all repos
    cerebro metrics watch       — interactive real-time watcher
    cerebro metrics report <n>  — detailed report for one repo
"""

import time
from datetime import datetime

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

metrics_app = typer.Typer(help="Metrics & Tracking (Zero Tokens)", no_args_is_help=True)
console = Console()


def _collector():
    from cerebro.core.metrics_collector import MetricsCollector
    return MetricsCollector()


def _load():
    return _collector().load_snapshot()


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------
@metrics_app.command("scan")
def scan(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Per-repo output"),
) -> None:
    """Full zero-token metrics scan of all repositories.

    Discovers every git repo under ~/arch and collects:
      • git log / shortlog  →  commits, contributors, branches
      • filesystem traversal  →  LoC, file counts by language
      • config parsing  →  dependencies (pyproject / Cargo / package.json / go.mod)
      • regex security scan  →  secrets, unsafe patterns

    No LLM tokens are consumed.
    """
    collector = _collector()

    console.print(Panel(
        "[bold cyan]CEREBRO METRICS[/bold cyan] — Zero-Token Repository Analysis",
        border_style="cyan",
    ))

    repos = collector.discover_repos()
    console.print(f"\n📍 Discovered [bold]{len(repos)}[/bold] repositories\n")

    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning…", total=len(repos))
        for repo_path in repos:
            progress.update(task, description=f"[cyan]{repo_path.name}[/cyan]")
            try:
                snapshot = collector.collect_repo(repo_path)
                results.append(snapshot)
                if verbose:
                    console.print(f"  ✓ {snapshot.name}: {snapshot.total_loc:,} LoC  health={snapshot.health_score}%")
            except Exception as e:
                console.print(f"  ✗ [red]{repo_path.name}[/red]: {e}")
            progress.advance(task)

    collector._save_snapshot(results)

    # ---- summary table ------------------------------------------------
    table = Table(
        title=f"[bold]CEREBRO METRICS REPORT[/bold] — {len(results)} Repositories",
        box=box.HEAVY_HEAD, show_header=True, header_style="bold magenta",
    )
    for col, kw in [
        ("Repository", {"style": "cyan", "no_wrap": True}),
        ("Status", {"justify": "center"}),
        ("Health", {"justify": "center"}),
        ("LoC", {"justify": "right", "style": "dim"}),
        ("Files", {"justify": "right", "style": "dim"}),
        ("Commits", {"justify": "right", "style": "dim"}),
        ("Lang", {"style": "dim"}),
        ("Deps", {"justify": "right", "style": "dim"}),
        ("Security", {"justify": "right"}),
    ]:
        table.add_column(col, **kw)

    results.sort(key=lambda r: r.health_score, reverse=True)

    t_loc = t_files = t_commits = t_deps = 0
    status_color = {"active": "green", "maintenance": "yellow", "archived": "dim", "empty": "dim red"}
    for r in results:
        hc = "green" if r.health_score >= 70 else "yellow" if r.health_score >= 40 else "red"
        sc = status_color.get(r.status, "white")
        commits = r.git.get("total_commits", 0)
        t_loc += r.total_loc
        t_files += r.total_files
        t_commits += commits
        t_deps += r.dep_count
        sec_c = "green" if r.security_score >= 70 else "yellow" if r.security_score >= 40 else "red"
        table.add_row(
            r.name,
            f"[{sc}]{r.status}[/{sc}]",
            f"[{hc}]{r.health_score}[/{hc}]",
            f"{r.total_loc:,}", f"{r.total_files:,}", f"{commits:,}",
            r.primary_language or "—", str(r.dep_count),
            f"[{sec_c}]{r.security_score:.0f}[/{sec_c}]",
        )

    table.add_section()
    avg_h = sum(r.health_score for r in results) / len(results) if results else 0
    table.add_row(
        "[bold]TOTALS[/bold]", "",
        f"[bold]{avg_h:.1f}[/bold]",
        f"[bold]{t_loc:,}[/bold]", f"[bold]{t_files:,}[/bold]",
        f"[bold]{t_commits:,}[/bold]", "",
        f"[bold]{t_deps}[/bold]", "",
    )
    console.print(table)


# ---------------------------------------------------------------------------
# watch
# ---------------------------------------------------------------------------
@metrics_app.command("watch")
def watch(
    interval: int = typer.Option(5, "--interval", "-i", help="Poll interval (seconds)"),
) -> None:
    """Interactive real-time repository watcher.

    Monitors every tracked repo for new commits.  When a change is detected
    the affected repo is re-scanned and the updated metrics are printed live.

    Press Ctrl+C to stop.
    """
    collector = _collector()
    repos = collector.discover_repos()

    console.print(Panel(
        f"[bold cyan]LIVE WATCHER[/bold cyan] — {len(repos)} repos  •  {interval}s interval\n"
        "[dim]Press Ctrl+C to stop[/dim]",
        border_style="cyan",
    ))

    head_cache: dict = {}
    for repo in repos:
        head_cache[repo.name] = collector.get_head_hash(repo)

    changes = 0
    iteration = 0
    try:
        while True:
            iteration += 1
            for repo in repos:
                current = collector.get_head_hash(repo)
                cached = head_cache.get(repo.name, "")
                if current and cached and current != cached:
                    head_cache[repo.name] = current
                    changes += 1
                    try:
                        snapshot = collector.collect_repo(repo)
                        console.print(
                            f"[{datetime.now().strftime('%H:%M:%S')}] "
                            f"[green]⚡ CHANGE[/green] [cyan]{repo.name}[/cyan] "
                            f"→ {current[:12]}  health={snapshot.health_score}%  LoC={snapshot.total_loc:,}"
                        )
                    except Exception as e:
                        console.print(f"  [red]✗ {repo.name}: {e}[/red]")
                elif not cached:
                    head_cache[repo.name] = current

            if iteration % max(1, 30 // interval) == 0:
                console.print(
                    f"[dim][{datetime.now().strftime('%H:%M:%S')}] "
                    f"watching {len(repos)} repos … {changes} change(s) detected[/dim]"
                )
            time.sleep(interval)

    except KeyboardInterrupt:
        console.print(f"\n[yellow]Watcher stopped.  {changes} change(s) detected.[/yellow]")


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def _print_markdown_report(repo_data: dict) -> None:
    md = [
        f"# {repo_data['name']}",
        f"**Health:** {repo_data['health_score']} | **Status:** {repo_data['status']}",
        "",
        "## Architecture",
        f"- **Frameworks:** {', '.join(repo_data.get('frameworks', [])) or 'None'}",
        f"- **Entrypoints:** {', '.join(repo_data.get('entrypoints', [])) or 'None'}",
        f"- **Infrastructure:** {', '.join(repo_data.get('infrastructure', [])) or 'None'}",
        f"- **Databases:** {', '.join(repo_data.get('databases', [])) or 'None'}",
        f"- **APIs:** {', '.join(repo_data.get('apis', [])) or 'None'}",
        "",
        "## Complexity",
        f"- **Max Depth:** {repo_data.get('max_depth', 0)}",
        f"- **Avg File Size:** {repo_data.get('avg_file_size', 0)} bytes",
        "",
        "## Code & Quality",
        f"- **LoC:** {repo_data['total_loc']:,}",
        f"- **Files:** {repo_data['total_files']:,}",
        f"- **Security Score:** {repo_data['security_score']}%",
        f"- **Dependencies:** {repo_data['dep_count']}",
        f"- **Primary Language:** {repo_data.get('primary_language', 'None')}"
    ]
    print("\n".join(md))


@metrics_app.command("report")
def report(
    repo_name: str = typer.Argument(..., help="Repository name"),
    format: str = typer.Option("cli", "--format", "-f", help="Output format: cli, json, markdown"),
) -> None:
    """Detailed metrics report for a single repository.

    Run 'cerebro metrics scan' first if no snapshot exists.
    """
    snapshot = _load()
    if not snapshot:
        console.print("[red]❌ No snapshot.  Run: cerebro metrics scan[/red]")
        raise typer.Exit(1)

    repo_data = next((r for r in snapshot.get("repos", []) if r["name"] == repo_name), None)
    if not repo_data:
        names = ", ".join(r["name"] for r in snapshot["repos"])
        console.print(f"[red]❌ '{repo_name}' not found.[/red]\nAvailable: {names}")
        raise typer.Exit(1)

    if format == "json":
        import json as _json
        print(_json.dumps(repo_data, indent=2))
        return
    elif format == "markdown":
        _print_markdown_report(repo_data)
        return

    hc = "green" if repo_data["health_score"] >= 70 else "yellow" if repo_data["health_score"] >= 40 else "red"
    console.print(Panel(
        f"[bold cyan]{repo_data['name']}[/bold cyan]  |  "
        f"Health [{hc}]{repo_data['health_score']}[/{hc}]  |  Status: {repo_data['status']}",
        border_style="cyan",
    ))

    # --- architecture ---
    if any([repo_data.get("frameworks"), repo_data.get("entrypoints"), repo_data.get("infrastructure"), repo_data.get("databases"), repo_data.get("apis")]):
        at = Table(title="Architecture", box=box.SIMPLE)
        at.add_column("Category", style="cyan")
        at.add_column("Details", style="bold")
        if repo_data.get("frameworks"): at.add_row("Frameworks", ", ".join(repo_data.get("frameworks", [])))
        if repo_data.get("entrypoints"): at.add_row("Entrypoints", ", ".join(repo_data.get("entrypoints", [])))
        if repo_data.get("infrastructure"): at.add_row("Infrastructure", ", ".join(repo_data.get("infrastructure", [])))
        if repo_data.get("databases"): at.add_row("Databases", ", ".join(repo_data.get("databases", [])))
        if repo_data.get("apis"): at.add_row("APIs", ", ".join(repo_data.get("apis", [])))
        console.print(at)

    # --- complexity ---
    ct = Table(title="Complexity", box=box.SIMPLE)
    ct.add_column("Metric", style="cyan")
    ct.add_column("Value", style="bold")
    ct.add_row("Max Depth", str(repo_data.get("max_depth", 0)))
    ct.add_row("Avg File Size", f"{repo_data.get('avg_file_size', 0)} bytes")
    console.print(ct)

    # --- code ---
    t = Table(title="Code", box=box.SIMPLE)
    t.add_column("Metric", style="cyan")
    t.add_column("Value", style="bold")
    t.add_row("Total LoC", f"{repo_data['total_loc']:,}")
    t.add_row("Total Files", f"{repo_data['total_files']:,}")
    t.add_row("Primary Language", repo_data.get("primary_language") or "—")
    t.add_row("Dependencies", str(repo_data["dep_count"]))
    t.add_row("Security Score", f"{repo_data['security_score']:.0f}%")
    console.print(t)

    # --- languages ---
    langs = repo_data.get("languages", {})
    if langs:
        lt = Table(title="Languages", box=box.SIMPLE)
        lt.add_column("Language", style="cyan")
        lt.add_column("Files", justify="right")
        lt.add_column("LoC", justify="right")
        for lang, stats in sorted(langs.items(), key=lambda x: x[1]["lines"], reverse=True)[:12]:
            lt.add_row(lang, str(stats["files"]), f"{stats['lines']:,}")
        console.print(lt)

    # --- git ---
    git = repo_data.get("git", {})
    if git and "error" not in git:
        gt = Table(title="Git", box=box.SIMPLE)
        gt.add_column("Metric", style="cyan")
        gt.add_column("Value", style="bold")
        gt.add_row("Total Commits", f"{git.get('total_commits', 0):,}")
        gt.add_row("Commits (30 d)", str(git.get("commits_30d", 0)))
        gt.add_row("Commits (90 d)", str(git.get("commits_90d", 0)))
        gt.add_row("Contributors", str(git.get("contributors", 0)))
        gt.add_row("Branches", str(git.get("branches", 0)))
        gt.add_row("Tags", str(git.get("tags", 0)))
        if git.get("last_commit_author"):
            gt.add_row("Last Commit", f"{git['last_commit_author']} — {git.get('last_commit_message', '')}")
            gt.add_row("Date", git.get("last_commit_date", ""))
        console.print(gt)

    # --- security ---
    findings = repo_data.get("security_findings", [])
    if findings:
        console.print(f"\n[bold red]⚠️  Security Findings ({len(findings)})[/bold red]")
        for f in findings:
            console.print(f"  [{f['type']}] {f['file']}:{f['line']}")

    # --- quality ---
    console.print("\n[bold]Quality Indicators[/bold]")
    for label, key in [("README", "has_readme"), ("Tests", "has_tests"), ("CI/CD", "has_ci"), ("Docs", "has_docs"), ("Nix Flake", "has_flake")]:
        ok = repo_data.get(key, False)
        console.print(f"  {'[green]✓[/green]' if ok else '[red]✗[/red]'} {label}")


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------
@metrics_app.command("compare")
def compare(repo_name: str = typer.Argument(..., help="Repository name")) -> None:
    """Compare the two most recent metrics snapshots for a repository."""
    collector = _collector()
    history_dir = collector.metrics_dir / "history"
    if not history_dir.exists():
        console.print("[red]❌ No history found.[/red]")
        raise typer.Exit(1)
        
    files = sorted(history_dir.glob("metrics_snapshot_*.json"), reverse=True)
    if len(files) < 2:
        console.print("[red]❌ Need at least 2 historical snapshots to compare.[/red]")
        raise typer.Exit(1)
        
    import json
    try:
        snap_new = json.loads(files[0].read_text())
        snap_old = json.loads(files[1].read_text())
    except Exception as e:
        console.print(f"[red]❌ Error loading snapshots: {e}[/red]")
        raise typer.Exit(1)
        
    repo_new = next((r for r in snap_new.get("repos", []) if r["name"] == repo_name), None)
    repo_old = next((r for r in snap_old.get("repos", []) if r["name"] == repo_name), None)
    
    if not repo_new or not repo_old:
        console.print(f"[red]❌ '{repo_name}' not found in both snapshots.[/red]")
        raise typer.Exit(1)
        
    console.print(Panel(f"[bold cyan]Trend Analysis: {repo_name}[/bold cyan]", border_style="cyan"))
    
    t = Table(box=box.SIMPLE)
    t.add_column("Metric", style="cyan")
    t.add_column("Previous", style="dim")
    t.add_column("Current", style="bold")
    t.add_column("Delta")
    
    def _add_row(name, key, is_float=False):
        old_val = repo_old.get(key, 0)
        new_val = repo_new.get(key, 0)
        if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
            delta = new_val - old_val
            color = "green" if delta > 0 else "red" if delta < 0 else "dim"
            if key == "security_findings": color = "red" if delta > 0 else "green"
            sign = "+" if delta > 0 else ""
            delta_str = f"[{color}]{sign}{delta:.1f if is_float else delta}[/{color}]"
            t.add_row(name, str(old_val), str(new_val), delta_str)
            
    _add_row("Health Score", "health_score", True)
    _add_row("LoC", "total_loc")
    _add_row("Files", "total_files")
    _add_row("Dependencies", "dep_count")
    
    old_sec = len(repo_old.get("security_findings", []))
    new_sec = len(repo_new.get("security_findings", []))
    sec_delta = new_sec - old_sec
    sec_color = "red" if sec_delta > 0 else "green" if sec_delta < 0 else "dim"
    sec_sign = "+" if sec_delta > 0 else ""
    t.add_row("Security Issues", str(old_sec), str(new_sec), f"[{sec_color}]{sec_sign}{sec_delta}[/{sec_color}]")

    console.print(t)


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------
@metrics_app.command("check")
def check(
    min_health: float = typer.Option(0.0, "--min-health", help="Minimum health score"),
    fail_on_secrets: bool = typer.Option(False, "--fail-on-secrets", help="Fail if any security findings exist"),
    max_deps: int = typer.Option(0, "--max-deps", help="Maximum allowed dependencies"),
) -> None:
    """CI/CD Quality Gate based on the latest metrics snapshot."""
    snapshot = _load()
    if not snapshot:
        console.print("[red]❌ No snapshot. Run: cerebro metrics scan[/red]")
        raise typer.Exit(1)
        
    failed = False
    for repo in snapshot.get("repos", []):
        issues = []
        if min_health > 0 and repo["health_score"] < min_health:
            issues.append(f"health {repo['health_score']} < {min_health}")
        if fail_on_secrets and repo.get("security_findings"):
            issues.append(f"found {len(repo['security_findings'])} security secrets")
        if max_deps > 0 and repo["dep_count"] > max_deps:
            issues.append(f"deps {repo['dep_count']} > {max_deps}")
            
        if issues:
            failed = True
            console.print(f"[red]❌ {repo['name']} failed quality gate:[/red] {', '.join(issues)}")
            
    if failed:
        raise typer.Exit(1)
    console.print("[green]✅ All repositories passed the quality gates.[/green]")
