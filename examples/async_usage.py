"""Async and streaming usage examples for DeepProbe."""

import asyncio

from deep_probe import DeepProbe, ProbeNetworkError


async def main() -> None:
    """Basic async research example."""
    # Initialize the client
    probe = DeepProbe()

    # Run deep research asynchronously
    print("Starting research...")
    try:
        result = await probe.research_async("What are the latest developments in AI agent frameworks?")

        # Print the report
        print("\n" + "=" * 60)
        print("RESEARCH REPORT")
        print("=" * 60)
        print(result.report)
        print()

        # Print metadata
        print(f"Interaction ID: {result.interaction_id}")
        print(f"Status: {result.status.value}")
        print(f"Tokens used: {result.cost_usage.total_tokens}")

        # Save to file
        result.save("ai_agents_report.md")
        print("\nReport saved to ai_agents_report.md")

    except ProbeNetworkError as e:
        print(f"Network error: {e}")
        if e.interaction_id:
            print(f"You can resume with: probe.resume('{e.interaction_id}')")


def streaming_example() -> None:
    """Streaming research example with real-time output."""
    probe = DeepProbe()

    print("Starting streaming research...\n")

    def on_text(text: str) -> None:
        """Callback for text chunks."""
        print(text, end="", flush=True)

    def on_thought(thought: str) -> None:
        """Callback for thinking summaries."""
        print(f"\n💭 [Thinking] {thought}\n")

    result = probe.research_stream(
        "What is the future of AI?",
        on_text=on_text,
        on_thought=on_thought,
    )

    print(f"\n\nInteraction ID: {result.interaction_id}")
    print(f"Total thoughts: {len(result.thoughts)}")


async def run_multiple_researches() -> None:
    """Run multiple research queries concurrently."""
    probe = DeepProbe()

    topics = [
        "What is retrieval-augmented generation (RAG)?",
        "What are the benefits of vector databases?",
        "How do large language models handle reasoning?",
    ]

    print("Running multiple research queries concurrently...")

    # Run all research queries concurrently
    tasks = [probe.research_async(topic) for topic in topics]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for topic, result in zip(topics, results):
        if isinstance(result, Exception):
            print(f"Failed: {topic} - {result}")
        else:
            print(f"\nCompleted: {topic}")
            print(f"  ID: {result.interaction_id}")
            print(f"  Tokens: {result.cost_usage.total_tokens}")


async def resume_previous_research() -> None:
    """Resume a previous research operation."""
    probe = DeepProbe()

    # Use a previously saved interaction ID
    interaction_id = "your-interaction-id-here"

    print(f"Resuming research: {interaction_id}")
    result = await probe.resume_async(interaction_id)

    print(f"Status: {result.status.value}")
    print(f"Report length: {len(result.report)} characters")


if __name__ == "__main__":
    # Run basic async example
    asyncio.run(main())

    # Uncomment to run other examples:
    # streaming_example()
    # asyncio.run(run_multiple_researches())
    # asyncio.run(resume_previous_research())