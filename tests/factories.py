"""Test data factories."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime

if sys.version_info >= (3, 11):
    from datetime import UTC
else:
    from datetime import timezone

    UTC = timezone.utc
from typing import Any

from claudeguard.hook import HookInput, HookResponse
from claudeguard.models import (
    Profile,
    ProfileMetadata,
    ProfileRule,
    ToolCall,
    ToolInput,
    ToolName,
    ToolPattern,
)


def make_tool_pattern(**overrides) -> ToolPattern:
    defaults = {"pattern": "Edit(*)", "action": "allow"}
    return ToolPattern(**{**defaults, **overrides})


def make_profile_rule(**overrides) -> ProfileRule:
    defaults = {"pattern": "Edit(*)", "action": "allow", "comment": ""}
    return ProfileRule(**{**defaults, **overrides})


def make_tool_call(tool_name: ToolName = "Edit", **input_overrides) -> ToolCall:
    tool_input = ToolInput(data=input_overrides)
    return ToolCall(name=tool_name, input=tool_input)


def make_edit_tool_call(file_path: str = "src/main.py", **overrides) -> ToolCall:
    input_data = {"file_path": file_path, **overrides}
    return make_tool_call("Edit", **input_data)


def make_read_tool_call(file_path: str = "docs/README.md", **overrides) -> ToolCall:
    input_data = {"file_path": file_path, **overrides}
    return make_tool_call("Read", **input_data)


def make_bash_tool_call(command: str = "git status", **overrides) -> ToolCall:
    input_data = {"command": command, **overrides}
    return make_tool_call("Bash", **input_data)


def make_write_tool_call(
    file_path: str = "output.txt", content: str = "test", **overrides
) -> ToolCall:
    input_data = {"file_path": file_path, "content": content, **overrides}
    return make_tool_call("Write", **input_data)


def make_glob_tool_call(
    pattern: str = "*.py", path: str = "src", **overrides
) -> ToolCall:
    input_data = {"pattern": pattern, "path": path, **overrides}
    return make_tool_call("Glob", **input_data)


def make_grep_tool_call(
    pattern: str = "test", path: str | None = None, glob: str | None = None, **overrides
) -> ToolCall:
    """Create Grep tool call.

    Args:
        pattern: The search pattern
        path: Directory to search in (optional, can be None to use glob instead)
        glob: Glob pattern to filter files (optional, used when path is None)
        **overrides: Additional parameters
    """
    input_data = {"pattern": pattern, **overrides}
    if path is not None:
        input_data["path"] = path
    if glob is not None:
        input_data["glob"] = glob
    return make_tool_call("Grep", **input_data)


def make_mcp_tool_call(
    mcp_server: str, tool_name: str, **resource_overrides
) -> ToolCall:
    mcp_tool_name = f"mcp__{mcp_server}__{tool_name}"
    tool_input = ToolInput(data=resource_overrides)
    return ToolCall(name=mcp_tool_name, input=tool_input)


def make_task_tool_call(content: str = "Test task content", **overrides) -> ToolCall:
    """Create Task tool call - has no meaningful resource."""
    input_data = {"content": content, **overrides}
    return make_tool_call("Task", **input_data)


def make_todo_write_tool_call(
    todos: list[dict[str, str]] | None = None, **overrides
) -> ToolCall:
    """Create TodoWrite tool call - has no meaningful resource."""
    if todos is None:
        todos = [{"content": "Test todo", "status": "pending", "id": "test_id"}]
    input_data = {"todos": todos, **overrides}
    return make_tool_call("TodoWrite", **input_data)


def make_exit_plan_mode_tool_call(**overrides) -> ToolCall:
    """Create ExitPlanMode tool call - has no meaningful resource."""
    input_data = {**overrides}
    return make_tool_call("ExitPlanMode", **input_data)


def make_bash_output_tool_call(bash_id: str = "test_bash_123", **overrides) -> ToolCall:
    """Create BashOutput tool call - has no meaningful resource."""
    input_data = {"bash_id": bash_id, **overrides}
    return make_tool_call("BashOutput", **input_data)


def make_kill_bash_tool_call(shell_id: str = "test_shell_456", **overrides) -> ToolCall:
    """Create KillBash tool call - has no meaningful resource."""
    input_data = {"shell_id": shell_id, **overrides}
    return make_tool_call("KillBash", **input_data)


def make_allow_all_reads() -> ToolPattern:
    return make_tool_pattern(pattern="Read(*)", action="allow")


def make_ask_src_edits() -> ToolPattern:
    return make_tool_pattern(pattern="Edit(src/**)", action="ask")


def make_allow_safe_git() -> ToolPattern:
    return make_tool_pattern(pattern="Bash(git status*)", action="allow")


def make_deny_dangerous_bash() -> ToolPattern:
    return make_tool_pattern(pattern="Bash(rm -rf*)", action="deny")


def make_wildcard_ask() -> ToolPattern:
    return make_tool_pattern(pattern="*", action="ask")


@dataclass(frozen=True)
class Decision:
    """A security decision made by claudeguard."""

    tool_signature: str
    action: str
    rule_pattern: str = "*"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


def make_decision(**overrides) -> Decision:
    defaults = {
        "tool_signature": "Read(/test/file.py)",
        "action": "allow",
        "rule_pattern": "Read(*)",
        "timestamp": datetime.now(UTC),
    }
    return Decision(**{**defaults, **overrides})


def make_claude_settings_content(**overrides) -> dict[str, Any]:
    defaults = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {"type": "command", "command": "claudeguard-hook", "timeout": 30}
                    ],
                }
            ]
        }
    }
    return {**defaults, **overrides}


def create_hook_input(**overrides) -> HookInput:
    defaults = {"tool_name": "Read", "tool_input": {"file_path": "/test/file.py"}}
    return HookInput(**{**defaults, **overrides})


def create_hook_response(**overrides) -> HookResponse:
    defaults = {
        "permission_decision": "allow",
        "permission_decision_reason": "claudeguard: Rule matched: Read(*) → allow",
        "suppress_output": False,
    }
    return HookResponse(**{**defaults, **overrides})


def make_profile_metadata(**overrides) -> ProfileMetadata:
    defaults = {
        "name": "test-profile",
        "description": "Test profile description",
        "version": "1.0",
        "created_by": "claudeguard",
    }
    return ProfileMetadata(**{**defaults, **overrides})


def make_profile(**overrides) -> Profile:
    overrides = dict(overrides)
    if "metadata" in overrides:
        metadata = overrides.pop("metadata")
        if not isinstance(metadata, ProfileMetadata):
            raise TypeError("metadata must be ProfileMetadata instance")
    else:
        metadata_overrides = {}
        for key in ["name", "description", "version", "created_by"]:
            if key in overrides:
                metadata_overrides[key] = overrides.pop(key)
        metadata = make_profile_metadata(**metadata_overrides)

    if "rules" in overrides:
        rules = overrides.pop("rules")
        if isinstance(rules, list):
            rules = tuple(rules)
        elif not isinstance(rules, tuple):
            rules = (rules,) if rules is not None else ()
    else:
        rules = (make_profile_rule(pattern="Read(*)", action="allow"),)

    return Profile(metadata=metadata, rules=rules)


def make_restrictive_profile(**overrides) -> Profile:
    defaults = {
        "name": "restrictive",
        "description": "Restrictive security profile",
        "rules": [
            ProfileRule(pattern="Bash(rm -rf *)", action="deny"),
            # All other operations default to ask (no rules match)
        ],
    }
    return make_profile(**{**defaults, **overrides})


def make_permissive_profile(**overrides) -> Profile:
    defaults = {
        "name": "permissive",
        "description": "Permissive security profile",
        "rules": [
            ProfileRule(pattern="Read(*)", action="allow"),
            ProfileRule(pattern="Edit(*)", action="allow"),
            ProfileRule(pattern="Bash(*)", action="allow"),
        ],
    }
    return make_profile(**{**defaults, **overrides})
