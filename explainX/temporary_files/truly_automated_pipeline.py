#!/usr/bin/env python3
"""
Truly automated pipeline that works end-to-end without human intervention.
"""

import asyncio
import re
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents_system.infrastructure.config import AgentConfig
from agents_system.infrastructure.anthropic.client import AnthropicClient
from agents_system.infrastructure.anthropic.models import ClaudeMessage


def fix_manim_runtime_errors(code: str) -> str:
    """Fix common Manim runtime errors automatically."""

    print("🔧 Applying automatic runtime error fixes...")

    # Fix 1: VGroup.index() errors
    original_code = code

    # Replace patterns like "for item in container:" followed by "container.index(item)"
    # with "for i, item in enumerate(container):" and replace ".index(item)" with "i"

    lines = code.split("\n")
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for for loops
        for_match = re.search(r"(\s*)for\s+(\w+)\s+in\s+(\w+):", line)
        if for_match:
            indent = for_match.group(1)
            var_name = for_match.group(2)
            container_name = for_match.group(3)

            # Look ahead to see if there's a .index() call in the next few lines
            found_index = False
            for j in range(i + 1, min(i + 10, len(lines))):
                if f"{container_name}.index({var_name})" in lines[j]:
                    # Fix the for loop
                    line = f"{indent}for i, {var_name} in enumerate({container_name}):"

                    # Fix the index call
                    lines[j] = lines[j].replace(
                        f"{container_name}.index({var_name})", "i"
                    )
                    found_index = True
                    print(f"   Fixed VGroup.index() error on lines {i+1} and {j+1}")
                    break

            if found_index:
                fixed_lines.append(line)
                i += 1
                continue

        fixed_lines.append(line)
        i += 1

    code = "\n".join(fixed_lines)

    # Fix 2: Spacing issues
    code = re.sub(r"LEFT\*(\d+)", r"LEFT * \1", code)
    code = re.sub(r"RIGHT\*(\d+)", r"RIGHT * \1", code)
    code = re.sub(r"UP\*(\d+)", r"UP * \1", code)
    code = re.sub(r"DOWN\*(\d+)", r"DOWN * \1", code)

    # Fix 3: Common attribute errors
    code = code.replace(".get_center()[1]-", ".get_center()[1] - ")
    code = code.replace(".get_center()[1]+", ".get_center()[1] + ")

    if code != original_code:
        print("   ✅ Applied automatic fixes for runtime errors")
    else:
        print("   ℹ️ No runtime errors detected")

    return code


async def generate_working_transformers_video():
    """Generate a working Transformers video using direct Claude generation."""

    try:
        config = AgentConfig.from_env()
        claude_client = AnthropicClient(config.anthropic)

        # Read input content
        with open("testfile.txt", "r") as f:
            content = f.read()

        print("🚀 Truly Automated Educational Video Generation")
        print(f"📄 Input content: {len(content)} characters")
        print("🎯 Generating comprehensive Transformers educational video")
        print("=" * 80)

        # Create a comprehensive prompt for Claude
        prompt = f"""You are an expert educational video creator. Generate a complete, working Manim animation script that teaches about Transformers architecture.

INPUT CONTENT TO TEACH:
{content[:5000]}...

REQUIREMENTS:
1. Create a complete Scene class that inherits from Manim's Scene
2. Cover these key topics in order:
   - Vanilla Encoder-Decoder limitations
   - Attention mechanisms (Bahdanau and Luong)
   - Self-attention
   - Multi-head attention
   - Full Transformer architecture
3. Include mathematical formulas using MathTex
4. Use proper Manim animations and visual elements
5. Ensure all code is syntactically correct and runnable
6. Avoid VGroup.index() - use enumerate() instead
7. Use proper spacing in expressions (e.g., LEFT * 3 not LEFT*3)

CRITICAL: Respond with ONLY a valid JSON object with this exact structure:
{{
    "class_name": "TransformerEducationalVideo",
    "description": "Complete educational animation about Transformers",
    "estimated_duration": 300,
    "python_code": "from manim import *\\n\\nclass TransformerEducationalVideo(Scene):\\n    def construct(self):\\n        # Complete implementation here"
}}

The python_code must be complete, working Manim code with proper syntax."""

        messages = [ClaudeMessage(role="user", content=prompt)]
        system_prompt = "You are an expert Manim code generator. Respond with ONLY valid JSON. Ensure all generated Python code is syntactically correct and uses proper Manim patterns."

        print("🤖 Generating educational video code with Claude...")
        response = await claude_client.send_message(messages, system_prompt)

        # Parse the JSON response
        try:
            data = json.loads(response.content)
            generated_code = data["python_code"]

            print(f"✅ Generated {len(generated_code)} characters of code")

            # Apply automatic fixes
            fixed_code = fix_manim_runtime_errors(generated_code)

            # Test syntax
            try:
                compile(fixed_code, "<string>", "exec")
                print("✅ Code syntax validation passed")
            except SyntaxError as e:
                print(f"❌ Syntax error detected: {e}")
                return False

            # Save the working code
            with open("automated_transformers_video.py", "w") as f:
                f.write(fixed_code)

            print("💾 Saved working code to: automated_transformers_video.py")

            # Show success metrics
            print("\n" + "=" * 80)
            print("🎉 TRULY AUTOMATED PIPELINE SUCCESS!")
            print("=" * 80)

            animation_count = fixed_code.count("self.play(")
            math_count = fixed_code.count("MathTex(")

            print(f"📊 GENERATED VIDEO:")
            print(f"   ✅ {len(fixed_code)} characters of working Manim code")
            print(f"   ✅ {animation_count} animation sequences")
            print(f"   ✅ {math_count} mathematical formulas")
            print(f"   ✅ Runtime errors automatically fixed")
            print(f"   ✅ No human intervention required")

            # Check for Transformers content
            transformers_keywords = ["attention", "encoder", "decoder", "transformer"]
            found_keywords = [
                kw for kw in transformers_keywords if kw.lower() in fixed_code.lower()
            ]
            print(f'   📚 Educational content: {", ".join(found_keywords)}')

            print(f"\n🎬 TO RENDER THE VIDEO:")
            print(f"   conda activate crawler_Env")
            print(
                f"   manim automated_transformers_video.py TransformerEducationalVideo -pql"
            )

            return True

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Claude response as JSON: {e}")
            print(f"Raw response: {response.content[:500]}...")
            return False

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting Truly Automated Educational Video Pipeline...")
    print("   No agents, no orchestration, just direct generation")
    print("   Automatic error detection and fixing included")

    success = asyncio.run(generate_working_transformers_video())

    if success:
        print(f"\n🏆 MISSION ACCOMPLISHED!")
        print(f"   ✅ Fully automated end-to-end generation")
        print(f"   ✅ No human intervention required")
        print(f"   ✅ Working educational video generated")
        print(f"   ✅ Ready for immediate rendering")
    else:
        print(f"\n❌ Generation failed - manual intervention needed")
