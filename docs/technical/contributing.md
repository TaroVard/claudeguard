# Contributing to claudeguard

Welcome to claudeguard! This guide provides comprehensive information for contributors to help maintain high code quality, security standards, and project consistency.

## Getting Started

### Development Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/tarovard/claudeguard
   cd claudeguard
   ```

2. **Set up development environment**
   ```bash
   # Install dependencies with uv
   uv sync

   # Install development tools
   uv add --dev pytest pytest-cov pytest-xdist mypy ruff black

   # Install pre-commit hooks (if available)
   uv run pre-commit install
   ```

3. **Verify setup**
   ```bash
   # Run test suite
   uv run pytest

   # Run type checking
   uv run mypy src tests

   # Run linting
   uv run ruff check --fix .

   # Test CLI
   uv run claudeguard --help
   ```

### Development Tools

- **uv**: Dependency management and virtual environment
- **pytest**: Testing framework with coverage reporting
- **mypy**: Static type checking with `--strict` mode
- **ruff**: Fast Python linter and formatter
- **black**: Code formatting (if not using ruff format)

## Project Structure and Architecture

### Core Components

```
src/claudeguard/
├── cli.py                 # Command-line interface (Click-based)
├── hook.py               # Claude Code hook integration
├── models.py             # Data models and types
├── pattern_matcher.py    # Pattern matching engine
├── profile_loader.py     # Profile management system
├── permission_decision.py # Permission decision logic
└── default_rules.py      # Built-in security rules
```

### Key Design Principles

1. **Security First**: All code must fail safely and securely
2. **Immutable Data**: Use frozen dataclasses for thread safety
3. **Type Safety**: Full mypy --strict compliance required
4. **Performance**: Critical paths must meet performance requirements
5. **Testability**: All code must be thoroughly testable

## Code Quality Standards

### Type Safety Requirements

All code must pass `mypy --strict`:

```python
# Good: Fully typed with explicit return types
def load_profile(path: Path) -> Profile | None:
    """Load profile from file path with proper error handling."""
    try:
        content = path.read_text(encoding="utf-8")
        return parse_profile(content)
    except (FileNotFoundError, PermissionError):
        return None

# Bad: Missing type annotations
def load_profile(path):
    content = path.read_text()
    return parse_profile(content)
```

### Error Handling Standards

1. **Fail-Safe Design**: Always default to secure behavior
2. **Comprehensive Exception Handling**: Handle all possible error conditions
3. **Logging**: Log security-relevant events and errors
4. **User-Friendly Messages**: Provide actionable error messages

```python
# Good: Comprehensive error handling
def make_permission_decision(tool_call: ToolCall) -> HookResponse:
    """Make permission decision with fail-safe error handling."""
    try:
        profile = load_active_profile()
        result = evaluate_rules(tool_call, profile.rules)
        log_decision(tool_call, result)
        return create_response(result)
    except ProfileLoadError as e:
        logger.warning(f"Profile load failed: {e}, using safe defaults")
        return HookResponse(action="ask", reason="Profile unavailable")
    except Exception as e:
        logger.error(f"Unexpected error in permission decision: {e}")
        return HookResponse(action="ask", reason="Internal error")

# Bad: Insufficient error handling
def make_permission_decision(tool_call: ToolCall) -> HookResponse:
    profile = load_active_profile()  # Could fail
    result = evaluate_rules(tool_call, profile.rules)  # Could fail
    return create_response(result)
```

### Performance Requirements

Critical components must meet performance targets:

- **Hook Response Time**: < 100ms for permission decisions
- **Pattern Matching**: < 10ms for complex patterns
- **Profile Loading**: < 50ms for profile loading
- **Memory Usage**: < 10MB for typical operation

```python
# Performance testing example
def test_permission_decision_performance():
    """Ensure permission decisions meet performance requirements."""
    tool_call = create_test_tool_call()

    start_time = time.time()
    for _ in range(1000):
        make_permission_decision(tool_call)
    end_time = time.time()

    average_time = (end_time - start_time) / 1000
    assert average_time < 0.1, f"Permission decision too slow: {average_time}s"
```

## Security Guidelines

### Input Validation

All user inputs must be validated and sanitized:

```python
# Good: Comprehensive input validation
def validate_profile_name(name: str) -> bool:
    """Validate profile name for security and correctness."""
    if not name or len(name) > 100:
        return False

    # Prevent path traversal
    if ".." in name or "/" in name or "\\" in name:
        return False

    # Prevent command injection
    if any(char in name for char in [";", "&", "|", "`", "$"]):
        return False

    # Prevent reserved names
    if name.lower() in ["con", "prn", "aux", "nul"]:  # Windows reserved
        return False

    # Must be valid filename
    return re.match(r"^[a-zA-Z0-9_-]+$", name) is not None

# Bad: No validation
def create_profile(name: str):
    path = Path(f".claudeguard/profiles/{name}.yaml")  # Vulnerable to path traversal
    path.write_text(profile_content)
```

### Path Security

Prevent directory traversal attacks:

```python
# Good: Secure path handling
def resolve_profile_path(name: str) -> Path:
    """Resolve profile path with security validation."""
    if not validate_profile_name(name):
        raise SecurityError(f"Invalid profile name: {name}")

    base_dir = Path(".claudeguard/profiles").resolve()
    profile_path = (base_dir / f"{name}.yaml").resolve()

    # Ensure path is within allowed directory
    if not str(profile_path).startswith(str(base_dir)):
        raise SecurityError(f"Path traversal attempt: {name}")

    return profile_path

# Bad: Vulnerable to path traversal
def resolve_profile_path(name: str) -> Path:
    return Path(f".claudeguard/profiles/{name}.yaml")
```

### Regex Security

Protect against ReDoS (Regular Expression Denial of Service):

```python
# Good: Secure regex with protections
class RegexResourceMatcher:
    MAX_PATTERN_LENGTH = 1000
    MAX_QUANTIFIERS = 20
    TIMEOUT_SECONDS = 0.1

    def matches(self, pattern: str, resource: str) -> bool:
        """Match with comprehensive security protections."""
        if not self._is_safe_pattern(pattern):
            raise PatternSecurityError(f"Unsafe regex pattern: {pattern}")

        compiled = self._get_compiled_pattern(pattern)
        return self._execute_with_timeout(compiled, resource)

    def _is_safe_pattern(self, pattern: str) -> bool:
        """Validate pattern for security."""
        if len(pattern) > self.MAX_PATTERN_LENGTH:
            return False

        quantifier_count = pattern.count("*") + pattern.count("+")
        if quantifier_count > self.MAX_QUANTIFIERS:
            return False

        # Check for dangerous patterns
        dangerous_patterns = [".*.*", ".+.+", "(.*)*", "(.+)+"]
        return not any(dangerous in pattern for dangerous in dangerous_patterns)
```

## Testing Requirements

### Test Coverage Standards

- **Overall Coverage**: Minimum 95%
- **Security-Critical Code**: 100% coverage required
- **New Features**: All new code must include comprehensive tests
- **Bug Fixes**: Must include regression tests

### Test Categories

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Security Tests**: Test attack scenarios and edge cases
4. **Performance Tests**: Validate performance requirements
5. **End-to-End Tests**: Test complete workflows

### Writing Good Tests

```python
# Good: Descriptive test with clear arrange-act-assert
def test_profile_loading_falls_back_to_default_when_project_missing():
    """Test that profile loading gracefully falls back to default."""
    # Arrange
    with mock_filesystem(project_profile_exists=False):

        # Act
        profile = load_active_profile()

        # Assert
        assert profile.name == "default"
        assert len(profile.rules) > 0
        assert all(rule.action in ["allow", "ask", "deny"] for rule in profile.rules)

# Bad: Unclear test purpose and insufficient validation
def test_profile_loading():
    profile = load_active_profile()
    assert profile is not None
```

### Security Test Requirements

All security-critical code must have comprehensive security tests:

```python
def test_regex_dos_protection():
    """Test protection against ReDoS attacks."""
    dangerous_patterns = [
        "/(.*)*$/",
        "/(.+)+$/",
        "/a*a*a*a*a*$/",
    ]

    for pattern in dangerous_patterns:
        with pytest.raises(PatternSecurityError):
            matcher = RegexResourceMatcher()
            matcher.matches(pattern, "test_string")

def test_path_traversal_prevention():
    """Test prevention of directory traversal attacks."""
    malicious_names = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "profile.yaml\x00.txt",
    ]

    for name in malicious_names:
        with pytest.raises(SecurityError):
            resolve_profile_path(name)
```

## Development Workflow

### Branch Strategy

1. **main**: Production-ready code
2. **develop**: Integration branch for features
3. **feature/***: Individual feature development
4. **hotfix/***: Critical bug fixes
5. **security/***: Security-related fixes

### Commit Standards

Use conventional commits format:

```bash
# Feature commits
git commit -m "feat(cli): add profile deletion with safety checks"

# Bug fixes
git commit -m "fix(pattern): resolve regex timeout issue"

# Security fixes
git commit -m "security(validation): prevent path traversal in profile names"

# Documentation
git commit -m "docs(api): add comprehensive pattern matching examples"

# Performance improvements
git commit -m "perf(matching): optimize directory pattern matching algorithm"
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/add-advanced-patterns
   ```

2. **Implement Changes**
   - Write code following standards
   - Add comprehensive tests
   - Update documentation

3. **Quality Checks**
   ```bash
   # Run all tests
   uv run pytest

   # Type checking
   uv run mypy src tests

   # Linting and formatting
   uv run ruff check --fix .

   # Security scan (if available)
   uv run bandit -r src/
   ```

4. **Create Pull Request**
   - Clear title and description
   - Reference related issues
   - Include test results
   - Request appropriate reviewers

### Code Review Guidelines

#### For Authors

1. **Self-Review First**: Review your own code before submitting
2. **Test Thoroughly**: Ensure all tests pass and coverage is adequate
3. **Document Changes**: Update relevant documentation
4. **Small PRs**: Keep changes focused and reviewable

#### For Reviewers

1. **Security Focus**: Pay special attention to security implications
2. **Test Quality**: Verify test coverage and quality
3. **Performance Impact**: Consider performance implications
4. **Documentation**: Ensure documentation is updated

### Review Checklist

- [ ] Code follows project standards and conventions
- [ ] All tests pass and coverage requirements are met
- [ ] Security implications have been considered
- [ ] Performance impact is acceptable
- [ ] Documentation is updated
- [ ] Breaking changes are properly documented
- [ ] Error handling is comprehensive
- [ ] Type annotations are complete and correct

## Component-Specific Guidelines

### CLI Development (`cli.py`)

```python
# Good: Robust CLI command with validation
@click.command()
@click.argument("name", type=str)
@click.option("--description", "-d", help="Profile description")
@click.option("--force", is_flag=True, help="Force overwrite existing profile")
def create_profile(name: str, description: str | None, force: bool) -> None:
    """Create a new security profile with validation."""
    try:
        # Validate input
        if not validate_profile_name(name):
            raise click.ClickException(f"Invalid profile name: {name}")

        # Check for existing profile
        if profile_exists(name) and not force:
            raise click.ClickException(
                f"Profile '{name}' already exists. Use --force to overwrite."
            )

        # Create profile
        profile = create_default_profile(name, description)
        save_profile(profile)

        click.echo(f"✅ Created profile '{name}'")

    except SecurityError as e:
        raise click.ClickException(f"Security error: {e}")
    except ProfileError as e:
        raise click.ClickException(f"Profile error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error creating profile: {e}")
        raise click.ClickException("Internal error occurred")
```

### Pattern Matching (`pattern_matcher.py`)

```python
# Good: Secure pattern matching with comprehensive validation
def matches_pattern(tool_call: ToolCall, pattern: str) -> bool:
    """Match tool call against pattern with security validation."""
    try:
        # Validate inputs
        if not pattern:
            return False

        # Handle universal wildcard
        if pattern == "*":
            return True

        # Parse pattern
        tool_pattern, resource_pattern = parse_pattern(pattern)

        # Match tool
        if not fnmatch.fnmatch(tool_call.tool, tool_pattern):
            return False

        # Extract and match resource
        resource = extract_resource(tool_call)
        matcher = select_matcher(resource_pattern)
        return matcher.matches(resource_pattern, resource)

    except PatternSecurityError:
        logger.warning(f"Security violation in pattern: {pattern}")
        return False
    except Exception as e:
        logger.error(f"Pattern matching error: {e}")
        return False
```

### Profile Management (`profile_loader.py`)

```python
# Good: Robust profile loading with fallback hierarchy
def load_active_profile() -> Profile:
    """Load active profile with comprehensive fallback strategy."""
    try:
        # Try project-specific profile
        if profile := load_project_profile():
            return profile

        # Try home directory profile
        if profile := load_home_profile():
            return profile

        # Fall back to default
        return create_default_profile()

    except Exception as e:
        logger.error(f"Profile loading failed: {e}, using emergency defaults")
        return create_emergency_default_profile()

def load_project_profile() -> Profile | None:
    """Load project-specific profile with error handling."""
    try:
        active_file = Path(".claudeguard/active_profile")
        if not active_file.exists():
            return None

        profile_name = active_file.read_text().strip()
        if not validate_profile_name(profile_name):
            logger.warning(f"Invalid active profile name: {profile_name}")
            return None

        profile_path = resolve_profile_path(profile_name)
        return load_profile_from_path(profile_path)

    except Exception as e:
        logger.warning(f"Failed to load project profile: {e}")
        return None
```

## Documentation Standards

### Code Documentation

All public functions and classes must have comprehensive docstrings:

```python
def evaluate_rules(tool_call: ToolCall, rules: tuple[ProfileRule, ...]) -> MatchResult:
    """Evaluate security rules against a tool call.

    Processes rules in order until the first match is found. Uses fail-safe
    behavior by defaulting to "ask" if no rules match or errors occur.

    Args:
        tool_call: The tool call to evaluate
        rules: Tuple of rules to check in order

    Returns:
        MatchResult containing the action to take and matching rule

    Example:
        >>> tool_call = ToolCall(tool="Edit", input={"file_path": "main.py"})
        >>> rules = (ProfileRule(pattern="Edit(*.py)", action="ask"),)
        >>> result = evaluate_rules(tool_call, rules)
        >>> result.action
        'ask'
    """
```

### API Documentation

Document all public APIs with examples:

```python
class PatternMatcher:
    """Pattern matching engine for security rule evaluation.

    Supports multiple pattern types:
    - Glob patterns: Edit(*.py), Bash(git *)
    - Regex patterns: Edit(/.*\\.py$/)
    - MCP patterns: mcp__server__*, mcp__*

    Example:
        >>> matcher = PatternMatcher()
        >>> tool_call = ToolCall(tool="Edit", input={"file_path": "main.py"})
        >>> matcher.matches(tool_call, "Edit(*.py)")
        True
    """
```

## Release Process

### Version Management

Use semantic versioning (semver):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update Version**
   ```bash
   # Update version in pyproject.toml
   version = "1.2.0"
   ```

2. **Update Changelog**
   ```markdown
   ## [1.2.0] - 2024-01-15

   ### Added
   - Advanced pattern matching with regex support
   - MCP tool integration

   ### Fixed
   - Path traversal vulnerability in profile names
   - Performance issue with large rule sets

   ### Security
   - Added ReDoS protection for regex patterns
   ```

3. **Quality Gates**
   ```bash
   # All tests must pass
   uv run pytest

   # Type checking must pass
   uv run mypy src tests

   # Security scan must pass
   uv run bandit -r src/

   # Performance tests must pass
   uv run pytest -m performance
   ```

4. **Create Release**
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   ```

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Security Issues**: Email security@claudeguard.dev for security concerns

### Contributing Guidelines

1. **Start Small**: Begin with small improvements or bug fixes
2. **Ask Questions**: Don't hesitate to ask for clarification
3. **Follow Standards**: Adhere to code quality and security standards
4. **Be Patient**: Code review process ensures high quality

### Reporting Issues

When reporting issues, include:

1. **Environment**: OS, Python version, claudeguard version
2. **Steps to Reproduce**: Clear steps to reproduce the issue
3. **Expected vs Actual**: What you expected vs what happened
4. **Logs**: Relevant log files or error messages
5. **Security**: Mark security issues as private

### Feature Requests

For feature requests, provide:

1. **Use Case**: Why this feature is needed
2. **Proposed Solution**: How you envision it working
3. **Alternatives**: Other solutions you've considered
4. **Impact**: Who would benefit from this feature

Thank you for contributing to claudeguard! Your efforts help make Claude Code more secure for everyone.
