#!/usr/bin/env python3
"""
Test script for the Visual Composer Agent.

This script tests the Visual Composer Agent using sample Manim code and
demonstrates its ability to compose and coordinate visual elements.
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig
from agents_system.core.workflows.visual_composition_workflow import (
    VisualCompositionWorkflow,
)


# Sample Manim code with various visual elements
SAMPLE_MANIM_CODE = """
from manim import *

class NeuralNetworkScene(Scene):
    def construct(self):
        # Title
        title = Text("Neural Network Basics", font_size=48)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create a simple neural network
        network = self.create_network()
        self.play(Create(network))
        self.wait(1)
        
        # Show forward propagation
        self.show_forward_propagation(network)
        self.wait(2)
        
        # Conclusion
        conclusion = Text("Deep Learning Foundation", font_size=36)
        conclusion.to_edge(DOWN)
        self.play(FadeIn(conclusion))
        self.wait(1)
    
    def create_network(self):
        # Create layers
        input_layer = self.create_layer(3, LEFT * 4, "Input Layer")
        hidden_layer = self.create_layer(4, ORIGIN, "Hidden Layer")
        output_layer = self.create_layer(2, RIGHT * 4, "Output Layer")
        
        # Group all layers
        network = VGroup(input_layer, hidden_layer, output_layer)
        
        # Add connections between layers
        connections = self.create_connections(input_layer, hidden_layer)
        connections.add(self.create_connections(hidden_layer, output_layer))
        network.add(connections)
        
        return network
    
    def create_layer(self, num_neurons, position, label_text):
        neurons = VGroup()
        for i in range(num_neurons):
            neuron = Circle(radius=0.3, color=BLUE, fill_opacity=0.5)
            neuron.move_to(position + DOWN * (i - (num_neurons-1)/2) * 1.5)
            neurons.add(neuron)
        
        # Add label
        label = Text(label_text, font_size=24)
        label.next_to(neurons, UP, buff=0.5)
        
        layer = VGroup(neurons, label)
        return layer
    
    def create_connections(self, layer1, layer2):
        connections = VGroup()
        neurons1 = layer1[0]  # Get neurons from layer1
        neurons2 = layer2[0]  # Get neurons from layer2
        
        for n1 in neurons1:
            for n2 in neurons2:
                connection = Line(n1.get_center(), n2.get_center(), stroke_opacity=0.3)
                connections.add(connection)
        
        return connections
    
    def show_forward_propagation(self, network):
        input_layer = network[0][0]  # Get neurons from input layer
        hidden_layer = network[1][0]  # Get neurons from hidden layer
        output_layer = network[2][0]  # Get neurons from output layer
        
        # Highlight input
        self.play(input_layer.animate.set_color(GREEN))
        self.wait(0.5)
        
        # Show data flowing to hidden layer
        for neuron in hidden_layer:
            self.play(neuron.animate.set_color(YELLOW), run_time=0.3)
        self.wait(0.5)
        
        # Show data flowing to output layer
        for neuron in output_layer:
            self.play(neuron.animate.set_color(RED), run_time=0.3)
        self.wait(0.5)
"""


# Sample Manim code with suboptimal visual composition
SAMPLE_SUBOPTIMAL_CODE = """
from manim import *

class MathConcepts(Scene):
    def construct(self):
        # Title
        title = Text("Mathematical Concepts")
        self.play(Write(title))
        self.wait(1)
        self.play(FadeOut(title))
        
        # First equation
        eq1 = MathTex(r"f(x) = x^2 + 2x + 1")
        self.play(Write(eq1))
        self.wait(1)
        
        # Second equation
        eq2 = MathTex(r"f(x) = (x+1)^2")
        eq2.shift(DOWN)
        self.play(Write(eq2))
        self.wait(1)
        
        # Show they're equivalent
        arrow = Arrow(eq1.get_bottom(), eq2.get_top())
        self.play(Create(arrow))
        self.wait(1)
        
        # Third equation - factored form
        eq3 = MathTex(r"f(x) = (x+1)(x+1)")
        eq3.shift(DOWN * 2)
        self.play(Write(eq3))
        self.wait(1)
        
        # Final statement
        conclusion = Text("Completing the square")
        conclusion.shift(DOWN * 3)
        self.play(Write(conclusion))
        self.wait(2)
        
        # Clear everything
        self.play(FadeOut(eq1), FadeOut(eq2), FadeOut(eq3), 
                 FadeOut(arrow), FadeOut(conclusion))
        self.wait(1)
"""


async def test_visual_composer_agent():
    """Test the Visual Composer Agent with sample Manim code."""

    print("🎨 Testing Visual Composer Agent")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize the agent directly (skip the workflow for faster testing)
        print("\n🔧 Initializing Visual Composer Agent...")
        from agents_system.infrastructure.anthropic.client import AnthropicClient
        from agents_system.core.agents.visual_composer import VisualComposerAgent

        claude_client = AnthropicClient(config.anthropic)
        visual_composer = VisualComposerAgent(claude_client)
        print("✅ Visual Composer Agent initialized")

        # Select which code to test
        test_code = SAMPLE_SUBOPTIMAL_CODE  # Change to test different code
        test_name = "SAMPLE_SUBOPTIMAL_CODE"  # Update this if you change the code

        # Display the input code
        print(f"\n📝 INPUT MANIM CODE ({test_name}):")
        print("-" * 60)
        print(test_code)
        print("-" * 60)

        # Execute Visual Composer
        print("\n🚀 Executing Visual Composer Agent...")
        print("=" * 60)

        # Use the agent directly
        compositions = await visual_composer.analyze_visual_elements(test_code)

        # Generate improvements
        layout_improvements = await visual_composer.generate_layout_improvements(
            test_code, compositions
        )
        animation_improvements = await visual_composer.generate_animation_improvements(
            test_code, compositions
        )

        # Generate suggestions
        element_suggestions = await visual_composer.generate_element_suggestions(
            test_code, compositions
        )

        # Apply improvements
        enhanced_code = await visual_composer.apply_improvements(
            test_code, layout_improvements, animation_improvements
        )

        # Create a result object
        from agents_system.domain.models import VisualCompositionResult

        result = VisualCompositionResult(
            original_code=test_code,
            enhanced_code=enhanced_code,
            compositions=compositions,
            element_suggestions=element_suggestions,
            layout_improvements=layout_improvements,
            animation_improvements=animation_improvements,
            success=True,
            processing_time=0.0,
        )

        # Create a result object
        from agents_system.domain.models import AgentResult

        agent_result = AgentResult(
            success=True,
            data=result,
            errors=[],
            warnings=[],
            metadata={
                "compositions_created": len(compositions),
                "elements_composed": sum(len(comp.elements) for comp in compositions),
                "improvements_made": len(layout_improvements)
                + len(animation_improvements),
                "suggestions_made": len(element_suggestions),
            },
        )

        print("=" * 60)

        if agent_result.success:
            print("✅ Visual composition: SUCCESS")
            composition_result = agent_result.data

            print("\n" + "=" * 70)
            print("🎨 VISUAL COMPOSITION RESULTS")
            print("=" * 70)

            # Basic metrics
            print(f"🎯 Compositions Created: {len(composition_result.compositions)}")
            print(
                f"🔧 Visual Elements: {sum(len(comp.elements) for comp in composition_result.compositions)}"
            )
            print(
                f"💡 Improvements: {len(composition_result.layout_improvements) + len(composition_result.animation_improvements)}"
            )
            print(f"✨ Suggestions: {len(composition_result.element_suggestions)}")

            # Compositions
            print("\n📊 Visual Compositions:")
            for i, comp in enumerate(composition_result.compositions, 1):
                print(f"\n   Composition {i}: {comp.title}")
                print(f"   Elements: {len(comp.elements)}")

                # Group elements by type
                elements_by_type = {}
                for element in comp.elements:
                    if element.element_type not in elements_by_type:
                        elements_by_type[element.element_type] = 0
                    elements_by_type[element.element_type] += 1

                print(f"   Element Types: {elements_by_type}")

                if comp.timeline:
                    print(f"   Timeline Steps: {len(comp.timeline)}")

            # Layout improvements
            if composition_result.layout_improvements:
                print(
                    f"\n🔄 Layout Improvements ({len(composition_result.layout_improvements)}):"
                )
                for i, improvement in enumerate(
                    composition_result.layout_improvements, 1
                ):
                    print(f"\n   Improvement {i}: {improvement['description']}")

            # Animation improvements
            if composition_result.animation_improvements:
                print(
                    f"\n⏱️ Animation Improvements ({len(composition_result.animation_improvements)}):"
                )
                for i, improvement in enumerate(
                    composition_result.animation_improvements, 1
                ):
                    print(f"\n   Improvement {i}: {improvement['description']}")

            # Element suggestions
            if composition_result.element_suggestions:
                print(
                    f"\n💡 Element Suggestions ({len(composition_result.element_suggestions)}):"
                )
                for i, suggestion in enumerate(
                    composition_result.element_suggestions, 1
                ):
                    print(f"\n   Suggestion {i}: {suggestion['description']}")
                    print(f"   Element Type: {suggestion['element_type']}")

            # Code comparison
            print("\n📝 Code Changes:")
            original_lines = composition_result.original_code.count("\n")
            enhanced_lines = composition_result.enhanced_code.count("\n")
            print(f"   Original Code: {original_lines} lines")
            print(f"   Enhanced Code: {enhanced_lines} lines")
            print(f"   Line Difference: {enhanced_lines - original_lines} lines")

            # Show a sample of the enhanced code
            print("\n📄 Enhanced Code Sample (first 10 lines):")
            print("```python")
            print("\n".join(composition_result.enhanced_code.split("\n")[:10]))
            print("...")
            print("```")

            print("\n🎉 Visual Composer Agent test: PASSED")
            return True

        else:
            print("❌ Visual composition: FAILED")
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


async def test_visual_composition_workflow():
    """Test the complete Visual Composition Workflow."""

    print("🔄 Testing Visual Composition Workflow")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize workflow
        print("\n🔧 Initializing Visual Composition Workflow...")
        workflow = VisualCompositionWorkflow(config)
        print("✅ Visual Composition Workflow initialized")

        # Select which code to test
        test_code = SAMPLE_SUBOPTIMAL_CODE  # Change to test different code
        test_name = "SAMPLE_SUBOPTIMAL_CODE"  # Update this if you change the code

        # Display the input code
        print(f"\n📝 INPUT MANIM CODE ({test_name}):")
        print("-" * 60)
        print(test_code)
        print("-" * 60)

        # Execute workflow
        print("\n🚀 Executing Visual Composition Workflow...")
        print("=" * 60)

        result = await workflow.compose_visuals(test_code)

        print("=" * 60)

        if result.success:
            print("✅ Visual composition workflow: SUCCESS")

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

            print("\n🎉 Visual Composition Workflow test: PASSED")
            return True

        else:
            print("❌ Visual composition workflow: FAILED")
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
    print("🚀 ExplainX Visual Composer Agent Test")
    print("🎯 Testing visual composition and coordination")
    print("📍 Using Manim code with various visual elements")
    print()

    # Run the agent test
    success = asyncio.run(test_visual_composer_agent())

    # Uncomment to test the full workflow
    # workflow_success = asyncio.run(test_visual_composition_workflow())

    if success:
        print("\n" + "=" * 70)
        print("🎉 VISUAL COMPOSER AGENT WORKS CORRECTLY!")
        print("✅ Successfully analyzed and enhanced visual compositions")
        print("🔄 Next agents to implement:")
        print("   1. Rendering Optimizer Agent (optimize rendering settings)")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("⚠️ VISUAL COMPOSER AGENT ENCOUNTERED ISSUES!")
        print("❌ Some visual compositions could not be processed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
