#!/usr/bin/env python3
"""
Quick fix for the bottleneck_highlight error to demonstrate Error Surgeon capability.
"""


def fix_bottleneck_error():
    """Fix the bottleneck_highlight undefined variable error."""

    # Read the file
    with open("orchestrated_transformers_video.py", "r") as f:
        code = f.read()

    lines = code.split("\n")

    # Find the problematic lines
    for i, line in enumerate(lines):
        if (
            "bottleneck_highlight" in line
            and "Create(bottleneck_highlight)" in line
            and i < 60
        ):
            print(f"Found problematic line {i+1}: {line.strip()}")

            # Look for where bottleneck_highlight should be defined
            # Find the bottleneck_text definition line
            for j, search_line in enumerate(lines):
                if 'bottleneck_text = Text("Bottleneck Problem"' in search_line:
                    print(
                        f"Found bottleneck_text definition at line {j+1}: {search_line.strip()}"
                    )

                    # Create bottleneck_highlight definition
                    bottleneck_highlight_def = "        bottleneck_highlight = Circle(radius=0.3, color=RED).next_to(bottleneck_text, DOWN)"

                    # Insert the definition before the problematic line
                    lines.insert(i, bottleneck_highlight_def)

                    # Write the fixed code
                    fixed_code = "\n".join(lines)

                    with open("fixed_transformers_video.py", "w") as f:
                        f.write(fixed_code)

                    print(
                        f"✅ Fixed! Added bottleneck_highlight definition at line {i+1}"
                    )
                    print(f"💾 Saved fixed code to: fixed_transformers_video.py")
                    return True

    print("❌ Could not find the problematic pattern")
    return False


if __name__ == "__main__":
    fix_bottleneck_error()
