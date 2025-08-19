"""Tests for CLI security validation functions and path traversal protection."""

from unittest.mock import patch

import pytest

from claudeguard.cli import (
    _load_template_data,
    _validate_claudeguard_setup,
    _validate_profile_name,
    _validate_profile_path,
)


class TestProfileNameValidation:
    """Test profile name validation for security and format compliance."""

    def test_validate_empty_profile_name_exits_with_error(self, capsys) -> None:
        """
        GIVEN an empty profile name
        WHEN validating the profile name
        THEN it should exit with code 1 and show clear error message
        """
        with pytest.raises(SystemExit) as exc_info:
            _validate_profile_name("")

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "❌ Invalid profile name" in captured.out
        assert "Profile name cannot be empty" in captured.out

    def test_validate_invalid_characters_exits_with_error(self, capsys) -> None:
        """
        GIVEN profile name with invalid characters
        WHEN validating the profile name
        THEN it should exit with code 1 and show format requirements
        """
        invalid_names = [
            "profile@name",
            "profile name",
            "profile$",
            "profile/path",
            "profile\\path",
        ]

        for invalid_name in invalid_names:
            with pytest.raises(SystemExit) as exc_info:
                _validate_profile_name(invalid_name)

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "❌ Invalid profile name" in captured.out
            assert "letters, numbers, hyphens, and underscores" in captured.out

    def test_validate_valid_profile_names_pass(self) -> None:
        """
        GIVEN valid profile names
        WHEN validating profile names
        THEN validation should pass without error
        """
        valid_names = [
            "default",
            "test-profile",
            "test_profile",
            "Profile123",
            "a",
            "A-B_C-123",
        ]

        for valid_name in valid_names:
            # Should not raise any exception
            _validate_profile_name(valid_name)


class TestclaudeguardSetupValidation:
    """Test claudeguard directory setup validation."""

    def test_validate_nonexistent_claudeguard_dir_exits_with_error(self, tmp_path, capsys) -> None:
        """
        GIVEN nonexistent claudeguard directory
        WHEN validating claudeguard setup
        THEN it should exit with code 1 and suggest initialization
        """
        nonexistent_dir = tmp_path / "nonexistent" / ".claudeguard"

        with pytest.raises(SystemExit) as exc_info:
            _validate_claudeguard_setup(nonexistent_dir)

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "❌ claudeguard not initialized in this project" in captured.out
        assert "Run 'claudeguard install' to get started" in captured.out

    def test_validate_missing_profiles_dir_exits_with_error(self, tmp_path, capsys) -> None:
        """
        GIVEN claudeguard dir without profiles subdirectory
        WHEN validating claudeguard setup
        THEN it should exit with code 1 and suggest initialization
        """
        claudeguard_dir = tmp_path / ".claudeguard"
        claudeguard_dir.mkdir()
        # Don't create profiles directory

        with pytest.raises(SystemExit) as exc_info:
            _validate_claudeguard_setup(claudeguard_dir)

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "❌ No profiles directory found" in captured.out
        assert "Run 'claudeguard install' to set up the profile structure" in captured.out

    def test_validate_valid_claudeguard_setup_returns_profiles_dir(self, tmp_path) -> None:
        """
        GIVEN properly set up claudeguard directory
        WHEN validating claudeguard setup
        THEN it should return the profiles directory path
        """
        claudeguard_dir = tmp_path / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        profiles_dir.mkdir(parents=True)

        result = _validate_claudeguard_setup(claudeguard_dir)

        assert result == profiles_dir
        assert result.exists()


class TestProfilePathValidation:
    """Test profile path validation for path traversal protection."""

    def test_validate_normal_profile_path_returns_path(self, tmp_path) -> None:
        """
        GIVEN normal profile name and profiles directory
        WHEN validating profile path
        THEN it should return the correct profile file path
        """
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()

        result = _validate_profile_path("test-profile", profiles_dir)

        assert result == profiles_dir / "test-profile.yaml"

    def test_validate_path_traversal_attempt_exits_with_error(self, tmp_path, capsys) -> None:
        """
        GIVEN profile name that attempts path traversal
        WHEN validating profile path
        THEN it should exit with code 1 to prevent security issue
        """
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()

        # Create a target directory outside profiles for traversal attempt
        (tmp_path / "outside").mkdir()

        # This should be blocked even if the path exists
        with pytest.raises(SystemExit) as exc_info:
            _validate_profile_path("../outside/malicious", profiles_dir)

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "❌ Invalid profile path" in captured.out

    def test_validate_symlink_traversal_attempt_exits_with_error(self, tmp_path, capsys) -> None:
        """
        GIVEN symlink that could enable path traversal
        WHEN validating profile path
        THEN it should exit with code 1 to prevent security issue
        """
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()

        # Create symlink pointing outside profiles directory
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        symlink_path = profiles_dir / "symlink.yaml"
        symlink_path.symlink_to(outside_dir / "target.yaml")

        # Validation should catch that resolved path is outside profiles dir
        with pytest.raises(SystemExit) as exc_info:
            _validate_profile_path("symlink", profiles_dir)

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "❌ Invalid profile path" in captured.out


class TestTemplateDataLoading:
    """Test template data loading with error handling."""

    def test_load_nonexistent_default_template_returns_none(self, tmp_path) -> None:
        """
        GIVEN nonexistent default template file
        WHEN loading template data
        THEN it should return None without error
        """
        template_file = tmp_path / "default.yaml"
        # Don't create the file

        result = _load_template_data(template_file, "default")

        assert result is None

    def test_load_nonexistent_custom_template_exits_with_error(self, tmp_path, capsys) -> None:
        """
        GIVEN nonexistent custom template file
        WHEN loading template data
        THEN it should exit with code 1 and show error
        """
        template_file = tmp_path / "custom.yaml"
        # Don't create the file

        with pytest.raises(SystemExit) as exc_info:
            _load_template_data(template_file, "custom")

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "❌ Template profile 'custom' not found" in captured.out

    def test_load_invalid_yaml_exits_with_error(self, tmp_path, capsys) -> None:
        """
        GIVEN template file with invalid YAML
        WHEN loading template data
        THEN it should exit with code 1 and show YAML error
        """
        template_file = tmp_path / "invalid.yaml"
        template_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(SystemExit) as exc_info:
            _load_template_data(template_file, "invalid")

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "❌ Invalid YAML in template profile 'invalid'" in captured.out

    def test_load_template_with_os_error_exits_with_error(self, tmp_path, capsys) -> None:
        """
        GIVEN template file that causes OS error when reading
        WHEN loading template data
        THEN it should exit with code 1 and show OS error
        """
        template_file = tmp_path / "protected.yaml"
        template_file.write_text("name: test")

        # Mock the open function to raise an OSError instead of relying on file permissions
        # This works reliably across all platforms including Windows
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(SystemExit) as exc_info:
                _load_template_data(template_file, "protected")

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "❌ Error reading template profile 'protected'" in captured.out

    def test_load_valid_template_returns_data(self, tmp_path) -> None:
        """
        GIVEN valid template file
        WHEN loading template data
        THEN it should return the parsed YAML data
        """
        template_file = tmp_path / "valid.yaml"
        template_content = """
name: test-template
description: Test template
version: "1.0"
rules:
  - pattern: "Read(*)"
    action: allow
"""
        template_file.write_text(template_content)

        result = _load_template_data(template_file, "valid")

        assert result is not None
        assert isinstance(result, dict)
        assert result["name"] == "test-template"
        assert result["description"] == "Test template"
        assert "rules" in result
