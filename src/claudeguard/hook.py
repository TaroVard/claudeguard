"""Core hook integration for Claude Code permission system."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claudeguard.models import ToolCall, ToolInput, ToolPattern
from claudeguard.pattern_matcher import PatternMatcher
from claudeguard.profile_loader import ProfileLoader


def find_repo_root() -> Path | None:
    """Find git repository root by looking for .git directory."""
    current_path = Path.cwd()

    while current_path != current_path.parent:
        git_dir = current_path / ".git"
        if git_dir.exists():
            return current_path
        current_path = current_path.parent

    return None


def sanitize_error_message(error_msg: str) -> str:
    """Sanitize error messages to avoid leaking sensitive information."""
    sensitive_patterns = [
        r"/home/[^/\s]+/\.[^/\s]*",
        r"/Users/[^/\s]+/\.[^/\s]*",
        r"\.secret[^/\s]*",
        r"\.ssh[^/\s]*",
        r"\.env[^/\s]*",
        r"\.key[^/\s]*",
        r"password[^/\s]*",
        r"token[^/\s]*",
    ]

    sanitized = error_msg
    for pattern in sensitive_patterns:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)

    return sanitized


@dataclass(frozen=True)
class HookInput:
    """Input received from Claude Code hook system."""

    tool_name: str
    tool_input: dict[str, Any]


@dataclass(frozen=True)
class HookResponse:
    """Response sent back to Claude Code hook system."""

    permission_decision: str
    permission_decision_reason: str
    suppress_output: bool = False


class AuditLogger:
    """Simplified audit logging for claudeguard hook operations."""

    def __init__(self) -> None:
        repo_root = find_repo_root()
        if repo_root:
            self.audit_log_path = repo_root / ".claudeguard" / "audit.log"
        else:
            self.audit_log_path = Path.home() / ".claudeguard" / "audit.log"

        self.audit_log_path.parent.mkdir(exist_ok=True)

    def log_hook_invocation(
        self,
        hook_input: HookInput,
        response: HookResponse,
        matched_rule: str | None,
    ) -> None:
        """Log hook invocation with simplified format."""
        audit_entry = {
            "tool_input": {
                "tool_name": hook_input.tool_name,
                "tool_input": hook_input.tool_input,
            },
            "tool_output": {
                "permission_decision": response.permission_decision,
                "permission_decision_reason": response.permission_decision_reason,
            },
            "matched_rule": matched_rule,
        }

        with open(self.audit_log_path, "a") as f:
            json.dump(audit_entry, f, separators=(",", ":"))
            f.write("\n")


class PermissionEngine:
    """Core permission decision engine."""

    def __init__(self) -> None:
        self.profile_loader = ProfileLoader()
        self.pattern_matcher = PatternMatcher()
        self.audit_logger = AuditLogger()

    def check_permission(self, hook_input: HookInput) -> HookResponse:
        """Make permission decision for tool call."""
        response = None
        matched_rule = None

        try:
            profile = self.profile_loader.load_profile()
            tool_call = self._convert_hook_input_to_tool_call(hook_input)

            for rule in profile.rules:
                pattern = ToolPattern(pattern=rule.pattern, action=rule.action)
                match_result = self.pattern_matcher.match_pattern(pattern, tool_call)

                if match_result.matched:
                    matched_rule = rule.pattern
                    reason = f"claudeguard: Rule matched: {rule.pattern} → {rule.action}"
                    if rule.comment:
                        reason += f" ({rule.comment})"

                    response = HookResponse(
                        permission_decision=rule.action,
                        permission_decision_reason=reason,
                        suppress_output=False,
                    )
                    break

            if not response:
                matched_rule = None
                response = HookResponse(
                    permission_decision="ask",
                    permission_decision_reason=(
                        "claudeguard: No matching rules found (fallback to ask)"
                    ),
                    suppress_output=False,
                )

        except Exception as e:
            sanitized_error = sanitize_error_message(str(e))
            response = HookResponse(
                permission_decision="ask",
                permission_decision_reason=(
                    f"claudeguard error: {sanitized_error} (fail-safe to ask)"
                ),
                suppress_output=False,
            )

        self.audit_logger.log_hook_invocation(hook_input, response, matched_rule)
        return response

    def _convert_hook_input_to_tool_call(self, hook_input: HookInput) -> ToolCall:
        """Convert HookInput to ToolCall for pattern matching."""
        tool_input = ToolInput(data=hook_input.tool_input)
        return ToolCall(name=hook_input.tool_name, input=tool_input)


def parse_hook_input(json_str: str) -> HookInput:
    """Parse JSON input from Claude Code hook system with validation."""
    if not json_str.strip():
        raise ValueError("Empty input")

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    if "tool_name" not in data:
        raise ValueError("tool_name field is required")
    if "tool_input" not in data:
        raise ValueError("tool_input field is required")

    if not isinstance(data["tool_name"], str):
        raise ValueError("tool_name must be a string")
    if not isinstance(data["tool_input"], dict):
        raise ValueError("tool_input must be a dict")

    return HookInput(tool_name=data["tool_name"], tool_input=data["tool_input"])


def read_stdin_input() -> str:
    """Read JSON input from stdin with error handling."""
    try:
        raw_input = sys.stdin.read()
        return raw_input.strip()
    except OSError as e:
        raise ValueError(f"Failed to read from stdin: {e}") from e


def format_hook_response(response: HookResponse) -> str:
    """Format HookResponse as JSON for Claude Code PreToolUse hook."""
    data = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": response.permission_decision,
            "permissionDecisionReason": response.permission_decision_reason,
        }
    }
    return json.dumps(data)


def main() -> None:
    """Main entry point for claudeguard hook."""
    try:
        input_json = sys.stdin.read()
        hook_input = parse_hook_input(input_json)

        engine = PermissionEngine()
        response = engine.check_permission(hook_input)

        output = format_hook_response(response)
        print(output)

        if response.permission_decision == "deny":
            sys.exit(2)
        else:
            sys.exit(0)

    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        error_response = HookResponse(
            permission_decision="ask",
            permission_decision_reason=(
                f"claudeguard error: {sanitized_error} (fail-safe to ask)"
            ),
            suppress_output=False,
        )
        output = format_hook_response(error_response)
        print(output)
        sys.exit(0)


if __name__ == "__main__":
    main()
