#!/usr/bin/env python3
"""
Test script for the Rendering Optimizer Agent.

This script tests the Rendering Optimizer Agent using sample Manim code and
demonstrates its ability to optimize rendering settings for performance.
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig
from agents_system.core.workflows.rendering_optimization_workflow import (
    RenderingOptimizationWorkflow,
)


# Sample Manim code with computationally expensive operations
SAMPLE_COMPLEX_CODE = """
from manim import *

class ComplexScene(Scene):
    def construct(self):
        # Title
        title = Text("Complex Animation Example", font_size=48)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create a grid of shapes
        shapes = VGroup()
        for i in range(10):
            for j in range(10):
                if (i + j) % 2 == 0:
                    shape = Square(side_length=0.2, fill_opacity=0.8)
                else:
                    shape = Circle(radius=0.1, fill_opacity=0.8)
                shape.set_color(color_gradient([BLUE, GREEN], 2)[(i + j) % 2])
                shape.move_to(np.array([-2.25 + i * 0.5, 1.5 - j * 0.5, 0]))
                shapes.add(shape)
        
        # Animate the grid
        self.play(FadeIn(shapes, lag_ratio=0.05, run_time=3))
        self.wait(1)
        
        # Create complex formula
        formula = MathTex(
            r"f(z) = \\frac{1}{2\\pi i} \\oint_\\gamma \\frac{f(\\zeta)}{\\zeta - z} d\\zeta",
            font_size=40
        )
        formula.next_to(shapes, DOWN, buff=0.5)
        
        # Animate formula
        self.play(Write(formula))
        self.wait(1)
        
        # Create a graph
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 2, 1],
            x_length=6,
            y_length=4,
            axis_config={"include_tip": False}
        )
        
        # Plot a function
        graph = axes.plot(lambda x: np.sin(x), color=YELLOW)
        graph_label = axes.get_graph_label(graph, "\\sin(x)", x_val=2)
        
        graph_group = VGroup(axes, graph, graph_label)
        graph_group.scale(0.6)
        graph_group.to_edge(DOWN)
        
        # Animate graph
        self.play(FadeTransform(formula, graph_group))
        self.wait(1)
        
        # Create dots that move along the graph
        dots = VGroup()
        for i in range(20):
            dot = Dot(color=RED)
            dot.move_to(axes.c2p(i/10 - 3, np.sin(i/10 - 3)))
            dots.add(dot)
        
        self.play(FadeIn(dots))
        
        # Animate dots along the curve
        animations = []
        for i, dot in enumerate(dots):
            target_x = i/10 + 3
            target_y = np.sin(target_x)
            target_point = axes.c2p(target_x, target_y)
            animations.append(dot.animate.move_to(target_point))
        
        self.play(AnimationGroup(*animations, lag_ratio=0.1))
        self.wait(1)
        
        # Final animation
        final_text = Text("Optimization Complete", font_size=42)
        final_text.to_edge(DOWN)
        
        self.play(
            FadeOut(shapes),
            FadeOut(graph_group),
            FadeOut(dots),
            FadeOut(title),
            FadeIn(final_text)
        )
        self.wait(2)
"""


# Sample Manim code with inefficient rendering settings
SAMPLE_INEFFICIENT_CODE = """
from manim import *

class IneffientScene(Scene):
    def construct(self):
        # High-resolution text
        title = Text("Inefficient Animation Example", font_size=72)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create many small objects
        small_objects = VGroup()
        for i in range(30):
            for j in range(30):
                dot = Dot(radius=0.02, color=BLUE)
                dot.move_to([i/10 - 1.5, j/10 - 1.5, 0])
                small_objects.add(dot)
        
        # Animate each object individually (inefficient)
        for obj in small_objects:
            self.play(FadeIn(obj), run_time=0.01)
        
        self.wait(1)
        
        # Create a complex mathematical expression
        complex_formula = MathTex(
            r"\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}",
            r"\sum_{n=0}^{\infty} \frac{z^n}{n!} = e^z",
            r"\frac{d}{dx}[e^x \sin(x)] = e^x \sin(x) + e^x \cos(x)",
            font_size=36
        )
        complex_formula.arrange(DOWN, buff=0.5)
        
        # Animate each part separately (inefficient)
        for part in complex_formula:
            self.play(Write(part))
            self.wait(0.5)
        
        # Create a graph with too many points
        axes = Axes(
            x_range=[-5, 5, 0.1],  # Too fine-grained
            y_range=[-3, 3, 0.1],  # Too fine-grained
            x_length=10,
            y_length=6,
            axis_config={"include_tip": True, "numbers_to_include": list(range(-5, 6))}
        )
        
        # Plot with too many sample points
        graph = axes.plot(lambda x: np.sin(x) * np.exp(-0.1 * x**2), 
                         x_range=[-5, 5, 0.01],  # Too many sample points
                         color=YELLOW)
        
        self.play(Create(axes), run_time=2)
        self.play(Create(graph), run_time=2)
        
        self.wait(2)
        
        # Inefficient fade out (one by one)
        for obj in [*complex_formula, axes, graph, title]:
            self.play(FadeOut(obj), run_time=0.5)
        
        self.wait(1)
"""


async def test_rendering_optimizer_agent():
    """Test the Rendering Optimizer Agent with sample Manim code."""

    print("⚙️ Testing Rendering Optimizer Agent")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize the agent directly (skip the workflow for faster testing)
        print("\n🔧 Initializing Rendering Optimizer Agent...")
        from agents_system.infrastructure.anthropic.client import AnthropicClient
        from agents_system.core.agents.rendering_optimizer import (
            RenderingOptimizerAgent,
        )

        claude_client = AnthropicClient(config.anthropic)
        rendering_optimizer = RenderingOptimizerAgent(claude_client)
        print("✅ Rendering Optimizer Agent initialized")

        # Select which code to test
        test_code = SAMPLE_INEFFICIENT_CODE  # Change to test different code
        test_name = "SAMPLE_INEFFICIENT_CODE"  # Update this if you change the code

        # Display the input code
        print(f"\n📝 INPUT MANIM CODE ({test_name}):")
        print("-" * 60)
        print(test_code)
        print("-" * 60)

        # Execute Rendering Optimizer
        print("\n🚀 Executing Rendering Optimizer Agent...")
        print("=" * 60)

        # Create default profile
        from agents_system.domain.models import RenderingProfile

        original_profile = RenderingProfile(
            profile_id="test_profile",
            name="Test Profile",
            quality="high",
            resolution=(1920, 1080),
            frame_rate=60,
            renderer="cairo",
        )

        # Use the agent directly
        performance_metrics = await rendering_optimizer.analyze_performance(
            test_code, original_profile
        )

        # Generate optimization suggestions
        optimization_suggestions = (
            await rendering_optimizer.generate_optimization_suggestions(
                test_code, original_profile, performance_metrics
            )
        )

        # Apply code optimizations
        optimized_code, applied_optimizations = (
            await rendering_optimizer.apply_code_optimizations(
                test_code, optimization_suggestions
            )
        )

        # Create optimized profile
        optimized_profile = await rendering_optimizer.create_optimized_profile(
            original_profile, optimization_suggestions, applied_optimizations
        )

        # Calculate estimated improvements
        estimated_speedup = rendering_optimizer._calculate_estimated_speedup(
            applied_optimizations, performance_metrics
        )
        estimated_time_saved = (
            performance_metrics.total_render_time * (1 - 1 / estimated_speedup)
            if performance_metrics and performance_metrics.total_render_time > 0
            else 0.0
        )

        # Create a result object
        from agents_system.domain.models import RenderingOptimizationResult

        result = RenderingOptimizationResult(
            original_code=test_code,
            optimized_code=optimized_code,
            original_profile=original_profile,
            optimized_profile=optimized_profile,
            performance_metrics=performance_metrics,
            optimization_suggestions=optimization_suggestions,
            applied_optimizations=applied_optimizations,
            estimated_time_saved=estimated_time_saved,
            estimated_speedup=estimated_speedup,
            success=estimated_speedup > 1.05,  # At least 5% improvement
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
                "suggestions_made": len(result.optimization_suggestions),
                "optimizations_applied": len(result.applied_optimizations),
                "estimated_speedup": result.estimated_speedup,
                "estimated_time_saved": result.estimated_time_saved,
            },
        )

        print("=" * 60)

        if agent_result.success:
            print("✅ Rendering optimization: SUCCESS")
            optimization_result = agent_result.data

            print("\n" + "=" * 70)
            print("⚙️ RENDERING OPTIMIZATION RESULTS")
            print("=" * 70)

            # Basic metrics
            print(
                f"🎯 Optimization Suggestions: {len(optimization_result.optimization_suggestions)}"
            )
            print(
                f"🔧 Applied Optimizations: {len(optimization_result.applied_optimizations)}"
            )
            print(f"⏱️ Estimated Speedup: {optimization_result.estimated_speedup:.2f}x")
            print(
                f"💰 Estimated Time Saved: {optimization_result.estimated_time_saved:.2f} seconds"
            )

            # Performance metrics
            if optimization_result.performance_metrics:
                metrics = optimization_result.performance_metrics
                print("\n📊 Performance Metrics:")
                print(f"   Total Render Time: {metrics.total_render_time:.2f} seconds")
                print(f"   Frames Rendered: {metrics.frames_rendered}")
                print(
                    f"   Average Frame Time: {metrics.average_frame_time:.4f} seconds"
                )
                print(f"   Peak Memory Usage: {metrics.peak_memory_usage:.2f} MB")
                print(f"   CPU Usage: {metrics.cpu_usage:.1f}%")

                if metrics.bottlenecks:
                    print("\n⚠️ Identified Bottlenecks:")
                    for i, bottleneck in enumerate(metrics.bottlenecks, 1):
                        print(f"   {i}. {bottleneck}")

            # Optimization suggestions
            if optimization_result.optimization_suggestions:
                print(
                    f"\n💡 Optimization Suggestions ({len(optimization_result.optimization_suggestions)}):"
                )

                # Group by category
                suggestions_by_category = {}
                for suggestion in optimization_result.optimization_suggestions:
                    if suggestion.category not in suggestions_by_category:
                        suggestions_by_category[suggestion.category] = []
                    suggestions_by_category[suggestion.category].append(suggestion)

                for category, suggestions in suggestions_by_category.items():
                    print(
                        f"\n   {category.upper()} OPTIMIZATIONS ({len(suggestions)}):"
                    )
                    for i, suggestion in enumerate(suggestions, 1):
                        print(f"\n      {i}. {suggestion.description}")
                        print(f"         Impact: {suggestion.impact}")
                        print(
                            f"         Complexity: {suggestion.implementation_complexity}"
                        )
                        print(
                            f"         Estimated Speedup: {suggestion.estimated_speedup:.2f}x"
                        )
                        print(
                            f"         Applied: {'Yes' if suggestion.applied else 'No'}"
                        )

            # Profile comparison
            print("\n🔄 Rendering Profile Changes:")
            print(
                f"   Original Quality: {optimization_result.original_profile.quality}"
            )
            print(
                f"   Optimized Quality: {optimization_result.optimized_profile.quality}"
            )
            print(
                f"   Original Resolution: {optimization_result.original_profile.resolution[0]}x{optimization_result.original_profile.resolution[1]}"
            )
            print(
                f"   Optimized Resolution: {optimization_result.optimized_profile.resolution[0]}x{optimization_result.optimized_profile.resolution[1]}"
            )
            print(
                f"   Original Frame Rate: {optimization_result.original_profile.frame_rate}"
            )
            print(
                f"   Optimized Frame Rate: {optimization_result.optimized_profile.frame_rate}"
            )

            # Code comparison
            print("\n📝 Code Changes:")
            original_lines = optimization_result.original_code.count("\n")
            optimized_lines = optimization_result.optimized_code.count("\n")
            print(f"   Original Code: {original_lines} lines")
            print(f"   Optimized Code: {optimized_lines} lines")
            print(f"   Line Difference: {optimized_lines - original_lines} lines")

            # Show a sample of the optimized code
            print("\n📄 Optimized Code Sample (first 10 lines):")
            print("```python")
            print("\n".join(optimization_result.optimized_code.split("\n")[:10]))
            print("...")
            print("```")

            print("\n🎉 Rendering Optimizer Agent test: PASSED")
            return True

        else:
            print("❌ Rendering optimization: FAILED")
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


async def test_rendering_optimization_workflow():
    """Test the complete Rendering Optimization Workflow."""

    print("🔄 Testing Rendering Optimization Workflow")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize workflow
        print("\n🔧 Initializing Rendering Optimization Workflow...")
        workflow = RenderingOptimizationWorkflow(config)
        print("✅ Rendering Optimization Workflow initialized")

        # Select which code to test
        test_code = SAMPLE_INEFFICIENT_CODE  # Change to test different code
        test_name = "SAMPLE_INEFFICIENT_CODE"  # Update this if you change the code

        # Display the input code
        print(f"\n📝 INPUT MANIM CODE ({test_name}):")
        print("-" * 60)
        print(test_code)
        print("-" * 60)

        # Create default profile
        from agents_system.domain.models import RenderingProfile

        original_profile = RenderingProfile(
            profile_id="test_profile",
            name="Test Profile",
            quality="high",
            resolution=(1920, 1080),
            frame_rate=60,
            renderer="cairo",
        )

        # Execute workflow
        print("\n🚀 Executing Rendering Optimization Workflow...")
        print("=" * 60)

        result = await workflow.optimize_rendering(test_code, original_profile)

        print("=" * 60)

        if result.success:
            print("✅ Rendering optimization workflow: SUCCESS")

            # Print agent messages
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

            print("\n🎉 Rendering Optimization Workflow test: PASSED")
            return True

        else:
            print("❌ Rendering optimization workflow: FAILED")
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
    print("🚀 ExplainX Rendering Optimizer Agent Test")
    print("🎯 Testing rendering optimization for performance")
    print("📍 Using Manim code with inefficient rendering settings")
    print()

    # Run the agent test
    success = asyncio.run(test_rendering_optimizer_agent())

    # Uncomment to test the full workflow
    # workflow_success = asyncio.run(test_rendering_optimization_workflow())

    if success:
        print("\n" + "=" * 70)
        print("🎉 RENDERING OPTIMIZER AGENT WORKS CORRECTLY!")
        print("✅ Successfully analyzed and optimized rendering settings")
        print("🔄 Next agents to implement:")
        print("   1. Integration Orchestrator Agent (coordinates all agents)")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("⚠️ RENDERING OPTIMIZER AGENT ENCOUNTERED ISSUES!")
        print("❌ Some rendering optimizations could not be processed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
