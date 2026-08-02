"""Tests for the Cerebro Smart Launcher."""

from unittest.mock import patch

from cerebro.launcher import detect_environment


class TestDetectEnvironment:
    """Test the detect_environment() function under various conditions."""

    def test_gui_env_cerebro_gui(self):
        with patch.dict("os.environ", {"CEREBRO_GUI": "1"}, clear=False):
            assert detect_environment() == "gui"

    def test_gui_env_cerebro_dashboard(self):
        with patch.dict("os.environ", {"CEREBRO_DASHBOARD": "1"}, clear=False):
            assert detect_environment() == "gui"

    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_non_interactive_stdin(self, mock_stdout, mock_stdin):
        """Non-interactive stdin (pipe) should return 'cli'."""
        mock_stdin.isatty.return_value = False
        mock_stdout.isatty.return_value = True
        with patch.dict("os.environ", {}, clear=False):
            os_env = {k: v for k, v in __import__("os").environ.items() if k not in ("CEREBRO_GUI", "CEREBRO_DASHBOARD")}
            with patch.dict("os.environ", os_env, clear=True):
                with patch("sys.argv", ["cerebro"]):
                    assert detect_environment() == "cli"

    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_non_interactive_stdout(self, mock_stdout, mock_stdin):
        """Non-interactive stdout (redirect) should return 'cli'."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = False
        with patch.dict("os.environ", {}, clear=False):
            os_env = {k: v for k, v in __import__("os").environ.items() if k not in ("CEREBRO_GUI", "CEREBRO_DASHBOARD")}
            with patch.dict("os.environ", os_env, clear=True):
                with patch("sys.argv", ["cerebro"]):
                    assert detect_environment() == "cli"

    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_cli_with_args(self, mock_stdout, mock_stdin):
        """Interactive terminal with CLI args should return 'cli'."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        with patch.dict("os.environ", {}, clear=False):
            os_env = {k: v for k, v in __import__("os").environ.items() if k not in ("CEREBRO_GUI", "CEREBRO_DASHBOARD")}
            with patch.dict("os.environ", os_env, clear=True):
                with patch("sys.argv", ["cerebro", "info"]):
                    assert detect_environment() == "cli"

    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_tui_mode_selector(self, mock_stdout, mock_stdin):
        """Explicit 'tui' arg should return 'tui'."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        with patch.dict("os.environ", {}, clear=False):
            os_env = {k: v for k, v in __import__("os").environ.items() if k not in ("CEREBRO_GUI", "CEREBRO_DASHBOARD")}
            with patch.dict("os.environ", os_env, clear=True):
                with patch("sys.argv", ["cerebro", "tui"]):
                    assert detect_environment() == "tui"

    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_gui_mode_selector(self, mock_stdout, mock_stdin):
        """Explicit 'gui' arg should return 'gui'."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        with patch.dict("os.environ", {}, clear=False):
            os_env = {k: v for k, v in __import__("os").environ.items() if k not in ("CEREBRO_GUI", "CEREBRO_DASHBOARD")}
            with patch.dict("os.environ", os_env, clear=True):
                with patch("sys.argv", ["cerebro", "gui"]):
                    assert detect_environment() == "gui"

    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_dashboard_mode_selector(self, mock_stdout, mock_stdin):
        """Explicit 'dashboard' arg should return 'gui'."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        with patch.dict("os.environ", {}, clear=False):
            os_env = {k: v for k, v in __import__("os").environ.items() if k not in ("CEREBRO_GUI", "CEREBRO_DASHBOARD")}
            with patch.dict("os.environ", os_env, clear=True):
                with patch("sys.argv", ["cerebro", "dashboard"]):
                    assert detect_environment() == "gui"

    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_default_tui(self, mock_stdout, mock_stdin):
        """Interactive terminal with no args should default to 'tui'."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        with patch.dict("os.environ", {}, clear=False):
            os_env = {k: v for k, v in __import__("os").environ.items() if k not in ("CEREBRO_GUI", "CEREBRO_DASHBOARD")}
            with patch.dict("os.environ", os_env, clear=True):
                with patch("sys.argv", ["cerebro"]):
                    assert detect_environment() == "tui"
