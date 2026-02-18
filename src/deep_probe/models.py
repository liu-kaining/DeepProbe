"""Pydantic data models for DeepProbe library."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResearchStatus(str, Enum):
    """Status of a research operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Citation(BaseModel):
    """A citation/reference from the research."""

    url: str = Field(..., description="URL of the source")
    title: str | None = Field(None, description="Title of the source")
    snippet: str | None = Field(None, description="Brief snippet from the source")


class Thought(BaseModel):
    """A thought/step in the research process."""

    timestamp: datetime = Field(default_factory=datetime.now, description="When this thought occurred")
    content: str = Field(..., description="The thought content")
    phase: str | None = Field(None, description="Research phase (e.g., 'planning', 'searching', 'synthesizing')")


class TokenUsage(BaseModel):
    """Token usage statistics."""

    input_tokens: int = Field(default=0, description="Number of input tokens used")
    output_tokens: int = Field(default=0, description="Number of output tokens generated")
    total_tokens: int = Field(default=0, description="Total tokens used")


class ResearchEvent(BaseModel):
    """An event during the research process."""

    event_type: str = Field(..., description="Type of event (e.g., 'thought', 'search', 'citation')")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the event occurred")
    data: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")


class ResearchResult(BaseModel):
    """Result of a deep research operation."""

    report: str = Field(..., description="The final research report in markdown format")
    sources: list[Citation] = Field(default_factory=list, description="List of sources cited")
    thoughts: list[Thought] = Field(default_factory=list, description="Research thoughts/process")
    cost_usage: TokenUsage = Field(default_factory=TokenUsage, description="Token usage statistics")
    interaction_id: str = Field(..., description="Unique identifier for this research interaction")
    status: ResearchStatus = Field(default=ResearchStatus.COMPLETED, description="Final status")
    created_at: datetime = Field(default_factory=datetime.now, description="When the research was created")
    completed_at: datetime | None = Field(None, description="When the research completed")

    def save(self, filepath: str) -> None:
        """Save the research result to a file.

        Args:
            filepath: Path to save the report to.
        """
        from .utils import save_report

        save_report(self, filepath)