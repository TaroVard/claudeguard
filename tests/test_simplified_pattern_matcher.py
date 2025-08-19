"""Comprehensive tests for simplified pattern matcher behavior.

This test suite defines the expected behavior for the refactored pattern matcher
that will support only three pattern types:
1. Glob patterns (default) - using fnmatch
2. Regex patterns - marked by /pattern/
3. MCP patterns - for MCP tool matching

Tests focus on BEHAVIOR, not implementation details.
These tests will initially FAIL as they describe the simplified system.
"""

from __future__ import annotations

from claudeguard.pattern_matcher import PatternMatcher
from tests.factories import (
    make_bash_tool_call,
    make_edit_tool_call,
    make_mcp_tool_call,
    make_read_tool_call,
    make_tool_pattern,
    make_write_tool_call,
)


class TestGlobPatternMatching:
    """Test glob pattern matching as the default behavior using fnmatch."""

    def test_exact_file_path_match(self):
        """Should match exact file paths."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(src/main.py)")
        tool_call = make_edit_tool_call("src/main.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(src/main.py)"
        assert result.resource_extracted == "src/main.py"

    def test_simple_wildcard_file_matching(self):
        """Should match files using simple wildcards."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(*.py)")
        tool_call = make_edit_tool_call("main.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(*.py)"
        assert result.resource_extracted == "main.py"

    def test_directory_wildcard_matching(self):
        """Should match directory patterns with wildcards."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(src/*)")
        tool_call = make_edit_tool_call("src/utils.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(src/*)"
        assert result.resource_extracted == "src/utils.py"

    def test_recursive_directory_matching(self):
        """Should match recursive directory patterns."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(src/**)")
        tool_call = make_edit_tool_call("src/utils/helper.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(src/**)"
        assert result.resource_extracted == "src/utils/helper.py"

    def test_bash_command_glob_matching(self):
        """Should match bash commands using glob patterns."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Bash(git *)")
        tool_call = make_bash_tool_call("git status")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Bash(git *)"
        assert result.resource_extracted == "git status"

    def test_glob_pattern_no_match(self):
        """Should not match when glob pattern doesn't match resource."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(*.py)")
        tool_call = make_edit_tool_call("main.js")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "main.js"

    def test_tool_name_mismatch(self):
        """Should not match when tool name doesn't match."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(*.py)")
        tool_call = make_read_tool_call("main.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "main.py"


class TestRegexPatternMatching:
    """Test regex pattern matching marked by /pattern/ syntax."""

    def test_simple_regex_pattern(self):
        """Should match using regex when pattern starts and ends with /."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(/src.*\\.py/)")
        tool_call = make_edit_tool_call("src/main.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(/src.*\\.py/)"
        assert result.resource_extracted == "src/main.py"

    def test_regex_with_special_characters(self):
        """Should handle regex special characters correctly."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Bash(/git (status|diff|log)/)")
        tool_call = make_bash_tool_call("git status")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Bash(/git (status|diff|log)/)"
        assert result.resource_extracted == "git status"

    def test_regex_case_sensitive_matching(self):
        """Should perform case-sensitive regex matching."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(/[A-Z].*\\.py/)")
        tool_call = make_edit_tool_call("Main.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(/[A-Z].*\\.py/)"
        assert result.resource_extracted == "Main.py"

    def test_regex_no_match(self):
        """Should not match when regex pattern doesn't match resource."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(/\\.js$/)")
        tool_call = make_edit_tool_call("main.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "main.py"

    def test_invalid_regex_should_not_match(self):
        """Should handle invalid regex patterns gracefully."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(/[invalid/)")
        tool_call = make_edit_tool_call("test.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "test.py"


class TestMCPPatternMatching:
    """Test MCP tool pattern matching."""

    def test_exact_mcp_tool_match(self):
        """Should match exact MCP tool names."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="mcp__filesystem__read_file")
        tool_call = make_mcp_tool_call("filesystem", "read_file", file_path="test.txt")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "mcp__filesystem__read_file"
        assert result.resource_extracted == "test.txt"

    def test_mcp_server_wildcard_matching(self):
        """Should match MCP tools using server wildcards."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="mcp__filesystem__*")
        tool_call = make_mcp_tool_call("filesystem", "write_file", file_path="output.txt")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "mcp__filesystem__*"
        assert result.resource_extracted == "output.txt"

    def test_mcp_universal_wildcard(self):
        """Should match any MCP tool using universal MCP wildcard."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="mcp__*")
        tool_call = make_mcp_tool_call("database", "query", table_name="users")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "mcp__*"
        assert result.resource_extracted == "users"

    def test_mcp_tool_with_resource_pattern(self):
        """Should match MCP tools with resource patterns."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="mcp__filesystem__read_file(*.txt)")
        tool_call = make_mcp_tool_call("filesystem", "read_file", file_path="config.txt")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "mcp__filesystem__read_file(*.txt)"
        assert result.resource_extracted == "config.txt"

    def test_mcp_tool_no_match_wrong_server(self):
        """Should not match MCP tools from different servers."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="mcp__database__*")
        tool_call = make_mcp_tool_call("filesystem", "read_file", file_path="test.txt")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "test.txt"

    def test_regular_tool_not_matching_mcp_pattern(self):
        """Should not match regular tools against MCP patterns."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="mcp__*")
        tool_call = make_edit_tool_call("test.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "test.py"


class TestUniversalWildcard:
    """Test universal wildcard * behavior."""

    def test_universal_wildcard_matches_any_tool(self):
        """Should match any tool call with universal wildcard."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="*")
        tool_call = make_edit_tool_call("any/file.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "*"
        assert result.resource_extracted == "any/file.py"

    def test_universal_wildcard_matches_bash(self):
        """Should match bash commands with universal wildcard."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="*")
        tool_call = make_bash_tool_call("rm -rf dangerous")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "*"
        assert result.resource_extracted == "rm -rf dangerous"

    def test_universal_wildcard_matches_mcp_tools(self):
        """Should match MCP tools with universal wildcard."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="*")
        tool_call = make_mcp_tool_call("server", "tool", resource="data")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "*"
        assert result.resource_extracted == "data"


class TestBareToolNames:
    """Test bare tool names matching any resource."""

    def test_bare_tool_name_matches_any_resource(self):
        """Should match any resource when using bare tool name."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit")
        tool_call = make_edit_tool_call("any/path/file.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit"
        assert result.resource_extracted == "any/path/file.py"

    def test_bare_tool_name_matches_empty_resource(self):
        """Should match even when resource is empty."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Read")
        tool_call = make_read_tool_call("")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Read"
        assert result.resource_extracted == ""

    def test_bare_tool_name_wrong_tool_no_match(self):
        """Should not match when tool name is different."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit")
        tool_call = make_read_tool_call("test.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "test.py"

    def test_bare_mcp_tool_matching(self):
        """Should match bare MCP tool names."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="mcp__filesystem__read_file")
        tool_call = make_mcp_tool_call("filesystem", "read_file", file_path="any.txt")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "mcp__filesystem__read_file"
        assert result.resource_extracted == "any.txt"


class TestStructuredPatternSyntax:
    """Test Tool(resource) pattern syntax."""

    def test_structured_pattern_exact_match(self):
        """Should parse and match structured Tool(resource) patterns."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Write(output.txt)")
        tool_call = make_write_tool_call("output.txt")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Write(output.txt)"
        assert result.resource_extracted == "output.txt"

    def test_structured_pattern_with_glob(self):
        """Should handle glob patterns inside structured syntax."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Read(docs/*.md)")
        tool_call = make_read_tool_call("docs/README.md")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Read(docs/*.md)"
        assert result.resource_extracted == "docs/README.md"

    def test_structured_pattern_with_regex(self):
        """Should handle regex patterns inside structured syntax."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Bash(/git .*/)")
        tool_call = make_bash_tool_call("git commit -m 'test'")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Bash(/git .*/)"
        assert result.resource_extracted == "git commit -m 'test'"

    def test_structured_pattern_empty_resource(self):
        """Should handle empty resource patterns."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit()")
        tool_call = make_edit_tool_call("")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit()"
        assert result.resource_extracted == ""

    def test_malformed_structured_pattern(self):
        """Should handle malformed structured patterns gracefully."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(unclosed")
        tool_call = make_edit_tool_call("test.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "test.py"


class TestResourceExtraction:
    """Test resource extraction from different tool types."""

    def test_file_tools_extract_file_path(self):
        """Should extract file_path from file operation tools."""
        matcher = PatternMatcher()

        edit_call = make_edit_tool_call("src/main.py")
        assert matcher.extract_resource(edit_call) == "src/main.py"

        read_call = make_read_tool_call("docs/README.md")
        assert matcher.extract_resource(read_call) == "docs/README.md"

        write_call = make_write_tool_call("output.txt")
        assert matcher.extract_resource(write_call) == "output.txt"

    def test_bash_tools_extract_command(self):
        """Should extract command from Bash tools."""
        matcher = PatternMatcher()
        bash_call = make_bash_tool_call("git status")

        assert matcher.extract_resource(bash_call) == "git status"

    def test_mcp_tools_extract_primary_resource(self):
        """Should extract primary resource parameter from MCP tools."""
        matcher = PatternMatcher()

        # Test file_path extraction
        mcp_call = make_mcp_tool_call("filesystem", "read", file_path="test.txt")
        assert matcher.extract_resource(mcp_call) == "test.txt"

        # Test table_name extraction when file_path not present
        mcp_call = make_mcp_tool_call("database", "query", table_name="users")
        assert matcher.extract_resource(mcp_call) == "users"

    def test_unknown_tool_returns_empty_resource(self):
        """Should return empty string for unknown tool types."""
        matcher = PatternMatcher()
        from tests.factories import make_tool_call

        unknown_call = make_tool_call("UnknownTool", some_param="value")
        assert matcher.extract_resource(unknown_call) == ""


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error scenarios."""

    def test_empty_pattern_no_match(self):
        """Should handle empty patterns gracefully."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="")
        tool_call = make_edit_tool_call("test.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "test.py"

    def test_whitespace_only_pattern_no_match(self):
        """Should handle whitespace-only patterns."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="   ")
        tool_call = make_edit_tool_call("test.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "test.py"

    def test_pattern_with_special_characters(self):
        """Should handle patterns with special characters in filenames."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(*-file[1].py)")
        tool_call = make_edit_tool_call("test-file[1].py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(*-file[1].py)"
        assert result.resource_extracted == "test-file[1].py"

    def test_case_sensitive_tool_name_matching(self):
        """Should perform case-sensitive tool name matching."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="edit(*)")  # lowercase
        tool_call = make_edit_tool_call("test.py")  # Edit tool

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "test.py"

    def test_missing_input_data_empty_resource(self):
        """Should handle missing input data gracefully."""
        matcher = PatternMatcher()
        from tests.factories import make_tool_call

        # Tool call with empty input data
        tool_call = make_tool_call("Edit")  # No file_path provided
        pattern = make_tool_pattern(pattern="Edit(*)")

        result = matcher.match_pattern(pattern, tool_call)

        # Should match since "*" universally matches any resource including none
        assert result.matched is True
        assert result.pattern_used == "Edit(*)"
        assert result.resource_extracted == ""


class TestPatternMatcherIntegrationScenarios:
    """Integration tests for realistic usage scenarios."""

    def test_security_rule_matching_scenario(self):
        """Should match patterns in realistic security rule scenarios."""
        matcher = PatternMatcher()

        # Allow all reads
        allow_reads = make_tool_pattern(pattern="Read(*)", action="allow")
        read_call = make_read_tool_call("src/config.py")
        result = matcher.match_pattern(allow_reads, read_call)
        assert result.matched is True
        assert result.pattern_used == "Read(*)"

        # Deny dangerous bash commands
        deny_rm = make_tool_pattern(pattern="Bash(rm -rf*)", action="deny")
        dangerous_call = make_bash_tool_call("rm -rf /important/files")
        result = matcher.match_pattern(deny_rm, dangerous_call)
        assert result.matched is True
        assert result.pattern_used == "Bash(rm -rf*)"

        # Allow safe git commands using regex
        allow_git = make_tool_pattern(pattern="Bash(/git (status|diff|log)/)", action="allow")
        git_call = make_bash_tool_call("git status")
        result = matcher.match_pattern(allow_git, git_call)
        assert result.matched is True
        assert result.pattern_used == "Bash(/git (status|diff|log)/)"

    def test_mcp_server_security_scenario(self):
        """Should handle MCP server security scenarios."""
        matcher = PatternMatcher()

        # Allow filesystem operations
        allow_fs = make_tool_pattern(pattern="mcp__filesystem__*", action="allow")
        fs_call = make_mcp_tool_call("filesystem", "read_file", file_path="safe.txt")
        result = matcher.match_pattern(allow_fs, fs_call)
        assert result.matched is True
        assert result.pattern_used == "mcp__filesystem__*"

        # Deny database operations
        deny_db = make_tool_pattern(pattern="mcp__database__*", action="deny")
        db_call = make_mcp_tool_call("database", "delete_table", table_name="users")
        result = matcher.match_pattern(deny_db, db_call)
        assert result.matched is True
        assert result.pattern_used == "mcp__database__*"

    def test_fallback_universal_wildcard_scenario(self):
        """Should handle fallback to universal wildcard."""
        matcher = PatternMatcher()

        # Universal wildcard as last resort
        universal = make_tool_pattern(pattern="*", action="ask")
        any_call = make_edit_tool_call("unknown/path/file.py")
        result = matcher.match_pattern(universal, any_call)
        assert result.matched is True
        assert result.pattern_used == "*"
        assert result.resource_extracted == "unknown/path/file.py"
