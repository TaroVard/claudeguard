"""Test hook input parsing and validation behavior."""

import json
from unittest.mock import patch

import pytest

from claudeguard.hook import parse_hook_input, read_stdin_input

from .conftest import (
    hook_input_to_json,
    make_bash_hook_input,
    make_edit_hook_input,
    make_hook_input,
    make_read_hook_input,
    make_write_hook_input,
)


class TestHookInputParsing:
    """Test hook input parsing from stdin JSON."""

    def test_parses_valid_read_tool_input(self) -> None:
        """Hook should parse valid Read tool JSON input from stdin."""
        hook_input = make_read_hook_input(file_path="/test/example.py")
        json_input = hook_input_to_json(hook_input)

        result = parse_hook_input(json_input)

        assert result.tool_name == "Read"
        assert result.tool_input == {"file_path": "/test/example.py"}

    def test_parses_valid_edit_tool_input(self) -> None:
        """Hook should parse valid Edit tool JSON input from stdin."""
        hook_input = make_edit_hook_input(file_path="/src/main.py")
        json_input = hook_input_to_json(hook_input)

        result = parse_hook_input(json_input)

        assert result.tool_name == "Edit"
        assert result.tool_input["file_path"] == "/src/main.py"

    def test_parses_valid_bash_tool_input(self) -> None:
        """Hook should parse valid Bash tool JSON input from stdin."""
        hook_input = make_bash_hook_input(command="git status")
        json_input = hook_input_to_json(hook_input)

        result = parse_hook_input(json_input)

        assert result.tool_name == "Bash"
        assert result.tool_input == {"command": "git status"}

    def test_parses_valid_write_tool_input(self) -> None:
        """Hook should parse valid Write tool JSON input from stdin."""
        hook_input = make_write_hook_input(file_path="/output/result.json")
        json_input = hook_input_to_json(hook_input)

        result = parse_hook_input(json_input)

        assert result.tool_name == "Write"
        assert result.tool_input["file_path"] == "/output/result.json"

    def test_validates_required_tool_name_field(self) -> None:
        """Hook should reject input missing required tool_name field."""
        missing_tool_name_json = json.dumps({"tool_input": {"file_path": "/test.py"}})

        with pytest.raises(ValueError, match="tool_name.*required"):
            parse_hook_input(missing_tool_name_json)

    def test_validates_required_tool_input_field(self) -> None:
        """Hook should reject input missing required tool_input field."""
        missing_tool_input_json = json.dumps({"tool_name": "Read"})

        with pytest.raises(ValueError, match="tool_input.*required"):
            parse_hook_input(missing_tool_input_json)

    def test_validates_tool_name_is_string(self) -> None:
        """Hook should reject input with non-string tool_name."""
        non_string_tool_name_json = json.dumps(
            {"tool_name": 123, "tool_input": {"file_path": "/test.py"}}
        )

        with pytest.raises(ValueError, match="tool_name.*string"):
            parse_hook_input(non_string_tool_name_json)

    def test_validates_tool_input_is_dict(self) -> None:
        """Hook should reject input with non-dict tool_input."""
        non_dict_tool_input_json = json.dumps(
            {"tool_name": "Read", "tool_input": "invalid"}
        )

        with pytest.raises(ValueError, match="tool_input.*dict"):
            parse_hook_input(non_dict_tool_input_json)

    def test_rejects_malformed_json(self) -> None:
        """Hook should reject malformed JSON input."""
        malformed_json_string = '{"tool_name": "Read", "tool_input": {'

        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_hook_input(malformed_json_string)

    def test_rejects_empty_input(self) -> None:
        """Hook should reject empty string input."""
        empty_input_string = ""

        with pytest.raises(ValueError, match="Empty input"):
            parse_hook_input(empty_input_string)

    def test_handles_extra_fields_gracefully(self) -> None:
        """Hook should ignore extra fields in JSON input."""
        input_with_extra_fields = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/test.py"},
            "extra_field": "should_be_ignored",
            "another_extra": 42,
        }
        json_with_extras = json.dumps(input_with_extra_fields)

        result = parse_hook_input(json_with_extras)

        assert result.tool_name == "Read"
        assert result.tool_input == {"file_path": "/test.py"}

    def test_preserves_tool_input_structure(self) -> None:
        """Hook should preserve complex tool_input structure unchanged."""
        complex_hook_input = make_hook_input(
            tool_name="Edit",
            tool_input={
                "file_path": "/complex/path/file.py",
                "old_string": "def old_function():\n    pass",
                "new_string": "def new_function():\n    return True",
                "nested": {
                    "data": ["item1", "item2"],
                    "config": {"enabled": True, "timeout": 30},
                },
            },
        )
        complex_json_input = hook_input_to_json(complex_hook_input)

        result = parse_hook_input(complex_json_input)

        assert result.tool_name == "Edit"
        assert result.tool_input["file_path"] == "/complex/path/file.py"
        assert result.tool_input["nested"]["data"] == ["item1", "item2"]
        assert result.tool_input["nested"]["config"]["enabled"] is True


class TestStdinReadBehavior:
    """Test reading JSON input from stdin."""

    @patch("sys.stdin.read")
    def test_reads_json_from_stdin(self, mock_stdin) -> None:
        """Hook should read JSON input from stdin."""
        hook_input = make_read_hook_input()
        json_data = hook_input_to_json(hook_input)
        mock_stdin.return_value = json_data

        result = read_stdin_input()

        assert result == json_data.strip()
        mock_stdin.assert_called_once()

    @patch("sys.stdin.read")
    def test_handles_stdin_read_errors(self, mock_stdin) -> None:
        """Hook should handle stdin read errors gracefully."""
        mock_stdin.side_effect = OSError("Stdin read error")

        with pytest.raises(ValueError, match="Failed to read from stdin"):
            read_stdin_input()

    @patch("sys.stdin.read")
    def test_strips_whitespace_from_stdin(self, mock_stdin) -> None:
        """Hook should strip whitespace from stdin input."""
        hook_input = make_read_hook_input()
        json_data = hook_input_to_json(hook_input)
        mock_stdin.return_value = f"  {json_data}  \n\t"

        result = read_stdin_input()

        assert result == json_data
        mock_stdin.assert_called_once()


class TestInputValidationBoundaries:
    """Test validation edge cases and boundary conditions."""

    def test_handles_unicode_in_tool_input(self) -> None:
        """Hook should handle Unicode characters in tool input."""
        unicode_hook_input = make_read_hook_input(file_path="/test/файл.py")
        unicode_json_input = hook_input_to_json(unicode_hook_input)

        result = parse_hook_input(unicode_json_input)

        assert result.tool_name == "Read"
        assert result.tool_input["file_path"] == "/test/файл.py"

    def test_handles_very_large_tool_input(self) -> None:
        """Hook should handle large tool_input data structures."""
        large_content_string = "x" * 10000
        large_hook_input = make_hook_input(
            tool_name="Edit",
            tool_input={
                "file_path": "/large/file.txt",
                "old_string": large_content_string,
                "new_string": large_content_string + "_modified",
            },
        )
        large_json_input = hook_input_to_json(large_hook_input)

        result = parse_hook_input(large_json_input)

        assert result.tool_name == "Edit"
        assert result.tool_input["file_path"] == "/large/file.txt"
        assert len(result.tool_input["old_string"]) == 10000

    def test_handles_nested_json_structures(self) -> None:
        """Hook should handle deeply nested JSON structures."""
        deeply_nested_hook_input = make_hook_input(
            tool_name="Write",
            tool_input={
                "file_path": "/config.json",
                "content": json.dumps(
                    {
                        "level1": {
                            "level2": {
                                "level3": {
                                    "data": ["a", "b", "c"],
                                    "numbers": [1, 2, 3],
                                }
                            }
                        }
                    }
                ),
            },
        )
        nested_json_input = hook_input_to_json(deeply_nested_hook_input)

        result = parse_hook_input(nested_json_input)

        assert result.tool_name == "Write"
        assert result.tool_input["file_path"] == "/config.json"
        assert "level1" in json.loads(result.tool_input["content"])

    def test_allows_unknown_tool_names(self) -> None:
        """Hook should allow any tool name - pattern matching will handle validation."""
        unknown_tool_json = json.dumps(
            {"tool_name": "UnknownTool", "tool_input": {"data": "test"}}
        )

        result = parse_hook_input(unknown_tool_json)

        assert result.tool_name == "UnknownTool"
        assert result.tool_input == {"data": "test"}

    def test_allows_all_supported_claude_tools(self) -> None:
        """Hook should accept all supported Claude Code tool names."""
        supported_tool_names = [
            "Read",
            "Edit",
            "Bash",
            "Write",
            "Glob",
            "Grep",
            "WebFetch",
        ]

        for tool_name in supported_tool_names:
            supported_tool_input = make_hook_input(
                tool_name=tool_name, tool_input={"test": "data"}
            )
            supported_tool_json = hook_input_to_json(supported_tool_input)

            result = parse_hook_input(supported_tool_json)

            assert result.tool_name == tool_name
            assert result.tool_input == {"test": "data"}
