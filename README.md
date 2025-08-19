# claudeguard

**claudeguard** enhances Claude Code with intelligent pattern matching and team-shareable security profiles for consistent, automated permission decisions.

## Why claudeguard?

Claude Code's interactive permission system ensures security but can be repetitive for routine operations. claudeguard builds on this foundation by providing automated pattern-based decisions for common workflows while maintaining full security for sensitive operations. It seamlessly integrates with Claude Code's permission system to give you the best of both worlds: security when you need it, automation when you don't.

## Features

- **Reliable pattern matching**: `Edit(src/**)`, `Bash(/git (status|diff)/)`, `Bash(rm -rf*)`
- **Smart defaults**: Safe operations auto-allowed, dangerous operations denied
- **Team sharing**: Security policies committed to git in `.claudeguard/profiles/`
- **Zero config**: Works immediately with sensible rules
- **Full transparency**: See exactly which rule matched and why

## Quick Start

### Installation

```bash
# Install as a tool (recommended)
uv tool install claudeguard

# Or add to your project
uv add claudeguard

# Or use pip
pip install claudeguard
```

### Setup

```bash
cd your-claude-code-project
claudeguard install    # Configures Claude Code hooks and initializes profiles
```

### Usage

Just use Claude Code normally - claudeguard works transparently in the background!

```bash
claude  # Enhanced with automated permission decisions
```

## How It Works

claudeguard uses pattern matching to automatically make permission decisions:

```yaml
# .claudeguard/profiles/default.yaml
rules:
  - pattern: "Read(*)"                    # Allow all file reads
    action: allow
  - pattern: "Edit(*.md)"                 # Allow markdown edits
    action: allow
  - pattern: "Bash(/git (status|diff)/)"  # Allow safe git commands (regex)
    action: allow
  - pattern: "Edit(src/**)"               # Ask before editing code
    action: ask
  - pattern: "Bash(rm -rf*)"              # Block dangerous commands
    action: deny
  - pattern: "*"                          # Ask for everything else
    action: ask
```

When Claude Code requests a tool permission, claudeguard:
1. Matches the operation against your rules (first match wins)
2. Returns `allow`, `deny`, or `ask` back to Claude Code's permission system
3. Shows debug info: "Rule matched: Read(*) → allow"

## Commands

- `claudeguard install` - Install hooks and initialize claudeguard in current project
- `claudeguard status` - Show current configuration
- `claudeguard create-profile` - Create a new security profile
- `claudeguard list-profiles` - List available security profiles
- `claudeguard switch-profile` - Switch to a different security profile
- `claudeguard delete-profile` - Delete a security profile
- `claudeguard uninstall` - Remove claudeguard hook from Claude Code

## Pattern Examples

| Pattern | Matches | Typical Action |
|---------|---------|----------------|
| `Read(*)` | All file reads | `allow` |
| `Edit(src/**)` | Edit files in src/ | `ask` |
| `Edit(*.md)` | Edit markdown files | `allow` |
| `Bash(/git (status\|diff)/)` | Safe git commands (regex) | `allow` |
| `Bash(rm -rf*)` | Destructive rm commands | `deny` |
| `Bash(sudo *)` | All sudo commands | `deny` |
| `*` | Everything else | `ask` |

## Team Workflow

1. Project lead runs `claudeguard install` and customizes `.claudeguard/profiles/default.yaml`
2. Commit profile: `git add .claudeguard && git commit -m "Add claudeguard security profile"`
3. Team members clone repo and run `claudeguard install`
4. Everyone gets consistent, reliable permissions

## Advanced Usage

### Custom Profiles

```yaml
# .claudeguard/profiles/default.yaml
name: "strict-policy"
description: "Strict security for production code"
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

### Debug Output

claudeguard shows exactly why each decision was made:

```
claudeguard: Rule matched: Bash(/git (status|diff)/) → allow (Safe git operations)
claudeguard: Rule matched: Edit(src/**) → ask (Code changes should be reviewed)
claudeguard: Rule matched: Bash(rm -rf*) → deny (Destructive operations blocked)
```

## Security Design

- **Fail-safe**: Always fails to "ask", never to "allow"
- **Input validation**: All tool calls validated and sanitized
- **Audit trail**: All decisions logged with reasons
- **Least privilege**: Minimal default permissions
- **Team oversight**: Policies reviewed and committed to git

## Development

```bash
git clone https://github.com/tarovard/claudeguard
cd claudeguard
uv sync                    # Install dependencies

# Setup pre-commit hooks (recommended)
uv run pre-commit install  # Install git hooks for automatic code quality

# Development commands
uv run pytest             # Run tests
uv run mypy src tests      # Type checking
uv run ruff check --fix .  # Format and lint

# Pre-commit will automatically run on git commit, or manually:
uv run pre-commit run --all-files  # Run all hooks manually
```

## License

MIT - see [LICENSE](LICENSE) file.

## Contributing

Bug reports and feature requests welcome at [GitHub Issues](https://github.com/tarovard/claudeguard/issues).
