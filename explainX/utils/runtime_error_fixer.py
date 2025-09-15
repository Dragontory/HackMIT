#!/usr/bin/env python3
"""
Runtime Error Detection and Correction System

This script runs Manim code, captures runtime errors, and uses the Error Surgeon Agent
to automatically fix them, creating a feedback loop for automatic error correction.
"""

import asyncio
import subprocess
import re
import tempfile
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents_system.infrastructure.config import AgentConfig
from agents_system.infrastructure.anthropic.client import AnthropicClient
from agents_system.core.agents.error_surgeon import ErrorSurgeonAgent


async def test_manim_code(code: str, class_name: str) -> tuple[bool, str]:
    """Test Manim code and capture any runtime errors."""

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = f.name

        # Run manim with the code - use correct flags
        cmd = [
            "conda",
            "run",
            "-n",
            "crawler_Env",
            "manim",
            temp_file,
            class_name,
            "-pql",  # preview, quality low
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30  # Shorter timeout
        )

        # Clean up
        os.unlink(temp_file)

        # Combine stdout and stderr for complete error context
        full_output = f"{result.stdout}\n{result.stderr}".strip()

        if result.returncode == 0:
            return True, ""
        else:
            return False, full_output

    except subprocess.TimeoutExpired:
        return False, "Timeout: Code execution took too long"
    except Exception as e:
        return False, f"Error running code: {str(e)}"


async def fix_runtime_errors(
    code: str, class_name: str, max_iterations: int = 3
) -> tuple[str, bool]:
    """Fix runtime errors in Manim code using Error Surgeon Agent."""

    config = AgentConfig.from_env()
    claude_client = AnthropicClient(config.anthropic)
    error_surgeon = ErrorSurgeonAgent(claude_client)

    current_code = code
    iteration = 0

    print(f"🔧 Starting runtime error correction for {class_name}")
    print(f"📄 Initial code length: {len(current_code)} characters")

    while iteration < max_iterations:
        iteration += 1
        print(f"\n🔄 Iteration {iteration}/{max_iterations}")

        # Test the current code
        success, error_output = await test_manim_code(current_code, class_name)

        if success:
            print(f"✅ Code runs successfully after {iteration-1} fixes!")
            return current_code, True

        print(f"❌ Runtime error detected:")
        # Show more error context for debugging
        print(f"   Full error (first 500 chars): {error_output[:500]}...")

        # Extract the actual error message for the surgeon
        error_lines = error_output.split("\n")
        key_error = ""

        # Look for specific error types
        for line in error_lines:
            if any(
                error_type in line
                for error_type in [
                    "NameError:",
                    "UnboundLocalError:",
                    "AttributeError:",
                    "TypeError:",
                ]
            ):
                key_error = line.strip()
                break

        if not key_error:
            # Fallback to looking for generic patterns
            for line in error_lines:
                if "Error:" in line or "Exception:" in line:
                    key_error = line.strip()
                    break

        print(f"   Key error: {key_error}")

        # Save full error log for debugging
        with open(f"error_log_iteration_{iteration}.txt", "w") as f:
            f.write(error_output)
        print(f"   📄 Full error saved to: error_log_iteration_{iteration}.txt")

        # Use Error Surgeon Agent to fix the error
        try:
            print(f"🏥 Applying Error Surgeon Agent...")
            surgery_result = await error_surgeon.fix_errors(current_code, error_output)

            if surgery_result.success and surgery_result.fixed_code:
                current_code = surgery_result.fixed_code
                print(f"✅ Applied {len(surgery_result.applied_fixes)} fixes")

                # Show what was fixed
                for fix in surgery_result.applied_fixes:
                    print(f"   🔧 {fix.fix_description}")

            else:
                print(f"❌ Error Surgeon could not fix the error")
                break

        except Exception as e:
            print(f"❌ Error Surgeon failed: {e}")
            break

    print(f"\n⚠️ Could not fix all errors after {max_iterations} iterations")
    return current_code, False


async def main():
    """Main function to test and fix the orchestrated video."""

    # Read the generated code
    try:
        with open("orchestrated_transformers_video.py", "r") as f:
            code = f.read()
    except FileNotFoundError:
        print("❌ orchestrated_transformers_video.py not found")
        print("   Run the orchestration first: python run_and_save_video.py")
        return

    # Extract class name from code
    class_match = re.search(r"class\s+(\w+)\s*\(Scene\)", code)
    if not class_match:
        print("❌ Could not find Scene class in the code")
        return

    class_name = class_match.group(1)
    print(f"🎯 Found Scene class: {class_name}")

    # Test and fix runtime errors
    fixed_code, success = await fix_runtime_errors(code, class_name)

    if success:
        # Save the fixed code
        with open("fixed_transformers_video.py", "w") as f:
            f.write(fixed_code)

        print(f"\n🎉 SUCCESS!")
        print(f"💾 Fixed code saved to: fixed_transformers_video.py")
        print(f"📊 Final code length: {len(fixed_code)} characters")

        # Test the final code one more time
        print(f"\n🧪 Final validation test...")
        final_success, final_error = await test_manim_code(fixed_code, class_name)

        if final_success:
            print(f"✅ Final validation passed!")
            print(f"\n🎬 To render the video:")
            print(f"   conda activate crawler_Env")
            print(f"   manim fixed_transformers_video.py {class_name} -pql")
        else:
            print(f"❌ Final validation failed: {final_error}")

    else:
        print(f"\n❌ Could not automatically fix all runtime errors")
        print(f"📄 Partially fixed code length: {len(fixed_code)} characters")

        # Save partial fix anyway
        with open("partially_fixed_transformers_video.py", "w") as f:
            f.write(fixed_code)
        print(
            f"💾 Partially fixed code saved to: partially_fixed_transformers_video.py"
        )


if __name__ == "__main__":
    asyncio.run(main())
