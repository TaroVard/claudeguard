"""Default security rules for claudeguard profiles."""

from __future__ import annotations

from claudeguard.models import ProfileRule


def get_default_rules() -> tuple[ProfileRule, ...]:
    """Return the default security rules used when no profile is found.

    These rules mirror Claude Code's default behavior: safe operations are allowed
    while potentially risky operations require user confirmation.
    """
    return (
        # Safe read-only operations
        ProfileRule(pattern="Read(*)", action="allow"),
        ProfileRule(pattern="LS(*)", action="allow"),
        ProfileRule(pattern="Glob(*)", action="allow"),
        ProfileRule(pattern="Grep(*)", action="allow"),
        ProfileRule(pattern="TodoWrite(*)", action="allow"),
        ProfileRule(pattern="Edit(*.md)", action="allow"),
        ProfileRule(pattern="Edit(*.txt)", action="allow"),
        ProfileRule(pattern="Edit(*.rst)", action="allow"),
        ProfileRule(pattern="Edit(CHANGELOG*)", action="allow"),
        ProfileRule(pattern="Edit(README*)", action="allow"),
        # Safe git operations
        ProfileRule(pattern="Bash(git status)", action="allow"),
        ProfileRule(pattern="Bash(git diff*)", action="allow"),
        ProfileRule(pattern="Bash(git log*)", action="allow"),
        ProfileRule(pattern="Bash(git show*)", action="allow"),
        ProfileRule(pattern="Bash(git branch*)", action="allow"),
        # Safe development tools
        ProfileRule(pattern="Bash(uv run pytest*)", action="allow"),
        ProfileRule(pattern="Bash(uv run mypy*)", action="allow"),
        ProfileRule(pattern="Bash(uv run ruff*)", action="allow"),
        ProfileRule(pattern="Bash(uv run pre-commit*)", action="allow"),
        ProfileRule(pattern="Bash(pytest*)", action="allow"),
        ProfileRule(pattern="Bash(mypy*)", action="allow"),
        ProfileRule(pattern="Bash(ruff*)", action="allow"),
        # Safe shell commands
        ProfileRule(pattern="Bash(ls*)", action="allow"),
        ProfileRule(pattern="Bash(pwd)", action="allow"),
        ProfileRule(pattern="Bash(which *)", action="allow"),
        ProfileRule(pattern="Bash(cat *)", action="allow"),
        ProfileRule(pattern="Bash(head *)", action="allow"),
        ProfileRule(pattern="Bash(tail *)", action="allow"),
        ProfileRule(pattern="Bash(grep*)", action="allow"),
        ProfileRule(pattern="Bash(find*)", action="allow"),
        ProfileRule(pattern="Bash(wc *)", action="allow"),
        ProfileRule(pattern="Bash(sort *)", action="allow"),
        ProfileRule(pattern="Bash(uniq *)", action="allow"),
        ProfileRule(pattern="Bash(awk *)", action="allow"),
        ProfileRule(pattern="Bash(sed *)", action="allow"),
        # Planning and analysis tools
        ProfileRule(pattern="Task(*)", action="allow"),
        ProfileRule(pattern="ExitPlanMode(*)", action="allow"),
        ProfileRule(pattern="BashOutput(*)", action="allow"),
        ProfileRule(pattern="KillBash(*)", action="allow"),
        # Code modifications
        ProfileRule(pattern="Edit(*.py)", action="ask"),
        ProfileRule(pattern="Edit(*.js)", action="ask"),
        ProfileRule(pattern="Edit(*.ts)", action="ask"),
        ProfileRule(pattern="Edit(*.json)", action="ask"),
        ProfileRule(pattern="Edit(*.yaml)", action="ask"),
        ProfileRule(pattern="Edit(*.yml)", action="ask"),
        ProfileRule(pattern="Edit(*.toml)", action="ask"),
        ProfileRule(pattern="Edit(src/**)", action="ask"),
        # File creation and operations
        ProfileRule(pattern="Write(*)", action="ask"),
        ProfileRule(pattern="MultiEdit(*)", action="ask"),
        ProfileRule(pattern="NotebookEdit(*)", action="ask"),
        # Network operations
        ProfileRule(pattern="WebFetch(*)", action="ask"),
        ProfileRule(pattern="WebSearch(*)", action="ask"),
        # Git state changes
        ProfileRule(pattern="Bash(git add*)", action="ask"),
        ProfileRule(pattern="Bash(git commit*)", action="ask"),
        ProfileRule(pattern="Bash(git push*)", action="ask"),
        # Package management
        ProfileRule(pattern="Bash(npm install*)", action="ask"),
        ProfileRule(pattern="Bash(pip install*)", action="ask"),
        ProfileRule(pattern="Bash(uv add*)", action="ask"),
        # File system modifications
        ProfileRule(pattern="Bash(mkdir*)", action="ask"),
        ProfileRule(pattern="Bash(mv *)", action="ask"),
        ProfileRule(pattern="Bash(cp *)", action="ask"),
        ProfileRule(pattern="Bash(chmod*)", action="ask"),
        # Dangerous operations
        ProfileRule(pattern="Bash(sudo *)", action="deny"),
        ProfileRule(pattern="Bash(rm -rf*)", action="deny"),
        ProfileRule(pattern="Bash(chmod 777*)", action="deny"),
        # MCP tools and default
        ProfileRule(pattern="mcp__*", action="ask"),
        ProfileRule(pattern="*", action="ask"),
    )
