"""Pytest configuration and shared fixtures."""

import json
import tempfile
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml

from claudeguard.default_rules import get_default_rules
from claudeguard.models import Profile, ProfileMetadata, ProfileRule
from tests.factories import (
    Decision,
    make_claude_settings_content,
    make_decision,
)


@dataclass(frozen=True)
class HookInput:
    """Represents input to the claudeguard hook from Claude Code."""

    tool_name: str
    tool_input: dict[str, Any]


def make_profile(**overrides) -> Profile:
    overrides = dict(overrides)

    if "metadata" in overrides:
        metadata = overrides.pop("metadata")
        if not isinstance(metadata, ProfileMetadata):
            raise TypeError("metadata must be ProfileMetadata instance")
    else:
        metadata_overrides = {}
        for key in ["name", "description", "version", "created_by"]:
            if key in overrides:
                metadata_overrides[key] = overrides.pop(key)
        metadata = make_profile_metadata(**metadata_overrides)

    if "rules" in overrides:
        rules = overrides.pop("rules")
        if isinstance(rules, list):
            rules = tuple(rules)
        elif not isinstance(rules, tuple):
            rules = (rules,) if rules is not None else ()
    else:
        rules = make_default_rules()

    return Profile(metadata=metadata, rules=rules)


def make_default_profile() -> Profile:
    return make_profile(
        name="default", description="Default security profile with balanced rules"
    )


def make_profile_metadata(**overrides) -> ProfileMetadata:
    defaults = {
        "name": "test-profile",
        "description": "Test profile for testing",
        "version": "1.0",
        "created_by": "test",
    }
    return ProfileMetadata(**{**defaults, **overrides})


def make_profile_rule(
    pattern: str | None = None, action: str | None = None, **overrides
) -> ProfileRule:
    defaults = {
        "pattern": "Read(*)",
        "action": "allow",
        "comment": "Safe read operations",
    }

    if pattern is not None:
        overrides["pattern"] = pattern
    if action is not None:
        overrides["action"] = action

    return ProfileRule(**{**defaults, **overrides})


def make_yaml_profile_data(**overrides) -> dict:
    defaults = {
        "name": "test-profile",
        "description": "Test profile for testing",
        "version": "1.0",
        "created_by": "test",
        "rules": [
            {"pattern": "Read(*)", "action": "allow", "comment": "Safe reads"},
            {"pattern": "Edit(*.md)", "action": "allow", "comment": "Safe edits"},
            {"pattern": "Bash(git status)", "action": "allow", "comment": "Safe git"},
            {"pattern": "*", "action": "ask", "comment": "Default ask"},
        ],
    }
    return {**defaults, **overrides}


def make_default_rules() -> tuple[ProfileRule, ...]:
    return get_default_rules()


def make_hook_input(**overrides) -> HookInput:
    defaults = {"tool_name": "Read", "tool_input": {"file_path": "/test/example.py"}}
    return HookInput(**{**defaults, **overrides})


def make_read_hook_input(file_path: str = "/test/example.py", **overrides) -> HookInput:
    tool_input = {"file_path": file_path, **overrides}
    return make_hook_input(tool_name="Read", tool_input=tool_input)


def make_edit_hook_input(file_path: str = "/src/main.py", **overrides) -> HookInput:
    tool_input = {"file_path": file_path, **overrides}
    return make_hook_input(tool_name="Edit", tool_input=tool_input)


def make_bash_hook_input(command: str = "git status", **overrides) -> HookInput:
    tool_input = {"command": command, **overrides}
    return make_hook_input(tool_name="Bash", tool_input=tool_input)


def make_write_hook_input(
    file_path: str = "/output.txt", content: str = "test", **overrides
) -> HookInput:
    tool_input = {"file_path": file_path, "content": content, **overrides}
    return make_hook_input(tool_name="Write", tool_input=tool_input)


def hook_input_to_json(hook_input: HookInput) -> str:
    data = {"tool_name": hook_input.tool_name, "tool_input": hook_input.tool_input}
    return json.dumps(data)


@pytest.fixture
def project_dir() -> Generator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        claudeguard_dir = project_path / ".claudeguard"
        claudeguard_dir.mkdir()
        yield project_path


@pytest.fixture
def temp_dir() -> Generator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_project_dir() -> Generator[Path]:
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_claude_project(temp_project_dir: Path) -> Path:
    claude_dir = temp_project_dir / ".claude"
    claude_dir.mkdir()

    settings_file = claude_dir / "settings.local.json"
    settings_file.write_text("{}")

    return temp_project_dir


@pytest.fixture
def mock_claudeguard_project(mock_claude_project: Path) -> Path:
    project_dir = mock_claude_project

    # Create claudeguard structure
    claudeguard_dir = project_dir / ".claudeguard"
    claudeguard_dir.mkdir()

    profiles_dir = claudeguard_dir / "profiles"
    profiles_dir.mkdir()

    cache_dir = claudeguard_dir / "cache"
    cache_dir.mkdir()

    # Create default profile
    default_profile = profiles_dir / "default.yaml"
    profile_content = """name: default
description: Default test profile
version: "1.0.0"

rules:
  - pattern: "Read(*)"
    action: allow
  - pattern: "Edit(*.md)"
    action: allow
  - pattern: "Bash(git status)"
    action: allow
  - pattern: "Bash(rm -rf*)"
    action: deny
  - pattern: "*"
    action: ask
"""
    default_profile.write_text(profile_content)

    # Set active profile
    active_profile_file = claudeguard_dir / "active-profile"
    active_profile_file.write_text("default")

    return project_dir


@pytest.fixture
def mock_git_repository(temp_project_dir: Path) -> Path:
    git_dir = temp_project_dir / ".git"
    git_dir.mkdir()

    return temp_project_dir


@pytest.fixture
def sample_profile() -> Profile:
    return make_profile(
        name="test-profile",
        description="Sample profile for testing",
    )


@pytest.fixture
def sample_decisions() -> list[Decision]:
    return [
        make_decision(
            tool_signature="Read(/src/main.py)", action="allow", rule_pattern="Read(*)"
        ),
        make_decision(
            tool_signature="Edit(/docs/readme.md)",
            action="allow",
            rule_pattern="Edit(*.md)",
        ),
        make_decision(
            tool_signature="Bash(git status)",
            action="allow",
            rule_pattern="Bash(git status)",
        ),
        make_decision(
            tool_signature="Bash(rm -rf /)", action="deny", rule_pattern="Bash(rm -rf*)"
        ),
    ]


@pytest.fixture
def claude_settings_with_hooks() -> dict[str, Any]:
    return make_claude_settings_content()


@pytest.fixture
def mock_user_input() -> Any:
    class MockInput:
        def __init__(self):
            self.responses = []
            self.index = 0

        def add_response(self, response: str):
            self.responses.append(response)

        def __call__(self, prompt: str = "") -> str:
            if self.index < len(self.responses):
                response = self.responses[self.index]
                self.index += 1
                return response
            return "y"  # Default to yes

    return MockInput()


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "filesystem: marks tests that perform filesystem operations"
    )


def assert_command_succeeded(result, message="Command should have succeeded") -> None:
    assert result.exit_code == 0, (
        f"{message}. Exit code: {result.exit_code}, stderr: {result.stderr_lines}"
    )


def assert_command_failed(result, message="Command should have failed") -> None:
    assert result.exit_code != 0, f"{message}. Command unexpectedly succeeded."


def assert_file_contains(
    file_path: Path,
    expected_content: str,
    message="File should contain expected content",
) -> None:
    assert file_path.exists(), f"File {file_path} does not exist"
    content = file_path.read_text()
    assert expected_content in content, (
        f"{message}. Expected '{expected_content}' in file content: {content}"
    )


def assert_valid_json(
    file_path: Path, message="File should contain valid JSON"
) -> None:
    assert file_path.exists(), f"File {file_path} does not exist"
    try:
        with open(file_path) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"{message}. JSON decode error: {e}")


def assert_valid_yaml(
    file_path: Path, message="File should contain valid YAML"
) -> None:
    assert file_path.exists(), f"File {file_path} does not exist"
    try:
        with open(file_path) as f:
            yaml.safe_load(f)
    except yaml.YAMLError as e:
        pytest.fail(f"{message}. YAML parse error: {e}")
    except ImportError:
        content = file_path.read_text().strip()
        assert len(content) > 0, f"{message}. File is empty"


pytest.assert_command_succeeded = assert_command_succeeded
pytest.assert_command_failed = assert_command_failed
pytest.assert_file_contains = assert_file_contains
pytest.assert_valid_json = assert_valid_json
pytest.assert_valid_yaml = assert_valid_yaml
