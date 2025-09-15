#!/usr/bin/env python3
"""
Debug the Error Surgeon Agent directly with the NameError.
"""

import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents_system.infrastructure.config import AgentConfig
from agents_system.infrastructure.anthropic.client import AnthropicClient
from agents_system.core.agents.error_surgeon import ErrorSurgeonAgent


async def debug_error_surgeon():
    """Debug the Error Surgeon Agent with the specific NameError."""

    config = AgentConfig.from_env()
    claude_client = AnthropicClient(config.anthropic)
    error_surgeon = ErrorSurgeonAgent(claude_client)

    # Read the problematic code
    with open("orchestrated_transformers_video.py", "r") as f:
        code = f.read()

    # Define the specific error
    error_log = """NameError: name 'bottleneck_highlight' is not defined

The error occurs on line 57:
self.play(Create(bottleneck_highlight), Write(bottleneck_text))

The variable 'bottleneck_highlight' is used before it's defined.
Looking at the code, 'bottleneck_text' is defined on line 59, but 'bottleneck_highlight' is never defined.
"""

    print("🔧 Testing Error Surgeon Agent directly")
    print("=" * 60)
    print(f"📄 Code length: {len(code)}")
    print(f"❌ Error: {error_log.split('on line')[0].strip()}")

    try:
        # Test the error diagnosis first
        print("\n🔍 Step 1: Diagnosing errors...")
        diagnoses = await error_surgeon.diagnose_errors(code, error_log)

        print(f"   Found {len(diagnoses)} error diagnoses:")
        for i, diagnosis in enumerate(diagnoses, 1):
            print(f"   {i}. {diagnosis.error_type}: {diagnosis.error_message}")
            print(f"      Location: {diagnosis.error_location}")
            print(f"      Severity: {diagnosis.severity}")
            print(f"      Root cause: {diagnosis.root_cause}")
            if diagnosis.suggested_fix:
                print(f"      Suggested fix: {diagnosis.suggested_fix}")

        if not diagnoses:
            print("   ❌ No errors diagnosed!")
            return

        # Test fix generation
        print(f"\n🔧 Step 2: Generating fixes for {len(diagnoses)} diagnosis(es)...")
        all_fixes = []

        for i, diagnosis in enumerate(diagnoses, 1):
            print(f"   Generating fixes for diagnosis {i}...")
            fixes = await error_surgeon.generate_fixes(code, diagnosis)
            all_fixes.extend(fixes)
            print(f"   Generated {len(fixes)} fixes")

            for j, fix in enumerate(fixes, 1):
                print(f"      Fix {j}: {fix.fix_description}")
                print(f"      Type: {fix.fix_type}")
                print(f"      Confidence: {fix.confidence}")

        if not all_fixes:
            print("   ❌ No fixes generated!")
            return

        # Test fix application
        print(f"\n⚡ Step 3: Applying {len(all_fixes)} fix(es)...")
        fixed_code = code
        applied_fixes = []

        for i, fix in enumerate(all_fixes, 1):
            print(f"   Applying fix {i}: {fix.fix_description}")
            try:
                fixed_code = error_surgeon._apply_fix(fixed_code, fix)
                applied_fixes.append(fix)
                print(f"   ✅ Applied successfully")
            except Exception as e:
                print(f"   ❌ Failed to apply: {e}")

        # Save the result
        if applied_fixes:
            with open("debug_fixed_transformers.py", "w") as f:
                f.write(fixed_code)

            print(f"\n🎉 SUCCESS!")
            print(f"✅ Applied {len(applied_fixes)} fixes")
            print(f"💾 Fixed code saved to: debug_fixed_transformers.py")
            print(f"📊 Fixed code length: {len(fixed_code)}")

            # Show the difference
            print(f"\n📋 Changes made:")
            for fix in applied_fixes:
                print(f"   • {fix.fix_description}")
        else:
            print(f"\n❌ No fixes were successfully applied")

    except Exception as e:
        print(f"❌ Error Surgeon debugging failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_error_surgeon())
