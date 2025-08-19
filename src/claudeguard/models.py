"""Immutable data models for claudeguard pattern matching system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ToolName = str

Action = Literal["allow", "deny", "ask"]


@dataclass(frozen=True)
class ToolInput:
    data: dict[str, Any]


@dataclass(frozen=True)
class ToolPattern:
    pattern: str
    action: Action


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    pattern_used: str | None = None
    resource_extracted: str | None = None
    debug_info: str | None = None


@dataclass(frozen=True)
class ToolCall:
    name: ToolName
    input: ToolInput


@dataclass(frozen=True)
class ProfileRule:
    pattern: str
    action: Action
    comment: str = ""


@dataclass(frozen=True)
class ProfileMetadata:
    name: str
    description: str = ""
    version: str = "1.0"
    created_by: str = "claudeguard"


@dataclass(frozen=True)
class Profile:
    metadata: ProfileMetadata
    rules: tuple[ProfileRule, ...]
