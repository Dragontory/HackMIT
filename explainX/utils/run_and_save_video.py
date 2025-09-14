#!/usr/bin/env python3
"""
Run the orchestration and properly save the generated video.
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


async def run_and_save():
    try:
        # Load config and initialize client
        config = AgentConfig.from_env()
        claude_client = AnthropicClient(config.anthropic)

        # Initialize the Integration Orchestrator
        orchestrator = IntegrationOrchestratorAgent(claude_client)

        # Read the Transformers content
        with open("testfile.txt", "r") as f:
            content = f.read()

        print("🚀 Running Multi-Agent Pipeline and Saving Video...")
        print(f"📄 Content length: {len(content)} characters")
        print("=" * 80)

        # Run the orchestration
        result = await orchestrator.orchestrate_agents(content)

        print(f"\n📊 RESULT SUMMARY:")
        print(f"   Success: {result.success}")
        print(f"   Agents Executed: {result.agents_executed}")
        print(f"   Success Rate: {result.success_rate:.1%}")

        # Check and save the final output
        if result.final_output:
            print(f"\n✅ Generated code: {len(result.final_output)} characters")

            # Save the generated code
            with open("orchestrated_transformers_video.py", "w") as f:
                f.write(result.final_output)
            print(f"💾 Saved to: orchestrated_transformers_video.py")

            # Test syntax
            try:
                compile(result.final_output, "<string>", "exec")
                print("✅ Generated code has valid syntax!")
            except SyntaxError as e:
                print(f"⚠️ Syntax issue: {e}")

            # Show preview
            print(f"\n📺 PREVIEW (first 500 chars):")
            print("-" * 50)
            print(result.final_output[:500])
            print("..." if len(result.final_output) > 500 else "")
            print("-" * 50)

            return True
        else:
            print("❌ No final output generated")

            # Check intermediate results
            print("\n🔍 Checking intermediate results...")

            # Check if code modification result exists
            if hasattr(result, "code_modifications") and result.code_modifications:
                print(f"✅ Found code modifications: {len(result.code_modifications)}")

            # Look for any manim code in the state or execution results
            for execution in result.agent_executions:
                if (
                    execution.agent_name == "CodeModificationAgent"
                    and execution.success
                ):
                    if execution.metadata and "result_data" in execution.metadata:
                        code_data = execution.metadata["result_data"]
                        if (
                            hasattr(code_data, "modified_code")
                            and code_data.modified_code
                        ):
                            print(
                                f"✅ Found code in {execution.agent_name}: {len(code_data.modified_code)} chars"
                            )

                            # Save this code instead
                            with open("orchestrated_transformers_video.py", "w") as f:
                                f.write(code_data.modified_code)
                            print(
                                f"💾 Saved from {execution.agent_name} to: orchestrated_transformers_video.py"
                            )

                            return True

            return False

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_and_save())
    print(f'\n🏁 Final Result: {"SUCCESS - Video Ready!" if success else "FAILED"}')
