"""Tests for the Cerebro CLI."""

from typer.testing import CliRunner

from cerebro.cli import app

runner = CliRunner()


def test_info_command():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "CEREBRO" in result.stdout
    assert "GCP Integration" in result.stdout


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    from cerebro import __version__
    assert f"v{__version__}" in result.stdout


def test_version_output_format():
    """Version output should be a single line with 'Cerebro CLI vX.Y.Z'."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip().startswith("Cerebro CLI v")


def test_help_lists_command_groups():
    """--help should list all registered command groups."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "knowledge" in result.stdout
    assert "ops" in result.stdout
    assert "rag" in result.stdout


def test_help_shows_info_and_version():
    """--help should mention info and version commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "info" in result.stdout
    assert "version" in result.stdout


def test_knowledge_help():
    """knowledge --help should show sub-commands."""
    result = runner.invoke(app, ["knowledge", "--help"])
    assert result.exit_code == 0
    assert "analyze" in result.stdout


def test_ops_help():
    """ops --help should show sub-commands."""
    result = runner.invoke(app, ["ops", "--help"])
    assert result.exit_code == 0
    assert "health" in result.stdout
    assert "status" in result.stdout


def test_rag_help():
    """rag --help should show sub-commands."""
    result = runner.invoke(app, ["rag", "--help"])
    assert result.exit_code == 0
    assert "ingest" in result.stdout
    assert "query" in result.stdout


def test_no_args_shows_help():
    """Running with no args should show help (no_args_is_help=True)."""
    result = runner.invoke(app, [])
    # Typer uses exit code 0 or 2 for help display
    assert result.exit_code in (0, 2)
    output = result.stdout + (result.stderr if hasattr(result, 'stderr') and result.stderr else "")
    assert "Usage" in output or "usage" in output.lower()


def test_invalid_command():
    """An unknown command should produce a non-zero exit code."""
    result = runner.invoke(app, ["nonexistent-command-xyz"])
    assert result.exit_code != 0
