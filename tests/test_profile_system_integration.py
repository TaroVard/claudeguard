"""Tests for profile system integration."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from claudeguard.profile_loader import ProfileLoader, ProfileLoadError


class TestProfileDiscovery:
    """Test profile discovery and loading behavior."""

    def test_discovers_project_claudeguard_directory(self) -> None:
        """Hook should discover .claudeguard directory in project root."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            # Create a minimal profile file
            profile_file = profiles_dir / "default.yaml"
            profile_file.write_text("""
name: test-profile
description: Test profile
rules:
  - pattern: "Read(*)"
    action: allow
""")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert profile.metadata.name == "test-profile"
            assert len(profile.rules) == 1

    def test_walks_up_directory_tree_to_find_claudeguard(self) -> None:
        """Hook should walk up directory tree to find .claudeguard directory."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            claudeguard_dir.mkdir()

            # Create nested directory structure
            nested_dir = project_root / "src" / "deep" / "nested"
            nested_dir.mkdir(parents=True)

            # Create profile file in root .claudeguard
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)
            profile_file = profiles_dir / "default.yaml"
            profile_file.write_text("""
name: root-profile
description: Root profile
rules:
  - pattern: "Edit(*)"
    action: ask
""")

            # Test from nested directory without specifying project root
            with patch("pathlib.Path.cwd", return_value=nested_dir):
                loader = ProfileLoader()
                profile = loader.load_profile()

                assert profile.metadata.name == "root-profile"

    def test_falls_back_to_default_when_no_claudeguard_found(self) -> None:
        """Hook should use default profile if no .claudeguard found in tree."""
        with TemporaryDirectory() as temp_dir:
            # Empty directory with no .claudeguard
            project_root = Path(temp_dir)
            home_dir = Path(temp_dir) / "fake_home"
            home_dir.mkdir()

            loader = ProfileLoader(project_root=project_root, home_directory=home_dir)
            profile = loader.load_profile()

            assert profile.metadata.name == "default"
            assert profile.metadata.description == "Default security profile for claudeguard"

    def test_loads_active_profile_from_claudeguard_directory(self) -> None:
        """Hook should load active profile name from .claudeguard/active_profile."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            # Create active profile file
            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("restrictive")

            # Create the referenced profile
            profile_file = profiles_dir / "restrictive.yaml"
            profile_file.write_text("""
name: restrictive
description: Restrictive security profile
rules:
  - pattern: "Bash(*)"
    action: deny
""")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert profile.metadata.name == "restrictive"

    def test_defaults_to_default_profile_if_no_active_file(self) -> None:
        """Hook should default to 'default' profile if no active_profile file."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            # Create default profile but no active_profile file
            profile_file = profiles_dir / "default.yaml"
            profile_file.write_text("""
name: default
description: Default profile
rules:
  - pattern: "Read(*)"
    action: allow
""")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert profile.metadata.name == "default"


class TestProfileLoading:
    """Test profile loading from YAML files."""

    def test_loads_profile_from_yaml_file(self) -> None:
        """Hook should load profile from YAML file in profiles directory."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "custom.yaml"
            profile_file.write_text("""
name: custom
description: Custom profile
version: "2.0"
created_by: test-user
rules:
  - pattern: "Read(*)"
    action: allow
    comment: Allow all reads
  - pattern: "Edit(*.py)"
    action: ask
    comment: Ask for Python files
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("custom")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert profile.metadata.name == "custom"
            assert profile.metadata.description == "Custom profile"
            assert profile.metadata.version == "2.0"
            assert profile.metadata.created_by == "test-user"
            assert len(profile.rules) == 2
            assert profile.rules[0].pattern == "Read(*)"
            assert profile.rules[0].action == "allow"
            assert profile.rules[1].pattern == "Edit(*.py)"
            assert profile.rules[1].action == "ask"

    def test_loads_profile_with_complex_rules(self) -> None:
        """Hook should load profile with complex rule patterns."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "complex.yaml"
            profile_file.write_text("""
name: complex
description: Complex rule patterns
rules:
  - pattern: "Edit(src/**/*.py)"
    action: ask
  - pattern: "Bash(git status|git diff|git log)"
    action: allow
  - pattern: "mcp__playwright__*"
    action: deny
  - pattern: "*"
    action: ask
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("complex")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert len(profile.rules) == 4
            assert profile.rules[0].pattern == "Edit(src/**/*.py)"
            assert profile.rules[1].pattern == "Bash(git status|git diff|git log)"
            assert profile.rules[2].pattern == "mcp__playwright__*"
            assert profile.rules[3].pattern == "*"

    def test_validates_profile_yaml_structure(self) -> None:
        """Hook should validate profile YAML has required structure."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            # Missing name field
            profile_file = profiles_dir / "invalid.yaml"
            profile_file.write_text("""
description: Missing name field
rules:
  - pattern: "Read(*)"
    action: allow
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("invalid")

            loader = ProfileLoader(project_root=project_root)

            with pytest.raises(ProfileLoadError, match="Missing required field: name"):
                loader.load_profile()

    def test_validates_rule_format_in_profile(self) -> None:
        """Hook should validate individual rule format in profiles."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            # Rule missing pattern
            profile_file = profiles_dir / "invalid-rule.yaml"
            profile_file.write_text("""
name: invalid-rule
rules:
  - action: allow
    comment: Missing pattern
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("invalid-rule")

            loader = ProfileLoader(project_root=project_root)

            with pytest.raises(ProfileLoadError, match="Missing required field: pattern"):
                loader.load_profile()

    def test_handles_yaml_parsing_errors_gracefully(self) -> None:
        """Hook should handle YAML parsing errors gracefully."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            # Invalid YAML syntax
            profile_file = profiles_dir / "bad-yaml.yaml"
            profile_file.write_text("""
name: bad-yaml
rules:
  - pattern: "Read(*)"
    action: allow
  [invalid yaml syntax
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("bad-yaml")

            loader = ProfileLoader(project_root=project_root)

            with pytest.raises(ProfileLoadError, match="Failed to load profile"):
                loader.load_profile()

    def test_falls_back_to_builtin_default_profile(self) -> None:
        """Hook should fall back to built-in default profile if no files found."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            home_dir = Path(temp_dir) / "fake_home"
            home_dir.mkdir()
            # No .claudeguard directory at all

            loader = ProfileLoader(project_root=project_root, home_directory=home_dir)
            profile = loader.load_profile()

            assert profile.metadata.name == "default"
            assert profile.metadata.created_by == "claudeguard"
            assert len(profile.rules) > 0  # Should have default rules


class TestMultiProfileSupport:
    """Test support for multiple profiles in the same project."""

    def test_loads_different_profiles_by_name(self) -> None:
        """Hook should load different profiles by name from profiles directory."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            # Create multiple profiles
            dev_profile = profiles_dir / "development.yaml"
            dev_profile.write_text("""
name: development
description: Development profile
rules:
  - pattern: "Edit(*)"
    action: allow
""")

            prod_profile = profiles_dir / "production.yaml"
            prod_profile.write_text("""
name: production
description: Production profile
rules:
  - pattern: "Edit(*)"
    action: deny
""")

            # Test loading development profile
            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("development")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert profile.metadata.name == "development"
            assert profile.rules[0].action == "allow"

            # Switch to production profile
            active_file.write_text("production")

            profile = loader.load_profile()

            assert profile.metadata.name == "production"
            assert profile.rules[0].action == "deny"

    def test_handles_missing_profile_gracefully(self) -> None:
        """Hook should handle requests for non-existent profiles gracefully."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            # Reference non-existent profile
            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("nonexistent")

            loader = ProfileLoader(project_root=project_root)

            with pytest.raises(ProfileLoadError, match="Profile 'nonexistent' not found"):
                loader.load_profile()

    def test_profile_isolation_between_projects(self) -> None:
        """Hook should isolate profiles between different projects."""
        with TemporaryDirectory() as temp_dir:
            # Create two separate project directories
            project1 = Path(temp_dir) / "project1"
            project2 = Path(temp_dir) / "project2"

            for project_dir in [project1, project2]:
                claudeguard_dir = project_dir / ".claudeguard"
                profiles_dir = claudeguard_dir / "profiles"
                profiles_dir.mkdir(parents=True)

                profile_file = profiles_dir / "default.yaml"
                profile_file.write_text(f"""
name: default
description: Profile for {project_dir.name}
rules:
  - pattern: "Edit(*)"
    action: {"allow" if project_dir.name == "project1" else "deny"}
""")

            # Test project1
            loader1 = ProfileLoader(project_root=project1)
            profile1 = loader1.load_profile()

            # Test project2
            loader2 = ProfileLoader(project_root=project2)
            profile2 = loader2.load_profile()

            assert profile1.metadata.description == "Profile for project1"
            assert profile2.metadata.description == "Profile for project2"
            assert profile1.rules[0].action == "allow"
            assert profile2.rules[0].action == "deny"


class TestProfileRuleOrder:
    """Test that profile rule order is preserved and respected."""

    def test_preserves_rule_order_from_yaml_file(self) -> None:
        """Hook should preserve rule order as defined in YAML file."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "ordered.yaml"
            profile_file.write_text("""
name: ordered
description: Test rule ordering
rules:
  - pattern: "Edit(*.py)"
    action: allow
    comment: First rule
  - pattern: "Edit(*)"
    action: deny
    comment: Second rule
  - pattern: "*"
    action: ask
    comment: Fallback rule
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("ordered")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert len(profile.rules) == 3
            assert profile.rules[0].pattern == "Edit(*.py)"
            assert profile.rules[0].comment == "First rule"
            assert profile.rules[1].pattern == "Edit(*)"
            assert profile.rules[1].comment == "Second rule"
            assert profile.rules[2].pattern == "*"
            assert profile.rules[2].comment == "Fallback rule"
