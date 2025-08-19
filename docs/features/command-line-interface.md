# Command Line Interface

claudeguard provides a comprehensive command-line interface for managing Claude Code security profiles and permissions.

## Installation & Setup

### `claudeguard install`
Initializes claudeguard in your Claude Code project and installs the permission hook.

```bash
claudeguard install
```

**What it does:**
- Creates `.claudeguard/profiles/default.yaml` with comprehensive security rules
- Modifies `.claude/settings.local.json` to add the claudeguard permission hook
- Provides clear next steps for restart and customization

**Output example:**
```
✅ Created default profile at .claudeguard/profiles/default.yaml
✅ Installed claudeguard hook in .claude/settings.local.json
📝 Restart Claude Code to activate claudeguard
🔧 Edit .claudeguard/profiles/default.yaml to customize security rules
```

### `claudeguard uninstall`
Safely removes claudeguard hook from Claude Code while preserving your security profiles.

```bash
claudeguard uninstall
```

**What it does:**
- Removes claudeguard hooks from Claude Code settings
- Preserves all security profiles for easy reinstallation
- Provides feedback on successful removal

## Status & Information

### `claudeguard status`
Shows current claudeguard configuration and system health.

```bash
claudeguard status
```

**Example output:**
```
🔒 claudeguard Status

Active Profile: development (12 rules)
Hook Status: ✅ Installed and configured
Profiles Available: 3 (default, development, testing)
Security Rules: 12 active rules loaded
Last Updated: 2 hours ago
```

### `claudeguard list-profiles`
Lists all available security profiles with their details.

```bash
claudeguard list-profiles
```

**Example output:**
```
📋 Available Profiles

→ development (active)
  Description: Development environment rules
  Rules: 12
  Location: .claudeguard/profiles/development.yaml

  default
  Description: Default security configuration
  Rules: 16
  Location: .claudeguard/profiles/default.yaml

⚠️ testing (corrupted)
  Error: Invalid YAML syntax
  Location: .claudeguard/profiles/testing.yaml
```

## Profile Management

### `claudeguard switch-profile <name>`
Changes the active security profile.

```bash
claudeguard switch-profile development
claudeguard switch-profile default
```

**Features:**
- Validates profile exists and has correct structure
- Provides immediate feedback on successful switching
- Updates `.claudeguard/active_profile` file

### `claudeguard create-profile <name>`
Creates new security profiles with flexible options.

```bash
# Create minimal profile
claudeguard create-profile testing

# Create from existing profile as template
claudeguard create-profile staging --from development

# Create with description and auto-switch
claudeguard create-profile production --description "Production security rules" --switch
```

**Options:**
- `--from <template>`: Use existing profile as template
- `--description <text>`: Set profile description
- `--switch`: Automatically switch to new profile after creation

### `claudeguard delete-profile <name>`
Removes security profiles with safety protections.

```bash
# Safe deletion
claudeguard delete-profile old-profile

# Force delete active profile (switches to default)
claudeguard delete-profile development --force
```

**Safety features:**
- Cannot delete the default profile
- Requires `--force` flag to delete active profiles
- Automatically switches to default when active profile is deleted
- Confirms deletion before proceeding

## Usage Patterns

### Team Collaboration
```bash
# Setup claudeguard for team project
claudeguard install

# Create team-specific profile
claudeguard create-profile team-security --description "Team security standards"

# Commit profiles to git for sharing
git add .claudeguard/
git commit -m "Add team security profiles"
```

### Environment-Specific Profiles
```bash
# Development environment (more permissive)
claudeguard create-profile development --from default
claudeguard switch-profile development

# Production environment (more restrictive)
claudeguard create-profile production --description "Production security"
claudeguard switch-profile production
```

### Profile Testing
```bash
# Check current configuration
claudeguard status

# List all available profiles
claudeguard list-profiles

# Test switching between profiles
claudeguard switch-profile testing
claudeguard switch-profile default
```

## Error Handling

claudeguard provides clear error messages and graceful fallback behavior:

- **Missing profiles**: Automatically creates default profile
- **Corrupted profiles**: Falls back to built-in safe defaults
- **Permission errors**: Provides specific guidance for resolution
- **Invalid commands**: Shows helpful usage information

## Next Steps

After installing claudeguard:
1. **Restart Claude Code** to activate the permission hook
2. **Review default rules** in `.claudeguard/profiles/default.yaml`
3. **Customize patterns** to match your project needs
4. **Create additional profiles** for different environments
5. **Commit profiles to git** for team sharing

See [Security Rules](security-rules.md) for detailed information about configuring security patterns and policies.
