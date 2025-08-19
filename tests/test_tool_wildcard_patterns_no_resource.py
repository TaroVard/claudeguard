"""Tests for Tool(*) patterns with tools that have no meaningful resources.

This test suite describes the desired behavior where Tool(*) patterns should match
tool calls even when the tool has no meaningful resource parameter. These are tools
like Task, TodoWrite, ExitPlanMode, BashOutput, and KillBash.

The issue is that people copy-paste patterns like Edit(*) but for tools that don't
have resources, they write Task(*) which currently doesn't work because:
1. These tools return empty string from extract_resource()
2. The _match_resource() method doesn't handle "*" pattern with empty actual_resource
3. In GlobResourceMatcher.match_resource(), empty actual_resource with "*" pattern returns False

These tests will initially FAIL as they describe the desired behavior.
"""

from __future__ import annotations

from claudeguard.pattern_matcher import PatternMatcher
from tests.factories import (
    make_bash_output_tool_call,
    make_edit_tool_call,
    make_exit_plan_mode_tool_call,
    make_kill_bash_tool_call,
    make_task_tool_call,
    make_todo_write_tool_call,
    make_tool_pattern,
)


class TestToolWildcardPatternsWithNoResource:
    """Test Tool(*) patterns for tools without meaningful resources.

    These tests describe the desired behavior where Tool(*) should match
    tools even when they have no meaningful resource parameter.
    """

    def test_task_wildcard_pattern_matches_task_tool(self):
        """Task(*) pattern should match Task tool calls despite having no meaningful resource."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Task(*)")
        tool_call = make_task_tool_call("Complete the user story")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Task(*)"
        assert result.resource_extracted == ""

    def test_todo_write_wildcard_pattern_matches_todo_write_tool(self):
        """TodoWrite(*) pattern should match TodoWrite tool calls despite having no meaningful resource."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="TodoWrite(*)")
        todos = [
            {"content": "Write tests", "status": "in_progress", "id": "test1"},
            {"content": "Implement feature", "status": "pending", "id": "test2"},
        ]
        tool_call = make_todo_write_tool_call(todos=todos)

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "TodoWrite(*)"
        assert result.resource_extracted == ""

    def test_exit_plan_mode_wildcard_pattern_matches_exit_plan_mode_tool(self):
        """ExitPlanMode(*) pattern should match ExitPlanMode tool calls despite having no meaningful resource."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="ExitPlanMode(*)")
        tool_call = make_exit_plan_mode_tool_call()

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "ExitPlanMode(*)"
        assert result.resource_extracted == ""

    def test_bash_output_wildcard_pattern_matches_bash_output_tool(self):
        """BashOutput(*) pattern should match BashOutput tool calls despite having no meaningful resource."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="BashOutput(*)")
        tool_call = make_bash_output_tool_call(bash_id="shell_abc_123")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "BashOutput(*)"
        assert result.resource_extracted == ""

    def test_kill_bash_wildcard_pattern_matches_kill_bash_tool(self):
        """KillBash(*) pattern should match KillBash tool calls despite having no meaningful resource."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="KillBash(*)")
        tool_call = make_kill_bash_tool_call(shell_id="shell_xyz_789")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "KillBash(*)"
        assert result.resource_extracted == ""


class TestWildcardPatternsBehaviorConsistency:
    """Test that wildcard patterns behave consistently across tool types.

    Tools with resources should continue to work, and tools without resources
    should now also work with the (*) pattern.
    """

    def test_wildcard_patterns_work_for_tools_with_resources(self):
        """Edit(*) should continue to work for tools with meaningful resources."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Edit(*)")
        tool_call = make_edit_tool_call("src/main.py")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(*)"
        assert result.resource_extracted == "src/main.py"

    def test_wildcard_patterns_work_for_tools_without_resources(self):
        """Task(*) should now work for tools without meaningful resources."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Task(*)")
        tool_call = make_task_tool_call("Write unit tests")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Task(*)"
        assert result.resource_extracted == ""

    def test_specific_patterns_dont_match_empty_resources(self):
        """Specific patterns like Task(specific_value) should not match empty resources."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Task(write_documentation)")
        tool_call = make_task_tool_call("Complete user story")  # Different content

        result = matcher.match_pattern(pattern, tool_call)

        # Should not match because Task has no meaningful resource to match against
        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == ""

    def test_empty_pattern_matches_empty_resource(self):
        """Task() with empty parentheses should match tools with empty resources."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Task()")
        tool_call = make_task_tool_call("Any content")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Task()"
        assert result.resource_extracted == ""


class TestBareToolNamesVsWildcardPatterns:
    """Test the distinction between bare tool names and wildcard patterns.

    Both Task and Task(*) should match Task tool calls, but they represent
    different user intentions in pattern specifications.
    """

    def test_bare_tool_name_matches_tools_without_resources(self):
        """Bare tool name 'Task' should match Task tool calls."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Task")
        tool_call = make_task_tool_call("Complete implementation")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Task"
        assert result.resource_extracted == ""

    def test_wildcard_pattern_matches_tools_without_resources(self):
        """Wildcard pattern 'Task(*)' should also match Task tool calls."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Task(*)")
        tool_call = make_task_tool_call("Complete implementation")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Task(*)"
        assert result.resource_extracted == ""

    def test_bare_todo_write_name_matches(self):
        """Bare tool name 'TodoWrite' should match TodoWrite tool calls."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="TodoWrite")
        tool_call = make_todo_write_tool_call()

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "TodoWrite"
        assert result.resource_extracted == ""

    def test_wildcard_todo_write_pattern_matches(self):
        """Wildcard pattern 'TodoWrite(*)' should also match TodoWrite tool calls."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="TodoWrite(*)")
        tool_call = make_todo_write_tool_call()

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "TodoWrite(*)"
        assert result.resource_extracted == ""


class TestWildcardPatternEdgeCases:
    """Test edge cases for wildcard patterns with tools without resources."""

    def test_wrong_tool_name_with_wildcard_no_match(self):
        """Task(*) should not match TodoWrite tool calls."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Task(*)")
        tool_call = make_todo_write_tool_call()

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == ""

    def test_case_sensitive_tool_names_with_wildcard(self):
        """task(*) (lowercase) should not match Task tool calls."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="task(*)")
        tool_call = make_task_tool_call()

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == ""

    def test_malformed_wildcard_patterns_no_match(self):
        """Malformed patterns like Task(*) should be handled gracefully."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Task(*")  # Missing closing parenthesis
        tool_call = make_task_tool_call()

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == ""


class TestResourceExtraction:
    """Test that tools without meaningful resources return empty string."""

    def test_task_tool_returns_empty_resource(self):
        """Task tool should return empty string as resource."""
        matcher = PatternMatcher()
        tool_call = make_task_tool_call("Write comprehensive tests")

        resource = matcher.extract_resource(tool_call)

        assert resource == ""

    def test_todo_write_tool_returns_empty_resource(self):
        """TodoWrite tool should return empty string as resource."""
        matcher = PatternMatcher()
        tool_call = make_todo_write_tool_call()

        resource = matcher.extract_resource(tool_call)

        assert resource == ""

    def test_exit_plan_mode_tool_returns_empty_resource(self):
        """ExitPlanMode tool should return empty string as resource."""
        matcher = PatternMatcher()
        tool_call = make_exit_plan_mode_tool_call()

        resource = matcher.extract_resource(tool_call)

        assert resource == ""

    def test_bash_output_tool_returns_empty_resource(self):
        """BashOutput tool should return empty string as resource."""
        matcher = PatternMatcher()
        tool_call = make_bash_output_tool_call()

        resource = matcher.extract_resource(tool_call)

        assert resource == ""

    def test_kill_bash_tool_returns_empty_resource(self):
        """KillBash tool should return empty string as resource."""
        matcher = PatternMatcher()
        tool_call = make_kill_bash_tool_call()

        resource = matcher.extract_resource(tool_call)

        assert resource == ""


class TestSecurityRuleIntegration:
    """Test realistic security rule scenarios with tools without resources."""

    def test_allow_all_task_operations(self):
        """Task(*) with action='allow' should allow Task tool calls."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Task(*)", action="allow")
        tool_call = make_task_tool_call("Generate test cases")

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Task(*)"
        assert result.resource_extracted == ""

    def test_deny_todo_write_operations(self):
        """TodoWrite(*) with action='deny' should match TodoWrite tool calls."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="TodoWrite(*)", action="deny")
        tool_call = make_todo_write_tool_call()

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "TodoWrite(*)"
        assert result.resource_extracted == ""

    def test_ask_for_plan_mode_changes(self):
        """ExitPlanMode(*) with action='ask' should match ExitPlanMode tool calls."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="ExitPlanMode(*)", action="ask")
        tool_call = make_exit_plan_mode_tool_call()

        result = matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "ExitPlanMode(*)"
        assert result.resource_extracted == ""

    def test_mixed_rules_with_resources_and_without(self):
        """Should handle mixed rules - some with resources, some without."""
        matcher = PatternMatcher()

        # Rule for tools with resources
        edit_pattern = make_tool_pattern(pattern="Edit(*.py)", action="allow")
        edit_call = make_edit_tool_call("main.py")
        edit_result = matcher.match_pattern(edit_pattern, edit_call)

        # Rule for tools without resources
        task_pattern = make_tool_pattern(pattern="Task(*)", action="allow")
        task_call = make_task_tool_call("Refactor code")
        task_result = matcher.match_pattern(task_pattern, task_call)

        # Both should match successfully
        assert edit_result.matched is True
        assert edit_result.pattern_used == "Edit(*.py)"
        assert edit_result.resource_extracted == "main.py"

        assert task_result.matched is True
        assert task_result.pattern_used == "Task(*)"
        assert task_result.resource_extracted == ""
