# Team Collaboration

claudeguard enables teams to share consistent security policies across projects and environments through git-based profile management.

## Overview

Teams can create, share, and maintain security profiles that ensure consistent Claude Code permissions across all team members and projects.

**Key Benefits:**
- **Consistency** - Same security rules for everyone
- **Transparency** - Security policies visible in git history
- **Flexibility** - Different profiles for different environments
- **Governance** - Centralized security policy management

## Setting Up Team Profiles

### 1. Initialize claudeguard in Your Project
```bash
# Project maintainer sets up claudeguard
claudeguard install

# This creates:
# .claudeguard/profiles/default.yaml
# .claudeguard/active_profile
# .claude/settings.local.json (not committed)
```

### 2. Create Team-Specific Profiles
```bash
# Create development team profile
claudeguard create-profile team-dev --description "Development team security rules"

# Create production profile
claudeguard create-profile team-prod --description "Production deployment rules"

# Create code review profile
claudeguard create-profile code-review --description "Rules for code review process"
```

### 3. Customize Profiles for Your Team
Edit `.claudeguard/profiles/team-dev.yaml`:
```yaml
name: team-dev
description: Development team security rules
version: "1.0"
created_by: team-lead
rules:
  # Allow all safe operations
  - pattern: "Read(*)"
    action: allow
    comment: "Reading is always safe"

  - pattern: "LS(*)"
    action: allow
    comment: "Directory listing is safe"

  # Allow development tools
  - pattern: "Bash(uv run pytest*)"
    action: allow
    comment: "Testing is encouraged"

  - pattern: "Bash(uv run mypy*)"
    action: allow
    comment: "Type checking is safe"

  # Team-specific rules
  - pattern: "Edit(src/core/**)"
    action: ask
    comment: "Core module changes need extra review"

  - pattern: "Edit(tests/**)"
    action: allow
    comment: "Test files can be freely modified"

  # Still block dangerous operations
  - pattern: "Bash(rm -rf*)"
    action: deny
    comment: "No recursive deletion"

  - pattern: "*"
    action: ask
    comment: "Default: ask for permission"
```

### 4. Commit Profiles to Git
```bash
# Add security profiles to version control
git add .claudeguard/profiles/
git commit -m "Add team security profiles

- team-dev: Permissive rules for development
- team-prod: Restrictive rules for production
- code-review: Rules for reviewing pull requests"

# Push to share with team
git push origin main
```

## Team Member Setup

### 1. Clone and Install
```bash
# Clone project repository
git clone https://github.com/yourteam/project.git
cd project

# Install claudeguard (gets shared profiles)
claudeguard install

# Profiles are automatically available
claudeguard list-profiles
```

### 2. Choose Appropriate Profile
```bash
# Developers use development profile
claudeguard switch-profile team-dev

# Production engineers use production profile
claudeguard switch-profile team-prod

# Code reviewers use review profile
claudeguard switch-profile code-review
```

### 3. Restart Claude Code
Team members restart Claude Code to activate claudeguard with team profiles.

## Profile Management Workflow

### Creating New Profiles
```bash
# Team lead creates new profile
claudeguard create-profile team-frontend --description "Frontend development rules"

# Customize the profile
# Edit .claudeguard/profiles/team-frontend.yaml

# Commit and share
git add .claudeguard/profiles/team-frontend.yaml
git commit -m "Add frontend team security profile"
git push
```

### Updating Existing Profiles
```bash
# Update profile rules
# Edit .claudeguard/profiles/team-dev.yaml

# Commit changes
git add .claudeguard/profiles/team-dev.yaml
git commit -m "Update team-dev profile: allow more test operations"
git push

# Team members get updates on next pull
git pull
# claudeguard automatically picks up changes
```

### Profile Versioning
```yaml
name: team-dev
description: Development team security rules
version: "2.1"  # Increment when making changes
created_by: team-lead
updated_by: alice
last_updated: "2024-01-15"
rules:
  # ... rules
```

## Environment-Specific Collaboration

### Development Teams
**Profile**: `team-dev.yaml`
```yaml
name: team-dev
description: Development environment - permissive for productivity
rules:
  # Allow development tools
  - pattern: "Bash(uv run *)"
    action: allow
    comment: "All uv commands in development"

  # Allow test edits
  - pattern: "Edit(test*/**)"
    action: allow
    comment: "Tests can be freely modified"

  # Ask for source changes (but allow)
  - pattern: "Edit(src/**)"
    action: ask
    comment: "Source code changes for review"

  # Block dangerous operations
  - pattern: "Bash(rm -rf*)"
    action: deny
```

### DevOps/SRE Teams
**Profile**: `team-ops.yaml`
```yaml
name: team-ops
description: Operations team - infrastructure focus
rules:
  # Allow infrastructure tools
  - pattern: "Bash(kubectl *)"
    action: allow
    comment: "Kubernetes operations"

  - pattern: "Bash(terraform *)"
    action: ask
    comment: "Infrastructure changes need review"

  # Allow monitoring
  - pattern: "WebFetch(https://monitoring.*)"
    action: allow
    comment: "Monitoring dashboards"

  # Block application code edits
  - pattern: "Edit(src/**)"
    action: deny
    comment: "Ops team shouldn't edit application code"
```

### Security Teams
**Profile**: `team-security.yaml`
```yaml
name: team-security
description: Security team - audit and compliance focus
rules:
  # Allow security tools
  - pattern: "Bash(security-scan*)"
    action: allow
    comment: "Security scanning tools"

  # Allow audit reads
  - pattern: "Read(*)"
    action: allow
    comment: "Security needs to read everything"

  # Ask for any modifications
  - pattern: "Edit(*)"
    action: ask
    comment: "All edits need security review"

  # Allow compliance checks
  - pattern: "Bash(compliance-check*)"
    action: allow
    comment: "Compliance verification"
```

## Code Review Integration

### Pull Request Security Profile
**Profile**: `code-review.yaml`
```yaml
name: code-review
description: Code review process - balanced permissions
rules:
  # Allow reading everything for review
  - pattern: "Read(*)"
    action: allow
    comment: "Reviewers need to read all files"

  - pattern: "Grep(*)"
    action: allow
    comment: "Searching code during review"

  # Allow safe git operations
  - pattern: "Bash(git diff*)"
    action: allow
    comment: "Viewing changes"

  - pattern: "Bash(git log*)"
    action: allow
    comment: "Checking commit history"

  # Ask for any edits during review
  - pattern: "Edit(*)"
    action: ask
    comment: "Edits during review need justification"

  # Allow test runs
  - pattern: "Bash(uv run pytest*)"
    action: allow
    comment: "Running tests during review"
```

### Using in CI/CD
```yaml
# .github/workflows/security-check.yml
name: Security Check
on: [pull_request]

jobs:
  security-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install claudeguard
        run: |
          pip install claudeguard
          claudeguard install

      - name: Use security profile
        run: claudeguard switch-profile team-security

      - name: Run security scan
        run: |
          # Claude Code will use team-security profile
          claude-code run security-review.md
```

## Global vs Project Profiles

### Global Team Profiles
Located in `~/.claudeguard/profiles/` - shared across all projects:
```bash
# Create global team profiles
mkdir -p ~/.claudeguard/profiles/

# Copy team profiles to global location
cp .claudeguard/profiles/team-*.yaml ~/.claudeguard/profiles/

# Now available in all projects
cd other-project
claudeguard list-profiles  # Shows team-* profiles
```

### Project-Specific Overrides
Project profiles in `.claudeguard/profiles/` override global profiles:
```yaml
# Project-specific profile
name: team-dev
description: Development rules for this specific project
version: "1.0-project-specific"
rules:
  # Project has additional security requirements
  - pattern: "Edit(sensitive/**)"
    action: deny
    comment: "This project has sensitive data"

  # Inherit other rules from base team-dev profile
  # ... standard team-dev rules
```

## Governance and Compliance

### Profile Approval Process
1. **Proposal**: Team member creates new profile or updates existing
2. **Review**: Security team reviews changes
3. **Approval**: Team lead approves and merges
4. **Deployment**: Team members pull updates

### Audit Trail
```bash
# View profile change history
git log --oneline .claudeguard/profiles/

# See who changed what rules
git blame .claudeguard/profiles/team-dev.yaml

# Compare profile versions
git diff HEAD~1 .claudeguard/profiles/team-dev.yaml
```

### Compliance Reporting
```bash
# Generate profile usage report
claudeguard status --report

# View audit logs across team
find . -name "audit.log" -exec cat {} \; | grep "team-prod"

# Check rule compliance
claudeguard validate-profiles --compliance-check
```

## Best Practices

### Profile Organization
```
.claudeguard/profiles/
├── team-dev.yaml          # Development team
├── team-ops.yaml          # Operations team
├── team-security.yaml     # Security team
├── prod-deployment.yaml   # Production deployments
├── code-review.yaml       # Code review process
└── intern.yaml           # New team members
```

### Naming Conventions
- `team-<role>` - Role-based profiles
- `env-<environment>` - Environment-specific profiles
- `process-<workflow>` - Workflow-specific profiles

### Documentation
Create `docs/security/profiles.md`:
```markdown
# Team Security Profiles

## Available Profiles

### team-dev
- **Purpose**: Daily development work
- **Users**: All developers
- **Permissions**: Permissive for productivity

### team-prod
- **Purpose**: Production deployments
- **Users**: Senior engineers, DevOps
- **Permissions**: Highly restrictive

### code-review
- **Purpose**: Pull request reviews
- **Users**: All team members during reviews
- **Permissions**: Read-focused with careful edit controls
```

## Troubleshooting

### Profile Conflicts
```bash
# Check which profile is active
claudeguard status

# List available profiles
claudeguard list-profiles

# Switch if wrong profile is active
claudeguard switch-profile team-dev
```

### Update Issues
```bash
# Pull latest profiles
git pull

# Restart Claude Code to pick up changes
# (claudeguard automatically reloads profiles)
```

### Permission Denied
```bash
# Check if user has correct profile
claudeguard status

# Verify profile rules
cat .claudeguard/profiles/team-dev.yaml

# Check audit log for denied operations
tail .claudeguard/audit.log
```

## Next Steps

1. **Set up team profiles** in your project repository
2. **Define governance process** for profile changes
3. **Create documentation** for your team's security policies
4. **Integrate with CI/CD** for automated security checks
5. **Monitor audit logs** for security insights
6. **Train team members** on profile usage and security practices

See [Security Rules](security-rules.md) for detailed rule configuration and [Pattern Examples](pattern-examples.md) for advanced team-specific patterns.
