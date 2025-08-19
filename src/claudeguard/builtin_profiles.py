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
            {"pattern": "Read(*)", "action": "allow"},
            {"pattern": "Edit(*.md)", "action": "allow"},
            {"pattern": "Edit(*.txt)", "action": "allow"},
            {"pattern": "Bash(git status)", "action": "allow"},
            {"pattern": "Bash(git diff)", "action": "allow"},
            {"pattern": "Bash(git log*)", "action": "allow"},
            {
                "pattern": "Edit(src/**)",
                "action": "ask",
                "comment": "Glob patterns work on file paths",
            },
            {"pattern": "Edit(*.py)", "action": "ask"},
            {"pattern": "Bash(git push*)", "action": "ask"},
            {
                "pattern": "Bash(pip install*)",
                "action": "ask",
                "comment": "Wildcards match command arguments",
            },
            {"pattern": "Bash(rm -rf*)", "action": "deny"},
            {"pattern": "Bash(sudo *)", "action": "deny"},
            {
                "pattern": "Bash(chmod 777*)",
                "action": "deny",
                "comment": "Specific dangerous patterns can be blocked",
            },
            {"pattern": "*", "action": "ask"},
        ],
    }


def create_minimal_profile_data() -> dict[str, Any]:
    """Create minimal restrictive profile.

    Allows only essential read-only operations.
    """
    return {
        "name": "minimal",
        "description": ("Minimal restrictive policy allowing only essential read-only operations"),
        "version": "1.0",
        "rules": [
            # Allow essential read-only Claude tools
            {"pattern": "Read(*)", "action": "allow"},
            {"pattern": "Glob(*)", "action": "allow"},
            {"pattern": "Grep(*)", "action": "allow"},
            {"pattern": "LS(*)", "action": "allow"},
            {"pattern": "TodoWrite(*)", "action": "allow"},
            # Allow safe git and basic commands
            {"pattern": "Bash(git status)", "action": "allow"},
            {"pattern": "Bash(git diff)", "action": "allow"},
            {"pattern": "Bash(git log*)", "action": "allow"},
            {"pattern": "Bash(ls*)", "action": "allow"},
            {"pattern": "Bash(pwd)", "action": "allow"},
            {"pattern": "Bash(which *)", "action": "allow"},
            {"pattern": "Bash(uv run pytest*)", "action": "allow"},
            {"pattern": "Bash(uv run mypy*)", "action": "allow"},
            # Ask for external operations and file modifications
            {"pattern": "Task(*)", "action": "ask"},
            {"pattern": "WebFetch(*)", "action": "ask"},
            {"pattern": "WebSearch(*)", "action": "ask"},
            {"pattern": "Edit(*)", "action": "ask"},
            {"pattern": "MultiEdit(*)", "action": "ask"},
            {"pattern": "Write(*)", "action": "ask"},
            # Ask for git state changes
            {"pattern": "Bash(git add*)", "action": "ask"},
            {"pattern": "Bash(git commit*)", "action": "ask"},
            {"pattern": "Bash(git push*)", "action": "ask"},
            {"pattern": "Bash(git pull*)", "action": "ask"},
            {"pattern": "Bash(git merge*)", "action": "ask"},
            {"pattern": "Bash(git checkout*)", "action": "ask"},
            # Catch-all for other bash commands
            {
                "pattern": "Bash(*)",
                "action": "ask",
                "comment": "Fallback rule - comes before package installs",
            },
            # Block package installations
            {"pattern": "Bash(npm install*)", "action": "deny"},
            {"pattern": "Bash(yarn add*)", "action": "deny"},
            {"pattern": "Bash(pip install*)", "action": "deny"},
            {"pattern": "Bash(cargo install*)", "action": "deny"},
            {"pattern": "Bash(uv add*)", "action": "deny"},
            # Block dangerous operations
            {"pattern": "Bash(sudo *)", "action": "deny"},
            {"pattern": "Bash(rm -rf*)", "action": "deny"},
            {"pattern": "Bash(sudo rm*)", "action": "deny"},
            {"pattern": "Bash(chmod 777*)", "action": "deny"},
            {"pattern": "Bash(chmod -R 777*)", "action": "deny"},
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
