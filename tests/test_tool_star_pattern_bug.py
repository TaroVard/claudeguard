"""Tests demonstrating the Tool(*) pattern bug with empty resources.

This test demonstrates a critical bug where Tool(*) patterns fail to match
tool calls that have empty resources, even though "*" should mean
"any resource including none".

The issue occurs when:
1. A tool call has an empty resource (e.g., Grep with no path parameter)
2. A Tool(*) pattern should match it (since * means "any including none")
3. But the current context-aware logic only handles this for tools in the
   _tool_has_no_meaningful_resource() set
4. Grep is not in that set, so Grep(*) fails to match Grep calls with empty resources

This is inconsistent because:
- Task(*) matches Task calls with empty resources (Task is in the set)
- Grep(*) should match Grep calls with empty resources (but doesn't)
- The "*" pattern should universally mean "any resource including none"
"""

from __future__ import annotations

from claudeguard.pattern_matcher import PatternMatcher
from tests.factories import (
    make_bash_output_tool_call,
    make_grep_tool_call,
    make_task_tool_call,
    make_todo_write_tool_call,
    make_tool_pattern,
)


class TestToolStarPatternWithEmptyResources:
    """Test that Tool(*) patterns universally match any tool call including empty resources."""

    def test_grep_star_should_match_grep_with_empty_path(self):
        """Grep(*) should match Grep calls using glob instead of path (empty resource).

        This demonstrates the core bug: when Grep is called with glob parameter
        instead of path, extract_resource() returns empty string, but Grep(*)
        should still match because "*" means "any resource including none".
        """
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Grep(*)")

        # Grep call with glob instead of path - results in empty resource
        tool_call = make_grep_tool_call(
            pattern="search_term",
            glob="*.py",  # Using glob instead of path
            path=None,  # No path parameter
        )

        result = matcher.match_pattern(pattern, tool_call)

        # This currently FAILS but should PASS
        assert result.matched is True, "Grep(*) should match Grep calls with empty path"
        assert result.pattern_used == "Grep(*)"
        assert result.resource_extracted == ""

    def test_grep_star_should_match_grep_with_explicit_empty_path(self):
        """Grep(*) should match Grep calls with explicitly empty path."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Grep(*)")

        # Grep call with explicitly empty path
        tool_call = make_grep_tool_call(
            pattern="search_term",
            path="",  # Explicitly empty path
        )

        result = matcher.match_pattern(pattern, tool_call)

        # This currently FAILS but should PASS
        assert result.matched is True, "Grep(*) should match Grep calls with empty path"
        assert result.pattern_used == "Grep(*)"
        assert result.resource_extracted == ""

    def test_task_star_matches_task_with_empty_resource_correctly(self):
        """Task(*) should match Task calls with empty resource (this currently works).

        This test shows the inconsistency - Task(*) works because Task is in
        the _tool_has_no_meaningful_resource() set, but Grep(*) doesn't work
        because Grep is not in that set.
        """
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="Task(*)")

        # Task call - extract_resource() returns empty string by design
        tool_call = make_task_tool_call(content="Some task content")

        result = matcher.match_pattern(pattern, tool_call)

        # This currently PASSES (showing the inconsistency)
        assert result.matched is True
        assert result.pattern_used == "Task(*)"
        assert result.resource_extracted == ""

    def test_todo_write_star_matches_todo_write_with_empty_resource(self):
        """TodoWrite(*) should match TodoWrite calls with empty resource (this currently works)."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="TodoWrite(*)")

        # TodoWrite call - extract_resource() returns empty string by design
        tool_call = make_todo_write_tool_call()

        result = matcher.match_pattern(pattern, tool_call)

        # This currently PASSES (showing the inconsistency)
        assert result.matched is True
        assert result.pattern_used == "TodoWrite(*)"
        assert result.resource_extracted == ""

    def test_bash_output_star_matches_bash_output_with_empty_resource(self):
        """BashOutput(*) should match BashOutput calls with empty resource (this currently works)."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="BashOutput(*)")

        # BashOutput call - extract_resource() returns empty string by design
        tool_call = make_bash_output_tool_call()

        result = matcher.match_pattern(pattern, tool_call)

        # This currently PASSES (showing the inconsistency)
        assert result.matched is True
        assert result.pattern_used == "BashOutput(*)"
        assert result.resource_extracted == ""


class TestUniversalStarPatternBehavior:
    """Test that the universal '*' pattern behavior is consistent."""

    def test_universal_star_matches_all_empty_resources(self):
        """Universal '*' pattern should match all tool calls regardless of resource."""
        matcher = PatternMatcher()
        pattern = make_tool_pattern(pattern="*")

        test_calls = [
            make_grep_tool_call(
                pattern="test", glob="*.py", path=None
            ),  # empty resource
            make_task_tool_call(),  # empty resource by design
            make_todo_write_tool_call(),  # empty resource by design
            make_bash_output_tool_call(),  # empty resource by design
        ]

        for tool_call in test_calls:
            result = matcher.match_pattern(pattern, tool_call)

            # Universal '*' should match everything
            assert result.matched is True, (
                f"Universal '*' should match {tool_call.name}"
            )
            assert result.pattern_used == "*"


class TestToolStarPatternConsistencyRequirement:
    """Test that demonstrates the required consistent behavior for Tool(*) patterns."""

    def test_tool_star_should_be_consistent_across_all_tools(self):
        """All Tool(*) patterns should behave consistently - match any resource including empty.

        This test captures the desired behavior: Tool(*) should universally mean
        "match this tool with any resource, including no resource at all".
        """
        matcher = PatternMatcher()

        # Test cases: (pattern, tool_call, description)
        test_cases = [
            (
                "Grep(*)",
                make_grep_tool_call(pattern="test", glob="*.py", path=None),
                "Grep(*) with glob parameter (no path)",
            ),
            (
                "Grep(*)",
                make_grep_tool_call(pattern="test", path=""),
                "Grep(*) with empty path",
            ),
            ("Task(*)", make_task_tool_call(), "Task(*) with no meaningful resource"),
            (
                "TodoWrite(*)",
                make_todo_write_tool_call(),
                "TodoWrite(*) with no meaningful resource",
            ),
            (
                "BashOutput(*)",
                make_bash_output_tool_call(),
                "BashOutput(*) with no meaningful resource",
            ),
        ]

        for pattern_str, tool_call, description in test_cases:
            pattern = make_tool_pattern(pattern=pattern_str)
            result = matcher.match_pattern(pattern, tool_call)

            # ALL Tool(*) patterns should match their respective tools with empty resources
            assert result.matched is True, f"{description} should match"
            assert result.pattern_used == pattern_str
            assert result.resource_extracted == ""


class TestRealWorldScenariosThatCurrentlyFail:
    """Test real-world scenarios that currently fail due to this bug."""

    def test_security_rule_grep_star_allow_should_work(self):
        """Security rule 'Grep(*) -> allow' should match Grep calls with glob parameter.

        This is a realistic security scenario where a user wants to allow all
        Grep operations regardless of how they're called (with path or glob).
        """
        matcher = PatternMatcher()
        allow_all_grep = make_tool_pattern(pattern="Grep(*)", action="allow")

        # Grep call using glob instead of path (common in real usage)
        grep_with_glob = make_grep_tool_call(
            pattern="TODO", glob="**/*.py", output_mode="content"
        )

        result = matcher.match_pattern(allow_all_grep, grep_with_glob)

        # This should match but currently doesn't
        assert result.matched is True, (
            "Security rule Grep(*) should allow all Grep calls"
        )
        assert result.pattern_used == "Grep(*)"

    def test_audit_scenario_grep_calls_with_different_parameter_styles(self):
        """Audit logs should consistently match Grep(*) for all Grep call styles.

        This represents the user's reported issue - their audit logs show
        Grep calls that don't match their Grep(*) patterns.
        """
        matcher = PatternMatcher()
        grep_pattern = make_tool_pattern(pattern="Grep(*)")

        # Different ways Grep can be called
        grep_calls = [
            make_grep_tool_call(pattern="search", path="src/"),  # with path
            make_grep_tool_call(pattern="search", glob="*.py"),  # with glob only
            make_grep_tool_call(
                pattern="search", path="", glob="*.js"
            ),  # empty path + glob
        ]

        for i, tool_call in enumerate(grep_calls):
            result = matcher.match_pattern(grep_pattern, tool_call)

            # All should match Grep(*) pattern
            assert result.matched is True, (
                f"Grep call #{i} should match Grep(*) pattern"
            )
            assert result.pattern_used == "Grep(*)"


# This test will fail and demonstrate the exact issue
def test_demonstrates_the_bug_directly():
    """Direct demonstration of the bug described in the GitHub issue.

    The user reported that Grep(*) patterns don't match Grep tool calls
    when the Grep call uses glob parameter instead of path parameter.
    """
    matcher = PatternMatcher()

    # Extract resource behavior - this shows the root cause
    grep_with_path = make_grep_tool_call(pattern="test", path="src/")
    grep_with_glob_only = make_grep_tool_call(pattern="test", glob="*.py", path=None)

    path_resource = matcher.extract_resource(grep_with_path)
    glob_resource = matcher.extract_resource(grep_with_glob_only)

    # Show the resource extraction difference
    assert path_resource == "src/"
    assert glob_resource == ""  # Empty because no path parameter

    # Pattern matching - this is where the bug manifests
    grep_star_pattern = make_tool_pattern(pattern="Grep(*)")

    # This works (has path)
    result_with_path = matcher.match_pattern(grep_star_pattern, grep_with_path)
    assert result_with_path.matched is True

    # This fails (empty resource) - THE BUG
    result_with_glob_only = matcher.match_pattern(
        grep_star_pattern, grep_with_glob_only
    )

    # This assertion will FAIL, demonstrating the bug
    assert result_with_glob_only.matched is True, (
        "BUG: Grep(*) should match Grep calls with empty resources, "
        "but it doesn't because Grep is not in _tool_has_no_meaningful_resource() set"
    )
