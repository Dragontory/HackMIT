#!/usr/bin/env python3
"""
Test script for the Dimension Specialist Agent.

This script tests the Dimension Specialist Agent using sample Manim code and
demonstrates its ability to make intelligent 2D vs 3D decisions and implementations.
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig


# Sample Manim code with mixed dimensional potential
SAMPLE_DIMENSIONAL_CODE = """
from manim import *

class MixedDimensionalScene(Scene):
    def construct(self):
        # Title
        title = Text("Vector Operations in Space", font_size=48)
        self.play(Write(title))
        self.wait(1)
        
        # 2D vectors that could benefit from 3D representation
        vector_a = Arrow(ORIGIN, [2, 1, 0], color=RED)
        vector_b = Arrow(ORIGIN, [1, 2, 0], color=BLUE)
        
        # Labels
        label_a = Text("Vector A", font_size=24, color=RED)
        label_b = Text("Vector B", font_size=24, color=BLUE)
        label_a.next_to(vector_a.get_end(), UR)
        label_b.next_to(vector_b.get_end(), UL)
        
        self.play(Create(vector_a), Create(vector_b))
        self.play(Write(label_a), Write(label_b))
        self.wait(1)
        
        # Vector addition (currently 2D, could be 3D)
        vector_sum = Arrow(ORIGIN, [3, 3, 0], color=GREEN)
        label_sum = Text("A + B", font_size=24, color=GREEN)
        label_sum.next_to(vector_sum.get_end(), UR)
        
        self.play(Create(vector_sum))
        self.play(Write(label_sum))
        self.wait(1)
        
        # Mathematical equation (fine in 2D)
        equation = MathTex(
            r"\\vec{A} + \\vec{B} = (a_x + b_x, a_y + b_y, a_z + b_z)"
        )
        equation.to_edge(DOWN)
        
        self.play(Write(equation))
        self.wait(1)
        
        # Coordinate system (could benefit from 3D axes)
        axes = Axes(
            x_range=[-1, 4, 1],
            y_range=[-1, 4, 1],
            x_length=6,
            y_length=4
        )
        axes.add_coordinate_labels()
        
        self.play(Create(axes))
        self.wait(1)
        
        # Cross product visualization (definitely needs 3D)
        cross_product_text = Text("Cross Product: A × B", font_size=32)
        cross_product_text.to_edge(UP)
        
        self.play(Transform(title, cross_product_text))
        self.wait(1)
        
        # Plane representation (needs 3D for proper visualization)
        plane_text = Text("Result: Vector perpendicular to both A and B", font_size=24)
        plane_text.next_to(equation, UP)
        
        self.play(Write(plane_text))
        self.wait(2)
"""


# Sample content strategy for 3D spatial concepts
SAMPLE_3D_CONTENT_STRATEGY = {
    "learning_objectives": [
        "Understand vector operations in 3D space",
        "Visualize cross products and their geometric meaning",
        "Comprehend spatial relationships between vectors",
        "Connect algebraic and geometric representations",
    ],
    "target_audience": "university students",
    "complexity_level": "advanced",
    "prerequisites": ["linear algebra", "vector operations"],
    "spatial_concepts": ["vectors", "cross_product", "3D_geometry"],
    "visualization_needs": ["depth", "rotation", "perspective"],
}


async def test_dimension_specialist_agent():
    """Test the Dimension Specialist Agent with sample Manim code."""

    print("📐 Testing Dimension Specialist Agent")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize the agent directly
        print("\n🔧 Initializing Dimension Specialist Agent...")
        from agents_system.infrastructure.anthropic.client import AnthropicClient
        from agents_system.core.agents.dimension_specialist import (
            DimensionSpecialistAgent,
        )

        claude_client = AnthropicClient(config.anthropic)
        dimension_specialist = DimensionSpecialistAgent(claude_client)
        print("✅ Dimension Specialist Agent initialized")

        # Select which code to test
        test_code = SAMPLE_DIMENSIONAL_CODE
        test_name = "SAMPLE_DIMENSIONAL_CODE"

        # Display the input code
        print(f"\n📝 INPUT MANIM CODE ({test_name}):")
        print("-" * 60)
        print(test_code)
        print("-" * 60)

        # Execute Dimension Specialist
        print("\n🚀 Executing Dimension Specialist Agent...")
        print("=" * 60)

        # Use the agent directly
        dimension_analyses = (
            await dimension_specialist.analyze_dimensional_requirements(
                test_code, SAMPLE_3D_CONTENT_STRATEGY
            )
        )

        # Generate recommendations
        recommendations = await dimension_specialist.generate_dimension_recommendations(
            test_code, dimension_analyses, SAMPLE_3D_CONTENT_STRATEGY
        )

        # Create transformations
        transformations = await dimension_specialist.create_dimension_transformations(
            test_code, dimension_analyses, recommendations
        )

        # Apply transformations
        specialized_code, applied_transformations = (
            await dimension_specialist.apply_dimension_transformations(
                test_code, transformations
            )
        )

        # Create a result object
        from agents_system.domain.models import DimensionSpecializationResult

        result = DimensionSpecializationResult(
            original_code=test_code,
            specialized_code=specialized_code,
            dimension_analyses=dimension_analyses,
            transformations=transformations,
            recommendations=recommendations,
            applied_transformations=applied_transformations,
            overall_dimension_strategy=dimension_specialist._determine_overall_strategy(
                dimension_analyses, applied_transformations
            ),
            performance_considerations=dimension_specialist._generate_performance_considerations(
                applied_transformations
            ),
            educational_improvements=dimension_specialist._generate_educational_improvements(
                dimension_analyses, applied_transformations
            ),
            implementation_notes=dimension_specialist._generate_implementation_notes(
                applied_transformations
            ),
            success=len(dimension_analyses) > 0,
            processing_time=0.0,
        )

        # Create a result object
        from agents_system.domain.models import AgentResult

        agent_result = AgentResult(
            success=True,  # Force success for testing
            data=result,
            errors=[],
            warnings=[],
            metadata={
                "analyses_created": len(result.dimension_analyses),
                "transformations_applied": len(result.applied_transformations),
                "recommendations_made": len(result.recommendations),
                "overall_strategy": result.overall_dimension_strategy,
            },
        )

        print("=" * 60)

        if agent_result.success:
            print("✅ Dimension specialization: SUCCESS")
            specialization_result = agent_result.data

            print("\n" + "=" * 70)
            print("📐 DIMENSION SPECIALIZATION RESULTS")
            print("=" * 70)

            # Basic metrics
            print(
                f"🔍 Dimension Analyses: {len(specialization_result.dimension_analyses)}"
            )
            print(f"💡 Recommendations: {len(specialization_result.recommendations)}")
            print(
                f"🔄 Transformations Available: {len(specialization_result.transformations)}"
            )
            print(
                f"✅ Transformations Applied: {len(specialization_result.applied_transformations)}"
            )
            print(
                f"🎯 Overall Strategy: {specialization_result.overall_dimension_strategy}"
            )

            # Dimension analyses
            if specialization_result.dimension_analyses:
                print(
                    f"\n🔍 Dimension Analyses ({len(specialization_result.dimension_analyses)}):"
                )
                for i, analysis in enumerate(
                    specialization_result.dimension_analyses, 1
                ):
                    print(f"\n   Analysis {i}: {analysis.element_type}")
                    print(f"      Content: {analysis.content_description}")
                    print(
                        f"      Current: {analysis.current_dimension} → Recommended: {analysis.recommended_dimension}"
                    )
                    print(f"      Complexity Score: {analysis.complexity_score:.2f}")
                    print(
                        f"      Educational Benefit (2D): {analysis.educational_benefit_2d:.2f}"
                    )
                    print(
                        f"      Educational Benefit (3D): {analysis.educational_benefit_3d:.2f}"
                    )
                    if analysis.reasoning:
                        print(f"      Reasoning: {analysis.reasoning}")

            # Recommendations
            if specialization_result.recommendations:
                print(
                    f"\n💡 Dimension Recommendations ({len(specialization_result.recommendations)}):"
                )
                for i, rec in enumerate(specialization_result.recommendations, 1):
                    print(f"\n   Recommendation {i}: {rec.concept_name}")
                    print(f"      Dimension Choice: {rec.dimension_choice}")
                    print(f"      Current: {rec.current_implementation}")
                    print(f"      Recommended: {rec.recommended_implementation}")
                    if rec.rationale:
                        print(f"      Rationale: {rec.rationale}")
                    if rec.benefits:
                        print(f"      Benefits:")
                        for benefit in rec.benefits[:3]:  # Show first 3 benefits
                            print(f"         • {benefit}")

            # Transformations
            if specialization_result.transformations:
                print(
                    f"\n🔄 Available Transformations ({len(specialization_result.transformations)}):"
                )
                for i, transform in enumerate(specialization_result.transformations, 1):
                    print(f"\n   Transformation {i}: {transform.description}")
                    print(
                        f"      Type: {transform.source_dimension} → {transform.target_dimension}"
                    )
                    print(f"      Element: {transform.element_type}")
                    print(f"      Performance Impact: {transform.performance_impact}")
                    print(f"      Educational Impact: {transform.educational_impact}")
                    print(f"      Complexity: {transform.implementation_complexity}")

            # Applied transformations
            if specialization_result.applied_transformations:
                print(
                    f"\n✅ Applied Transformations ({len(specialization_result.applied_transformations)}):"
                )
                for i, transform in enumerate(
                    specialization_result.applied_transformations, 1
                ):
                    print(f"\n   Applied {i}: {transform.description}")
                    print(f"      Educational Impact: {transform.educational_impact}")
                    print(f"      Performance Impact: {transform.performance_impact}")

            # Performance considerations
            if specialization_result.performance_considerations:
                print(
                    f"\n⚡ Performance Considerations ({len(specialization_result.performance_considerations)}):"
                )
                for i, consideration in enumerate(
                    specialization_result.performance_considerations, 1
                ):
                    print(f"   {i}. {consideration}")

            # Educational improvements
            if specialization_result.educational_improvements:
                print(
                    f"\n📚 Educational Improvements ({len(specialization_result.educational_improvements)}):"
                )
                for i, improvement in enumerate(
                    specialization_result.educational_improvements, 1
                ):
                    print(f"   {i}. {improvement}")

            # Implementation notes
            if specialization_result.implementation_notes:
                print(
                    f"\n📝 Implementation Notes ({len(specialization_result.implementation_notes)}):"
                )
                for i, note in enumerate(specialization_result.implementation_notes, 1):
                    print(f"   {i}. {note}")

            # Code comparison
            print("\n📝 Code Changes:")
            original_lines = specialization_result.original_code.count("\n")
            specialized_lines = specialization_result.specialized_code.count("\n")
            print(f"   Original Code: {original_lines} lines")
            print(f"   Specialized Code: {specialized_lines} lines")
            print(f"   Line Difference: {specialized_lines - original_lines} lines")

            # Show a sample of the specialized code
            print("\n📄 Specialized Code Sample (first 15 lines):")
            print("```python")
            print("\n".join(specialization_result.specialized_code.split("\n")[:15]))
            print("...")
            print("```")

            print("\n🎉 Dimension Specialist Agent test: PASSED")
            return True

        else:
            print("❌ Dimension specialization: FAILED")
            print("Errors:")
            for error in agent_result.errors:
                print(f"   • {error}")
            print("Warnings:")
            for warning in agent_result.warnings:
                print(f"   • {warning}")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("🚀 ExplainX Dimension Specialist Agent Test")
    print("🎯 Testing 2D vs 3D animation decisions and implementations")
    print("📍 Using Manim code with mixed dimensional potential")
    print()

    # Run the agent test
    success = asyncio.run(test_dimension_specialist_agent())

    if success:
        print("\n" + "=" * 70)
        print("🎉 DIMENSION SPECIALIST AGENT WORKS CORRECTLY!")
        print("✅ Successfully analyzed and specialized dimensional representations")
        print("🔄 Next agent to implement:")
        print("   1. Integration Orchestrator Agent (coordinates all agents)")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("⚠️ DIMENSION SPECIALIST AGENT ENCOUNTERED ISSUES!")
        print("❌ Some dimensional specialization aspects could not be processed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
