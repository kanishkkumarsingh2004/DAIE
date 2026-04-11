"""Tests for CLI module - Command-Line Interface for System Management.
Updated to work with argparse instead of typer.
"""

import io
import sys
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import pytest

from daie.cli.main import cli


class CliRunner:
    """Helper to test argparse-based CLI."""

    def invoke(self, app_func, args=None):
        if args is None:
            args = []

        stdout = io.StringIO()
        # Mock sys.argv for argparse.parse_args()
        with patch.object(sys, "argv", ["daie"] + args):
            with redirect_stdout(stdout):
                try:
                    app_func()
                    exit_code = 0
                except SystemExit as e:
                    exit_code = e.code if e.code is not None else 0
                except Exception:
                    exit_code = 1

        return Mock(exit_code=exit_code, output=stdout.getvalue())


class TestCLI:
    """Tests for main CLI commands."""

    def test_cli_help(self):
        """Test main CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "DAIE" in result.output
        assert "Available Commands" in result.output

    @patch("daie.cli.core.start_server")
    @patch("daie.cli.core.DecentralizedAISystem")
    def test_core_cli_start(self, mock_system, mock_start_server):
        """Test core system CLI start command."""
        runner = CliRunner()

        mock_instance = Mock()
        mock_system.return_value = mock_instance

        # Patch read_pid to return None (not running)
        with patch("daie.cli.core.read_pid", return_value=None):
            result = runner.invoke(cli, ["core", "start"])

        assert result.exit_code == 0
        assert "Starting Central Core" in result.output

    @patch("os.kill")
    @patch("daie.cli.core.read_pid")
    def test_core_cli_stop(self, mock_read_pid, mock_kill):
        """Test core system CLI stop command."""
        runner = CliRunner()
        mock_read_pid.return_value = 1234

        result = runner.invoke(cli, ["core", "stop"])

        assert result.exit_code == 0
        assert "Stopping Central Core" in result.output

    def test_agent_cli_start(self):
        """Test agent CLI start command."""
        runner = CliRunner()

        result = runner.invoke(cli, ["agent", "start", "test-agent"])

        assert result.exit_code == 0
        assert "Starting Agent: test-agent" in result.output

    def test_agent_cli_stop(self):
        """Test agent CLI stop command."""
        runner = CliRunner()

        result = runner.invoke(cli, ["agent", "stop", "test-agent"])

        assert result.exit_code == 0
        assert "Stopping Agent: test-agent" in result.output

    def test_agent_cli_status(self):
        """Test agent CLI status command."""
        runner = CliRunner()

        result = runner.invoke(cli, ["agent", "status", "test-agent"])

        assert result.exit_code == 0
        assert "Agent Status: test-agent" in result.output

    def test_core_cli_status(self):
        """Test core system CLI status command."""
        runner = CliRunner()

        result = runner.invoke(cli, ["core", "status"])

        assert result.exit_code == 0
        assert "Central Core System Status" in result.output


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    @patch("daie.cli.core.read_pid")
    def test_core_cli_start_already_running(self, mock_read_pid):
        """Test core system start when already running."""
        runner = CliRunner()
        mock_read_pid.return_value = 1234

        result = runner.invoke(cli, ["core", "start"])

        assert result.exit_code == 1
        assert "already running" in result.output

    def test_agent_cli_missing_id(self):
        """Test agent command with missing ID."""
        runner = CliRunner()

        # Argparse will exit 2 for missing arguments
        result = runner.invoke(cli, ["agent", "start"])

        assert result.exit_code != 0


class TestCLIOptions:
    """Tests for CLI options and arguments."""

    def test_cli_version(self):
        """Test version option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "Version" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
