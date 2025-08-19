# Testing Strategy

claudeguard employs a comprehensive testing strategy with multiple layers of validation to ensure security, reliability, and maintainable code quality.

## Testing Philosophy

### Core Principles

1. **Security-First Testing**: Every security-critical path must have comprehensive test coverage
2. **Behavior-Driven Development**: Tests focus on expected behavior rather than implementation details
3. **Fail-Safe Validation**: Extensive testing of error conditions to ensure secure defaults
4. **Performance Validation**: Critical paths must meet performance requirements
5. **Real-World Scenarios**: Tests simulate actual usage patterns and edge cases

### Test-Driven Development (TDD)

Many test files explicitly state "these tests will fail until implementation is created", demonstrating the TDD approach:

```python
# Example from test files
def test_profile_validation_comprehensive():
    """
    This test will fail until comprehensive profile validation is implemented.
    Tests all aspects of profile structure validation.
    """
    # Test implementation follows...
```

## Test Architecture

### Test Organization Structure

```
tests/
├── conftest.py                           # Shared fixtures and configuration
├── factories.py                          # Test data factories
├── __init__.py                          # Test package initialization
│
├── unit/                                # Unit tests for individual components
│   ├── test_pattern_matcher.py
│   ├── test_profile_loader.py
│   ├── test_permission_decision.py
│   └── test_models.py
│
├── integration/                         # Integration tests
│   ├── test_profile_system_integration.py
│   ├── test_hook_integration.py
│   └── test_cli_integration.py
│
├── security/                           # Security-focused tests
│   ├── test_regex_dos_protection.py
│   ├── test_path_traversal.py
│   └── test_input_validation.py
│
├── performance/                        # Performance tests
│   ├── test_pattern_matching_performance.py
│   └── test_profile_loading_performance.py
│
└── edge_cases/                         # Edge case and error handling
    ├── test_error_handling.py
    ├── test_malformed_input.py
    └── test_edge_cases_final.py
```

## Test Types and Coverage

### 1. Unit Tests

#### Pattern Matching Tests (`test_simplified_pattern_matcher.py`)
```python
class TestPatternMatching:
    """Comprehensive pattern matching validation"""

    def test_exact_pattern_matching(self):
        """Test exact string matching"""
        assert matches_pattern("Edit(main.py)", "Edit(main.py)")
        assert not matches_pattern("Edit(main.py)", "Edit(other.py)")

    def test_glob_pattern_matching(self):
        """Test glob wildcard patterns"""
        assert matches_pattern("Edit(*.py)", "Edit(main.py)")
        assert matches_pattern("Edit(src/**)", "Edit(src/utils/helper.py)")
        assert not matches_pattern("Edit(*.js)", "Edit(main.py)")

    def test_regex_pattern_matching(self):
        """Test regex patterns with security validation"""
        assert matches_pattern("Edit(/.*\\.py$/)", "Edit(main.py)")

        # Security: Should reject dangerous patterns
        with pytest.raises(PatternSecurityError):
            matches_pattern("Edit(/(.*)*$/)", "Edit(anything)")

    def test_mcp_tool_patterns(self):
        """Test MCP tool matching"""
        assert matches_pattern("mcp__server__tool", "mcp__server__tool")
        assert matches_pattern("mcp__server__*", "mcp__server__anything")
        assert not matches_pattern("mcp__server__*", "mcp__other__tool")
```

#### Profile System Tests (`test_profile_loader.py`, `test_profile_models.py`)
```python
class TestProfileLoader:
    """Profile loading and validation tests"""

    def test_hierarchical_profile_loading(self):
        """Test project -> home -> default fallback"""
        with mock_filesystem():
            # No project profile, no home profile
            profile = load_active_profile()
            assert profile.name == "default"
            assert len(profile.rules) == 16  # Default rule count

    def test_profile_validation(self):
        """Test comprehensive profile validation"""
        invalid_profile = {
            "name": "",  # Invalid: empty name
            "rules": [
                {"pattern": "Edit(*)", "action": "invalid"}  # Invalid action
            ]
        }

        with pytest.raises(ProfileValidationError):
            validate_profile(invalid_profile)

    def test_corrupted_profile_handling(self):
        """Test graceful handling of corrupted profiles"""
        with mock_file_content("invalid: yaml: content"):
            profile = load_profile_safe("corrupted.yaml")
            assert profile is None  # Should return None, not crash
```

#### Permission Decision Tests (`test_permission_decision_logic.py`)
```python
class TestPermissionDecision:
    """Core permission decision logic tests"""

    def test_rule_precedence(self):
        """Test that first matching rule wins"""
        rules = [
            ProfileRule(pattern="Edit(*.py)", action="deny"),
            ProfileRule(pattern="Edit(*)", action="allow"),  # More general
        ]

        tool_call = ToolCall(tool="Edit", input={"file_path": "main.py"})
        result = evaluate_rules(tool_call, rules)

        assert result.action == "deny"  # First rule should match
        assert result.rule.pattern == "Edit(*.py)"

    def test_fallback_behavior(self):
        """Test default fallback when no rules match"""
        rules = [ProfileRule(pattern="Read(*)", action="allow")]
        tool_call = ToolCall(tool="Edit", input={"file_path": "main.py"})

        result = evaluate_rules(tool_call, rules)
        assert result.action == "ask"  # Default fallback
```

### 2. Integration Tests

#### Profile System Integration (`test_profile_system_integration.py`)
```python
class TestProfileSystemIntegration:
    """End-to-end profile system testing"""

    def test_complete_profile_workflow(self):
        """Test full profile creation, loading, and switching"""
        # Create profile
        create_profile("test-profile", description="Test profile")

        # Switch to profile
        switch_profile("test-profile")

        # Load and verify
        profile = load_active_profile()
        assert profile.name == "test-profile"

        # Test profile isolation
        with temp_directory():
            other_profile = load_active_profile()
            assert other_profile.name == "default"  # Different context

    def test_team_collaboration_workflow(self):
        """Test git-based team profile sharing"""
        # Setup team profiles
        setup_team_profiles()

        # Simulate git clone
        with simulated_git_repo():
            profiles = list_available_profiles()
            assert "team-dev" in profiles
            assert "team-prod" in profiles

            # Test profile switching
            switch_profile("team-dev")
            verify_team_permissions()
```

#### CLI Integration Tests (`test_cli_edge_cases_final.py`)
```python
class TestCLIIntegration:
    """Command-line interface integration tests"""

    def test_complete_installation_workflow(self):
        """Test full claudeguard installation process"""
        with temp_project():
            # Install claudeguard
            result = run_cli(["install"])
            assert result.exit_code == 0

            # Verify installation
            assert Path(".claudeguard/profiles/default.yaml").exists()
            assert claude_settings_has_hook()

            # Test status command
            result = run_cli(["status"])
            assert "✅ Installed and configured" in result.output

    def test_profile_management_workflow(self):
        """Test profile creation, switching, deletion"""
        with installed_claudeguard():
            # Create profile
            result = run_cli(["create-profile", "test", "--description", "Test"])
            assert result.exit_code == 0

            # Switch profile
            result = run_cli(["switch-profile", "test"])
            assert result.exit_code == 0

            # List profiles
            result = run_cli(["list-profiles"])
            assert "→ test (active)" in result.output

            # Delete profile
            result = run_cli(["delete-profile", "test", "--force"])
            assert result.exit_code == 0
```

### 3. Security Tests

#### Regex DoS Protection (`test_tool_star_pattern_bug.py`)
```python
class TestRegexSecurity:
    """Security tests for regex pattern matching"""

    def test_regex_dos_protection(self):
        """Test protection against ReDoS attacks"""
        dangerous_patterns = [
            "/(.*)*$/",           # Nested quantifiers
            "/(.+)+$/",           # Nested quantifiers
            "/a*a*a*a*a*a*$/",   # Exponential backtracking
        ]

        for pattern in dangerous_patterns:
            with pytest.raises(PatternSecurityError):
                matches_pattern(f"Edit({pattern})", "Edit(anything)")

    def test_regex_timeout_protection(self):
        """Test timeout protection for long-running regex"""
        # This pattern could cause catastrophic backtracking
        pattern = "/a*a*a*a*a*a*b$/"
        test_string = "a" * 100 + "c"  # No 'b' at end

        start_time = time.time()
        result = matches_pattern(f"Edit({pattern})", f"Edit({test_string})")
        end_time = time.time()

        # Should timeout quickly, not hang
        assert (end_time - start_time) < 0.5
        assert result is False

    def test_pattern_length_limits(self):
        """Test pattern length security limits"""
        long_pattern = "a" * 2000  # Exceeds MAX_PATTERN_LENGTH

        with pytest.raises(PatternSecurityError):
            matches_pattern(f"Edit(/{long_pattern}/)", "Edit(anything)")
```

#### Input Validation Tests (`test_cli_security_validation.py`)
```python
class TestInputValidation:
    """Security validation of user inputs"""

    def test_profile_name_validation(self):
        """Test profile name injection prevention"""
        invalid_names = [
            "../../../etc/passwd",  # Path traversal
            "profile; rm -rf /",    # Command injection
            "profile\x00.yaml",     # Null byte injection
            "CON",                  # Windows reserved name
        ]

        for invalid_name in invalid_names:
            result = run_cli(["create-profile", invalid_name])
            assert result.exit_code != 0
            assert "Invalid profile name" in result.output

    def test_file_path_security(self):
        """Test file path traversal protection"""
        dangerous_paths = [
            "../../../etc/passwd",
            "/etc/passwd",
            "..\\..\\..\\windows\\system32",
            "profile.yaml\x00.txt",
        ]

        for dangerous_path in dangerous_paths:
            with pytest.raises(SecurityError):
                validate_profile_path(dangerous_path)
```

### 4. Performance Tests

#### Pattern Matching Performance
```python
class TestPatternMatchingPerformance:
    """Performance validation for pattern matching"""

    def test_simple_pattern_performance(self):
        """Test basic pattern matching speed"""
        tool_call = ToolCall(tool="Edit", input={"file_path": "main.py"})
        pattern = "Edit(*.py)"

        # Should complete 10,000 matches in under 100ms
        start_time = time.time()
        for _ in range(10000):
            matches_pattern(tool_call, pattern)
        end_time = time.time()

        assert (end_time - start_time) < 0.1

    def test_complex_pattern_performance(self):
        """Test complex pattern matching speed"""
        tool_call = ToolCall(tool="Edit", input={"file_path": "src/deep/nested/file.py"})
        pattern = "Edit(src/**/*.py)"

        # Should complete 1,000 complex matches in under 50ms
        start_time = time.time()
        for _ in range(1000):
            matches_pattern(tool_call, pattern)
        end_time = time.time()

        assert (end_time - start_time) < 0.05

    @pytest.mark.slow
    def test_large_profile_performance(self):
        """Test performance with large profiles"""
        # Create profile with 1000 rules
        rules = [
            ProfileRule(pattern=f"Edit(file_{i}.py)", action="allow")
            for i in range(1000)
        ]

        tool_call = ToolCall(tool="Edit", input={"file_path": "file_999.py"})

        start_time = time.time()
        result = evaluate_rules(tool_call, tuple(rules))
        end_time = time.time()

        assert result.action == "allow"
        assert (end_time - start_time) < 0.01  # Should be very fast due to caching
```

### 5. Edge Case Tests

#### Error Handling (`test_error_handling_and_fail_safe.py`)
```python
class TestErrorHandling:
    """Comprehensive error handling validation"""

    def test_corrupted_profile_recovery(self):
        """Test recovery from corrupted profile files"""
        corrupted_scenarios = [
            "invalid: yaml: content",           # YAML syntax error
            '{"json": "instead of yaml"}',      # Wrong format
            "",                                 # Empty file
            "name: test\nrules: invalid",      # Invalid rules structure
        ]

        for corrupted_content in corrupted_scenarios:
            with mock_file_content(corrupted_content):
                # Should not crash, should fall back to defaults
                profile = load_profile_safe("corrupted.yaml")
                assert profile is None or profile.name == "default"

    def test_filesystem_error_handling(self):
        """Test handling of filesystem errors"""
        error_scenarios = [
            PermissionError("Permission denied"),
            FileNotFoundError("File not found"),
            OSError("Disk full"),
            IsADirectoryError("Is a directory"),
        ]

        for error in error_scenarios:
            with mock_filesystem_error(error):
                # Should handle gracefully, not crash
                result = load_profile_safe("nonexistent.yaml")
                assert result is None

    def test_hook_communication_errors(self):
        """Test hook communication error handling"""
        error_scenarios = [
            '{"malformed": json}',              # Invalid JSON
            '{"missing": "required_fields"}',   # Missing fields
            '{"tool": "Unknown", "input": {}}', # Unknown tool
        ]

        for invalid_input in error_scenarios:
            with mock_stdin(invalid_input):
                response = run_hook()
                assert response["action"] == "ask"  # Fail-safe default
                assert "error" in response
```

#### Edge Cases (`test_edge_cases.py`)
```python
class TestEdgeCases:
    """Comprehensive edge case testing"""

    def test_empty_patterns(self):
        """Test handling of empty or whitespace patterns"""
        edge_patterns = ["", "   ", "\t\n", None]

        for pattern in edge_patterns:
            # Should not match anything or crash
            result = matches_pattern("Edit(main.py)", pattern or "")
            assert result is False

    def test_unicode_handling(self):
        """Test unicode file names and patterns"""
        unicode_cases = [
            "файл.py",           # Cyrillic
            "文件.py",           # Chinese
            "ファイル.py",        # Japanese
            "🎉_emoji.py",       # Emoji
        ]

        for unicode_name in unicode_cases:
            tool_call = ToolCall(tool="Edit", input={"file_path": unicode_name})
            assert matches_pattern(tool_call, "Edit(*.py)")

    def test_extremely_long_paths(self):
        """Test handling of very long file paths"""
        long_path = "a/" * 1000 + "file.py"
        tool_call = ToolCall(tool="Edit", input={"file_path": long_path})

        # Should handle without crashing
        result = matches_pattern(tool_call, "Edit(**)")
        assert result is True

    def test_special_characters_in_patterns(self):
        """Test patterns with special regex characters"""
        special_chars = ["[", "]", "(", ")", ".", "+", "?", "^", "$", "|", "\\"]

        for char in special_chars:
            filename = f"file{char}.py"
            tool_call = ToolCall(tool="Edit", input={"file_path": filename})

            # Glob patterns should escape special chars
            assert matches_pattern(tool_call, f"Edit(file{char}.py)")
```

## Test Data and Factories

### Factory Pattern for Test Data (`factories.py`)
```python
class ProfileFactory:
    """Factory for creating test profiles"""

    @staticmethod
    def create_default_profile() -> Profile:
        """Create default test profile"""
        return Profile(
            metadata=ProfileMetadata(
                name="default",
                description="Default test profile",
                version="1.0",
                created_by="test-factory"
            ),
            rules=(
                ProfileRule(pattern="Read(*)", action="allow", comment="Safe reads"),
                ProfileRule(pattern="Edit(*.py)", action="ask", comment="Python files"),
                ProfileRule(pattern="*", action="ask", comment="Default fallback"),
            )
        )

    @staticmethod
    def create_permissive_profile() -> Profile:
        """Create permissive test profile"""
        return Profile(
            metadata=ProfileMetadata(
                name="permissive",
                description="Permissive test profile",
                version="1.0"
            ),
            rules=(
                ProfileRule(pattern="*", action="allow", comment="Allow everything"),
            )
        )

    @staticmethod
    def create_restrictive_profile() -> Profile:
        """Create restrictive test profile"""
        return Profile(
            metadata=ProfileMetadata(
                name="restrictive",
                description="Restrictive test profile",
                version="1.0"
            ),
            rules=(
                ProfileRule(pattern="Read(*)", action="allow", comment="Only allow reads"),
                ProfileRule(pattern="*", action="deny", comment="Deny everything else"),
            )
        )

class ToolCallFactory:
    """Factory for creating test tool calls"""

    @staticmethod
    def create_edit_call(file_path: str) -> ToolCall:
        return ToolCall(tool="Edit", input={"file_path": file_path})

    @staticmethod
    def create_bash_call(command: str) -> ToolCall:
        return ToolCall(tool="Bash", input={"command": command})

    @staticmethod
    def create_mcp_call(tool_name: str) -> ToolCall:
        return ToolCall(tool=tool_name, input={})
```

### Shared Fixtures (`conftest.py`)
```python
@pytest.fixture
def temp_project():
    """Create temporary project directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        try:
            yield Path(temp_dir)
        finally:
            os.chdir(old_cwd)

@pytest.fixture
def mock_filesystem():
    """Mock filesystem operations"""
    with patch("pathlib.Path.exists") as mock_exists, \
         patch("pathlib.Path.read_text") as mock_read_text, \
         patch("pathlib.Path.write_text") as mock_write_text:

        yield MockFileSystem(mock_exists, mock_read_text, mock_write_text)

@pytest.fixture
def default_profile():
    """Provide default test profile"""
    return ProfileFactory.create_default_profile()

@pytest.fixture
def sample_tool_calls():
    """Provide common tool calls for testing"""
    return [
        ToolCallFactory.create_edit_call("main.py"),
        ToolCallFactory.create_edit_call("src/utils.py"),
        ToolCallFactory.create_bash_call("git status"),
        ToolCallFactory.create_mcp_call("mcp__server__tool"),
    ]
```

## Test Execution Strategy

### Test Categories and Markers
```python
# pytest.ini configuration
[tool:pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    security: marks tests as security-focused
    integration: marks tests as integration tests
    performance: marks tests as performance validation
    edge_case: marks tests as edge case validation

# Running specific test categories
pytest -m "not slow"              # Skip slow tests
pytest -m "security"              # Run only security tests
pytest -m "integration"           # Run only integration tests
pytest tests/unit/               # Run only unit tests
```

### Continuous Integration Testing
```yaml
# GitHub Actions workflow
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          uv sync
          uv run pip install pytest-cov pytest-xdist

      - name: Run fast tests
        run: uv run pytest -m "not slow" --cov=src --cov-report=xml

      - name: Run slow tests
        run: uv run pytest -m "slow" --timeout=300

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Local Development Testing
```bash
# Quick development testing
uv run pytest -x                    # Stop on first failure
uv run pytest --lf                  # Run only last failed tests
uv run pytest -k "test_pattern"     # Run tests matching pattern

# Comprehensive testing
uv run pytest --cov=src             # With coverage report
uv run pytest --cov=src --cov-report=html  # HTML coverage report

# Performance testing
uv run pytest -m "performance"      # Run performance tests
uv run pytest --benchmark-only      # Run benchmarks only

# Security testing
uv run pytest -m "security"         # Run security-focused tests
uv run pytest tests/security/       # Run security test directory
```

## Quality Metrics and Coverage

### Coverage Requirements
- **Overall Coverage**: Minimum 95%
- **Security-Critical Code**: 100% coverage required
- **Edge Case Coverage**: All identified edge cases must have tests
- **Performance-Critical Paths**: Must have performance validation

### Quality Metrics
```python
# Coverage configuration (.coveragerc)
[run]
source = src
omit =
    */tests/*
    */conftest.py
    */factories.py

[report]
fail_under = 95
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

### Test Quality Validation
```python
# Test quality checks
def test_all_public_functions_have_tests():
    """Ensure all public functions have corresponding tests"""
    from src.claudeguard import cli, hook, pattern_matcher

    modules = [cli, hook, pattern_matcher]
    tested_functions = get_tested_functions()

    for module in modules:
        public_functions = get_public_functions(module)
        for func in public_functions:
            assert func in tested_functions, f"{func} missing tests"

def test_all_error_paths_covered():
    """Ensure all error conditions are tested"""
    error_conditions = [
        "FileNotFoundError",
        "PermissionError",
        "ProfileValidationError",
        "PatternSecurityError",
    ]

    test_coverage = get_exception_coverage()

    for error in error_conditions:
        assert error in test_coverage, f"{error} not tested"
```

## Best Practices and Guidelines

### Test Writing Guidelines

1. **Test Names Should Be Descriptive**
   ```python
   # Good
   def test_profile_loading_falls_back_to_default_when_project_profile_missing():
       pass

   # Bad
   def test_profile_loading():
       pass
   ```

2. **Arrange-Act-Assert Pattern**
   ```python
   def test_pattern_matching_with_glob_wildcards():
       # Arrange
       tool_call = ToolCall(tool="Edit", input={"file_path": "main.py"})
       pattern = "Edit(*.py)"

       # Act
       result = matches_pattern(tool_call, pattern)

       # Assert
       assert result is True
   ```

3. **Test One Thing at a Time**
   ```python
   # Good - focused test
   def test_regex_pattern_timeout_protection():
       """Test that regex patterns timeout appropriately"""
       # Test implementation

   def test_regex_pattern_security_validation():
       """Test that dangerous patterns are rejected"""
       # Test implementation

   # Bad - testing multiple concerns
   def test_regex_patterns():
       """Test regex patterns"""
       # Tests timeout, security, performance, etc.
   ```

4. **Use Appropriate Test Doubles**
   ```python
   # Use mocks for external dependencies
   @patch("pathlib.Path.read_text")
   def test_profile_loading_with_file_error(mock_read):
       mock_read.side_effect = PermissionError("Access denied")
       result = load_profile_safe("profile.yaml")
       assert result is None

   # Use fakes for complex behaviors
   class FakeFileSystem:
       def __init__(self):
           self.files = {}

       def read_text(self, path):
           return self.files.get(str(path), "")
   ```

### Security Testing Guidelines

1. **Always Test Fail-Safe Behavior**
   ```python
   def test_unknown_tool_defaults_to_ask():
       """Ensure unknown tools default to safe behavior"""
       tool_call = ToolCall(tool="UnknownTool", input={})
       result = make_permission_decision(tool_call)
       assert result.action == "ask"  # Safe default
   ```

2. **Test Attack Scenarios**
   ```python
   def test_path_traversal_attack_prevention():
       """Test protection against directory traversal attacks"""
       malicious_paths = ["../../../etc/passwd", "..\\..\\windows\\system32"]

       for path in malicious_paths:
           with pytest.raises(SecurityError):
               validate_file_path(path)
   ```

3. **Validate Input Sanitization**
   ```python
   def test_profile_name_injection_prevention():
       """Test prevention of command injection in profile names"""
       malicious_names = ["profile; rm -rf /", "profile`whoami`"]

       for name in malicious_names:
           assert not is_valid_profile_name(name)
   ```

The comprehensive testing strategy ensures claudeguard maintains the highest standards of security, reliability, and performance while providing confidence for continuous development and deployment.
