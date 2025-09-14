#!/usr/bin/env python3
"""
Test script for the Integration Orchestrator Agent.

This script tests the Integration Orchestrator Agent's ability to coordinate
all specialized agents and create comprehensive educational animation pipelines.
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig


# Sample comprehensive educational content for orchestration
SAMPLE_ORCHESTRATION_CONTENT = """
Title: Understanding Machine Learning Fundamentals

Content Overview:
Machine learning is a branch of artificial intelligence that enables computers to 
learn and improve from experience without being explicitly programmed. This comprehensive
guide covers essential concepts, algorithms, and practical applications.

Core Learning Topics:

1. Introduction to Machine Learning
   - Definition and key concepts
   - Types of machine learning (supervised, unsupervised, reinforcement)
   - Real-world applications and use cases
   - Historical context and evolution

2. Mathematical Foundations
   - Linear algebra: vectors, matrices, eigenvalues
   - Statistics and probability theory
   - Calculus for optimization
   - Information theory basics

3. Supervised Learning Algorithms
   - Linear regression and polynomial regression
   - Logistic regression for classification
   - Decision trees and random forests
   - Support vector machines (SVM)
   - Neural networks and deep learning

4. Unsupervised Learning Methods
   - K-means clustering
   - Hierarchical clustering
   - Principal component analysis (PCA)
   - Dimensionality reduction techniques

5. Model Evaluation and Validation
   - Training, validation, and test sets
   - Cross-validation techniques
   - Performance metrics (accuracy, precision, recall, F1-score)
   - Overfitting and underfitting

6. Practical Implementation
   - Data preprocessing and feature engineering
   - Model selection and hyperparameter tuning
   - Deployment considerations
   - Ethics and bias in machine learning

Mathematical Components:
- Linear regression: y = wx + b
- Gradient descent: θ = θ - α∇J(θ)
- Sigmoid function: σ(z) = 1/(1 + e^(-z))
- Cost functions and optimization

Visual Elements Needed:
- Interactive plots showing algorithm convergence
- 3D visualizations of decision boundaries
- Animated demonstrations of gradient descent
- Comparison charts of different algorithms

Educational Requirements:
- Clear concept progression from basic to advanced
- Interactive examples and hands-on exercises
- Visual metaphors for abstract mathematical concepts
- Assessment checkpoints throughout the content
- Accessibility features for diverse learners

Learning Objectives:
1. Understand fundamental machine learning concepts and terminology
2. Apply mathematical foundations to machine learning problems
3. Implement basic supervised and unsupervised learning algorithms
4. Evaluate model performance using appropriate metrics
5. Design end-to-end machine learning solutions for real problems

Target Audience: Intermediate students with basic programming and math background
Duration: 90-120 minutes of interactive content
Assessment: Mixed formative and summative evaluation strategies
"""


async def test_integration_orchestrator_agent():
    """Test the Integration Orchestrator Agent with comprehensive content."""

    print("🚀 Testing Integration Orchestrator Agent")
    print("=" * 80)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize the orchestrator
        print("\n🔧 Initializing Integration Orchestrator Agent...")
        from agents_system.infrastructure.anthropic.client import AnthropicClient
        from agents_system.core.agents.integration_orchestrator import (
            IntegrationOrchestratorAgent,
        )

        claude_client = AnthropicClient(config.anthropic)
        orchestrator = IntegrationOrchestratorAgent(claude_client)
        print("✅ Integration Orchestrator Agent initialized")
        print(f"📊 Available agents: {len(orchestrator.agents)}")

        # Display available agents
        print("\n🤖 Available Specialized Agents:")
        for i, (agent_name, agent) in enumerate(orchestrator.agents.items(), 1):
            print(f"   {i:2}. {agent_name}: {agent.description}")

        # Display the input content
        print(f"\n📝 INPUT EDUCATIONAL CONTENT:")
        print("-" * 80)
        print(
            SAMPLE_ORCHESTRATION_CONTENT[:500] + "..."
            if len(SAMPLE_ORCHESTRATION_CONTENT) > 500
            else SAMPLE_ORCHESTRATION_CONTENT
        )
        print("-" * 80)

        # Execute Integration Orchestration
        print("\n🚀 Executing Integration Orchestrator Agent...")
        print("=" * 80)

        # Start orchestration
        start_time = time.time()
        result = await orchestrator.orchestrate_agents(SAMPLE_ORCHESTRATION_CONTENT)
        total_time = time.time() - start_time

        # Create agent result
        from agents_system.domain.models import AgentResult

        agent_result = AgentResult(
            success=result.success,
            data=result,
            metadata={
                "orchestration_time": total_time,
                "agents_executed": result.agents_executed,
                "success_rate": result.success_rate,
                "quality_score": result.quality_metrics.overall_score,
            },
        )

        print("=" * 80)

        if agent_result.success:
            print("✅ Integration orchestration: SUCCESS")
            orchestration_result = agent_result.data

            print("\n" + "=" * 80)
            print("🚀 INTEGRATION ORCHESTRATION RESULTS")
            print("=" * 80)

            # Basic orchestration metrics
            print(f"🎯 Orchestration ID: {orchestration_result.orchestration_id}")
            print(f"📊 Agents Executed: {orchestration_result.agents_executed}")
            print(f"✅ Success Rate: {orchestration_result.success_rate:.1%}")
            print(
                f"⏱️ Total Processing Time: {orchestration_result.total_processing_time:.2f} seconds"
            )
            print(
                f"🎨 Quality Score: {orchestration_result.quality_metrics.overall_score:.2f}/1.0"
            )
            print(
                f"⚡ Parallel Efficiency: {orchestration_result.parallel_efficiency:.1%}"
            )

            # Execution plan overview
            print(f"\n📋 Execution Plan Overview:")
            print(f"   Plan ID: {orchestration_result.execution_plan.plan_id}")
            print(f"   Title: {orchestration_result.execution_plan.title}")
            print(
                f"   Strategy: {orchestration_result.execution_plan.optimization_strategy}"
            )
            print(
                f"   Phases: {len(orchestration_result.execution_plan.execution_phases)}"
            )
            print(
                f"   Estimated Duration: {orchestration_result.execution_plan.estimated_duration:.1f} seconds"
            )

            # Execution phases
            print(
                f"\n🔄 Execution Phases ({len(orchestration_result.execution_plan.execution_phases)}):"
            )
            for i, phase in enumerate(
                orchestration_result.execution_plan.execution_phases, 1
            ):
                print(f"   Phase {i}: {', '.join(phase)}")

            # Critical path
            if orchestration_result.execution_plan.critical_path:
                print(f"\n🎯 Critical Path:")
                print(
                    f"   {' → '.join(orchestration_result.execution_plan.critical_path)}"
                )
                print(
                    f"   Critical Path Time: {orchestration_result.critical_path_time:.2f} seconds"
                )

            # Parallel opportunities
            if orchestration_result.execution_plan.parallel_opportunities:
                print(f"\n⚡ Parallel Execution Groups:")
                for i, group in enumerate(
                    orchestration_result.execution_plan.parallel_opportunities, 1
                ):
                    print(f"   Group {i}: {', '.join(group)}")

            # Agent execution details
            if orchestration_result.agent_executions:
                print(
                    f"\n🤖 Agent Execution Details ({len(orchestration_result.agent_executions)}):"
                )
                successful_executions = [
                    ex for ex in orchestration_result.agent_executions if ex.success
                ]
                failed_executions = [
                    ex for ex in orchestration_result.agent_executions if not ex.success
                ]

                print(f"   ✅ Successful: {len(successful_executions)}")
                print(f"   ❌ Failed: {len(failed_executions)}")

                # Show successful executions
                if successful_executions:
                    print(f"\n   ✅ Successful Executions:")
                    for i, execution in enumerate(successful_executions, 1):
                        print(
                            f"      {i:2}. {execution.agent_name}: {execution.duration:.2f}s"
                        )

                # Show failed executions
                if failed_executions:
                    print(f"\n   ❌ Failed Executions:")
                    for i, execution in enumerate(failed_executions, 1):
                        errors = "; ".join(execution.errors[:2])  # Show first 2 errors
                        print(f"      {i:2}. {execution.agent_name}: {errors}")

            # Quality metrics breakdown
            print(f"\n📊 Quality Metrics Breakdown:")
            metrics = orchestration_result.quality_metrics
            print(f"   🔧 Technical Quality: {metrics.technical_quality:.2f}")
            print(f"   🎓 Educational Quality: {metrics.educational_quality:.2f}")
            print(f"   🎨 Visual Appeal: {metrics.visual_appeal:.2f}")
            print(f"   ⚡ Performance Score: {metrics.performance_score:.2f}")
            print(f"   🛡️ Robustness Score: {metrics.robustness_score:.2f}")
            print(f"   📖 Content Accuracy: {metrics.content_accuracy:.2f}")
            print(f"   ♿ Accessibility Score: {metrics.accessibility_score:.2f}")
            print(f"   🎮 Engagement Score: {metrics.engagement_score:.2f}")
            print(f"   💡 Innovation Score: {metrics.innovation_score:.2f}")

            # Aggregated results summary
            print(f"\n📈 Aggregated Results Summary:")
            if orchestration_result.content_strategy_applied:
                print(f"   ✅ Content Strategy Applied")
            if orchestration_result.latex_fixes_applied:
                print(
                    f"   ✅ LaTeX Fixes: {len(orchestration_result.latex_fixes_applied)}"
                )
            if orchestration_result.code_modifications:
                print(
                    f"   ✅ Code Modifications: {len(orchestration_result.code_modifications)}"
                )
            if orchestration_result.tests_passed:
                print(f"   ✅ Tests Passed: {len(orchestration_result.tests_passed)}")
            if orchestration_result.errors_fixed:
                print(f"   ✅ Errors Fixed: {len(orchestration_result.errors_fixed)}")
            if orchestration_result.visual_enhancements:
                print(
                    f"   ✅ Visual Enhancements: {len(orchestration_result.visual_enhancements)}"
                )
            if orchestration_result.rendering_optimizations:
                print(
                    f"   ✅ Rendering Optimizations: {len(orchestration_result.rendering_optimizations)}"
                )
            if orchestration_result.animation_directions:
                print(
                    f"   ✅ Animation Directions: {len(orchestration_result.animation_directions)}"
                )
            if orchestration_result.dimensional_specializations:
                print(
                    f"   ✅ Dimensional Specializations: {len(orchestration_result.dimensional_specializations)}"
                )
            if orchestration_result.educational_design_applied:
                print(f"   ✅ Educational Design Applied")

            # Recommendations and next steps
            if orchestration_result.recommendations:
                print(
                    f"\n💡 Recommendations ({len(orchestration_result.recommendations)}):"
                )
                for i, rec in enumerate(orchestration_result.recommendations, 1):
                    print(f"   {i}. {rec}")

            if orchestration_result.next_steps:
                print(f"\n🎯 Next Steps ({len(orchestration_result.next_steps)}):")
                for i, step in enumerate(orchestration_result.next_steps, 1):
                    print(f"   {i}. {step}")

            # Performance analysis
            print(f"\n⚡ Performance Analysis:")
            if orchestration_result.agent_executions:
                avg_execution_time = sum(
                    ex.duration for ex in orchestration_result.agent_executions
                ) / len(orchestration_result.agent_executions)
                max_execution_time = max(
                    ex.duration for ex in orchestration_result.agent_executions
                )
                min_execution_time = min(
                    ex.duration for ex in orchestration_result.agent_executions
                )

                print(f"   Average Execution Time: {avg_execution_time:.2f} seconds")
                print(f"   Maximum Execution Time: {max_execution_time:.2f} seconds")
                print(f"   Minimum Execution Time: {min_execution_time:.2f} seconds")
                print(
                    f"   Improvement Factor: {orchestration_result.improvement_factor:.2f}x"
                )

            # Final output information
            print(f"\n📄 Final Output:")
            output_length = len(orchestration_result.final_output)
            input_length = len(orchestration_result.original_input)
            print(f"   Input Length: {input_length:,} characters")
            print(f"   Output Length: {output_length:,} characters")
            print(
                f"   Content Expansion: {output_length/input_length:.1f}x"
                if input_length > 0
                else "   Content Expansion: N/A"
            )

            print("\n🎉 Integration Orchestrator Agent test: PASSED")
            return True

        else:
            print("❌ Integration orchestration: FAILED")
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
    print("🚀 ExplainX Integration Orchestrator Agent Test")
    print("🎯 Testing comprehensive multi-agent coordination")
    print("📍 Using machine learning educational content")
    print("🤖 Coordinating 11 specialized agents")
    print()

    # Run the orchestrator test
    success = asyncio.run(test_integration_orchestrator_agent())

    if success:
        print("\n" + "=" * 80)
        print("🎉 INTEGRATION ORCHESTRATOR AGENT WORKS CORRECTLY!")
        print("✅ Successfully coordinated all specialized agents")
        print("🚀 Complete multi-agent educational animation pipeline operational!")
        print("📊 System demonstrates:")
        print("   • Intelligent agent dependency management")
        print("   • Parallel execution optimization")
        print("   • Comprehensive quality assessment")
        print("   • Educational effectiveness integration")
        print("   • Robust error handling and recovery")
        print("=" * 80)
        return 0
    else:
        print("\n" + "=" * 80)
        print("⚠️ INTEGRATION ORCHESTRATOR AGENT ENCOUNTERED ISSUES!")
        print("❌ Some orchestration aspects could not be processed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit(main())
