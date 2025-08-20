"""Command-line interface for claudeguard."""

from __future__ import annotations

import json
import re
import shutil
import string
import sys
from collections.abc import Callable
from importlib import metadata
from pathlib import Path
from typing import Any

import click
import yaml

from claudeguard.builtin_profiles import (
    create_default_profile_data,
    create_minimal_profile_data,
    create_yolo_profile_data,
)
from claudeguard.profile_loader import ProfileLoader

VALID_PROFILE_CHARS = frozenset(string.ascii_letters + string.digits + "_-")
DEFAULT_TEMPLATE_NAME = "default"
PROFILE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def _validate_profile_name(name: str) -> None:
    """Validate profile name for security and format compliance."""
    if not name:
        click.echo("❌ Invalid profile name")
        click.echo("   Profile name cannot be empty")
        sys.exit(1)

    if not PROFILE_NAME_PATTERN.match(name):
        click.echo("❌ Invalid profile name")
        click.echo("   Profile names can only contain letters, numbers, hyphens, and underscores")
        sys.exit(1)


def _validate_claudeguard_setup(claudeguard_dir: Path) -> Path:
    """Validate claudeguard directory setup and return profiles directory.

    Used by create-profile command.
    """
    if not claudeguard_dir.exists():
        click.echo("❌ claudeguard not initialized in this project")
        click.echo("   Run 'claudeguard install' to get started")
        sys.exit(1)

    profiles_dir = claudeguard_dir / "profiles"
    if not profiles_dir.exists():
        click.echo("❌ No profiles directory found")
        click.echo("   Run 'claudeguard install' to set up the profile structure")
        sys.exit(1)

    return profiles_dir


def _validate_claudeguard_setup_common(claudeguard_dir: Path) -> Path:
    """Common claudeguard validation for most commands."""
    if not claudeguard_dir.exists():
        click.echo("❌ claudeguard not initialized in this project")
        click.echo("   Run 'claudeguard install' to get started")
        sys.exit(1)

    profiles_dir = claudeguard_dir / "profiles"
    if not profiles_dir.exists():
        click.echo("❌ No profiles found")
        click.echo("   Run 'claudeguard install' to create a default profile")
        sys.exit(1)

    return profiles_dir


def _get_claudeguard_directories() -> tuple[Path, Path]:
    """Get and validate claudeguard and profiles directories."""
    claudeguard_dir = Path.cwd() / ".claudeguard"
    profiles_dir = _validate_claudeguard_setup_common(claudeguard_dir)
    return claudeguard_dir, profiles_dir


def _get_active_profile_name(claudeguard_dir: Path) -> str:
    """Get active profile name with fallback to 'default'."""
    active_profile_file = claudeguard_dir / "active_profile"
    if not active_profile_file.exists():
        return "default"

    try:
        content = active_profile_file.read_text().strip()
        if content and content.replace("-", "").replace("_", "").isalnum():
            return content
    except (OSError, UnicodeDecodeError):
        pass

    return "default"


def _is_claudeguard_hook_installed() -> bool:
    """Check if claudeguard hook is installed in Claude Code settings."""
    settings_file = Path.cwd() / ".claude" / "settings.local.json"
    if not settings_file.exists():
        return False

    try:
        with open(settings_file) as f:
            settings = json.load(f)
            pre_tool_hooks = settings.get("hooks", {}).get("PreToolUse", [])
            for hook_group in pre_tool_hooks:
                if isinstance(hook_group, dict) and "hooks" in hook_group:
                    for hook in hook_group["hooks"]:
                        if isinstance(hook, dict) and hook.get("command") == "claudeguard-hook":
                            return True
    except (json.JSONDecodeError, FileNotFoundError):
        pass

    return False


def _validate_profile_path(profile_name: str, profiles_dir: Path) -> Path:
    """Validate and return secure profile file path."""
    profile_file = profiles_dir / f"{profile_name}.yaml"

    if profile_file.resolve().parent != profiles_dir.resolve():
        click.echo("❌ Invalid profile path")
        sys.exit(1)

    return profile_file


def _load_template_data(template_file: Path, template_name: str) -> dict[str, Any] | None:
    """Load template profile data with error handling."""
    if not template_file.exists():
        if template_name != DEFAULT_TEMPLATE_NAME:
            click.echo(f"❌ Template profile '{template_name}' not found")
            sys.exit(1)
        return None

    try:
        with open(template_file) as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else None
    except yaml.YAMLError:
        click.echo(f"❌ Invalid YAML in template profile '{template_name}'")
        sys.exit(1)
    except OSError as e:
        click.echo(f"❌ Error reading template profile '{template_name}': {e}")
        sys.exit(1)


@click.group()
@click.version_option(version=metadata.version("claudeguard"), prog_name="claudeguard")
def cli() -> None:
    """claudeguard - Claude Code security guard with reliable permissions."""


def _init_claudeguard_project() -> bool:
    """Initialize claudeguard in current project.

    Returns True if initialization was needed.
    """
    try:
        current_dir = Path.cwd()
        claudeguard_dir = current_dir / ".claudeguard"
        profiles_dir = claudeguard_dir / "profiles"
        active_profile_file = claudeguard_dir / "active_profile"

        # All seed profiles to create
        seed_profiles: list[tuple[str, Callable[[], dict[str, Any]]]] = [
            ("default.yaml", create_default_profile_data),
            ("minimal.yaml", create_minimal_profile_data),
            ("yolo.yaml", create_yolo_profile_data),
        ]

        initialization_needed = False

        if not claudeguard_dir.exists():
            profiles_dir.mkdir(parents=True, exist_ok=True)
            initialization_needed = True

        elif not profiles_dir.exists():
            profiles_dir.mkdir(parents=True, exist_ok=True)
            initialization_needed = True

        # Create all seed profiles if they don't exist
        for profile_filename, profile_factory in seed_profiles:
            profile_file = profiles_dir / profile_filename
            if not profile_file.exists():
                profile_data = profile_factory()
                with open(profile_file, "w") as f:
                    yaml.dump(profile_data, f, default_flow_style=False, indent=2)
                initialization_needed = True

        # Set default active profile if none exists
        if not active_profile_file.exists():
            active_profile_file.write_text("default")
            initialization_needed = True

        return initialization_needed

    except (OSError, PermissionError) as e:
        click.echo(f"❌ Error initializing claudeguard: {e}")
        sys.exit(1)


@cli.command()
def install() -> None:
    """Install and initialize claudeguard in current project."""
    settings_file = Path.cwd() / ".claude" / "settings.local.json"

    if not settings_file.exists():
        click.echo("❌ This is not a Claude Code directory!")
        click.echo(f"   {settings_file} not found")
        click.echo("   Please run this from a Claude Code project directory")
        sys.exit(1)

    # Initialize claudeguard project structure
    initialization_needed = _init_claudeguard_project()

    if initialization_needed:
        click.echo("✅ Initialized claudeguard with seed profiles")
        click.echo("📁 Created profiles: default, minimal, yolo")
        click.echo("📝 Set 'default' as active profile")

    # Install hook into Claude Code
    settings = {}
    if settings_file.stat().st_size > 0:
        try:
            with open(settings_file) as f:
                content = f.read().strip()
                if content and content != "{}":
                    settings = json.loads(content)
        except json.JSONDecodeError:
            click.echo("⚠️  Warning: Invalid JSON in settings file, creating backup...")
            backup_file = settings_file.with_suffix(".json.backup")
            shutil.copy2(settings_file, backup_file)
            click.echo(f"   Backup saved as {backup_file}")
            settings = {}

    if "hooks" not in settings:
        settings["hooks"] = {}

    if "PreToolUse" not in settings["hooks"]:
        settings["hooks"]["PreToolUse"] = []

    hook_already_installed = _is_claudeguard_hook_installed()
    if not hook_already_installed:
        claudeguard_hook_group = {
            "matcher": "*",
            "hooks": [{"type": "command", "command": "claudeguard-hook", "timeout": 30}],
        }

        settings["hooks"]["PreToolUse"].append(claudeguard_hook_group)

        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        click.echo("✅ Installed claudeguard hook in Claude Code")
        click.echo(f"⚙️  Updated {settings_file}")
    else:
        click.echo("i  claudeguard hook already installed")

    click.echo("📝 Next steps:")
    if not hook_already_installed:
        click.echo("   1. Restart Claude Code to load the new hooks")
        click.echo("   2. Test with any Claude Code tool operation")
        click.echo("   3. Customize profiles/ for your team's needs")
        click.echo("   4. Commit .claudeguard/ to git for team sharing")
    else:
        click.echo("   1. Customize profiles/ for your team's needs")
        click.echo("   2. Commit .claudeguard/ to git for team sharing")


@cli.command()
def uninstall() -> None:
    """Remove claudeguard hook from Claude Code."""
    settings_file = Path.cwd() / ".claude" / "settings.local.json"

    # Check if we're in a Claude Code directory
    if not settings_file.exists():
        click.echo("❌ This is not a Claude Code directory!")
        click.echo(f"   {settings_file} not found")
        click.echo("   claudeguard hook cannot be removed without Claude settings file")
        sys.exit(1)

    hook_removed = False

    # Remove hook from Claude Code settings
    if settings_file.stat().st_size > 0:
        try:
            with open(settings_file) as f:
                content = f.read().strip()
                if content and content != "{}":
                    settings = json.loads(content)
                else:
                    settings = {}
        except json.JSONDecodeError:
            click.echo("⚠️  Warning: Invalid JSON in settings file")
            settings = {}

        if "hooks" in settings and "PreToolUse" in settings["hooks"]:
            original_hooks = settings["hooks"]["PreToolUse"][:]
            # Filter out claudeguard hooks
            settings["hooks"]["PreToolUse"] = [
                hook_group
                for hook_group in settings["hooks"]["PreToolUse"]
                if not (
                    isinstance(hook_group, dict)
                    and "hooks" in hook_group
                    and any(
                        isinstance(hook, dict) and hook.get("command") == "claudeguard-hook"
                        for hook in hook_group["hooks"]
                    )
                )
            ]

            if len(settings["hooks"]["PreToolUse"]) < len(original_hooks):
                hook_removed = True

                # Clean up empty hooks structure if needed
                if not settings["hooks"]["PreToolUse"]:
                    del settings["hooks"]["PreToolUse"]
                    if not settings["hooks"]:
                        del settings["hooks"]

                with open(settings_file, "w") as f:
                    json.dump(settings, f, indent=2)

    if hook_removed:
        click.echo("✅ Removed claudeguard hook from Claude Code")
        click.echo(f"⚙️  Updated {settings_file}")
        click.echo("📝 Restart Claude Code to complete hook removal")
    else:
        click.echo("i  claudeguard hook was not installed")

    # Note about keeping project files
    claudeguard_dir = Path.cwd() / ".claudeguard"
    if claudeguard_dir.exists():
        click.echo("i  claudeguard project files kept in .claudeguard/")
        click.echo("   Run 'claudeguard install' to reinstall the hook")


@cli.command()
def status() -> None:
    """Show current claudeguard status and configuration."""
    claudeguard_dir, profiles_dir = _get_claudeguard_directories()

    try:
        loader = ProfileLoader()
        profile = loader.load_profile()

        click.echo("📋 claudeguard Status")
        click.echo(f"   Project: {Path.cwd().name}")
        click.echo(f"   Profile: {profile.metadata.name}")
        click.echo(f"   Description: {profile.metadata.description}")
        click.echo(f"   Rules: {len(profile.rules)} configured")

        active_name = _get_active_profile_name(claudeguard_dir)
        click.echo(f"   Active Profile File: {active_name}")

        hook_installed = _is_claudeguard_hook_installed()
        hook_status = "✅ installed" if hook_installed else "❌ not installed"
        click.echo(f"   Claude Code hook: {hook_status}")

        if not hook_installed:
            click.echo("   Run 'claudeguard install' to set up Claude Code integration")

    except Exception as e:
        click.echo(f"❌ Error reading profile: {e}")


@cli.command()
def list_profiles() -> None:
    """List available security profiles."""
    claudeguard_dir, profiles_dir = _get_claudeguard_directories()
    active_profile_name = _get_active_profile_name(claudeguard_dir)

    profiles_found = []

    if profiles_dir.exists():
        for profile_path in profiles_dir.glob("*.yaml"):
            try:
                with open(profile_path) as f:
                    profile_data = yaml.safe_load(f)
                name = profile_data.get("name", profile_path.stem)
                description = profile_data.get("description", "")
                marker = "✓" if name == active_profile_name else ""
                profiles_found.append((name, description, marker))
            except (yaml.YAMLError, OSError, KeyError):
                profiles_found.append((profile_path.stem, "Profile file (corrupted)", "⚠"))

    if not profiles_found:
        click.echo("❌ No profiles found")
        click.echo("   Run 'claudeguard install' to create a default profile")
        sys.exit(1)

    click.echo("📋 Available profiles:")
    for name, description, marker in profiles_found:
        marker_str = f" {marker}" if marker else ""
        click.echo(f"   {name}{marker_str}")
        if description:
            click.echo(f"      {description}")


@cli.command()
@click.argument("profile_name")
def switch_profile(profile_name: str) -> None:
    """Switch to a different security profile."""
    claudeguard_dir, profiles_dir = _get_claudeguard_directories()
    current_profile_name = _get_active_profile_name(claudeguard_dir)

    if current_profile_name == profile_name:
        click.echo(f"✅ Already using profile '{profile_name}'")
        return

    target_profile_file = profiles_dir / f"{profile_name}.yaml"
    if not target_profile_file.exists():
        available_profiles: list[str] = []
        if profiles_dir.exists():
            available_profiles.extend(p.stem for p in profiles_dir.glob("*.yaml"))

        click.echo(f"❌ Profile '{profile_name}' not found")
        if available_profiles:
            click.echo(f"   Available profiles: {', '.join(available_profiles)}")
        else:
            click.echo("   No profiles found. Run 'claudeguard install' to create default profile")
        sys.exit(1)
    try:
        with open(target_profile_file) as f:
            profile_data = yaml.safe_load(f)

        if not isinstance(profile_data, dict):
            click.echo(f"❌ Profile '{profile_name}' has invalid structure")
            sys.exit(1)

        if "name" not in profile_data:
            click.echo(f"❌ Profile '{profile_name}' missing required 'name' field")
            sys.exit(1)

        if "rules" not in profile_data or not isinstance(profile_data["rules"], list):
            click.echo(f"❌ Profile '{profile_name}' has invalid rules structure")
            sys.exit(1)

    except (yaml.YAMLError, OSError) as e:
        click.echo(f"❌ Cannot read profile '{profile_name}': {e}")
        sys.exit(1)

    try:
        active_profile_file = claudeguard_dir / "active_profile"
        active_profile_file.write_text(profile_name)
        click.echo(f"✅ Switched to profile '{profile_name}'")

        description = profile_data.get("description", "")
        if description:
            click.echo(f"📝 {description}")

    except OSError as e:
        click.echo(f"❌ Error switching profile: {e}")
        sys.exit(1)


@cli.command()
@click.argument("profile_name")
@click.option(
    "--from",
    "template_name",
    default=DEFAULT_TEMPLATE_NAME,
    help="Template profile to copy from",
)
@click.option("--description", help="Description for the new profile")
@click.option(
    "--switch",
    is_flag=True,
    help="Switch to the new profile after creating it",
)
def create_profile(
    profile_name: str,
    template_name: str,
    description: str | None,
    *,
    switch: bool,
) -> None:
    """Create a new security profile."""
    claudeguard_dir = Path.cwd() / ".claudeguard"

    _validate_profile_name(profile_name)
    profiles_dir = _validate_claudeguard_setup(claudeguard_dir)
    new_profile_file = _validate_profile_path(profile_name, profiles_dir)

    if new_profile_file.exists():
        click.echo(f"❌ Profile '{profile_name}' already exists")
        sys.exit(1)

    template_file = profiles_dir / f"{template_name}.yaml"
    template_data = _load_template_data(template_file, template_name)

    if template_data:
        profile_data = template_data.copy()
        profile_data["name"] = profile_name
        if description:
            profile_data["description"] = description
        template_msg = f" from template '{template_name}'"
    else:
        profile_data = create_default_profile_data(profile_name, description)
        template_msg = ""

    try:
        with open(new_profile_file, "w") as f:
            yaml.dump(profile_data, f, default_flow_style=False, indent=2)

        click.echo(f"✅ Created profile '{profile_name}'{template_msg}")

        if switch:
            _switch_to_profile(claudeguard_dir, profile_name)
        else:
            click.echo(f"📝 Run 'claudeguard switch-profile {profile_name}' to use this profile")

    except (OSError, PermissionError) as e:
        click.echo(f"❌ Error creating profile: {e}")
        sys.exit(1)


@cli.command()
@click.argument("profile_name")
@click.option("--force", is_flag=True, help="Delete profile even if it's currently active")
def delete_profile(profile_name: str, *, force: bool) -> None:
    """Delete a security profile."""
    claudeguard_dir, profiles_dir = _get_claudeguard_directories()

    _validate_profile_name(profile_name)

    if profile_name == "default":
        click.echo("❌ Cannot delete the default profile")
        sys.exit(1)

    profile_file = _validate_profile_path(profile_name, profiles_dir)

    if not profile_file.exists():
        click.echo(f"❌ Profile '{profile_name}' not found")
        sys.exit(1)

    # Check if this is the active profile
    active_profile_name = _get_active_profile_name(claudeguard_dir)
    if active_profile_name == profile_name and not force:
        click.echo(f"❌ Cannot delete active profile '{profile_name}'")
        click.echo("   Switch to another profile first or use --force")
        sys.exit(1)

    try:
        profile_file.unlink()
        click.echo(f"✅ Deleted profile '{profile_name}'")

        # If we deleted the active profile with --force, switch to default
        if active_profile_name == profile_name:
            _switch_to_profile(claudeguard_dir, "default")

    except OSError as e:
        click.echo(f"❌ Error deleting profile: {e}")
        sys.exit(1)


def _switch_to_profile(claudeguard_dir: Path, profile_name: str) -> None:
    """Switch to a specific profile."""
    active_profile_file = claudeguard_dir / "active_profile"
    try:
        active_profile_file.write_text(profile_name)
        click.echo(f"🔗 Switched to profile '{profile_name}'")
    except OSError as e:
        click.echo(f"⚠️  Profile created but failed to switch: {e}")


if __name__ == "__main__":
    cli()
