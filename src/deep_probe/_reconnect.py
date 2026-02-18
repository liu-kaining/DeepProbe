"""Auto-reconnection and timeout management for DeepProbe."""

import time
from dataclasses import dataclass


@dataclass
class ConnectionConfig:
    """Configuration for connection management.

    Attributes:
        max_retries: Maximum number of retry attempts for network errors.
        keepalive_timeout: Seconds without activity before refreshing connection.
        poll_interval: Seconds between status polls.
        base_retry_delay: Base delay in seconds for exponential backoff.
        max_retry_delay: Maximum delay in seconds between retries.
        request_timeout: Maximum time in seconds for a single request.
        total_timeout: Maximum total time in seconds for the entire operation.
    """

    max_retries: int = 3
    keepalive_timeout: float = 120.0  # 2 minutes
    poll_interval: float = 10.0
    base_retry_delay: float = 2.0
    max_retry_delay: float = 60.0
    request_timeout: float = 30.0
    total_timeout: float = 1800.0  # 30 minutes (matches Google's 60-min max)


class ReconnectionManager:
    """Manages connection state for retry logic.

    This class handles:
    - Tracking last activity time for keepalive
    - Tracking retry count
    """

    def __init__(self, config: ConnectionConfig | None = None):
        """Initialize the reconnection manager.

        Args:
            config: Connection configuration. Uses defaults if not provided.
        """
        self.config = config or ConnectionConfig()
        self._last_activity: float = time.time()
        self._retry_count = 0

    def check_keepalive(self) -> bool:
        """Check if connection needs refresh due to inactivity.

        Returns:
            True if keepalive timeout has been exceeded.
        """
        inactive_time = time.time() - self._last_activity
        return inactive_time > self.config.keepalive_timeout

    def reset_keepalive(self) -> None:
        """Reset the keepalive timer."""
        self._last_activity = time.time()

    @property
    def retry_count(self) -> int:
        """Get the current retry count."""
        return self._retry_count

    @retry_count.setter
    def retry_count(self, value: int) -> None:
        """Set the retry count."""
        self._retry_count = value