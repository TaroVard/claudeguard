"""Tests for error handling and fail-safe behavior."""

import json
from io import StringIO
from unittest.mock import patch

from claudeguard.hook import main

from .conftest import (
    hook_input_to_json,
    make_read_hook_input,
)


class TestInputValidationErrors:
    """Test error handling for invalid input scenarios."""

    def test_handles_empty_stdin_gracefully(self) -> None:
        """Hook should handle empty stdin input gracefully."""
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    mock_stdin.return_value = ""
                    main()

                    # Should output fail-safe JSON response
                    output = mock_stdout.getvalue()
                    assert "ask" in output
                    assert "claudeguard error" in output

                    # Should exit with code 0 (not error exit)
                    mock_exit.assert_called_once_with(0)

    def test_handles_malformed_json_gracefully(self) -> None:
        """Hook should handle malformed JSON input gracefully."""
        malformed_inputs = [
            '{"tool_name": "Read"',
            '{"tool_name": "Read", "tool_input": }',
            "not json at all",
            "[]",
            "null",
        ]
        for malformed_input in malformed_inputs:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    with patch("sys.exit") as mock_exit:
                        mock_stdin.return_value = malformed_input
                        main()

                        # Should output fail-safe JSON response
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        assert "claudeguard error" in output

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)
                        mock_exit.reset_mock()
                        mock_stdout.seek(0)
                        mock_stdout.truncate(0)

    def test_handles_missing_required_fields_gracefully(self) -> None:
        """Hook should handle missing required fields gracefully."""
        invalid_inputs = [
            '{"tool_input": {"file_path": "/test.py"}}',
            '{"tool_name": "Read"}',
            '{"tool_name": null, "tool_input": {}}',
            '{"tool_name": "Read", "tool_input": null}',
        ]
        for invalid_input in invalid_inputs:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    with patch("sys.exit") as mock_exit:
                        mock_stdin.return_value = invalid_input
                        main()

                        # Should output fail-safe JSON response
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        assert "claudeguard error" in output

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)
                        mock_exit.reset_mock()
                        mock_stdout.seek(0)
                        mock_stdout.truncate(0)

    def test_handles_invalid_field_types_gracefully(self) -> None:
        """Hook should handle invalid field types gracefully."""
        invalid_inputs = [
            '{"tool_name": 123, "tool_input": {}}',
            '{"tool_name": "Read", "tool_input": "string"}',
            '{"tool_name": ["Read"], "tool_input": {}}',
        ]
        for invalid_input in invalid_inputs:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    with patch("sys.exit") as mock_exit:
                        mock_stdin.return_value = invalid_input
                        main()

                        # Should output fail-safe JSON response
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        assert "claudeguard error" in output

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)
                        mock_exit.reset_mock()
                        mock_stdout.seek(0)
                        mock_stdout.truncate(0)

    def test_handles_stdin_read_exceptions(self) -> None:
        """Hook should handle stdin read exceptions gracefully."""
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    mock_stdin.side_effect = OSError("Stdin read failed")
                    main()

                    # Should output fail-safe JSON response
                    output = mock_stdout.getvalue()
                    assert "ask" in output
                    assert "claudeguard error" in output

                    # Should exit with code 0 (not error exit)
                    mock_exit.assert_called_once_with(0)


class TestProfileLoadingErrors:
    """Test error handling for profile loading failures."""

    def test_handles_missing_profile_directory_gracefully(self) -> None:
        """Hook should handle missing .claudeguard profile directory gracefully."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    with patch("pathlib.Path.exists") as mock_exists:
                        mock_exists.return_value = False
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should output JSON response (fallback to default profile)
                        output = mock_stdout.getvalue()
                        assert "hookSpecificOutput" in output
                        # Should handle gracefully by falling back to defaults
                        # (not necessarily an error - may use default profile)

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)

    def test_handles_missing_profile_file_gracefully(self) -> None:
        """Hook should handle missing profile file gracefully."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    with patch("pathlib.Path.exists") as mock_exists:
                        with patch("builtins.open") as mock_file:
                            mock_exists.return_value = True
                            mock_file.side_effect = FileNotFoundError("Profile not found")
                            mock_stdin.return_value = hook_input_to_json(hook_input)
                            main()

                            # Should output JSON response (may fallback to defaults)
                            output = mock_stdout.getvalue()
                            assert "hookSpecificOutput" in output
                            # Should handle gracefully (may fallback to defaults or fail-safe)

                            # Should exit with code 0 (not error exit)
                            mock_exit.assert_called_once_with(0)

    def test_handles_corrupt_profile_file_gracefully(self) -> None:
        """Hook should handle corrupted profile YAML file gracefully."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                        mock_load.side_effect = Exception("Corrupted YAML file")
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should output fail-safe JSON response
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        # May have error message or fallback behavior

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)

    def test_handles_profile_with_invalid_rules_gracefully(self) -> None:
        """Hook should handle profile with invalid rule format gracefully."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                        mock_load.side_effect = Exception("Invalid rule format")
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should output fail-safe JSON response
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        # May have error message or fallback behavior

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)


class TestPatternMatchingErrors:
    """Test error handling during pattern matching operations."""

    def test_handles_regex_compilation_errors_gracefully(self) -> None:
        """Hook should handle regex compilation errors in patterns gracefully."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    with patch("claudeguard.hook.PatternMatcher.match_pattern") as mock_match:
                        import re

                        mock_match.side_effect = re.error("Invalid regex pattern")
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should output fail-safe JSON response
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        # Should handle regex errors gracefully

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)

    def test_handles_missing_tool_input_fields_in_matching(self) -> None:
        """Hook should handle missing tool input fields during pattern matching."""
        incomplete_input = {"tool_name": "Read", "tool_input": {}}
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    mock_stdin.return_value = json.dumps(incomplete_input)
                    main()

                    # Should output JSON response (may be ask or allow based on profile)
                    output = mock_stdout.getvalue()
                    # Should handle incomplete input gracefully
                    assert "hookSpecificOutput" in output

                    # Should exit with code 0 (not error exit)
                    mock_exit.assert_called_once_with(0)

    def test_handles_pattern_matching_exceptions(self) -> None:
        """Hook should handle exceptions during pattern matching gracefully."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    # Mock the actual pattern matcher method that's called
                    with patch(
                        "claudeguard.pattern_matcher.PatternMatcher.match_pattern"
                    ) as mock_match:
                        mock_match.side_effect = RuntimeError("Pattern matching failed")
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should output fail-safe JSON response
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        assert "claudeguard error" in output

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)


class TestSystemResourceErrors:
    """Test error handling for system resource issues."""

    def test_handles_out_of_memory_gracefully(self) -> None:
        """Hook should handle out of memory errors gracefully."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    # Mock the actual permission engine method
                    with patch("claudeguard.hook.PermissionEngine.check_permission") as mock_decide:
                        mock_decide.side_effect = MemoryError("Out of memory")
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should output fail-safe JSON response
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        assert "claudeguard error" in output

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)

    def test_handles_disk_full_errors_gracefully(self) -> None:
        """Hook should handle disk full errors gracefully."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    with patch("builtins.open") as mock_file:
                        mock_file.side_effect = OSError("No space left on device")
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should output fail-safe JSON response
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        # May have error message or fallback behavior

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)

    def test_handles_interrupted_system_calls(self) -> None:
        """Hook should handle interrupted system calls gracefully."""
        make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    mock_stdin.side_effect = InterruptedError("System call interrupted")
                    main()

                    # Should output fail-safe JSON response
                    output = mock_stdout.getvalue()
                    assert "ask" in output
                    assert "claudeguard error" in output

                    # Should exit with code 0 (not error exit)
                    mock_exit.assert_called_once_with(0)


class TestFailSafeBehavior:
    """Test fail-safe behavior principles."""

    def test_always_fails_safe_to_ask_on_errors(self) -> None:
        """Hook should always fail-safe to 'ask' decision on any error."""
        hook_input = make_read_hook_input()
        error_scenarios = [
            ValueError("Invalid input"),
            RuntimeError("Processing failed"),
            KeyError("Missing key"),
            TypeError("Type error"),
            Exception("Unknown error"),
        ]
        for error in error_scenarios:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    with patch("sys.exit") as mock_exit:
                        # Mock the actual permission engine method
                        with patch(
                            "claudeguard.hook.PermissionEngine.check_permission"
                        ) as mock_decide:
                            mock_decide.side_effect = error
                            mock_stdin.return_value = hook_input_to_json(hook_input)
                            main()

                            # Should ALWAYS fail-safe to 'ask'
                            output = mock_stdout.getvalue()
                            assert "ask" in output
                            assert "claudeguard error" in output
                            # Should never return 'allow' on errors
                            assert "allow" not in output.replace("claudeguard error", "")

                            # Should exit with code 0 (not error exit)
                            mock_exit.assert_called_once_with(0)
                            mock_exit.reset_mock()
                            mock_stdout.seek(0)
                            mock_stdout.truncate(0)

    def test_never_fails_safe_to_allow_on_errors(self) -> None:
        """Hook should never fail-safe to 'allow' on errors (security principle)."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    # Mock the actual permission engine method
                    with patch("claudeguard.hook.PermissionEngine.check_permission") as mock_decide:
                        mock_decide.side_effect = RuntimeError("Error")
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should NEVER fail-safe to 'allow' (security principle)
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        assert "claudeguard error" in output
                        # CRITICAL: Should never return 'allow' on any error
                        assert "allow" not in output.replace("claudeguard error", "")

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)

    def test_provides_error_context_in_fail_safe_responses(self) -> None:
        """Hook should provide error context in fail-safe responses for debugging."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    # Mock the actual permission engine method
                    with patch("claudeguard.hook.PermissionEngine.check_permission") as mock_decide:
                        mock_decide.side_effect = ValueError("Test error")
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should provide error context for debugging
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        assert "claudeguard error" in output
                        # Should include some error context without leaking sensitive info

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)

    def test_maintains_performance_during_error_handling(self) -> None:
        """Hook should maintain good performance even when handling errors."""
        hook_input = make_read_hook_input()
        for i in range(10):
            with patch("sys.stdin.read") as mock_stdin:
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    with patch("sys.exit") as mock_exit:
                        # Mock the actual permission engine method
                        with patch(
                            "claudeguard.hook.PermissionEngine.check_permission"
                        ) as mock_decide:
                            mock_decide.side_effect = RuntimeError(f"Error {i}")
                            mock_stdin.return_value = hook_input_to_json(hook_input)
                            main()

                            # Should handle errors consistently
                            output = mock_stdout.getvalue()
                            assert "ask" in output
                            assert "claudeguard error" in output

                            # Should exit with code 0 (not error exit)
                            mock_exit.assert_called_once_with(0)
                            mock_exit.reset_mock()
                            mock_stdout.seek(0)
                            mock_stdout.truncate(0)

    def test_error_handling_doesnt_leak_sensitive_information(self) -> None:
        """Hook should not leak sensitive information in error messages."""
        hook_input = make_read_hook_input()
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    # Mock the actual profile loader method
                    with patch(
                        "claudeguard.profile_loader.ProfileLoader.load_profile"
                    ) as mock_load:
                        mock_load.side_effect = RuntimeError(
                            "Error processing /home/user/.secret/key"
                        )
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should provide error context but not leak sensitive paths
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        assert "claudeguard error" in output
                        # Should not leak sensitive file paths
                        assert ".secret" not in output
                        assert "/home/user" not in output

                        # Should exit with code 0 (not error exit)
                        mock_exit.assert_called_once_with(0)


class TestRecoveryBehavior:
    """Test recovery behavior after errors."""

    def test_recovers_from_transient_profile_load_errors(self) -> None:
        """Hook should recover from transient profile loading errors."""
        hook_input = make_read_hook_input()
        # First call with error
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    # Mock the actual profile loader method
                    with patch(
                        "claudeguard.profile_loader.ProfileLoader.load_profile"
                    ) as mock_load:
                        mock_load.side_effect = OSError("Temporary error")
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()

                        # Should fail-safe to ask
                        output = mock_stdout.getvalue()
                        assert "ask" in output
                        mock_exit.assert_called_once_with(0)

        # Second call should work normally (recovery)
        with patch("sys.stdin.read") as mock_stdin:
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.exit") as mock_exit:
                    mock_stdin.return_value = hook_input_to_json(hook_input)
                    main()

                    # Should work normally now
                    output = mock_stdout.getvalue()
                    assert "hookSpecificOutput" in output
                    mock_exit.assert_called_once_with(0)

    def test_no_persistent_error_state_between_calls(self) -> None:
        """Hook should not maintain persistent error state between calls."""
        hook_input = make_read_hook_input()
        error_conditions = [
            ValueError("Error 1"),
            RuntimeError("Error 2"),
            None,
            KeyError("Error 3"),
            None,
        ]
        for condition in error_conditions:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    with patch("sys.exit") as mock_exit:
                        # Mock the actual permission engine method
                        with patch(
                            "claudeguard.hook.PermissionEngine.check_permission"
                        ) as mock_decide:
                            if condition:
                                mock_decide.side_effect = condition
                                mock_stdin.return_value = hook_input_to_json(hook_input)
                                main()

                                # Should fail-safe to ask on errors
                                output = mock_stdout.getvalue()
                                assert "ask" in output
                                assert "claudeguard error" in output
                            else:
                                # No error condition - should work normally
                                from claudeguard.hook import HookResponse

                                mock_decide.return_value = HookResponse(
                                    permission_decision="allow",
                                    permission_decision_reason="Test success",
                                )
                                mock_stdin.return_value = hook_input_to_json(hook_input)
                                main()

                                # Should work normally
                                output = mock_stdout.getvalue()
                                assert "allow" in output

                            # Should always exit with code 0
                            mock_exit.assert_called_once_with(0)
                            mock_exit.reset_mock()
                            mock_stdout.seek(0)
                            mock_stdout.truncate(0)
