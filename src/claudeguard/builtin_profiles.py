"""Built-in profile definitions for claudeguard."""

from typing import Any


def create_default_profile_data(
    profile_name: str = "default", description: str | None = None
) -> dict[str, Any]:
    """Create default profile data with comprehensive security rules."""
    return {
        "name": profile_name,
        "description": description or "Default security profile for claudeguard",
        "version": "1.0",
        "rules": [
            # Safe read-only operations
            {"pattern": "Read(*)", "action": "allow"},
            {"pattern": "LS(*)", "action": "allow"},
            {"pattern": "Glob(*)", "action": "allow"},
            {"pattern": "Grep(*)", "action": "allow"},
            {"pattern": "TodoWrite(*)", "action": "allow"},
            {"pattern": "Task(*)", "action": "allow"},
            {"pattern": "BashOutput(*)", "action": "allow"},
            {"pattern": "KillBash(*)", "action": "allow"},
            # Safe git operations
            {"pattern": "Bash(git status)", "action": "allow"},
            {"pattern": "Bash(git diff*)", "action": "allow"},
            {"pattern": "Bash(git log*)", "action": "allow"},
            {"pattern": "Bash(git show*)", "action": "allow"},
            {"pattern": "Bash(git branch*)", "action": "allow"},
            # Safe development tools
            {"pattern": "Bash(uv run pytest*)", "action": "allow"},
            {"pattern": "Bash(uv run mypy*)", "action": "allow"},
            {"pattern": "Bash(uv run ruff*)", "action": "allow"},
            {"pattern": "Bash(uv run pre-commit*)", "action": "allow"},
            {"pattern": "Bash(pytest*)", "action": "allow"},
            {"pattern": "Bash(mypy*)", "action": "allow"},
            {"pattern": "Bash(ruff*)", "action": "allow"},
            # Safe shell commands
            {"pattern": "Bash(ls*)", "action": "allow"},
            {"pattern": "Bash(pwd)", "action": "allow"},
            {"pattern": "Bash(which *)", "action": "allow"},
            {"pattern": "Bash(cat *)", "action": "allow"},
            {"pattern": "Bash(head *)", "action": "allow"},
            {"pattern": "Bash(tail *)", "action": "allow"},
            {"pattern": "Bash(grep*)", "action": "allow"},
            {"pattern": "Bash(find*)", "action": "allow"},
            {"pattern": "Bash(wc *)", "action": "allow"},
            {"pattern": "Bash(sort *)", "action": "allow"},
            {"pattern": "Bash(uniq *)", "action": "allow"},
            {"pattern": "Bash(awk *)", "action": "allow"},
            {"pattern": "Bash(sed *)", "action": "allow"},
            # File creation and multi-edit operations
            {"pattern": "Write(*)", "action": "ask"},
            {"pattern": "MultiEdit(*)", "action": "ask"},
            {"pattern": "NotebookEdit(*)", "action": "ask"},
            # Network operations
            {"pattern": "WebFetch(*)", "action": "ask"},
            {"pattern": "WebSearch(*)", "action": "ask"},
            # MCP tools and catch-all
            {"pattern": "mcp__*", "action": "ask"},
            {"pattern": "*", "action": "ask"},
        ],
    }


def create_minimal_profile_data() -> dict[str, Any]:
    """Create minimal restrictive profile.

    Allows only essential read-only operations.
    """
    return {
        "name": "minimal",
        "description": "Minimal restrictive policy allowing only essential read-only operations",
        "version": "1.0",
        "rules": [
            {"pattern": "Read(*)", "action": "allow"},
            {"pattern": "Glob(*)", "action": "allow"},
            {"pattern": "Grep(*)", "action": "allow"},
            {"pattern": "LS(*)", "action": "allow"},
            {"pattern": "TodoWrite(*)", "action": "allow"},
            {
                "pattern": "*",
                "action": "ask",
                "comment": "Minimal profile default - ask for everything else",
            },
        ],
    }


def create_yolo_profile_data() -> dict[str, Any]:
    """Create YOLO profile that allows everything - for development/testing only."""
    return {
        "name": "yolo",
        "description": "YOLO profile - allows everything (use with caution)",
        "version": "1.0",
        "rules": [
            {"pattern": "*", "action": "allow"},
        ],
    }
