"""Core DeepProbe client with sync/async support."""

import asyncio
import os
import time
from typing import Any, Callable

from dotenv import load_dotenv

from ._reconnect import ConnectionConfig, ReconnectionManager
from .exceptions import ProbeAPIError, ProbeAuthError, ProbeNetworkError, ProbeTimeoutError
from .models import Citation, ResearchResult, ResearchStatus, Thought, TokenUsage

# Load environment variables
load_dotenv()

DEEP_RESEARCH_AGENT = "deep-research-pro-preview-12-2025"


class DeepProbe:
    """Client for running deep research using Google Gemini Deep Research API.

    This client provides both synchronous and asynchronous methods for running
    deep research with automatic reconnection and structured output.

    Example:
        ```python
        from deep_probe import DeepProbe

        # Initialize
        probe = DeepProbe()

        # Run synchronous research
        result = probe.research("What is quantum computing?")
        print(result.report)

        # Run async research
        result = await probe.research_async("AI trends 2024")
        print(result.report)
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        config: ConnectionConfig | None = None,
        thinking_summaries: bool = True,
    ):
        """Initialize the DeepProbe client.

        Args:
            api_key: Google Gemini API key. If not provided, reads from
                GEMINI_API_KEY environment variable.
            config: Connection configuration. Uses defaults if not provided.
            thinking_summaries: Whether to enable thinking summaries output.

        Raises:
            ProbeAuthError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ProbeAuthError(
                "No API key provided. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.config = config or ConnectionConfig()
        self.thinking_summaries = thinking_summaries
        self._reconnect_manager = ReconnectionManager(self.config)
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create the Google GenAI client."""
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _get_agent_config(self) -> dict[str, Any]:
        """Get the agent configuration."""
        return {
            "type": "deep-research",
            "thinking_summaries": "auto" if self.thinking_summaries else "none",
        }

    def research(self, topic: str, on_thought: Callable[[str], None] | None = None) -> ResearchResult:
        """Run deep research synchronously.

        This method starts a background research task and polls until completion.

        Args:
            topic: The research topic or question.
            on_thought: Optional callback for thinking summaries.

        Returns:
            ResearchResult containing the report and metadata.

        Raises:
            ProbeAuthError: If authentication fails.
            ProbeNetworkError: If network errors occur after all retries.
            ProbeTimeoutError: If the operation times out.
        """
        client = self._get_client()

        # Start background research with retry
        interaction = self._start_research_with_retry(client, topic)
        interaction_id = self._extract_interaction_id(interaction)

        # Poll until complete
        final_interaction = self._poll_until_complete(
            client, interaction_id, on_thought
        )

        # Extract and return results
        return self._build_result(final_interaction, interaction_id)

    async def research_async(
        self,
        topic: str,
        on_thought: Callable[[str], None] | None = None,
    ) -> ResearchResult:
        """Run deep research asynchronously.

        This method runs the synchronous research in an asyncio executor.

        Args:
            topic: The research topic or question.
            on_thought: Optional callback for thinking summaries.

        Returns:
            ResearchResult containing the report and metadata.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.research(topic, on_thought),
        )

    def _start_research_with_retry(self, client: Any, topic: str) -> Any:
        """Start a new background research interaction with retry logic."""
        last_error: Exception | None = None
        rate_limit_retries = 0
        max_rate_limit_retries = 5  # More retries for rate limits

        for attempt in range(self.config.max_retries + 1):
            try:
                interaction = client.interactions.create(
                    input=topic,
                    agent=DEEP_RESEARCH_AGENT,
                    background=True,
                    agent_config=self._get_agent_config(),
                )
                self._reconnect_manager.reset_keepalive()
                return interaction
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # Auth errors should not be retried
                if "auth" in error_msg or "api key" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
                    raise ProbeAuthError(f"Authentication failed: {e}")

                # Rate limit / quota errors (429) - retry with exponential backoff
                if "429" in error_msg or "too_many_requests" in error_msg or "quota" in error_msg or "rate limit" in error_msg:
                    if rate_limit_retries < max_rate_limit_retries:
                        # Use longer delays for rate limits: 60s, 120s, 240s, 300s, 300s
                        delay = min(60 * (2 ** min(rate_limit_retries, 2)), 300)
                        rate_limit_retries += 1
                        # Log retry attempt (will be shown in CLI if verbose)
                        import warnings
                        warnings.warn(
                            f"Rate limit encountered. Retrying in {delay}s (attempt {rate_limit_retries}/{max_rate_limit_retries})...",
                            UserWarning,
                            stacklevel=2,
                        )
                        time.sleep(delay)
                        continue  # Retry the request
                    else:
                        # Max retries reached for rate limit
                        raise ProbeAPIError(
                            f"API quota exceeded or rate limit reached after {rate_limit_retries} retries: {e}",
                            status_code=429,
                            error_code="too_many_requests",
                        )

                # Check if we should retry for other errors
                if attempt < self.config.max_retries:
                    delay = self.config.base_retry_delay * (2**attempt)
                    time.sleep(delay)
                else:
                    raise ProbeNetworkError(f"Failed to start research after {attempt} retries: {e}")

        # Should not reach here
        if last_error:
            raise ProbeNetworkError(f"Failed to start research: {last_error}")
        raise ProbeNetworkError("Failed to start research")

    def _poll_until_complete(
        self,
        client: Any,
        interaction_id: str,
        on_thought: Callable[[str], None] | None = None,
    ) -> Any:
        """Poll the interaction status until complete."""
        start_time = time.time()
        last_error: Exception | None = None
        consecutive_errors = 0

        while True:
            # Check total timeout
            elapsed = time.time() - start_time
            if elapsed > self.config.total_timeout:
                raise ProbeTimeoutError(
                    f"Research timed out after {elapsed:.1f} seconds",
                    interaction_id=interaction_id,
                    elapsed_seconds=elapsed,
                )

            try:
                interaction = client.interactions.get(id=interaction_id)
                self._reconnect_manager.reset_keepalive()
                consecutive_errors = 0
                last_error = None

                # Check if complete
                status = getattr(interaction, "status", None)
                if status == "completed":
                    return interaction
                elif status == "failed":
                    error_msg = getattr(interaction, "error", "Unknown error")
                    raise ProbeAPIError(
                        f"Research failed: {error_msg}",
                        interaction_id=interaction_id,
                    )

                # Handle thought summaries callback
                if on_thought and hasattr(interaction, "outputs"):
                    for output in interaction.outputs:
                        if hasattr(output, "thought_summary"):
                            on_thought(output.thought_summary)

            except (ProbeAPIError, ProbeTimeoutError):
                # Don't retry API errors or timeouts
                raise
            except Exception as e:
                last_error = e
                consecutive_errors += 1

                if consecutive_errors > self.config.max_retries:
                    raise ProbeNetworkError(
                        f"Failed to poll research status after {consecutive_errors} errors: {e}",
                        interaction_id=interaction_id,
                    )

                # Wait before retry
                time.sleep(self.config.base_retry_delay * consecutive_errors)
                continue

            # Wait before next poll
            time.sleep(self.config.poll_interval)

    def _extract_interaction_id(self, interaction: Any) -> str:
        """Extract the interaction ID from the response."""
        if hasattr(interaction, "id"):
            return str(interaction.id)
        if hasattr(interaction, "interaction_id"):
            return str(interaction.interaction_id)
        # Fallback: try to find any ID-like attribute
        for attr in ["id", "interaction_id", "uuid", "uid"]:
            if hasattr(interaction, attr):
                return str(getattr(interaction, attr))
        raise ProbeNetworkError("Could not extract interaction ID from response")

    def _build_result(self, interaction: Any, interaction_id: str) -> ResearchResult:
        """Build a ResearchResult from the interaction response."""
        # Extract report content from outputs
        report = ""
        thoughts: list[Thought] = []

        if hasattr(interaction, "outputs") and interaction.outputs:
            # Get the last text output as the main report
            for output in interaction.outputs:
                if hasattr(output, "text") and output.text:
                    report = output.text
                # Extract thought summaries (must be a string)
                thought_summary = getattr(output, "thought_summary", None)
                if thought_summary and isinstance(thought_summary, str):
                    thoughts.append(
                        Thought(
                            content=thought_summary,
                            phase="thinking",
                        )
                    )

        # Fallback: try other common patterns
        if not report:
            if hasattr(interaction, "response"):
                response = interaction.response
                if hasattr(response, "text"):
                    report = response.text
                elif hasattr(response, "content"):
                    report = response.content
                elif isinstance(response, str):
                    report = response

        # Extract sources/citations
        sources: list[Citation] = []
        if hasattr(interaction, "citations"):
            for cite in interaction.citations:
                sources.append(
                    Citation(
                        url=getattr(cite, "url", ""),
                        title=getattr(cite, "title", None),
                        snippet=getattr(cite, "snippet", None),
                    )
                )

        # Extract token usage
        usage = TokenUsage()
        if hasattr(interaction, "usage_metadata"):
            meta = interaction.usage_metadata
            usage = TokenUsage(
                input_tokens=getattr(meta, "prompt_token_count", 0)
                or getattr(meta, "input_tokens", 0)
                or 0,
                output_tokens=getattr(meta, "candidates_token_count", 0)
                or getattr(meta, "output_tokens", 0)
                or 0,
                total_tokens=getattr(meta, "total_token_count", 0)
                or getattr(meta, "total_tokens", 0)
                or 0,
            )

        # Determine status
        status = ResearchStatus.COMPLETED
        if hasattr(interaction, "status"):
            status_map = {
                "completed": ResearchStatus.COMPLETED,
                "failed": ResearchStatus.FAILED,
                "cancelled": ResearchStatus.CANCELLED,
                "in_progress": ResearchStatus.RUNNING,
                "running": ResearchStatus.RUNNING,
                "pending": ResearchStatus.PENDING,
            }
            status = status_map.get(str(interaction.status).lower(), ResearchStatus.COMPLETED)

        return ResearchResult(
            report=report,
            sources=sources,
            thoughts=thoughts,
            cost_usage=usage,
            interaction_id=interaction_id,
            status=status,
        )

    def resume(self, interaction_id: str) -> ResearchResult:
        """Resume a previous research operation synchronously.

        Args:
            interaction_id: The ID of a previously started research interaction.

        Returns:
            ResearchResult containing the report and metadata.

        Raises:
            ProbeAuthError: If authentication fails.
            ProbeNetworkError: If network errors occur after all retries.
            ProbeTimeoutError: If the operation times out.
        """
        client = self._get_client()

        # Poll until complete
        final_interaction = self._poll_until_complete(client, interaction_id)

        return self._build_result(final_interaction, interaction_id)

    async def resume_async(self, interaction_id: str) -> ResearchResult:
        """Resume a previous research operation asynchronously.

        Args:
            interaction_id: The ID of a previously started research interaction.

        Returns:
            ResearchResult containing the report and metadata.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.resume(interaction_id),
        )

    def research_stream(
        self,
        topic: str,
        on_text: Callable[[str], None] | None = None,
        on_thought: Callable[[str], None] | None = None,
    ) -> ResearchResult:
        """Run deep research with streaming output.

        This method streams the research output in real-time.

        Args:
            topic: The research topic or question.
            on_text: Callback for text chunks.
            on_thought: Callback for thinking summaries.

        Returns:
            ResearchResult containing the report and metadata.
        """
        client = self._get_client()

        # Start streaming research
        interaction_id: str | None = None
        last_event_id: str | None = None
        is_complete = False
        report_parts: list[str] = []
        thoughts: list[Thought] = []

        def process_stream(stream: Any) -> None:
            nonlocal interaction_id, last_event_id, is_complete, report_parts, thoughts

            try:
                for chunk in stream:
                    # Track event ID for reconnection
                    if hasattr(chunk, "event_id"):
                        last_event_id = chunk.event_id

                    # Handle interaction start
                    if hasattr(chunk, "event_type"):
                        if chunk.event_type == "interaction.start":
                            if hasattr(chunk, "interaction") and hasattr(chunk.interaction, "id"):
                                interaction_id = str(chunk.interaction.id)

                        # Handle content delta
                        elif chunk.event_type == "content.delta":
                            if hasattr(chunk, "delta"):
                                delta = chunk.delta
                                if hasattr(delta, "type"):
                                    if delta.type == "text" and hasattr(delta, "text"):
                                        text = delta.text
                                        report_parts.append(text)
                                        if on_text:
                                            on_text(text)
                                    elif delta.type == "thought_summary":
                                        if hasattr(delta, "content") and hasattr(delta.content, "text"):
                                            thought_text = delta.content.text
                                            thoughts.append(Thought(content=thought_text, phase="thinking"))
                                            if on_thought:
                                                on_thought(thought_text)

                        # Handle completion
                        elif chunk.event_type == "interaction.complete":
                            is_complete = True

                        # Handle error
                        elif chunk.event_type == "error":
                            is_complete = True
                            if hasattr(chunk, "error"):
                                raise ProbeAPIError(
                                    f"Research error: {chunk.error}",
                                    interaction_id=interaction_id,
                                )
            except (ConnectionError, IOError, OSError) as e:
                # Network error during streaming - will be handled by reconnection loop
                error_msg = str(e).lower()
                if "connection" in error_msg or "closed" in error_msg or "chunked" in error_msg:
                    # This is expected - the reconnection loop will handle it
                    return
                raise

        # Initial streaming request with retry
        for attempt in range(self.config.max_retries + 1):
            try:
                stream = client.interactions.create(
                    input=topic,
                    agent=DEEP_RESEARCH_AGENT,
                    background=True,
                    stream=True,
                    agent_config=self._get_agent_config(),
                )
                process_stream(stream)
                # If we get here and not complete, connection was closed
                if not is_complete and interaction_id:
                    break  # Will enter reconnection loop
                elif is_complete:
                    break  # Successfully completed
            except (ProbeAPIError, ProbeAuthError):
                raise
            except (ConnectionError, IOError, OSError) as e:
                # Network error - try reconnection if we have interaction_id
                if interaction_id:
                    break  # Enter reconnection loop
                if attempt >= self.config.max_retries:
                    raise ProbeNetworkError(
                        f"Failed to start streaming research: {e}",
                        interaction_id=interaction_id,
                    )
                time.sleep(self.config.base_retry_delay * (2**attempt))
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a connection-related error
                if "connection" in error_msg or "closed" in error_msg or "chunked" in error_msg:
                    if interaction_id:
                        break  # Enter reconnection loop
                if attempt >= self.config.max_retries:
                    raise ProbeNetworkError(
                        f"Failed to start streaming research: {e}",
                        interaction_id=interaction_id,
                    )
                time.sleep(self.config.base_retry_delay * (2**attempt))

        # Reconnection loop if not complete
        retry_count = 0
        max_reconnect_attempts = self.config.max_retries * 2  # Allow more attempts for reconnection
        
        while not is_complete and interaction_id:
            if retry_count >= max_reconnect_attempts:
                # Fallback: try polling mode to get final result
                try:
                    final_interaction = client.interactions.get(id=interaction_id)
                    if hasattr(final_interaction, "status") and final_interaction.status == "completed":
                        # Build result from final interaction
                        return self._build_result(final_interaction, interaction_id)
                except Exception:
                    pass
                
                raise ProbeNetworkError(
                    f"Max reconnection attempts reached. Interaction ID: {interaction_id}",
                    interaction_id=interaction_id,
                )

            if retry_count > 0:
                # Wait before reconnecting (exponential backoff)
                wait_time = min(self.config.base_retry_delay * (2 ** min(retry_count, 3)), 30)
                time.sleep(wait_time)

            try:
                resume_stream = client.interactions.get(
                    id=interaction_id,
                    stream=True,
                    last_event_id=last_event_id,
                )
                process_stream(resume_stream)
                retry_count = 0  # Reset on success
                if is_complete:
                    break
            except (ConnectionError, IOError, OSError) as e:
                retry_count += 1
                # Continue retrying for connection errors
                continue
            except Exception as e:
                retry_count += 1
                error_msg = str(e).lower()
                if "connection" in error_msg or "closed" in error_msg:
                    # Connection error - continue retrying
                    continue
                if retry_count >= max_reconnect_attempts:
                    raise ProbeNetworkError(
                        f"Reconnection failed: {e}",
                        interaction_id=interaction_id,
                    )

        # Build and return result
        return ResearchResult(
            report="".join(report_parts),
            sources=[],  # Sources not available in streaming mode
            thoughts=thoughts,
            cost_usage=TokenUsage(),  # Usage not available in streaming mode
            interaction_id=interaction_id or "unknown",
            status=ResearchStatus.COMPLETED,
        )