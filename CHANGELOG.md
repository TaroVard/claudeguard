# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-08-20

### Added
- CLI version command (`claudeguard --version`) for better user experience
- CHANGELOG.md file following Keep a Changelog format

### Changed
- Improved CLI help output to include version option

## [0.1.0] - 2025-08-20

### Added
- Initial release of claudeguard - Claude Code security guard
- Hook integration with Claude Code's permission system
- Pattern-based security rules (glob, regex, MCP-specific patterns)
- Profile system with built-in profiles: default, minimal, yolo
- CLI interface with commands: install, status, create-profile, list-profiles, switch-profile, delete-profile, uninstall
- Fail-safe security architecture (errors default to "ask")
- DoS protection for regex patterns to prevent backtracking attacks
- Comprehensive test suite with 394+ tests
- Support for Python 3.10, 3.11, and 3.12
- Project-level and home directory profile hierarchy
- Profile validation and sanitized error handling

### Security
- Implemented secure defaults with fail-safe behavior
- Added input validation and path traversal protection
- Included sensitive information sanitization in error messages
- Regex complexity limits to prevent denial-of-service attacks

[0.1.1]: https://github.com/tarovard/claudeguard/releases/tag/v0.1.1
[0.1.0]: https://github.com/tarovard/claudeguard/releases/tag/v0.1.0
