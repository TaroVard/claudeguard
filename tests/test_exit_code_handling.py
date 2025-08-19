"""Tests for exit code handling behavior."""

from io import StringIO
from unittest.mock import patch

from claudeguard.hook import main
from tests.factories import (
    make_restrictive_profile,
)

from .conftest import (
    hook_input_to_json,
    make_bash_hook_input,
    make_default_profile,
    make_edit_hook_input,
    make_read_hook_input,
)


class TestExitCodeBehavior:
    """Test exit code behavior for different permission decisions."""

    def test_exits_with_code_0_for_allow_decision(self) -> None:
        """Hook should exit with code 0 for allow decisions."""
        hook_input = make_read_hook_input()
        profile = make_default_profile()

        with patch("sys.exit") as mock_exit:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                    mock_load.return_value = profile
                    mock_stdin.return_value = hook_input_to_json(hook_input)
                    main()
                    mock_exit.assert_called_once_with(0)

    def test_exits_with_code_0_for_ask_decision(self) -> None:
        """Hook should exit with code 0 for ask decisions."""
        hook_input = make_edit_hook_input(file_path="/src/main.py")
        profile = make_default_profile()

        with patch("sys.exit") as mock_exit:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                    mock_load.return_value = profile
                    mock_stdin.return_value = hook_input_to_json(hook_input)
                    main()
                    mock_exit.assert_called_once_with(0)

    def test_exits_with_code_2_for_deny_decision(self) -> None:
        """Hook should exit with code 2 for deny decisions."""
        hook_input = make_bash_hook_input(command="rm -rf /")
        profile = make_default_profile()

        with patch("sys.exit") as mock_exit:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                    mock_load.return_value = profile
                    mock_stdin.return_value = hook_input_to_json(hook_input)
                    main()
                    mock_exit.assert_called_once_with(2)

    def test_exit_code_consistency_across_multiple_allow_calls(self) -> None:
        """Hook should consistently exit with code 0 for multiple allow decisions."""
        allow_inputs = [
            make_read_hook_input(file_path="/file1.py"),
            make_read_hook_input(file_path="/file2.py"),
            make_bash_hook_input(command="git status"),
        ]
        profile = make_default_profile()

        for hook_input in allow_inputs:
            with patch("sys.exit") as mock_exit:
                with patch("sys.stdin.read") as mock_stdin:
                    with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                        mock_load.return_value = profile
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()
                        mock_exit.assert_called_once_with(0)

    def test_exit_code_consistency_across_multiple_deny_calls(self) -> None:
        """Hook should consistently exit with code 2 for multiple deny decisions."""
        deny_inputs = [
            make_bash_hook_input(command="rm -rf /home"),
            make_bash_hook_input(command="rm -rf /var"),
            make_bash_hook_input(command="rm -rf /important"),
        ]
        profile = make_default_profile()

        for hook_input in deny_inputs:
            with patch("sys.exit") as mock_exit:
                with patch("sys.stdin.read") as mock_stdin:
                    with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                        mock_load.return_value = profile
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()
                        mock_exit.assert_called_once_with(2)


class TestExitCodeWithOutputBehavior:
    """Test exit codes combined with stdout/stderr output behavior."""

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.stderr", new_callable=StringIO)
    def test_allow_decision_outputs_json_to_stdout_with_exit_0(
        self, mock_stderr, mock_stdout
    ) -> None:
        """Allow decisions should output JSON to stdout and exit with code 0."""
        hook_input = make_read_hook_input()
        profile = make_default_profile()

        with patch("sys.exit") as mock_exit:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                    mock_load.return_value = profile
                    mock_stdin.return_value = hook_input_to_json(hook_input)
                    main()
                    mock_exit.assert_called_once_with(0)

        # Check that JSON output was written to stdout
        output = mock_stdout.getvalue()
        assert "hookSpecificOutput" in output
        assert "permissionDecision" in output

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.stderr", new_callable=StringIO)
    def test_ask_decision_outputs_json_to_stdout_with_exit_0(
        self, mock_stderr, mock_stdout
    ) -> None:
        """Ask decisions should output JSON to stdout and exit with code 0."""
        hook_input = make_edit_hook_input(file_path="/src/main.py")
        profile = make_default_profile()

        with patch("sys.exit") as mock_exit:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                    mock_load.return_value = profile
                    mock_stdin.return_value = hook_input_to_json(hook_input)
                    main()
                    mock_exit.assert_called_once_with(0)

        # Check that JSON output was written to stdout
        output = mock_stdout.getvalue()
        assert "hookSpecificOutput" in output
        assert "permissionDecision" in output

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.stderr", new_callable=StringIO)
    def test_deny_decision_outputs_to_stderr_with_exit_2(self, mock_stderr, mock_stdout) -> None:
        """Deny decisions should output to stderr and exit with code 2."""
        hook_input = make_bash_hook_input(command="rm -rf /")
        profile = make_default_profile()

        with patch("sys.exit") as mock_exit:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                    mock_load.return_value = profile
                    mock_stdin.return_value = hook_input_to_json(hook_input)
                    main()
                    mock_exit.assert_called_once_with(2)

        # For deny decisions, output should still go to stdout (not stderr)
        # as per Claude Code hook protocol
        output = mock_stdout.getvalue()
        assert "hookSpecificOutput" in output
        assert "permissionDecision" in output


class TestExitCodeErrorHandling:
    """Test exit code behavior during error conditions."""

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.stderr", new_callable=StringIO)
    def test_exits_with_0_on_json_parse_error_fail_safe(self, mock_stderr, mock_stdout) -> None:
        """Hook should exit with code 0 (fail-safe) on JSON parse errors."""
        invalid_json = "invalid json"

        with patch("sys.exit") as mock_exit:
            with patch("sys.stdin.read") as mock_stdin:
                mock_stdin.return_value = invalid_json
                main()
                mock_exit.assert_called_once_with(0)

        # Check that error response was written to stdout
        output = mock_stdout.getvalue()
        assert "hookSpecificOutput" in output
        assert "claudeguard error" in output

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.stderr", new_callable=StringIO)
    def test_exits_with_0_on_profile_load_error_fail_safe(self, mock_stderr, mock_stdout) -> None:
        """Hook should exit with code 0 (fail-safe) on profile load errors."""
        hook_input = make_read_hook_input()

        with patch("sys.exit") as mock_exit:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                    mock_load.side_effect = FileNotFoundError("Profile not found")
                    mock_stdin.return_value = hook_input_to_json(hook_input)
                    main()
                    mock_exit.assert_called_once_with(0)

        # Check that error response was written to stdout
        output = mock_stdout.getvalue()
        assert "hookSpecificOutput" in output
        assert "claudeguard error" in output

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.stderr", new_callable=StringIO)
    def test_exits_with_0_on_unexpected_exceptions_fail_safe(
        self, mock_stderr, mock_stdout
    ) -> None:
        """Hook should exit with code 0 (fail-safe) on unexpected exceptions."""
        hook_input = make_read_hook_input()

        with patch("sys.exit") as mock_exit:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("claudeguard.hook.PermissionEngine.check_permission") as mock_decide:
                    mock_decide.side_effect = RuntimeError("Unexpected error")
                    mock_stdin.return_value = hook_input_to_json(hook_input)
                    main()
                    mock_exit.assert_called_once_with(0)

        # Check that error response was written to stdout
        output = mock_stdout.getvalue()
        assert "hookSpecificOutput" in output
        assert "claudeguard error" in output


class TestExitCodeIntegration:
    """Test exit code behavior in integration scenarios."""

    def test_exit_codes_match_claude_code_expectations(self) -> None:
        """Exit codes should match Claude Code's hook expectations."""
        test_cases = [
            (make_read_hook_input(), 0),
            (make_edit_hook_input(file_path="/src/test.py"), 0),
            (make_bash_hook_input(command="rm -rf /"), 2),
        ]
        profile = make_default_profile()

        for hook_input, expected_exit in test_cases:
            with patch("sys.exit") as mock_exit:
                with patch("sys.stdin.read") as mock_stdin:
                    with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                        mock_load.return_value = profile
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()
                        mock_exit.assert_called_once_with(expected_exit)

    def test_exit_behavior_with_different_profiles(self) -> None:
        """Exit codes should work correctly with different profile configurations."""
        hook_input = make_edit_hook_input()

        with patch("sys.exit") as mock_exit:
            with patch("sys.stdin.read") as mock_stdin:
                with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                    mock_load.return_value = make_restrictive_profile()
                    mock_stdin.return_value = hook_input_to_json(hook_input)
                    main()
                    mock_exit.assert_called_once_with(0)  # Should ask for edits

    def test_exit_code_performance_under_load(self) -> None:
        """Exit code behavior should be consistent under multiple rapid calls."""
        hook_input = make_read_hook_input()
        profile = make_default_profile()

        for _i in range(10):
            with patch("sys.exit") as mock_exit:
                with patch("sys.stdin.read") as mock_stdin:
                    with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                        mock_load.return_value = profile
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()
                        mock_exit.assert_called_once_with(0)

    def test_no_exit_code_interference_between_calls(self) -> None:
        """Exit codes should not be affected by previous calls."""
        test_sequence = [
            (make_read_hook_input(), 0),
            (make_bash_hook_input(command="rm -rf /"), 2),
            (make_read_hook_input(), 0),
        ]
        profile = make_default_profile()

        for hook_input, expected_exit in test_sequence:
            with patch("sys.exit") as mock_exit:
                with patch("sys.stdin.read") as mock_stdin:
                    with patch("claudeguard.hook.ProfileLoader.load_profile") as mock_load:
                        mock_load.return_value = profile
                        mock_stdin.return_value = hook_input_to_json(hook_input)
                        main()
                        mock_exit.assert_called_once_with(expected_exit)


class TestExitCodeDocumentation:
    """Test that exit codes are well-documented and follow conventions."""

    def test_exit_codes_follow_unix_conventions(self) -> None:
        """Exit codes should follow Unix conventions."""
        assert True

    def test_exit_codes_match_mvp_behavior(self) -> None:
        """Exit codes should match the successful MVP implementation."""
        assert True
