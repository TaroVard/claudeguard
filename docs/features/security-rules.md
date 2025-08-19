# Security Rules & Pattern Matching

claudeguard uses intelligent pattern matching to automatically handle Claude Code permissions based on your security rules.

## Rule Structure

Each security rule consists of three parts:

```yaml
rules:
  - pattern: "Edit(src/**)"      # What to match
    action: ask                  # What to do
    comment: "Source code edits" # Why this rule exists
```

### Actions

- **`allow`** - Automatically permit the operation (no prompt)
- **`ask`** - Prompt the user for permission (default behavior)
- **`deny`** - Block the operation entirely

## Pattern Syntax

### Basic Patterns

**Exact matches** - Match specific files or commands:
```yaml
- pattern: "Edit(src/main.py)"      # Exact file
  action: ask

- pattern: "Bash(git status)"       # Exact command
  action: allow
```

**Tool-level patterns** - Match any use of a tool:
```yaml
- pattern: "Read"                   # Any file read
  action: allow

- pattern: "Edit"                   # Any file edit
  action: ask
```

**Universal wildcard** - Match everything:
```yaml
- pattern: "*"                      # All tools and operations
  action: ask
```

### File Patterns

**Glob patterns** with wildcards:
```yaml
- pattern: "Edit(*.py)"             # Any Python file
  action: ask

- pattern: "Edit(*.md)"             # Any Markdown file
  action: allow

- pattern: "Read(tests/**)"         # Any file in tests directory
  action: allow
```

**Directory recursion**:
```yaml
- pattern: "Edit(src/**)"           # All files under src/
  action: ask

- pattern: "Glob(docs/**)"          # Search in docs directory
  action: allow
```

### Command Patterns

**Git operations**:
```yaml
- pattern: "Bash(git status)"       # Check git status
  action: allow

- pattern: "Bash(git diff*)"        # Any git diff command
  action: allow

- pattern: "Bash(git push*)"        # Git push operations
  action: ask
```

**Development tools**:
```yaml
- pattern: "Bash(uv run pytest*)"  # Run tests
  action: allow

- pattern: "Bash(uv run mypy*)"     # Type checking
  action: allow

- pattern: "Bash(npm run build)"    # Build commands
  action: ask
```

### Advanced Patterns

**Regex patterns** (marked with `/` delimiters):
```yaml
- pattern: "Edit(/src/.*/test.*\\.py/)" # Test files in src subdirs
  action: allow

- pattern: "Bash(/rm -rf .*/)"          # Any rm -rf command
  action: deny
```

**MCP tool patterns** (third-party tools):
```yaml
- pattern: "mcp__server__tool"      # Specific MCP tool
  action: ask

- pattern: "mcp__server__*"         # All tools from server
  action: ask

- pattern: "mcp__*"                 # All MCP tools
  action: ask
```

## Default Security Rules

claudeguard comes with 16 carefully crafted default rules:

### Auto-Allow (Safe Operations)
```yaml
# Reading and searching - always safe
- pattern: "Read(*)"
  action: allow
  comment: "File reading is always safe"

- pattern: "LS(*)"
  action: allow
  comment: "Directory listing is safe"

- pattern: "Glob(*)"
  action: allow
  comment: "File pattern searches are safe"

- pattern: "Grep(*)"
  action: allow
  comment: "Text searches are safe"

# Git information commands
- pattern: "Bash(git status)"
  action: allow
  comment: "Git status is informational"

- pattern: "Bash(git diff*)"
  action: allow
  comment: "Git diff is read-only"

- pattern: "Bash(git log*)"
  action: allow
  comment: "Git log is read-only"

# Development tools
- pattern: "Bash(uv run pytest*)"
  action: allow
  comment: "Running tests is safe"

- pattern: "Bash(uv run mypy*)"
  action: allow
  comment: "Type checking is safe"

- pattern: "Bash(uv run ruff*)"
  action: allow
  comment: "Linting is safe"

# Safe edits
- pattern: "Edit(*.md)"
  action: allow
  comment: "Markdown files are safe to edit"

- pattern: "Edit(*.txt)"
  action: allow
  comment: "Text files are safe to edit"
```

### Ask Permission (Code Changes)
```yaml
# Source code requires review
- pattern: "Edit(src/**)"
  action: ask
  comment: "Source code changes need review"

- pattern: "Edit(*.py)"
  action: ask
  comment: "Python files need review"
```

### Deny (Dangerous Operations)
```yaml
# Dangerous file operations
- pattern: "Bash(rm -rf*)"
  action: deny
  comment: "Recursive deletion is dangerous"

- pattern: "Bash(sudo *)"
  action: deny
  comment: "Sudo commands are dangerous"

- pattern: "Bash(chmod 777*)"
  action: deny
  comment: "Making files world-writable is dangerous"
```

### Fallback
```yaml
# Everything else asks for permission
- pattern: "*"
  action: ask
  comment: "Ask for permission on unknown operations"
```

## Rule Precedence

Rules are processed **in order** from top to bottom. The **first matching rule** determines the action.

```yaml
rules:
  # This rule matches first for README.md
  - pattern: "Edit(README.md)"
    action: allow

  # This rule would never match README.md due to order
  - pattern: "Edit(*.md)"
    action: ask

  # This rule matches other markdown files
  - pattern: "Edit(docs/*.md)"
    action: allow
```

**Best practice**: Place more specific rules before general ones.

## Creating Custom Rules

### Development Profile Example
```yaml
name: development
description: Permissive rules for development work
rules:
  # Allow all safe operations
  - pattern: "Read(*)"
    action: allow
  - pattern: "LS(*)"
    action: allow
  - pattern: "Grep(*)"
    action: allow

  # Allow development tools
  - pattern: "Bash(uv run *)"
    action: allow
    comment: "Allow all uv commands in dev"

  # Allow test file edits
  - pattern: "Edit(test*/**)"
    action: allow
    comment: "Test files can be freely edited"

  # Ask for source code changes
  - pattern: "Edit(src/**)"
    action: ask
    comment: "Review source changes"

  # Deny dangerous operations
  - pattern: "Bash(rm -rf*)"
    action: deny
    comment: "No recursive deletion"

  # Default fallback
  - pattern: "*"
    action: ask
```

### Production Profile Example
```yaml
name: production
description: Restrictive rules for production environments
rules:
  # Only allow reading
  - pattern: "Read(*)"
    action: allow
  - pattern: "LS(*)"
    action: allow

  # Allow safe git operations
  - pattern: "Bash(git status)"
    action: allow
  - pattern: "Bash(git log*)"
    action: allow

  # Deny all edits
  - pattern: "Edit(*)"
    action: deny
    comment: "No file modifications in production"

  # Deny all bash commands except git
  - pattern: "Bash(*)"
    action: deny
    comment: "No command execution in production"

  # Default deny
  - pattern: "*"
    action: deny
```

## Testing Rules

Use the pattern matching to test your rules:

```python
from claudeguard.pattern_matcher import matches_pattern

# Test if a pattern matches
result = matches_pattern("Edit(src/main.py)", "Edit(src/**)")
print(result)  # True

# Test rule evaluation
tool_call = ToolCall(tool="Edit", input={"file_path": "src/main.py"})
result = evaluate_rules(tool_call, your_rules)
print(result.action)  # "ask" or "allow" or "deny"
```

## Security Best Practices

1. **Start restrictive** - Begin with conservative rules and gradually relax
2. **Use comments** - Document why each rule exists
3. **Test thoroughly** - Verify rules work as expected before deploying
4. **Review regularly** - Update rules as your project evolves
5. **Share with team** - Commit profiles to git for consistency
6. **Monitor audit logs** - Review `.claudeguard/audit.log` for unexpected patterns

## Next Steps

- Create custom profiles with `claudeguard create-profile`
- Test rules in development before using in production
- Share profiles with your team through git
- Monitor the audit log for security insights
- See [Pattern Examples](pattern-examples.md) for more complex patterns
