"""Utility functions for DeepProbe library."""

import re
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ResearchResult


def save_report(result: "ResearchResult", filepath: str) -> None:
    """Save a research result to a markdown file.

    Args:
        result: The ResearchResult to save.
        filepath: Path to save the file to.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        # Write header with metadata
        f.write(f"# Research Report\n\n")
        f.write(f"**Interaction ID:** `{result.interaction_id}`\n\n")
        f.write(f"**Status:** {result.status.value}\n\n")
        f.write(f"**Created:** {result.created_at.isoformat()}\n\n")
        if result.completed_at:
            f.write(f"**Completed:** {result.completed_at.isoformat()}\n\n")
        f.write(f"**Tokens:** {result.cost_usage.total_tokens} ")
        f.write(f"(input: {result.cost_usage.input_tokens}, output: {result.cost_usage.output_tokens})\n\n")
        f.write("---\n\n")

        # Write main report
        f.write(result.report)
        f.write("\n\n")

        # Write sources if available
        if result.sources:
            f.write("## Sources\n\n")
            for i, source in enumerate(result.sources, 1):
                f.write(f"{i}. [{source.title or source.url}]({source.url})")
                if source.snippet:
                    f.write(f"\n   > {source.snippet}")
                f.write("\n")
            f.write("\n")


def extract_headings(markdown: str, max_level: int = 3) -> list[dict[str, str | int]]:
    """Extract headings from markdown content.

    Args:
        markdown: Markdown content to parse.
        max_level: Maximum heading level to extract (1-6).

    Returns:
        List of dicts with 'level', 'text', and 'id' keys.
    """
    headings = []
    pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    for match in pattern.finditer(markdown):
        level = len(match.group(1))
        if level <= max_level:
            text = match.group(2).strip()
            # Generate an ID for the heading
            heading_id = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            headings.append(
                {
                    "level": level,
                    "text": text,
                    "id": heading_id,
                }
            )

    return headings


def extract_links(markdown: str) -> list[dict[str, str]]:
    """Extract all links from markdown content.

    Args:
        markdown: Markdown content to parse.

    Returns:
        List of dicts with 'text' and 'url' keys.
    """
    links = []
    # Match [text](url) format
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for match in pattern.finditer(markdown):
        links.append(
            {
                "text": match.group(1),
                "url": match.group(2),
            }
        )

    return links


def format_interaction_id(interaction_id: str, max_length: int = 12) -> str:
    """Format an interaction ID for display (truncate if needed).

    Args:
        interaction_id: Full interaction ID.
        max_length: Maximum length for display.

    Returns:
        Truncated interaction ID with ellipsis if needed.
    """
    if len(interaction_id) <= max_length:
        return interaction_id
    return f"{interaction_id[:max_length]}..."


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Human-readable duration string.
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def estimate_read_time(text: str, words_per_minute: int = 200) -> int:
    """Estimate reading time for text.

    Args:
        text: Text to estimate reading time for.
        words_per_minute: Average reading speed.

    Returns:
        Estimated reading time in minutes.
    """
    word_count = len(text.split())
    return max(1, word_count // words_per_minute)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length.
        suffix: Suffix to add when truncated.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix