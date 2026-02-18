# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
