# Pattern Examples

This guide provides practical examples of claudeguard security patterns for common development scenarios.

## File Operations

### Source Code Protection
```yaml
# Python development
- pattern: "Edit(*.py)"
  action: ask
  comment: "Review Python file changes"

- pattern: "Edit(src/**/*.py)"
  action: ask
  comment: "Extra scrutiny for source files"

# Allow test file edits
- pattern: "Edit(test_*.py)"
  action: allow
  comment: "Test files are safe to modify"

- pattern: "Edit(tests/**)"
  action: allow
  comment: "Test directory modifications allowed"
```

### Configuration Files
```yaml
# Allow documentation edits
- pattern: "Edit(*.md)"
  action: allow
  comment: "Documentation is safe to edit"

- pattern: "Edit(docs/**)"
  action: allow
  comment: "Documentation directory"

# Ask for config changes
- pattern: "Edit(*.json)"
  action: ask
  comment: "Configuration files need review"

- pattern: "Edit(*.yaml)"
  action: ask
  comment: "YAML configs need review"

- pattern: "Edit(.env*)"
  action: ask
  comment: "Environment files are sensitive"
```

### File System Operations
```yaml
# Safe file operations
- pattern: "Read(*)"
  action: allow
  comment: "Reading is always safe"

- pattern: "LS(*)"
  action: allow
  comment: "Directory listing is safe"

- pattern: "Glob(*.py)"
  action: allow
  comment: "Finding Python files is safe"

# Dangerous operations
- pattern: "Edit(/etc/**)"
  action: deny
  comment: "No system file modifications"

- pattern: "Edit(/usr/**)"
  action: deny
  comment: "No system directory edits"
```

## Command Patterns

### Git Operations
```yaml
# Safe git commands
- pattern: "Bash(git status)"
  action: allow
  comment: "Check repository status"

- pattern: "Bash(git diff*)"
  action: allow
  comment: "View changes safely"

- pattern: "Bash(git log*)"
  action: allow
  comment: "View commit history"

- pattern: "Bash(git show*)"
  action: allow
  comment: "Show commit details"

# Commands needing review
- pattern: "Bash(git add*)"
  action: ask
  comment: "Staging files for commit"

- pattern: "Bash(git commit*)"
  action: ask
  comment: "Creating commits"

- pattern: "Bash(git push*)"
  action: ask
  comment: "Publishing changes"

# Dangerous git operations
- pattern: "Bash(git reset --hard*)"
  action: deny
  comment: "Hard reset loses work"

- pattern: "Bash(git clean -fd*)"
  action: deny
  comment: "Force clean removes files"
```

### Development Tools
```yaml
# Python tools
- pattern: "Bash(python -m pytest*)"
  action: allow
  comment: "Running tests is safe"

- pattern: "Bash(uv run pytest*)"
  action: allow
  comment: "UV pytest execution"

- pattern: "Bash(uv run mypy*)"
  action: allow
  comment: "Type checking with mypy"

- pattern: "Bash(uv run ruff*)"
  action: allow
  comment: "Code formatting and linting"

# Node.js tools
- pattern: "Bash(npm test)"
  action: allow
  comment: "Running npm tests"

- pattern: "Bash(npm run build)"
  action: ask
  comment: "Building requires review"

- pattern: "Bash(npm install*)"
  action: ask
  comment: "Installing packages affects dependencies"

# Build operations
- pattern: "Bash(make test)"
  action: allow
  comment: "Running make tests"

- pattern: "Bash(make build)"
  action: ask
  comment: "Building artifacts"
```

### System Commands
```yaml
# Safe information commands
- pattern: "Bash(ls*)"
  action: allow
  comment: "Directory listing"

- pattern: "Bash(cat *)"
  action: allow
  comment: "Reading files (prefer Read tool)"

- pattern: "Bash(grep*)"
  action: allow
  comment: "Text searching (prefer Grep tool)"

- pattern: "Bash(find*)"
  action: allow
  comment: "Finding files (prefer Glob tool)"

# Process management
- pattern: "Bash(ps*)"
  action: allow
  comment: "View running processes"

- pattern: "Bash(kill *)"
  action: ask
  comment: "Terminating processes needs review"

# Dangerous commands
- pattern: "Bash(rm -rf*)"
  action: deny
  comment: "Recursive deletion is dangerous"

- pattern: "Bash(sudo *)"
  action: deny
  comment: "Elevated privileges denied"

- pattern: "Bash(chmod 777*)"
  action: deny
  comment: "World-writable files are insecure"
```

## Web & Network Operations

### Web Fetching
```yaml
# Allow documentation sites
- pattern: "WebFetch(https://docs.*)"
  action: allow
  comment: "Documentation sites are safe"

- pattern: "WebFetch(https://github.com/*)"
  action: allow
  comment: "GitHub is generally safe"

# Ask for other sites
- pattern: "WebFetch(*)"
  action: ask
  comment: "External web requests need review"

# Search operations
- pattern: "WebSearch(*)"
  action: ask
  comment: "Web searches may expose queries"
```

## Language-Specific Patterns

### Python Projects
```yaml
# Package management
- pattern: "Bash(pip install*)"
  action: ask
  comment: "Package installation affects environment"

- pattern: "Bash(uv add*)"
  action: ask
  comment: "Adding dependencies"

- pattern: "Bash(uv remove*)"
  action: ask
  comment: "Removing dependencies"

# Virtual environments
- pattern: "Bash(uv sync)"
  action: allow
  comment: "Syncing dependencies is safe"

# Python execution
- pattern: "Bash(python *.py)"
  action: ask
  comment: "Running Python scripts"

# Testing and quality
- pattern: "Edit(pyproject.toml)"
  action: ask
  comment: "Project configuration changes"

- pattern: "Edit(requirements*.txt)"
  action: ask
  comment: "Dependency changes need review"
```

### JavaScript/Node.js Projects
```yaml
# Package management
- pattern: "Bash(npm install)"
  action: ask
  comment: "Installing dependencies"

- pattern: "Bash(yarn install)"
  action: ask
  comment: "Yarn package installation"

# Configuration files
- pattern: "Edit(package.json)"
  action: ask
  comment: "Package configuration is critical"

- pattern: "Edit(tsconfig.json)"
  action: ask
  comment: "TypeScript configuration"

- pattern: "Edit(.eslintrc*)"
  action: allow
  comment: "Linting config is safe"

# Build and test
- pattern: "Bash(npm run test)"
  action: allow
  comment: "Running tests"

- pattern: "Bash(npm run build)"
  action: ask
  comment: "Building artifacts"
```

### Rust Projects
```yaml
# Cargo operations
- pattern: "Bash(cargo test)"
  action: allow
  comment: "Running Rust tests"

- pattern: "Bash(cargo check)"
  action: allow
  comment: "Type checking Rust code"

- pattern: "Bash(cargo build)"
  action: ask
  comment: "Building Rust project"

- pattern: "Bash(cargo add*)"
  action: ask
  comment: "Adding Rust dependencies"

# Configuration
- pattern: "Edit(Cargo.toml)"
  action: ask
  comment: "Rust project configuration"

- pattern: "Edit(src/**/*.rs)"
  action: ask
  comment: "Rust source code changes"
```

## Environment-Specific Profiles

### Development Environment
```yaml
name: development
description: Permissive rules for active development
rules:
  # Allow most read operations
  - pattern: "Read(*)"
    action: allow
  - pattern: "LS(*)"
    action: allow
  - pattern: "Glob(*)"
    action: allow
  - pattern: "Grep(*)"
    action: allow

  # Allow development tools
  - pattern: "Bash(uv run *)"
    action: allow
    comment: "All uv commands in development"

  - pattern: "Bash(git status|git diff*|git log*)"
    action: allow
    comment: "Safe git operations"

  # Allow test and doc edits
  - pattern: "Edit(test*/**)"
    action: allow
  - pattern: "Edit(docs/**)"
    action: allow
  - pattern: "Edit(*.md)"
    action: allow

  # Ask for source changes
  - pattern: "Edit(src/**)"
    action: ask
    comment: "Source code needs review"

  # Still deny dangerous operations
  - pattern: "Bash(rm -rf*)"
    action: deny
  - pattern: "Bash(sudo *)"
    action: deny

  # Default ask
  - pattern: "*"
    action: ask
```

### CI/CD Environment
```yaml
name: ci-cd
description: Automated build and test environment
rules:
  # Allow all read operations
  - pattern: "Read(*)"
    action: allow
  - pattern: "LS(*)"
    action: allow
  - pattern: "Glob(*)"
    action: allow

  # Allow build tools
  - pattern: "Bash(uv run pytest*)"
    action: allow
  - pattern: "Bash(uv run mypy*)"
    action: allow
  - pattern: "Bash(uv build)"
    action: allow

  # Allow git operations for CI
  - pattern: "Bash(git*)"
    action: allow
    comment: "CI needs git access"

  # Deny all edits (CI shouldn't modify files)
  - pattern: "Edit(*)"
    action: deny
    comment: "CI should not modify files"

  # Deny dangerous commands
  - pattern: "Bash(rm -rf*)"
    action: deny
  - pattern: "Bash(sudo *)"
    action: deny

  # Ask for everything else
  - pattern: "*"
    action: ask
```

### Production Environment
```yaml
name: production
description: Highly restrictive rules for production
rules:
  # Only allow reading
  - pattern: "Read(*)"
    action: allow
  - pattern: "LS(*)"
    action: allow

  # Allow safe git info
  - pattern: "Bash(git status)"
    action: allow
  - pattern: "Bash(git log*)"
    action: allow

  # Deny all modifications
  - pattern: "Edit(*)"
    action: deny
    comment: "No file modifications in production"

  # Deny all command execution
  - pattern: "Bash(*)"
    action: deny
    comment: "No command execution in production"

  # Deny everything else
  - pattern: "*"
    action: deny
    comment: "Production environment is read-only"
```

## Advanced Pattern Techniques

### Regex Patterns
```yaml
# Match test files with regex
- pattern: "Edit(/.*test.*\\.py$/)"
  action: allow
  comment: "Python test files (regex)"

# Match version files
- pattern: "Edit(/.*version.*\\.(py|json|yaml)$/)"
  action: ask
  comment: "Version files need careful review"

# Match temporary files
- pattern: "Edit(/tmp\\/.*$/)"
  action: allow
  comment: "Temporary files are safe"
```

### MCP Tool Patterns
```yaml
# Specific MCP tools
- pattern: "mcp__filesystem__read"
  action: allow
  comment: "MCP file reading"

- pattern: "mcp__database__query"
  action: ask
  comment: "Database queries need review"

# Server-wide patterns
- pattern: "mcp__github__*"
  action: ask
  comment: "All GitHub MCP operations"

- pattern: "mcp__*"
  action: ask
  comment: "All MCP tools require permission"
```

### Complex Conditional Logic
```yaml
# Allow edits in development branch
- pattern: "Edit(*)"
  action: allow
  comment: "Development branch allows edits"
  condition: "git_branch == 'development'"

# Stricter rules on main branch
- pattern: "Edit(src/**)"
  action: deny
  comment: "No direct edits to main branch"
  condition: "git_branch == 'main'"
```

## Testing Your Patterns

Always test patterns before deploying:

1. **Create test profile**:
   ```bash
   claudeguard create-profile test-patterns
   ```

2. **Test specific patterns**:
   ```python
   from claudeguard.pattern_matcher import matches_pattern

   # Test your pattern
   matches_pattern("Edit(src/main.py)", "Edit(src/**)")  # True
   ```

3. **Use development profile first**:
   ```bash
   claudeguard switch-profile test-patterns
   # Test with Claude Code
   claudeguard switch-profile production  # Only when confident
   ```

4. **Monitor audit logs**:
   ```bash
   tail -f .claudeguard/audit.log
   ```

## Next Steps

- Start with [Security Rules](security-rules.md) for basic concepts
- Use the [Command Line Interface](command-line-interface.md) to manage profiles
- Create environment-specific profiles for your workflow
- Share profiles with your team through git
- Monitor audit logs to refine your patterns over time
