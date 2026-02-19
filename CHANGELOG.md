# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-02-19

### Added
- Read research topic from file: `-i` / `--input` option for long prompts (e.g. `deep-probe research -i prompt.txt --save report.md`)

## [0.1.3] - 2026-02-18

### Fixed
- Documentation: CLI examples now use the correct `research` subcommand
- All docs and docstrings use `deep-probe research "topic"` instead of `deep-probe "topic"`

## [0.1.2] - 2026-02-18

### Added
- Automatic retry mechanism for API rate limit errors (429)
- Exponential backoff for rate limit retries (60s, 120s, 240s, 300s delays)
- User-friendly retry progress notifications in CLI
- Enhanced error messages with retry information

### Improved
- Better handling of quota exceeded errors with automatic retry (up to 5 attempts)
- More informative error messages when rate limits are encountered

## [0.1.1] - 2026-02-18

### Fixed
- Fix Typer compatibility issue: Replace `str | None` with `Optional[str]` for Python 3.9+ compatibility
- CLI now works correctly with Typer's type system

## [0.1.0] - 2026-02-18

### Added
- Initial release of DeepProbe
- Core `DeepProbe` client with sync/async support
- Research methods: `research()`, `research_async()`, `research_stream()`
- Resume functionality: `resume()`, `resume_async()`
- CLI tool with Rich-powered interface
- Automatic reconnection with exponential backoff
- Structured output with Pydantic models
- Support for thinking summaries and citations
- Token usage tracking
- Comprehensive error handling with custom exceptions

### Features
- Simple one-line API for deep research
- Real-time streaming output
- Progress tracking and status updates
- Markdown report generation
- Source citation extraction
- Network error recovery with interaction ID tracking
