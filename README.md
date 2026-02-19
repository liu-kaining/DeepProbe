# Deep Probe

> Research anything, deeply, in one line of code.

A Python library that wraps Google Gemini Deep Research API with automatic reconnection and structured output.

<img width="1024" height="549" alt="image" src="https://github.com/user-attachments/assets/e3045be1-20c1-406b-a916-8c3fb3c11d67" />


## Features

- **Simple API**: One line of code to run deep research
- **Auto-reconnection**: Handles network failures with exponential backoff
- **Structured output**: Pydantic models for type-safe results
- **Sync & Async**: Both synchronous and asynchronous interfaces
- **Streaming**: Real-time output with thought summaries
- **CLI tool**: Rich-powered command-line interface
- **Resume support**: Resume interrupted research operations

## Installation

```bash
pip install deep-probe
```

## Quick Start

### Python API

```python
from deep_probe import DeepProbe

# Initialize (uses GEMINI_API_KEY environment variable)
probe = DeepProbe()

# Run research
result = probe.research("What is quantum computing?")

# Access the report
print(result.report)

# Save to file
result.save("report.md")
```

### Async API

```python
import asyncio
from deep_probe import DeepProbe

async def main():
    probe = DeepProbe()
    result = await probe.research_async("AI trends 2024")
    print(result.report)

asyncio.run(main())
```

### Streaming API

```python
from deep_probe import DeepProbe

probe = DeepProbe()

def on_text(text: str):
    print(text, end="", flush=True)

def on_thought(thought: str):
    print(f"\n💭 {thought}\n")

result = probe.research_stream(
    "What is the future of AI?",
    on_text=on_text,
    on_thought=on_thought,
)
```

### CLI
<img width="1014" height="548" alt="image" src="https://github.com/user-attachments/assets/5d2f02f3-5d9e-4afe-8d2f-79168b68bb99" />

The CLI uses a `research` subcommand. Examples:

```bash
# Basic usage
deep-probe research "What is quantum computing?"

# Long prompt from file (e.g. -i prompt.txt)
deep-probe research -i prompt.txt --save report.md --stream --verbose

# Save to file
deep-probe research "AI trends 2024" --save report.md

# Show thinking process
deep-probe research "Climate change effects" --verbose

# Stream output in real-time
deep-probe research "Research topic" --stream

# Quiet mode (only output report)
deep-probe research "Test topic" --quiet

# Resume previous research
deep-probe research --resume "interaction-id-here"
```

## Configuration

Set your Google Gemini API key:

```bash
export GEMINI_API_KEY='your-api-key'
```

Or create a `.env` file:

```
GEMINI_API_KEY=your-api-key
```

Get your API key from [Google AI Studio](https://aistudio.google.com/apikey).

## API Reference

### DeepProbe

Main client for running deep research.

```python
from deep_probe import DeepProbe, ResearchResult

# Initialize with optional settings
probe = DeepProbe(
    api_key="optional-api-key",  # Or use GEMINI_API_KEY env var
    thinking_summaries=True,      # Enable thinking summaries output
)

# Synchronous research
result: ResearchResult = probe.research("topic")

# Asynchronous research
result: ResearchResult = await probe.research_async("topic")

# Streaming research with callbacks
result: ResearchResult = probe.research_stream(
    "topic",
    on_text=lambda text: print(text, end=""),
    on_thought=lambda thought: print(f"💭 {thought}"),
)

# Resume previous research
result: ResearchResult = probe.resume("interaction-id")
result: ResearchResult = await probe.resume_async("interaction-id")
```

### ResearchResult

```python
result.report          # str - The research report in markdown
result.sources         # list[Citation] - Sources cited
result.thoughts        # list[Thought] - Research process/thinking summaries
result.cost_usage      # TokenUsage - Token statistics
result.interaction_id  # str - Unique identifier for resume
result.status          # ResearchStatus - Final status

result.save("file.md")  # Save to file
```

### Exceptions

```python
from deep_probe.exceptions import (
    DeepProbeError,      # Base exception
    ProbeAuthError,      # API key issues
    ProbeNetworkError,   # Connection failures (includes interaction_id)
    ProbeTimeoutError,   # Time limit exceeded
    ProbeAPIError,       # Server-side errors
    ProbeCancelledError, # User cancellation
)
```

## Auto-Reconnection

DeepProbe handles network failures automatically:

| Scenario | Action | Max Retries | Delay |
|----------|--------|-------------|-------|
| Network disconnect | Auto-reconnect | 3 | 2s → 4s → 8s |
| API rate limit | Wait and retry | 3 | 60s |
| Auth error | No retry | 0 | N/A |

All network errors include `interaction_id` for resuming interrupted research.

## Google Gemini Deep Research

This library uses the `deep-research-pro-preview-12-2025` agent from Google's Gemini API. Key characteristics:

- **Max duration**: 60 minutes per research task
- **Sources**: Uses Google Search and URL context tools
- **Pricing**: ~$2-5 per task (estimates from Google)
- **Output**: Markdown-formatted research reports

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy src/
```

## License

Apache License 2.0

## Links

- **GitHub**: https://github.com/liu-kaining/DeepProbe
- **Author**: liukaining
