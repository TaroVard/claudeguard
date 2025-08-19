"""Core permission decision logic for claudeguard pattern matching system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from claudeguard.models import (
    Action,
    Profile,
    ProfileRule,
    ToolCall,
    ToolInput,
    ToolPattern,
)
from claudeguard.pattern_matcher import PatternMatcher


@dataclass(frozen=True)
class HookInput:
    """Represents input to the claudeguard hook from Claude Code."""

    tool_name: str
    tool_input: dict[str, Any]


@dataclass(frozen=True)
class PermissionDecision:
    """Result of a permission decision."""

    action: Action
    reason: str
    matched_rule: ProfileRule | None = None


def matches_pattern(pattern: str, hook_input: HookInput) -> bool:
    """Check if a pattern matches against a hook input.

    Args:
        pattern: Pattern string (e.g., "Read(*)", "Bash(git status)")
        hook_input: Hook input containing tool_name and tool_input

    Returns:
        True if pattern matches, False otherwise

    """
    pattern_matcher = PatternMatcher()

    tool_call = _convert_hook_input_to_tool_call(hook_input)
    tool_pattern = ToolPattern(pattern=pattern, action="allow")
    match_result = pattern_matcher.match_pattern(tool_pattern, tool_call)

    return match_result.matched


def make_permission_decision(
    hook_input: HookInput, profile: Profile
) -> PermissionDecision:
    """Make a permission decision for a tool call based on profile rules.

    Args:
        hook_input: Hook input containing tool_name and tool_input
        profile: Profile containing security rules

    Returns:
        PermissionDecision with action and reason

    """
    pattern_matcher = PatternMatcher()

    tool_call = _convert_hook_input_to_tool_call(hook_input)
    for rule in profile.rules:
        tool_pattern = ToolPattern(pattern=rule.pattern, action=rule.action)
        match_result = pattern_matcher.match_pattern(tool_pattern, tool_call)

        if match_result.matched:
            reason = f"Rule matched: {rule.pattern} → {rule.action}"
            if rule.comment:
                reason += f" ({rule.comment})"

            return PermissionDecision(
                action=rule.action, reason=reason, matched_rule=rule
            )

    return PermissionDecision(
        action="ask",
        reason="No matching rules found (default to ask)",
        matched_rule=None,
    )


def _convert_hook_input_to_tool_call(hook_input: HookInput) -> ToolCall:
    """Convert HookInput to ToolCall for pattern matching."""
    tool_input = ToolInput(data=hook_input.tool_input)
    return ToolCall(name=hook_input.tool_name, input=tool_input)
