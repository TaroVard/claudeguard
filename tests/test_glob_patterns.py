"""Tests for glob pattern matching with wildcards."""

from __future__ import annotations

import pytest

from claudeguard.pattern_matcher import PatternMatcher
from tests.factories import (
    make_edit_tool_call,
    make_tool_pattern,
)


@pytest.fixture
def pattern_matcher() -> PatternMatcher:
    return PatternMatcher()


class TestGlobWildcards:
    """Tests for glob pattern matching with wildcards."""

    def test_single_wildcard_matches_any_filename(self, pattern_matcher: PatternMatcher):
        """Edit(*) should match any Edit file operation."""
        pattern = make_tool_pattern(pattern="Edit(*)", action="allow")
        tool_call = make_edit_tool_call(file_path="any_file.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(*)"
        assert result.resource_extracted == "any_file.py"

    def test_extension_wildcard_matches_specific_extension(self, pattern_matcher: PatternMatcher):
        """Edit(*.py) should match Python files."""
        pattern = make_tool_pattern(pattern="Edit(*.py)", action="ask")
        tool_call = make_edit_tool_call(file_path="main.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(*.py)"
        assert result.resource_extracted == "main.py"

    def test_extension_wildcard_no_match_different_extension(self, pattern_matcher: PatternMatcher):
        """Edit(*.py) should not match non-Python files."""
        pattern = make_tool_pattern(pattern="Edit(*.py)", action="ask")
        tool_call = make_edit_tool_call(file_path="README.md")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "README.md"

    def test_directory_recursive_wildcard_matches_subdirectories(
        self, pattern_matcher: PatternMatcher
    ):
        """Edit(src/**) should match files in src directory and subdirectories."""
        pattern = make_tool_pattern(pattern="Edit(src/**)", action="ask")
        tool_call = make_edit_tool_call(file_path="src/module/component.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(src/**)"
        assert result.resource_extracted == "src/module/component.py"

    def test_directory_recursive_wildcard_matches_direct_files(
        self, pattern_matcher: PatternMatcher
    ):
        """Edit(src/**) should match direct files in src directory."""
        pattern = make_tool_pattern(pattern="Edit(src/**)", action="ask")
        tool_call = make_edit_tool_call(file_path="src/main.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(src/**)"
        assert result.resource_extracted == "src/main.py"

    def test_directory_wildcard_no_match_different_directory(self, pattern_matcher: PatternMatcher):
        """Edit(src/**) should not match files outside src directory."""
        pattern = make_tool_pattern(pattern="Edit(src/**)", action="ask")
        tool_call = make_edit_tool_call(file_path="tests/test_main.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is False
        assert result.pattern_used is None
        assert result.resource_extracted == "tests/test_main.py"

    def test_complex_glob_pattern_matches_correctly(self, pattern_matcher: PatternMatcher):
        """Edit(src/**/*.py) should match Python files in src subdirectories."""
        pattern = make_tool_pattern(pattern="Edit(src/**/*.py)", action="ask")
        tool_call = make_edit_tool_call(file_path="src/utils/helper.py")

        result = pattern_matcher.match_pattern(pattern, tool_call)

        assert result.matched is True
        assert result.pattern_used == "Edit(src/**/*.py)"
        assert result.resource_extracted == "src/utils/helper.py"


class TestPatternSpecificity:
    """Tests for pattern specificity ordering."""

    def test_more_specific_patterns_should_be_ordered_before_general(
        self, pattern_matcher: PatternMatcher
    ):
        """More specific patterns should logically come before general ones."""
        specific_patterns = [
            "Edit(src/config.py)",
            "Edit(src/*.py)",
            "Edit(*.py)",
            "Edit(src/**)",
            "Edit(*)",
            "*",
        ]

        tool_call = make_edit_tool_call(file_path="src/config.py")

        for pattern_str in specific_patterns:
            pattern = make_tool_pattern(pattern=pattern_str, action="allow")
            result = pattern_matcher.match_pattern(pattern, tool_call)
            assert result.matched is True, f"Pattern {pattern_str} should match src/config.py"
