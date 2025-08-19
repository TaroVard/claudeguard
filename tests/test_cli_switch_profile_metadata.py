"""
Test CLI switch_profile command with active_profile metadata approach.

This module tests the new lightweight profile switching that uses active_profile metadata:
- switch_profile writes profile name to .claudeguard/active_profile file (no file copying)
- Validates target profile exists in .claudeguard/profiles/ directory
- Provides helpful error messages and available profile listing
- Handles edge cases gracefully

Following TDD principles - these tests will fail until the new switch_profile implementation is complete.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml
from click.testing import CliRunner

from claudeguard.cli import switch_profile
from tests.conftest import make_yaml_profile_data


class TestSwitchProfileMetadata:
    """Test switch_profile command with active_profile metadata system."""

    def test_writes_profile_name_to_active_profile_file(self) -> None:
        """Should write profile name to .claudeguard/active_profile file to track active profile."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create developer profile
            developer_data = make_yaml_profile_data(
                name="developer", description="Developer profile with relaxed rules"
            )
            developer_file = profiles_dir / "developer.yaml"
            with open(developer_file, "w") as f:
                yaml.dump(developer_data, f)

            # Create default profile and set as active initially
            default_data = make_yaml_profile_data(name="default")
            default_file = profiles_dir / "default.yaml"
            with open(default_file, "w") as f:
                yaml.dump(default_data, f)

            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("default")

            result = runner.invoke(switch_profile, ["developer"])

            assert result.exit_code == 0
            assert "Switched to profile 'developer'" in result.output
            assert active_profile_file.read_text().strip() == "developer"

    def test_does_not_copy_profile_files(self) -> None:
        """Should not copy profile files - only update active_profile metadata."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create reviewer profile
            reviewer_data = make_yaml_profile_data(
                name="reviewer", description="Strict review profile"
            )
            reviewer_file = profiles_dir / "reviewer.yaml"
            with open(reviewer_file, "w") as f:
                yaml.dump(reviewer_data, f)

            # Create default profile
            default_data = make_yaml_profile_data(name="default")
            default_file = profiles_dir / "default.yaml"
            with open(default_file, "w") as f:
                yaml.dump(default_data, f)

            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("default")

            # Store original file timestamps
            reviewer_mtime = reviewer_file.stat().st_mtime
            default_mtime = default_file.stat().st_mtime

            result = runner.invoke(switch_profile, ["reviewer"])

            assert result.exit_code == 0

            # Profile files should not have been modified (no copying)
            assert reviewer_file.stat().st_mtime == reviewer_mtime
            assert default_file.stat().st_mtime == default_mtime

            # Only active_profile should be updated
            assert active_profile_file.read_text().strip() == "reviewer"

    def test_validates_target_profile_exists(self) -> None:
        """Should validate target profile exists in profiles/ directory before switching."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create only default profile
            default_data = make_yaml_profile_data(name="default")
            default_file = profiles_dir / "default.yaml"
            with open(default_file, "w") as f:
                yaml.dump(default_data, f)

            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("default")

            result = runner.invoke(switch_profile, ["nonexistent"])

            assert result.exit_code != 0
            assert "Profile 'nonexistent' not found" in result.output
            assert "Available profiles:" in result.output
            assert "default" in result.output
            # active_profile should not be changed
            assert active_profile_file.read_text().strip() == "default"

    def test_lists_available_profiles_on_error(self) -> None:
        """Should list available profiles when target profile not found."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create multiple profiles
            profile_names = ["default", "developer", "reviewer", "maintainer"]
            for name in profile_names:
                profile_data = make_yaml_profile_data(name=name)
                profile_file = profiles_dir / f"{name}.yaml"
                with open(profile_file, "w") as f:
                    yaml.dump(profile_data, f)

            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("default")

            result = runner.invoke(switch_profile, ["invalid"])

            assert result.exit_code != 0
            assert "Profile 'invalid' not found" in result.output
            assert "Available profiles:" in result.output
            for name in profile_names:
                assert name in result.output

    def test_handles_already_active_profile(self) -> None:
        """Should handle case where target profile is already active."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create developer profile
            developer_data = make_yaml_profile_data(name="developer")
            developer_file = profiles_dir / "developer.yaml"
            with open(developer_file, "w") as f:
                yaml.dump(developer_data, f)

            # Set developer as active profile
            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("developer")

            result = runner.invoke(switch_profile, ["developer"])

            assert result.exit_code == 0
            assert "Already using profile 'developer'" in result.output
            assert active_profile_file.read_text().strip() == "developer"

    def test_creates_active_profile_file_if_missing(self) -> None:
        """Should create active_profile file if it doesn't exist."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create reviewer profile
            reviewer_data = make_yaml_profile_data(name="reviewer")
            reviewer_file = profiles_dir / "reviewer.yaml"
            with open(reviewer_file, "w") as f:
                yaml.dump(reviewer_data, f)

            # Don't create active_profile file
            active_profile_file = claudeguard_dir / "active_profile"
            assert not active_profile_file.exists()

            result = runner.invoke(switch_profile, ["reviewer"])

            assert result.exit_code == 0
            assert "Switched to profile 'reviewer'" in result.output
            assert active_profile_file.exists()
            assert active_profile_file.read_text().strip() == "reviewer"

    def test_shows_profile_description_after_switch(self) -> None:
        """Should show profile description after successful switch."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create profile with description
            maintainer_data = make_yaml_profile_data(
                name="maintainer",
                description="Maintainer profile with balanced security rules",
            )
            maintainer_file = profiles_dir / "maintainer.yaml"
            with open(maintainer_file, "w") as f:
                yaml.dump(maintainer_data, f)

            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("default")

            result = runner.invoke(switch_profile, ["maintainer"])

            assert result.exit_code == 0
            assert "Switched to profile 'maintainer'" in result.output
            assert "Maintainer profile with balanced security rules" in result.output

    def test_handles_missing_profiles_directory(self, temp_dir) -> None:
        """Should handle missing profiles/ directory gracefully."""
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()
        claudeguard_dir = project_dir / ".claudeguard"
        claudeguard_dir.mkdir()

        # Don't create profiles directory
        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(switch_profile, ["any-profile"])

        assert result.exit_code != 0
        assert "No profiles found" in result.output
        assert "Run 'claudeguard install' to create" in result.output

    def test_handles_empty_profiles_directory(self) -> None:
        """Should handle empty profiles/ directory gracefully."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure with empty profiles directory
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            result = runner.invoke(switch_profile, ["any-profile"])

            assert result.exit_code != 0
            assert "No profiles found" in result.output


class TestSwitchProfileErrorHandling:
    """Test error handling in switch_profile command."""

    def test_handles_uninitialized_project(self) -> None:
        """Should handle project without .claudeguard directory."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Don't create .claudeguard directory - project is uninitialized
            result = runner.invoke(switch_profile, ["any-profile"])

            assert result.exit_code != 0
            assert "claudeguard not initialized" in result.output
            assert "Run 'claudeguard install' to get started" in result.output

    def test_preserves_current_profile_on_validation_failure(self, temp_dir) -> None:
        """Should preserve current active profile when target profile validation fails."""
        project_dir = temp_dir / "test-project"
        project_dir.mkdir()
        claudeguard_dir = project_dir / ".claudeguard"
        claudeguard_dir.mkdir()
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Create valid current profile
        current_data = make_yaml_profile_data(name="current-profile")
        current_file = profiles_dir / "current-profile.yaml"
        with open(current_file, "w") as f:
            yaml.dump(current_data, f)

        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text("current-profile")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(switch_profile, ["nonexistent"])

        assert result.exit_code != 0
        assert "Profile 'nonexistent' not found" in result.output
        # Current profile should remain unchanged
        assert active_profile_file.read_text().strip() == "current-profile"


class TestSwitchProfileWithProfileValidation:
    """Test switch_profile with profile validation before switching."""
