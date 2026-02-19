"""Deep Probe - Research anything, deeply, in one line of code.

A Python library that wraps Google Gemini Deep Research API with automatic
reconnection and structured output.

Example:
    ```python
    from deep_probe import DeepProbe, ResearchResult

    # Initialize client
    probe = DeepProbe()

    # Run deep research
    result = probe.research("What is quantum computing?")
    print(result.report)

    # Save result
    result.save("report.md")
    ```

For CLI usage:
    ```bash
    deep-probe research "What is quantum computing?"
    deep-probe research "AI trends" --save report.md
    deep-probe research --resume "interaction-id"
    ```
"""

from .core import DeepProbe
from .exceptions import (
    DeepProbeError,
    ProbeAPIError,
    ProbeAuthError,
    ProbeCancelledError,
    ProbeNetworkError,
    ProbeTimeoutError,
)
from .models import (
    Citation,
    ResearchEvent,
    ResearchResult,
    ResearchStatus,
    Thought,
    TokenUsage,
)

__version__ = "0.1.2"

__all__ = [
    # Core
    "DeepProbe",
    # Models
    "ResearchResult",
    "ResearchStatus",
    "ResearchEvent",
    "Citation",
    "Thought",
    "TokenUsage",
    # Exceptions
    "DeepProbeError",
    "ProbeAuthError",
    "ProbeNetworkError",
    "ProbeTimeoutError",
    "ProbeAPIError",
    "ProbeCancelledError",
    # Version
    "__version__",
]