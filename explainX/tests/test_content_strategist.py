#!/usr/bin/env python3
"""
Test script for the Content Strategist Agent.

This script tests the Content Strategist Agent using the actual content
from testfile.txt to demonstrate intelligent content analysis and strategy creation.
"""

import asyncio
import sys
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig
from agents_system.core.workflows.content_analysis_workflow import (
    ContentAnalysisWorkflow,
)


async def test_content_strategist():
    """Test the Content Strategist Agent with real ExplainX content."""

    print("🧠 Testing Content Strategist Agent")
    print("=" * 60)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Read the actual test content
        print("📖 Reading test content from testfile.txt...")
        testfile_path = Path("testfile.txt")

        if not testfile_path.exists():
            print("❌ testfile.txt not found")
            return False

        content = testfile_path.read_text(encoding="utf-8")
        content_preview = content[:500] + "..." if len(content) > 500 else content

        print(f"✅ Content loaded: {len(content)} characters")
        print(f"📄 Preview: {content_preview}")

        # Initialize the workflow
        print("\n🔧 Initializing Content Analysis Workflow...")
        workflow = ContentAnalysisWorkflow(config)
        print("✅ Workflow initialized")

        # Execute content analysis
        print("\n🚀 Executing Content Strategist Agent...")
        print("-" * 40)

        result = await workflow.analyze_content(
            content=content,
            title="Attention, NMT, and Transformers - Educational Content Analysis",
        )

        print("-" * 40)

        if result.success:
            print("✅ Content analysis: SUCCESS")
            strategy = result.data

            print("\n" + "=" * 60)
            print("📊 CONTENT STRATEGY RESULTS")
            print("=" * 60)

            # Basic metrics
            print(f"🎯 Learning Objectives: {len(strategy.learning_objectives)}")
            print(f"📚 Content Chunks: {len(strategy.content_chunks)}")
            print(f"🎬 Recommended Scenes: {strategy.recommended_scene_count}")
            print(f"⏱️  Estimated Duration: {strategy.total_estimated_time} minutes")
            print(f"🧠 Cognitive Load: {strategy.cognitive_load_assessment}")

            # Content analysis metrics
            print(f"\n📈 Content Analysis:")
            print(f"   Mathematical Density: {strategy.mathematical_density:.2f}")
            print(f"   Conceptual Complexity: {strategy.conceptual_complexity:.2f}")
            print(f"   Practical Relevance: {strategy.practical_relevance:.2f}")

            # Recommendations
            print(f"\n🎨 Recommendations:")
            print(
                f"   Visualization Opportunities: {len(strategy.visual_opportunities)}"
            )
            print(
                f"   Animation Recommendations: {len(strategy.animation_recommendations)}"
            )

            # Learning objectives details
            print(f"\n🎯 Learning Objectives Details:")
            for i, obj in enumerate(strategy.learning_objectives, 1):
                print(f"   {i}. {obj.title}")
                print(f"      Difficulty: {obj.difficulty.value}")
                print(f"      Time: {obj.estimated_time_minutes} min")
                print(f"      Description: {obj.description}")
                if obj.prerequisites:
                    print(f"      Prerequisites: {', '.join(obj.prerequisites)}")
                print()

            # Content chunks details
            print(f"📚 Content Chunks Details:")
            for i, chunk in enumerate(strategy.content_chunks, 1):
                print(f"   {i}. {chunk.title} ({chunk.id})")
                print(f"      Type: {chunk.content_type.value}")
                print(f"      Difficulty: {chunk.difficulty.value}")
                print(f"      Reading Time: {chunk.estimated_reading_time} min")
                print(f"      Key Concepts: {', '.join(chunk.key_concepts)}")
                if chunk.mathematical_concepts:
                    print(
                        f"      Math Concepts: {', '.join(chunk.mathematical_concepts)}"
                    )
                print()

            # Visualization opportunities
            if strategy.visual_opportunities:
                print(f"🎨 Visualization Opportunities:")
                for viz in strategy.visual_opportunities:
                    print(f"   • {viz.concept} ({viz.visualization_type.value})")
                    print(
                        f"     Priority: {viz.priority}, Complexity: {viz.estimated_complexity}"
                    )
                    print(f"     Description: {viz.description}")
                print()

            # Animation recommendations
            if strategy.animation_recommendations:
                print(f"🎬 Animation Recommendations:")
                for anim in strategy.animation_recommendations:
                    print(f"   • {anim.concept} ({anim.animation_type})")
                    print(
                        f"     Value: {anim.educational_value}, Complexity: {anim.complexity}"
                    )
                    print(f"     Description: {anim.description}")
                print()

            # Workflow metadata
            print("🔧 Workflow Execution Details:")
            print(
                f"   Processing Steps: {result.metadata.get('total_processing_steps', 0)}"
            )
            print(f"   Final State: {result.metadata.get('workflow_state', 'unknown')}")

            # Agent messages
            if "agent_messages" in result.metadata:
                print(f"\n📨 Agent Messages:")
                for msg in result.metadata["agent_messages"]:
                    agent = msg.get("agent", "unknown")
                    status = msg.get("status", "unknown")
                    print(f"   {agent}: {status}")
                    if "metadata" in msg:
                        for key, value in msg["metadata"].items():
                            print(f"     {key}: {value}")

            print("\n🎉 Content Strategist Agent test: PASSED")
            print("🚀 Ready to integrate with LaTeX Specialist Agent!")
            return True

        else:
            print("❌ Content analysis: FAILED")
            print("Errors:")
            for error in result.errors:
                print(f"   • {error}")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("🚀 ExplainX Content Strategist Agent Test")
    print("🎯 Testing intelligent content analysis for educational videos")
    print("📍 Using testfile.txt content about Transformers and Attention")
    print()

    # Run the test
    success = asyncio.run(test_content_strategist())

    if success:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Content Strategist Agent is working correctly")
        print("🔄 Ready to implement downstream agents:")
        print("   1. LaTeX Specialist Agent (fix compilation errors)")
        print("   2. Code Modifier Agent (fix positioning/bounds)")
        print("   3. Visual Composer Agent (optimize layouts)")
        print("=" * 60)
        return 0
    else:
        print("\n❌ TESTS FAILED")
        print("Please check configuration and try again.")
        return 1


if __name__ == "__main__":
    exit(main())
