#!/usr/bin/env python3
"""
Continue iterative fixing from the last successful iteration.
"""

import re
from iterative_error_fixer import iterative_fix_errors


def main():
    """Continue fixing from iteration 5."""

    # Start from the last successful iteration
    try:
        with open("iteration_5_fixed.py", "r") as f:
            code = f.read()
        print("🔄 Continuing from iteration_5_fixed.py")
    except FileNotFoundError:
        print("❌ iteration_5_fixed.py not found")
        return

    # Extract class name
    class_match = re.search(r"class\s+(\w+)\s*\(Scene\)", code)
    if not class_match:
        print("❌ Could not find Scene class in the code")
        return

    class_name = class_match.group(1)
    print(f"🎯 Found Scene class: {class_name}")

    # Continue with more iterations
    fixed_code, success = iterative_fix_errors(code, class_name, max_iterations=10)

    if success:
        # Save the final result
        with open("completely_fixed_transformers.py", "w") as f:
            f.write(fixed_code)

        print(f"\n🎉 COMPLETE SUCCESS!")
        print(f"💾 Completely fixed code saved to: completely_fixed_transformers.py")
        print(f"📊 Final code length: {len(fixed_code)} characters")

        print(f"\n🎬 To render the final video:")
        print(f"   conda activate crawler_Env")
        print(f"   manim completely_fixed_transformers.py {class_name} -pql")

    else:
        # Save partial result
        with open("extended_fixed_transformers.py", "w") as f:
            f.write(fixed_code)

        print(f"\n⚠️ Extended partial success")
        print(f"💾 Extended fixed code saved to: extended_fixed_transformers.py")
        print(f"📊 Extended code length: {len(fixed_code)} characters")


if __name__ == "__main__":
    main()
