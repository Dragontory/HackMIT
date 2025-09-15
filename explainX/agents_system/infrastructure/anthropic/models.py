"""
Data models for Anthropic Claude interactions.
"""

from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class ClaudeMessage:
    """Represents a message in a conversation with Claude."""

    role: Literal["user", "assistant"]
    content: str


@dataclass
class ClaudeResponse:
    """Represents a response from Claude."""

    content: str
    usage_tokens: int
    model: str
    finish_reason: Optional[str] = None
