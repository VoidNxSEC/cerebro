"""
Cerebro Smart Launcher

Automatically detects the best interface based on environment:
- Non-interactive (pipe/script) → CLI
- GUI environment variable → Dashboard (GUI)
- Interactive terminal with args → CLI
- Interactive terminal no args → TUI (default)
"""

import sys
import os
import subprocess
from pathlib import Path


def detect_environment() -> str:
    """
    Detect the best interface for the current environment.

    Returns:
        str: One of "cli", "tui", or "gui"
    """
    # Check for GUI environment variable
    if os.getenv("CEREBRO_GUI") or os.getenv("CEREBRO_DASHBOARD"):
        return "gui"

    # Check if running in non-interactive mode (pipe/script)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return "cli"

    # If user provided arguments (and not just "tui"), use CLI
    if len(sys.argv) > 1:
        # Check if first arg is a mode selector
        if sys.argv[1] in ("tui", "gui", "dashboard"):
            return sys.argv[1] if sys.argv[1] != "dashboard" else "gui"
        # Otherwise it's a CLI command
        return "cli"

    # Default to TUI for interactive terminals with no args
    return "tui"


def launch_tui():
    """Launch the Text User Interface."""
    try:
        from cerebro.tui.app import main as run_tui
        run_tui()
    except ImportError as e:
        print(f"Error: TUI dependencies not installed: {e}")
        print("Install with: poetry install --extras tui")
        print("\nRequired: textual>=0.47.0")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching TUI: {e}")
        print("Try running with --debug for more information")
        sys.exit(1)


def launch_gui():
    """Launch the Dashboard GUI (React + FastAPI)."""
    print("🚀 Launching Cerebro Dashboard...")

    # Check if dashboard exists
    dashboard_dir = Path(__file__).parent.parent.parent / "dashboard"
    if not dashboard_dir.exists():
        print("Error: Dashboard directory not found")
        sys.exit(1)

    # Start the backend API server
    print("📡 Starting backend API server...")
    backend_process = subprocess.Popen(
        ["uvicorn", "cerebro.api.server:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=Path(__file__).parent.parent.parent,
    )

    # Start the frontend dev server
    print("🎨 Starting frontend dev server...")
    try:
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=dashboard_dir,
        )

        print("\n✅ Cerebro Dashboard is running!")
        print("   Backend:  http://localhost:8000")
        print("   Frontend: http://localhost:5173")
        print("\nPress Ctrl+C to stop both servers\n")

        # Wait for user interrupt
        try:
            frontend_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            frontend_process.terminate()
            backend_process.terminate()
            frontend_process.wait()
            backend_process.wait()
            print("✅ Shutdown complete")

    except Exception as e:
        print(f"Error starting frontend: {e}")
        backend_process.terminate()
        sys.exit(1)


def launch_cli():
    """Launch the CLI interface."""
    from cerebro.cli import app
    app()


def main():
    """Main entry point with smart detection."""
    # Detect the best interface
    mode = detect_environment()

    # Remove mode selector from args if present
    if len(sys.argv) > 1 and sys.argv[1] in ("tui", "gui", "dashboard"):
        sys.argv.pop(1)

    # Launch the appropriate interface
    if mode == "tui":
        launch_tui()
    elif mode == "gui":
        launch_gui()
    else:  # cli
        launch_cli()


if __name__ == "__main__":
    main()
