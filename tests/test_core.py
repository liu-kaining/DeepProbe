"""Tests for DeepProbe core client."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from deep_probe import DeepProbe
from deep_probe.exceptions import ProbeAuthError, ProbeNetworkError
from deep_probe.models import ResearchStatus


class TestDeepProbeInit:
    """Tests for DeepProbe initialization."""

    def test_init_with_api_key(self, mock_api_key: str) -> None:
        """Test initialization with explicit API key."""
        probe = DeepProbe(api_key=mock_api_key)
        assert probe.api_key == mock_api_key

    def test_init_with_env_var(self, mock_api_key: str, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test initialization with environment variable."""
        monkeypatch.setenv("GEMINI_API_KEY", mock_api_key)
        probe = DeepProbe()
        assert probe.api_key == mock_api_key

    def test_init_no_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test initialization fails without API key."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(ProbeAuthError):
            DeepProbe()

    def test_init_with_thinking_summaries(self, mock_api_key: str) -> None:
        """Test initialization with thinking_summaries option."""
        probe = DeepProbe(api_key=mock_api_key, thinking_summaries=False)
        assert probe.thinking_summaries is False


class TestDeepProbeResearch:
    """Tests for research methods."""

    def test_research_sync(self, probe: DeepProbe, mock_result) -> None:
        """Test synchronous research method."""
        mock_interaction = MagicMock()
        mock_interaction.id = mock_result.interaction_id

        # Create output mock with explicit thought_summary = None
        mock_output = MagicMock()
        mock_output.text = mock_result.report
        mock_output.thought_summary = None  # Explicitly set to None

        mock_final_interaction = MagicMock()
        mock_final_interaction.status = "completed"
        mock_final_interaction.outputs = [mock_output]

        with patch.object(probe, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.interactions.create.return_value = mock_interaction
            mock_client.interactions.get.return_value = mock_final_interaction
            mock_get_client.return_value = mock_client

            result = probe.research("test topic")
            assert result.interaction_id == mock_result.interaction_id
            assert result.report == mock_result.report

    @pytest.mark.asyncio
    async def test_research_async(self, probe: DeepProbe, mock_result) -> None:
        """Test async research method."""
        mock_interaction = MagicMock()
        mock_interaction.id = mock_result.interaction_id

        mock_output = MagicMock()
        mock_output.text = mock_result.report
        mock_output.thought_summary = None

        mock_final_interaction = MagicMock()
        mock_final_interaction.status = "completed"
        mock_final_interaction.outputs = [mock_output]

        with patch.object(probe, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.interactions.create.return_value = mock_interaction
            mock_client.interactions.get.return_value = mock_final_interaction
            mock_get_client.return_value = mock_client

            result = await probe.research_async("test topic")
            assert result.interaction_id == mock_result.interaction_id


class TestDeepProbeResume:
    """Tests for resume methods."""

    def test_resume_sync(self, probe: DeepProbe, mock_result) -> None:
        """Test synchronous resume method."""
        mock_output = MagicMock()
        mock_output.text = mock_result.report
        mock_output.thought_summary = None

        mock_final_interaction = MagicMock()
        mock_final_interaction.status = "completed"
        mock_final_interaction.outputs = [mock_output]

        with patch.object(probe, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.interactions.get.return_value = mock_final_interaction
            mock_get_client.return_value = mock_client

            result = probe.resume("interaction-id")
            assert result.interaction_id == "interaction-id"

    @pytest.mark.asyncio
    async def test_resume_async(self, probe: DeepProbe, mock_result) -> None:
        """Test async resume method."""
        mock_output = MagicMock()
        mock_output.text = mock_result.report
        mock_output.thought_summary = None

        mock_final_interaction = MagicMock()
        mock_final_interaction.status = "completed"
        mock_final_interaction.outputs = [mock_output]

        with patch.object(probe, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.interactions.get.return_value = mock_final_interaction
            mock_get_client.return_value = mock_client

            result = await probe.resume_async("interaction-id")
            assert result.interaction_id == "interaction-id"


class TestDeepProbeStreaming:
    """Tests for streaming research method."""

    def test_research_stream(self, probe: DeepProbe, mock_result) -> None:
        """Test streaming research method."""
        # Mock streaming chunks
        mock_chunks = [
            MagicMock(event_type="interaction.start", interaction=MagicMock(id=mock_result.interaction_id)),
            MagicMock(event_type="content.delta", delta=MagicMock(type="text", text="Hello ")),
            MagicMock(event_type="content.delta", delta=MagicMock(type="text", text="World")),
            MagicMock(event_type="interaction.complete"),
        ]

        mock_client = MagicMock()
        mock_client.interactions.create.return_value = iter(mock_chunks)

        with patch.object(probe, "_get_client", return_value=mock_client):
            result = probe.research_stream("test topic")
            assert "Hello World" in result.report
            assert result.interaction_id == mock_result.interaction_id


class TestDeepProbeErrorHandling:
    """Tests for error handling."""

    def test_auth_error_on_create(self, probe: DeepProbe) -> None:
        """Test that auth errors propagate correctly."""
        mock_client = MagicMock()
        mock_client.interactions.create.side_effect = Exception("Unauthorized: 401")

        with patch.object(probe, "_get_client", return_value=mock_client):
            with pytest.raises(ProbeAuthError):
                probe.research("test")

    def test_network_error_includes_interaction_id(self, probe: DeepProbe) -> None:
        """Test that network errors include interaction ID for resume."""
        mock_interaction = MagicMock()
        mock_interaction.id = "test-id"

        mock_client = MagicMock()
        mock_client.interactions.create.return_value = mock_interaction
        mock_client.interactions.get.side_effect = Exception("Connection failed")

        with patch.object(probe, "_get_client", return_value=mock_client):
            with pytest.raises(ProbeNetworkError) as exc_info:
                probe.research("test")
            assert exc_info.value.interaction_id == "test-id"


class TestDeepProbeBuildResult:
    """Tests for building research results."""

    def test_build_result_from_outputs(self, probe: DeepProbe) -> None:
        """Test building result from outputs list."""
        mock_output = MagicMock()
        mock_output.text = "Report content here"
        mock_output.thought_summary = None

        mock_interaction = MagicMock()
        mock_interaction.status = "completed"
        mock_interaction.outputs = [mock_output]

        result = probe._build_result(mock_interaction, "test-id")
        assert result.report == "Report content here"
        assert result.status == ResearchStatus.COMPLETED

    def test_build_result_with_outputs_fallback(self, probe: DeepProbe) -> None:
        """Test building result with fallback to response."""
        mock_interaction = MagicMock()
        mock_interaction.status = "completed"
        mock_interaction.outputs = []
        mock_interaction.response = MagicMock(text="Fallback content")

        result = probe._build_result(mock_interaction, "test-id")
        assert result.report == "Fallback content"

    def test_build_result_with_thought_summaries(self, probe: DeepProbe) -> None:
        """Test building result with thought summaries."""
        mock_output1 = MagicMock()
        mock_output1.text = "Report content"
        mock_output1.thought_summary = None

        mock_output2 = MagicMock()
        mock_output2.text = None
        mock_output2.thought_summary = "Thinking about the problem..."

        mock_interaction = MagicMock()
        mock_interaction.status = "completed"
        mock_interaction.outputs = [mock_output1, mock_output2]

        result = probe._build_result(mock_interaction, "test-id")
        assert result.report == "Report content"
        assert len(result.thoughts) == 1
        assert result.thoughts[0].content == "Thinking about the problem..."