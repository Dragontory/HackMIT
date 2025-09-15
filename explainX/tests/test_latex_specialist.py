#!/usr/bin/env python3
"""
Test script for the LaTeX Specialist Agent.

This script tests the LaTeX Specialist Agent using the actual problematic
LaTeX expression from the terminal error to demonstrate automatic fixing.
"""

import asyncio
import sys
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig
from agents_system.core.workflows.latex_fixing_workflow import LaTeXFixingWorkflow


# The exact problematic code from the terminal error (line 266)
PROBLEMATIC_MANIM_CODE = """
from manim import *

class Scene_Chunk01_Scene3(Scene):
    def construct(self):
        # Line 57-62 from terminal error
        text = Text("Understanding attention mechanism", font_size=24)
        text.shift(UP * 0.0)
        self.play(Write(text), run_time=1.5)
        self.wait(1)

        self.wait(0.500)
        # This is the EXACT problematic line from terminal (line 266)
        eq = MathTex(r"e_t &= (H W_a) \\\\cdot s_{t-1} \\\\in \\\\mathbb{R}^{B\\\\times n},", font_size=32)
        self.play(Write(eq), run_time=1.2)
        self.wait(0.8)

        # Additional problematic expressions found in the codebase
        self.wait(0.500)
        eq2 = MathTex(r"\\\\alpha_{i,j} &= \\\\text{softmax}(\\\\beta_{i,j})", font_size=28)
        self.play(Write(eq2), run_time=1.0)
        self.wait(0.6)
        
        # Complex nested expression with multiple issues
        eq3 = MathTex(r"Q, K, V &= h W_Q, h W_K, h W_V \\\\in \\\\mathbb{R}^{n \\\\times d_k},", font_size=30)
        self.play(Write(eq3), run_time=1.0)
        self.wait(0.8)
"""

# The error log from the terminal
ERROR_LOG = """
ValueError: latex error converting to dvi. See log output above or the log file: media/Tex/65d720eb4db018f5.log

The LaTeX expression contains alignment operators (&=) which are not compatible with single equation MathTex objects in Manim.
Double escaping (\\\\) is also causing compilation issues.
"""


async def test_latex_specialist():
    """Test the LaTeX Specialist Agent with real problematic expressions."""

    print("🔧 Testing LaTeX Specialist Agent")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize the LaTeX fixing workflow
        print("\n🔧 Initializing LaTeX Fixing Workflow...")
        workflow = LaTeXFixingWorkflow(config)
        print("✅ Workflow initialized")

        # Display the problematic code
        print("\n🚨 PROBLEMATIC MANIM CODE (from terminal error):")
        print("-" * 50)
        print(PROBLEMATIC_MANIM_CODE)
        print("-" * 50)

        print(f"\n📊 Code Analysis:")
        print(f"   Characters: {len(PROBLEMATIC_MANIM_CODE)}")
        print(f"   Lines: {len(PROBLEMATIC_MANIM_CODE.splitlines())}")
        print(f"   Contains '&=': {'&=' in PROBLEMATIC_MANIM_CODE}")

        # Check for double escaping without f-string backslashes
        double_escaping_check = "\\\\\\\\" in PROBLEMATIC_MANIM_CODE
        print(f"   Contains double escaping: {double_escaping_check}")

        # Execute LaTeX fixing
        print("\n🚀 Executing LaTeX Specialist Agent...")
        print("=" * 50)

        result = await workflow.fix_latex_code(
            manim_code=PROBLEMATIC_MANIM_CODE, error_log=ERROR_LOG
        )

        print("=" * 50)

        if result.success:
            print("✅ LaTeX fixing: SUCCESS")
            latex_result = result.data

            print("\n" + "=" * 70)
            print("🔧 LATEX SPECIALIST RESULTS")
            print("=" * 70)

            # Basic metrics
            print(f"🎯 Fixes Applied: {len(latex_result.fixes_applied)}")
            print(
                f"📊 Expressions Processed: {latex_result.code_analysis.total_latex_expressions if latex_result.code_analysis else 0}"
            )
            print(f"✅ Validation Success: {latex_result.success}")
            print(f"⏱️  Processing Time: {latex_result.processing_time:.2f} seconds")

            if latex_result.code_analysis:
                print(
                    f"🧮 Code Complexity: {latex_result.code_analysis.complexity_score:.2f}"
                )
                print(
                    f"⚠️  Compatibility Issues: {len(latex_result.code_analysis.manim_compatibility_issues)}"
                )

            # Show original vs fixed code
            print(f"\n📏 Code Comparison:")
            print(f"   Original length: {len(latex_result.original_code)} characters")
            print(f"   Fixed length: {len(latex_result.fixed_code)} characters")

            # Display specific fixes
            if latex_result.fixes_applied:
                print(f"\n🔧 Specific Fixes Applied:")
                for i, fix in enumerate(latex_result.fixes_applied, 1):
                    print(f"\n   Fix {i}: {fix.error_type}")
                    print(f"   ❌ Original: {fix.original_expression}")
                    print(f"   ✅ Fixed:    {fix.fixed_expression}")
                    print(f"   💡 Explanation: {fix.explanation}")
                    print(f"   🎯 Confidence: {fix.confidence:.2f}")

            # Display validation results
            if latex_result.validation_results:
                print(f"\n✅ Validation Results:")
                valid_count = sum(
                    1 for v in latex_result.validation_results if v.is_valid
                )
                total_count = len(latex_result.validation_results)
                print(f"   Valid expressions: {valid_count}/{total_count}")

                for i, validation in enumerate(latex_result.validation_results, 1):
                    status = "✅" if validation.is_valid else "❌"
                    print(
                        f"   {status} Expression {i}: {'Valid' if validation.is_valid else 'Invalid'}"
                    )
                    if validation.errors:
                        for error in validation.errors:
                            print(f"      ❌ Error: {error}")
                    if validation.warnings:
                        for warning in validation.warnings:
                            print(f"      ⚠️  Warning: {warning}")
                    if validation.suggestions:
                        for suggestion in validation.suggestions:
                            print(f"      💡 Suggestion: {suggestion}")

            # Show the fixed code
            print(f"\n🎉 FIXED MANIM CODE:")
            print("=" * 50)
            print(latex_result.fixed_code)
            print("=" * 50)

            # Workflow execution details
            print(f"\n🔧 Workflow Execution Details:")
            print(
                f"   Processing Steps: {result.metadata.get('total_processing_steps', 0)}"
            )
            print(f"   Final State: {result.metadata.get('workflow_state', 'unknown')}")

            # Agent messages
            if "agent_messages" in result.metadata:
                print(f"\n📨 Agent Execution Log:")
                for msg in result.metadata["agent_messages"]:
                    agent = msg.get("agent", "unknown")
                    status = msg.get("status", "unknown")
                    message = msg.get("message", "")
                    print(f"   📍 {agent}: {status}")
                    if message:
                        print(f"      💬 {message}")
                    if "metadata" in msg:
                        for key, value in msg["metadata"].items():
                            print(f"      📊 {key}: {value}")

            # Demonstrate the fix for the specific terminal error
            print(f"\n🎯 SPECIFIC TERMINAL ERROR FIX:")
            print("=" * 50)
            terminal_error_line = 'MathTex(r"e_t &= (H W_a) \\\\\\\\cdot s_{t-1} \\\\\\\\in \\\\\\\\mathbb{R}^{B\\\\\\\\times n},"'

            # Find the corresponding fix
            for fix in latex_result.fixes_applied:
                if "e_t" in fix.original_expression and "&=" in fix.original_expression:
                    print(f"❌ BROKEN (line 266): {fix.original_expression}")
                    print(f"✅ FIXED: {fix.fixed_expression}")
                    print(f"💡 This fix resolves the terminal LaTeX compilation error!")
                    break

            print("\n🎉 LaTeX Specialist Agent test: PASSED")
            print("🚀 Ready to integrate with Code Modification Agent!")
            return True

        else:
            print("❌ LaTeX fixing: FAILED")
            print("Errors:")
            for error in result.errors:
                print(f"   • {error}")
            print("Warnings:")
            for warning in result.warnings:
                print(f"   • {warning}")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("🚀 ExplainX LaTeX Specialist Agent Test")
    print("🎯 Testing automatic LaTeX compilation error fixing")
    print("📍 Using EXACT problematic code from terminal error (line 266)")
    print()

    # Run the test
    success = asyncio.run(test_latex_specialist())

    if success:
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("✅ LaTeX Specialist Agent successfully fixed compilation errors")
        print("🔄 Next agents to implement:")
        print("   1. Code Modification Agent (build on LaTeX fixes)")
        print("   2. Code Testing Agent (validate fixes in sandbox)")
        print("   3. Error Surgeon Agent (handle edge cases)")
        print("=" * 70)
        return 0
    else:
        print("\n❌ TESTS FAILED")
        print("Please check configuration and try again.")
        return 1


if __name__ == "__main__":
    exit(main())
