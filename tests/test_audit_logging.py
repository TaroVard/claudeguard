"""Tests for audit logging system."""

from __future__ import annotations

import json
from unittest.mock import patch

from claudeguard.hook import AuditLogger, find_repo_root
from tests.factories import create_hook_input, create_hook_response


class TestAuditLogger:
    """Test audit logging functionality."""

    def test_audit_logger_uses_repo_local_claudeguard_directory(self, tmp_path) -> None:
        """Audit logger should store logs in current repo's .claudeguard directory."""
        with patch("claudeguard.hook.find_repo_root", return_value=tmp_path):
            audit_logger = AuditLogger()

        expected_path = tmp_path / ".claudeguard" / "audit.log"
        assert audit_logger.audit_log_path == expected_path

    def test_audit_logger_creates_claudeguard_directory_if_missing(self, tmp_path) -> None:
        """Audit logger should create .claudeguard directory if it doesn't exist."""
        with patch("claudeguard.hook.find_repo_root", return_value=tmp_path):
            AuditLogger()

        claudeguard_dir = tmp_path / ".claudeguard"
        assert claudeguard_dir.exists()
        assert claudeguard_dir.is_dir()

    def test_audit_logger_falls_back_to_home_when_not_in_git_repo(
        self, tmp_path
    ) -> None:
        """When not in a git repo, audit logger should fall back to ~/.claudeguard."""
        with patch("claudeguard.hook.find_repo_root", return_value=None):
            with patch("pathlib.Path.home", return_value=tmp_path):
                audit_logger = AuditLogger()

        expected_path = tmp_path / ".claudeguard" / "audit.log"
        assert audit_logger.audit_log_path == expected_path

    def test_simplified_audit_log_format(self, tmp_path) -> None:
        """Audit log should only contain tool input, tool output, and matched rule."""
        with patch("claudeguard.hook.find_repo_root", return_value=tmp_path):
            audit_logger = AuditLogger()

        hook_input = create_hook_input(
            tool_name="Read", tool_input={"file_path": "/path/to/file.py"}
        )
        hook_response = create_hook_response(
            permission_decision="allow",
            permission_decision_reason="claudeguard: Rule matched: Read(*) → allow",
        )
        matched_rule = "Read(*)"

        audit_logger.log_hook_invocation(hook_input, hook_response, matched_rule)

        log_file = tmp_path / ".claudeguard" / "audit.log"
        assert log_file.exists()

        log_content = log_file.read_text()
        log_entry = json.loads(log_content.strip())

        expected_keys = {"tool_input", "tool_output", "matched_rule"}
        assert set(log_entry.keys()) == expected_keys

        assert log_entry["tool_input"] == {
            "tool_name": "Read",
            "tool_input": {"file_path": "/path/to/file.py"},
        }
        assert log_entry["tool_output"] == {
            "permission_decision": "allow",
            "permission_decision_reason": "claudeguard: Rule matched: Read(*) → allow",
        }
        assert log_entry["matched_rule"] == "Read(*)"

    def test_audit_log_handles_no_matched_rule(self, tmp_path) -> None:
        """When no rule matches, matched_rule should be null."""
        with patch("claudeguard.hook.find_repo_root", return_value=tmp_path):
            audit_logger = AuditLogger()

        hook_input = create_hook_input(
            tool_name="SomeUnknownTool", tool_input={"param": "value"}
        )
        hook_response = create_hook_response(
            permission_decision="ask",
            permission_decision_reason=(
                "claudeguard: No matching rules found (fallback to ask)"
            ),
        )
        matched_rule = None

        audit_logger.log_hook_invocation(hook_input, hook_response, matched_rule)

        log_file = tmp_path / ".claudeguard" / "audit.log"
        log_content = log_file.read_text()
        log_entry = json.loads(log_content.strip())

        assert log_entry["matched_rule"] is None

    def test_audit_log_appends_multiple_entries(self, tmp_path) -> None:
        """Multiple audit entries should be appended to the same log file."""
        with patch("claudeguard.hook.find_repo_root", return_value=tmp_path):
            audit_logger = AuditLogger()

        hook_input1 = create_hook_input(
            tool_name="Read", tool_input={"file_path": "file1.py"}
        )
        hook_response1 = create_hook_response(permission_decision="allow")
        audit_logger.log_hook_invocation(hook_input1, hook_response1, "Read(*)")

        hook_input2 = create_hook_input(
            tool_name="Edit", tool_input={"file_path": "file2.py"}
        )
        hook_response2 = create_hook_response(permission_decision="ask")
        audit_logger.log_hook_invocation(hook_input2, hook_response2, None)

        log_file = tmp_path / ".claudeguard" / "audit.log"
        log_lines = log_file.read_text().strip().split("\n")

        assert len(log_lines) == 2

        entry1 = json.loads(log_lines[0])
        entry2 = json.loads(log_lines[1])

        assert entry1["tool_input"]["tool_input"]["file_path"] == "file1.py"
        assert entry2["tool_input"]["tool_input"]["file_path"] == "file2.py"

    def test_no_verbose_logging_to_stderr_or_multiple_files(self, tmp_path) -> None:
        """Audit logger should not create verbose logs or log to stderr."""
        with patch("claudeguard.hook.find_repo_root", return_value=tmp_path):
            audit_logger = AuditLogger()

        hook_input = create_hook_input()
        hook_response = create_hook_response()

        audit_logger.log_hook_invocation(hook_input, hook_response, "Read(*)")

        claudeguard_dir = tmp_path / ".claudeguard"
        log_files = list(claudeguard_dir.glob("*"))

        assert len(log_files) == 1
        assert log_files[0].name == "audit.log"


class TestGitRepoDetection:
    """Test git repository detection functionality."""

    def test_find_repo_root_finds_git_directory(self, tmp_path) -> None:
        """Should find git repo root by looking for .git directory."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        nested_dir = repo_root / "src" / "claudeguard"
        nested_dir.mkdir(parents=True)

        with patch("pathlib.Path.cwd", return_value=nested_dir):
            result = find_repo_root()

        assert result == repo_root

    def test_find_repo_root_returns_none_when_not_in_repo(self, tmp_path) -> None:
        """Should return None when not in a git repository."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = find_repo_root()

        assert result is None

    def test_find_repo_root_stops_at_filesystem_root(self, tmp_path) -> None:
        """Should stop searching at filesystem root if no .git found."""
        mock_path = tmp_path / "very" / "deep" / "nested" / "path"
        mock_path.mkdir(parents=True)

        with patch("pathlib.Path.cwd", return_value=mock_path):
            result = find_repo_root()

        assert result is None
