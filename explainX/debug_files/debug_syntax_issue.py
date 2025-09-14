#!/usr/bin/env python3
"""
Debug the specific syntax error in generated code.
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


async def debug_syntax_error():
    try:
        # Load config and initialize client
        config = AgentConfig.from_env()
        claude_client = AnthropicClient(config.anthropic)

        # Initialize the Integration Orchestrator
        orchestrator = IntegrationOrchestratorAgent(claude_client)

        # Load Transformers content
        with open("testfile.txt", "r") as f:
            content = f.read()

        print("🔍 Debugging Syntax Error in Generated Code...")
        print(f"📄 Content length: {len(content)} characters")
        print("=" * 70)

        # Run orchestration but catch and save problematic code
        try:
            result = await orchestrator.orchestrate_agents(content)

            if result.success:
                print(f"✅ Pipeline completed successfully!")
                final_code = result.final_output

                # Save successful code
                with open("successful_transformers_code.py", "w") as f:
                    f.write(final_code)
                print("💾 Saved successful code to: successful_transformers_code.py")

                return True
            else:
                print(f"❌ Pipeline failed: {result.errors}")
                return False

        except Exception as e:
            error_msg = str(e)
            print(f"🚨 Exception during orchestration: {error_msg}")

            # If it's a syntax error, try to extract and save the problematic code
            if (
                "syntax error" in error_msg.lower()
                or "invalid syntax" in error_msg.lower()
            ):
                print(
                    "🔍 Syntax error detected, attempting to capture problematic code..."
                )

                # Try to get partial results from the orchestrator's state
                # This is a debug approach to see what was generated
                try:
                    # Run just the first few agents to get the generated code
                    from agents_system.core.agents.content_strategist import (
                        ContentStrategistAgent,
                    )
                    from agents_system.core.agents.code_modifier import (
                        CodeModificationAgent,
                    )

                    content_agent = ContentStrategistAgent(claude_client)
                    code_agent = CodeModificationAgent(claude_client)

                    # Get content strategy
                    print("📝 Getting content strategy...")
                    strategy_state = {
                        "raw_content": content,
                        "content_title": "Introduction to Transformers Architecture",
                    }
                    strategy_result = await content_agent.process(strategy_state)

                    if strategy_result.success:
                        print("✅ Content strategy generated")

                        # Generate code
                        print("🔧 Generating Manim code...")
                        code_state = {
                            "raw_content": content,
                            "content_title": "Introduction to Transformers Architecture",
                            "content_strategy": strategy_result.data,
                            "manim_code": "",  # Empty to trigger generation
                        }

                        code_result = await code_agent.process(code_state)

                        if code_result.success:
                            generated_code = code_result.data.modified_code
                            print(f"✅ Generated {len(generated_code)} characters")

                            # Save for inspection
                            with open("problematic_generated_code.py", "w") as f:
                                f.write(generated_code)
                            print(
                                "💾 Saved problematic code to: problematic_generated_code.py"
                            )

                            # Test syntax line by line
                            print("🔍 Testing syntax...")
                            try:
                                compile(generated_code, "<string>", "exec")
                                print("✅ Code has valid syntax!")
                            except SyntaxError as syntax_err:
                                print(
                                    f"❌ Syntax error at line {syntax_err.lineno}: {syntax_err.msg}"
                                )

                                lines = generated_code.split("\n")
                                if syntax_err.lineno and syntax_err.lineno <= len(
                                    lines
                                ):
                                    start_line = max(0, syntax_err.lineno - 5)
                                    end_line = min(len(lines), syntax_err.lineno + 5)

                                    print(
                                        f"\n📍 Code around error (lines {start_line+1}-{end_line}):"
                                    )
                                    print("-" * 60)
                                    for i in range(start_line, end_line):
                                        marker = (
                                            ">>>"
                                            if i == syntax_err.lineno - 1
                                            else "   "
                                        )
                                        print(f"{marker} {i+1:3d}: {lines[i]}")
                                    print("-" * 60)

                                return False
                        else:
                            print(f"❌ Code generation failed: {code_result.errors}")
                    else:
                        print(f"❌ Content strategy failed: {strategy_result.errors}")

                except Exception as debug_e:
                    print(f"❌ Debug extraction failed: {debug_e}")

            return False

    except Exception as e:
        print(f"❌ Major error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting Syntax Error Debug Session...")
    success = asyncio.run(debug_syntax_error())
    print(f'\n🏁 Debug Result: {"SUCCESS" if success else "IDENTIFIED ISSUE"}')
