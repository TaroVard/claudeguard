"""Test comprehensive support for all Claude Code tools."""

import pytest

from claudeguard.models import ToolCall, ToolInput, ToolPattern
from claudeguard.pattern_matcher import PatternMatcher


class TestAllClaudeToolsSupport:
    """Test that all Claude Code tools are properly supported."""

    @pytest.fixture
    def pattern_matcher(self) -> PatternMatcher:
        """Create pattern matcher for testing."""
        return PatternMatcher()

    def test_file_operations_extract_file_path(self, pattern_matcher: PatternMatcher):
        """File operation tools should extract file_path parameter."""
        file_tools = ["Edit", "Read", "Write", "MultiEdit"]

        for tool_name in file_tools:
            tool_call = ToolCall(
                name=tool_name, input=ToolInput(data={"file_path": "/src/main.py"})
            )

            resource = pattern_matcher.extract_resource(tool_call)
            assert resource == "/src/main.py", f"{tool_name} should extract file_path"

    def test_notebook_edit_extracts_notebook_path(self, pattern_matcher: PatternMatcher):
        """NotebookEdit should extract notebook_path parameter."""
        tool_call = ToolCall(
            name="NotebookEdit",
            input=ToolInput(data={"notebook_path": "/notebooks/analysis.ipynb"}),
        )

        resource = pattern_matcher.extract_resource(tool_call)
        assert resource == "/notebooks/analysis.ipynb"

    def test_bash_extracts_command(self, pattern_matcher: PatternMatcher):
        """Bash should extract command parameter."""
        tool_call = ToolCall(name="Bash", input=ToolInput(data={"command": "git status"}))

        resource = pattern_matcher.extract_resource(tool_call)
        assert resource == "git status"

    def test_search_tools_extract_path_or_pattern(self, pattern_matcher: PatternMatcher):
        """Search tools should extract appropriate parameters."""
        # Glob extracts pattern
        glob_call = ToolCall(name="Glob", input=ToolInput(data={"pattern": "**/*.py"}))
        assert pattern_matcher.extract_resource(glob_call) == "**/*.py"

        # Grep and LS extract path
        search_tools = ["Grep", "LS"]
        for tool_name in search_tools:
            tool_call = ToolCall(name=tool_name, input=ToolInput(data={"path": "/src"}))
            resource = pattern_matcher.extract_resource(tool_call)
            assert resource == "/src", f"{tool_name} should extract path"

    def test_network_tools_extract_url(self, pattern_matcher: PatternMatcher):
        """Network tools should extract URL parameter."""
        network_tools = ["WebFetch", "WebSearch"]

        for tool_name in network_tools:
            tool_call = ToolCall(
                name=tool_name, input=ToolInput(data={"url": "https://example.com"})
            )

            resource = pattern_matcher.extract_resource(tool_call)
            assert resource == "https://example.com", f"{tool_name} should extract url"

    def test_no_resource_tools_return_empty_string(self, pattern_matcher: PatternMatcher):
        """Tools without meaningful resources should return empty string."""
        no_resource_tools = [
            "Task",
            "ExitPlanMode",
            "TodoWrite",
            "BashOutput",
            "KillBash",
        ]

        for tool_name in no_resource_tools:
            tool_call = ToolCall(name=tool_name, input=ToolInput(data={"some_param": "value"}))

            resource = pattern_matcher.extract_resource(tool_call)
            assert resource == "", f"{tool_name} should return empty resource"

    def test_unknown_tools_return_empty_string(self, pattern_matcher: PatternMatcher):
        """Unknown tools should return empty string for fallback matching."""
        tool_call = ToolCall(name="UnknownTool", input=ToolInput(data={"any_param": "value"}))

        resource = pattern_matcher.extract_resource(tool_call)
        assert resource == ""

    def test_no_resource_tools_match_bare_patterns(self, pattern_matcher: PatternMatcher):
        """Tools with no resources should match bare tool name patterns."""
        pattern = ToolPattern(pattern="Task", action="allow")
        tool_call = ToolCall(name="Task", input=ToolInput(data={"description": "some task"}))

        result = pattern_matcher.match_pattern(pattern, tool_call)
        assert result.matched is True
        assert result.resource_extracted == ""

    def test_mcp_tools_use_dynamic_extraction(self, pattern_matcher: PatternMatcher):
        """MCP tools should use dynamic resource extraction."""
        mcp_call = ToolCall(
            name="mcp__server__database_query",
            input=ToolInput(data={"table_name": "users", "other_param": "ignored"}),
        )

        resource = pattern_matcher.extract_resource(mcp_call)
        assert resource == "users"  # Should find table_name from resource_params list
