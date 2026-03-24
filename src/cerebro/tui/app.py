"""
Cerebro TUI - Interactive Terminal User Interface

Main Textual application with screen navigation and command integration.
"""

import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Button, Static, DataTable, Input, Label, ProgressBar
from textual.screen import Screen


class Sidebar(Vertical):
    """Navigation sidebar with screen selection buttons."""

    def compose(self) -> ComposeResult:
        yield Static("🧠 CEREBRO", classes="sidebar-title")
        yield Button("📊 Dashboard", id="nav-dashboard", variant="primary")
        yield Button("📁 Projects", id="nav-projects")
        yield Button("🔍 Intelligence", id="nav-intelligence")
        yield Button("⚙️  Scripts", id="nav-scripts")
        yield Button("💰 GCP Credits", id="nav-gcp")
        yield Button("📋 Logs", id="nav-logs")
        yield Static("", classes="sidebar-spacer")
        yield Button("❌ Quit", id="nav-quit", variant="error")


class DashboardScreen(Screen):
    """Main dashboard with system metrics and quick actions."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "quick_scan", "Scan"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = None
        self.auto_refresh = True

    def compose(self) -> ComposeResult:
        from textual.containers import Horizontal, VerticalScroll

        yield Header()
        yield VerticalScroll(
            Static("📊 [bold cyan]Dashboard[/bold cyan]", classes="screen-title"),

            # System Metrics Panel
            Container(
                Static("[bold]System Metrics[/bold]", classes="panel-header"),
                Static("Loading...", id="metrics-display", classes="metrics-content"),
                classes="metrics-panel"
            ),

            # Alerts Panel
            Container(
                Static("[bold]Alerts & Warnings[/bold]", classes="panel-header"),
                Static("No alerts", id="alerts-display", classes="alerts-content"),
                classes="alerts-panel"
            ),

            # Quick Actions
            Container(
                Static("[bold]Quick Actions[/bold]", classes="panel-header"),
                Horizontal(
                    Button("🔍 Scan Projects", id="action-scan", variant="primary"),
                    Button("🧠 Query Intelligence", id="action-query"),
                    Button("🔄 Refresh", id="action-refresh"),
                    classes="action-buttons"
                ),
                classes="actions-panel"
            ),

            # Recent Activity
            Container(
                Static("[bold]Recent Activity[/bold]", classes="panel-header"),
                Static("No recent activity", id="activity-display", classes="activity-content"),
                classes="activity-panel"
            ),

            id="main-content"
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Load initial data when screen mounts."""
        from cerebro.tui.commands.router import CommandRouter

        self.router = CommandRouter()
        await self.load_metrics()

        # Set up auto-refresh every 10 seconds
        if self.auto_refresh:
            self.set_interval(10.0, self.load_metrics)

    async def load_metrics(self) -> None:
        """Load and display system metrics."""
        if not self.router:
            return

        try:
            status = await self.router.get_system_status()

            metrics_text = f"""
[cyan]Total Projects:[/cyan] {status.get('total_projects', 0)}
[green]Active Projects:[/green] {status.get('active_projects', 0)}
[yellow]Health Score:[/yellow] {status.get('health_score', 0):.1f}/100
[magenta]Intelligence Items:[/magenta] {status.get('total_intelligence', 0)}
            """

            metrics_widget = self.query_one("#metrics-display", Static)
            metrics_widget.update(metrics_text.strip())

            # Update alerts if health score is low
            alerts_widget = self.query_one("#alerts-display", Static)
            health_score = status.get('health_score', 100)
            if health_score < 50:
                alerts_widget.update(f"[red]⚠️  System health is low: {health_score:.1f}/100[/red]")
            elif health_score < 75:
                alerts_widget.update(f"[yellow]⚠️  System health needs attention: {health_score:.1f}/100[/yellow]")
            else:
                alerts_widget.update("[green]✓ All systems healthy[/green]")

        except Exception as e:
            metrics_widget = self.query_one("#metrics-display", Static)
            metrics_widget.update(f"[red]Error loading metrics: {str(e)}[/red]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle quick action button clicks."""
        if event.button.id == "action-scan":
            self.action_quick_scan()
        elif event.button.id == "action-query":
            self.app.switch_screen("intelligence")
        elif event.button.id == "action-refresh":
            self.action_refresh()

    async def action_quick_scan(self) -> None:
        """Execute quick project scan."""
        activity_widget = self.query_one("#activity-display", Static)
        activity_widget.update("[yellow]🔄 Scanning projects...[/yellow]")

        try:
            if self.router:
                async for update in self.router.run_scan(full_scan=False):
                    status = update.get("status")
                    message = update.get("message", "")

                    if status == "complete":
                        result = update.get("result", {})
                        activity_widget.update(
                            f"[green]✓ Scan complete: {result.get('projects_found', 0)} projects found[/green]"
                        )
                        await self.load_metrics()  # Refresh metrics
                    elif status == "error":
                        activity_widget.update(f"[red]✗ Error: {message}[/red]")
                    else:
                        activity_widget.update(f"[yellow]🔄 {message}[/yellow]")
        except Exception as e:
            activity_widget.update(f"[red]✗ Scan failed: {str(e)}[/red]")

    async def action_refresh(self) -> None:
        """Refresh dashboard data."""
        await self.load_metrics()


class ProjectsScreen(Screen):
    """Projects management and health scores."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("/", "focus_search", "Search"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = None
        self.all_projects = []
        self.page_size = 100  # Show 100 projects at a time
        self.current_page = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Static("📁 [bold cyan]Projects[/bold cyan]", classes="screen-title"),

            # Search/Filter Bar
            Container(
                Label("Search:", classes="search-label"),
                Input(placeholder="Filter projects...", id="search-input"),
                classes="search-container"
            ),

            # Projects DataTable
            DataTable(id="projects-table", classes="projects-table"),

            # Project Details Panel
            Container(
                Static("[bold]Project Details[/bold]", classes="panel-header"),
                Static("Select a project to view details", id="project-details", classes="details-content"),
                classes="details-panel"
            ),

            # Action Buttons
            Container(
                Horizontal(
                    Button("📊 Analyze", id="btn-analyze", variant="primary"),
                    Button("📝 Summarize", id="btn-summarize"),
                    Button("📂 Open Path", id="btn-open"),
                    Button("🔄 Refresh", id="btn-refresh"),
                    classes="action-buttons"
                ),
                classes="actions-panel"
            ),

            id="main-content"
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the projects table."""
        from cerebro.tui.commands.router import CommandRouter

        self.router = CommandRouter()

        # Set up table columns
        table = self.query_one("#projects-table", DataTable)
        table.add_columns("Name", "Status", "Health", "Languages", "Path")
        table.cursor_type = "row"

        await self.load_projects()

    async def load_projects(self) -> None:
        """Load projects from the backend."""
        if not self.router:
            return

        try:
            self.all_projects = await self.router.get_projects()
            await self.update_table()
        except Exception as e:
            table = self.query_one("#projects-table", DataTable)
            table.clear()
            details = self.query_one("#project-details", Static)
            details.update(f"[red]Error loading projects: {str(e)}[/red]")

    async def update_table(self, filter_text: str = "") -> None:
        """Update table with filtered and paginated projects."""
        table = self.query_one("#projects-table", DataTable)
        table.clear()

        # Filter projects
        projects = self.all_projects
        if filter_text:
            filter_lower = filter_text.lower()
            projects = [
                p for p in projects
                if filter_lower in p.get("name", "").lower()
                or filter_lower in p.get("path", "").lower()
            ]

        # Paginate for performance (show first page_size projects)
        # Full pagination with prev/next buttons can be added later
        displayed_projects = projects[:self.page_size]

        # Add rows
        for project in displayed_projects:
            name = project.get("name", "Unknown")
            status = project.get("status", "unknown")
            health = project.get("health_score", 0)
            languages = ", ".join(project.get("languages", []))[:30]
            path = project.get("path", "")[:50]

            # Color-code health score
            if health >= 75:
                health_str = f"[green]{health:.1f}[/green]"
            elif health >= 50:
                health_str = f"[yellow]{health:.1f}[/yellow]"
            else:
                health_str = f"[red]{health:.1f}[/red]"

            # Color-code status
            status_colors = {
                "active": "green",
                "inactive": "yellow",
                "error": "red",
                "unknown": "dim"
            }
            status_color = status_colors.get(status, "white")
            status_str = f"[{status_color}]{status}[/{status_color}]"

            table.add_row(name, status_str, health_str, languages, path)

        # Update count
        total_filtered = len(projects)
        showing = len(displayed_projects)
        count_text = f"[dim]Showing {showing} of {total_filtered} projects"
        if total_filtered != len(self.all_projects):
            count_text += f" ({len(self.all_projects)} total)"
        count_text += "[/dim]"

        if filter_text:
            count_text += f" [dim](filtered by '{filter_text}')[/dim]"
        if total_filtered > self.page_size:
            count_text += f" [yellow](Limited to first {self.page_size} for performance)[/yellow]"

        details = self.query_one("#project-details", Static)
        details.update(count_text)

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            await self.update_table(event.value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection to show project details."""
        row_index = event.cursor_row

        if 0 <= row_index < len(self.all_projects):
            project = self.all_projects[row_index]

            details_text = f"""
[cyan]Name:[/cyan] {project.get('name', 'N/A')}
[cyan]Path:[/cyan] {project.get('path', 'N/A')}
[cyan]Status:[/cyan] {project.get('status', 'N/A')}
[cyan]Health Score:[/cyan] {project.get('health_score', 0):.1f}/100
[cyan]Languages:[/cyan] {', '.join(project.get('languages', []))}
            """

            details = self.query_one("#project-details", Static)
            details.update(details_text.strip())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle action button clicks."""
        if event.button.id == "btn-refresh":
            self.action_refresh()
        elif event.button.id == "btn-analyze":
            self.notify("Analyze feature coming soon", severity="information")
        elif event.button.id == "btn-summarize":
            self.notify("Summarize feature coming soon", severity="information")
        elif event.button.id == "btn-open":
            self.notify("Open path feature coming soon", severity="information")

    async def action_refresh(self) -> None:
        """Refresh projects list."""
        await self.load_projects()
        self.notify("Projects refreshed", severity="information")

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()


class IntelligenceScreen(Screen):
    """AI-powered query interface with grounded generation."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("ctrl+q", "focus_query", "Focus Query"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = None
        self.query_history = []
        self.state_manager = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Static("🔍 [bold cyan]Intelligence Query[/bold cyan]", classes="screen-title"),

            # Query Input Section
            Container(
                Label("Query:", classes="query-label"),
                Input(
                    placeholder="Enter your question about the codebase...",
                    id="query-input",
                    classes="query-input"
                ),
                Horizontal(
                    Button("🔍 Search", id="btn-search", variant="primary"),
                    Button("🧹 Clear", id="btn-clear"),
                    Button("📝 Export", id="btn-export"),
                    classes="query-buttons"
                ),
                classes="query-container"
            ),

            # Query Options
            Container(
                Horizontal(
                    Label("Mode: ", classes="option-label"),
                    Button("Semantic", id="mode-semantic", variant="primary", classes="mode-btn"),
                    Button("Exact", id="mode-exact", classes="mode-btn"),
                    Label("  Limit: ", classes="option-label"),
                    Input(value="10", id="limit-input", classes="limit-input"),
                    classes="options-row"
                ),
                classes="options-container"
            ),

            # Status/Progress
            Container(
                Static("Ready", id="query-status", classes="status-text"),
                classes="status-container"
            ),

            # Results Panel
            Container(
                Static("[bold]Results[/bold]", classes="panel-header"),
                VerticalScroll(
                    Static("No results yet. Enter a query above to search.", id="results-display"),
                    id="results-scroll",
                    classes="results-scroll"
                ),
                classes="results-panel"
            ),

            id="main-content"
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the intelligence screen."""
        from cerebro.tui.commands.router import CommandRouter
        from cerebro.tui.state import TUIState

        self.router = CommandRouter()
        self.state_manager = TUIState()

        # Load saved mode and limit
        self.semantic_mode = self.state_manager.get("intelligence.last_mode", "semantic") == "semantic"
        last_limit = self.state_manager.get("intelligence.last_limit", 10)

        # Set limit input
        limit_input = self.query_one("#limit-input", Input)
        limit_input.value = str(last_limit)

        # Update mode buttons
        self.update_mode_buttons()

        # Load query history
        self.query_history = self.state_manager.get("intelligence.query_history", [])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "btn-search":
            self.action_execute_query()
        elif event.button.id == "btn-clear":
            self.action_clear_results()
        elif event.button.id == "btn-export":
            self.action_export_results()
        elif event.button.id == "mode-semantic":
            self.semantic_mode = True
            self.update_mode_buttons()
        elif event.button.id == "mode-exact":
            self.semantic_mode = False
            self.update_mode_buttons()

    def update_mode_buttons(self) -> None:
        """Update mode button styles."""
        semantic_btn = self.query_one("#mode-semantic", Button)
        exact_btn = self.query_one("#mode-exact", Button)

        if self.semantic_mode:
            semantic_btn.variant = "primary"
            exact_btn.variant = "default"
        else:
            semantic_btn.variant = "default"
            exact_btn.variant = "primary"

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in query input."""
        if event.input.id == "query-input":
            await self.action_execute_query()

    async def action_execute_query(self) -> None:
        """Execute the intelligence query."""
        if not self.router:
            self.notify("Router not initialized", severity="error")
            return

        query_input = self.query_one("#query-input", Input)
        query_text = query_input.value.strip()

        if not query_text:
            self.notify("Please enter a query", severity="warning")
            return

        # Get limit
        try:
            limit_input = self.query_one("#limit-input", Input)
            limit = int(limit_input.value) if limit_input.value else 10
        except ValueError:
            limit = 10

        # Update status
        status_widget = self.query_one("#query-status", Static)
        status_widget.update(f"[yellow]🔄 Searching for: {query_text}...[/yellow]")

        # Clear previous results
        results_widget = self.query_one("#results-display", Static)
        results_widget.update("[dim]Searching...[/dim]")

        try:
            async for update in self.router.run_intelligence_query(
                query=query_text,
                limit=limit,
                semantic=self.semantic_mode
            ):
                status = update.get("status")
                message = update.get("message", "")

                if status == "complete":
                    results = update.get("results", [])

                    if not results:
                        results_widget.update("[dim]No results found.[/dim]")
                        status_widget.update("[yellow]⚠️  No results found[/yellow]")
                    else:
                        # Format results
                        formatted = self.format_results(results)
                        results_widget.update(formatted)
                        status_widget.update(f"[green]✓ Found {len(results)} results[/green]")

                    # Add to history
                    query_record = {
                        "query": query_text,
                        "mode": "semantic" if self.semantic_mode else "exact",
                        "results_count": len(results),
                        "timestamp": __import__('datetime').datetime.now().isoformat()
                    }
                    self.query_history.append(query_record)

                    # Save to persistent state
                    if self.state_manager:
                        self.state_manager.add_to_history("intelligence.query_history", query_record)
                        self.state_manager.set("intelligence.last_mode", "semantic" if self.semantic_mode else "exact")
                        self.state_manager.set("intelligence.last_limit", limit)

                elif status == "error":
                    results_widget.update(f"[red]✗ Error: {message}[/red]")
                    status_widget.update("[red]✗ Query failed[/red]")
                else:
                    status_widget.update(f"[yellow]🔄 {message}[/yellow]")

        except Exception as e:
            results_widget.update(f"[red]✗ Error executing query: {str(e)}[/red]")
            status_widget.update("[red]✗ Error[/red]")

    def format_results(self, results: list) -> str:
        """Format query results for display."""
        if not results:
            return "[dim]No results.[/dim]"

        output_lines = []

        for i, result in enumerate(results, 1):
            output_lines.append(f"[bold cyan]Result {i}:[/bold cyan]")

            # Handle different result formats
            if isinstance(result, dict):
                for key, value in result.items():
                    if key not in ["embedding", "vector"]:  # Skip large fields
                        output_lines.append(f"  [yellow]{key}:[/yellow] {value}")
            else:
                output_lines.append(f"  {result}")

            output_lines.append("")  # Blank line between results

        return "\n".join(output_lines)

    def action_clear_results(self) -> None:
        """Clear query results."""
        query_input = self.query_one("#query-input", Input)
        query_input.value = ""

        results_widget = self.query_one("#results-display", Static)
        results_widget.update("[dim]No results yet. Enter a query above to search.[/dim]")

        status_widget = self.query_one("#query-status", Static)
        status_widget.update("Ready")

    def action_export_results(self) -> None:
        """Export results to markdown."""
        self.notify("Export feature coming soon", severity="information")

    def action_focus_query(self) -> None:
        """Focus the query input."""
        query_input = self.query_one("#query-input", Input)
        query_input.focus()


class ScriptsScreen(Screen):
    """Script launcher with progress monitoring."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = None
        self.commands = {}
        self.selected_group = None
        self.selected_command = None

    def compose(self) -> ComposeResult:
        from textual.widgets import ProgressBar

        yield Header()
        yield VerticalScroll(
            Static("⚙️  [bold cyan]Scripts & Commands[/bold cyan]", classes="screen-title"),

            # Command Selection Section
            Horizontal(
                # Command Groups List
                Container(
                    Static("[bold]Command Groups[/bold]", classes="panel-header"),
                    VerticalScroll(
                        Button("knowledge", id="group-knowledge", classes="group-btn"),
                        Button("rag", id="group-rag", classes="group-btn"),
                        Button("ops", id="group-ops", classes="group-btn"),
                        Button("gcp", id="group-gcp", classes="group-btn"),
                        Button("strategy", id="group-strategy", classes="group-btn"),
                        Button("content", id="group-content", classes="group-btn"),
                        Button("test", id="group-test", classes="group-btn"),
                        id="groups-scroll",
                        classes="groups-scroll"
                    ),
                    classes="groups-panel"
                ),

                # Commands List for Selected Group
                Container(
                    Static("[bold]Commands[/bold]", id="commands-header", classes="panel-header"),
                    VerticalScroll(
                        Static("Select a group to see commands", id="commands-list"),
                        id="commands-scroll",
                        classes="commands-scroll"
                    ),
                    classes="commands-panel"
                ),

                classes="selection-row"
            ),

            # Command Info & Parameters
            Container(
                Static("[bold]Command Details[/bold]", classes="panel-header"),
                Static("No command selected", id="command-info", classes="command-info"),
                classes="info-panel"
            ),

            # Execution Controls
            Container(
                Horizontal(
                    Button("▶️  Execute", id="btn-execute", variant="primary"),
                    Button("⏹️  Stop", id="btn-stop", variant="error"),
                    Button("🧹 Clear Output", id="btn-clear-output"),
                    classes="exec-buttons"
                ),
                classes="exec-panel"
            ),

            # Progress Bar
            Container(
                Static("Status: Ready", id="exec-status"),
                ProgressBar(id="exec-progress", total=100, show_eta=False),
                classes="progress-panel"
            ),

            # Output Panel
            Container(
                Static("[bold]Output[/bold]", classes="panel-header"),
                VerticalScroll(
                    Static("", id="command-output"),
                    id="output-scroll",
                    classes="output-scroll"
                ),
                classes="output-panel"
            ),

            id="main-content"
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the scripts screen."""
        from cerebro.tui.commands.router import CommandRouter

        self.router = CommandRouter()
        self.commands = await self.router.get_available_commands()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id

        if button_id and button_id.startswith("group-"):
            group_name = button_id.replace("group-", "")
            self.select_group(group_name)
        elif button_id and button_id.startswith("cmd-"):
            command_name = button_id.replace("cmd-", "").split("-", 1)[1]
            self.select_command(command_name)
        elif button_id == "btn-execute":
            self.action_execute_command()
        elif button_id == "btn-stop":
            self.action_stop_execution()
        elif button_id == "btn-clear-output":
            self.action_clear_output()

    def select_group(self, group_name: str) -> None:
        """Select a command group and display its commands."""
        self.selected_group = group_name
        self.selected_command = None

        # Update header
        header = self.query_one("#commands-header", Static)
        header.update(f"[bold]{group_name.capitalize()} Commands[/bold]")

        # Display commands for this group
        commands_list = self.commands.get(group_name, [])
        commands_container = self.query_one("#commands-list", Static)

        if commands_list:
            buttons_html = []
            for cmd in commands_list:
                buttons_html.append(f"  • {cmd}")

            commands_container.update("\n".join(buttons_html))
        else:
            commands_container.update("[dim]No commands in this group[/dim]")

        # Clear command info
        info = self.query_one("#command-info", Static)
        info.update(f"[dim]Select a command from the {group_name} group[/dim]")

    def select_command(self, command_name: str) -> None:
        """Select a specific command and display its info."""
        if not self.selected_group:
            return

        self.selected_command = command_name

        # Display command info (simplified - would fetch from router in production)
        info = self.query_one("#command-info", Static)
        info_text = f"""
[cyan]Group:[/cyan] {self.selected_group}
[cyan]Command:[/cyan] {command_name}
[cyan]Description:[/cyan] Execute {self.selected_group} {command_name} command

[yellow]Parameters:[/yellow]
(Parameter forms would appear here in full implementation)

[dim]Click Execute to run this command[/dim]
        """
        info.update(info_text.strip())

    async def action_execute_command(self) -> None:
        """Execute the selected command."""
        if not self.selected_group or not self.selected_command:
            self.notify("Please select a command first", severity="warning")
            return

        # Update status
        status = self.query_one("#exec-status", Static)
        status.update(f"[yellow]🔄 Executing {self.selected_group} {self.selected_command}...[/yellow]")

        # Clear previous output
        output = self.query_one("#command-output", Static)
        output.update("[dim]Starting execution...[/dim]\n")

        # Show progress
        progress = self.query_one("#exec-progress", ProgressBar)

        try:
            # Route to appropriate command
            command_map = {
                ("gcp", "burn"): self.router.run_batch_burn,
                ("gcp", "monitor"): lambda: self._simple_command(self.router.monitor_gcp_credits),
                ("strategy", "optimize"): self.router.run_strategy_optimizer,
                ("content", "mine"): lambda: self.router.run_content_miner("default_topic"),
                ("test", "grounded-search"): lambda: self.router.run_grounded_search_test("test query"),
                ("knowledge", "index-repo"): lambda: self.router.run_knowledge_index("."),
                ("knowledge", "docs"): lambda: self.router.generate_documentation("project"),
            }

            command_key = (self.selected_group, self.selected_command)
            command_func = command_map.get(command_key)

            if not command_func:
                output.update(f"[yellow]⚠️  Command not yet implemented: {self.selected_group} {self.selected_command}[/yellow]")
                status.update("[yellow]⚠️  Not implemented[/yellow]")
                return

            # Execute and stream results
            output_lines = []
            async for update in command_func():
                status_val = update.get("status")
                message = update.get("message", "")
                prog = update.get("progress", 0)

                # Update progress bar
                progress.update(progress=prog)

                # Update output
                output_lines.append(message)
                output.update("\n".join(output_lines))

                # Update status
                if status_val == "complete":
                    result = update.get("result", {})
                    status.update("[green]✓ Complete[/green]")
                    output_lines.append(f"\n[green]✓ Result: {result}[/green]")
                    output.update("\n".join(output_lines))
                elif status_val == "error":
                    status.update("[red]✗ Error[/red]")

        except Exception as e:
            status.update("[red]✗ Execution failed[/red]")
            output.update(f"[red]✗ Error: {str(e)}[/red]")

    async def _simple_command(self, coro):
        """Wrapper for commands that return dict instead of streaming."""
        result = await coro()
        yield {"status": "complete", "progress": 100, "message": "Done", "result": result}

    def action_stop_execution(self) -> None:
        """Stop current command execution."""
        self.notify("Stop functionality coming soon", severity="information")

    def action_clear_output(self) -> None:
        """Clear command output."""
        output = self.query_one("#command-output", Static)
        output.update("")

        status = self.query_one("#exec-status", Static)
        status.update("Status: Ready")

        progress = self.query_one("#exec-progress", ProgressBar)
        progress.update(progress=0)


class GCPCreditsScreen(Screen):
    """GCP Credit Management & Batch Execution."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = None
        self.credits_info = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Static("💰 [bold cyan]GCP Credits[/bold cyan]", classes="screen-title"),

            # Credit Status Panel
            Container(
                Static("[bold]Credit Status[/bold]", classes="panel-header"),
                Static("Loading...", id="credits-display"),
                ProgressBar(id="credits-progress", total=100, show_percentage=True),
                classes="credits-panel"
            ),

            # Batch Execution Controls
            Container(
                Static("[bold]Batch Execution[/bold]", classes="panel-header"),
                Horizontal(
                    Container(
                        Label("Queries:", classes="burn-label"),
                        Input(value="100", id="burn-queries", classes="burn-input"),
                        classes="burn-field"
                    ),
                    Container(
                        Label("Workers:", classes="burn-label"),
                        Input(value="10", id="burn-workers", classes="burn-input"),
                        classes="burn-field"
                    ),
                    classes="burn-inputs"
                ),
                Horizontal(
                    Button("▶️  Execute Batch", id="btn-start-burn", variant="primary"),
                    Button("⏹️  Stop", id="btn-stop-burn", variant="error"),
                    Button("🔄 Refresh", id="btn-refresh"),
                    classes="burn-buttons"
                ),
                classes="burn-panel"
            ),

            # Burn Progress
            Container(
                Static("Status: Ready", id="burn-status"),
                ProgressBar(id="burn-progress", total=100, show_eta=False),
                classes="burn-progress-panel"
            ),

            # Execution Results/History
            Container(
                Static("[bold]Execution History[/bold]", classes="panel-header"),
                VerticalScroll(
                    Static("No batch operations yet", id="burn-history"),
                    id="history-scroll",
                    classes="history-scroll"
                ),
                classes="history-panel"
            ),

            # Cost Calculator
            Container(
                Static("[bold]Cost Estimator[/bold]", classes="panel-header"),
                Static(
                    "[dim]Average cost per query: $0.002\n"
                    "100 queries ≈ $0.20\n"
                    "1000 queries ≈ $2.00[/dim]",
                    id="cost-estimate"
                ),
                classes="cost-panel"
            ),

            id="main-content"
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the GCP credits screen."""
        from cerebro.tui.commands.router import CommandRouter

        self.router = CommandRouter()
        await self.load_credits()

    async def load_credits(self) -> None:
        """Load current credit status."""
        if not self.router:
            return

        try:
            self.credits_info = await self.router.monitor_gcp_credits()

            total = self.credits_info.get("total_credits", 0)
            used = self.credits_info.get("used_credits", 0)
            remaining = self.credits_info.get("remaining_credits", 0)
            percentage = self.credits_info.get("usage_percentage", 0)

            # Update display
            credits_display = self.query_one("#credits-display", Static)
            credits_text = f"""
[cyan]Total Credits:[/cyan] ${total:.2f}
[yellow]Used:[/yellow] ${used:.2f}
[green]Remaining:[/green] ${remaining:.2f}
[magenta]Usage:[/magenta] {percentage:.1f}%
            """
            credits_display.update(credits_text.strip())

            # Update progress bar
            progress = self.query_one("#credits-progress", ProgressBar)
            progress.update(progress=int(percentage))

        except Exception as e:
            credits_display = self.query_one("#credits-display", Static)
            credits_display.update(f"[red]Error loading credits: {str(e)}[/red]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "btn-start-burn":
            self.action_start_burn()
        elif event.button.id == "btn-stop-burn":
            self.action_stop_burn()
        elif event.button.id == "btn-refresh":
            self.action_refresh()

    async def action_start_burn(self) -> None:
        """Start batch execution operation."""
        if not self.router:
            return

        # Get parameters
        try:
            queries_input = self.query_one("#burn-queries", Input)
            workers_input = self.query_one("#burn-workers", Input)

            queries = int(queries_input.value) if queries_input.value else 100
            workers = int(workers_input.value) if workers_input.value else 10
        except ValueError:
            self.notify("Invalid input values", severity="error")
            return

        # Confirm large burns
        if queries > 1000:
            self.notify("Large batch requested. Confirm in status bar.", severity="warning")
            # In production, show a confirmation dialog

        # Update status
        status = self.query_one("#burn-status", Static)
        status.update(f"[yellow]Executing {queries} queries with {workers} workers...[/yellow]")

        # Clear history and prepare for new entry
        history = self.query_one("#burn-history", Static)

        try:
            history_lines = []
            progress_bar = self.query_one("#burn-progress", ProgressBar)

            async for update in self.router.run_batch_burn(queries, workers):
                status_val = update.get("status")
                message = update.get("message", "")
                prog = update.get("progress", 0)

                # Update progress
                progress_bar.update(progress=prog)
                status.update(f"[yellow]{message}[/yellow]")

                if status_val == "complete":
                    result = update.get("result", {})
                    queries_processed = result.get("queries_processed", 0)

                    # Update status
                    status.update(f"[green]✓ Batch complete: {queries_processed} queries[/green]")

                    # Add to history
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    history_entry = f"[{timestamp}] {queries_processed} queries, {workers} workers - [green]Complete[/green]"
                    history_lines.insert(0, history_entry)
                    history.update("\n".join(history_lines[:10]))  # Keep last 10

                    # Refresh credits
                    await self.load_credits()

                elif status_val == "error":
                    status.update(f"[red]✗ Execution failed: {message}[/red]")

        except Exception as e:
            status.update(f"[red]✗ Error: {str(e)}[/red]")

    def action_stop_burn(self) -> None:
        """Stop current batch operation."""
        self.notify("Stop functionality coming soon", severity="information")

    async def action_refresh(self) -> None:
        """Refresh credit information."""
        await self.load_credits()
        self.notify("Credits refreshed", severity="information")


class LogsScreen(Screen):
    """Live log viewer with filtering.

    Set the CEREBRO_DEMO_MODE env var to "0" (or any falsy value) to connect
    to the real Python logging system instead of generating simulated logs.
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("p", "toggle_pause", "Pause"),
        Binding("c", "clear_logs", "Clear"),
    ]

    # True by default; set CEREBRO_DEMO_MODE=0 to disable
    DEMO_MODE: bool = os.getenv("CEREBRO_DEMO_MODE", "1").strip() not in ("0", "false", "")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use deque for efficient ring buffer
        from collections import deque
        self.log_buffer = deque(maxlen=1000)
        self.paused = False
        self.filter_level = "ALL"
        self.filter_module = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Static("📋 [bold cyan]Logs[/bold cyan]", classes="screen-title"),

            # Filter Controls
            Container(
                Horizontal(
                    Label("Level:", classes="filter-label"),
                    Button("ALL", id="level-all", variant="primary", classes="level-btn"),
                    Button("INFO", id="level-info", classes="level-btn"),
                    Button("WARNING", id="level-warning", classes="level-btn"),
                    Button("ERROR", id="level-error", classes="level-btn"),
                    classes="filter-row"
                ),
                Horizontal(
                    Label("Module:", classes="filter-label"),
                    Input(placeholder="Filter by module...", id="module-filter", classes="module-input"),
                    Label("  ", classes="spacer"),
                    Button("⏸️  Pause", id="btn-pause", classes="control-btn"),
                    Button("🧹 Clear", id="btn-clear", classes="control-btn"),
                    Button("💾 Export", id="btn-export", classes="control-btn"),
                    classes="filter-row"
                ),
                classes="filter-panel"
            ),

            # Log Display
            Container(
                VerticalScroll(
                    Static("", id="logs-display"),
                    id="logs-scroll",
                    classes="logs-scroll"
                ),
                classes="logs-panel"
            ),

            # Status Bar
            Container(
                Static(
                    "[green]● Live[/green] | Logs: 0 | Filtered: 0",
                    id="logs-status"
                ),
                classes="logs-status-panel"
            ),

            id="main-content"
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the logs screen."""
        self.add_log("INFO", "cerebro.core", "Cerebro TUI initialized")
        self.add_log("INFO", "cerebro.router", "Command router ready")
        self.add_log("INFO", "cerebro.intelligence", "Intelligence engine loaded")

        if self.DEMO_MODE:
            self.set_interval(2.0, self.add_simulated_log)
        else:
            self._attach_real_logging()

    def add_log(self, level: str, module: str, message: str) -> None:
        """Add a log entry to the buffer."""
        import datetime

        if self.paused:
            return

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # Apply filters
        if self.filter_level != "ALL" and level != self.filter_level:
            return

        if self.filter_module and self.filter_module.lower() not in module.lower():
            return

        # Color code by level
        level_colors = {
            "INFO": "cyan",
            "WARNING": "yellow",
            "ERROR": "red",
            "DEBUG": "dim"
        }
        color = level_colors.get(level, "white")

        log_entry = f"[dim]{timestamp}[/dim] [{color}]{level:8}[/{color}] [yellow]{module:20}[/yellow] | {message}"

        # Add to buffer (deque automatically handles max length)
        self.log_buffer.append(log_entry)

        # Update display
        self.update_logs_display()

    def add_simulated_log(self) -> None:
        """Add simulated log entries for demo."""
        import random

        if self.paused:
            return

        modules = [
            "cerebro.core",
            "cerebro.router",
            "cerebro.intelligence",
            "cerebro.scanner",
            "cerebro.indexer",
            "cerebro.api"
        ]

        messages = [
            "Processing request",
            "Indexing complete",
            "Query executed successfully",
            "Cache hit",
            "Background task started",
            "Health check passed"
        ]

        levels_weighted = ["INFO"] * 7 + ["WARNING"] * 2 + ["ERROR"] * 1

        level = random.choice(levels_weighted)
        module = random.choice(modules)
        message = random.choice(messages)

        self.add_log(level, module, message)

    def _attach_real_logging(self) -> None:
        """Install a logging handler that routes Python log records into the TUI."""
        import logging

        screen = self  # capture for the closure

        class _TUIHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                try:
                    screen.add_log(record.levelname, record.name, record.getMessage())
                except Exception:
                    pass

        handler = _TUIHandler()
        handler.setLevel(logging.DEBUG)
        # Attach to the root "cerebro" logger so all sub-loggers are captured
        logging.getLogger("cerebro").addHandler(handler)

    def update_logs_display(self) -> None:
        """Update the logs display widget."""
        logs_display = self.query_one("#logs-display", Static)

        # Show last 100 logs
        display_logs = self.log_buffer[-100:]
        logs_display.update("\n".join(display_logs))

        # Update status
        status = self.query_one("#logs-status", Static)
        pause_indicator = "[yellow]⏸️  Paused[/yellow]" if self.paused else "[green]● Live[/green]"
        status.update(
            f"{pause_indicator} | "
            f"Logs: {len(self.log_buffer)} | "
            f"Displayed: {len(display_logs)}"
        )

        # Auto-scroll to bottom if not paused
        if not self.paused:
            logs_scroll = self.query_one("#logs-scroll", VerticalScroll)
            logs_scroll.scroll_end(animate=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id

        if button_id and button_id.startswith("level-"):
            level = button_id.replace("level-", "").upper()
            self.filter_level = level
            self.update_level_buttons()
            self.refilter_logs()
        elif button_id == "btn-pause":
            self.action_toggle_pause()
        elif button_id == "btn-clear":
            self.action_clear_logs()
        elif button_id == "btn-export":
            self.action_export_logs()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle module filter changes."""
        if event.input.id == "module-filter":
            self.filter_module = event.value
            self.refilter_logs()

    def update_level_buttons(self) -> None:
        """Update level filter button styles."""
        for level in ["ALL", "INFO", "WARNING", "ERROR"]:
            button_id = f"level-{level.lower()}"
            try:
                button = self.query_one(f"#{button_id}", Button)
                button.variant = "primary" if level == self.filter_level else "default"
            except Exception:
                pass

    def refilter_logs(self) -> None:
        """Reapply filters to all logs."""
        # For simplicity, just update display
        # In production, would rebuild log_buffer from full unfiltered buffer
        self.update_logs_display()

    def action_toggle_pause(self) -> None:
        """Toggle pause state."""
        self.paused = not self.paused

        # Update button
        pause_btn = self.query_one("#btn-pause", Button)
        pause_btn.label = "▶️  Resume" if self.paused else "⏸️  Pause"

        self.update_logs_display()

        status = "paused" if self.paused else "resumed"
        self.notify(f"Logs {status}", severity="information")

    def action_clear_logs(self) -> None:
        """Clear all logs."""
        self.log_buffer.clear()
        self.update_logs_display()
        self.notify("Logs cleared", severity="information")

    def action_export_logs(self) -> None:
        """Export logs to file."""
        self.notify("Export functionality coming soon", severity="information")


class HelpScreen(Screen):
    """Comprehensive help screen with keyboard shortcuts and tips."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("q", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Static("❓ [bold cyan]Cerebro TUI Help[/bold cyan]", classes="screen-title"),

            # Keyboard Shortcuts Section
            Container(
                Static("[bold]⌨️  Keyboard Shortcuts[/bold]", classes="panel-header"),
                Static(
                    """[cyan]Global Navigation:[/cyan]
  d - Dashboard (system overview)
  p - Projects (repository management)
  i - Intelligence (query interface)
  s - Scripts (command launcher)
  g - GCP Credits (credit management)
  l - Logs (log monitoring)
  q - Quit application
  ? - Show this help screen

[cyan]Screen-Specific:[/cyan]
  r - Refresh current screen
  / - Search/Filter (where applicable)
  Esc - Back/Exit current screen
  Enter - Submit/Execute
  Tab - Cycle through widgets

[cyan]Dashboard:[/cyan]
  s - Quick scan projects
  r - Refresh metrics

[cyan]Projects:[/cyan]
  / - Filter projects
  r - Refresh project list
  Click row - View details

[cyan]Intelligence:[/cyan]
  Ctrl+Q - Focus query input
  Enter - Execute query

[cyan]Logs:[/cyan]
  p - Pause/Resume log tail
  c - Clear all logs
                    """,
                    classes="help-content"
                ),
                classes="help-panel"
            ),

            # Features by Screen Section
            Container(
                Static("[bold]📱 Features by Screen[/bold]", classes="panel-header"),
                Static(
                    """[yellow]Dashboard:[/yellow]
  • Real-time system metrics
  • Health score tracking
  • Alert monitoring
  • Quick actions (Scan, Query, Refresh)
  • Auto-refresh every 10 seconds

[yellow]Projects:[/yellow]
  • Sortable/filterable DataTable
  • Health score visualization
  • Color-coded status indicators
  • Project details on selection
  • Search functionality
  • Handles 1000+ projects

[yellow]Intelligence:[/yellow]
  • Natural language queries
  • Semantic vs Exact search modes
  • Configurable result limit
  • Progress tracking
  • Query history
  • Formatted results display

[yellow]Scripts:[/yellow]
  • 24 CLI commands organized in 7 groups
  • Real-time execution progress
  • Live output streaming
  • Command history
  • Parameter input (basic)

[yellow]GCP Credits:[/yellow]
  • Credit balance tracking
  • Usage percentage visualization
  • Batch execution interface
  • Real-time progress monitoring
  • Execution history log
  • Cost estimates

[yellow]Logs:[/yellow]
  • Live log tail
  • Level filtering (ALL/INFO/WARNING/ERROR)
  • Module name filtering
  • Color-coded log levels
  • Pause/Resume functionality
  • Ring buffer (1000 max logs)
                    """,
                    classes="help-content"
                ),
                classes="help-panel"
            ),

            # Tips & Tricks Section
            Container(
                Static("[bold]💡 Tips & Tricks[/bold]", classes="panel-header"),
                Static(
                    """• Use keyboard shortcuts for fast navigation
• Dashboard auto-refreshes - no manual refresh needed
• Projects screen: Type / then search term for instant filtering
• Intelligence: Toggle Semantic mode for better results
• Scripts: Monitor progress in real-time
• GCP Credits: Watch execution progress live
• Logs: Pause before searching to prevent auto-scroll
• All screens: Press r to manually refresh data
• Use Tab key to navigate between input fields
• Esc always goes back or exits
                    """,
                    classes="help-content"
                ),
                classes="help-panel"
            ),

            # Command Groups Section
            Container(
                Static("[bold]⚙️  Available Command Groups[/bold]", classes="panel-header"),
                Static(
                    """[green]knowledge[/green] (9 commands)
  analyze, batch-analyze, summarize, generate-queries,
  index-repo, etl, docs, and more

[green]rag[/green] (3 commands)
  ingest, query, health

[green]ops[/green] (1 command)
  health

[green]gcp[/green] (3 commands)
  burn, monitor, create-engine

[green]strategy[/green] (4 commands)
  optimize, salary, moat, trends

[green]content[/green] (1 command)
  mine

[green]test[/green] (3 commands)
  grounded-search, grounded-gen, verify-api

[dim]Access all commands from the Scripts screen (s)[/dim]
                    """,
                    classes="help-content"
                ),
                classes="help-panel"
            ),

            # About Section
            Container(
                Static("[bold]ℹ️  About Cerebro[/bold]", classes="panel-header"),
                Static(
                    """[cyan]Version:[/cyan] 0.1.0 (Phase 3 Complete)
[cyan]Project:[/cyan] Cerebro - Enterprise Knowledge Extraction Platform
[cyan]TUI Framework:[/cyan] Textual 0.47+
[cyan]License:[/cyan] MIT

[yellow]Architecture:[/yellow]
  • TUI (Textual) - Interactive terminal interface
  • CLI (Typer) - Scriptable command-line interface
  • GUI (React) - Web dashboard (coming soon)
  • Backend (FastAPI) - Unified API

[yellow]Documentation:[/yellow]
  • PHASE3_QUICK_START.md - User guide
  • PHASE3_IMPLEMENTATION_COMPLETE.md - Technical details
  • docs/ADR_SUMMARY.md - Architecture decisions
  • CEREBRO_OPTIMIZATION_PLAN.md - Project roadmap

[dim]Press Esc or q to close this help screen[/dim]
                    """,
                    classes="help-content"
                ),
                classes="help-panel"
            ),

            id="main-content"
        )
        yield Footer()


class CerebroApp(App):
    """
    Cerebro TUI - Interactive Terminal Interface

    Unified interface for code analysis, RAG queries, and GCP management.
    """

    CSS = """
    Screen {
        layout: horizontal;
    }

    Sidebar {
        width: 20;
        background: $panel;
        border-right: solid $primary;
        padding: 1;
    }

    .sidebar-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        padding: 1;
        background: $primary-darken-2;
    }

    .sidebar-spacer {
        height: 1fr;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }

    #main-content {
        width: 1fr;
        height: 100%;
        padding: 2;
        overflow-y: auto;
    }

    .screen-title {
        text-style: bold;
        margin-bottom: 2;
        padding-bottom: 1;
        border-bottom: solid $primary;
    }

    .screen-content {
        padding: 1;
    }

    /* Dashboard Panels */
    .metrics-panel, .alerts-panel, .actions-panel, .activity-panel {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
    }

    .panel-header {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .metrics-content, .alerts-content, .activity-content {
        padding: 1;
    }

    .action-buttons {
        height: auto;
    }

    .action-buttons Button {
        margin-right: 1;
        width: auto;
    }

    /* Projects Screen */
    .search-container {
        height: auto;
        margin-bottom: 1;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    .search-label {
        width: auto;
        margin-right: 1;
    }

    #search-input {
        width: 1fr;
    }

    .projects-table {
        height: 20;
        margin-bottom: 1;
        border: solid $primary;
    }

    .details-panel {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: auto;
    }

    .details-content {
        padding: 1;
    }

    /* Intelligence Screen */
    .query-container {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: auto;
    }

    .query-label {
        width: auto;
        margin-bottom: 1;
    }

    .query-input {
        width: 100%;
        margin-bottom: 1;
    }

    .query-buttons {
        height: auto;
    }

    .query-buttons Button {
        margin-right: 1;
        width: auto;
    }

    .options-container {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: auto;
    }

    .options-row {
        height: auto;
        align: center middle;
    }

    .option-label {
        width: auto;
        margin-right: 1;
    }

    .mode-btn {
        margin-right: 1;
        width: auto;
    }

    .limit-input {
        width: 10;
    }

    .status-container {
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        border: solid $primary;
        height: auto;
    }

    .status-text {
        text-align: center;
    }

    .results-panel {
        border: solid $primary;
        padding: 1;
        background: $panel;
        height: 1fr;
    }

    .results-scroll {
        height: 100%;
        border: none;
    }

    #results-display {
        padding: 1;
    }

    /* Scripts Screen */
    .selection-row {
        height: 15;
        margin-bottom: 1;
    }

    .groups-panel {
        width: 20;
        border: solid $primary;
        padding: 1;
        background: $panel;
        margin-right: 1;
    }

    .groups-scroll {
        height: 100%;
        border: none;
    }

    .group-btn {
        width: 100%;
        margin-bottom: 1;
    }

    .commands-panel {
        width: 1fr;
        border: solid $primary;
        padding: 1;
        background: $panel;
    }

    .commands-scroll {
        height: 100%;
        border: none;
    }

    .info-panel {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: auto;
    }

    .command-info {
        padding: 1;
    }

    .exec-panel {
        height: auto;
        margin-bottom: 1;
    }

    .exec-buttons {
        height: auto;
    }

    .exec-buttons Button {
        margin-right: 1;
        width: auto;
    }

    .progress-panel {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: auto;
    }

    #exec-status {
        margin-bottom: 1;
    }

    .output-panel {
        border: solid $primary;
        padding: 1;
        background: $panel;
        height: 1fr;
    }

    .output-scroll {
        height: 100%;
        border: none;
    }

    #command-output {
        padding: 1;
    }

    /* GCP Credits Screen */
    .credits-panel {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: auto;
    }

    #credits-display {
        padding: 1;
        margin-bottom: 1;
    }

    #credits-progress {
        margin-bottom: 1;
    }

    .burn-panel {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: auto;
    }

    .burn-inputs {
        height: auto;
        margin-bottom: 1;
    }

    .burn-field {
        margin-right: 2;
        width: auto;
    }

    .burn-label {
        width: auto;
        margin-right: 1;
    }

    .burn-input {
        width: 15;
    }

    .burn-buttons {
        height: auto;
    }

    .burn-buttons Button {
        margin-right: 1;
        width: auto;
    }

    .burn-progress-panel {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: auto;
    }

    #burn-status {
        margin-bottom: 1;
    }

    .history-panel {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: 15;
    }

    .history-scroll {
        height: 100%;
        border: none;
    }

    .cost-panel {
        border: solid $primary;
        padding: 1;
        background: $panel;
        height: auto;
    }

    #cost-estimate {
        padding: 1;
    }

    /* Logs Screen */
    .filter-panel {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: auto;
    }

    .filter-row {
        height: auto;
        margin-bottom: 1;
    }

    .filter-label {
        width: auto;
        margin-right: 1;
    }

    .level-btn {
        margin-right: 1;
        width: auto;
    }

    .module-input {
        width: 30;
        margin-right: 1;
    }

    .spacer {
        width: 2;
    }

    .control-btn {
        margin-right: 1;
        width: auto;
    }

    .logs-panel {
        border: solid $primary;
        padding: 1;
        background: $panel;
        height: 1fr;
        margin-bottom: 1;
    }

    .logs-scroll {
        height: 100%;
        border: none;
    }

    #logs-display {
        padding: 1;
        overflow-y: auto;
    }

    .logs-status-panel {
        border: solid $primary;
        padding: 1;
        background: $panel;
        height: auto;
    }

    #logs-status {
        text-align: center;
    }

    /* Help Screen */
    .help-panel {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $panel;
        height: auto;
    }

    .help-content {
        padding: 1;
        line-height: 1.5;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("?", "show_help", "Help"),
        Binding("d", "show_dashboard", "Dashboard"),
        Binding("p", "show_projects", "Projects"),
        Binding("i", "show_intelligence", "Intelligence"),
        Binding("s", "show_scripts", "Scripts"),
        Binding("g", "show_gcp", "GCP"),
        Binding("l", "show_logs", "Logs"),
    ]

    SCREENS = {
        "dashboard": DashboardScreen,
        "projects": ProjectsScreen,
        "intelligence": IntelligenceScreen,
        "scripts": ScriptsScreen,
        "gcp": GCPCreditsScreen,
        "logs": LogsScreen,
        "help": HelpScreen,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from cerebro.tui.state import TUIState
        self.state_manager = TUIState()

    def compose(self) -> ComposeResult:
        """Build the application layout."""
        yield Sidebar()
        yield Header(show_clock=True)
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app by showing last screen or dashboard."""
        # Load last screen from state
        last_screen = self.state_manager.get("last_screen", "dashboard")

        # Ensure it's a valid screen
        if last_screen in self.SCREENS:
            self.push_screen(last_screen)
        else:
            self.push_screen("dashboard")

    def on_unmount(self) -> None:
        """Save state when app closes."""
        # Save current screen if we have one
        if self.screen_stack:
            current_screen = self.screen.name if hasattr(self.screen, "name") else "dashboard"
            self.state_manager.set("last_screen", current_screen)

        # Final save
        self.state_manager.save()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle sidebar button clicks."""
        button_id = event.button.id

        if button_id == "nav-quit":
            self.exit()
        elif button_id and button_id.startswith("nav-"):
            screen_name = button_id.replace("nav-", "")
            if screen_name in self.SCREENS:
                self.switch_screen(screen_name)

    def action_show_dashboard(self) -> None:
        """Show dashboard screen."""
        self.switch_screen("dashboard")

    def action_show_projects(self) -> None:
        """Show projects screen."""
        self.switch_screen("projects")

    def action_show_intelligence(self) -> None:
        """Show intelligence screen."""
        self.switch_screen("intelligence")

    def action_show_scripts(self) -> None:
        """Show scripts screen."""
        self.switch_screen("scripts")

    def action_show_gcp(self) -> None:
        """Show GCP credits screen."""
        self.switch_screen("gcp")

    def action_show_logs(self) -> None:
        """Show logs screen."""
        self.switch_screen("logs")

    def action_show_help(self) -> None:
        """Show help screen."""
        self.push_screen("help")


def main():
    """Run the Cerebro TUI application."""
    app = CerebroApp()
    app.run()


if __name__ == "__main__":
    main()
