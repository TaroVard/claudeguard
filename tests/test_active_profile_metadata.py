"""
Test active_profile metadata approach for ProfileLoader.

This module tests the new lightweight metadata system that replaces file copying:
- ProfileLoader reads active_profile file to determine which profile to load
- Profiles are stored in .claudeguard/profiles/{name}.yaml
- Default behavior when active_profile doesn't exist
- Error handling for missing/corrupted files

Following TDD principles - these tests will fail until the new active_profile system is implemented.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
import yaml

from claudeguard.models import Profile
from claudeguard.profile_loader import ProfileLoader, ProfileLoadError
from tests.conftest import make_yaml_profile_data


class TestActiveProfileMetadataLoading:
    """Test ProfileLoader with active_profile metadata system."""

    def test_loads_profile_specified_in_active_profile_file(self, project_dir) -> None:
        """Should load profile specified in .claudeguard/active_profile file from profiles/ directory."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Create developer profile in profiles directory
        developer_profile_data = make_yaml_profile_data(
            name="developer",
            description="Developer profile with relaxed rules",
            rules=[
                {"pattern": "Read(*)", "action": "allow", "comment": "Allow all reads"},
                {
                    "pattern": "Edit(src/**)",
                    "action": "allow",
                    "comment": "Allow source edits",
                },
                {"pattern": "*", "action": "ask", "comment": "Ask for everything else"},
            ],
        )
        developer_profile_file = profiles_dir / "developer.yaml"
        with open(developer_profile_file, "w") as f:
            yaml.dump(developer_profile_data, f)

        # Set active profile to developer
        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text("developer")

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert isinstance(profile, Profile)
        assert profile.metadata.name == "developer"
        assert profile.metadata.description == "Developer profile with relaxed rules"
        assert len(profile.rules) == 3
        assert profile.rules[0].pattern == "Read(*)"
        assert profile.rules[1].pattern == "Edit(src/**)"

    def test_loads_different_profile_when_active_profile_changes(self, project_dir) -> None:
        """Should load different profile when active_profile content changes."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Create two different profiles
        reviewer_data = make_yaml_profile_data(
            name="reviewer",
            description="Reviewer profile with strict rules",
            rules=[
                {"pattern": "Read(*)", "action": "allow", "comment": "Allow reads"},
                {"pattern": "Edit(*)", "action": "ask", "comment": "Ask before edits"},
                {
                    "pattern": "Bash(git push*)",
                    "action": "deny",
                    "comment": "Deny pushes",
                },
            ],
        )

        maintainer_data = make_yaml_profile_data(
            name="maintainer",
            description="Maintainer profile with balanced rules",
            rules=[
                {"pattern": "Read(*)", "action": "allow", "comment": "Allow reads"},
                {
                    "pattern": "Edit(src/**)",
                    "action": "allow",
                    "comment": "Allow source edits",
                },
                {
                    "pattern": "Bash(git push*)",
                    "action": "ask",
                    "comment": "Ask before pushes",
                },
            ],
        )

        reviewer_file = profiles_dir / "reviewer.yaml"
        with open(reviewer_file, "w") as f:
            yaml.dump(reviewer_data, f)

        maintainer_file = profiles_dir / "maintainer.yaml"
        with open(maintainer_file, "w") as f:
            yaml.dump(maintainer_data, f)

        active_profile_file = claudeguard_dir / "active_profile"
        loader = ProfileLoader()

        active_profile_file.write_text("reviewer")
        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile1 = loader.load_profile()

        assert profile1.metadata.name == "reviewer"
        assert profile1.metadata.description == "Reviewer profile with strict rules"
        # Find the git push rule
        git_push_rule = next(rule for rule in profile1.rules if "git push" in rule.pattern)
        assert git_push_rule.action == "deny"

        active_profile_file.write_text("maintainer")
        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile2 = loader.load_profile()

        assert profile2.metadata.name == "maintainer"
        assert profile2.metadata.description == "Maintainer profile with balanced rules"
        # Find the git push rule
        git_push_rule2 = next(rule for rule in profile2.rules if "git push" in rule.pattern)
        assert git_push_rule2.action == "ask"

    def test_defaults_to_default_profile_when_no_active_profile_file(self, project_dir) -> None:
        """Should default to 'default' profile when active_profile file doesn't exist."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Create default profile in profiles directory
        default_profile_data = make_yaml_profile_data(
            name="default",
            description="Default security profile",
            rules=[
                {"pattern": "Read(*)", "action": "allow", "comment": "Allow reads"},
                {
                    "pattern": "Edit(*.md)",
                    "action": "allow",
                    "comment": "Allow markdown edits",
                },
                {"pattern": "*", "action": "ask", "comment": "Ask for everything else"},
            ],
        )
        default_profile_file = profiles_dir / "default.yaml"
        with open(default_profile_file, "w") as f:
            yaml.dump(default_profile_data, f)

        # Don't create active_profile file - should default to "default"
        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert isinstance(profile, Profile)
        assert profile.metadata.name == "default"
        assert profile.metadata.description == "Default security profile"

    def test_falls_back_to_generated_default_when_no_profiles_directory(self, project_dir) -> None:
        """Should fall back to generated default profile when no profiles/ directory exists."""
        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert isinstance(profile, Profile)
        assert profile.metadata.name == "default"
        assert len(profile.rules) > 0  # Should have default rules from generator

    def test_handles_missing_profiles_directory_gracefully(self, project_dir) -> None:
        """Should handle missing profiles/ directory and fall back to generated default."""
        claudeguard_dir = project_dir / ".claudeguard"
        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text("nonexistent")

        # Don't create profiles directory
        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert isinstance(profile, Profile)
        assert profile.metadata.name == "default"
        assert len(profile.rules) > 0

    def test_preserves_rule_order_from_active_profile_yaml(self, project_dir) -> None:
        """Should preserve rule order when loading from active profile in profiles/ directory."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        ordered_profile_data = make_yaml_profile_data(
            name="ordered-profile",
            rules=[
                {"pattern": "Read(*)", "action": "allow", "comment": "First rule"},
                {"pattern": "Edit(*.py)", "action": "ask", "comment": "Second rule"},
                {"pattern": "Bash(rm*)", "action": "deny", "comment": "Third rule"},
                {"pattern": "*", "action": "ask", "comment": "Fourth rule"},
            ],
        )
        profile_file = profiles_dir / "ordered-profile.yaml"
        with open(profile_file, "w") as f:
            yaml.dump(ordered_profile_data, f)

        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text("ordered-profile")

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert profile.rules[0].comment == "First rule"
        assert profile.rules[1].comment == "Second rule"
        assert profile.rules[2].comment == "Third rule"
        assert profile.rules[3].comment == "Fourth rule"


class TestActiveProfileErrorHandling:
    """Test error handling for active_profile metadata system."""

    def test_handles_corrupted_active_profile_file_gracefully(self, project_dir) -> None:
        """Should handle corrupted active_profile file and fall back to default."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Create default profile
        default_data = make_yaml_profile_data(name="default")
        default_file = profiles_dir / "default.yaml"
        with open(default_file, "w") as f:
            yaml.dump(default_data, f)

        # Create corrupted active_profile file with binary data
        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_bytes(b"\x00\x01\x02invalid")

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert isinstance(profile, Profile)
        assert profile.metadata.name == "default"

    def test_handles_empty_active_profile_file(self, project_dir) -> None:
        """Should handle empty active_profile file and fall back to default."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Create default profile
        default_data = make_yaml_profile_data(name="default")
        default_file = profiles_dir / "default.yaml"
        with open(default_file, "w") as f:
            yaml.dump(default_data, f)

        # Create empty active_profile file
        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text("")

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert profile.metadata.name == "default"

    def test_handles_whitespace_only_active_profile_file(self, project_dir) -> None:
        """Should handle active_profile file with only whitespace and fall back to default."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Create default profile
        default_data = make_yaml_profile_data(name="default")
        default_file = profiles_dir / "default.yaml"
        with open(default_file, "w") as f:
            yaml.dump(default_data, f)

        # Create active_profile file with whitespace
        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text("   \n\t   \n  ")

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert profile.metadata.name == "default"

    def test_raises_error_when_referenced_profile_not_found(self, project_dir) -> None:
        """Should raise ProfileLoadError when active_profile references non-existent profile."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Set active profile to non-existent profile
        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text("nonexistent-profile")

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with pytest.raises(ProfileLoadError) as exc_info:
                loader.load_profile()

            assert "Profile 'nonexistent-profile' not found" in str(exc_info.value)

    def test_raises_error_when_referenced_profile_yaml_invalid(self, project_dir) -> None:
        """Should raise ProfileLoadError when referenced profile YAML is invalid."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Create profile with invalid YAML
        invalid_profile = profiles_dir / "invalid.yaml"
        invalid_profile.write_text("{ invalid: yaml: content")

        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text("invalid")

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with pytest.raises(ProfileLoadError) as exc_info:
                loader.load_profile()

            assert "Failed to load profile from" in str(exc_info.value)

    def test_strips_whitespace_from_active_profile_content(self, project_dir) -> None:
        """Should strip whitespace from active_profile file content when reading profile name."""
        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Create profile with whitespace-padded name
        spaced_data = make_yaml_profile_data(name="spaced-profile")
        spaced_file = profiles_dir / "spaced-profile.yaml"
        with open(spaced_file, "w") as f:
            yaml.dump(spaced_data, f)

        # Write active_profile with extra whitespace
        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text("  spaced-profile  \n\t")

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            profile = loader.load_profile()

        assert profile.metadata.name == "spaced-profile"


class TestActiveProfileWithHomeDirectory:
    """Test active_profile system with home directory fallback."""

    def test_prefers_project_active_profile_over_home_profile(self, temp_dir) -> None:
        """Should prefer project active_profile system over home directory profile."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        project_claudeguard = project_dir / ".claudeguard"
        project_claudeguard.mkdir()
        project_profiles = project_claudeguard / "profiles"
        project_profiles.mkdir()

        home_dir = temp_dir / "home"
        home_dir.mkdir()
        home_claudeguard = home_dir / ".claudeguard"
        home_claudeguard.mkdir()

        # Create project profile with active_profile system
        project_data = make_yaml_profile_data(name="project-profile")
        project_file = project_profiles / "project-profile.yaml"
        with open(project_file, "w") as f:
            yaml.dump(project_data, f)

        active_profile_file = project_claudeguard / "active_profile"
        active_profile_file.write_text("project-profile")

        # Create home profile using new system
        home_profiles_dir = home_claudeguard / "profiles"
        home_profiles_dir.mkdir(parents=True)
        home_data = make_yaml_profile_data(name="home-profile")
        home_file = home_profiles_dir / "default.yaml"
        with open(home_file, "w") as f:
            yaml.dump(home_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with patch("pathlib.Path.home", return_value=home_dir):
                profile = loader.load_profile()

        assert profile.metadata.name == "project-profile"

    def test_falls_back_to_home_when_project_has_no_active_profile(self, temp_dir) -> None:
        """Should fall back to home directory when project doesn't use active_profile system."""
        project_dir = temp_dir / "project-no-profiles"
        project_dir.mkdir()

        home_dir = temp_dir / "home"
        home_dir.mkdir()
        home_claudeguard = home_dir / ".claudeguard"
        home_profiles_dir = home_claudeguard / "profiles"
        home_profiles_dir.mkdir(parents=True)

        # Create home profile
        home_data = make_yaml_profile_data(name="home-profile")
        home_file = home_profiles_dir / "default.yaml"
        with open(home_file, "w") as f:
            yaml.dump(home_data, f)

        loader = ProfileLoader()

        with patch("pathlib.Path.cwd", return_value=project_dir):
            with patch("pathlib.Path.home", return_value=home_dir):
                profile = loader.load_profile()

        assert profile.metadata.name == "home-profile"
