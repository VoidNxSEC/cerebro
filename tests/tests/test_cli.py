from typer.testing import CliRunner

from phantom.cli import app

runner = CliRunner()


def test_info_command():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "PHANTOM Framework" in result.stdout
    # The actual output uses "GCP Integration"
    assert "GCP Integration" in result.stdout


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    # The actual version is v0.1.0
    assert "v0.1.0" in result.stdout
