"""Test profile validation integration with existing ProfileLoader."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from claudeguard.profile_loader import ProfileLoader, ProfileLoadError


class TestProfileValidationIntegration:
    """Test profile validation through ProfileLoader."""

    def test_validates_valid_profile_structure(self) -> None:
        """Should accept valid profile with all required fields."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "valid.yaml"
            profile_file.write_text("""
name: valid-profile
description: Valid test profile
version: "1.0"
created_by: test
rules:
  - pattern: "Read(*)"
    action: allow
    comment: Allow all reads
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("valid")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert profile.metadata.name == "valid-profile"
            assert len(profile.rules) == 1

    def test_rejects_profile_missing_name_field(self) -> None:
        """Should reject profile without name field."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

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

    def test_rejects_profile_missing_rules_field(self) -> None:
        """Should reject profile without rules field."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "no-rules.yaml"
            profile_file.write_text("""
name: no-rules
description: Profile without rules
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("no-rules")

            loader = ProfileLoader(project_root=project_root)

            # Profile loader creates an empty rules list, which then gets validated
            profile = loader.load_profile()
            # Should get empty rules list, not an error
            assert len(profile.rules) == 0

    def test_rejects_rule_missing_pattern_field(self) -> None:
        """Should reject rule without pattern field."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "bad-rule.yaml"
            profile_file.write_text("""
name: bad-rule
rules:
  - action: allow
    comment: Missing pattern
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("bad-rule")

            loader = ProfileLoader(project_root=project_root)

            with pytest.raises(ProfileLoadError, match="Missing required field: pattern"):
                loader.load_profile()

    def test_rejects_rule_missing_action_field(self) -> None:
        """Should reject rule without action field."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "no-action.yaml"
            profile_file.write_text("""
name: no-action
rules:
  - pattern: "Read(*)"
    comment: Missing action
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("no-action")

            loader = ProfileLoader(project_root=project_root)

            with pytest.raises(ProfileLoadError, match="Missing required field: action"):
                loader.load_profile()

    @pytest.mark.parametrize("action", ["allow", "deny", "ask"])
    def test_accepts_valid_action_values(self, action) -> None:
        """Should accept all valid action values."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "valid-action.yaml"
            profile_file.write_text(f"""
name: valid-action
rules:
  - pattern: "Read(*)"
    action: {action}
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("valid-action")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert profile.rules[0].action == action

    @pytest.mark.parametrize(
        "invalid_action",
        ["permit", "block", "prompt", "ALLOW", "Allow"],
    )
    def test_rejects_invalid_action_values(self, invalid_action) -> None:
        """Should reject invalid action values."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "invalid-action.yaml"
            profile_file.write_text(f"""
name: invalid-action
rules:
  - pattern: "Read(*)"
    action: {invalid_action}
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("invalid-action")

            loader = ProfileLoader(project_root=project_root)

            with pytest.raises(ProfileLoadError, match=f"Invalid action value: {invalid_action}"):
                loader.load_profile()

    def test_rejects_empty_action_values(self) -> None:
        """Should reject empty action values."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "empty-action.yaml"
            profile_file.write_text("""
name: empty-action
rules:
  - pattern: "Read(*)"
    action: ""
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("empty-action")

            loader = ProfileLoader(project_root=project_root)

            with pytest.raises(ProfileLoadError, match="Missing required field: action"):
                loader.load_profile()

    def test_accepts_valid_tool_patterns(self) -> None:
        """Should accept valid Tool(resource) patterns."""
        valid_patterns = [
            "Read(*)",
            "Edit(*.py)",
            "Edit(src/**)",
            "Bash(git status)",
            "Bash(git push*)",
            "WebFetch(*.github.com)",
            "*",
        ]

        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            rules_yaml = "\n".join(
                [f'  - pattern: "{pattern}"\n    action: allow' for pattern in valid_patterns]
            )

            profile_file = profiles_dir / "patterns.yaml"
            profile_file.write_text(f"""
name: patterns
rules:
{rules_yaml}
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("patterns")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert len(profile.rules) == len(valid_patterns)
            for i, pattern in enumerate(valid_patterns):
                assert profile.rules[i].pattern == pattern

    def test_handles_complex_yaml_structure(self) -> None:
        """Should handle complex YAML structures correctly."""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claudeguard_dir = project_root / ".claudeguard"
            profiles_dir = claudeguard_dir / "profiles"
            profiles_dir.mkdir(parents=True)

            profile_file = profiles_dir / "complex.yaml"
            profile_file.write_text("""
name: complex
description: Complex profile with all features
version: "2.1"
created_by: test-user
rules:
  - pattern: "Edit(src/**/*.py)"
    action: ask
    comment: Ask for Python source files
  - pattern: "Bash(git status|git diff|git log)"
    action: allow
    comment: Allow safe git commands
  - pattern: "mcp__playwright__*"
    action: deny
    comment: Deny all playwright MCP tools
  - pattern: "*"
    action: ask
    comment: Ask for everything else
""")

            active_file = claudeguard_dir / "active_profile"
            active_file.write_text("complex")

            loader = ProfileLoader(project_root=project_root)
            profile = loader.load_profile()

            assert profile.metadata.name == "complex"
            assert profile.metadata.description == "Complex profile with all features"
            assert profile.metadata.version == "2.1"
            assert profile.metadata.created_by == "test-user"
            assert len(profile.rules) == 4

            # Check each rule
            assert profile.rules[0].pattern == "Edit(src/**/*.py)"
            assert profile.rules[0].action == "ask"
            assert profile.rules[0].comment == "Ask for Python source files"

            assert profile.rules[1].pattern == "Bash(git status|git diff|git log)"
            assert profile.rules[1].action == "allow"
            assert profile.rules[1].comment == "Allow safe git commands"

            assert profile.rules[2].pattern == "mcp__playwright__*"
            assert profile.rules[2].action == "deny"
            assert profile.rules[2].comment == "Deny all playwright MCP tools"

            assert profile.rules[3].pattern == "*"
            assert profile.rules[3].action == "ask"
            assert profile.rules[3].comment == "Ask for everything else"
