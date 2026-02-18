"""Tests for DeepProbe CLI."""

import pytest
from typer.testing import CliRunner
from unittest.mock import MagicMock, patch

from deep_probe.cli import app
from deep_probe.models import ResearchResult, ResearchStatus, TokenUsage

runner = CliRunner()


class TestCLI:
    """Tests for CLI commands."""

    def test_version(self) -> None:
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "deep-probe version" in result.output

    def test_help(self) -> None:
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Research anything, deeply" in result.output

    def test_config_command(self) -> None:
        """Test config command."""
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "GEMINI_API_KEY" in result.output

    def test_quiet_and_verbose_conflict(self) -> None:
        """Test that --quiet and --verbose conflict."""
        result = runner.invoke(app, ["research", "test topic", "--quiet", "--verbose"])
        # Typer uses exit code 2 for argument errors
        assert result.exit_code != 0
        assert "Cannot use both" in result.output

    def test_research_with_mock(self, mock_result: ResearchResult, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test research command with mocked client."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        with patch("deep_probe.cli.DeepProbe") as mock_probe_class:
            mock_probe = MagicMock()
            mock_probe.research.return_value = mock_result
            mock_probe_class.return_value = mock_probe

            result = runner.invoke(app, ["research", "test topic"])
            assert result.exit_code == 0
            assert "Research completed" in result.output

    def test_resume_with_mock(self, mock_result: ResearchResult, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test resume command with mocked client."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        with patch("deep_probe.cli.DeepProbe") as mock_probe_class:
            mock_probe = MagicMock()
            mock_probe.resume.return_value = mock_result
            mock_probe_class.return_value = mock_probe

            # resume uses --resume flag with topic argument
            result = runner.invoke(app, ["research", "test", "--resume", "test-id"])
            assert result.exit_code == 0


class TestQuietMode:
    """Tests for quiet mode output."""

    def test_quiet_output(self, mock_result: ResearchResult, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that quiet mode only outputs report."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        with patch("deep_probe.cli.DeepProbe") as mock_probe_class:
            mock_probe = MagicMock()
            mock_probe.research.return_value = mock_result
            mock_probe_class.return_value = mock_probe

            result = runner.invoke(app, ["research", "test", "--quiet"])
            assert mock_result.report in result.output
            # Should not show status messages
            assert "Research completed" not in result.output