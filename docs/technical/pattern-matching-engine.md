# Pattern Matching Engine

The pattern matching engine is the core security component of claudeguard, responsible for matching tool calls against security rule patterns with high performance and security.

## Overview

The pattern matching system uses a strategy pattern with three specialized matchers:
- **GlobResourceMatcher**: fnmatch-based glob patterns with directory support
- **RegexResourceMatcher**: Regex patterns with DoS protection and timeouts
- **McpResourceMatcher**: MCP (Model Context Protocol) tool name matching

## Architecture

### Resource Matcher Interface
```python
from abc import ABC, abstractmethod

class ResourceMatcher(ABC):
    @abstractmethod
    def matches(self, pattern: str, resource: str) -> bool:
        """Match a pattern against a resource string"""
        pass
```

### Pattern Selection Strategy
```python
def select_matcher(pattern: str) -> ResourceMatcher:
    """Choose appropriate matcher based on pattern syntax"""

    # Regex patterns marked with /pattern/ syntax
    if pattern.startswith("/") and pattern.endswith("/"):
        return RegexResourceMatcher()

    # MCP tool patterns
    if pattern.startswith("mcp__"):
        return McpResourceMatcher()

    # Default to glob matching
    return GlobResourceMatcher()
```

## Glob Resource Matcher

### Implementation Details
```python
class GlobResourceMatcher(ResourceMatcher):
    def matches(self, pattern: str, resource: str) -> bool:
        """Enhanced fnmatch with directory support"""

        # Handle special directory patterns
        if "**" in pattern:
            return self._matches_directory_pattern(pattern, resource)

        # Standard glob matching
        return fnmatch.fnmatch(resource, pattern)

    def _matches_directory_pattern(self, pattern: str, path: str) -> bool:
        """Optimized matching for directory recursion patterns"""

        # src/** matches src/file.py, src/dir/file.py, etc.
        if pattern.endswith("/**"):
            base_dir = pattern[:-3]  # Remove /**
            normalized_path = path.replace("\\", "/")
            return normalized_path.startswith(base_dir + "/") or normalized_path == base_dir

        # **/*.py matches any .py file in any directory
        if pattern.startswith("**/"):
            suffix_pattern = pattern[3:]  # Remove **/
            return any(
                fnmatch.fnmatch(part, suffix_pattern)
                for part in path.split("/")
            )

        # General ** handling
        return self._recursive_glob_match(pattern, path)
```

### Directory Pattern Optimization
```python
def _recursive_glob_match(self, pattern: str, path: str) -> bool:
    """Efficient recursive directory matching"""

    pattern_parts = pattern.split("/")
    path_parts = path.split("/")

    return self._match_parts(pattern_parts, path_parts, 0, 0)

def _match_parts(self, pattern_parts: list[str], path_parts: list[str],
                 p_idx: int, path_idx: int) -> bool:
    """Recursive part matching with early termination"""

    # Base cases
    if p_idx >= len(pattern_parts):
        return path_idx >= len(path_parts)

    if path_idx >= len(path_parts):
        return all(part == "**" for part in pattern_parts[p_idx:])

    current_pattern = pattern_parts[p_idx]

    # Handle ** (zero or more directories)
    if current_pattern == "**":
        # Try matching zero directories
        if self._match_parts(pattern_parts, path_parts, p_idx + 1, path_idx):
            return True

        # Try matching one or more directories
        for i in range(path_idx + 1, len(path_parts) + 1):
            if self._match_parts(pattern_parts, path_parts, p_idx + 1, i):
                return True

        return False

    # Regular pattern matching
    if fnmatch.fnmatch(path_parts[path_idx], current_pattern):
        return self._match_parts(pattern_parts, path_parts, p_idx + 1, path_idx + 1)

    return False
```

### Examples
```python
matcher = GlobResourceMatcher()

# File patterns
matcher.matches("*.py", "main.py")           # True
matcher.matches("test_*.py", "test_main.py") # True
matcher.matches("*.js", "main.py")           # False

# Directory patterns
matcher.matches("src/**", "src/main.py")           # True
matcher.matches("src/**", "src/utils/helper.py")   # True
matcher.matches("src/**", "tests/test_main.py")    # False

# Complex patterns
matcher.matches("**/test_*.py", "tests/test_main.py")     # True
matcher.matches("**/test_*.py", "src/tests/test_util.py") # True
```

## Regex Resource Matcher

### Security-First Design
```python
class RegexResourceMatcher(ResourceMatcher):
    # Security limits to prevent ReDoS attacks
    MAX_PATTERN_LENGTH = 1000
    MAX_QUANTIFIERS = 20
    TIMEOUT_SECONDS = 0.1
    DANGEROUS_PATTERNS = [
        ".*.*",     # Nested quantifiers
        ".+.+",     # Nested quantifiers
        "(.*)*",    # Exponential backtracking
        "(.+)+",    # Exponential backtracking
    ]

    def __init__(self):
        self._compiled_patterns: dict[str, re.Pattern] = {}

    def matches(self, pattern: str, resource: str) -> bool:
        """Secure regex matching with timeout protection"""

        # Remove regex delimiters /pattern/
        if pattern.startswith("/") and pattern.endswith("/"):
            pattern = pattern[1:-1]

        # Security validation
        if not self._is_safe_pattern(pattern):
            raise PatternSecurityError(f"Unsafe regex pattern: {pattern}")

        # Compile and cache pattern
        compiled = self._get_compiled_pattern(pattern)

        # Execute with timeout protection
        return self._execute_with_timeout(compiled, resource)
```

### Pattern Security Validation
```python
def _is_safe_pattern(self, pattern: str) -> bool:
    """Comprehensive pattern security validation"""

    # Length limit
    if len(pattern) > self.MAX_PATTERN_LENGTH:
        return False

    # Count quantifiers
    quantifier_count = (
        pattern.count("*") + pattern.count("+") +
        pattern.count("?") + pattern.count("{")
    )
    if quantifier_count > self.MAX_QUANTIFIERS:
        return False

    # Check for dangerous patterns
    for dangerous in self.DANGEROUS_PATTERNS:
        if dangerous in pattern:
            return False

    # Validate syntax
    try:
        re.compile(pattern)
    except re.error:
        return False

    return True

def _get_compiled_pattern(self, pattern: str) -> re.Pattern:
    """Cache compiled patterns for performance"""
    if pattern not in self._compiled_patterns:
        self._compiled_patterns[pattern] = re.compile(pattern)
    return self._compiled_patterns[pattern]
```

### Timeout Protection
```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: float):
    """Context manager for operation timeout"""
    def timeout_handler(signum, frame):
        raise TimeoutError("Regex execution timeout")

    # Set up signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def _execute_with_timeout(self, compiled: re.Pattern, resource: str) -> bool:
    """Execute regex with timeout protection"""
    try:
        with timeout(self.TIMEOUT_SECONDS):
            return bool(compiled.match(resource))
    except TimeoutError:
        # Log security event
        logger.warning(f"Regex timeout for pattern: {compiled.pattern}")
        return False
```

### Examples
```python
matcher = RegexResourceMatcher()

# Valid patterns
matcher.matches("/src/.*/.*\\.py/", "src/utils/helper.py")  # True
matcher.matches("/test_.*\\.py$/", "test_main.py")          # True

# Security-blocked patterns
try:
    matcher.matches("/(.*)*$/", "anything")  # Raises PatternSecurityError
except PatternSecurityError:
    pass
```

## MCP Resource Matcher

### MCP Tool Pattern Support
```python
class McpResourceMatcher(ResourceMatcher):
    def matches(self, pattern: str, resource: str) -> bool:
        """Match MCP tool patterns using fnmatch"""

        # Exact MCP tool matching
        if not "*" in pattern:
            return pattern == resource

        # Wildcard MCP tool matching
        return fnmatch.fnmatch(resource, pattern)
```

### MCP Pattern Examples
```python
matcher = McpResourceMatcher()

# Exact tool matching
matcher.matches("mcp__server__tool", "mcp__server__tool")     # True
matcher.matches("mcp__server__tool", "mcp__server__other")   # False

# Server-wide patterns
matcher.matches("mcp__server__*", "mcp__server__tool")       # True
matcher.matches("mcp__server__*", "mcp__server__other")      # True
matcher.matches("mcp__server__*", "mcp__other__tool")        # False

# Cross-server patterns
matcher.matches("mcp__*", "mcp__server__tool")               # True
matcher.matches("mcp__*", "mcp__other__tool")                # True
matcher.matches("mcp__*", "regular_tool")                    # False
```

## Resource Extraction

### Tool-Specific Resource Extraction
```python
def extract_resource(tool_call: ToolCall) -> str:
    """Extract relevant resource string from tool call"""

    tool_name = tool_call.tool
    tool_input = tool_call.input

    # File operation tools
    if tool_name in ("Edit", "Read", "Write"):
        return tool_input.get("file_path", "")

    if tool_name == "NotebookEdit":
        return tool_input.get("notebook_path", "")

    # Directory operations
    if tool_name in ("LS", "Glob"):
        return tool_input.get("path", "")

    # Search operations
    if tool_name == "Grep":
        path = tool_input.get("path", "")
        pattern = tool_input.get("pattern", "")
        return f"{path}:{pattern}" if path else pattern

    # Command execution
    if tool_name == "Bash":
        return tool_input.get("command", "")

    # Web operations
    if tool_name in ("WebFetch", "WebSearch"):
        return tool_input.get("url", "") or tool_input.get("query", "")

    # MCP tools
    if tool_name.startswith("mcp__"):
        return tool_name

    # Default: return tool name for bare patterns
    return tool_name
```

### Resource Extraction Examples
```python
# File operations
tool_call = ToolCall(tool="Edit", input={"file_path": "src/main.py"})
resource = extract_resource(tool_call)  # "src/main.py"

# Commands
tool_call = ToolCall(tool="Bash", input={"command": "git status"})
resource = extract_resource(tool_call)  # "git status"

# MCP tools
tool_call = ToolCall(tool="mcp__server__tool", input={})
resource = extract_resource(tool_call)  # "mcp__server__tool"
```

## Pattern Matching Pipeline

### Main Matching Function
```python
def matches_pattern(tool_call: ToolCall, pattern: str) -> bool:
    """Main pattern matching function"""

    # Handle universal wildcard
    if pattern == "*":
        return True

    # Handle bare tool patterns
    if not "(" in pattern:
        return pattern == tool_call.tool

    # Parse tool and resource pattern
    tool_pattern, resource_pattern = parse_pattern(pattern)

    # Match tool name
    if not fnmatch.fnmatch(tool_call.tool, tool_pattern):
        return False

    # Extract resource from tool call
    resource = extract_resource(tool_call)

    # Match resource using appropriate matcher
    matcher = select_matcher(resource_pattern)
    return matcher.matches(resource_pattern, resource)
```

### Pattern Parsing
```python
def parse_pattern(pattern: str) -> tuple[str, str]:
    """Parse pattern into tool and resource components"""

    # Examples:
    # "Edit(*.py)" -> ("Edit", "*.py")
    # "Bash(git status)" -> ("Bash", "git status")
    # "mcp__server__*" -> ("mcp__server__*", "")

    if "(" not in pattern:
        # Bare tool pattern
        return pattern, ""

    # Tool(resource) pattern
    tool_end = pattern.index("(")
    tool_pattern = pattern[:tool_end]

    if not pattern.endswith(")"):
        raise PatternParseError(f"Invalid pattern syntax: {pattern}")

    resource_pattern = pattern[tool_end + 1:-1]  # Remove ( and )

    return tool_pattern, resource_pattern
```

## Performance Optimizations

### Pattern Caching
```python
class PatternCache:
    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, bool] = {}
        self._max_size = max_size

    def get(self, pattern: str, resource: str) -> bool | None:
        """Get cached result for pattern-resource pair"""
        key = f"{pattern}:{resource}"
        return self._cache.get(key)

    def put(self, pattern: str, resource: str, result: bool):
        """Cache pattern matching result"""
        if len(self._cache) >= self._max_size:
            # Simple LRU: remove oldest entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        key = f"{pattern}:{resource}"
        self._cache[key] = result
```

### Early Exit Optimization
```python
def evaluate_rules(tool_call: ToolCall, rules: tuple[ProfileRule, ...]) -> MatchResult:
    """Evaluate rules with early exit on first match"""

    for rule in rules:
        if matches_pattern(tool_call, rule.pattern):
            return MatchResult(
                action=rule.action,
                rule=rule,
                matched_pattern=rule.pattern
            )

    # No rules matched - default fallback
    return MatchResult(action="ask", rule=None, matched_pattern="*")
```

### Batch Matching Optimization
```python
def matches_any_pattern(tool_call: ToolCall, patterns: list[str]) -> bool:
    """Optimized matching against multiple patterns"""

    # Pre-extract resource once
    resource = extract_resource(tool_call)

    # Group patterns by type for efficient matching
    glob_patterns = []
    regex_patterns = []
    mcp_patterns = []

    for pattern in patterns:
        if pattern.startswith("/") and pattern.endswith("/"):
            regex_patterns.append(pattern)
        elif pattern.startswith("mcp__"):
            mcp_patterns.append(pattern)
        else:
            glob_patterns.append(pattern)

    # Batch process each type
    return (
        any(GlobResourceMatcher().matches(p, resource) for p in glob_patterns) or
        any(RegexResourceMatcher().matches(p, resource) for p in regex_patterns) or
        any(McpResourceMatcher().matches(p, resource) for p in mcp_patterns)
    )
```

## Error Handling

### Pattern Validation Errors
```python
class PatternError(Exception):
    """Base class for pattern-related errors"""
    pass

class PatternSecurityError(PatternError):
    """Raised when pattern violates security constraints"""
    pass

class PatternParseError(PatternError):
    """Raised when pattern syntax is invalid"""
    pass

class PatternTimeoutError(PatternError):
    """Raised when pattern matching times out"""
    pass
```

### Graceful Error Recovery
```python
def safe_pattern_match(tool_call: ToolCall, pattern: str) -> bool:
    """Pattern matching with graceful error handling"""
    try:
        return matches_pattern(tool_call, pattern)
    except PatternSecurityError:
        # Log security violation attempt
        logger.warning(f"Security violation in pattern: {pattern}")
        return False
    except PatternTimeoutError:
        # Log timeout and fail safe
        logger.warning(f"Pattern matching timeout: {pattern}")
        return False
    except Exception as e:
        # Log unexpected error and fail safe
        logger.error(f"Unexpected pattern matching error: {e}")
        return False
```

## Testing Strategy

### Unit Tests for Each Matcher
```python
class TestGlobResourceMatcher:
    def test_simple_glob_patterns(self):
        matcher = GlobResourceMatcher()
        assert matcher.matches("*.py", "main.py")
        assert not matcher.matches("*.py", "main.js")

    def test_directory_patterns(self):
        matcher = GlobResourceMatcher()
        assert matcher.matches("src/**", "src/main.py")
        assert matcher.matches("src/**", "src/utils/helper.py")

class TestRegexResourceMatcher:
    def test_security_validation(self):
        matcher = RegexResourceMatcher()
        with pytest.raises(PatternSecurityError):
            matcher.matches("/(.*)*$/", "test")

    def test_timeout_protection(self):
        matcher = RegexResourceMatcher()
        # This should not hang
        result = matcher.matches("/a*a*a*a*a*a*$/)$/", "aaaaaaaaaaaaaaaaaaaaX")
        assert result is False

class TestMcpResourceMatcher:
    def test_exact_mcp_matching(self):
        matcher = McpResourceMatcher()
        assert matcher.matches("mcp__server__tool", "mcp__server__tool")
        assert not matcher.matches("mcp__server__tool", "mcp__server__other")
```

### Integration Tests
```python
def test_full_pattern_matching_pipeline():
    """Test complete pattern matching workflow"""
    tool_call = ToolCall(
        tool="Edit",
        input={"file_path": "src/main.py"}
    )

    patterns = [
        "Read(*)",           # Should not match
        "Edit(*.js)",        # Should not match
        "Edit(src/**)",      # Should match
        "Edit(*)",           # Would match but not reached
    ]

    # Test that first matching pattern wins
    for i, pattern in enumerate(patterns):
        result = matches_pattern(tool_call, pattern)
        if i < 2:
            assert not result
        else:
            assert result
            break
```

### Performance Tests
```python
def test_pattern_matching_performance():
    """Ensure pattern matching meets performance requirements"""
    tool_call = ToolCall(tool="Edit", input={"file_path": "src/main.py"})
    patterns = ["Edit(src/**)"] * 1000  # 1000 identical patterns

    start_time = time.time()
    for pattern in patterns:
        matches_pattern(tool_call, pattern)
    end_time = time.time()

    # Should complete 1000 matches in under 100ms
    assert (end_time - start_time) < 0.1
```

## Future Enhancements

### Advanced Pattern Features
- **Conditional Patterns**: Patterns that depend on context (git branch, time, etc.)
- **Weighted Patterns**: Patterns with priority/weight for conflict resolution
- **Dynamic Patterns**: Patterns that can be modified at runtime

### Performance Improvements
- **Parallel Matching**: Concurrent evaluation of independent patterns
- **Pattern Compilation**: Pre-compile patterns for faster execution
- **Smart Indexing**: Index patterns by tool type for faster lookup

### Security Enhancements
- **Pattern Signatures**: Cryptographically signed patterns
- **Audit Integration**: Deep integration with audit logging
- **Threat Detection**: Pattern-based threat detection and blocking

The pattern matching engine provides a robust, secure, and performant foundation for claudeguard's security model while maintaining flexibility for future enhancements.
