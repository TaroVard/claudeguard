"""Profile loading system for claudeguard security configurations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from claudeguard.default_rules import get_default_rules
from claudeguard.models import Profile, ProfileMetadata, ProfileRule


class ProfileLoadError(Exception):
    pass


class ProfileLoader:
    def __init__(self, project_root: Path | None = None, home_directory: Path | None = None):
        self._project_root = project_root
        self._home_directory = home_directory

    def load_profile(self) -> Profile:
        project_profile = self._try_load_project_profile()
        if project_profile:
            return project_profile

        home_profile = self._try_load_home_profile()
        if home_profile:
            return home_profile

        return self._generate_default_profile()

    def _try_load_project_profile(self) -> Profile | None:
        project_root = self._project_root or self._find_project_root()
        if not project_root:
            return None

        claudeguard_dir = project_root / ".claudeguard"
        if not claudeguard_dir.exists():
            return None

        return self._load_active_project_profile(claudeguard_dir)

    def _load_active_project_profile(self, claudeguard_dir: Path) -> Profile | None:
        """Load the active profile from the profiles directory structure."""
        active_profile_file = claudeguard_dir / "active_profile"
        has_explicit_active_profile = active_profile_file.exists()

        active_profile_name = self._get_active_profile_name(claudeguard_dir)
        if not active_profile_name:
            return self._generate_default_profile()

        profiles_dir = claudeguard_dir / "profiles"
        profile_path = profiles_dir / f"{active_profile_name}.yaml"

        return self._handle_profile_file_loading(
            profiles_dir, profile_path, active_profile_name, has_explicit_active_profile
        )

    def _handle_profile_file_loading(
        self,
        profiles_dir: Path,
        profile_path: Path,
        active_profile_name: str,
        has_explicit_active_profile: bool,
    ) -> Profile | None:
        """Handle the loading of a specific profile file with error handling."""
        if not profiles_dir.exists():
            return self._generate_default_profile()

        if not profile_path.exists():
            if has_explicit_active_profile and active_profile_name != "default":
                raise ProfileLoadError(
                    f"Profile '{active_profile_name}' not found in {profiles_dir}"
                )
            return self._generate_default_profile()

        return self._load_profile_from_path(profile_path)

    def _try_load_home_profile(self) -> Profile | None:
        home_directory = self._home_directory or Path.home()
        home_claudeguard_dir = home_directory / ".claudeguard"
        if not home_claudeguard_dir.exists():
            return None

        active_profile_file = home_claudeguard_dir / "active_profile"
        profiles_dir = home_claudeguard_dir / "profiles"

        if not profiles_dir.exists():
            return None

        if active_profile_file.exists():
            profile_name = active_profile_file.read_text().strip()
            profile_path = profiles_dir / f"{profile_name}.yaml"
        else:
            profile_path = profiles_dir / "default.yaml"

        return self._load_profile_from_path(profile_path)

    def _find_project_root(self) -> Path | None:
        current = Path.cwd()
        for parent in [current, *list(current.parents)]:
            claudeguard_dir = parent / ".claudeguard"
            if claudeguard_dir.exists() and claudeguard_dir.is_dir():
                return parent
        return None

    def _load_profile_from_path(self, profile_path: Path) -> Profile | None:
        if not profile_path.exists():
            return None

        try:
            with open(profile_path) as f:
                data = yaml.safe_load(f)

            if not data:
                return None

            return self._parse_profile_data(data)

        except PermissionError:
            return None
        except (yaml.YAMLError, OSError) as e:
            raise ProfileLoadError(f"Failed to load profile from {profile_path}: {e}") from e

    def _parse_profile_data(self, data: dict[str, Any]) -> Profile:
        try:
            if not isinstance(data, dict):
                raise ProfileLoadError("Profile data must be a dictionary")

            name = data.get("name")
            if not name:
                raise ProfileLoadError("Missing required field: name")

            metadata = ProfileMetadata(
                name=name,
                description=data.get("description", ""),
                version=data.get("version", "1.0"),
                created_by=data.get("created_by", "unknown"),
            )

            rules_data = data.get("rules", [])
            if not isinstance(rules_data, list):
                raise ProfileLoadError("Invalid rule structure: rules must be a list")

            rules = []
            for i, rule in enumerate(rules_data):
                if not isinstance(rule, dict):
                    raise ProfileLoadError(f"Invalid rule structure: rule {i} must be a dictionary")

                pattern = rule.get("pattern")
                action = rule.get("action")

                if not pattern:
                    raise ProfileLoadError(f"Missing required field: pattern in rule {i}")
                if not action:
                    raise ProfileLoadError(f"Missing required field: action in rule {i}")

                if action not in ("allow", "deny", "ask"):
                    raise ProfileLoadError(f"Invalid action value: {action} in rule {i}")

                rules.append(
                    ProfileRule(pattern=pattern, action=action, comment=rule.get("comment", ""))
                )

            return Profile(metadata=metadata, rules=tuple(rules))

        except ProfileLoadError:
            raise
        except (KeyError, TypeError, ValueError) as e:
            raise ProfileLoadError(f"Invalid profile format: {e}") from e

    def _get_active_profile_name(self, claudeguard_dir: Path) -> str | None:
        """Read the active profile name from .claudeguard/active_profile file."""
        active_profile_file = claudeguard_dir / "active_profile"

        if not active_profile_file.exists():
            return "default"

        try:
            with open(active_profile_file, encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                return "default"

            if not content.replace("-", "").replace("_", "").isalnum():
                return "default"

            return content
        except (OSError, PermissionError, UnicodeDecodeError):
            return "default"

    def _generate_default_profile(self) -> Profile:
        metadata = ProfileMetadata(
            name="default",
            description="Default security profile for claudeguard",
            version="1.0",
            created_by="claudeguard",
        )

        return Profile(metadata=metadata, rules=get_default_rules())
