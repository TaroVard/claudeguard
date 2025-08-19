"""Final edge case tests to push CLI coverage to 95%+."""

from pathlib import Path

import yaml
from click.testing import CliRunner

from claudeguard.cli import cli


class TestInitCommandEdgeCases:
    """Test init command edge cases for complete coverage."""

    def test_install_missing_active_profile_file_repair(self) -> None:
        """
        GIVEN claudeguard dir with profiles but missing active_profile file
        WHEN running install
        THEN it should repair the missing active_profile file
        """
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create .claude directory for install command
            claude_dir = Path(".claude")
            claude_dir.mkdir()
            settings_file = claude_dir / "settings.local.json"
            settings_file.write_text("{}")

            # Create partial claudeguard structure
            claudeguard_dir = Path(".claudeguard")
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            # Don't create active_profile file or default profile

            result = runner.invoke(cli, ["install"])

            assert result.exit_code == 0
            # Should initialize since missing default profile and active_profile
            assert "✅ Initialized claudeguard with seed profiles" in result.output

            # Verify active_profile file was created
            active_profile_file = claudeguard_dir / "active_profile"
            assert active_profile_file.exists()
            assert active_profile_file.read_text() == "default"


class TestInstallCommandEdgeCases:
    """Test install command edge cases."""

    def test_install_with_corrupt_json_creates_backup(self) -> None:
        """
        GIVEN settings file with corrupt JSON
        WHEN running install
        THEN it should create backup and install fresh
        """
        runner = CliRunner()
        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()
            settings_file = claude_dir / "settings.local.json"
            settings_file.write_text('{"invalid": json content')

            result = runner.invoke(cli, ["install"])

            assert result.exit_code == 0
            assert "⚠️  Warning: Invalid JSON in settings file, creating backup..." in result.output
            assert "✅ Installed claudeguard hook in Claude Code" in result.output

            # Verify backup was created
            backup_file = claude_dir / "settings.local.json.backup"
            assert backup_file.exists()

    def test_install_with_empty_settings_file(self) -> None:
        """
        GIVEN empty settings file
        WHEN running install
        THEN it should create hooks structure
        """
        runner = CliRunner()
        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()
            settings_file = claude_dir / "settings.local.json"
            settings_file.write_text("")  # Empty file

            result = runner.invoke(cli, ["install"])

            assert result.exit_code == 0
            assert "✅ Installed claudeguard hook in Claude Code" in result.output


class TestStatusCommandEdgeCases:
    """Test status command edge cases."""

    def test_status_with_profile_loading_error(self) -> None:
        """
        GIVEN claudeguard directory but corrupted profile
        WHEN running status
        THEN it should show error without crashing
        """
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create claudeguard directory with corrupted profile
            claudeguard_dir = Path(".claudeguard")
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            # Create corrupted profile
            default_profile = profiles_dir / "default.yaml"
            default_profile.write_text("invalid yaml content: [unclosed")

            active_profile_file = claudeguard_dir / "active_profile"
            active_profile_file.write_text("default")

            result = runner.invoke(cli, ["status"])

            # Should not exit but show error
            assert "❌ Error reading profile:" in result.output


class TestSwitchProfileEdgeCases:
    """Test switch-profile command edge cases."""

    def test_switch_profile_with_invalid_yaml(self) -> None:
        """
        GIVEN profile with invalid YAML
        WHEN switching to that profile
        THEN it should exit with error
        """
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create .claude directory for install command
            claude_dir = Path(".claude")
            claude_dir.mkdir()
            settings_file = claude_dir / "settings.local.json"
            settings_file.write_text("{}")

            runner.invoke(cli, ["install"])

            # Create profile with invalid YAML
            profiles_dir = Path(".claudeguard/profiles")
            bad_profile = profiles_dir / "bad.yaml"
            bad_profile.write_text("invalid: yaml: content: [unclosed")

            result = runner.invoke(cli, ["switch-profile", "bad"])

            assert result.exit_code == 1
            assert "❌ Cannot read profile 'bad'" in result.output

    def test_switch_profile_with_invalid_structure(self) -> None:
        """
        GIVEN profile with invalid structure (missing name field)
        WHEN switching to that profile
        THEN it should exit with specific error
        """
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create .claude directory for install command
            claude_dir = Path(".claude")
            claude_dir.mkdir()
            settings_file = claude_dir / "settings.local.json"
            settings_file.write_text("{}")

            runner.invoke(cli, ["install"])

            # Create profile without name field
            profiles_dir = Path(".claudeguard/profiles")
            no_name_profile = profiles_dir / "noname.yaml"
            profile_data = {"description": "Profile without name", "rules": []}
            with open(no_name_profile, "w") as f:
                yaml.dump(profile_data, f)

            result = runner.invoke(cli, ["switch-profile", "noname"])

            assert result.exit_code == 1
            assert "❌ Profile 'noname' missing required 'name' field" in result.output

    def test_switch_profile_with_invalid_rules_structure(self) -> None:
        """
        GIVEN profile with invalid rules structure
        WHEN switching to that profile
        THEN it should exit with rules structure error
        """
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create .claude directory for install command
            claude_dir = Path(".claude")
            claude_dir.mkdir()
            settings_file = claude_dir / "settings.local.json"
            settings_file.write_text("{}")

            runner.invoke(cli, ["install"])

            # Create profile with rules as dict instead of list
            profiles_dir = Path(".claudeguard/profiles")
            bad_rules_profile = profiles_dir / "badrules.yaml"
            profile_data = {"name": "badrules", "rules": {"pattern": "not a list"}}
            with open(bad_rules_profile, "w") as f:
                yaml.dump(profile_data, f)

            result = runner.invoke(cli, ["switch-profile", "badrules"])

            assert result.exit_code == 1
            assert "❌ Profile 'badrules' has invalid rules structure" in result.output


class TestCreateProfileEdgeCases:
    """Test create-profile command edge cases."""

    def test_create_profile_with_template_from_existing(self) -> None:
        """
        GIVEN existing profile to use as template
        WHEN creating new profile from template
        THEN it should copy template and update metadata
        """
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create .claude directory for install command
            claude_dir = Path(".claude")
            claude_dir.mkdir()
            settings_file = claude_dir / "settings.local.json"
            settings_file.write_text("{}")

            runner.invoke(cli, ["install"])

            result = runner.invoke(
                cli,
                [
                    "create-profile",
                    "from-default",
                    "--from",
                    "default",
                    "--description",
                    "Based on default template",
                ],
            )

            assert result.exit_code == 0
            assert "✅ Created profile 'from-default' from template 'default'" in result.output

            # Verify template was used
            profile_file = Path(".claudeguard/profiles/from-default.yaml")
            with open(profile_file) as f:
                profile_data = yaml.safe_load(f)

            assert profile_data["name"] == "from-default"
            assert profile_data["description"] == "Based on default template"


class TestListProfilesEdgeCases:
    """Test list-profiles edge cases."""

    def test_list_profiles_with_corrupted_profile(self) -> None:
        """
        GIVEN profiles directory with corrupted profile file
        WHEN listing profiles
        THEN it should show corrupted marker for broken profiles
        """
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create .claude directory for install command
            claude_dir = Path(".claude")
            claude_dir.mkdir()
            settings_file = claude_dir / "settings.local.json"
            settings_file.write_text("{}")

            runner.invoke(cli, ["install"])

            # Create corrupted profile
            profiles_dir = Path(".claudeguard/profiles")
            corrupt_profile = profiles_dir / "corrupt.yaml"
            corrupt_profile.write_text("invalid yaml: [unclosed")

            result = runner.invoke(cli, ["list-profiles"])

            assert result.exit_code == 0
            assert "corrupt ⚠" in result.output
            assert "Profile file (corrupted)" in result.output

    def test_list_profiles_with_empty_profiles_directory(self) -> None:
        """
        GIVEN profiles directory with no profiles
        WHEN listing profiles
        THEN it should exit with no profiles error
        """
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create claudeguard structure but remove default profile
            claudeguard_dir = Path(".claudeguard")
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            result = runner.invoke(cli, ["list-profiles"])

            assert result.exit_code == 1
            assert "❌ No profiles found" in result.output
