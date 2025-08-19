"""
Test permission decision logic and pattern matching behavior.
Following TDD principles - these tests will fail until implementation is created.
"""

from claudeguard.permission_decision import make_permission_decision, matches_pattern
from tests.factories import (
    make_permissive_profile,
    make_profile,
    make_restrictive_profile,
)

from .conftest import (
    make_bash_hook_input,
    make_default_profile,
    make_edit_hook_input,
    make_profile_rule,
    make_read_hook_input,
    make_write_hook_input,
)


class TestPatternMatching:
    """Test pattern matching logic for tool operations."""

    def test_matches_read_tool_wildcard_pattern(self) -> None:
        """Pattern matcher should match Read(*) against any Read tool operation."""
        rule = make_profile_rule("Read(*)", "allow")
        hook_input = make_read_hook_input(file_path="/any/file.py")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True

    def test_matches_read_tool_specific_file_pattern(self) -> None:
        """Pattern matcher should match specific file patterns for Read tool."""
        rule = make_profile_rule("Read(*.py)", "allow")
        hook_input = make_read_hook_input(file_path="/src/main.py")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True

    def test_matches_read_tool_directory_pattern(self) -> None:
        """Pattern matcher should match directory patterns for Read tool."""
        rule = make_profile_rule("Read(src/**)", "allow")
        hook_input = make_read_hook_input(file_path="/project/src/module/file.py")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True

    def test_does_not_match_read_wrong_file_pattern(self) -> None:
        """Pattern matcher should not match wrong file patterns."""
        rule = make_profile_rule("Read(*.js)", "allow")
        hook_input = make_read_hook_input(file_path="/src/main.py")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is False

    def test_matches_edit_tool_patterns(self) -> None:
        """Pattern matcher should match Edit tool patterns correctly."""
        rule = make_profile_rule("Edit(src/**)", "ask")
        hook_input = make_edit_hook_input(file_path="/project/src/file.py")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True

    def test_matches_bash_exact_command(self) -> None:
        """Pattern matcher should match exact Bash commands."""
        rule = make_profile_rule("Bash(git status)", "allow")
        hook_input = make_bash_hook_input(command="git status")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True

    def test_matches_bash_command_prefix(self) -> None:
        """Pattern matcher should match Bash command prefixes."""
        rule = make_profile_rule("Bash(git *)", "allow")
        hook_input = make_bash_hook_input(command="git diff --cached")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True

    def test_does_not_match_bash_wrong_command(self) -> None:
        """Pattern matcher should not match wrong Bash commands."""
        rule = make_profile_rule("Bash(git status)", "allow")
        hook_input = make_bash_hook_input(command="rm -rf /")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is False

    def test_matches_universal_wildcard_pattern(self) -> None:
        """Pattern matcher should match universal wildcard against any tool."""
        rule = make_profile_rule("*", "ask")

        test_inputs = [
            make_read_hook_input(),
            make_edit_hook_input(),
            make_bash_hook_input(),
            make_write_hook_input(),
        ]

        for hook_input in test_inputs:
            result = matches_pattern(rule.pattern, hook_input)
            assert result is True

    def test_handles_case_sensitive_patterns(self) -> None:
        """Pattern matcher should be case sensitive for tool names."""
        lowercase_rule = make_profile_rule("read(*)", "allow")
        capitalized_hook_input = make_read_hook_input()

        result = matches_pattern(lowercase_rule.pattern, capitalized_hook_input)
        assert result is False

    def test_matches_write_tool_patterns(self) -> None:
        """Pattern matcher should match Write tool patterns."""
        rule = make_profile_rule("Write(*.json)", "ask")
        hook_input = make_write_hook_input(file_path="/output/data.json")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True


class TestPermissionDecisionLogic:
    """Test permission decision making based on profile rules."""

    def test_returns_allow_for_matching_allow_rule(self) -> None:
        """Decision logic should return allow for matching allow rules."""
        profile = make_profile(
            rules=(make_profile_rule("Read(*)", "allow"), make_profile_rule("*", "ask"))
        )
        hook_input = make_read_hook_input()

        decision = make_permission_decision(hook_input, profile)
        assert decision.action == "allow"
        assert "Read(*)" in decision.reason

    def test_returns_deny_for_matching_deny_rule(self) -> None:
        """Decision logic should return deny for matching deny rules."""
        profile = make_profile(
            rules=(
                make_profile_rule("Bash(rm -rf*)", "deny"),
                make_profile_rule("*", "ask"),
            )
        )
        hook_input = make_bash_hook_input(command="rm -rf /important")

        decision = make_permission_decision(hook_input, profile)
        assert decision.action == "deny"
        assert "Bash(rm -rf*)" in decision.reason

    def test_returns_ask_for_matching_ask_rule(self) -> None:
        """Decision logic should return ask for matching ask rules."""
        profile = make_profile(
            rules=(make_profile_rule("Edit(*)", "ask"), make_profile_rule("*", "deny"))
        )
        hook_input = make_edit_hook_input()

        decision = make_permission_decision(hook_input, profile)
        assert decision.action == "ask"
        assert "Edit(*)" in decision.reason

    def test_uses_first_matching_rule(self) -> None:
        """Decision logic should use first matching rule in order."""
        profile = make_profile(
            rules=(
                make_profile_rule("Read(*)", "allow"),
                make_profile_rule("Read(*.py)", "deny"),
                make_profile_rule("*", "ask"),
            )
        )
        hook_input = make_read_hook_input(file_path="/test.py")

        decision = make_permission_decision(hook_input, profile)
        assert decision.action == "allow"
        assert "Read(*)" in decision.reason

    def test_defaults_to_ask_when_no_rules_match(self) -> None:
        """Decision logic should default to ask when no rules match."""
        profile = make_profile(
            rules=(
                make_profile_rule("Read(*.txt)", "allow"),
                make_profile_rule("Edit(*.md)", "allow"),
            )
        )
        unmatched_hook_input = make_bash_hook_input()

        decision = make_permission_decision(unmatched_hook_input, profile)
        assert decision.action == "ask"
        assert "No matching rules found" in decision.reason

    def test_handles_empty_profile_rules(self) -> None:
        """Decision logic should handle profile with no rules."""
        empty_profile = make_profile(rules=())
        hook_input = make_read_hook_input()

        decision = make_permission_decision(hook_input, empty_profile)
        assert decision.action == "ask"
        assert "No matching rules found" in decision.reason

    def test_provides_detailed_decision_reason(self) -> None:
        """Decision logic should provide detailed reason for transparency."""
        profile = make_default_profile()
        hook_input = make_read_hook_input(file_path="/src/main.py")

        decision = make_permission_decision(hook_input, profile)
        assert decision.reason is not None
        assert len(decision.reason) > 0
        assert "→" in decision.reason

    def test_works_with_default_profile_rules(self) -> None:
        """Decision logic should work correctly with default profile."""
        profile = make_default_profile()

        test_cases = [
            (make_read_hook_input(), "allow"),
            (make_edit_hook_input(file_path="/README.md"), "allow"),
            (make_edit_hook_input(file_path="/src/main.py"), "ask"),
            (make_bash_hook_input(command="git status"), "allow"),
            (make_bash_hook_input(command="rm -rf /"), "deny"),
        ]

        for hook_input, expected_action in test_cases:
            decision = make_permission_decision(hook_input, profile)
            assert decision.action == expected_action

    def test_works_with_restrictive_profile_rules(self) -> None:
        """Decision logic should work correctly with restrictive profile."""
        profile = make_restrictive_profile()

        test_cases = [
            (make_read_hook_input(), "ask"),
            (make_edit_hook_input(), "ask"),
            (make_bash_hook_input(command="git status"), "ask"),
            (make_bash_hook_input(command="rm -rf /tmp"), "deny"),
        ]

        for hook_input, expected_action in test_cases:
            decision = make_permission_decision(hook_input, profile)
            assert decision.action == expected_action

    def test_works_with_permissive_profile_rules(self) -> None:
        """Decision logic should work correctly with permissive profile."""
        profile = make_permissive_profile()

        test_cases = [
            (make_read_hook_input(), "allow"),
            (make_edit_hook_input(), "allow"),
            (make_bash_hook_input(command="git push"), "allow"),
            (make_bash_hook_input(command="rm -rf /"), "allow"),
            (make_bash_hook_input(command="sudo rm file"), "allow"),
        ]

        for hook_input, expected_action in test_cases:
            decision = make_permission_decision(hook_input, profile)
            assert decision.action == expected_action


class TestPatternComplexity:
    """Test complex pattern matching scenarios."""

    def test_handles_nested_directory_patterns(self) -> None:
        """Pattern matcher should handle deeply nested directory patterns."""
        rule = make_profile_rule("Read(src/**/test/**/*.py)", "allow")
        hook_input = make_read_hook_input(
            file_path="/project/src/module/test/unit/test_file.py"
        )

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True

    def test_handles_multiple_wildcard_patterns(self) -> None:
        """Pattern matcher should handle multiple wildcards in patterns."""
        rule = make_profile_rule("Edit(**/test_*.py)", "ask")
        hook_input = make_edit_hook_input(file_path="/any/deep/path/test_example.py")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True

    def test_handles_bash_complex_command_patterns(self) -> None:
        """Pattern matcher should handle complex bash command patterns."""
        rule = make_profile_rule("Bash(git diff --*)", "allow")
        hook_input = make_bash_hook_input(command="git diff --cached --stat")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True

    def test_handles_special_characters_in_patterns(self) -> None:
        """Pattern matcher should handle special characters in file patterns."""
        rule = make_profile_rule("Read(*[test]*)", "allow")
        hook_input = make_read_hook_input(file_path="/path/file[test].py")

        result = matches_pattern(rule.pattern, hook_input)
        assert result is True

    def test_pattern_matching_performance_with_many_rules(self) -> None:
        """Pattern matcher should perform well with many rules."""
        many_rules = tuple(
            make_profile_rule(f"Read(pattern_{i}/*)", "allow") for i in range(100)
        )
        many_rules += (make_profile_rule("Read(*)", "allow"),)

        profile_with_many_rules = make_profile(rules=many_rules)
        hook_input = make_read_hook_input(file_path="/test/file.py")

        decision = make_permission_decision(hook_input, profile_with_many_rules)
        assert decision.action == "allow"
        assert "Read(*)" in decision.reason
