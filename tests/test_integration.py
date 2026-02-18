"""Integration tests for DeepProbe - includes actual API calls."""

import os
import sys
import time
import tempfile

# Add src to path for standalone execution
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
from deep_probe import DeepProbe
from deep_probe.exceptions import ProbeAuthError, ProbeNetworkError, ProbeTimeoutError
from deep_probe.models import Citation, Thought, TokenUsage, ResearchResult, ResearchStatus


class TestImports:
    """Test all module imports."""

    def test_core_imports(self):
        """Test core module imports."""
        from deep_probe import DeepProbe, ResearchResult, ResearchStatus
        assert DeepProbe is not None
        assert ResearchResult is not None
        assert ResearchStatus is not None

    def test_model_imports(self):
        """Test model imports."""
        from deep_probe.models import Citation, Thought, TokenUsage
        assert Citation is not None
        assert Thought is not None
        assert TokenUsage is not None

    def test_exception_imports(self):
        """Test exception imports."""
        from deep_probe.exceptions import (
            DeepProbeError,
            ProbeAuthError,
            ProbeNetworkError,
            ProbeTimeoutError,
            ProbeAPIError,
            ProbeCancelledError,
        )
        assert all(cls is not None for cls in [
            DeepProbeError, ProbeAuthError, ProbeNetworkError,
            ProbeTimeoutError, ProbeAPIError, ProbeCancelledError
        ])


class TestModels:
    """Test data models."""

    def test_citation_model(self):
        """Test Citation model."""
        citation = Citation(
            url="https://example.com",
            title="Example",
            snippet="A snippet",
        )
        assert citation.url == "https://example.com"
        assert citation.title == "Example"
        assert citation.snippet == "A snippet"

    def test_thought_model(self):
        """Test Thought model."""
        thought = Thought(content="Test thought", phase="testing")
        assert thought.content == "Test thought"
        assert thought.phase == "testing"
        assert thought.timestamp is not None

    def test_token_usage_model(self):
        """Test TokenUsage model."""
        usage = TokenUsage(input_tokens=100, output_tokens=200, total_tokens=300)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 200
        assert usage.total_tokens == 300

    def test_research_result_model(self):
        """Test ResearchResult model."""
        result = ResearchResult(
            report="# Test Report\n\nContent here.",
            interaction_id="test-123",
            status=ResearchStatus.COMPLETED,
        )
        assert result.interaction_id == "test-123"
        assert result.status == ResearchStatus.COMPLETED
        assert result.report == "# Test Report\n\nContent here."

    def test_research_result_save(self):
        """Test saving research result."""
        result = ResearchResult(
            report="# Test Report\n\nContent here.",
            interaction_id="test-123",
            status=ResearchStatus.COMPLETED,
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            test_file = f.name
        
        try:
            result.save(test_file)
            assert os.path.exists(test_file)
            
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Test Report" in content
                assert "test-123" in content
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


class TestExceptions:
    """Test exception classes."""

    def test_probe_auth_error(self):
        """Test ProbeAuthError."""
        error = ProbeAuthError("Test auth error")
        assert "auth" in str(error).lower() or "Test auth error" in str(error)

    def test_probe_network_error(self):
        """Test ProbeNetworkError with interaction_id."""
        error = ProbeNetworkError("Test network error", interaction_id="test-id")
        assert error.interaction_id == "test-id"
        assert "test-id" in str(error)

    def test_probe_timeout_error(self):
        """Test ProbeTimeoutError."""
        error = ProbeTimeoutError("Test timeout", elapsed_seconds=60.0)
        assert error.elapsed_seconds == 60.0


class TestDeepProbeInitialization:
    """Test DeepProbe initialization."""

    def test_init_with_api_key_from_env(self, monkeypatch):
        """Test initialization with API key from environment."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
        probe = DeepProbe()
        assert probe.api_key == "test-key-123"

    def test_init_with_explicit_api_key(self):
        """Test initialization with explicit API key."""
        probe = DeepProbe(api_key="explicit-key")
        assert probe.api_key == "explicit-key"

    def test_init_no_api_key(self, monkeypatch):
        """Test initialization fails without API key."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(ProbeAuthError):
            DeepProbe()

    def test_init_with_thinking_summaries(self):
        """Test initialization with thinking_summaries option."""
        probe = DeepProbe(api_key="test-key", thinking_summaries=False)
        assert probe.thinking_summaries is False

    def test_config_defaults(self):
        """Test default configuration."""
        probe = DeepProbe(api_key="test-key")
        assert probe.config is not None
        assert probe.config.max_retries >= 0
        assert probe.config.total_timeout > 0


class TestGoogleGenAIClient:
    """Test Google GenAI client creation (requires API key)."""

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set"
    )
    def test_client_creation(self):
        """Test Google GenAI client can be created."""
        probe = DeepProbe()
        client = probe._get_client()
        assert client is not None

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set"
    )
    def test_agent_config(self):
        """Test agent configuration."""
        probe = DeepProbe()
        config = probe._get_agent_config()
        assert config["type"] == "deep-research"
        assert config["thinking_summaries"] in ["auto", "none"]


class TestAPIConnection:
    """Test actual API connection (requires API key and network)."""

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set"
    )
    def test_api_connection(self):
        """Test basic API connection."""
        probe = DeepProbe()
        client = probe._get_client()
        
        # Try to start a research in background mode
        interaction = client.interactions.create(
            input="Test connection",
            agent="deep-research-pro-preview-12-2025",
            background=True,
            agent_config=probe._get_agent_config(),
        )
        
        interaction_id = probe._extract_interaction_id(interaction)
        assert interaction_id is not None
        assert len(interaction_id) > 0


class TestResearchFlow:
    """Test complete research flow (requires API key and may take time)."""

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set"
    )
    @pytest.mark.slow
    def test_research_complete(self):
        """Test complete research flow (may take several minutes)."""
        probe = DeepProbe()
        
        # Use a simple topic
        topic = "What is artificial intelligence?"
        
        thoughts_received = []
        
        def on_thought(thought: str):
            thoughts_received.append(thought)
        
        # Start research
        result = probe.research(topic, on_thought=on_thought)
        
        # Verify result
        assert result is not None
        assert result.interaction_id is not None
        assert result.status == ResearchStatus.COMPLETED
        assert len(result.report) > 0
        
        # Verify save works
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            test_file = f.name
        
        try:
            result.save(test_file)
            assert os.path.exists(test_file)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


class TestUtilities:
    """Test utility functions."""

    def test_format_interaction_id(self):
        """Test format_interaction_id utility."""
        from deep_probe.utils import format_interaction_id
        
        short_id = format_interaction_id("short")
        assert short_id == "short"
        
        long_id = format_interaction_id("a" * 100, max_length=10)
        assert len(long_id) <= 13  # 10 + "..."
        assert long_id.endswith("...")

    def test_format_duration(self):
        """Test format_duration utility."""
        from deep_probe.utils import format_duration
        
        assert "s" in format_duration(30)
        assert "m" in format_duration(90)
        assert "h" in format_duration(3600)

    def test_estimate_read_time(self):
        """Test estimate_read_time utility."""
        from deep_probe.utils import estimate_read_time
        
        read_time = estimate_read_time("word " * 200)
        assert read_time >= 1


if __name__ == "__main__":
    """Allow running as standalone script."""
    print("=" * 60)
    print("DeepProbe Integration Tests")
    print("=" * 60)
    print("\nRunning integration tests...")
    print("Note: Some tests require GEMINI_API_KEY environment variable")
    print("      and may make actual API calls.\n")
    
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
