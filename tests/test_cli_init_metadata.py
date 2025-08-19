"""
Test CLI init command with active_profile metadata approach.

This module tests the init command that creates the profile structure:
- Creates .claudeguard/profiles/default.yaml with proper directory structure
- Creates .claudeguard/active_profile file pointing to "default"
- Handles existing projects with proper structure detection
- Sets up the metadata-based profile system

Following TDD principles - these tests will fail until the init implementation is complete.
"""

from __future__ import annotations

from unittest.mock import patch

import yaml
from click.testing import CliRunner

from claudeguard.cli import install
from tests.conftest import make_yaml_profile_data


class TestInitWithProfilesDirectory:
    """Test init command creating profiles/ directory structure."""

    def test_creates_profiles_directory_structure(self, temp_dir) -> None:
        """Should create .claudeguard/profiles/ directory structure with default profile."""
        project_dir = temp_dir / "new-project"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0
        assert "✅ Initialized claudeguard with seed profiles" in result.output

        claudeguard_dir = project_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        assert claudeguard_dir.exists()
        assert profiles_dir.exists()
        assert profiles_dir.is_dir()

    def test_creates_default_profile_in_profiles_directory(self, temp_dir) -> None:
        """Should create default.yaml profile in profiles/ directory."""
        project_dir = temp_dir / "new-project"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        default_profile = project_dir / ".claudeguard" / "profiles" / "default.yaml"
        assert default_profile.exists()
        assert default_profile.is_file()

        with open(default_profile) as f:
            profile_data = yaml.safe_load(f)

        assert profile_data["name"] == "default"
        assert "description" in profile_data
        assert "rules" in profile_data
        assert isinstance(profile_data["rules"], list)
        assert len(profile_data["rules"]) > 0

    def test_creates_active_profile_file_pointing_to_default(self, temp_dir) -> None:
        """Should create active_profile file pointing to 'default' profile."""
        project_dir = temp_dir / "new-project"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        active_profile_file = project_dir / ".claudeguard" / "active_profile"
        assert active_profile_file.exists()
        assert active_profile_file.is_file()

        content = active_profile_file.read_text().strip()
        assert content == "default"

    def test_uses_profiles_directory_not_single_file(self, temp_dir) -> None:
        """Should create profiles directory structure, not a single profile file."""
        project_dir = temp_dir / "new-project"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        single_profile = project_dir / ".claudeguard" / "profile.yaml"
        assert not single_profile.exists()

    def test_default_profile_contains_comprehensive_rules(self, temp_dir) -> None:
        """Should create default profile with comprehensive security rules."""
        project_dir = temp_dir / "new-project"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        default_profile = project_dir / ".claudeguard" / "profiles" / "default.yaml"
        with open(default_profile) as f:
            profile_data = yaml.safe_load(f)

        rules = profile_data["rules"]
        patterns = [rule["pattern"] for rule in rules]

        assert "Read(*)" in patterns
        assert "Edit(*.md)" in patterns
        assert "Edit(*.txt)" in patterns
        assert "Edit(src/**)" in patterns
        assert "Bash(git status)" in patterns
        assert "Bash(git diff)" in patterns
        assert "Bash(git log*)" in patterns
        assert "Bash(rm -rf*)" in patterns
        assert "Bash(sudo *)" in patterns
        assert "*" in patterns  # Catch-all rule

    def test_default_profile_has_secure_actions(self, temp_dir) -> None:
        """Should create default profile with secure default actions."""
        project_dir = temp_dir / "new-project"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        default_profile = project_dir / ".claudeguard" / "profiles" / "default.yaml"
        with open(default_profile) as f:
            profile_data = yaml.safe_load(f)

        rule_actions = {
            rule["pattern"]: rule["action"] for rule in profile_data["rules"]
        }

        assert rule_actions["Read(*)"] == "allow"
        assert rule_actions["Edit(*.md)"] == "allow"
        assert rule_actions["Bash(git status)"] == "allow"
        assert rule_actions["Bash(git diff)"] == "allow"
        assert rule_actions["Bash(git log*)"] == "allow"

        assert rule_actions["Bash(rm -rf*)"] == "deny"
        assert rule_actions["Bash(sudo *)"] == "deny"

        assert rule_actions["Edit(src/**)"] == "ask"
        assert rule_actions["*"] == "ask"

    def test_shows_updated_next_steps_message(self, temp_dir) -> None:
        """Should show next steps that reference profile structure."""
        project_dir = temp_dir / "new-project"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        output_lines = result.output.split("\n")

        assert any("profiles/" in line for line in output_lines)
        assert any(
            ("git" in line and "team" in line.lower()) or "sharing" in line.lower()
            for line in output_lines
        )


class TestInitExistingProjects:
    """Test init command behavior with existing projects."""

    def test_preserves_existing_profiles_directory(self, temp_dir) -> None:
        """Should preserve existing profiles/ directory if it already exists."""
        project_dir = temp_dir / "existing-with-profiles"
        project_dir.mkdir()
        claudeguard_dir = project_dir / ".claudeguard"
        claudeguard_dir.mkdir()
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        # Create existing custom profile and default profile with active profile file
        custom_data = make_yaml_profile_data(
            name="custom", description="Existing custom profile"
        )
        custom_file = profiles_dir / "custom.yaml"
        with open(custom_file, "w") as f:
            yaml.dump(custom_data, f)

        # Create default profile and active_profile to simulate fully initialized state
        default_data = make_yaml_profile_data(name="default")
        default_file = profiles_dir / "default.yaml"
        with open(default_file, "w") as f:
            yaml.dump(default_data, f)

        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text("default")

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0
        # Should not say "Initialized" because claudeguard was already set up
        assert "✅ Initialized claudeguard with default profile" not in result.output

        assert custom_file.exists()
        with open(custom_file) as f:
            preserved_data = yaml.safe_load(f)
        assert preserved_data["name"] == "custom"
        assert preserved_data["description"] == "Existing custom profile"

    def test_creates_active_profile_if_missing_from_existing_project(
        self, temp_dir
    ) -> None:
        """Should create active_profile file if missing from existing project with profiles/."""
        project_dir = temp_dir / "partial-structure"
        project_dir.mkdir()
        claudeguard_dir = project_dir / ".claudeguard"
        claudeguard_dir.mkdir()
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        default_data = make_yaml_profile_data(name="default")
        default_file = profiles_dir / "default.yaml"
        with open(default_file, "w") as f:
            yaml.dump(default_data, f)

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        active_profile_file = claudeguard_dir / "active_profile"
        assert active_profile_file.exists()
        assert active_profile_file.read_text().strip() == "default"

    def test_creates_default_profile_if_missing_from_profiles_directory(
        self, temp_dir
    ) -> None:
        """Should create default.yaml if missing from existing profiles/ directory."""
        project_dir = temp_dir / "missing-default"
        project_dir.mkdir()
        claudeguard_dir = project_dir / ".claudeguard"
        claudeguard_dir.mkdir()
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir()

        custom_data = make_yaml_profile_data(name="custom")
        custom_file = profiles_dir / "custom.yaml"
        with open(custom_file, "w") as f:
            yaml.dump(custom_data, f)

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        default_file = profiles_dir / "default.yaml"
        assert default_file.exists()

        assert custom_file.exists()


class TestInitErrorHandling:
    """Test error handling in init command."""

    def test_handles_filesystem_errors_gracefully(self, temp_dir) -> None:
        """Should handle various filesystem errors gracefully."""
        project_dir = temp_dir / "filesystem-error"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                with patch("pathlib.Path.mkdir", side_effect=OSError("Disk full")):
                    result = runner.invoke(install, [])
        assert result.exit_code != 0
        assert (
            "Error initializing claudeguard" in result.output
            or "Disk full" in result.output
        )


class TestInitProfileContent:
    """Test the content and structure of created profile files."""

    def test_created_profile_has_valid_metadata(self, temp_dir) -> None:
        """Should create profile with valid metadata structure."""
        project_dir = temp_dir / "metadata-test"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        default_profile = project_dir / ".claudeguard" / "profiles" / "default.yaml"
        with open(default_profile) as f:
            profile_data = yaml.safe_load(f)

        assert "name" in profile_data
        assert "description" in profile_data
        assert "version" in profile_data
        assert profile_data["name"] == "default"
        assert isinstance(profile_data["description"], str)
        assert len(profile_data["description"]) > 0

    def test_created_profile_rules_have_required_fields(self, temp_dir) -> None:
        """Should create profile rules with all required fields."""
        project_dir = temp_dir / "rules-test"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        default_profile = project_dir / ".claudeguard" / "profiles" / "default.yaml"
        with open(default_profile) as f:
            profile_data = yaml.safe_load(f)

        rules = profile_data["rules"]
        for i, rule in enumerate(rules):
            assert "pattern" in rule, f"Rule {i} missing pattern"
            assert "action" in rule, f"Rule {i} missing action"
            assert isinstance(rule["pattern"], str), f"Rule {i} pattern not string"
            assert rule["action"] in ["allow", "deny", "ask"], (
                f"Rule {i} invalid action"
            )

    def test_created_profile_rules_are_properly_ordered(self, temp_dir) -> None:
        """Should create profile with rules in proper precedence order."""
        project_dir = temp_dir / "order-test"
        project_dir.mkdir()

        # Create .claude directory for install command
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        settings_file = claude_dir / "settings.local.json"
        settings_file.write_text("{}")

        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch("pathlib.Path.cwd", return_value=project_dir):
                result = runner.invoke(install, [])
        assert result.exit_code == 0

        default_profile = project_dir / ".claudeguard" / "profiles" / "default.yaml"
        with open(default_profile) as f:
            profile_data = yaml.safe_load(f)

        rules = profile_data["rules"]
        patterns = [rule["pattern"] for rule in rules]

        wildcard_index = patterns.index("*")
        assert wildcard_index == len(patterns) - 1, "Wildcard rule should be last"

        read_index = patterns.index("Read(*)")
        assert read_index < wildcard_index, "Read rule should come before wildcard"
