# Contributing to claudeguard

Thank you for your interest in contributing to claudeguard! We welcome contributions of all kinds.

## Ways to Contribute

- 🐛 **Bug Reports** - Help us identify and fix issues
- 💡 **Feature Requests** - Suggest new functionality
- 📖 **Documentation** - Improve our docs and examples
- 🧪 **Testing** - Add test cases and improve quality
- 💻 **Code** - Submit bug fixes and new features

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/yourusername/claudeguard.git
cd claudeguard
```

### 2. Set Up Development Environment

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and set up pre-commit hooks
uv sync --all-extras --dev
uv run pre-commit install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 4. Make Changes

Follow our development workflow:

- **TDD Required**: Write failing tests first, then implement
- **Type Safety**: All code must pass `mypy --strict`
- **Code Quality**: Use Ruff for formatting and linting
- **Comprehensive Testing**: Write thorough tests

### 5. Run Quality Checks

```bash
# Run the full test suite
uv run pytest

# Type checking (must pass with zero warnings)
uv run mypy --strict src tests

# Code formatting and linting
uv run ruff check --fix .
uv run ruff format .

# Security scanning
uv run bandit -c pyproject.toml -r src/
```

### 6. Submit Pull Request

- Push your branch to your fork
- Create a pull request against the main branch
- Fill out the PR template completely
- Ensure all CI checks pass

## Development Standards

### Code Style

- **Python Conventions**: Follow PEP 8 and our Python conventions in `specs/python-conventions.md`
- **Type Hints**: All functions must have complete type annotations
- **Immutable Data**: Use `@dataclass(frozen=True)`, `NamedTuple`, or `TypedDict`
- **No Comments**: Code should be self-documenting through clear naming
- **Pure Functions**: Minimize side effects, maximize composability

### Testing Requirements

- **Behavior-Focused**: Test what the code does, not how it does it
- **Factory Patterns**: Use factories from `tests/factories.py` for test data
- **Comprehensive Testing**: Write thorough tests
- **Fast Tests**: Tests should run quickly and independently

```python
# Good test example
def test_pattern_matcher_allows_safe_read_operations():
    matcher = create_pattern_matcher(rules=[
        Rule(pattern="Read(*)", action=Action.ALLOW)
    ])

    result = matcher.match(ToolCall(tool="Read", resource="file.txt"))

    assert result.action == Action.ALLOW
    assert "Read(*)" in result.reason
```

### Security Guidelines

claudeguard is a security tool, so we follow strict practices:

- **Defensive Security Only**: We build tools that protect, never attack
- **Input Validation**: All external inputs must be validated and typed
- **Fail-Safe Design**: Always fail to "ask", never to "allow"
- **No Secrets**: Never hardcode credentials or sensitive data
- **Audit Trail**: All security decisions must be transparent

## Project Structure

```
claudeguard/
├── src/claudeguard/          # Production code (TDD-developed)
├── tests/                # Comprehensive test suite
├── docs/                 # Documentation
├── specs/                # Project specifications
└── .github/              # GitHub workflows and templates
```

## Issue Guidelines

### Bug Reports

Use our bug report template and include:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Relevant logs or error messages

### Feature Requests

- Describe the problem you're trying to solve
- Explain your proposed solution
- Consider alternatives and trade-offs
- Think about security implications

## Pull Request Process

1. **Follow the Template**: Fill out our PR template completely
2. **Single Purpose**: One feature/fix per PR
3. **Test Quality**: Write comprehensive, behavior-focused tests
4. **Quality Gates**: All CI checks must pass
5. **Documentation**: Update docs if needed
6. **Security Review**: Consider security implications

## Code Review Process

- PRs require at least one approving review
- Reviewers check for:
  - Correct TDD practices
  - Type safety and code quality
  - Security best practices
  - Test quality and behavior focus
  - Clear, self-documenting code

## Getting Help

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/tarovard/claudeguard/issues)
- 📖 **Documentation**: Check the `docs/` directory
- 📋 **Specifications**: Review `specs/` for detailed requirements

## Recognition

Contributors are recognized in:
- GitHub contributor graphs
- Release notes for significant contributions
- PROJECT_CONTRIBUTORS.md (for ongoing contributors)

Thank you for helping make claudeguard better! 🚀
