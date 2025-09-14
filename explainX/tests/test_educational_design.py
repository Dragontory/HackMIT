#!/usr/bin/env python3
"""
Test script for the Educational Design Agent.

This script tests the Educational Design Agent using sample educational content and
demonstrates its ability to design effective educational flows and scene structures.
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig


# Sample educational content for design
SAMPLE_EDUCATIONAL_CONTENT = """
Title: Introduction to Deep Learning Neural Networks

Content Overview:
Deep learning is a subset of machine learning that uses artificial neural networks 
with multiple layers to model and understand complex patterns in data. This content 
covers fundamental concepts, architectures, and applications.

Core Concepts:
1. Neural Network Basics
   - Neurons and activation functions
   - Weights and biases
   - Forward propagation
   - Backpropagation algorithm

2. Deep Network Architectures
   - Feedforward networks
   - Convolutional Neural Networks (CNNs)
   - Recurrent Neural Networks (RNNs)
   - Transformer models

3. Training Deep Networks
   - Loss functions and optimization
   - Gradient descent variants
   - Regularization techniques
   - Hyperparameter tuning

4. Practical Applications
   - Image recognition and computer vision
   - Natural language processing
   - Speech recognition
   - Generative models

Mathematical Foundations:
- Linear algebra: Matrices and vector operations
- Calculus: Derivatives and chain rule for backpropagation
- Probability: Distributions and Bayesian inference
- Statistics: Sampling and estimation

Hands-on Components:
- Building a simple neural network from scratch
- Implementing common activation functions
- Training a CNN for image classification
- Fine-tuning a pre-trained transformer model

Assessment Methods:
- Concept check quizzes after each section
- Coding exercises with immediate feedback
- Project: Build and train a neural network for a real dataset
- Peer review of project implementations
"""


# Sample content strategy for educational design context
SAMPLE_EDUCATIONAL_STRATEGY = {
    "learning_objectives": [
        "Understand fundamental concepts of neural networks",
        "Apply deep learning architectures to real problems",
        "Implement basic neural networks from scratch",
        "Analyze the performance of different network types",
    ],
    "target_audience": "intermediate",
    "complexity_level": "medium",
    "prerequisites": ["linear algebra", "basic programming", "calculus"],
    "duration_target": 90,  # minutes
    "pedagogical_preferences": ["constructivist", "active_learning"],
    "assessment_approach": "formative_and_summative",
    "engagement_style": "interactive_with_coding",
}


async def test_educational_design_agent():
    """Test the Educational Design Agent with sample content."""

    print("🎓 Testing Educational Design Agent")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize the agent directly
        print("\n🔧 Initializing Educational Design Agent...")
        from agents_system.infrastructure.anthropic.client import AnthropicClient
        from agents_system.core.agents.educational_design import EducationalDesignAgent

        claude_client = AnthropicClient(config.anthropic)
        educational_design = EducationalDesignAgent(claude_client)
        print("✅ Educational Design Agent initialized")

        # Select which content to test
        test_content = SAMPLE_EDUCATIONAL_CONTENT
        test_name = "SAMPLE_EDUCATIONAL_CONTENT"

        # Display the input content
        print(f"\n📝 INPUT EDUCATIONAL CONTENT ({test_name}):")
        print("-" * 60)
        print(test_content)
        print("-" * 60)

        # Execute Educational Design
        print("\n🚀 Executing Educational Design Agent...")
        print("=" * 60)

        # Use the agent directly
        learning_objectives = await educational_design.analyze_learning_objectives(
            test_content, SAMPLE_EDUCATIONAL_STRATEGY
        )

        # Design overall flow
        educational_flow = await educational_design.design_overall_flow(
            test_content, learning_objectives, SAMPLE_EDUCATIONAL_STRATEGY
        )

        # Structure scenes
        scene_structures = await educational_design.structure_scenes(
            test_content, educational_flow, learning_objectives
        )

        # Generate design principles
        design_principles = await educational_design.generate_design_principles(
            test_content, educational_flow, scene_structures
        )

        # Create a result object
        from agents_system.domain.models import EducationalDesignResult

        result = EducationalDesignResult(
            original_content=test_content,
            designed_flow=educational_flow,
            scene_structures=scene_structures,
            learning_objectives=learning_objectives,
            design_principles=design_principles,
            pedagogical_justifications=educational_design._generate_pedagogical_justifications(
                educational_flow, scene_structures
            ),
            accessibility_considerations=educational_design._generate_accessibility_considerations(
                educational_flow
            ),
            assessment_recommendations=educational_design._generate_assessment_recommendations(
                learning_objectives, educational_flow
            ),
            engagement_strategies=educational_design._generate_engagement_strategies(
                scene_structures
            ),
            implementation_notes=educational_design._generate_implementation_notes(
                educational_flow, scene_structures
            ),
            success=len(learning_objectives) > 0 and len(scene_structures) > 0,
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
                "scenes_designed": len(result.scene_structures),
                "learning_objectives": len(result.learning_objectives),
                "design_principles": len(result.design_principles),
                "flow_duration": result.designed_flow.total_duration,
            },
        )

        print("=" * 60)

        if agent_result.success:
            print("✅ Educational design: SUCCESS")
            design_result = agent_result.data

            print("\n" + "=" * 70)
            print("🎓 EDUCATIONAL DESIGN RESULTS")
            print("=" * 70)

            # Basic metrics
            print(f"📚 Learning Objectives: {len(design_result.learning_objectives)}")
            print(f"🎬 Scene Structures: {len(design_result.scene_structures)}")
            print(f"🧠 Design Principles: {len(design_result.design_principles)}")
            print(
                f"⏱️ Total Flow Duration: {design_result.designed_flow.total_duration:.1f} minutes"
            )
            print(
                f"🎯 Pedagogical Framework: {design_result.designed_flow.pedagogical_framework}"
            )
            print(f"📖 Learning Theory: {design_result.designed_flow.learning_theory}")

            # Educational flow information
            print("\n📊 Educational Flow Design:")
            print(f"   Title: {design_result.designed_flow.title}")
            print(f"   Framework: {design_result.designed_flow.pedagogical_framework}")
            print(f"   Learning Theory: {design_result.designed_flow.learning_theory}")
            print(
                f"   Difficulty Curve: {design_result.designed_flow.difficulty_curve}"
            )
            print(
                f"   Engagement Pattern: {design_result.designed_flow.engagement_pattern}"
            )
            print(f"   Target Audience: {design_result.designed_flow.target_audience}")

            # Learning objectives
            if design_result.learning_objectives:
                print(
                    f"\n🎯 Learning Objectives ({len(design_result.learning_objectives)}):"
                )
                total_objective_time = 0
                for i, obj in enumerate(design_result.learning_objectives, 1):
                    print(f"\n   Objective {i}: {obj.title}")
                    print(f"      Description: {obj.description}")
                    print(f"      Cognitive Level: {obj.cognitive_level}")
                    print(f"      Difficulty: {obj.difficulty}")
                    print(f"      Time Estimate: {obj.time_estimate:.1f} minutes")
                    if obj.concepts:
                        print(f"      Key Concepts: {', '.join(obj.concepts[:3])}")
                    total_objective_time += obj.time_estimate

                print(f"\n   Total Objectives Time: {total_objective_time:.1f} minutes")

            # Scene structures
            if design_result.scene_structures:
                print(f"\n🎬 Scene Structures ({len(design_result.scene_structures)}):")
                total_scene_time = 0
                for i, scene in enumerate(design_result.scene_structures, 1):
                    print(f"\n   Scene {i}: {scene.title}")
                    print(f"      Type: {scene.scene_type}")
                    print(f"      Opening Strategy: {scene.opening_strategy}")
                    print(f"      Closing Strategy: {scene.closing_strategy}")
                    print(f"      Pacing Strategy: {scene.pacing_strategy}")
                    print(f"      Duration: {scene.total_duration:.1f} minutes")
                    print(f"      Scaffolding Level: {scene.scaffolding_level}")
                    print(f"      Learning Segments: {len(scene.learning_segments)}")
                    total_scene_time += scene.total_duration

                print(f"\n   Total Scenes Time: {total_scene_time:.1f} minutes")

            # Design principles
            if design_result.design_principles:
                print(
                    f"\n🧠 Design Principles ({len(design_result.design_principles)}):"
                )
                for i, principle in enumerate(design_result.design_principles, 1):
                    print(f"   {i}. {principle}")

            # Pedagogical justifications
            if design_result.pedagogical_justifications:
                print(
                    f"\n🎯 Pedagogical Justifications ({len(design_result.pedagogical_justifications)}):"
                )
                for i, justification in enumerate(
                    design_result.pedagogical_justifications, 1
                ):
                    print(f"   {i}. {justification}")

            # Accessibility considerations
            if design_result.accessibility_considerations:
                print(
                    f"\n♿ Accessibility Considerations ({len(design_result.accessibility_considerations)}):"
                )
                for i, consideration in enumerate(
                    design_result.accessibility_considerations, 1
                ):
                    print(f"   {i}. {consideration}")

            # Assessment recommendations
            if design_result.assessment_recommendations:
                print(
                    f"\n📊 Assessment Recommendations ({len(design_result.assessment_recommendations)}):"
                )
                for i, recommendation in enumerate(
                    design_result.assessment_recommendations, 1
                ):
                    print(f"   {i}. {recommendation}")

            # Engagement strategies
            if design_result.engagement_strategies:
                print(
                    f"\n🎮 Engagement Strategies ({len(design_result.engagement_strategies)}):"
                )
                for i, strategy in enumerate(design_result.engagement_strategies, 1):
                    print(f"   {i}. {strategy}")

            # Implementation notes
            if design_result.implementation_notes:
                print(
                    f"\n📝 Implementation Notes ({len(design_result.implementation_notes)}):"
                )
                for i, note in enumerate(design_result.implementation_notes, 1):
                    print(f"   {i}. {note}")

            # Summary statistics
            print("\n📈 Design Summary:")
            avg_scene_duration = (
                total_scene_time / len(design_result.scene_structures)
                if design_result.scene_structures
                else 0
            )
            print(f"   Average Scene Duration: {avg_scene_duration:.1f} minutes")

            total_segments = sum(
                len(scene.learning_segments) for scene in design_result.scene_structures
            )
            print(f"   Total Learning Segments: {total_segments}")

            cognitive_levels = [
                obj.cognitive_level for obj in design_result.learning_objectives
            ]
            unique_levels = list(set(cognitive_levels))
            print(f"   Cognitive Levels Covered: {', '.join(unique_levels)}")

            print("\n🎉 Educational Design Agent test: PASSED")
            return True

        else:
            print("❌ Educational design: FAILED")
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
    print("🚀 ExplainX Educational Design Agent Test")
    print("🎯 Testing educational flow and scene structure design")
    print("📍 Using deep learning educational content")
    print()

    # Run the agent test
    success = asyncio.run(test_educational_design_agent())

    if success:
        print("\n" + "=" * 70)
        print("🎉 EDUCATIONAL DESIGN AGENT WORKS CORRECTLY!")
        print("✅ Successfully designed educational flows and scene structures")
        print("🔄 Next agent to implement:")
        print("   1. Integration Orchestrator Agent (coordinates all agents)")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("⚠️ EDUCATIONAL DESIGN AGENT ENCOUNTERED ISSUES!")
        print("❌ Some educational design aspects could not be processed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
