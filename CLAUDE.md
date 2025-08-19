# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Setup and dependencies
uv sync                    # Install dependencies
uv run pre-commit install  # Setup git hooks for code quality

# Testing
uv run pytest             # Run all tests
uv run pytest tests/test_specific.py  # Run specific test file
uv run pytest -k "test_pattern"       # Run tests matching pattern

# Code quality
uv run mypy src tests      # Type checking
uv run ruff check --fix .  # Format and lint code
uv run pre-commit run --all-files  # Run all hooks manually

# CLI development and testing
uv run claudeguard --help          # Test CLI commands
uv run claudeguard install         # Install hook and initialize default profiles
uv run claudeguard status          # Show configuration status
uv run claudeguard create-profile  # Create new security profile
uv run claudeguard list-profiles   # List available profiles
uv run claudeguard switch-profile  # Switch between profiles
uv run claudeguard delete-profile  # Delete security profile
uv run claudeguard uninstall       # Remove claudeguard hook
```

## Architecture Overview

claudeguard is a security layer for Claude Code that intercepts tool calls and makes permission decisions through pattern matching. The system is built around these core components:

### Hook System (`src/claudeguard/hook.py`)
- Entry point that intercepts Claude Code tool calls via JSON stdin/stdout protocol
- Integrates with Claude Code's `permissionDecision` hook system
- Handles error sanitization and fail-safe behavior

### Permission Engine (`src/claudeguard/permission_decision.py`)
- Makes security decisions (`allow`, `ask`, `deny`) based on loaded profiles
- Implements fail-safe defaults (errors default to "ask")
- Core decision-making logic for tool call authorization

### Pattern Matching (`src/claudeguard/pattern_matcher.py`)
- Multi-strategy pattern matching: glob, regex, and MCP-specific patterns
- Includes DoS protection for regex patterns and input validation
- Extracts resources from tool calls for pattern comparison

### Profile System (`src/claudeguard/profile_loader.py`, `src/claudeguard/models.py`)
- Loads security profiles from `.claudeguard/profiles/` directory
- Hierarchy: project-specific → home directory → built-in defaults
- Immutable data structures with YAML-based configuration

### CLI Interface (`src/claudeguard/cli.py`)
- Click-based CLI for profile management and system configuration
- Commands: `install`, `status`, `create-profile`, `list-profiles`, `switch-profile`, `delete-profile`, `uninstall`
- Handles Claude Code settings integration

## Key Patterns

- **Fail-safe architecture**: All errors default to secure behavior ("ask")
- **Immutable data structures**: Thread-safe with frozen dataclasses and tuples
- **Chain of responsibility**: Rules processed in order until first match
- **Strategy pattern**: Different resource matchers for different pattern types
- **Defense in depth**: Input validation, DoS protection, path traversal prevention

## Testing Strategy

Tests are organized by functionality:
- `test_*_metadata.py`: CLI and profile management tests
- `test_*_patterns.py`: Pattern matching logic tests
- `test_*_security.py`: Security validation tests
- `test_*_integration.py`: End-to-end system tests

Use factories in `tests/factories.py` for consistent test data generation.
