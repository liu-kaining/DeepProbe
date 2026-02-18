"""Command-line interface for DeepProbe."""

import threading
import time
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.status import Status

from . import __version__
from .core import DeepProbe
from .exceptions import DeepProbeError, ProbeNetworkError
from .models import ResearchResult
from .utils import save_report

app = typer.Typer(
    name="deep-probe",
    help="Research anything, deeply, in one line of code.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"deep-probe version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = False,
) -> None:
    """Deep Probe - Research anything, deeply, in one line of code."""
    pass


@app.command()
def research(
    topic: Annotated[str, typer.Argument(help="Research topic or question")],
    save: Annotated[
        Optional[str],
        typer.Option("--save", "-s", help="Save report to file"),
    ] = None,
    resume: Annotated[
        Optional[str],
        typer.Option("--resume", "-r", help="Resume previous research by interaction ID"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-V", help="Show thinking process and details"),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Only output the final report"),
    ] = False,
    stream: Annotated[
        bool,
        typer.Option("--stream", help="Stream output in real-time"),
    ] = False,
    api_key: Annotated[
        Optional[str],
        typer.Option("--api-key", "-k", help="Google Gemini API key", envvar="GEMINI_API_KEY"),
    ] = None,
) -> None:
    """Run deep research on a topic.

    Examples:
        deep-probe "What is quantum computing?"
        deep-probe "AI trends 2024" --save report.md
        deep-probe --resume "interaction-id-here"
        deep-probe "Climate change effects" --verbose
        deep-probe "Research topic" --stream
    
    Note: Deep research typically takes 2-10 minutes. Use --stream for real-time output.
    """
    if quiet and verbose:
        console.print("[red]Error: Cannot use both --quiet and --verbose[/red]")
        raise typer.Exit(1)

    try:
        probe = DeepProbe(api_key=api_key)
    except DeepProbeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if resume:
        _run_resume(probe, resume, save, verbose, quiet)
    else:
        _run_research(probe, topic, save, verbose, quiet, stream)


def _run_research(
    probe: DeepProbe,
    topic: str,
    save: Optional[str],
    verbose: bool,
    quiet: bool,
    stream: bool,
) -> None:
    """Execute a new research operation."""
    if not quiet:
        console.print(Panel(f"[bold blue]{topic}[/bold blue]", title="Research Topic"))
        if stream:
            console.print("[dim]💡 Streaming mode: Real-time output with thinking process[/dim]\n")
        elif verbose:
            console.print("[dim]💡 Verbose mode: Thinking process will be shown during research[/dim]\n")
        else:
            console.print("[dim]💡 Tip: Use --stream for real-time output, or --verbose to see thinking process[/dim]\n")

    try:
        if stream:
            result = _run_streaming_research(probe, topic, verbose, quiet)
        else:
            result = _run_polling_research(probe, topic, verbose, quiet)

        _display_result(result, save, verbose, quiet)
    except DeepProbeError as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if e.interaction_id:
            console.print(f"[yellow]Resume with: python -m deep_probe.cli research --resume {e.interaction_id}[/yellow]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Research cancelled by user[/yellow]")
        raise typer.Exit(130)


def _run_polling_research(
    probe: DeepProbe,
    topic: str,
    verbose: bool,
    quiet: bool,
) -> ResearchResult:
    """Run research with polling mode."""
    if quiet:
        return probe.research(topic)

    thoughts_received = []
    start_time = time.time()
    result = None
    
    def on_thought(thought: str) -> None:
        """Callback for thinking summaries."""
        thoughts_received.append(thought)
        if verbose:
            elapsed = time.time() - start_time
            elapsed_str = f"{elapsed/60:.1f}min" if elapsed >= 60 else f"{elapsed:.0f}s"
            console.print(f"\n[dim]💭 [{elapsed_str}] {thought}[/dim]")

    # Show initial message with time estimate
    console.print("\n[yellow]⏳ Starting deep research...[/yellow]")
    console.print("[dim]   ⏱️  Estimated time: 2-10 minutes (depending on topic complexity)[/dim]")
    console.print("[dim]   📊 Status updates every 10 seconds[/dim]")
    if verbose:
        console.print("[dim]   💭 Thinking process will be shown below[/dim]")
    console.print()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing research...", total=None)
            
            # Start research with dynamic status updates
            def update_status():
                """Update status message periodically."""
                while not progress.finished:
                    elapsed = time.time() - start_time
                    
                    if elapsed < 30:
                        status = "Starting research task..."
                    elif elapsed < 120:
                        status = f"Researching... ({elapsed:.0f}s elapsed, typically 2-10 min)"
                    elif elapsed < 300:
                        status = f"Researching... ({elapsed/60:.1f} min elapsed, typically 2-10 min)"
                    elif elapsed < 600:
                        status = f"Researching... ({elapsed/60:.1f} min elapsed, may take up to 10 min)"
                    else:
                        status = f"Researching... ({elapsed/60:.1f} min elapsed, max 30 min)"
                    
                    if verbose and thoughts_received:
                        status += f" | 💭 {len(thoughts_received)} thoughts"
                    
                    progress.update(task, description=status)
                    time.sleep(2)  # Update every 2 seconds
            
            # Start status update thread
            status_thread = threading.Thread(target=update_status, daemon=True)
            status_thread.start()
            
            # Start the research (this will block until complete)
            result = probe.research(topic, on_thought=on_thought if verbose else None)
            
            progress.update(task, description="Processing results...")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Research interrupted by user[/yellow]")
        if result and hasattr(result, 'interaction_id') and result.interaction_id:
            console.print(f"[cyan]💡 Resume with: python -m deep_probe.cli research --resume {result.interaction_id}[/cyan]")
        raise typer.Exit(130)
    
    elapsed_total = time.time() - start_time
    elapsed_min = elapsed_total / 60
    
    console.print(f"\n[green]✓ Research completed in {elapsed_min:.1f} minute{'s' if elapsed_min != 1 else ''}[/green]")
    
    if verbose and thoughts_received:
        console.print(f"[dim]   💭 Total thoughts captured: {len(thoughts_received)}[/dim]")

    return result


def _run_streaming_research(
    probe: DeepProbe,
    topic: str,
    verbose: bool,
    quiet: bool,
) -> ResearchResult:
    """Run research with streaming output."""
    import time
    
    start_time = time.time()
    thoughts_count = [0]
    text_received = [False]
    
    def on_text(text: str) -> None:
        if not quiet:
            if not text_received[0]:
                # First text chunk - show header
                elapsed = time.time() - start_time
                console.print(f"\n[green]📝 Report started ({elapsed:.0f}s)[/green]\n")
                text_received[0] = True
            console.print(text, end="", flush=True)

    def on_thought(thought: str) -> None:
        if verbose and not quiet:
            thoughts_count[0] += 1
            elapsed = time.time() - start_time
            elapsed_str = f"{elapsed/60:.1f}min" if elapsed >= 60 else f"{elapsed:.0f}s"
            console.print(f"\n[yellow]💭 [{elapsed_str}] Thinking Step {thoughts_count[0]}:[/yellow]")
            console.print(f"[dim]{thought}[/dim]\n")

    if not quiet:
        console.print("[yellow]⏳ Starting streaming research...[/yellow]")
        console.print("[dim]   ⏱️  Real-time output mode - content will stream as it's generated[/dim]")
        if verbose:
            console.print("[dim]   💭 Thinking process will be shown with timestamps[/dim]")
        console.print()

    try:
        result = probe.research_stream(
            topic,
            on_text=on_text if not quiet else None,
            on_thought=on_thought if verbose else None,
        )
        
        elapsed_total = time.time() - start_time
        elapsed_min = elapsed_total / 60
        
        if not quiet:
            console.print("\n")
            console.print(f"[green]✓ Research completed in {elapsed_min:.1f} minute{'s' if elapsed_min != 1 else ''}[/green]")
            if verbose:
                console.print(f"[dim]   💭 Total thinking steps: {thoughts_count[0]}[/dim]")
                if result.report:
                    console.print(f"[dim]   📝 Report length: {len(result.report)} characters[/dim]")
        
    except ProbeNetworkError as e:
        elapsed = time.time() - start_time
        console.print(f"\n[yellow]⚠️  Network connection interrupted after {elapsed:.0f}s[/yellow]")
        if e.interaction_id:
            console.print(f"[cyan]💡 Interaction ID: {e.interaction_id}[/cyan]")
            console.print(f"[cyan]💡 Resume with: python -m deep_probe.cli research --resume {e.interaction_id}[/cyan]")
            console.print("[dim]   Or wait a moment and try again - the research continues in the background[/dim]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        console.print(f"\n[yellow]⚠️  Research interrupted after {elapsed:.0f}s[/yellow]")
        # Try to get interaction_id from probe if possible
        console.print("[dim]   Note: If research was started, you may be able to resume it later[/dim]")
        raise typer.Exit(130)

    return result


def _run_resume(
    probe: DeepProbe,
    interaction_id: str,
    save: Optional[str],
    verbose: bool,
    quiet: bool,
) -> None:
    """Resume a previous research operation."""
    if not quiet:
        console.print(f"[yellow]Resuming research: {interaction_id}[/yellow]")

    try:
        if quiet:
            result = probe.resume(interaction_id)
        else:
            with Status("[yellow]Checking research status...[/yellow]", console=console):
                result = probe.resume(interaction_id)

        _display_result(result, save, verbose, quiet)
    except DeepProbeError as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Research cancelled by user[/yellow]")
        raise typer.Exit(130)


def _display_result(
    result: ResearchResult,
    save: Optional[str],
    verbose: bool,
    quiet: bool,
) -> None:
    """Display the research result."""
    if quiet:
        # Only output the report
        console.print(result.report)
        return

    # Display metadata
    console.print()
    console.print(f"[green]✓ Research Summary[/green]")
    console.print(f"  📋 Interaction ID: [cyan]{result.interaction_id}[/cyan]")
    console.print(f"  📊 Status: {result.status.value}")
    
    if result.cost_usage.total_tokens > 0:
        console.print(f"  🔢 Tokens: {result.cost_usage.total_tokens:,} "
                     f"(input: {result.cost_usage.input_tokens:,}, "
                     f"output: {result.cost_usage.output_tokens:,})")
    
    if result.report:
        console.print(f"  📝 Report length: {len(result.report):,} characters")
    
    if result.thoughts:
        console.print(f"  💭 Thinking steps: {len(result.thoughts)}")
    
    if result.sources:
        console.print(f"  🔗 Sources: {len(result.sources)}")

    if save:
        save_report(result, save)
        console.print(f"  💾 Saved to: [cyan]{save}[/cyan]")

    # Display thoughts if verbose and not already shown (streaming mode shows them in real-time)
    if verbose and result.thoughts and not result.report:
        console.print()
        console.print("[bold]Research Process:[/bold]")
        for i, thought in enumerate(result.thoughts, 1):
            phase_str = f"[{thought.phase}]" if thought.phase else ""
            content = thought.content[:150] + "..." if len(thought.content) > 150 else thought.content
            console.print(f"  {i}. {phase_str} {content}")

    # Display the report (only if not already shown in streaming mode)
    if result.report and not quiet:
        # Check if report was already printed (streaming mode)
        # For now, always show it in a formatted way
        console.print()
        console.print("[bold]📄 Final Report:[/bold]")
        console.print()

        # Render as markdown
        md = Markdown(result.report)
        console.print(md)

    # Display sources if available
    if result.sources:
        console.print()
        console.print(f"[bold]🔗 Sources ({len(result.sources)}):[/bold]")
        for i, source in enumerate(result.sources[:10], 1):  # Limit to 10
            title = source.title or source.url
            console.print(f"  {i}. [link={source.url}]{title}[/link]")
            if source.snippet:
                snippet = source.snippet[:100] + "..." if len(source.snippet) > 100 else source.snippet
                console.print(f"     [dim]{snippet}[/dim]")
        if len(result.sources) > 10:
            console.print(f"  ... and {len(result.sources) - 10} more")


@app.command()
def config() -> None:
    """Show configuration instructions."""
    console.print(Panel(
        "[bold]Configuration[/bold]\n\n"
        "Set your Google Gemini API key:\n\n"
        "  [cyan]export GEMINI_API_KEY='your-api-key'[/cyan]\n\n"
        "Or create a [cyan].env[/cyan] file:\n\n"
        "  [cyan]GEMINI_API_KEY=your-api-key[/cyan]\n\n"
        "Get your API key from: [link]https://aistudio.google.com/apikey[/link]",
        title="Deep Probe Setup",
    ))


if __name__ == "__main__":
    app()