"""
Test profile data models for type safety and immutability.

This module tests the fundamental data structures used in the profile system.
Following TDD principles - these tests will fail until the models are implemented.
"""

from __future__ import annotations

from typing import get_type_hints

import pytest

from claudeguard.models import Profile, ProfileMetadata, ProfileRule
from tests.conftest import make_profile, make_profile_metadata, make_profile_rule


class TestProfileRule:
    """Test the ProfileRule immutable data structure."""

    def test_profile_rule_creation(self) -> None:
        """ProfileRule should be creatable with required fields."""
        rule = ProfileRule(pattern="Read(*)", action="allow", comment="Allow all reads")

        assert rule.pattern == "Read(*)"
        assert rule.action == "allow"
        assert rule.comment == "Allow all reads"

    def test_profile_rule_immutability(self) -> None:
        """ProfileRule should be immutable (frozen dataclass)."""
        rule = make_profile_rule()

        with pytest.raises(AttributeError):
            rule.pattern = "Edit(*)"

        with pytest.raises(AttributeError):
            rule.action = "deny"

    def test_profile_rule_type_hints(self) -> None:
        """ProfileRule should have proper type hints."""
        hints = get_type_hints(ProfileRule)

        assert "pattern" in hints
        assert "action" in hints
        assert "comment" in hints

        assert hasattr(hints["action"], "__args__")

    def test_profile_rule_default_comment(self) -> None:
        """ProfileRule should allow empty comment with default."""
        rule = ProfileRule(pattern="Read(*)", action="allow")
        assert rule.comment == ""

    def test_profile_rule_factory_defaults(self) -> None:
        """Factory should create valid ProfileRule with sensible defaults."""
        rule = make_profile_rule()

        assert isinstance(rule.pattern, str)
        assert rule.action in ("allow", "deny", "ask")
        assert isinstance(rule.comment, str)

    def test_profile_rule_factory_overrides(self) -> None:
        """Factory should accept overrides for all fields."""
        rule = make_profile_rule(
            pattern="Bash(rm -rf*)", action="deny", comment="Dangerous operation"
        )

        assert rule.pattern == "Bash(rm -rf*)"
        assert rule.action == "deny"
        assert rule.comment == "Dangerous operation"


class TestProfileMetadata:
    """Test the ProfileMetadata immutable data structure."""

    def test_profile_metadata_creation(self) -> None:
        """ProfileMetadata should be creatable with required fields."""
        metadata = ProfileMetadata(
            name="test-profile",
            description="Test profile",
            version="1.0",
            created_by="test-user",
        )

        assert metadata.name == "test-profile"
        assert metadata.description == "Test profile"
        assert metadata.version == "1.0"
        assert metadata.created_by == "test-user"

    def test_profile_metadata_immutability(self) -> None:
        """ProfileMetadata should be immutable (frozen dataclass)."""
        metadata = make_profile_metadata()

        with pytest.raises(AttributeError):
            metadata.name = "new-name"

        with pytest.raises(AttributeError):
            metadata.description = "new description"

    def test_profile_metadata_defaults(self) -> None:
        """ProfileMetadata should provide sensible defaults."""
        metadata = ProfileMetadata(name="test")

        assert metadata.name == "test"
        assert metadata.description == ""
        assert metadata.version == "1.0"
        assert metadata.created_by == "claudeguard"

    def test_profile_metadata_factory_defaults(self) -> None:
        """Factory should create valid ProfileMetadata."""
        metadata = make_profile_metadata()

        assert isinstance(metadata.name, str)
        assert isinstance(metadata.description, str)
        assert isinstance(metadata.version, str)
        assert isinstance(metadata.created_by, str)

    def test_profile_metadata_factory_overrides(self) -> None:
        """Factory should accept overrides for all fields."""
        metadata = make_profile_metadata(
            name="custom-profile",
            description="Custom description",
            version="2.0",
            created_by="admin",
        )

        assert metadata.name == "custom-profile"
        assert metadata.description == "Custom description"
        assert metadata.version == "2.0"
        assert metadata.created_by == "admin"


class TestProfile:
    """Test the complete Profile immutable data structure."""

    def test_profile_creation(self) -> None:
        """Profile should be creatable with metadata and rules."""
        metadata = make_profile_metadata(name="test-profile")
        rules = (
            make_profile_rule(pattern="Read(*)", action="allow"),
            make_profile_rule(pattern="*", action="ask"),
        )

        profile = Profile(metadata=metadata, rules=rules)

        assert profile.metadata == metadata
        assert profile.rules == rules
        assert len(profile.rules) == 2

    def test_profile_immutability(self) -> None:
        """Profile should be immutable (frozen dataclass)."""
        profile = make_profile()

        with pytest.raises(AttributeError):
            profile.metadata = make_profile_metadata(name="new-name")

        with pytest.raises(AttributeError):
            profile.rules = ()

    def test_profile_rules_tuple_immutability(self) -> None:
        """Profile rules should be stored as immutable tuple."""
        profile = make_profile()

        assert isinstance(profile.rules, tuple)
        with pytest.raises(TypeError):
            profile.rules[0] = make_profile_rule()

    def test_profile_factory_creates_complete_profile(self) -> None:
        """Factory should create complete Profile with defaults."""
        profile = make_profile()

        assert isinstance(profile.metadata, ProfileMetadata)
        assert isinstance(profile.rules, tuple)
        assert len(profile.rules) > 0

        for rule in profile.rules:
            assert isinstance(rule, ProfileRule)

    def test_profile_factory_overrides_metadata(self) -> None:
        """Factory should allow metadata overrides."""
        custom_metadata = make_profile_metadata(name="custom")
        profile = make_profile(metadata=custom_metadata)

        assert profile.metadata.name == "custom"

    def test_profile_factory_overrides_rules(self) -> None:
        """Factory should allow rules overrides."""
        custom_rules = (make_profile_rule(pattern="Edit(*)", action="deny"),)
        profile = make_profile(rules=custom_rules)

        assert len(profile.rules) == 1
        assert profile.rules[0].pattern == "Edit(*)"
        assert profile.rules[0].action == "deny"

    def test_profile_supports_empty_rules(self) -> None:
        """Profile should support empty rules tuple."""
        profile = make_profile(rules=())

        assert len(profile.rules) == 0
        assert isinstance(profile.rules, tuple)
