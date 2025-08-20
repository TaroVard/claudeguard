# claudeguard

**claudeguard** enhances Claude Code with automated security decisions using pattern matching and team-shareable profiles.

## Why claudeguard?

Claude Code's permission prompts are great for security but repetitive for routine tasks. claudeguard automates common decisions while keeping you in control of sensitive operations.

## How it works

**claudeguard** uses the `PreToolUse` Claude Code hook to intercept tool calls and override Claude Code's builtin permission logic

## Features

- **Pattern matching**: `Edit(src/**)`, `Bash(/git status/)`, `Bash(rm -rf*)`
- **Team sharing**: Profiles stored in `.claudeguard/profiles/`
- **Zero config**: Works immediately with sensible rules

## Quick Start

```bash
# Install
uv tool install claudeguard

# Setup in your project
cd your-claude-code-project
claudeguard install

# Use Claude Code normally - claudeguard works in the background
claude
```

## How It Works

claudeguard matches tool calls against rules in `.claudeguard/profiles/default.yaml`:

```yaml
rules:
  - pattern: "Read(*)"
    action: allow
  - pattern: "Edit(*.md)"
    action: allow
  - pattern: "Bash(/git (status|diff)/)"
    action: allow
  - pattern: "Edit(src/**)"
    action: ask
  - pattern: "Bash(rm -rf*)"
    action: deny
  - pattern: "*"
    action: ask
```

First matching rule wins. Actions: `allow`, `ask`, `deny`.

## Commands

- `claudeguard install` - Setup in current project
- `claudeguard status` - Show configuration
- `claudeguard create-profile` - Create new profile
- `claudeguard list-profiles` - List profiles
- `claudeguard switch-profile` - Switch profile
- `claudeguard delete-profile` - Delete profile
- `claudeguard uninstall` - Remove from project

## Pattern Examples

| Pattern | Matches | Action |
|---------|---------|--------|
| `Read(*)` | All file reads | `allow` |
| `Edit(*.md)` | Markdown files | `allow` |
| `Bash(/git (status\|diff)/)` | Safe git commands | `allow` |
| `Edit(src/**)` | Code files | `ask` |
| `Bash(rm -rf*)` | Destructive commands | `deny` |

## Custom Profiles

Create profiles for different security levels:

```yaml
# .claudeguard/profiles/strict.yaml
name: "strict-policy"
description: "Strict security for production"
rules:
  - pattern: "Read(*)"
    action: allow
  - pattern: "Edit(docs/**)"
    action: allow
  - pattern: "Edit(*)"
    action: ask
  - pattern: "Bash(/git (status|diff|log)/)"
    action: allow
  - pattern: "Bash(*)"
    action: deny
  - pattern: "*"
    action: deny
```

## Development

```bash
git clone https://github.com/tarovard/claudeguard
cd claudeguard
uv sync                   # Install dependencies
uv run pre-commit install # Setup git hooks

# Test and lint
uv run pytest            # Run tests
uv run mypy src tests     # Type checking
uv run ruff check --fix . # Format and lint
```

## License

MIT - see [LICENSE](LICENSE) file.

## Contributing

Bug reports and feature requests welcome at [GitHub Issues](https://github.com/tarovard/claudeguard/issues).
