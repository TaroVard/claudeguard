"""
Test CLI list_profiles command with active_profile metadata approach.

This module tests the updated list_profiles command that reads active_profile to show which profile is active:
- Reads active_profile file to determine which profile is currently active
- Shows available profiles from .claudeguard/profiles/ directory
- Marks active profile with indicator (checkmark or similar)
- Handles missing active_profile file gracefully

Following TDD principles - these tests will fail until the new list_profiles implementation is complete.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml
from click.testing import CliRunner

from claudeguard.cli import list_profiles
from tests.conftest import make_yaml_profile_data


class TestListProfilesWithActiveProfile:
    """Test list_profiles command with active_profile metadata system."""

    def test_shows_active_profile_with_indicator(self, temp_dir) -> None:
        """Should show which profile is active based on active_profile file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create multiple profiles
            profile_names = ["default", "developer", "reviewer"]
            for name in profile_names:
                profile_data = make_yaml_profile_data(
                    name=name, description=f"{name.title()} profile for testing"
                )
                profile_file = profiles_dir / f"{name}.yaml"
                with open(profile_file, "w") as f:
                    yaml.dump(profile_data, f)

            # Set developer as active profile
            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("developer")

            result = runner.invoke(list_profiles, [])

        assert result.exit_code == 0
        assert "Available profiles:" in result.output

        # Check that all profiles are shown
        for name in profile_names:
            assert name in result.output

        # Check that developer profile is marked as active
        lines = result.output.split("\n")
        developer_line = next(
            line
            for line in lines
            if "developer" in line and not line.strip().startswith("Developer profile")
        )
        assert (
            "✓" in developer_line or "*" in developer_line
        )  # Should have active indicator

        # Check that other profiles don't have active indicator
        default_line = next(
            line
            for line in lines
            if "default" in line and not line.strip().startswith("Default profile")
        )
        reviewer_line = next(
            line
            for line in lines
            if "reviewer" in line and not line.strip().startswith("Reviewer profile")
        )
        assert "✓" not in default_line and "*" not in default_line
        assert "✓" not in reviewer_line and "*" not in reviewer_line

    def test_shows_profile_descriptions(self) -> None:
        """Should show profile descriptions alongside profile names."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create profiles with specific descriptions
            profiles_info = [
                ("default", "Default security profile with balanced rules"),
                ("strict", "Strict profile that denies most operations"),
                ("permissive", "Permissive profile for development work"),
            ]

            for name, description in profiles_info:
                profile_data = make_yaml_profile_data(
                    name=name, description=description
                )
                profile_file = profiles_dir / f"{name}.yaml"
                with open(profile_file, "w") as f:
                    yaml.dump(profile_data, f)

            # Set strict as active
            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("strict")

            result = runner.invoke(list_profiles, [])

            assert result.exit_code == 0

            # Check that descriptions are shown
            for name, description in profiles_info:
                assert name in result.output
                assert description in result.output

    def test_defaults_to_default_when_no_active_profile_file(self) -> None:
        """Should show 'default' as active when active_profile file doesn't exist."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create profiles including default
            profile_names = ["default", "developer"]
            for name in profile_names:
                profile_data = make_yaml_profile_data(name=name)
                profile_file = profiles_dir / f"{name}.yaml"
                with open(profile_file, "w") as f:
                    yaml.dump(profile_data, f)

            # Don't create active_profile file
            result = runner.invoke(list_profiles, [])

            assert result.exit_code == 0

            # Default should be marked as active
            lines = result.output.split("\n")
            default_line = next(
                line for line in lines if "default" in line and "Default" not in line
            )
            assert "✓" in default_line or "*" in default_line

    def test_handles_corrupted_active_profile_file(self) -> None:
        """Should handle corrupted active_profile file and default to 'default' profile."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create profiles
            profile_names = ["default", "developer"]
            for name in profile_names:
                profile_data = make_yaml_profile_data(name=name)
                profile_file = profiles_dir / f"{name}.yaml"
                with open(profile_file, "w") as f:
                    yaml.dump(profile_data, f)

            # Create corrupted active_profile file
            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_bytes(b"\x00\x01\x02corrupted")

            result = runner.invoke(list_profiles, [])

            assert result.exit_code == 0

            # Should default to 'default' profile as active
            lines = result.output.split("\n")
            default_line = next(
                (line for line in lines if "default" in line and "Default" not in line),
                None,
            )
            assert default_line is not None
            assert "✓" in default_line or "*" in default_line

    def test_handles_empty_active_profile_file(self) -> None:
        """Should handle empty active_profile file and default to 'default'."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create profiles
            for name in ["default", "developer"]:
                profile_data = make_yaml_profile_data(name=name)
                profile_file = profiles_dir / f"{name}.yaml"
                with open(profile_file, "w") as f:
                    yaml.dump(profile_data, f)

            # Create empty active_profile file
            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("")

            result = runner.invoke(list_profiles, [])

            assert result.exit_code == 0

            # Should default to 'default' profile as active
            lines = result.output.split("\n")
            default_line = next(
                line for line in lines if "default" in line and "Default" not in line
            )
            assert "✓" in default_line or "*" in default_line

    def test_strips_whitespace_from_active_profile_name(self) -> None:
        """Should strip whitespace from active_profile file content when determining active profile."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create profiles
            for name in ["default", "spaced-profile"]:
                profile_data = make_yaml_profile_data(name=name)
                profile_file = profiles_dir / f"{name}.yaml"
                with open(profile_file, "w") as f:
                    yaml.dump(profile_data, f)

            # Write active_profile with extra whitespace
            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("  spaced-profile  \n\t")

            result = runner.invoke(list_profiles, [])

            assert result.exit_code == 0

            # spaced-profile should be marked as active
            lines = result.output.split("\n")
            spaced_line = next(line for line in lines if "spaced-profile" in line)
            assert "✓" in spaced_line or "*" in spaced_line


class TestListProfilesErrorHandling:
    """Test error handling in list_profiles command."""

    def test_handles_uninitialized_project(self, temp_dir) -> None:
        """Should handle project without .claudeguard directory."""
        project_dir = temp_dir / "uninitialized"
        project_dir.mkdir()

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(list_profiles, [])

        assert result.exit_code != 0
        assert "claudeguard not initialized" in result.output
        assert "Run 'claudeguard install' to get started" in result.output

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
                result = runner.invoke(list_profiles, [])

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

            result = runner.invoke(list_profiles, [])

            assert result.exit_code != 0
            assert "No profiles found" in result.output

    def test_handles_corrupted_profile_files_gracefully(self) -> None:
        """Should handle corrupted profile files and still show available profiles."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create valid profile
            valid_data = make_yaml_profile_data(name="valid")
            valid_file = profiles_dir / "valid.yaml"
            with open(valid_file, "w") as f:
                yaml.dump(valid_data, f)

            # Create corrupted profile
            corrupted_file = profiles_dir / "corrupted.yaml"
            corrupted_file.write_text("{ invalid: yaml: content")

            # Set valid profile as active
            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("valid")

            result = runner.invoke(list_profiles, [])

            assert result.exit_code == 0
            assert "valid" in result.output
            assert "corrupted" in result.output
            assert "⚠" in result.output or "(corrupted)" in result.output


class TestListProfilesFormatting:
    """Test output formatting of list_profiles command."""

    def test_formats_profile_list_consistently(self) -> None:
        """Should format profile list with consistent indentation and markers."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create profiles with varying name lengths
            profiles_info = [
                ("a", "Short name"),
                ("very-long-profile-name", "Long name profile"),
                ("mid", "Medium name"),
            ]

            for name, description in profiles_info:
                profile_data = make_yaml_profile_data(
                    name=name, description=description
                )
                profile_file = profiles_dir / f"{name}.yaml"
                with open(profile_file, "w") as f:
                    yaml.dump(profile_data, f)

            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("mid")

            result = runner.invoke(list_profiles, [])

            assert result.exit_code == 0

            # Check that the output is well-formatted
            assert "Available profiles:" in result.output

            # All profile names should be present
            for name, description in profiles_info:
                assert name in result.output
                assert description in result.output
