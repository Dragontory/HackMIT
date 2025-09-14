#!/usr/bin/env python3
"""
Iterative runtime error fixer that automatically handles all variable dependency issues.
"""

import re
import subprocess
import tempfile
import os


def extract_undefined_variable(error_output: str) -> str:
    """Extract the undefined variable name from error output."""

    # Check for IndentationError first - this means the fix itself has a problem
    if "IndentationError" in error_output:
        print("   ⚠️ IndentationError detected - skipping this iteration")
        return "INDENTATION_ERROR"

    # Look for NameError or UnboundLocalError patterns
    patterns = [
        r"NameError: name '(\w+)' is not defined",
        r"UnboundLocalError: cannot access local variable '(\w+)'",
    ]

    for pattern in patterns:
        match = re.search(pattern, error_output)
        if match:
            return match.group(1)

    return None


def find_variable_usage_and_definition(code: str, var_name: str):
    """Find where a variable is used and defined."""

    lines = code.split("\n")
    usage_lines = []
    definition_lines = []

    for i, line in enumerate(lines):
        if var_name in line and not line.strip().startswith("#"):
            # Check if this is a usage (not an assignment)
            if f"{var_name} = " in line:
                definition_lines.append((i, line.strip()))
            else:
                usage_lines.append((i, line.strip()))

    return usage_lines, definition_lines


def fix_undefined_variable(code: str, var_name: str) -> str:
    """Fix an undefined variable by adding an appropriate definition."""

    lines = code.split("\n")
    usage_lines, definition_lines = find_variable_usage_and_definition(code, var_name)

    if not usage_lines:
        print(f"   ⚠️ No usage found for {var_name}")
        return code

    print(
        f"   📍 Found {len(usage_lines)} usage(s) and {len(definition_lines)} definition(s)"
    )

    # If there are definitions but used before defined, move the definition
    if definition_lines:
        first_usage_line = min(usage_lines, key=lambda x: x[0])[0]
        first_definition_line = min(definition_lines, key=lambda x: x[0])[0]

        if first_usage_line < first_definition_line:
            print(
                f"   🔄 Moving definition from line {first_definition_line + 1} to before line {first_usage_line + 1}"
            )

            # Remove the definition line
            definition_content = lines[first_definition_line]
            lines.pop(first_definition_line)

            # Insert it before the first usage (adjust index due to removal)
            insert_position = (
                first_usage_line
                if first_usage_line < first_definition_line
                else first_usage_line - 1
            )
            lines.insert(insert_position, definition_content)

            return "\n".join(lines)

    # If no definition exists, create one
    first_usage_line, first_usage_content = min(usage_lines, key=lambda x: x[0])

    # Get the line before the usage for proper indentation context
    context_line = (
        lines[first_usage_line]
        if first_usage_line < len(lines)
        else first_usage_content
    )

    # Analyze the usage to create an appropriate definition
    definition = create_variable_definition(var_name, first_usage_content, context_line)

    print(f"   ✅ Creating definition: {definition}")

    # Insert the definition before the first usage
    lines.insert(first_usage_line, definition)

    return "\n".join(lines)


def create_variable_definition(
    var_name: str, usage_context: str, insertion_line: str = None
) -> str:
    """Create an appropriate variable definition based on usage context."""

    # Get the proper indentation from the insertion context or usage line
    if insertion_line:
        indent = len(insertion_line) - len(insertion_line.lstrip())
    else:
        indent = len(usage_context) - len(usage_context.lstrip())
    indent_str = " " * indent

    # Specific patterns for known variables
    if "title" in var_name.lower():
        return f'{indent_str}{var_name} = Text("{var_name.replace("_", " ").title()}", font_size=32, color=BLUE)'

    elif "highlight" in var_name.lower():
        return f"{indent_str}{var_name} = Circle(radius=0.8, color=RED, stroke_width=3)"

    elif "arrow" in var_name.lower():
        return f"{indent_str}{var_name} = Arrow(LEFT, RIGHT, color=YELLOW)"

    elif "text" in var_name.lower():
        return f'{indent_str}{var_name} = Text("{var_name.replace("_", " ").title()}", font_size=24)'

    elif "label" in var_name.lower():
        return f'{indent_str}{var_name} = Text("{var_name.replace("_", " ").title()}", font_size=20)'

    elif "box" in var_name.lower() or "rect" in var_name.lower():
        return f"{indent_str}{var_name} = Rectangle(width=2, height=1, color=WHITE)"

    elif "line" in var_name.lower():
        return f"{indent_str}{var_name} = Line(ORIGIN, UP, color=WHITE)"

    else:
        # Generic object based on usage
        if "Write(" in usage_context:
            return f'{indent_str}{var_name} = Text("{var_name.replace("_", " ").title()}", font_size=24)'
        elif "Create(" in usage_context:
            return f"{indent_str}{var_name} = Circle(radius=0.5, color=BLUE)"
        else:
            return f"{indent_str}{var_name} = VGroup()  # Define as needed"


def test_manim_code(
    code: str, class_name: str, filename: str = None
) -> tuple[bool, str]:
    """Test Manim code and capture any runtime errors."""

    try:
        if filename:
            temp_file = filename
            with open(temp_file, "w") as f:
                f.write(code)
        else:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_file = f.name

        # Run manim with the code
        cmd = [
            "conda",
            "run",
            "-n",
            "crawler_Env",
            "manim",
            temp_file,
            class_name,
            "-pql",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Clean up temporary file only
        if not filename:
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


def iterative_fix_errors(
    code: str, class_name: str, max_iterations: int = 10
) -> tuple[str, bool]:
    """Iteratively fix runtime errors in Manim code."""

    current_code = code
    iteration = 0

    print(f"🔧 Starting iterative error correction for {class_name}")
    print(f"📄 Initial code length: {len(current_code)} characters")

    while iteration < max_iterations:
        iteration += 1
        print(f"\n🔄 Iteration {iteration}/{max_iterations}")

        # Test the current code
        success, error_output = test_manim_code(
            current_code, class_name, f"iteration_{iteration}_test.py"
        )

        if success:
            print(f"✅ Code runs successfully after {iteration-1} fixes!")
            return current_code, True

        # Extract the undefined variable
        undefined_var = extract_undefined_variable(error_output)

        if not undefined_var:
            print(f"❌ Could not extract undefined variable from error")
            print(f"   Error output: {error_output[:300]}...")
            break

        if undefined_var == "INDENTATION_ERROR":
            print(f"🔧 Fixing indentation error by reverting to previous iteration")
            # Try to continue with the previous iteration's code
            try:
                with open(f"iteration_{iteration-1}_fixed.py", "r") as f:
                    current_code = f.read()
                continue
            except:
                print(f"❌ Could not revert to previous iteration")
                break

        print(f"🔍 Found undefined variable: {undefined_var}")

        # Apply the fix
        try:
            fixed_code = fix_undefined_variable(current_code, undefined_var)

            if fixed_code == current_code:
                print(f"❌ No changes made - fix failed")
                break

            current_code = fixed_code
            print(f"✅ Applied fix for {undefined_var}")

            # Save intermediate result
            with open(f"iteration_{iteration}_fixed.py", "w") as f:
                f.write(current_code)
            print(f"💾 Saved to: iteration_{iteration}_fixed.py")

        except Exception as e:
            print(f"❌ Failed to apply fix: {e}")
            break

    print(f"\n⚠️ Could not fix all errors after {max_iterations} iterations")
    return current_code, False


def main():
    """Main function to iteratively fix the transformers video."""

    # Read the original generated code
    try:
        with open("orchestrated_transformers_video.py", "r") as f:
            code = f.read()
    except FileNotFoundError:
        print("❌ orchestrated_transformers_video.py not found")
        return

    # Extract class name
    class_match = re.search(r"class\s+(\w+)\s*\(Scene\)", code)
    if not class_match:
        print("❌ Could not find Scene class in the code")
        return

    class_name = class_match.group(1)
    print(f"🎯 Found Scene class: {class_name}")

    # Apply iterative fixes
    fixed_code, success = iterative_fix_errors(code, class_name)

    if success:
        # Save the final result
        with open("fully_fixed_transformers.py", "w") as f:
            f.write(fixed_code)

        print(f"\n🎉 SUCCESS!")
        print(f"💾 Fully fixed code saved to: fully_fixed_transformers.py")
        print(f"📊 Final code length: {len(fixed_code)} characters")

        print(f"\n🎬 To render the final video:")
        print(f"   conda activate crawler_Env")
        print(f"   manim fully_fixed_transformers.py {class_name} -pql")

    else:
        # Save partial result
        with open("partially_fixed_transformers.py", "w") as f:
            f.write(fixed_code)

        print(f"\n⚠️ Partial success - some errors remain")
        print(f"💾 Partially fixed code saved to: partially_fixed_transformers.py")
        print(f"📊 Partial code length: {len(fixed_code)} characters")


if __name__ == "__main__":
    main()
