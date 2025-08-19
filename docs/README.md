# claudeguard Documentation

Welcome to the claudeguard documentation! This comprehensive guide covers everything from user-facing features to technical implementation details.

## Documentation Structure

### 📋 Features Documentation (`features/`)
User-facing documentation for getting the most out of claudeguard.

- **[Command Line Interface](features/command-line-interface.md)** - Complete CLI reference with examples
- **[Security Rules & Pattern Matching](features/security-rules.md)** - How to create and manage security rules
- **[Pattern Examples](features/pattern-examples.md)** - Real-world pattern examples and use cases
- **[Team Collaboration](features/team-collaboration.md)** - Sharing security profiles across teams

### 🔧 Technical Documentation (`technical/`)
In-depth technical documentation for contributors and advanced users.

- **[Architecture Overview](technical/architecture.md)** - System design and component interactions
- **[Pattern Matching Engine](technical/pattern-matching-engine.md)** - Deep dive into pattern matching algorithms
- **[Testing Strategy](technical/testing-strategy.md)** - Comprehensive testing approach and quality standards
- **[Contributing Guide](technical/contributing.md)** - How to contribute to claudeguard development

## Quick Start Guide

### 1. Installation
```bash
# Install claudeguard
pip install claudeguard

# Initialize in your Claude Code project
claudeguard install
```

### 2. Basic Usage
```bash
# Check status
claudeguard status

# List available profiles
claudeguard list-profiles

# Create custom profile
claudeguard create-profile development --description "Dev environment rules"

# Switch profiles
claudeguard switch-profile development
```

### 3. Understanding Security Rules
claudeguard uses pattern-based security rules with three actions:

- **`allow`** - Automatically permit the operation
- **`ask`** - Prompt user for permission (default)
- **`deny`** - Block the operation entirely

```yaml
# Example security profile
name: my-profile
description: Custom security rules
rules:
  - pattern: "Read(*)"
    action: allow
    comment: "Reading files is safe"

  - pattern: "Edit(src/**)"
    action: ask
    comment: "Source code changes need review"

  - pattern: "Bash(rm -rf*)"
    action: deny
    comment: "Prevent dangerous deletions"
```

## Key Features

### 🔒 Intelligent Security
- **Smart Pattern Matching** - Supports glob, regex, and MCP tool patterns
- **Fail-Safe Design** - Always defaults to secure behavior on errors
- **Zero Configuration** - Works immediately with sensible defaults

### 👥 Team Collaboration
- **Git-Based Sharing** - Security profiles committed to version control
- **Environment Profiles** - Different rules for dev, staging, production
- **Audit Logging** - Complete trail of all permission decisions

### ⚡ High Performance
- **< 100ms Response** - Permission decisions complete quickly
- **Pattern Caching** - Optimized pattern matching with caching
- **Minimal Overhead** - Lightweight integration with Claude Code

### 🛡️ Security-First
- **DoS Protection** - Regex patterns protected against ReDoS attacks
- **Input Validation** - Comprehensive validation of all user inputs
- **Path Security** - Protection against directory traversal attacks

## Common Use Cases

### Development Teams
```yaml
name: development
description: Permissive rules for active development
rules:
  # Allow safe operations
  - pattern: "Read(*)"
    action: allow
  - pattern: "Bash(uv run pytest*)"
    action: allow

  # Review code changes
  - pattern: "Edit(src/**)"
    action: ask

  # Block dangerous operations
  - pattern: "Bash(rm -rf*)"
    action: deny
```

### Production Environments
```yaml
name: production
description: Highly restrictive for production
rules:
  # Only allow reading
  - pattern: "Read(*)"
    action: allow
  - pattern: "LS(*)"
    action: allow

  # Deny all modifications
  - pattern: "Edit(*)"
    action: deny
  - pattern: "Bash(*)"
    action: deny
```

### Code Review Process
```yaml
name: code-review
description: Balanced permissions for code review
rules:
  # Allow reading and searching
  - pattern: "Read(*)"
    action: allow
  - pattern: "Grep(*)"
    action: allow

  # Allow safe git operations
  - pattern: "Bash(git diff*)"
    action: allow
  - pattern: "Bash(git log*)"
    action: allow

  # Ask for edits during review
  - pattern: "Edit(*)"
    action: ask
```

## Pattern Syntax Reference

### Basic Patterns
- `*` - Universal wildcard (matches everything)
- `Edit` - Tool-level pattern (any Edit operation)
- `Edit(*.py)` - File pattern with wildcards
- `Edit(src/**)` - Directory recursion

### Advanced Patterns
- `Edit(/.*\.py$/)` - Regex patterns (marked with `/`)
- `mcp__server__*` - MCP tool patterns
- `Bash(git status|git diff)` - Command patterns

### Security Actions
- `allow` - Auto-approve (safe operations)
- `ask` - Prompt user (default behavior)
- `deny` - Block entirely (dangerous operations)

## Best Practices

### 1. Start Conservative
Begin with restrictive rules and gradually relax based on your workflow needs.

### 2. Use Comments
Document why each rule exists for team understanding:
```yaml
- pattern: "Edit(src/core/**)"
  action: ask
  comment: "Core module changes need extra scrutiny"
```

### 3. Test Thoroughly
Test profiles in development before deploying to production environments.

### 4. Monitor Audit Logs
Review `.claudeguard/audit.log` regularly to understand usage patterns and refine rules.

### 5. Share with Team
Commit profiles to git so the entire team uses consistent security policies.

## Troubleshooting

### Common Issues

**Hook not working after installation**
```bash
# Check installation status
claudeguard status

# Restart Claude Code
# claudeguard hooks are loaded on startup
```

**Profile not loading**
```bash
# Check active profile
claudeguard status

# List available profiles
claudeguard list-profiles

# Switch to working profile
claudeguard switch-profile default
```

**Permission denied errors**
```bash
# Check file permissions
ls -la .claudeguard/

# Fix permissions if needed
chmod 644 .claudeguard/profiles/*.yaml
```

### Getting Help

- **Documentation**: Start with relevant docs above
- **GitHub Issues**: Report bugs and request features
- **Audit Logs**: Check `.claudeguard/audit.log` for decision history
- **Verbose Mode**: Use `claudeguard status --verbose` for detailed information

## Contributing

claudeguard is open source and welcomes contributions! See our [Contributing Guide](technical/contributing.md) for:

- Development environment setup
- Code quality standards
- Security guidelines
- Testing requirements
- Pull request process

## What's Next?

1. **For Users**: Start with [Command Line Interface](features/command-line-interface.md)
2. **For Teams**: Read [Team Collaboration](features/team-collaboration.md)
3. **For Developers**: Check [Architecture Overview](technical/architecture.md)
4. **For Contributors**: See [Contributing Guide](technical/contributing.md)

---

**Need help?** Check the relevant documentation sections above, or create an issue on GitHub for additional support.
