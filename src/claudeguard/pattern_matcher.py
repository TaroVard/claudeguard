"""Pattern matching system for claudeguard security rules."""

from __future__ import annotations

import fnmatch
import re
import time
from abc import ABC, abstractmethod

from claudeguard.models import MatchResult, ToolCall, ToolPattern

MAX_REGEX_TIME = 0.1
MAX_REGEX_LENGTH = 1000
MAX_QUANTIFIERS = 20


class ResourceMatcher(ABC):
    """Abstract interface for resource matching strategies."""

    @abstractmethod
    def match_resource(self, pattern: str, actual_resource: str) -> bool:
        """Match a resource pattern against an actual resource.

        Args:
            pattern: The resource pattern to match against
            actual_resource: The actual resource string to test

        Returns:
            True if the pattern matches the resource, False otherwise

        """


class GlobResourceMatcher(ResourceMatcher):
    """Default resource matcher using fnmatch for glob patterns."""

    def match_resource(self, pattern: str, actual_resource: str) -> bool:
        """Match using fnmatch glob patterns with enhanced directory support."""
        if not actual_resource:
            if not pattern:
                return True
            if "*" in pattern or "?" in pattern:
                return False
            return False

        escaped_pattern = self._escape_special_chars(pattern)
        if fnmatch.fnmatch(actual_resource, escaped_pattern):
            return True

        if "**" in pattern and "/" in pattern:
            return self._match_directory_pattern(pattern, actual_resource)

        return False

    def _match_directory_pattern(self, pattern: str, actual_path: str) -> bool:
        """Match directory patterns like 'src/**' against absolute paths."""
        pattern_parts = pattern.split("/")
        path_parts = actual_path.lstrip("/").split("/")

        for i in range(len(path_parts)):
            if self._match_path_segments(pattern_parts, path_parts[i:]):
                return True

        return False

    def _match_path_segments(
        self, pattern_parts: list[str], path_parts: list[str]
    ) -> bool:
        """Match pattern segments against path segments using fnmatch rules."""
        if not pattern_parts:
            return True
        if not path_parts:
            return False

        pattern_part = pattern_parts[0]

        if pattern_part == "**":
            if len(pattern_parts) == 1:
                return True

            remaining_pattern = pattern_parts[1:]
            for j in range(len(path_parts) + 1):
                if self._match_path_segments(remaining_pattern, path_parts[j:]):
                    return True
            return False

        if not fnmatch.fnmatch(path_parts[0], pattern_part):
            return False
        return self._match_path_segments(pattern_parts[1:], path_parts[1:])

    def _escape_special_chars(self, pattern: str) -> str:
        """Escape square brackets to treat them as literal characters."""
        escaped = ""
        for char in pattern:
            if char == "[":
                escaped += "[[]"
            elif char == "]":
                escaped += "[]]"
            else:
                escaped += char
        return escaped


class RegexResourceMatcher(ResourceMatcher):
    """Resource matcher for regex patterns marked by /pattern/ syntax."""

    def match_resource(self, pattern: str, actual_resource: str) -> bool:
        """Match using regex patterns with security validation."""
        if not pattern.startswith("/") or not pattern.endswith("/"):
            return False

        regex_pattern = pattern[1:-1]

        if not self._is_safe_regex(regex_pattern):
            return False

        try:
            start_time = time.time()
            compiled_pattern = re.compile(regex_pattern)
            match_result = compiled_pattern.search(actual_resource) is not None

            if time.time() - start_time > MAX_REGEX_TIME:
                return False

            return match_result
        except re.error:
            return False

    def _is_safe_regex(self, pattern: str) -> bool:
        """Basic validation to prevent regex DoS attacks."""
        dangerous_patterns = [
            r"\(\?\:",
            r"\*\+",
            r"\+\*",
            r"\{\d+,\}\*",
            r"\*\*",
        ]

        for dangerous in dangerous_patterns:
            if re.search(dangerous, pattern):
                return False

        if len(pattern) > MAX_REGEX_LENGTH:
            return False

        quantifier_count = len(re.findall(r"[*+?{]", pattern))
        return not quantifier_count > MAX_QUANTIFIERS


class McpResourceMatcher(ResourceMatcher):
    """Resource matcher for MCP tools using fnmatch on tool names."""

    def match_resource(self, pattern: str, actual_resource: str) -> bool:
        """Match MCP tool patterns against tool names using fnmatch."""
        return fnmatch.fnmatch(actual_resource, pattern)


class PatternMatcher:
    """Matches security patterns against tool calls using Tool(resource) syntax."""

    def __init__(self) -> None:
        """Initialize pattern matcher with strategy matchers."""
        self._glob_matcher = GlobResourceMatcher()
        self._regex_matcher = RegexResourceMatcher()
        self._mcp_matcher = McpResourceMatcher()

    def match_pattern(self, pattern: ToolPattern, tool_call: ToolCall) -> MatchResult:
        """Match a security pattern against a tool call.

        Supports patterns like:
        - Edit(src/main.py) - exact match
        - Edit(*.py) - glob patterns
        - Edit(src/**) - recursive directory patterns
        - Edit(/src/.*/file.py/) - regex patterns (marked by /pattern/)
        - Edit - bare tool name matches any resource
        - mcp__server__tool - exact MCP tool match
        - mcp__server__* - server wildcard
        - mcp__* - cross-server wildcard
        - * - wildcard matching any tool/resource
        """
        resource_extracted = self.extract_resource(tool_call)

        # Handle universal wildcard
        if pattern.pattern == "*":
            return self._create_match_result(
                matched=True,
                pattern_used=pattern.pattern,
                resource_extracted=resource_extracted,
            )

        # Handle bare tool patterns
        if self._is_bare_tool_name(pattern.pattern):
            return self._handle_bare_pattern_match(
                pattern.pattern, tool_call, resource_extracted
            )

        # Handle structured Tool(resource) patterns
        return self._handle_structured_pattern_match(
            pattern, tool_call, resource_extracted
        )

    def _create_match_result(
        self, matched: bool, pattern_used: str | None, resource_extracted: str
    ) -> MatchResult:
        """Create a MatchResult with consistent structure."""
        return MatchResult(
            matched=matched,
            pattern_used=pattern_used,
            resource_extracted=resource_extracted,
        )

    def _handle_bare_pattern_match(
        self, pattern: str, tool_call: ToolCall, resource_extracted: str
    ) -> MatchResult:
        """Handle matching of bare tool name patterns."""
        matched = self._match_bare_pattern(pattern, tool_call.name)
        pattern_used = pattern if matched else None
        return self._create_match_result(
            matched=matched,
            pattern_used=pattern_used,
            resource_extracted=resource_extracted,
        )

    def _handle_structured_pattern_match(
        self, pattern: ToolPattern, tool_call: ToolCall, resource_extracted: str
    ) -> MatchResult:
        """Handle matching of structured Tool(resource) patterns."""
        parsed = self._parse_pattern(pattern.pattern)
        if not parsed:
            return self._create_match_result(
                matched=False, pattern_used=None, resource_extracted=resource_extracted
            )

        tool_name, resource_pattern = parsed

        if not self._match_tool_name(tool_name, tool_call.name):
            return self._create_match_result(
                matched=False, pattern_used=None, resource_extracted=resource_extracted
            )

        resource_matches = self._match_resource(
            resource_pattern, resource_extracted, tool_call.name
        )
        pattern_used = pattern.pattern if resource_matches else None
        return self._create_match_result(
            matched=resource_matches,
            pattern_used=pattern_used,
            resource_extracted=resource_extracted,
        )

    def extract_resource(self, tool_call: ToolCall) -> str:
        """Extract resource string from tool call based on tool type.

        Returns empty string for tools without meaningful resources,
        which allows them to fall back to bare tool name matching.
        """
        input_data = tool_call.input.data

        if tool_call.name in ("Edit", "Read", "Write", "MultiEdit"):
            return str(input_data.get("file_path", ""))
        if tool_call.name == "NotebookEdit":
            return str(input_data.get("notebook_path", ""))

        if tool_call.name == "Bash":
            return str(input_data.get("command", ""))

        if tool_call.name == "Glob":
            return str(input_data.get("pattern", ""))
        if tool_call.name in ("Grep", "LS"):
            return str(input_data.get("path", ""))

        if tool_call.name in ("WebFetch", "WebSearch"):
            return str(input_data.get("url", ""))

        if self._is_mcp_tool(tool_call.name):
            return self._extract_mcp_resource(tool_call)
        return ""

    def _parse_pattern(self, pattern: str) -> tuple[str, str] | None:
        """Parse Tool(resource) pattern into tool name and resource pattern.

        Returns None if pattern is malformed.
        """
        if not pattern or pattern == "*":
            return None

        match = re.match(
            r"^([A-Za-z][A-Za-z0-9_]*(?:__[A-Za-z0-9_*]+)*)\((.*)\)$", pattern
        )
        if not match:
            return None

        tool_name, resource_pattern = match.groups()
        return tool_name, resource_pattern

    def _is_bare_tool_name(self, pattern: str) -> bool:
        """Check if pattern is a bare tool name (no parentheses)."""
        if not pattern or pattern == "*":
            return False
        if self._is_mcp_wildcard_pattern(pattern):
            return True
        return re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", pattern) is not None

    def _match_resource(
        self, resource_pattern: str, actual_resource: str, tool_name: str
    ) -> bool:
        """Match resource pattern against actual resource using strategy pattern."""
        if resource_pattern.startswith("/") and resource_pattern.endswith("/"):
            return self._regex_matcher.match_resource(resource_pattern, actual_resource)
        return self._glob_matcher_with_context(
            resource_pattern, actual_resource, tool_name
        )

    def _glob_matcher_with_context(
        self, resource_pattern: str, actual_resource: str, tool_name: str
    ) -> bool:
        """Glob matching with tool context awareness."""
        if resource_pattern == "*" and not actual_resource:
            return True

        return self._glob_matcher.match_resource(resource_pattern, actual_resource)

    def _is_mcp_tool(self, tool_name: str) -> bool:
        """Check if tool name follows MCP naming convention."""
        return tool_name.startswith("mcp__") and tool_name.count("__") >= 2

    def _is_mcp_wildcard_pattern(self, pattern: str) -> bool:
        """Check if pattern is an MCP wildcard pattern."""
        if "(" in pattern:
            return False
        return (
            pattern == "mcp__*"
            or (pattern.startswith("mcp__") and pattern.endswith("__*"))
            or (pattern.startswith("mcp__") and "*" in pattern and "__" in pattern)
        )

    def _extract_mcp_resource(self, tool_call: ToolCall) -> str:
        """Extract resource from MCP tool call based on common parameter names."""
        input_data = tool_call.input.data

        resource_params = [
            "file_path",
            "table_name",
            "url",
            "output_file",
            "response_file",
            "path",
            "query",
            "name",
            "resource",
        ]

        for param in resource_params:
            if input_data.get(param):
                return str(input_data[param])

        return ""

    def _match_bare_pattern(self, pattern: str, tool_name: str) -> bool:
        """Match bare pattern against tool name, including MCP wildcards."""
        if self._is_mcp_wildcard_pattern(pattern):
            return self._match_mcp_wildcard(pattern, tool_name)
        return pattern == tool_name

    def _match_tool_name(self, pattern_tool: str, actual_tool: str) -> bool:
        """Match tool name pattern against actual tool name."""
        if "*" in pattern_tool:
            return self._match_mcp_wildcard(pattern_tool, actual_tool)
        return pattern_tool == actual_tool

    def _match_mcp_wildcard(self, pattern: str, tool_name: str) -> bool:
        """Match MCP wildcard patterns against tool names."""
        if not self._is_mcp_tool(tool_name):
            return False

        if pattern == "mcp__*":
            return True

        if pattern.endswith("__*"):
            server_pattern = pattern[:-1]
            return tool_name.startswith(server_pattern)

        if pattern.startswith("mcp__") and "*" in pattern:
            return fnmatch.fnmatch(tool_name, pattern)

        return False
