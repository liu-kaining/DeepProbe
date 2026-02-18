"""Command-line interface for DeepProbe."""

from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.status import Status

from . import __version__
from .core import DeepProbe
from .exceptions import DeepProbeError
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
        str | None,
        typer.Option("--save", "-s", help="Save report to file"),
    ] = None,
    resume: Annotated[
        str | None,
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
        str | None,
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
    save: str | None,
    verbose: bool,
    quiet: bool,
    stream: bool,
) -> None:
    """Execute a new research operation."""
    if not quiet:
        console.print(Panel(f"[bold blue]{topic}[/bold blue]", title="Research Topic"))

    try:
        if stream:
            result = _run_streaming_research(probe, topic, verbose, quiet)
        else:
            result = _run_polling_research(probe, topic, verbose, quiet)

        _display_result(result, save, verbose, quiet)
    except DeepProbeError as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if e.interaction_id:
            console.print(f"[yellow]Resume with: deep-probe --resume {e.interaction_id}[/yellow]")
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

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Starting research...", total=None)

        # Start research
        progress.update(task, description="Running deep research...")

        result = probe.research(topic)

        progress.update(task, description="Processing results...")

    return result


def _run_streaming_research(
    probe: DeepProbe,
    topic: str,
    verbose: bool,
    quiet: bool,
) -> ResearchResult:
    """Run research with streaming output."""
    def on_text(text: str) -> None:
        if not quiet:
            console.print(text, end="")

    def on_thought(thought: str) -> None:
        if verbose and not quiet:
            console.print(f"\n[dim]💭 {thought}[/dim]\n")

    if not quiet:
        console.print("[yellow]Starting streaming research...[/yellow]\n")

    result = probe.research_stream(
        topic,
        on_text=on_text if not quiet else None,
        on_thought=on_thought if verbose else None,
    )

    if not quiet:
        console.print("\n")

    return result


def _run_resume(
    probe: DeepProbe,
    interaction_id: str,
    save: str | None,
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
    save: str | None,
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
    console.print(f"[green]✓ Research completed[/green]")
    console.print(f"  Interaction ID: [cyan]{result.interaction_id}[/cyan]")
    console.print(f"  Status: {result.status.value}")
    console.print(f"  Tokens: {result.cost_usage.total_tokens}")

    if save:
        save_report(result, save)
        console.print(f"  Saved to: [cyan]{save}[/cyan]")

    # Display thoughts if verbose
    if verbose and result.thoughts:
        console.print()
        console.print("[bold]Research Process:[/bold]")
        for i, thought in enumerate(result.thoughts, 1):
            phase_str = f"[{thought.phase}]" if thought.phase else ""
            content = thought.content[:100] + "..." if len(thought.content) > 100 else thought.content
            console.print(f"  {i}. {phase_str} {content}")

    # Display the report
    console.print()
    console.print("[bold]Report:[/bold]")
    console.print()

    # Render as markdown
    md = Markdown(result.report)
    console.print(md)

    # Display sources if available
    if result.sources:
        console.print()
        console.print(f"[bold]Sources ({len(result.sources)}):[/bold]")
        for i, source in enumerate(result.sources[:10], 1):  # Limit to 10
            console.print(f"  {i}. [link={source.url}]{source.title or source.url}[/link]")
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