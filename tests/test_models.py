"""Tests for Pydantic data models."""

import pytest
from datetime import datetime

from deep_probe.models import (
    Citation,
    Thought,
    TokenUsage,
    ResearchEvent,
    ResearchResult,
    ResearchStatus,
)


class TestCitation:
    """Tests for Citation model."""

    def test_citation_creation(self) -> None:
        """Test creating a citation."""
        citation = Citation(
            url="https://example.com",
            title="Example",
            snippet="A snippet",
        )
        assert citation.url == "https://example.com"
        assert citation.title == "Example"
        assert citation.snippet == "A snippet"

    def test_citation_minimal(self) -> None:
        """Test creating a citation with only required fields."""
        citation = Citation(url="https://example.com")
        assert citation.url == "https://example.com"
        assert citation.title is None
        assert citation.snippet is None


class TestThought:
    """Tests for Thought model."""

    def test_thought_creation(self) -> None:
        """Test creating a thought."""
        thought = Thought(
            content="Thinking about X",
            phase="planning",
        )
        assert thought.content == "Thinking about X"
        assert thought.phase == "planning"
        assert isinstance(thought.timestamp, datetime)

    def test_thought_auto_timestamp(self) -> None:
        """Test that timestamp is auto-generated."""
        before = datetime.now()
        thought = Thought(content="Test")
        after = datetime.now()
        assert before <= thought.timestamp <= after


class TestTokenUsage:
    """Tests for TokenUsage model."""

    def test_token_usage_defaults(self) -> None:
        """Test default token usage values."""
        usage = TokenUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0

    def test_token_usage_creation(self) -> None:
        """Test creating token usage with values."""
        usage = TokenUsage(input_tokens=100, output_tokens=200, total_tokens=300)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 200
        assert usage.total_tokens == 300


class TestResearchEvent:
    """Tests for ResearchEvent model."""

    def test_event_creation(self) -> None:
        """Test creating a research event."""
        event = ResearchEvent(
            event_type="search",
            data={"query": "test"},
        )
        assert event.event_type == "search"
        assert event.data == {"query": "test"}
        assert isinstance(event.timestamp, datetime)


class TestResearchResult:
    """Tests for ResearchResult model."""

    def test_result_creation(self, mock_citation: Citation) -> None:
        """Test creating a research result."""
        result = ResearchResult(
            report="# Report",
            sources=[mock_citation],
            interaction_id="test-123",
            status=ResearchStatus.COMPLETED,
        )
        assert result.report == "# Report"
        assert len(result.sources) == 1
        assert result.interaction_id == "test-123"
        assert result.status == ResearchStatus.COMPLETED

    def test_result_defaults(self) -> None:
        """Test default values for research result."""
        result = ResearchResult(
            report="Test",
            interaction_id="test-123",
        )
        assert result.sources == []
        assert result.thoughts == []
        assert result.cost_usage.total_tokens == 0
        assert result.status == ResearchStatus.COMPLETED
        assert result.completed_at is None


class TestResearchStatus:
    """Tests for ResearchStatus enum."""

    def test_status_values(self) -> None:
        """Test that all expected statuses exist."""
        assert ResearchStatus.PENDING.value == "pending"
        assert ResearchStatus.RUNNING.value == "running"
        assert ResearchStatus.COMPLETED.value == "completed"
        assert ResearchStatus.FAILED.value == "failed"
        assert ResearchStatus.CANCELLED.value == "cancelled"

    def test_status_string_comparison(self) -> None:
        """Test comparing status to string."""
        assert ResearchStatus.COMPLETED == "completed"
        assert ResearchStatus.FAILED != "completed"