"""
Test profile loading system with comprehensive behavior coverage.

This module tests the core profile loading functionality including:
- Project-based profile loading (.claudeguard/profiles/)
- Home directory fallback loading
- Default profile generation
- YAML parsing and validation
- Error handling for malformed profiles

Following TDD principles - these tests will fail until ProfileLoader is implemented.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from claudeguard.models import Profile, ProfileRule
from claudeguard.profile_loader import ProfileLoader, ProfileLoadError
from tests.conftest import (
    make_default_rules,
    make_yaml_profile_data,
)


class TestProjectBasedProfileLoading:
    """Test loading profiles from project .claudeguard directory."""

    def test_loads_profile_from_project_claudeguard_directory(self, project_dir) -> None:
        """Should load profile from .claudeguard/profiles/default.yaml in project directory."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)

        profile_data = make_yaml_profile_data(name="project-profile")
        profile_file = profiles_dir / "default.yaml"

        with open(profile_file, "w") as f:
            yaml.dump(profile_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()
        assert isinstance(profile, Profile)
        assert profile.metadata.name == "project-profile"
        assert len(profile.rules) == 4

    def test_preserves_rule_order_from_yaml(self, project_dir) -> None:
        """Should preserve the order of rules as defined in YAML."""
        profile_data = make_yaml_profile_data(
            name="ordered-profile",
            rules=[
                {"pattern": "Read(*)", "action": "allow", "comment": "First rule"},
                {"pattern": "Edit(*.py)", "action": "ask", "comment": "Second rule"},
                {"pattern": "Bash(rm*)", "action": "deny", "comment": "Third rule"},
                {"pattern": "*", "action": "ask", "comment": "Fourth rule"},
            ],
        )
        profiles_dir = project_dir / ".claudeguard" / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profiles_dir / "default.yaml"

        with open(profile_file, "w") as f:
            yaml.dump(profile_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()
        assert profile.rules[0].comment == "First rule"
        assert profile.rules[1].comment == "Second rule"
        assert profile.rules[2].comment == "Third rule"
        assert profile.rules[3].comment == "Fourth rule"

    def test_converts_yaml_rules_to_profile_rule_objects(self, project_dir) -> None:
        """Should convert YAML rule dictionaries to ProfileRule objects."""
        profile_data = make_yaml_profile_data(
            rules=[
                {"pattern": "Read(*)", "action": "allow", "comment": "Allow reads"},
                {
                    "pattern": "Edit(*.py)",
                    "action": "deny",
                    "comment": "Deny Python edits",
                },
            ]
        )
        profiles_dir = project_dir / ".claudeguard" / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profiles_dir / "default.yaml"

        with open(profile_file, "w") as f:
            yaml.dump(profile_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert len(profile.rules) == 2

        first_rule = profile.rules[0]
        assert isinstance(first_rule, ProfileRule)
        assert first_rule.pattern == "Read(*)"
        assert first_rule.action == "allow"
        assert first_rule.comment == "Allow reads"

        second_rule = profile.rules[1]
        assert isinstance(second_rule, ProfileRule)
        assert second_rule.pattern == "Edit(*.py)"
        assert second_rule.action == "deny"
        assert second_rule.comment == "Deny Python edits"

    def test_handles_rules_without_comments(self, project_dir) -> None:
        """Should handle rules that don't specify comments."""
        profile_data = {
            "name": "minimal-profile",
            "description": "Profile with minimal rule data",
            "version": "1.0",
            "created_by": "test",
            "rules": [
                {"pattern": "Read(*)", "action": "allow"},
                {"pattern": "*", "action": "ask"},
            ],
        }
        profiles_dir = project_dir / ".claudeguard" / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profiles_dir / "default.yaml"

        with open(profile_file, "w") as f:
            yaml.dump(profile_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert profile.rules[0].comment == ""
        assert profile.rules[1].comment == ""

    def test_finds_project_directory_by_walking_up_tree(self, temp_dir) -> None:
        """Should walk up directory tree to find .claudeguard directory."""
        project_root = temp_dir / "my-project"
        project_root.mkdir()
        claudeguard_dir = project_root / ".claudeguard"
        claudeguard_dir.mkdir()

        nested_dir = project_root / "src" / "subdir" / "deeply" / "nested"
        nested_dir.mkdir(parents=True)

        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_data = make_yaml_profile_data(name="found-profile")
        profile_file = profiles_dir / "default.yaml"

        with open(profile_file, "w") as f:
            yaml.dump(profile_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=nested_dir):
            profile = loader.load_profile()

        assert profile.metadata.name == "found-profile"

    def test_stops_searching_at_filesystem_root(self, temp_dir) -> None:
        """Should stop searching when reaching filesystem root
        without finding .claudeguard."""
        no_claudeguard_dir = temp_dir / "no-claudeguard-project"
        no_claudeguard_dir.mkdir()

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=no_claudeguard_dir):
            with patch("pathlib.Path.home", return_value=temp_dir / "fake-home"):
                profile = loader.load_profile()

        assert isinstance(profile, Profile)


class TestHomeDirectoryFallback:
    """Test fallback to home directory profile loading."""

    def test_falls_back_to_home_directory_when_no_project_profile(self, temp_dir) -> None:
        """Should load profile from ~/.claudeguard/profiles/default.yaml when project has none."""
        project_dir = temp_dir / "project-without-profile"
        project_dir.mkdir()

        home_dir = temp_dir / "home"
        home_dir.mkdir()
        home_claudeguard = home_dir / ".claudeguard"
        home_profiles_dir = home_claudeguard / "profiles"
        home_profiles_dir.mkdir(parents=True)

        profile_data = make_yaml_profile_data(name="home-profile")
        home_profile_file = home_profiles_dir / "default.yaml"

        with open(home_profile_file, "w") as f:
            yaml.dump(profile_data, f)

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with patch("pathlib.Path.home", return_value=home_dir):
                loader = ProfileLoader(project_root=project_dir, home_directory=home_dir)
                profile = loader.load_profile()

        assert profile.metadata.name == "home-profile"

    def test_prefers_project_profile_over_home_profile(self, temp_dir) -> None:
        """Should prefer project profile when both project and home profiles exist."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        project_claudeguard = project_dir / ".claudeguard"
        project_profiles_dir = project_claudeguard / "profiles"
        project_profiles_dir.mkdir(parents=True)

        home_dir = temp_dir / "home"
        home_dir.mkdir()
        home_claudeguard = home_dir / ".claudeguard"
        home_profiles_dir = home_claudeguard / "profiles"
        home_profiles_dir.mkdir(parents=True)

        project_data = make_yaml_profile_data(name="project-profile")
        project_file = project_profiles_dir / "default.yaml"
        with open(project_file, "w") as f:
            yaml.dump(project_data, f)

        home_data = make_yaml_profile_data(name="home-profile")
        home_file = home_profiles_dir / "default.yaml"
        with open(home_file, "w") as f:
            yaml.dump(home_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with patch("pathlib.Path.home", return_value=home_dir):
                profile = loader.load_profile()

        assert profile.metadata.name == "project-profile"

    def test_handles_missing_home_claudeguard_directory(self, temp_dir) -> None:
        """Should handle missing ~/.claudeguard/profiles directory gracefully."""
        project_dir = temp_dir / "project-without-profile"
        project_dir.mkdir()

        home_dir = temp_dir / "home-without-claudeguard"
        home_dir.mkdir()

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with patch("pathlib.Path.home", return_value=home_dir):
                profile = loader.load_profile()

        assert isinstance(profile, Profile)


class TestDefaultProfileGeneration:
    """Test default profile generation when no profiles are found."""

    def test_generates_default_profile_when_no_profiles_exist(self, temp_dir) -> None:
        """Should generate sensible default profile when no config files exist."""
        empty_project = temp_dir / "empty-project"
        empty_project.mkdir()

        empty_home = temp_dir / "empty-home"
        empty_home.mkdir()

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=empty_project):
            with patch("pathlib.Path.home", return_value=empty_home):
                profile = loader.load_profile()

        assert isinstance(profile, Profile)
        assert profile.metadata.name == "default"
        assert len(profile.rules) > 0

    def test_default_profile_contains_expected_rules(self, temp_dir) -> None:
        """Default profile should contain comprehensive security rules."""
        empty_project = temp_dir / "empty-project"
        empty_project.mkdir()

        empty_home = temp_dir / "empty-home"
        empty_home.mkdir()

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=empty_project):
            with patch("pathlib.Path.home", return_value=empty_home):
                profile = loader.load_profile()

        rule_patterns = [rule.pattern for rule in profile.rules]

        assert "Read(*)" in rule_patterns
        assert "Edit(*.md)" in rule_patterns
        assert "Edit(src/**)" in rule_patterns
        assert "Edit(*.py)" in rule_patterns
        assert "Bash(git status)" in rule_patterns
        assert "Bash(git diff)" in rule_patterns
        assert "Bash(git log*)" in rule_patterns
        assert "Bash(git push*)" in rule_patterns
        assert "Bash(rm -rf*)" in rule_patterns
        assert "*" in rule_patterns

    def test_default_profile_rule_actions_are_secure(self, temp_dir) -> None:
        """Default profile should have secure action defaults."""
        empty_project = temp_dir / "empty-project"
        empty_project.mkdir()

        empty_home = temp_dir / "empty-home"
        empty_home.mkdir()

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=empty_project):
            with patch("pathlib.Path.home", return_value=empty_home):
                profile = loader.load_profile()

        rule_actions = {rule.pattern: rule.action for rule in profile.rules}

        assert rule_actions["Read(*)"] == "allow"
        assert rule_actions["Edit(*.md)"] == "allow"
        assert rule_actions["Edit(src/**)"] == "ask"
        assert rule_actions["Edit(*.py)"] == "ask"
        assert rule_actions["Bash(git status)"] == "allow"
        assert rule_actions["Bash(git diff)"] == "allow"
        assert rule_actions["Bash(git log*)"] == "allow"
        assert rule_actions["Bash(git push*)"] == "ask"
        assert rule_actions["Bash(rm -rf*)"] == "deny"
        assert rule_actions["*"] == "ask"

    def test_default_profile_uses_factory_rules(self) -> None:
        """Default profile should use the same rules as factory."""
        loader = ProfileLoader()
        expected_rules = make_default_rules()

        with patch("pathlib.Path.cwd", return_value=Path("/nonexistent")):
            with patch("pathlib.Path.home", return_value=Path("/nonexistent")):
                profile = loader.load_profile()

        actual_patterns = [(rule.pattern, rule.action) for rule in profile.rules]
        expected_patterns = [(rule.pattern, rule.action) for rule in expected_rules]

        assert actual_patterns == expected_patterns


class TestProfileLoaderConfiguration:
    """Test ProfileLoader configuration and customization."""

    def test_profile_loader_accepts_custom_project_root(self, temp_dir) -> None:
        """Should allow overriding project root directory."""
        custom_project = temp_dir / "custom-project"
        custom_project.mkdir()
        claudeguard_dir = custom_project / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir(parents=True)

        profile_data = make_yaml_profile_data(name="custom-root-profile")
        profile_file = profiles_dir / "default.yaml"

        with open(profile_file, "w") as f:
            yaml.dump(profile_data, f)

        loader = ProfileLoader(project_root=custom_project)
        profile = loader.load_profile()

        assert profile.metadata.name == "custom-root-profile"

    def test_profile_loader_accepts_custom_home_directory(self, temp_dir) -> None:
        """Should allow overriding home directory."""
        project_dir = temp_dir / "project-no-profile"
        project_dir.mkdir()

        custom_home = temp_dir / "custom-home"
        custom_home.mkdir()
        claudeguard_dir = custom_home / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir(parents=True)

        profile_data = make_yaml_profile_data(name="custom-home-profile")
        profile_file = profiles_dir / "default.yaml"

        with open(profile_file, "w") as f:
            yaml.dump(profile_data, f)

        with patch("pathlib.Path.cwd", return_value=project_dir):
            loader = ProfileLoader(project_root=project_dir, home_directory=custom_home)
            profile = loader.load_profile()

        assert profile.metadata.name == "custom-home-profile"


class TestProfileLoaderErrorHandling:
    """Test error handling in profile loading."""

    def test_raises_profile_load_error_for_invalid_yaml(self, project_dir) -> None:
        """Should raise ProfileLoadError for invalid YAML syntax."""
        profiles_dir = project_dir / ".claudeguard" / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profiles_dir / "default.yaml"
        profile_file.write_text("{ invalid: yaml: content")

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with pytest.raises(ProfileLoadError) as exc_info:
                loader.load_profile()

            assert "Failed to load profile from" in str(exc_info.value)

    def test_raises_profile_load_error_for_missing_required_fields(self, project_dir) -> None:
        """Should raise ProfileLoadError when required fields are missing."""
        incomplete_data = {"description": "Missing name field"}
        profiles_dir = project_dir / ".claudeguard" / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profiles_dir / "default.yaml"

        with open(profile_file, "w") as f:
            yaml.dump(incomplete_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with pytest.raises(ProfileLoadError) as exc_info:
                loader.load_profile()

            assert "Missing required field" in str(exc_info.value)

    def test_raises_profile_load_error_for_invalid_rule_structure(self, project_dir) -> None:
        """Should raise ProfileLoadError for malformed rule entries."""
        invalid_data = {
            "name": "invalid-rules-profile",
            "description": "Profile with invalid rules",
            "version": "1.0",
            "created_by": "test",
            "rules": ["invalid_rule_string", {"pattern": "Read(*)", "action": "allow"}],
        }
        profiles_dir = project_dir / ".claudeguard" / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profiles_dir / "default.yaml"

        with open(profile_file, "w") as f:
            yaml.dump(invalid_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with pytest.raises(ProfileLoadError) as exc_info:
                loader.load_profile()

            assert "Invalid rule structure" in str(exc_info.value)

    def test_raises_profile_load_error_for_invalid_action_values(self, project_dir) -> None:
        """Should raise ProfileLoadError for invalid action values."""
        invalid_data = make_yaml_profile_data(
            rules=[
                {
                    "pattern": "Read(*)",
                    "action": "invalid_action",
                    "comment": "Bad action",
                },
            ]
        )
        profiles_dir = project_dir / ".claudeguard" / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profiles_dir / "default.yaml"

        with open(profile_file, "w") as f:
            yaml.dump(invalid_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with pytest.raises(ProfileLoadError) as exc_info:
                loader.load_profile()

            assert "Invalid action value" in str(exc_info.value)

    def test_includes_file_path_in_error_messages(self, project_dir) -> None:
        """Should include the profile file path in error messages for debugging."""
        profiles_dir = project_dir / ".claudeguard" / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        profile_file = profiles_dir / "default.yaml"
        profile_file.write_text("{ invalid: yaml")

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with pytest.raises(ProfileLoadError) as exc_info:
                loader.load_profile()

            assert str(profile_file) in str(exc_info.value)
