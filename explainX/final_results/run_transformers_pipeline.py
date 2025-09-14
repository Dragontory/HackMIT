#!/usr/bin/env python3
"""
Run the full multi-agent pipeline with Transformers content.
"""

import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents_system.infrastructure.config import AgentConfig
from agents_system.infrastructure.anthropic.client import AnthropicClient


async def run_full_pipeline():
    try:
        # Load config and initialize client
        config = AgentConfig.from_env()
        claude_client = AnthropicClient(config.anthropic)

        # Initialize the Integration Orchestrator
        from agents_system.core.agents.integration_orchestrator import (
            IntegrationOrchestratorAgent,
        )

        orchestrator = IntegrationOrchestratorAgent(claude_client)

        # Read the Transformers content
        with open("testfile.txt", "r") as f:
            content = f.read()

        print("🚀 Starting Full Multi-Agent Pipeline with Transformers Content...")
        print(f"📄 Content length: {len(content)} characters")
        print(f"🎯 Target: Generate comprehensive Manim educational video")
        print("=" * 80)

        # Run the orchestration
        result = await orchestrator.orchestrate_agents(content)

        print("\n" + "=" * 80)
        print("🎉 PIPELINE COMPLETED!")
        print("=" * 80)

        # Print comprehensive results using correct attributes
        print(f"\n📊 ORCHESTRATION METRICS:")
        print(f"   Overall Success: {result.success}")
        print(f"   Total Processing Time: {result.total_processing_time:.2f}s")
        print(f"   Agents Executed: {result.agents_executed}")
        print(f"   Success Rate: {result.success_rate:.1%}")
        print(f"   Parallel Efficiency: {result.parallel_efficiency:.1%}")
        print(f"   Critical Path Time: {result.critical_path_time:.2f}s")

        if result.execution_plan:
            print(f"\n📋 EXECUTION PLAN:")
            print(f"   Strategy: {result.execution_plan.optimization_strategy}")
            print(f"   Total Phases: {len(result.execution_plan.execution_phases)}")
            if (
                hasattr(result.execution_plan, "critical_path")
                and result.execution_plan.critical_path
            ):
                print(
                    f'   Critical Path: {" → ".join(result.execution_plan.critical_path)}'
                )

            print(f"\n🔄 PHASE EXECUTION:")
            for i, phase in enumerate(result.execution_plan.execution_phases, 1):
                print(f"   Phase {i}: {', '.join(phase)}")
                for agent_name in phase:
                    execution = next(
                        (
                            e
                            for e in result.agent_executions
                            if e.agent_name == agent_name
                        ),
                        None,
                    )
                    if execution:
                        status = "✅" if execution.success else "❌"
                        print(
                            f"     {status} {agent_name}: {execution.execution_time:.2f}s"
                        )

        if result.quality_metrics:
            print(f"\n🎯 QUALITY METRICS:")
            print(f"   Overall Score: {result.quality_metrics.overall_score:.2f}/100")
            print(
                f"   Technical Quality: {result.quality_metrics.technical_quality:.1f}"
            )
            print(
                f"   Educational Value: {result.quality_metrics.educational_value:.1f}"
            )
            print(f"   Visual Appeal: {result.quality_metrics.visual_appeal:.1f}")
            print(f"   Performance: {result.quality_metrics.performance:.1f}")
            print(f"   Robustness: {result.quality_metrics.robustness:.1f}")

        # Show final generated code
        final_code = result.final_output
        if final_code:
            print(f"\n🎬 GENERATED MANIM CODE ({len(final_code)} chars):")
            print("=" * 50)
            print(final_code[:1000] + "..." if len(final_code) > 1000 else final_code)
            print("=" * 50)

            # Save the generated code
            with open("generated_transformers_video.py", "w") as f:
                f.write(final_code)
            print(f"\n💾 Code saved to: generated_transformers_video.py")

        # Show improvements applied
        if result.code_modifications:
            print(f"\n🔧 CODE MODIFICATIONS ({len(result.code_modifications)}):")
            for mod in result.code_modifications[:3]:
                print(f"   • {mod}")

        if result.visual_enhancements:
            print(f"\n🎨 VISUAL ENHANCEMENTS ({len(result.visual_enhancements)}):")
            for enh in result.visual_enhancements[:3]:
                print(f"   • {enh}")

        if result.animation_directions:
            print(f"\n🎬 ANIMATION DIRECTIONS ({len(result.animation_directions)}):")
            for dir_item in result.animation_directions[:3]:
                print(f"   • {dir_item}")

        if result.rendering_optimizations:
            print(
                f"\n⚡ RENDERING OPTIMIZATIONS ({len(result.rendering_optimizations)}):"
            )
            for opt in result.rendering_optimizations[:3]:
                print(f"   • {opt}")

        return result.success

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_full_pipeline())
    print(f'\n🏁 Final Result: {"SUCCESS" if success else "FAILED"}')
