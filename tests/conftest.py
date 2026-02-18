"""Pytest fixtures for DeepProbe tests."""

import pytest

from deep_probe import DeepProbe
from deep_probe.models import Citation, ResearchResult, ResearchStatus, TokenUsage


@pytest.fixture
def mock_api_key() -> str:
    """Return a mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def mock_citation() -> Citation:
    """Return a mock citation."""
    return Citation(
        url="https://example.com/article",
        title="Example Article",
        snippet="This is an example snippet.",
    )


@pytest.fixture
def mock_result() -> ResearchResult:
    """Return a mock research result."""
    return ResearchResult(
        report="# Test Report\n\nThis is a test research report.",
        sources=[
            Citation(url="https://example.com/1", title="Source 1"),
            Citation(url="https://example.com/2", title="Source 2"),
        ],
        interaction_id="test-interaction-123",
        status=ResearchStatus.COMPLETED,
        cost_usage=TokenUsage(input_tokens=100, output_tokens=200, total_tokens=300),
    )


@pytest.fixture
def probe(mock_api_key: str) -> DeepProbe:
    """Return a DeepProbe instance with a mock API key."""
    return DeepProbe(api_key=mock_api_key)