# claudeguard Python Development Conventions

## 1. Introduction

This document outlines the Python development conventions for the claudeguard project. These conventions ensure code consistency, readability, and maintainability across all components (CLI, pattern matching, profile management, hook integration, and testing).

### 1.1. Core Principles

Our development philosophy emphasizes:

* **Simplicity over complexity** - Code should be self-explanatory through meaningful names and clear flow
* **Minimal commenting** - Comments are highly discouraged; prefer descriptive naming and pure functions
* **Security-first approach** - Never expose or log secrets; follow security best practices
* **Type safety** - Use type hints extensively for better IDE support and error prevention
* **Natural testability** - Well-designed code should be testable through its public interface without special accommodations
* **Separation of concerns** - Each module should have a single, well-defined responsibility
* **Immutable data models** - Use frozen dataclasses for data structures to prevent mutation bugs

## 2. Code Style and Formatting

Our code style is enforced automatically through pre-commit hooks using `ruff` and follows **PEP 8** standards.

### 2.1. Naming Conventions

* **Variables, Functions, and Modules:** Use `snake_case`
* **Classes and Exceptions:** Use `PascalCase`
* **Constants:** Use `ALL_CAPS_WITH_UNDERSCORES`
* **Packages:** Use lowercase names (our package structure: `claudeguard.cli`, `claudeguard.models`, etc.)
* **Private attributes:** Use single underscore prefix (`_private_method`)

### 2.2. Line Length and Formatting

* **88 characters maximum** (enforced by `ruff format`)
* Use implicit line joining with parentheses for long statements
* Automatic formatting applied via pre-commit hooks

### 2.3. Imports

* Import organization handled automatically by `ruff`
* Order: standard library, third-party, local modules
* Use `from __future__ import annotations` for forward references
* Known first-party modules: `claudeguard`

### 2.4. Documentation Strategy

* **Minimal documentation approach** - Code should be self-documenting
* Use type hints extensively instead of docstring parameter documentation
* Focus docstrings on *why* and business logic, not implementation details
* CLI commands require clear help text for external users

### 2.5. Comments Policy

* **Comments are highly discouraged** per project guidelines
* Prefer meaningful variable/function names over explanatory comments
* Use pure functions and clear control flow instead of commented complex logic

## 3. Project Structure

Our project follows a modular architecture with clear separation of concerns:

```
claudeguard/
├── src/
│   └── claudeguard/
│       ├── __init__.py
│       ├── cli.py                  # Click-based command line interface
│       ├── hook.py                 # Claude Code hook integration
│       ├── models.py               # Immutable data models and types
│       ├── pattern_matcher.py      # Pattern matching engine
│       ├── profile_loader.py       # Profile management
│       ├── permission_decision.py  # Permission decision logic
│       └── default_rules.py        # Default security rules
├── tests/                          # Comprehensive test suite
├── docs/                           # User and technical documentation
│   ├── features/                   # User-facing feature docs
│   └── technical/                  # Technical documentation
├── specs/                          # Project specifications
└── pyproject.toml                  # Project configuration
```

### 3.1. Component-Specific Guidelines

* **CLI (`claudeguard/cli.py`)**: Click-based command interface with emoji-enhanced terminal output
* **Pattern Matching (`claudeguard/pattern_matcher.py`)**: Glob and regex pattern matching for security rules
* **Models (`claudeguard/models.py`)**: Immutable frozen dataclasses for all data structures
* **Profile System (`claudeguard/profile_loader.py`)**: YAML-based security profile management
* **Hook Integration (`claudeguard/hook.py`)**: Claude Code permissionDecision hook implementation
* **Tests (`tests/`)**: Pytest with comprehensive behavior-driven testing

### 3.2. Configuration Management

* `pyproject.toml` contains all Python tooling configuration
* Security profiles in `.claudeguard/profiles/` directory (YAML format)
* No environment variables for core functionality (security profiles handle configuration)

## 4. Dependency Management

We use **uv** for fast dependency management and virtual environment handling.

### 4.1. Core Commands

* **Install dependencies:** `uv sync`
* **Add dependency:** `uv add <package-name>`
* **Add dev dependency:** `uv add --group dev <package-name>`
* **Run commands:** `uv run <command>`

### 4.2. Key Dependencies

* **CLI Framework:** Click for command-line interface
* **Configuration:** PyYAML for profile management
* **Testing:** pytest with strict markers and configuration
* **Code Quality:** ruff, mypy, bandit for linting and security
* **Type Hints:** types-pyyaml for YAML type safety

### 4.3. Version Requirements

* **Python:** >= 3.10 (specified in pyproject.toml)
* **Dependency groups:** `dev` group for development dependencies
* **Lock file:** `uv.lock` ensures reproducible builds

## 5. Code Quality and Linting

### 5.1. Automated Enforcement

Code quality is enforced through development tools:

* **ruff check --fix**: Linting with automatic fixes
* **ruff format**: Code formatting
* **mypy**: Type checking with strict configuration
* **bandit**: Security linting

### 5.2. Current Ruff Configuration

```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["F", "E", "W", "I", "UP", "B", "S", "PL", "RUF"]
ignore = ["PLR0911", "PLR2004", "S108", "COM812", "ISC001"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "PLR2004", "E501", "PLC0415"]
```

### 5.3. MyPy Configuration

Strict typing configuration in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
exclude = ["build/", "dist/"]
disable_error_code = ["misc"]
```

## 6. Architecture and Design Patterns

### 6.1. Immutable Data Models

**Frozen Dataclasses:**

All data models use `@dataclass(frozen=True)` to prevent mutation bugs:

```python
@dataclass(frozen=True)
class ToolCall:
    name: ToolName
    input: ToolInput

@dataclass(frozen=True)
class ProfileRule:
    pattern: str
    action: Action
    comment: str = ""
```

**Type Safety:**

* Use literal types for constrained values: `Action = Literal["allow", "deny", "ask"]`
* Type aliases for clarity: `ToolName = str`
* Generic types for containers: `dict[str, Any]`, `tuple[ProfileRule, ...]`

### 6.2. Modular Architecture Principles

**Separation of Concerns:**

* Pattern matching logic isolated in `pattern_matcher.py`
* Profile management separated from pattern matching
* CLI commands delegate to specialized modules
* Hook integration isolated from core logic

**Clean Interfaces:**

* Design public APIs that hide implementation details
* Use immutable data structures for function parameters
* Prefer composition over inheritance

**Error Handling:**

* Use Click's built-in error handling for CLI commands
* System exits with appropriate error codes
* Clear error messages with emoji indicators

### 6.3. Security Patterns

**Input Validation:**

```python
def _validate_profile_name(name: str) -> None:
    if not PROFILE_NAME_PATTERN.match(name):
        click.echo("❌ Invalid profile name")
        sys.exit(1)
```

**Path Safety:**

* Use `Path` objects for all file operations
* Validate paths before file operations
* Never trust user input for file paths

## 7. Type Safety and Static Analysis

### 7.1. Type Hints Requirements

* **Mandatory for all code** - Type hints required for functions, methods, and complex variables
* **Future annotations** - Use `from __future__ import annotations` for forward references
* **Immutable structures** - Prefer tuples over lists for fixed-size collections

### 7.2. MyPy Strict Mode

All code must pass `mypy --strict` checking:

* `disallow_untyped_defs = true`
* `disallow_incomplete_defs = true`
* `check_untyped_defs = true`
* `no_implicit_optional = true`

### 7.3. External Library Handling

Type stubs included for external dependencies:

* `types-pyyaml` for YAML operations
* All dependencies have type annotations or stubs

## 8. Testing Strategy

### 8.1. Testing Framework

* **pytest** with strict configuration
* **Behavior-driven testing** focusing on observable outcomes
* **Comprehensive test markers** for categorization

### 8.2. Test Design Philosophy

**Test Behavior, Not Implementation:**

* Tests verify **what the code does** (behavior) rather than **how it's implemented**
* Use public interfaces and APIs instead of accessing private attributes
* Focus on functional outcomes and observable behavior
* Test names describe the behavior being tested

**Natural Testability:**

* Well-designed code should be inherently testable through its public interface
* Dependencies should be clear and minimal
* Use immutable data structures to make testing predictable

**Comprehensive Coverage:**

* Pattern matching edge cases
* CLI command combinations
* Profile validation scenarios
* Error handling paths

### 8.3. Test Organization

Test files follow clear naming conventions:

* `test_pattern_*.py` - Pattern matching tests
* `test_cli_*.py` - CLI command tests
* `test_profile_*.py` - Profile system tests
* `test_*_integration.py` - Integration tests
* `test_*_metadata.py` - Metadata and validation tests

### 8.4. Test Categories and Markers

```toml
[tool.pytest.ini_options]
addopts = [
    "--strict-markers",
    "--strict-config",
]
```

### 8.5. Testing Best Practices

**Good Test Examples:**

```python
def test_pattern_matches_exact_tool_name():
    """Test that exact tool names match correctly."""
    matcher = PatternMatcher()
    result = matcher.match("Edit", "Edit(file.txt)")
    assert result.matched is True

def test_cli_validates_profile_names():
    """Test that CLI rejects invalid profile names."""
    result = runner.invoke(cli, ["create-profile", "invalid@name"])
    assert result.exit_code == 1
    assert "Invalid profile name" in result.output
```

**Test Immutable Structures:**

```python
def test_tool_call_immutability():
    """Test that ToolCall objects cannot be modified."""
    tool_call = ToolCall(name="Edit", input=ToolInput(data={}))
    with pytest.raises(FrozenInstanceError):
        tool_call.name = "Write"  # Should fail
```

### 8.6. Running Tests

```bash
# All tests
uv run pytest

# Specific test categories
uv run pytest tests/test_pattern*.py    # Pattern matching tests
uv run pytest tests/test_cli*.py        # CLI command tests

# With coverage
uv run pytest --cov=claudeguard
```

## 9. Development Workflow

### 9.1. Essential Commands

```bash
# Quick start
uv sync && uv run claudeguard init

# Development
uv run claudeguard status                  # Check current status
uv run claudeguard install                 # Install hook integration

# Testing and Quality
uv run pytest                         # Run all tests
uv run mypy src tests                  # Type checking
uv run ruff check --fix .              # Lint and fix
uv run ruff format .                   # Format code
```

### 9.2. Git Workflow

* Use conventional commit messages for better versioning
* Never commit secrets or sensitive data
* Test changes before committing
* Keep commits focused and atomic

### 9.3. Security Guidelines

* Follow defensive security practices only
* Validate all user input
* Use secure file operations
* Never log or expose sensitive data
* Pattern matching for security rules, not exploitation

### 9.4. Documentation Standards

* Technical docs in `docs/technical/` directory
* User docs in `docs/features/` directory
* Self-documenting code preferred over extensive documentation
* Clear CLI help text and error messages
* Code examples in documentation must be tested

## 10. CLI Design Patterns

### 10.1. Click Framework Usage

* Use Click decorators for all commands
* Provide clear help text for all commands and options
* Use emoji indicators for success/error states
* Exit with appropriate error codes

### 10.2. User Experience

* Immediate feedback for all operations
* Clear error messages with actionable guidance
* Consistent emoji usage: ✅ success, ❌ error, ℹ️ info
* Progressive disclosure of complexity

### 10.3. Command Structure

```python
@click.command()
@click.argument("profile_name")
@click.option("--description", help="Profile description")
def create_profile(profile_name: str, description: str | None) -> None:
    """Create a new security profile."""
    # Implementation
```

This document serves as the authoritative guide for Python development practices in the claudeguard project, ensuring consistency, security, and maintainability across all code contributions.
