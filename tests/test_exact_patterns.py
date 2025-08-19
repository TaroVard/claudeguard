"""Tests for exact pattern matching without wildcards."""

from __future__ import annotations

import platform

import pytest

from claudeguard.pattern_matcher import PatternMatcher
from tests.factories import (
    make_bash_tool_call,
    make_edit_tool_call,
    make_mcp_tool_call,
    make_read_tool_call,
    make_tool_pattern,
)


@pytest.fixture
def pattern_matcher() -> PatternMatcher:
    return PatternMatcher()


class TestBasicExactMatching:
    """Tests for exact pattern matching."""

    def test_exact_edit_pattern_match(self, pattern_matcher: PatternMatcher):
        """Edit(src/main.py) should match Edit tool call with src/main.py."""
        pattern = make_tool_pattern(pattern="Edit(src/main.py)", action="allow")
        tool_call = make_edit_tool_call(file_path="src/main.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(src/main.py)"
        assert result.resource_extracted == "src/main.py"

    def test_exact_edit_pattern_no_match_different_file(self, pattern_matcher: PatternMatcher):
        """Edit(src/main.py) should not match Edit tool call with different file."""
        pattern = make_tool_pattern(pattern="Edit(src/main.py)", action="allow")
        tool_call = make_edit_tool_call(file_path="src/other.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "src/other.py"

    def test_exact_read_pattern_match(self, pattern_matcher: PatternMatcher):
        """Read(docs/README.md) should match Read tool call with docs/README.md."""
        pattern = make_tool_pattern(pattern="Read(docs/README.md)", action="allow")
        tool_call = make_read_tool_call(file_path="docs/README.md")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Read(docs/README.md)"
        assert result.resource_extracted == "docs/README.md"

    def test_exact_bash_command_match(self, pattern_matcher: PatternMatcher):
        """Bash(git status) should match Bash tool call with git status."""
        pattern = make_tool_pattern(pattern="Bash(git status)", action="allow")
        tool_call = make_bash_tool_call(command="git status")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Bash(git status)"
        assert result.resource_extracted == "git status"

    def test_exact_bash_command_no_match_different_command(self, pattern_matcher: PatternMatcher):
        """Bash(git status) should not match Bash tool call with git diff."""
        pattern = make_tool_pattern(pattern="Bash(git status)", action="allow")
        tool_call = make_bash_tool_call(command="git diff")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "git diff"

    def test_tool_name_mismatch_no_match(self, pattern_matcher: PatternMatcher) -> None:
        """Edit pattern should not match Read tool call."""
        pattern = make_tool_pattern(pattern="Edit(src/main.py)", action="allow")
        tool_call = make_read_tool_call(file_path="src/main.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None


class TestMCPExactMatching:
    """Tests for exact MCP tool pattern matching."""

    def test_exact_mcp_pattern_match(self, pattern_matcher: PatternMatcher):
        """mcp__playwright__browser_console_messages should match exactly."""
        pattern = make_tool_pattern(
            pattern="mcp__playwright__browser_console_messages", action="allow"
        )
        tool_call = make_mcp_tool_call(
            mcp_server="playwright", tool_name="browser_console_messages"
        )

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "mcp__playwright__browser_console_messages"
        assert result.resource_extracted == ""

    def test_exact_mcp_pattern_with_resource_match(self, pattern_matcher: PatternMatcher):
        """mcp__database__query_table(users) should match with resource extraction."""
        pattern = make_tool_pattern(pattern="mcp__database__query_table(users)", action="allow")
        tool_call = make_mcp_tool_call(
            mcp_server="database", tool_name="query_table", table_name="users"
        )

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "mcp__database__query_table(users)"
        assert result.resource_extracted == "users"

    def test_exact_mcp_pattern_no_match_different_server(self, pattern_matcher: PatternMatcher):
        """mcp__playwright__* should not match tools from different MCP server."""
        pattern = make_tool_pattern(
            pattern="mcp__playwright__browser_console_messages", action="allow"
        )
        tool_call = make_mcp_tool_call(mcp_server="database", tool_name="browser_console_messages")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None

    def test_exact_mcp_pattern_no_match_different_tool(self, pattern_matcher: PatternMatcher):
        """Exact MCP pattern should not match different tool from same server."""
        pattern = make_tool_pattern(
            pattern="mcp__playwright__browser_console_messages", action="allow"
        )
        tool_call = make_mcp_tool_call(mcp_server="playwright", tool_name="page_screenshot")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None

    def test_exact_mcp_pattern_no_match_non_mcp_tool(self, pattern_matcher: PatternMatcher):
        """MCP pattern should not match regular Claude Code tools."""
        pattern = make_tool_pattern(
            pattern="mcp__playwright__browser_console_messages", action="allow"
        )
        tool_call = make_edit_tool_call(file_path="test.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None


class TestCaseSensitivity:
    """Tests for case-sensitive pattern matching."""

    def test_case_sensitive_pattern_matching(self, pattern_matcher: PatternMatcher) -> None:
        """Pattern matching should be case sensitive on case-sensitive filesystems."""
        capitalized_pattern = make_tool_pattern(pattern="Edit(src/Main.py)", action="allow")
        lowercase_tool_call = make_edit_tool_call(file_path="src/main.py")

        result = pattern_matcher.match_pattern(capitalized_pattern, lowercase_tool_call)

        # Windows has case-insensitive filesystems, so the pattern will match
        # Unix-like systems are case-sensitive, so the pattern should not match
        if platform.system() == "Windows":
            assert result.matched is True
            assert result.pattern_used == "Edit(src/Main.py)"
        else:
            assert result.matched is False
            assert result.pattern_used is None
        assert result.resource_extracted == "src/main.py"

    def test_case_sensitive_tool_name_matching(self, pattern_matcher: PatternMatcher) -> None:
        """Tool name matching should be case sensitive."""
        lowercase_tool_pattern = make_tool_pattern(pattern="edit(src/main.py)", action="allow")
        capitalized_tool_call = make_edit_tool_call(file_path="src/main.py")

        result = pattern_matcher.match_pattern(lowercase_tool_pattern, capitalized_tool_call)

        assert result.matched is False
        assert result.pattern_used is None

    def test_mcp_pattern_case_sensitivity(self, pattern_matcher: PatternMatcher):
        """MCP patterns should be case sensitive."""
        pattern = make_tool_pattern(pattern="mcp__PLAYWRIGHT__*", action="allow")
        tool_call = make_mcp_tool_call("playwright", "screenshot")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None


class TestNoResourcePatterns:
    """Tests for no-resource pattern support (Edit equivalent to Edit(*))."""

    def test_bare_tool_name_matches_any_resource(self, pattern_matcher: PatternMatcher):
        """Edit (without parentheses) should match any Edit operation."""
        pattern = make_tool_pattern(pattern="Edit", action="ask")
        tool_call = make_edit_tool_call(file_path="any/file.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit"
        assert result.resource_extracted == "any/file.py"

    def test_bare_tool_name_matches_empty_resource(self, pattern_matcher: PatternMatcher):
        """Edit should match Edit operations with empty resources."""
        pattern = make_tool_pattern(pattern="Edit", action="ask")
        tool_call = make_edit_tool_call(file_path="")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit"
        assert result.resource_extracted == ""

    def test_bare_bash_matches_any_command(self, pattern_matcher: PatternMatcher) -> None:
        """Bash (without parentheses) should match any Bash command."""
        pattern = make_tool_pattern(pattern="Bash", action="deny")
        tool_call = make_bash_tool_call(command="rm -rf /")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Bash"
        assert result.resource_extracted == "rm -rf /"

    def test_bare_read_matches_any_file(self, pattern_matcher: PatternMatcher) -> None:
        """Read (without parentheses) should match any Read operation."""
        pattern = make_tool_pattern(pattern="Read", action="allow")
        tool_call = make_read_tool_call(file_path="docs/secrets.md")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Read"
        assert result.resource_extracted == "docs/secrets.md"

    def test_bare_tool_name_no_match_different_tool(self, pattern_matcher: PatternMatcher):
        """Edit should not match Read operations."""
        pattern = make_tool_pattern(pattern="Edit", action="allow")
        tool_call = make_read_tool_call(file_path="any/file.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "any/file.py"

    def test_bare_tool_name_case_sensitive(self, pattern_matcher: PatternMatcher) -> None:
        """Bare tool names should be case sensitive."""
        pattern = make_tool_pattern(pattern="edit", action="allow")
        tool_call = make_edit_tool_call(file_path="any/file.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
