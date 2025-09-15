"""
Anthropic Claude client implementation.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional

import anthropic
from anthropic import Anthropic
from anthropic.types import Message

from ..config import AnthropicConfig
from .models import ClaudeResponse, ClaudeMessage


logger = logging.getLogger(__name__)


class AnthropicClient:
    """
    Clean wrapper for Anthropic Claude API interactions.

    Provides a clean interface for agent communication with Claude,
    handling retries, error management, and response parsing.
    """

    def __init__(self, config: AnthropicConfig):
        self.config = config
        self.client = Anthropic(api_key=config.api_key)

    async def send_message(
        self,
        messages: List[ClaudeMessage],
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
    ) -> ClaudeResponse:
        """
        Send a message to Claude with retry logic.

        Args:
            messages: List of messages in the conversation
            system_prompt: Optional system prompt for context
            max_retries: Number of retry attempts

        Returns:
            ClaudeResponse: Parsed response from Claude

        Raises:
            anthropic.APIError: If API call fails after retries
        """
        for attempt in range(max_retries):
            try:
                # Convert our message format to Anthropic format
                anthropic_messages = [
                    {"role": msg.role, "content": msg.content} for msg in messages
                ]

                response = await asyncio.to_thread(
                    self._make_api_call, anthropic_messages, system_prompt
                )

                return ClaudeResponse(
                    content=response.content[0].text if response.content else "",
                    usage_tokens=response.usage.input_tokens
                    + response.usage.output_tokens,
                    model=response.model,
                    finish_reason=response.stop_reason,
                )

            except anthropic.APIError as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff

    def _make_api_call(
        self, messages: List[Dict[str, str]], system_prompt: Optional[str]
    ) -> Message:
        """Make the actual API call to Anthropic."""
        kwargs = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        return self.client.messages.create(**kwargs)

    def test_connection(self) -> bool:
        """
        Test the connection to Anthropic API.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello! This is a connection test. Please respond with 'Connection successful!'",
                    }
                ],
            )

            content = response.content[0].text if response.content else ""
            success = (
                "Connection successful" in content or "successful" in content.lower()
            )

            logger.info(f"API test response: {content}")
            return success

        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
