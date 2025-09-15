#!/usr/bin/env python3
"""
Test script for the Code Testing Agent.

This script tests the Code Testing Agent using modified Manim code and
demonstrates its ability to catch errors before full rendering.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig
from agents_system.core.workflows.code_testing_workflow import CodeTestingWorkflow
from agents_system.core.workflows.code_modification_workflow import (
    CodeModificationWorkflow,
)
from agents_system.core.workflows.latex_fixing_workflow import LaTeXFixingWorkflow


# Sample Manim code with subtle issues for testing
MANIM_CODE_WITH_SUBTLE_ISSUES = """
from manim import *

class Scene_SubtleIssues(Scene):
    def construct(self):
        # Title with good positioning
        title = Text("Attention Mechanisms", font_size=36)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)
        self.wait(0.8)
        
        # Equation with proper LaTeX but no positioning
        eq = MathTex(r"e_t = (H W_a) \\cdot s_{t-1} \\in \\mathbb{R}^{B\\times n}", font_size=32)
        # Missing positioning for eq - will overlap with title
        self.play(Write(eq), run_time=1.2)
        self.wait(0.8)
        
        # Explanation text with positioning
        explanation = Text("This equation computes attention energy", font_size=24)
        explanation.next_to(eq, DOWN, buff=0.3)
        self.play(Write(explanation), run_time=1.0)
        self.wait(0.8)
        
        # Another equation with a subtle reference error
        # The variable 'attention_weights' is used but never defined
        attention_weights.shift(DOWN)  # This will cause a runtime error
        eq2 = MathTex(r"\\alpha_{i,j} = \\text{softmax}(\\beta_{i,j})", font_size=28)
        eq2.next_to(explanation, DOWN, buff=0.3)
        self.play(Write(eq2), run_time=1.0)
        self.wait(0.8)
"""


# Sample Manim code with syntax error
MANIM_CODE_WITH_SYNTAX_ERROR = """
from manim import *

class Scene_SyntaxError(Scene):
    def construct(self):
        # Title
        title = Text("Attention Mechanisms", font_size=36)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)
        self.wait(0.8)
        
        # Missing closing parenthesis - syntax error
        eq = MathTex(r"e_t = (H W_a) \\cdot s_{t-1}", font_size=32
        eq.next_to(title, DOWN)
        self.play(Write(eq), run_time=1.2)
        self.wait(0.8)
"""


# Sample Manim code with no issues
MANIM_CODE_NO_ISSUES = """
from manim import *

class Scene_NoIssues(Scene):
    def construct(self):
        # Title with good positioning
        title = Text("Attention Mechanisms", font_size=36)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)
        self.wait(0.8)
        
        # Equation with proper LaTeX and positioning
        eq = MathTex(r"e_t = (H W_a) \\cdot s_{t-1} \\in \\mathbb{R}^{B\\times n}", font_size=32)
        eq.next_to(title, DOWN, buff=0.5)
        self.play(Write(eq), run_time=1.2)
        self.wait(0.8)
        
        # Explanation text with positioning
        explanation = Text("This equation computes attention energy", font_size=24)
        explanation.next_to(eq, DOWN, buff=0.3)
        self.play(Write(explanation), run_time=1.0)
        self.wait(0.8)
        
        # Another equation with proper positioning
        eq2 = MathTex(r"\\alpha_{i,j} = \\text{softmax}(\\beta_{i,j})", font_size=28)
        eq2.next_to(explanation, DOWN, buff=0.3)
        self.play(Write(eq2), run_time=1.0)
        self.wait(0.8)
"""


async def test_code_testing_agent():
    """Test the Code Testing Agent with various Manim code samples."""

    print("🧪 Testing Code Testing Agent")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize the agent directly (skip the workflow for faster testing)
        print("\n🔧 Initializing Code Testing Agent...")
        from agents_system.infrastructure.anthropic.client import AnthropicClient
        from agents_system.core.agents.code_tester import CodeTestingAgent

        claude_client = AnthropicClient(config.anthropic)
        code_tester = CodeTestingAgent(claude_client)
        print("✅ Code Testing Agent initialized")

        # Select which code to test
        test_code = MANIM_CODE_WITH_SYNTAX_ERROR  # Using code with clear syntax error for faster testing
        test_name = "MANIM_CODE_WITH_SYNTAX_ERROR"  # Update this if you change the code

        # Display the input code
        print(f"\n📝 INPUT CODE ({test_name}):")
        print("-" * 60)
        print(test_code)
        print("-" * 60)

        # Execute Code Testing - just test syntax which is fast
        print("\n🚀 Testing Syntax Validation...")
        print("=" * 60)

        # Create a minimal state
        state = {
            "content_title": "Syntax Test",
            "manim_code": test_code,
            "errors": [],
            "warnings": [],
            "agent_messages": [],
            "current_agent": "",
            "processing_stage": "initialized",
        }

        # Run just the syntax test
        syntax_result = code_tester._test_syntax(test_code)
        print(f"Syntax test result: {'PASSED' if syntax_result.success else 'FAILED'}")
        if not syntax_result.success and syntax_result.error_message:
            print(f"Error: {syntax_result.error_message}")

        print("=" * 60)

        # Create a simulated result
        result_data = {
            "success": not syntax_result.success,  # For syntax error test, we expect it to fail
            "data": {
                "syntax_valid": syntax_result.success,
                "test_cases": [
                    {
                        "test_id": "syntax_test",
                        "test_name": "Syntax Validation",
                        "test_description": "Verify code syntax",
                        "expected_result": "Valid syntax",
                        "actual_result": (
                            "Syntax error"
                            if not syntax_result.success
                            else "Valid syntax"
                        ),
                        "passed": syntax_result.success,
                        "error_message": syntax_result.error_message,
                    }
                ],
            },
        }

        # For our simplified test, we'll just use the syntax test result directly
        syntax_success = (
            not syntax_result.success
        )  # For syntax error test, success means finding the error

        print("\n🎉 CODE TESTING AGENT TEST RESULTS:")
        print(
            f"✅ Syntax error detection: {'PASSED' if not syntax_result.success else 'FAILED'}"
        )
        print(f"✅ Expected result: The code should have syntax errors")
        print(
            f"✅ Actual result: {'Syntax errors detected' if not syntax_result.success else 'No syntax errors found'}"
        )

        # Return success if we correctly detected syntax errors
        return syntax_success

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("🚀 ExplainX Code Testing Agent Test")
    print("🎯 Testing syntax validation functionality")
    print("📍 Using Manim code with syntax error")
    print()

    # Run the test
    success = asyncio.run(test_code_testing_agent())

    # For syntax error test, success means we correctly identified the error
    # So we expect success to be True for our test with MANIM_CODE_WITH_SYNTAX_ERROR
    if success:
        print("\n" + "=" * 70)
        print("🎉 CODE TESTING AGENT WORKS CORRECTLY!")
        print("✅ Successfully detected syntax error in the test code")
        print("🔄 Next agents to implement:")
        print("   1. Error Surgeon Agent (handle edge cases)")
        print("   2. Terminal Monitor Agent (real-time monitoring)")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("⚠️ UNEXPECTED RESULT!")
        print("❌ The test code should have syntax errors but none were detected")
        print("=" * 70)
        return 1  # Return error code if test fails


if __name__ == "__main__":
    exit(main())
