"""
Test CLI create_profile command with active_profile metadata approach.

This module tests the new create_profile command that creates new profiles:
- Creates new profile in .claudeguard/profiles/{name}.yaml
- Supports copying from existing profiles as templates
- Validates profile names and handles conflicts
- Optionally switches to the new profile after creation

Following TDD principles - these tests will fail until the create_profile implementation is complete.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from claudeguard.cli import create_profile
from tests.conftest import make_yaml_profile_data


class TestCreateProfileBasics:
    """Test basic profile creation functionality."""

    def test_creates_new_profile_from_default_template(self) -> None:
        """Should create new profile copying from default template."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure in the isolated filesystem
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create default profile as template
            default_data = make_yaml_profile_data(
                name="default",
                description="Default security policy",
                rules=[
                    {"pattern": "Read(*)", "action": "allow", "comment": "Safe reads"},
                    {
                        "pattern": "*",
                        "action": "ask",
                        "comment": "Ask for everything else",
                    },
                ],
            )
            default_file = profiles_dir / "default.yaml"
            with open(default_file, "w") as f:
                yaml.dump(default_data, f)

            result = runner.invoke(create_profile, ["developer"])

            assert result.exit_code == 0
            assert "✅ Created profile 'developer'" in result.output

            # Verify profile file was created
            new_profile_file = profiles_dir / "developer.yaml"
            assert new_profile_file.exists()

            # Verify profile content
            with open(new_profile_file) as f:
                profile_data = yaml.safe_load(f)

            assert profile_data["name"] == "developer"
            assert (
                profile_data["description"] == "Default security policy"
            )  # Copied from template
            assert len(profile_data["rules"]) == 2
            assert profile_data["rules"][0]["pattern"] == "Read(*)"
            assert profile_data["rules"][1]["pattern"] == "*"

    def test_creates_profile_with_minimal_template_when_no_default(self) -> None:
        """Should create profile with minimal rules when no default template exists."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create directory structure without default profile
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            result = runner.invoke(create_profile, ["minimal"])

            assert result.exit_code == 0
            assert "✅ Created profile 'minimal'" in result.output

            # Verify profile file was created
            new_profile_file = profiles_dir / "minimal.yaml"
            assert new_profile_file.exists()

            # Verify profile has minimal content
            with open(new_profile_file) as f:
                profile_data = yaml.safe_load(f)

            assert profile_data["name"] == "minimal"
            assert "description" in profile_data
            assert "rules" in profile_data
            assert isinstance(profile_data["rules"], list)
            assert (
                len(profile_data["rules"]) > 0
            )  # Should have at least some basic rules

    def test_shows_helpful_success_message(self) -> None:
        """Should show helpful success message with next steps."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            result = runner.invoke(create_profile, ["test-profile"])

            assert result.exit_code == 0
            assert "✅ Created profile 'test-profile'" in result.output
            assert "switch-profile" in result.output or "Switch to" in result.output


class TestCreateProfileTemplates:
    """Test template copying functionality."""

    def test_creates_profile_from_custom_template(self) -> None:
        """Should create profile copying from specified template."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create custom template profile
            strict_data = make_yaml_profile_data(
                name="strict",
                description="Strict security policy",
                rules=[
                    {"pattern": "Read(*)", "action": "allow", "comment": "Reads only"},
                    {
                        "pattern": "*",
                        "action": "deny",
                        "comment": "Deny everything else",
                    },
                ],
            )
            strict_file = profiles_dir / "strict.yaml"
            with open(strict_file, "w") as f:
                yaml.dump(strict_data, f)

            result = runner.invoke(create_profile, ["new-strict", "--from", "strict"])

            assert result.exit_code == 0
            assert "✅ Created profile 'new-strict'" in result.output
            assert "from template 'strict'" in result.output

            # Verify content copied from strict template
            new_profile_file = profiles_dir / "new-strict.yaml"
            with open(new_profile_file) as f:
                profile_data = yaml.safe_load(f)

            assert profile_data["name"] == "new-strict"
            assert profile_data["description"] == "Strict security policy"
            assert len(profile_data["rules"]) == 2
            assert profile_data["rules"][1]["action"] == "deny"

    def test_fails_when_template_profile_not_found(self) -> None:
        """Should fail with helpful message when template doesn't exist."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            result = runner.invoke(create_profile, ["test", "--from", "nonexistent"])

            assert result.exit_code != 0
            assert (
                "Template profile 'nonexistent' not found" in result.output
                or "not found" in result.output
            )


class TestCreateProfileOptions:
    """Test command line options."""

    def test_creates_profile_with_custom_description(self) -> None:
        """Should create profile with custom description when --description provided."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            result = runner.invoke(
                create_profile, ["custom", "--description", "My custom security policy"]
            )

            assert result.exit_code == 0

            # Verify custom description was used
            new_profile_file = profiles_dir / "custom.yaml"
            with open(new_profile_file) as f:
                profile_data = yaml.safe_load(f)

            assert profile_data["description"] == "My custom security policy"

    def test_creates_profile_and_switches_with_switch_option(self) -> None:
        """Should create profile and switch to it when --switch provided."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create default profile as template
            default_data = make_yaml_profile_data(name="default")
            default_file = profiles_dir / "default.yaml"
            with open(default_file, "w") as f:
                yaml.dump(default_data, f)

            # Set initial active profile
            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("default")

            result = runner.invoke(create_profile, ["new-active", "--switch"])

            assert result.exit_code == 0
            assert "✅ Created profile 'new-active'" in result.output
            assert "Switched to" in result.output or "Active profile" in result.output

            # Verify profile was created and is now active
            new_profile_file = profiles_dir / "new-active.yaml"
            assert new_profile_file.exists()

            active_content = active_profile_file.read_text().strip()
            assert active_content == "new-active"

    def test_combines_multiple_options_correctly(self) -> None:
        """Should handle multiple options together correctly."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create template
            template_data = make_yaml_profile_data(
                name="template", description="Template desc"
            )
            template_file = profiles_dir / "template.yaml"
            with open(template_file, "w") as f:
                yaml.dump(template_data, f)

            # Create active profile file
            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("template")

            result = runner.invoke(
                create_profile,
                [
                    "combo",
                    "--from",
                    "template",
                    "--description",
                    "Combined options test",
                    "--switch",
                ],
            )

            assert result.exit_code == 0

            # Verify all options were applied
            new_profile_file = profiles_dir / "combo.yaml"
            with open(new_profile_file) as f:
                profile_data = yaml.safe_load(f)

            assert profile_data["name"] == "combo"
            assert (
                profile_data["description"] == "Combined options test"
            )  # Custom description

            # Verify switched
            active_content = active_profile_file.read_text().strip()
            assert active_content == "combo"


class TestCreateProfileValidation:
    """Test input validation and conflict handling."""

    def test_validates_profile_name_format(self) -> None:
        """Should reject invalid profile names."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            invalid_names = [
                "invalid space",
                "invalid@symbol",
                "invalid.dot",
                "",
                "invalid/slash",
            ]

            for invalid_name in invalid_names:
                result = runner.invoke(create_profile, [invalid_name])
                assert result.exit_code != 0
                assert (
                    "Invalid profile name" in result.output
                    or "invalid" in result.output.lower()
                )

    def test_allows_valid_profile_names(self) -> None:
        """Should accept valid profile names."""
        runner = CliRunner()

        valid_names = [
            "valid",
            "valid-name",
            "valid_name",
            "valid123",
            "VALID",
            "Valid-Name_123",
        ]

        for valid_name in valid_names:
            with runner.isolated_filesystem():
                claudeguard_dir = Path(".claudeguard")
                claudeguard_dir.mkdir()
                profiles_dir = claudeguard_dir / "profiles"
                profiles_dir.mkdir()

                result = runner.invoke(create_profile, [valid_name])
                assert result.exit_code == 0, (
                    f"Valid name '{valid_name}' was rejected: {result.output}"
                )

    def test_prevents_profile_name_conflicts(self) -> None:
        """Should fail when profile already exists."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir()

            # Create existing profile
            existing_data = make_yaml_profile_data(name="existing")
            existing_file = profiles_dir / "existing.yaml"
            with open(existing_file, "w") as f:
                yaml.dump(existing_data, f)

            result = runner.invoke(create_profile, ["existing"])

            assert result.exit_code != 0
            assert (
                "already exists" in result.output or "conflict" in result.output.lower()
            )


class TestCreateProfileErrorHandling:
    """Test error scenarios."""

    def test_fails_when_claudeguard_not_initialized(self) -> None:
        """Should fail gracefully when claudeguard not initialized."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # No .claudeguard directory
            result = runner.invoke(create_profile, ["test"])

            assert result.exit_code != 0
            assert "not initialized" in result.output or "claudeguard init" in result.output

    def test_fails_when_no_profiles_directory(self) -> None:
        """Should fail when profiles directory doesn't exist."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create .claudeguard but not profiles directory
            claudeguard_dir = Path(".claudeguard")
            claudeguard_dir.mkdir()

            result = runner.invoke(create_profile, ["test"])

            assert result.exit_code != 0
            assert "profiles directory" in result.output or "not found" in result.output

    def test_handles_yaml_write_errors_gracefully(self) -> None:
        """Should handle errors when writing YAML files."""
        # This test would need mocking of file operations to simulate write failures
        # For now, we'll include it as a placeholder for the TDD approach
