#!/usr/bin/env python3
"""
Debug the orchestration issue step by step.
"""

import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents_system.infrastructure.config import AgentConfig
from agents_system.infrastructure.anthropic.client import AnthropicClient
from agents_system.core.agents.integration_orchestrator import (
    IntegrationOrchestratorAgent,
)


async def debug_orchestration():
    """Debug the orchestration step by step."""

    try:
        print("🔧 Debugging Orchestration Issue")
        print("=" * 60)

        # Load config and initialize client
        config = AgentConfig.from_env()
        claude_client = AnthropicClient(config.anthropic)

        # Initialize orchestrator
        orchestrator = IntegrationOrchestratorAgent(claude_client)
        print(f"✅ Orchestrator initialized with {len(orchestrator.agents)} agents")

        # List available agents
        print("\n🤖 Available Agents:")
        for name, agent in orchestrator.agents.items():
            print(f"   • {name}: {agent.description}")

        # Read minimal test content
        test_content = """
        Title: Simple Test Content
        
        This is a test of the Transformer attention mechanism.
        
        Key concepts:
        1. Attention computes a weighted sum
        2. Queries, keys, and values are projections
        3. Multi-head attention runs in parallel
        
        Mathematical formulation:
        Attention(Q,K,V) = softmax(QK^T/√d_k)V
        """

        print(f"\n📄 Test Content ({len(test_content)} chars):")
        print(test_content[:200] + "..." if len(test_content) > 200 else test_content)

        # Create orchestration plan
        print("\n🗓️ Creating Orchestration Plan...")
        try:
            plan = await orchestrator.create_orchestration_plan(test_content)
            print(f"✅ Plan created: {plan.plan_id}")
            print(f"   Strategy: {plan.optimization_strategy}")
            print(f"   Phases: {len(plan.execution_phases)}")

            for i, phase in enumerate(plan.execution_phases, 1):
                print(f"   Phase {i}: {', '.join(phase)}")

        except Exception as e:
            print(f"❌ Plan creation failed: {e}")
            import traceback

            traceback.print_exc()
            return False

        # Create initial state
        print("\n🏁 Creating Initial State...")
        state = orchestrator._create_initial_state(test_content)
        print(f"✅ Initial state created:")
        for key, value in state.items():
            if isinstance(value, str):
                value_preview = value[:50] + "..." if len(value) > 50 else value
            else:
                value_preview = str(value)
            print(f"   {key}: {value_preview}")

        # Try to execute first phase only
        print(f"\n🎯 Testing First Phase Execution...")
        if plan.execution_phases:
            first_phase = plan.execution_phases[0]
            print(f"   Executing: {', '.join(first_phase)}")

            try:
                # Execute just the content strategist
                if "ContentStrategistAgent" in first_phase:
                    print("\n📋 Testing Content Strategist Agent...")
                    agent = orchestrator.agents["ContentStrategistAgent"]
                    result = await agent.process(state.copy())

                    print(f"   Success: {result.success}")
                    if result.success:
                        print(f"   Data type: {type(result.data)}")
                        if hasattr(result.data, "learning_objectives"):
                            print(
                                f"   Learning objectives: {len(result.data.learning_objectives)}"
                            )
                        if hasattr(result.data, "content_chunks"):
                            print(
                                f"   Content chunks: {len(result.data.content_chunks)}"
                            )
                    else:
                        print(f"   Errors: {result.errors}")

                # Test Code Modification Agent with the results
                if "CodeModificationAgent" in orchestrator.agents:
                    print("\n🔧 Testing Code Modification Agent...")

                    # Update state with content strategy if available
                    if result.success and result.data:
                        state["content_strategy"] = result.data

                    code_agent = orchestrator.agents["CodeModificationAgent"]

                    # Enable more detailed debugging
                    import logging

                    logging.basicConfig(level=logging.INFO)

                    try:
                        code_result = await code_agent.process(state.copy())

                        print(f"   Success: {code_result.success}")
                        if code_result.success:
                            if hasattr(code_result.data, "modified_code"):
                                print(
                                    f"   Generated code length: {len(code_result.data.modified_code)}"
                                )
                                print(
                                    f"   Code preview: {code_result.data.modified_code[:200]}..."
                                )
                        else:
                            print(f"   Errors: {code_result.errors}")

                        # Check for debug files
                        import os

                        debug_files = [
                            "debug_claude_raw_response.txt",
                            "debug_syntax_error_code.py",
                        ]
                        for debug_file in debug_files:
                            if os.path.exists(debug_file):
                                print(f"   📄 Debug file created: {debug_file}")

                    except Exception as code_e:
                        print(f"❌ Code Modification Agent crashed: {code_e}")
                        import traceback

                        traceback.print_exc()

            except Exception as e:
                print(f"❌ Phase execution failed: {e}")
                import traceback

                traceback.print_exc()
                return False

        print("\n✅ Orchestration debugging completed!")
        return True

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(debug_orchestration())
    print(f"\n🏁 Debug Result: {'SUCCESS' if success else 'FAILED'}")
