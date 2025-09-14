#!/usr/bin/env python3
"""
Direct fix for the bottleneck_highlight error without complex parsing.
"""

import re


def fix_bottleneck_error():
    """Fix the bottleneck_highlight undefined variable error directly."""

    # Read the problematic code
    with open("orchestrated_transformers_video.py", "r") as f:
        code = f.read()

    print("🔧 Applying direct fix for bottleneck_highlight error")
    print("=" * 60)

    lines = code.split("\n")

    # Find the first usage of bottleneck_highlight
    first_usage_line = None
    for i, line in enumerate(lines):
        if "bottleneck_highlight" in line and "Create(bottleneck_highlight)" in line:
            first_usage_line = i
            print(f"📍 Found first usage at line {i + 1}: {line.strip()}")
            break

    if first_usage_line is None:
        print("❌ Could not find bottleneck_highlight usage")
        return False

    # Insert the definition before the first usage
    definition = (
        "        bottleneck_highlight = Circle(radius=0.8, color=RED, stroke_width=3)"
    )
    lines.insert(first_usage_line, definition)

    print(f"✅ Inserted definition: {definition}")

    # Check if bottleneck_text is defined after it's used
    bottleneck_text_usage = None
    bottleneck_text_definition = None

    for i, line in enumerate(lines):
        if "bottleneck_text" in line:
            if "Write(bottleneck_text)" in line and bottleneck_text_usage is None:
                bottleneck_text_usage = i + 1
                print(f"📍 Found bottleneck_text usage at line {i + 1}")
            elif "bottleneck_text = Text(" in line:
                bottleneck_text_definition = i + 1
                print(f"📍 Found bottleneck_text definition at line {i + 1}")

    # If bottleneck_text is used before it's defined, move the definition
    if (
        bottleneck_text_usage
        and bottleneck_text_definition
        and bottleneck_text_usage < bottleneck_text_definition
    ):
        print(
            f"⚠️ bottleneck_text used before definition (line {bottleneck_text_usage} vs {bottleneck_text_definition})"
        )

        # Find the definition line and move it before the usage
        for i, line in enumerate(lines):
            if "bottleneck_text = Text(" in line and "Bottleneck" in line:
                # Remove the definition from its current location
                definition_line = lines.pop(i)
                # Insert it before the usage (accounting for the removal)
                insert_position = (
                    bottleneck_text_usage - 2
                    if bottleneck_text_usage > i
                    else bottleneck_text_usage - 1
                )
                lines.insert(insert_position, definition_line)
                print(
                    f"✅ Moved bottleneck_text definition to line {insert_position + 1}"
                )
                break

    # Write the fixed code
    fixed_code = "\n".join(lines)

    with open("direct_fixed_transformers.py", "w") as f:
        f.write(fixed_code)

    print(f"\n🎉 SUCCESS!")
    print(f"💾 Fixed code saved to: direct_fixed_transformers.py")
    print(f"📊 Fixed code length: {len(fixed_code)} characters")

    return True


if __name__ == "__main__":
    success = fix_bottleneck_error()
    if success:
        print(f"\n🧪 To test the fix:")
        print(f"   conda activate crawler_Env")
        print(f"   manim direct_fixed_transformers.py AttentionMechanismsInNMT -pql")
