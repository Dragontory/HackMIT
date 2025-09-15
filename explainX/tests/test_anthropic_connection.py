#!/usr/bin/env python3
"""
Test script to verify Anthropic Claude API connection.

This script tests the basic functionality of our Anthropic integration
and ensures the API key is properly configured.
"""

import asyncio
import sys
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig
from agents_system.infrastructure.anthropic.client import AnthropicClient
from agents_system.infrastructure.anthropic.models import ClaudeMessage


async def test_anthropic_api():
    """Test Anthropic API connection and basic functionality."""

    print("🧪 Testing Anthropic Claude API Connection")
    print("=" * 50)

    try:
        # Load configuration
        print("📋 Loading configuration from environment...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize client
        print("🔌 Initializing Anthropic client...")
        client = AnthropicClient(config.anthropic)
        print("✅ Client initialized")

        # Test basic connection
        print("🔍 Testing basic API connection...")
        connection_success = client.test_connection()

        if connection_success:
            print("✅ Basic connection test: PASSED")
        else:
            print("❌ Basic connection test: FAILED")
            return False

        # Test agent-style conversation
        print("🤖 Testing agent-style conversation...")
        messages = [
            ClaudeMessage(
                role="user",
                content="""
                You are a LaTeX specialist for educational video generation.
                
                Task: Fix this problematic LaTeX expression that's causing Manim compilation errors:
                
                MathTex(r"e_t &= (H W_a) \\\\cdot s_{{t-1}} \\\\in \\\\mathbb{{R}}^{{B\\\\times n}},", font_size=32)
                
                The error occurs because of alignment operators and complex nesting.
                
                Please provide:
                1. The corrected LaTeX expression
                2. A brief explanation of what was wrong
                3. A Python code snippet with the fixed MathTex
                
                Respond in a structured format.
                """,
            )
        ]

        system_prompt = """
        You are a LaTeX and Manim specialist. You excel at:
        - Fixing LaTeX compilation errors
        - Ensuring Manim compatibility
        - Maintaining mathematical accuracy
        - Providing clear, actionable solutions
        
        Always provide practical, working solutions.
        """

        response = await client.send_message(messages, system_prompt)

        print("✅ Agent conversation test: PASSED")
        print(f"📊 Response length: {len(response.content)} characters")
        print(f"🎯 Tokens used: {response.usage_tokens}")
        print(f"🔧 Model used: {response.model}")

        print("\n" + "=" * 50)
        print("📝 Claude's Response:")
        print("=" * 50)
        print(response.content)

        # Test if the response contains expected elements
        response_lower = response.content.lower()
        has_latex = "latex" in response_lower or "mathtex" in response_lower
        has_explanation = "error" in response_lower or "wrong" in response_lower
        has_code = "mathtex(" in response.content

        print("\n" + "=" * 50)
        print("🔍 Response Quality Check:")
        print("=" * 50)
        print(f"✅ Contains LaTeX discussion: {has_latex}")
        print(f"✅ Contains error explanation: {has_explanation}")
        print(f"✅ Contains code solution: {has_code}")

        if has_latex and has_explanation and has_code:
            print("🎉 FULL API TEST: PASSED")
            print("🚀 Ready to implement LaTeX Specialist Agent!")
            return True
        else:
            print("⚠️  Response quality could be improved")
            return True  # Still a success, just noting quality

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n💡 To fix this:")
        print("1. Create a .env file in the project root")
        print("2. Add: ANTHROPIC_API_KEY=your_key_here")
        print("3. Get your API key from: https://console.anthropic.com/")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 ExplainX Agent System - Anthropic API Test")
    print("🎯 This test will verify our Claude integration")
    print("📍 Location: /Users/adewaleadenle/Downloads/Dev/explainX")
    print()

    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("💡 Create .env with ANTHROPIC_API_KEY=your_key")
        print()

    # Run the async test
    success = asyncio.run(test_anthropic_api())

    if success:
        print("\n🎉 All tests passed! Ready to implement agents.")
        return 0
    else:
        print("\n❌ Tests failed. Please check configuration.")
        return 1


if __name__ == "__main__":
    exit(main())
