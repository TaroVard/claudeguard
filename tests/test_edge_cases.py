"""Tests for edge cases and error conditions in pattern matching."""

from __future__ import annotations

import pytest

from claudeguard.models import ToolCall, ToolInput
from claudeguard.pattern_matcher import PatternMatcher
from tests.factories import (
    make_allow_all_reads,
    make_allow_safe_git,
    make_ask_src_edits,
    make_bash_tool_call,
    make_deny_dangerous_bash,
    make_edit_tool_call,
    make_glob_tool_call,
    make_mcp_tool_call,
    make_read_tool_call,
    make_tool_call,
    make_tool_pattern,
    make_wildcard_ask,
    make_write_tool_call,
)


@pytest.fixture
def pattern_matcher() -> PatternMatcher:
    return PatternMatcher()


class TestMalformedPatterns:
    """Tests for edge cases and malformed pattern handling."""

    def test_empty_pattern_no_match(self, pattern_matcher: PatternMatcher) -> None:
        """Empty pattern string should not match any tool call."""
        pattern = make_tool_pattern(pattern="", action="deny")
        tool_call = make_edit_tool_call()

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None

    def test_bare_tool_name_now_matches_as_no_resource_pattern(
        self, pattern_matcher: PatternMatcher
    ):
        """Bare tool name (no parentheses) now matches as no-resource pattern."""
        bare_tool_pattern = make_tool_pattern(pattern="Edit", action="allow")
        tool_call = make_edit_tool_call()

        result = pattern_matcher.match_pattern(bare_tool_pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit"

    def test_pattern_with_only_opening_parenthesis_no_match(
        self, pattern_matcher: PatternMatcher
    ):
        """Pattern with only opening parenthesis should not match."""
        pattern = make_tool_pattern(pattern="Edit(src/main.py", action="allow")
        tool_call = make_edit_tool_call(file_path="src/main.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None

    def test_pattern_with_only_closing_parenthesis_no_match(
        self, pattern_matcher: PatternMatcher
    ):
        """Pattern with only closing parenthesis should not match."""
        pattern = make_tool_pattern(pattern="src/main.py)", action="allow")
        tool_call = make_edit_tool_call(file_path="src/main.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None

    def test_pattern_with_empty_resource_matches_empty_resource(
        self, pattern_matcher: PatternMatcher
    ):
        """Pattern with empty resource should match tool calls with empty resource."""
        pattern = make_tool_pattern(pattern="Edit()", action="ask")
        tool_call = make_tool_call("Edit", file_path="")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit()"
        assert result.resource_extracted == ""


class TestResourceExtraction:
    """Tests for tool-specific resource extraction from tool inputs."""

    def test_edit_tool_extracts_file_path_from_input(
        self, pattern_matcher: PatternMatcher
    ):
        """Edit tool should extract file_path from input parameters."""
        tool_call = make_edit_tool_call(
            file_path="src/main.py", old_string="old", new_string="new"
        )

        resource = pattern_matcher.extract_resource(tool_call)

        assert resource == "src/main.py"

    def test_read_tool_extracts_file_path_from_input(
        self, pattern_matcher: PatternMatcher
    ):
        """Read tool should extract file_path from input parameters."""
        tool_call = make_read_tool_call(file_path="docs/guide.md", limit=100)

        resource = pattern_matcher.extract_resource(tool_call)

        assert resource == "docs/guide.md"

    def test_bash_tool_extracts_command_from_input(
        self, pattern_matcher: PatternMatcher
    ):
        """Bash tool should extract command from input parameters."""
        tool_call = make_bash_tool_call(command="git status --porcelain")

        resource = pattern_matcher.extract_resource(tool_call)

        assert resource == "git status --porcelain"

    def test_write_tool_extracts_file_path_from_input(
        self, pattern_matcher: PatternMatcher
    ):
        """Write tool should extract file_path from input parameters."""
        tool_call = make_write_tool_call(file_path="output.txt", content="test content")

        resource = pattern_matcher.extract_resource(tool_call)

        assert resource == "output.txt"

    def test_glob_tool_extracts_pattern_from_input(
        self, pattern_matcher: PatternMatcher
    ):
        """Glob tool should extract pattern from input parameters."""
        tool_call = make_glob_tool_call(pattern="**/*.py", path="src")

        resource = pattern_matcher.extract_resource(tool_call)

        assert resource in {"**/*.py", "src/**/*.py"}

    def test_tool_with_missing_expected_parameter_returns_empty(
        self, pattern_matcher: PatternMatcher
    ):
        """Tool call missing expected parameter should return empty resource."""
        tool_call_with_wrong_param = make_tool_call("Edit", some_other_param="value")

        resource = pattern_matcher.extract_resource(tool_call_with_wrong_param)

        assert resource == ""

    def test_webfetch_tool_extracts_url_from_input(
        self, pattern_matcher: PatternMatcher
    ):
        """WebFetch tool should extract URL from input data."""
        webfetch_call = make_tool_call("WebFetch", url="https://example.com")

        resource = pattern_matcher.extract_resource(webfetch_call)

        assert resource == "https://example.com"

    def test_websearch_tool_extracts_url_from_input(
        self, pattern_matcher: PatternMatcher
    ):
        """WebSearch tool should extract URL from input data."""
        websearch_call = make_tool_call("WebSearch", url="https://search.example.com")

        resource = pattern_matcher.extract_resource(websearch_call)

        assert resource == "https://search.example.com"

    def test_grep_tool_extracts_path_from_input(self, pattern_matcher: PatternMatcher):
        """Grep tool should extract path from input data."""
        grep_call = make_tool_call("Grep", path="/src/main.py")

        resource = pattern_matcher.extract_resource(grep_call)

        assert resource == "/src/main.py"

    def test_ls_tool_extracts_path_from_input(self, pattern_matcher: PatternMatcher):
        """LS tool should extract path from input data."""
        ls_call = make_tool_call("LS", path="/home/user/docs")

        resource = pattern_matcher.extract_resource(ls_call)

        assert resource == "/home/user/docs"

    def test_unknown_tool_type_returns_empty_resource(
        self, pattern_matcher: PatternMatcher
    ):
        """Unknown tool type should return empty resource."""
        tool_input = ToolInput(data={"some_param": "value"})
        unknown_tool_call = ToolCall(name="UnknownTool", input=tool_input)

        resource = pattern_matcher.extract_resource(unknown_tool_call)

        assert resource == ""


class TestMCPEdgeCases:
    """Tests for MCP edge cases and invalid pattern handling."""

    def test_invalid_mcp_pattern_single_underscore_rejected(
        self, pattern_matcher: PatternMatcher
    ):
        """Pattern with single underscore (mcp_server_tool) should not match MCP tools."""
        pattern = make_tool_pattern(pattern="mcp_playwright_screenshot", action="allow")
        tool_call = make_mcp_tool_call("playwright", "screenshot")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None

    def test_invalid_mcp_pattern_missing_server_rejected(
        self, pattern_matcher: PatternMatcher
    ):
        """Pattern missing server name (mcp____tool) should not match."""
        pattern = make_tool_pattern(pattern="mcp____screenshot", action="allow")
        tool_call = make_mcp_tool_call("playwright", "screenshot")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None

    def test_invalid_mcp_pattern_missing_tool_rejected(
        self, pattern_matcher: PatternMatcher
    ):
        """Pattern missing tool name (mcp__server__) should not match."""
        pattern = make_tool_pattern(pattern="mcp__playwright__", action="allow")
        tool_call = make_mcp_tool_call("playwright", "screenshot")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None

    def test_non_mcp_tool_with_mcp_like_name_not_matched_by_mcp_pattern(
        self, pattern_matcher: PatternMatcher
    ):
        """Regular tools with MCP-like names should not match MCP patterns."""
        pattern = make_tool_pattern(pattern="mcp__*", action="allow")
        fake_mcp_tool_call = make_tool_call(
            "Edit", file_path="mcp__playwright__test.py"
        )

        result = pattern_matcher.match_pattern(pattern, fake_mcp_tool_call)

        assert result.matched is False
        assert result.pattern_used is None

    def test_mcp_tool_resource_extraction_varies_by_tool_type(
        self, pattern_matcher: PatternMatcher
    ):
        """Different MCP tools should extract resources based on their input structure."""
        filesystem_tool = make_mcp_tool_call(
            "filesystem", "read_file", file_path="/test/file.txt"
        )
        database_tool = make_mcp_tool_call(
            "database", "query_table", table_name="users"
        )
        api_tool = make_mcp_tool_call(
            "api_client", "get_request", url="https://api.example.com"
        )

        fs_resource = pattern_matcher.extract_resource(filesystem_tool)
        db_resource = pattern_matcher.extract_resource(database_tool)
        api_resource = pattern_matcher.extract_resource(api_tool)

        assert fs_resource == "/test/file.txt"
        assert db_resource == "users"
        assert api_resource == "https://api.example.com"

    def test_malformed_mcp_tool_call_handled_gracefully(
        self, pattern_matcher: PatternMatcher
    ):
        """Malformed MCP tool calls should be handled without crashing."""
        pattern = make_tool_pattern(pattern="mcp__*", action="allow")
        malformed_tool = make_tool_call("mcp__incomplete")

        result = pattern_matcher.match_pattern(pattern, malformed_tool)

        assert result.matched is False
        assert result.pattern_used is None


class TestPatternPrecedence:
    """Tests for pattern precedence and matching order."""

    def test_first_matching_pattern_wins_in_list(self, pattern_matcher: PatternMatcher):
        """When multiple patterns match, first one should be selected."""
        patterns = [
            make_tool_pattern(pattern="Edit(*)", action="allow"),
            make_tool_pattern(pattern="Edit(*.py)", action="ask"),
            make_wildcard_ask(),
        ]
        tool_call = make_edit_tool_call(file_path="main.py")

        result1 = pattern_matcher.match_pattern(patterns[0], tool_call)
        result2 = pattern_matcher.match_pattern(patterns[1], tool_call)
        result3 = pattern_matcher.match_pattern(patterns[2], tool_call)

        assert result1.matched is True
        assert result2.matched is True
        assert result3.matched is True

    def test_mixed_patterns_precedence(self, pattern_matcher: PatternMatcher) -> None:
        """Test that specific patterns take precedence over bare tool names."""
        specific_pattern = make_tool_pattern(pattern="Edit(*.py)", action="deny")
        bare_pattern = make_tool_pattern(pattern="Edit", action="allow")

        python_file_call = make_edit_tool_call(file_path="main.py")
        text_file_call = make_edit_tool_call(file_path="README.txt")

        specific_result = pattern_matcher.match_pattern(
            specific_pattern, python_file_call
        )
        bare_result = pattern_matcher.match_pattern(bare_pattern, python_file_call)

        assert specific_result.matched is True
        assert bare_result.matched is True

        specific_txt_result = pattern_matcher.match_pattern(
            specific_pattern, text_file_call
        )
        bare_txt_result = pattern_matcher.match_pattern(bare_pattern, text_file_call)

        assert specific_txt_result.matched is False
        assert bare_txt_result.matched is True

    def test_mcp_pattern_specificity_ordering(self, pattern_matcher: PatternMatcher):
        """MCP patterns should follow logical specificity ordering."""
        mcp_specificity_patterns = [
            "mcp__playwright__browser_console_messages",
            "mcp__playwright__browser*",
            "mcp__playwright__*",
            "mcp__*",
            "*",
        ]

        tool_call = make_mcp_tool_call("playwright", "browser_console_messages")

        for pattern_str in mcp_specificity_patterns:
            pattern = make_tool_pattern(pattern=pattern_str, action="allow")
            result = pattern_matcher.match_pattern(pattern, tool_call)
            assert result.matched is True, (
                f"Pattern {pattern_str} should match MCP tool"
            )


class TestRuleEngineIntegration:
    """Tests for expected behavior with rule engine integration."""

    def test_rule_engine_integration_behavior(self, pattern_matcher: PatternMatcher):
        """Define expected behavior for rule engine integration."""
        default_rules = [
            make_allow_all_reads(),
            make_tool_pattern(pattern="Edit(*.md)", action="allow"),
            make_ask_src_edits(),
            make_tool_pattern(pattern="Edit(*.py)", action="ask"),
            make_allow_safe_git(),
            make_tool_pattern(pattern="Bash(git push*)", action="ask"),
            make_deny_dangerous_bash(),
            make_wildcard_ask(),
        ]

        test_cases = [
            (make_read_tool_call(file_path="any/file.txt"), "Read(*)", "allow"),
            (make_edit_tool_call(file_path="README.md"), "Edit(*.md)", "allow"),
            (make_edit_tool_call(file_path="src/main.py"), "Edit(src/**)", "ask"),
            (
                make_bash_tool_call(command="git status"),
                "Bash(git status*)",
                "allow",
            ),
            (make_bash_tool_call(command="rm -rf /"), "Bash(rm -rf*)", "deny"),
        ]

        for tool_call, expected_pattern, _expected_action in test_cases:
            matching_rule = None
            for rule in default_rules:
                result = pattern_matcher.match_pattern(rule, tool_call)
                if result.matched:
                    matching_rule = rule
                    break

            assert matching_rule is not None, f"No rule matched {tool_call}"
            assert matching_rule.pattern == expected_pattern

    def test_mcp_patterns_work_alongside_regular_patterns(
        self, pattern_matcher: PatternMatcher
    ):
        """MCP patterns should work alongside regular Claude Code patterns."""
        mixed_patterns = [
            make_tool_pattern(pattern="Edit(*.py)", action="ask"),
            make_tool_pattern(pattern="mcp__playwright__*", action="allow"),
            make_tool_pattern(pattern="Bash(git*)", action="allow"),
            make_tool_pattern(pattern="mcp__database__*(users*)", action="deny"),
        ]

        test_calls = [
            (make_edit_tool_call(file_path="test.py"), "Edit(*.py)"),
            (make_mcp_tool_call("playwright", "screenshot"), "mcp__playwright__*"),
            (make_bash_tool_call(command="git status"), "Bash(git*)"),
            (
                make_mcp_tool_call("database", "query", table_name="users"),
                "mcp__database__*(users*)",
            ),
        ]

        for tool_call, expected_pattern in test_calls:
            for pattern in mixed_patterns:
                result = pattern_matcher.match_pattern(pattern, tool_call)
                if result.matched:
                    assert pattern.pattern == expected_pattern
                    break
            else:
                pytest.fail(f"No pattern matched {tool_call}")

    def test_cross_server_wildcard_precedence_over_specific_patterns(
        self, pattern_matcher: PatternMatcher
    ):
        """More specific MCP patterns should be evaluated before general ones."""
        general_pattern = make_tool_pattern(pattern="mcp__*", action="deny")
        specific_pattern = make_tool_pattern(
            pattern="mcp__playwright__*", action="allow"
        )

        playwright_tool = make_mcp_tool_call("playwright", "page_screenshot")

        general_result = pattern_matcher.match_pattern(general_pattern, playwright_tool)
        specific_result = pattern_matcher.match_pattern(
            specific_pattern, playwright_tool
        )

        assert general_result.matched is True
        assert specific_result.matched is True
