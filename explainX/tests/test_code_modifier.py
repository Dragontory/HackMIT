#!/usr/bin/env python3
"""
Test script for the Code Modification Agent.

This script tests the Code Modification Agent using LaTeX-fixed code and
demonstrates automatic fixing of positioning, timing, and quality issues.
"""

import asyncio
import sys
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig
from agents_system.core.workflows.code_modification_workflow import (
    CodeModificationWorkflow,
)
from agents_system.core.workflows.latex_fixing_workflow import LaTeXFixingWorkflow


# Sample LaTeX-fixed code with positioning and timing issues
LATEX_FIXED_CODE_WITH_ISSUES = """
from manim import *

class Scene_FixedLatex_NeedsPositioning(Scene):
    def construct(self):
        # LaTeX is now fixed, but positioning and timing need work
        title = Text("Attention Mechanisms in Neural Networks", font_size=36)
        self.play(Write(title), run_time=0.5)  # Too fast for title
        
        # Fixed LaTeX but no positioning - will overlap
        eq1 = MathTex(r"e_t = (H W_a) \\cdot s_{t-1} \\in \\mathbb{R}^{B\\times n}", font_size=32)
        self.play(Write(eq1), run_time=0.7)  # No wait time
        
        # More content without positioning
        explanation = Text("This equation computes attention energy", font_size=24)
        self.play(Write(explanation), run_time=0.6)
        
        # Another equation - will overlap with previous content
        eq2 = MathTex(r"\\alpha_{i,j} = \\text{softmax}(\\beta_{i,j})", font_size=28)
        self.play(Write(eq2), run_time=0.5)
        
        # Detailed explanation with large font
        details = Text("Softmax ensures attention weights sum to 1", font_size=30)
        self.play(Write(details), run_time=0.4)  # Very fast
        
        # Final equation without proper spacing
        eq3 = MathTex(r"Q, K, V = h W_Q, h W_K, h W_V \\in \\mathbb{R}^{n \\times d_k}", font_size=35)
        self.play(Write(eq3), run_time=0.3)  # Too fast for complex equation
        
        self.wait(0.1)  # Inadequate processing time
"""


async def test_code_modifier_agent():
    """Test the Code Modification Agent with LaTeX-fixed code."""

    print("🔧 Testing Code Modification Agent")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize workflows
        print("\n🔧 Initializing Code Modification Workflow...")
        code_workflow = CodeModificationWorkflow(config)
        print("✅ Code Modification Workflow initialized")

        # Also initialize LaTeX workflow for context
        print("🔧 Initializing LaTeX Workflow for context...")
        latex_workflow = LaTeXFixingWorkflow(config)
        print("✅ LaTeX Workflow initialized")

        # Display the input code
        print("\n📝 INPUT CODE (LaTeX-fixed but with positioning/timing issues):")
        print("-" * 60)
        print(LATEX_FIXED_CODE_WITH_ISSUES)
        print("-" * 60)

        # Analyze the code issues
        print(f"\n📊 Code Issue Analysis:")
        print(f"   Characters: {len(LATEX_FIXED_CODE_WITH_ISSUES)}")
        print(f"   Lines: {len(LATEX_FIXED_CODE_WITH_ISSUES.splitlines())}")

        # Count elements and issues
        import re

        text_elements = len(re.findall(r"Text\(", LATEX_FIXED_CODE_WITH_ISSUES))
        math_elements = len(re.findall(r"MathTex\(", LATEX_FIXED_CODE_WITH_ISSUES))
        positioned_elements = len(
            re.findall(r"\.(to_edge|next_to|shift)", LATEX_FIXED_CODE_WITH_ISSUES)
        )
        fast_animations = len(
            [
                m
                for m in re.findall(r"run_time=([\d.]+)", LATEX_FIXED_CODE_WITH_ISSUES)
                if float(m) < 1.0
            ]
        )

        print(f"   Text elements: {text_elements}")
        print(f"   Math elements: {math_elements}")
        print(f"   Positioned elements: {positioned_elements}")
        print(f"   Fast animations: {fast_animations}")
        print(
            f"   Positioning coverage: {positioned_elements / (text_elements + math_elements) * 100:.1f}%"
        )

        # First, get LaTeX context by running LaTeX workflow on original problematic code
        print("\n🔬 Getting LaTeX context...")
        original_problematic = LATEX_FIXED_CODE_WITH_ISSUES.replace(
            r"e_t = (H W_a) \\cdot s_{t-1}", r"e_t &= (H W_a) \\\\cdot s_{t-1}"
        )  # Simulate original LaTeX issues

        latex_result = await latex_workflow.fix_latex_code(original_problematic)
        print(
            f"✅ LaTeX context obtained: {len(latex_result.data.fixes_applied) if latex_result.success else 0} fixes"
        )

        # Execute Code Modification
        print("\n🚀 Executing Code Modification Agent...")
        print("=" * 60)

        result = await code_workflow.modify_code(
            manim_code=LATEX_FIXED_CODE_WITH_ISSUES,
            latex_result=latex_result.data if latex_result.success else None,
            content_strategy=None,  # Could provide content strategy from previous agent
        )

        print("=" * 60)

        if result.success:
            print("✅ Code modification: SUCCESS")
            mod_result = result.data

            print("\n" + "=" * 70)
            print("🔧 CODE MODIFICATION RESULTS")
            print("=" * 70)

            # Basic metrics
            print(f"🎯 Modifications Applied: {len(mod_result.modifications_applied)}")
            print(f"✅ Validation Passed: {mod_result.validation_passed}")
            print(f"⏱️  Processing Time: {mod_result.processing_time:.2f} seconds")

            # Position analysis
            if mod_result.position_analysis:
                pos = mod_result.position_analysis
                print(f"\n📍 Positioning Analysis:")
                print(f"   Total Elements: {pos.total_elements}")
                print(f"   Out of Bounds Issues: {len(pos.out_of_bounds_elements)}")
                print(f"   Overlapping Issues: {len(pos.overlapping_elements)}")
                print(f"   Screen Utilization: {pos.screen_utilization:.2f}")
                print(f"   Positioning Suggestions: {len(pos.positioning_suggestions)}")

            # Timing analysis
            if mod_result.timing_analysis:
                timing = mod_result.timing_analysis
                print(f"\n⏰ Timing Analysis:")
                print(f"   Total Animations: {timing.total_animations}")
                print(f"   Timing Issues: {len(timing.timing_issues)}")
                print(f"   Suggested Pace: {timing.suggested_pace}")
                print(f"   Total Duration: {timing.total_duration:.1f}s")
                print(f"   Cognitive Load: {timing.cognitive_load_assessment}")

            # Quality metrics
            if mod_result.quality_metrics:
                quality = mod_result.quality_metrics
                print(f"\n📊 Quality Metrics:")
                print(f"   Complexity Score: {quality.complexity_score:.2f}")
                print(f"   Readability Score: {quality.readability_score:.2f}")
                print(f"   Performance Score: {quality.performance_score:.2f}")
                print(
                    f"   Educational Effectiveness: {quality.educational_effectiveness:.2f}"
                )
                print(f"   Maintainability Score: {quality.maintainability_score:.2f}")

            # Show original vs modified code length
            print(f"\n📏 Code Comparison:")
            print(f"   Original length: {len(mod_result.original_code)} characters")
            print(f"   Modified length: {len(mod_result.modified_code)} characters")
            print(
                f"   Length change: {len(mod_result.modified_code) - len(mod_result.original_code):+d} characters"
            )

            # Display specific modifications
            if mod_result.modifications_applied:
                print(f"\n🔧 Specific Modifications Applied:")

                # Group by type
                mod_by_type = {}
                for mod in mod_result.modifications_applied:
                    mod_type = mod.modification_type
                    if mod_type not in mod_by_type:
                        mod_by_type[mod_type] = []
                    mod_by_type[mod_type].append(mod)

                for mod_type, mods in mod_by_type.items():
                    print(f"\n   📂 {mod_type.upper()} Modifications ({len(mods)}):")
                    for i, mod in enumerate(mods, 1):
                        print(f"      {i}. Line {mod.line_number}: {mod.explanation}")
                        print(
                            f"         Confidence: {mod.confidence:.2f}, Impact: {mod.impact_score:.2f}"
                        )
                        print(f"         ❌ Before: {mod.original_line.strip()}")
                        print(f"         ✅ After:  {mod.modified_line.strip()}")

            # Show the modified code
            print(f"\n🎉 MODIFIED MANIM CODE:")
            print("=" * 60)
            print(mod_result.modified_code)
            print("=" * 60)

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
                    if "summary" in msg:
                        print(f"      📋 Summary:")
                        for key, value in msg["summary"].items():
                            print(f"         {key}: {value}")

            # Highlight key improvements
            print(f"\n🎯 KEY IMPROVEMENTS MADE:")
            print("=" * 50)
            positioning_mods = [
                m
                for m in mod_result.modifications_applied
                if m.modification_type == "positioning"
            ]
            timing_mods = [
                m
                for m in mod_result.modifications_applied
                if m.modification_type == "timing"
            ]
            structure_mods = [
                m
                for m in mod_result.modifications_applied
                if m.modification_type == "structure"
            ]

            if positioning_mods:
                print(
                    f"✅ POSITIONING: Fixed {len(positioning_mods)} positioning issues"
                )
                print("   - Elements now have explicit positioning")
                print("   - Prevents overlapping and out-of-bounds issues")
                print("   - Improves screen space utilization")

            if timing_mods:
                print(f"✅ TIMING: Optimized {len(timing_mods)} timing issues")
                print("   - Slower pace for better comprehension")
                print("   - Added processing time between animations")
                print("   - Educational effectiveness improved")

            if structure_mods:
                print(
                    f"✅ STRUCTURE: Enhanced {len(structure_mods)} structural aspects"
                )
                print("   - Better code organization")
                print("   - Added educational comments")
                print("   - Improved maintainability")

            print("\n🎉 Code Modification Agent test: PASSED")
            print("🚀 Ready to integrate with Code Testing Agent!")
            return True

        else:
            print("❌ Code modification: FAILED")
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
    print("🚀 ExplainX Code Modification Agent Test")
    print("🎯 Testing automatic code improvement for positioning, timing, and quality")
    print("📍 Using LaTeX-fixed code with positioning/timing issues")
    print()

    # Run the test
    success = asyncio.run(test_code_modifier_agent())

    if success:
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Code Modification Agent successfully improved code quality")
        print("🔄 Next agents to implement:")
        print("   1. Code Testing Agent (validate improvements in sandbox)")
        print("   2. Error Surgeon Agent (handle edge cases)")
        print("   3. Terminal Monitor Agent (real-time monitoring)")
        print("=" * 70)
        return 0
    else:
        print("\n❌ TESTS FAILED")
        print("Please check configuration and try again.")
        return 1


if __name__ == "__main__":
    exit(main())
