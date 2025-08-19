"""Default security rules for claudeguard profiles."""

from __future__ import annotations

from claudeguard.models import ProfileRule


def get_default_rules() -> tuple[ProfileRule, ...]:
    """Return the default security rules used when no profile is found."""
    return (
        ProfileRule(
            pattern="Read(*)",
            action="allow",
            comment="Reading files is generally safe",
        ),
        ProfileRule(
            pattern="LS(*)",
            action="allow",
            comment="Listing directory contents is safe",
        ),
        ProfileRule(
            pattern="Glob(*)",
            action="allow",
            comment="File pattern matching is safe",
        ),
        ProfileRule(
            pattern="Grep(*)",
            action="allow",
            comment="Searching file contents is safe",
        ),
        ProfileRule(
            pattern="Edit(*.md)",
            action="allow",
            comment="Editing markdown files is generally safe",
        ),
        ProfileRule(
            pattern="Edit(*.txt)",
            action="allow",
            comment="Editing text files is generally safe",
        ),
        ProfileRule(
            pattern="Bash(git status)",
            action="allow",
            comment="Git status is safe",
        ),
        ProfileRule(
            pattern="Bash(git diff)",
            action="allow",
            comment="Git diff is safe",
        ),
        ProfileRule(
            pattern="Bash(git log*)",
            action="allow",
            comment="Git log operations are safe",
        ),
        ProfileRule(
            pattern="Bash(uv run pytest *)",
            action="allow",
            comment="Running tests is generally safe",
        ),
        ProfileRule(
            pattern="Bash(uv run mypy *)",
            action="allow",
            comment="Type checking is safe",
        ),
        ProfileRule(
            pattern="Bash(uv run ruff *)",
            action="allow",
            comment="Code linting and formatting is safe",
        ),
        ProfileRule(
            pattern="Bash(uv run python3 *)",
            action="allow",
            comment="Running Python scripts via uv is generally safe",
        ),
        ProfileRule(
            pattern="Bash(grep*)",
            action="allow",
            comment="Grep commands are safe",
        ),
        ProfileRule(
            pattern="Bash(find*)",
            action="allow",
            comment="Find commands are safe",
        ),
        ProfileRule(
            pattern="Bash(sed *)",
            action="allow",
            comment="Text processing commands are safe",
        ),
        ProfileRule(
            pattern="Edit(src/**)",
            action="ask",
            comment="Code changes should be reviewed",
        ),
        ProfileRule(
            pattern="Edit(*.py)",
            action="ask",
            comment="Python file changes should be reviewed",
        ),
        ProfileRule(
            pattern="Bash(git push*)",
            action="ask",
            comment="Git push operations should be confirmed",
        ),
        ProfileRule(
            pattern="Bash(rm -rf*)",
            action="deny",
            comment="Destructive file operations are blocked",
        ),
        ProfileRule(
            pattern="*",
            action="ask",
            comment="Default rule: ask user for permission",
        ),
    )
