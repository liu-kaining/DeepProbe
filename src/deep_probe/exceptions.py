"""Custom exceptions for DeepProbe library."""


class DeepProbeError(Exception):
    """Base exception for all DeepProbe errors."""

    def __init__(self, message: str, interaction_id: str | None = None):
        super().__init__(message)
        self.message = message
        self.interaction_id = interaction_id

    def __str__(self) -> str:
        if self.interaction_id:
            return f"{self.message} (interaction_id: {self.interaction_id})"
        return self.message


class ProbeAuthError(DeepProbeError):
    """Raised when there are API key authentication issues.

    This error should not be retried - the user needs to fix their API key.
    """

    pass


class ProbeNetworkError(DeepProbeError):
    """Raised when there are network connection failures.

    This error includes the interaction_id to allow resuming the research.
    """

    def __init__(
        self,
        message: str,
        interaction_id: str | None = None,
        retry_count: int = 0,
    ):
        super().__init__(message, interaction_id)
        self.retry_count = retry_count


class ProbeTimeoutError(DeepProbeError):
    """Raised when a time limit is exceeded during research."""

    def __init__(
        self,
        message: str,
        interaction_id: str | None = None,
        elapsed_seconds: float | None = None,
    ):
        super().__init__(message, interaction_id)
        self.elapsed_seconds = elapsed_seconds


class ProbeAPIError(DeepProbeError):
    """Raised when there are server-side API errors.

    This includes rate limits, server errors, and other API-level issues.
    """

    def __init__(
        self,
        message: str,
        interaction_id: str | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
    ):
        super().__init__(message, interaction_id)
        self.status_code = status_code
        self.error_code = error_code


class ProbeCancelledError(DeepProbeError):
    """Raised when the user cancels the research operation."""

    def __init__(
        self,
        message: str = "Research was cancelled by the user",
        interaction_id: str | None = None,
        partial_result: str | None = None,
    ):
        super().__init__(message, interaction_id)
        self.partial_result = partial_result