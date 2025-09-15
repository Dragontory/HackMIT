"""
Configuration management for the agent system.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class AnthropicConfig:
    """Configuration for Anthropic Claude API."""

    api_key: str
    model: str = "claude-3-7-sonnet-20250219"
    max_tokens: int = 8000
    temperature: float = 0.1


@dataclass
class AgentConfig:
    """Main configuration for the agent system."""

    anthropic: AnthropicConfig
    debug: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create configuration from environment variables."""
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )

        return cls(
            anthropic=AnthropicConfig(
                api_key=anthropic_api_key,
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219"),
                max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "8000")),
                temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.1")),
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
