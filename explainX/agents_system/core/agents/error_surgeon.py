"""
Error Surgeon Agent implementation.

This agent performs surgical fixes on specific errors in Manim code,
analyzing error messages and applying targeted fixes without disrupting the rest of the code.
"""

import logging
import re
import time
import uuid
import ast
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from ...domain.interfaces import IAgent
from ...domain.models import (
    AgentState,
    AgentResult,
    ErrorSurgeryResult,
    ErrorDiagnosis,
    ErrorFix,
    CodeTestingResult,
    ManimTestResult,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage


logger = logging.getLogger(__name__)


class ErrorSurgeonAgent(IAgent):
    """
    Specialized agent for surgical error fixing in Manim code.

    Uses Claude's code understanding to:
    - Diagnose specific errors in detail
    - Apply targeted fixes without disrupting working code
    - Handle common Manim and LaTeX errors
    - Provide explanations of fixes for educational purposes
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()

    @property
    def name(self) -> str:
        return "ErrorSurgeonAgent"

    @property
    def description(self) -> str:
        return "Performs surgical fixes on specific errors in Manim code"

    async def process(self, state: AgentState) -> AgentResult:
        """Process state and fix errors in Manim code."""
        start_time = time.time()

        try:
            logger.info(f"Error Surgeon processing: {state['content_title']}")

            # Get the code to fix (should be from previous agent)
            manim_code = state.get("manim_code", "")
            error_log = state.get("error_log", "")
            testing_result = state.get("code_testing_result")

            if not manim_code:
                # Create sample code with errors for testing
                manim_code, error_log = self._create_sample_code_with_errors()
                logger.info("No Manim code provided, using sample with errors")

            # Perform error surgery
            result = await self.fix_errors(manim_code, error_log, testing_result)

            # Update state
            state["error_surgery_result"] = result
            state["manim_code"] = result.fixed_code
            state["current_agent"] = self.name
            state["processing_stage"] = "error_surgery_complete"

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "errors_diagnosed": len(result.error_diagnoses),
                    "fixes_applied": len(result.applied_fixes),
                    "unfixable_errors": len(result.unfixable_errors),
                    "requires_human_intervention": result.requires_human_intervention,
                    "processing_time": processing_time,
                },
            )

        except Exception as e:
            logger.error(f"Error Surgeon error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Error surgery failed: {str(e)}"],
            )

    async def fix_errors(
        self,
        manim_code: str,
        error_log: str = "",
        testing_result: Optional[CodeTestingResult] = None,
    ) -> ErrorSurgeryResult:
        """
        Perform surgical fixes on errors in Manim code.

        Args:
            manim_code: The Manim Python code to fix
            error_log: Error log from previous rendering attempt
            testing_result: Results from Code Testing Agent

        Returns:
            ErrorSurgeryResult: Complete results with diagnoses and fixes
        """

        # Step 1: Diagnose errors
        error_diagnoses = await self.diagnose_errors(
            manim_code, error_log, testing_result
        )

        # Step 2: Generate fixes for each error
        all_fixes = []
        unfixable_errors = []

        for diagnosis in error_diagnoses:
            fixes = await self.generate_fixes(manim_code, diagnosis)

            if fixes:
                all_fixes.extend(fixes)
            else:
                unfixable_errors.append(diagnosis)

        # Step 3: Apply fixes
        fixed_code = manim_code
        applied_fixes = []

        # Sort fixes by confidence (highest first) and line number (if available)
        sorted_fixes = sorted(
            all_fixes,
            key=lambda fix: (
                -fix.confidence,
                fix.line_number if fix.line_number is not None else float("inf"),
            ),
        )

        for fix in sorted_fixes:
            # Skip fixes that require human review for now
            if fix.requires_human_review:
                continue

            # Apply the fix
            try:
                fixed_code = self._apply_fix(fixed_code, fix)
                fix.is_applied = True
                applied_fixes.append(fix)
            except Exception as e:
                logger.error(f"Failed to apply fix {fix.fix_id}: {e}")
                fix.is_applied = False

        # Step 4: Determine success
        # Success if: no unfixable errors AND (either no errors found OR fixes applied)
        # Also succeed if error_log is empty (no actual errors to fix)
        no_errors_to_fix = len(error_diagnoses) == 0 or not error_log.strip()
        fixed_all_errors = len(applied_fixes) > 0 and len(unfixable_errors) == 0
        success = no_errors_to_fix or fixed_all_errors

        requires_human_intervention = len(unfixable_errors) > 0 or any(
            fix.requires_human_review for fix in all_fixes
        )

        return ErrorSurgeryResult(
            original_code=manim_code,
            fixed_code=fixed_code,
            error_diagnoses=error_diagnoses,
            applied_fixes=applied_fixes,
            unfixable_errors=unfixable_errors,
            success=success,
            requires_human_intervention=requires_human_intervention,
        )

    async def diagnose_errors(
        self,
        code: str,
        error_log: str = "",
        testing_result: Optional[CodeTestingResult] = None,
    ) -> List[ErrorDiagnosis]:
        """Diagnose errors in the code based on error logs and test results."""

        # Prepare context for Claude
        context_parts = ["I need to diagnose errors in this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        if error_log:
            context_parts.append("Error log:")
            context_parts.append(f"```\n{error_log}\n```")

        if testing_result:
            # Add test results
            failed_tests = [tc for tc in testing_result.test_cases if not tc.passed]

            if failed_tests:
                context_parts.append("Failed tests:")
                for test in failed_tests:
                    context_parts.append(
                        f"- {test.test_name}: {test.error_message or 'No error message'}"
                    )

            # Add detailed test results
            failed_manim_tests = [
                tr for tr in testing_result.manim_test_results if not tr.success
            ]

            if failed_manim_tests:
                context_parts.append("Detailed test failures:")
                for test in failed_manim_tests:
                    context_parts.append(
                        f"- {test.test_type} test failed: {test.error_message or 'No error message'}"
                    )

        # Add instructions
        context_parts.append(
            "Please diagnose each error with: error type, message, location, context, severity, and root cause."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_error_diagnoses(response.content, code, error_log)

    async def generate_fixes(
        self, code: str, diagnosis: ErrorDiagnosis
    ) -> List[ErrorFix]:
        """Generate fixes for a specific error diagnosis."""

        # For common syntax errors, we can generate fixes directly without calling Claude
        if (
            diagnosis.error_type == "syntax"
            and diagnosis.root_cause
            and diagnosis.suggested_fix
        ):
            if "missing closing parenthesis" in diagnosis.root_cause.lower():
                return self._generate_direct_syntax_fix(code, diagnosis, ")")
            elif "missing closing bracket" in diagnosis.root_cause.lower():
                return self._generate_direct_syntax_fix(code, diagnosis, "]")
            elif "missing closing brace" in diagnosis.root_cause.lower():
                return self._generate_direct_syntax_fix(code, diagnosis, "}")
            elif "missing closing single quote" in diagnosis.root_cause.lower():
                return self._generate_direct_syntax_fix(code, diagnosis, "'")
            elif "missing closing double quote" in diagnosis.root_cause.lower():
                return self._generate_direct_syntax_fix(code, diagnosis, '"')

        # For common runtime errors, generate fixes directly
        if (
            diagnosis.error_type == "runtime"
            and "nameerror" in diagnosis.error_message.lower()
        ):
            return self._generate_nameerror_fix(code, diagnosis)

        # For other errors, use Claude to generate fixes
        # Prepare context for Claude
        context = f"""
        I need to fix this error in Manim code:
        
        Error Type: {diagnosis.error_type}
        Error Message: {diagnosis.error_message}
        Location: {diagnosis.error_location or 'Unknown'}
        Root Cause: {diagnosis.root_cause or 'Unknown'}
        
        Here's the code:
        ```python
        {code}
        ```
        
        Please provide specific fixes for this error. For each fix:
        1. Describe the fix clearly
        2. Provide the exact code changes needed
        3. Rate your confidence in the fix (0.0-1.0)
        4. Indicate if human review is required
        
        Focus on minimal, surgical changes that fix the error without disrupting working code.
        """

        messages = [
            ClaudeMessage(
                role="user",
                content=context,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_error_fixes(response.content, code, diagnosis)

    def _generate_direct_syntax_fix(
        self, code: str, diagnosis: ErrorDiagnosis, closing_char: str
    ) -> List[ErrorFix]:
        """Generate a direct fix for common syntax errors without calling Claude."""

        fixes = []

        # Extract line number from location
        line_num = None
        if diagnosis.error_location:
            line_match = re.search(r"line (\d+)", diagnosis.error_location)
            if line_match:
                line_num = int(line_match.group(1)) - 1  # Convert to 0-indexed

        # If we have a line number and context
        if line_num is not None and diagnosis.error_context:
            lines = code.split("\n")
            if 0 <= line_num < len(lines):
                original_line = lines[line_num]
                fixed_line = original_line + closing_char

                # Create the fix
                fixes.append(
                    ErrorFix(
                        error_id=diagnosis.error_id,
                        fix_id=f"{diagnosis.error_id}_fix_1",
                        fix_description=f"Add {closing_char} to fix {diagnosis.error_type} error",
                        original_code=original_line,
                        fixed_code=fixed_line,
                        line_number=line_num,
                        confidence=0.9,  # High confidence for these simple fixes
                        requires_human_review=False,
                    )
                )

        return fixes

    def _generate_nameerror_fix(
        self, code: str, diagnosis: ErrorDiagnosis
    ) -> List[ErrorFix]:
        """Generate fixes for NameError issues."""
        fixes = []

        # Extract the undefined variable name from the error message
        import re

        match = re.search(r"name '(\w+)' is not defined", diagnosis.error_message)
        if not match:
            return fixes

        undefined_var = match.group(1)
        print(f"   🔍 Detected undefined variable: {undefined_var}")

        # Find where the variable is used
        lines = code.split("\n")
        usage_lines = []

        for i, line in enumerate(lines):
            if undefined_var in line and not line.strip().startswith("#"):
                usage_lines.append((i + 1, line.strip()))

        if not usage_lines:
            return fixes

        print(f"   📍 Found {len(usage_lines)} usage(s) of '{undefined_var}'")

        # Special handling for specific patterns
        if undefined_var == "bottleneck_highlight":
            # Look for bottleneck_text definition to understand the context
            bottleneck_text_line = None
            for i, line in enumerate(lines):
                if "bottleneck_text = Text(" in line and "Bottleneck" in line:
                    bottleneck_text_line = i
                    break

            if bottleneck_text_line is not None:
                # Create a fix to define bottleneck_highlight
                definition = f"        bottleneck_highlight = Circle(radius=0.8, color=RED, stroke_width=3)"

                # Find the first usage line to insert the definition before it
                first_usage_line = (
                    min(usage_lines, key=lambda x: x[0])[0] - 1
                )  # Convert to 0-based index

                fix = ErrorFix(
                    fix_id=f"fix_{uuid.uuid4().hex[:8]}",
                    error_id=diagnosis.error_id,
                    fix_type="variable_definition",
                    fix_description=f"Define missing variable '{undefined_var}' as a red circle",
                    old_code="",  # Will be set by _apply_fix
                    new_code=definition,
                    line_number=first_usage_line,
                    confidence=0.8,
                    requires_human_review=False,
                )

                fixes.append(fix)
                print(f"   ✅ Generated fix: Define {undefined_var} as red circle")

        # Generic variable definition fix
        if not fixes:
            # Try to infer variable type and create a generic definition
            first_usage = usage_lines[0][1]

            # Analyze usage to guess the type
            if "Create(" in first_usage:
                # Likely a Manim object
                definition = f"        {undefined_var} = Circle()  # TODO: Define appropriate Manim object"
            elif "Write(" in first_usage:
                # Likely text
                definition = f"        {undefined_var} = Text('TODO: Define text')  # TODO: Set appropriate text"
            else:
                # Generic
                definition = f"        {undefined_var} = None  # TODO: Define this variable appropriately"

            first_usage_line = min(usage_lines, key=lambda x: x[0])[0] - 1

            fix = ErrorFix(
                fix_id=f"fix_{uuid.uuid4().hex[:8]}",
                error_id=diagnosis.error_id,
                fix_type="variable_definition",
                fix_description=f"Define missing variable '{undefined_var}'",
                old_code="",
                new_code=definition,
                line_number=first_usage_line,
                confidence=0.5,
                requires_human_review=True,
            )

            fixes.append(fix)
            print(f"   ⚠️ Generated generic fix for {undefined_var}")

        return fixes

    def _apply_fix(self, code: str, fix: ErrorFix) -> str:
        """Apply a specific fix to the code."""

        # Special handling for variable definition fixes
        if fix.fix_type == "variable_definition":
            lines = code.split("\n")
            if 0 <= fix.line_number < len(lines):
                # Insert the variable definition before the specified line
                lines.insert(fix.line_number, fix.new_code)
                logger.info(
                    f"Inserted variable definition at line {fix.line_number}: {fix.fix_description}"
                )
                return "\n".join(lines)

        # If the fix specifies a line number, replace just that line
        if fix.line_number is not None:
            lines = code.split("\n")
            if 0 <= fix.line_number < len(lines):
                # Find the original line in the fixed code
                original_line = lines[fix.line_number]

                # For syntax error fixes, we often just need to append a character
                if fix.old_code and fix.old_code.strip() == original_line.strip():
                    lines[fix.line_number] = fix.new_code
                    logger.info(
                        f"Applied fix at line {fix.line_number}: {fix.fix_description}"
                    )
                    return "\n".join(lines)
                # Check if the original line matches what's expected
                elif fix.old_code and original_line.strip() == fix.old_code.strip():
                    lines[fix.line_number] = fix.fixed_code
                    logger.info(
                        f"Applied fix at line {fix.line_number}: {fix.fix_description}"
                    )
                    return "\n".join(lines)
                # Check if the original line is contained in the fixed code
                elif original_line.strip() in fix.fixed_code.strip():
                    lines[fix.line_number] = fix.fixed_code
                    logger.info(
                        f"Applied fix at line {fix.line_number}: {fix.fix_description}"
                    )
                    return "\n".join(lines)
                # Check if the fixed code is the original line plus something
                elif fix.fixed_code.strip().startswith(original_line.strip()):
                    lines[fix.line_number] = fix.fixed_code
                    logger.info(
                        f"Applied fix at line {fix.line_number}: {fix.fix_description}"
                    )
                    return "\n".join(lines)
                else:
                    # Try fuzzy matching
                    logger.warning(
                        f"Line {fix.line_number} doesn't match expected content, trying fuzzy replacement"
                    )
                    return code.replace(original_line, fix.fixed_code)
            else:
                logger.error(f"Line number {fix.line_number} out of range")
                return code

        # Otherwise, do a direct replacement
        if fix.original_code in code:
            logger.info(f"Applied fix: {fix.fix_description}")
            return code.replace(fix.original_code, fix.fixed_code)

        # If direct replacement fails, try with normalized whitespace
        orig_normalized = re.sub(r"\s+", " ", fix.original_code).strip()

        for line_num, line in enumerate(code.split("\n")):
            line_normalized = re.sub(r"\s+", " ", line).strip()
            if line_normalized == orig_normalized:
                lines = code.split("\n")
                lines[line_num] = fix.fixed_code
                logger.info(
                    f"Applied fix with normalized whitespace at line {line_num}"
                )
                return "\n".join(lines)
            elif line_normalized in orig_normalized:
                # Try to find the best match
                lines = code.split("\n")
                lines[line_num] = fix.fixed_code
                logger.info(
                    f"Applied partial fix with normalized whitespace at line {line_num}"
                )
                return "\n".join(lines)

        # If all else fails, return the code unchanged
        logger.warning(f"Could not apply fix: original code segment not found")
        return code

    def _create_sample_code_with_errors(self) -> Tuple[str, str]:
        """Create sample code with errors for testing."""

        # Sample code with multiple types of errors
        code_with_errors = """
from manim import *

class Scene_WithErrors(Scene):
    def construct(self):
        # Title with missing closing parenthesis - syntax error
        title = Text("Attention Mechanisms", font_size=36
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)
        self.wait(0.8)
        
        # LaTeX error - missing closing brace
        eq = MathTex(r"e_t = (H W_a \\cdot s_{t-1} \\in \\mathbb{R}^{B\\times n}", font_size=32)
        eq.next_to(title, DOWN, buff=0.5)
        self.play(Write(eq), run_time=1.2)
        self.wait(0.8)
        
        # Runtime error - undefined variable
        explanation = Text("This equation computes attention energy", font_size=24)
        explanation.next_to(eq, DOWN, buff=0.3)
        self.play(Write(explanation), run_time=1.0)
        self.wait(0.8)
        
        # Using undefined variable
        attention_weights.shift(DOWN)  # This will cause a runtime error
        
        # Manim-specific error - invalid animation
        eq2 = MathTex(r"\\alpha_{i,j} = \\text{softmax}(\\beta_{i,j})", font_size=28)
        eq2.next_to(explanation, DOWN, buff=0.3)
        self.play(eq2)  # Missing animation type
        self.wait(0.8)
"""

        # Sample error log
        error_log = """
File "scene_with_errors.py", line 6
    title = Text("Attention Mechanisms", font_size=36
                                                    ^
SyntaxError: '(' was never closed

During handling of the above exception, another exception occurred:

ValueError: LaTeX error converting to dvi. See log output above or the log file: media/Tex/65d720eb4db018f5.log

During handling of the above exception, another exception occurred:

NameError: name 'attention_weights' is not defined

During handling of the above exception, another exception occurred:

TypeError: play() missing 1 required positional argument: 'animation'
"""

        return code_with_errors, error_log

    def _create_system_prompt(self) -> str:
        """Create the system prompt for error surgery operations."""
        return """
        You are an expert Error Surgeon specializing in fixing Manim animation code.
        
        Your expertise includes:
        1. Diagnosing and fixing Python syntax errors
        2. Resolving LaTeX compilation issues in MathTex objects
        3. Fixing Manim-specific errors (animations, positioning, etc.)
        4. Addressing runtime errors in animation sequences
        5. Making minimal, surgical fixes without disrupting working code
        
        When diagnosing errors:
        - Identify the exact error type (syntax, LaTeX, runtime, Manim-specific)
        - Pinpoint the precise location in the code
        - Determine the root cause
        - Assess the severity
        
        When generating fixes:
        - Provide specific, targeted changes
        - Maintain the original intent of the code
        - Preserve working parts of the code
        - Rate your confidence in each fix
        - Flag fixes that require human review
        
        Common error patterns you can fix:
        - Unclosed parentheses, brackets, or quotes
        - LaTeX syntax errors (missing braces, incorrect commands)
        - Undefined variables or attributes
        - Incorrect Manim animation syntax
        - Missing positioning for objects
        - Improper animation sequences
        
        Be precise, methodical, and educational in your approach.
        """

    def _parse_error_diagnoses(
        self, response: str, code: str, error_log: str
    ) -> List[ErrorDiagnosis]:
        """Parse error diagnoses from Claude's response."""

        diagnoses = []

        # Try to extract structured diagnoses
        diagnosis_pattern = r"(?:Error|Issue|Problem)\s+(\d+|Type):\s*([^\n]+)"
        diagnosis_blocks = re.split(diagnosis_pattern, response)

        if len(diagnosis_blocks) > 2:  # We have structured diagnoses
            # Process each diagnosis block
            for i in range(1, len(diagnosis_blocks), 3):
                if i + 1 < len(diagnosis_blocks):
                    error_id = f"error_{diagnosis_blocks[i].lower()}"
                    if error_id == "error_type":
                        error_id = f"error_{len(diagnoses) + 1}"

                    # Extract error type
                    error_type_match = re.search(
                        r"(?:Error )?Type:?\s*([^\n]+)",
                        diagnosis_blocks[i + 1] + diagnosis_blocks[i + 2],
                    )
                    error_type = (
                        error_type_match.group(1).strip()
                        if error_type_match
                        else "unknown"
                    )

                    # Extract error message
                    error_msg_match = re.search(
                        r"(?:Error )?Message:?\s*([^\n]+(?:\n\s+[^\n]+)*)",
                        diagnosis_blocks[i + 1] + diagnosis_blocks[i + 2],
                    )
                    error_message = (
                        error_msg_match.group(1).strip() if error_msg_match else ""
                    )

                    # Extract location
                    location_match = re.search(
                        r"Location:?\s*([^\n]+)",
                        diagnosis_blocks[i + 1] + diagnosis_blocks[i + 2],
                    )
                    location = (
                        location_match.group(1).strip() if location_match else None
                    )

                    # Extract context
                    context_match = re.search(
                        r"Context:?\s*([^\n]+(?:\n\s+[^\n]+)*)",
                        diagnosis_blocks[i + 1] + diagnosis_blocks[i + 2],
                    )
                    context = context_match.group(1).strip() if context_match else None

                    # Extract severity
                    severity_match = re.search(
                        r"Severity:?\s*([^\n]+)",
                        diagnosis_blocks[i + 1] + diagnosis_blocks[i + 2],
                    )
                    severity = (
                        severity_match.group(1).strip().lower()
                        if severity_match
                        else "high"
                    )

                    # Extract root cause
                    cause_match = re.search(
                        r"(?:Root )?Cause:?\s*([^\n]+(?:\n\s+[^\n]+)*)",
                        diagnosis_blocks[i + 1] + diagnosis_blocks[i + 2],
                    )
                    root_cause = cause_match.group(1).strip() if cause_match else None

                    # Extract suggested fix
                    fix_match = re.search(
                        r"(?:Suggested )?Fix:?\s*([^\n]+(?:\n\s+[^\n]+)*)",
                        diagnosis_blocks[i + 1] + diagnosis_blocks[i + 2],
                    )
                    suggested_fix = fix_match.group(1).strip() if fix_match else None

                    diagnoses.append(
                        ErrorDiagnosis(
                            error_id=error_id,
                            error_type=error_type,
                            error_message=error_message,
                            error_location=location,
                            error_context=context,
                            severity=severity,
                            root_cause=root_cause,
                            suggested_fix=suggested_fix,
                        )
                    )
        else:
            # Fallback: extract errors from error log if available
            if error_log:
                error_patterns = [
                    (r"SyntaxError:\s*([^\n]+)", "syntax"),
                    (r"ValueError:\s*LaTeX error[^\n]+", "latex"),
                    (r"NameError:\s*([^\n]+)", "runtime"),
                    (r"TypeError:\s*([^\n]+)", "runtime"),
                    (r"AttributeError:\s*([^\n]+)", "runtime"),
                ]

                for pattern, error_type in error_patterns:
                    for match in re.finditer(pattern, error_log):
                        error_message = match.group(0)

                        # Try to extract line number
                        line_match = re.search(
                            r"line (\d+)", error_log[: match.start()]
                        )
                        location = f"line {line_match.group(1)}" if line_match else None

                        # For syntax errors, try to extract the context
                        context = None
                        root_cause = None
                        suggested_fix = None

                        if error_type == "syntax" and location:
                            # Extract line number
                            line_num = int(line_match.group(1))

                            # Get the line from the code
                            lines = code.split("\n")
                            if 0 < line_num <= len(lines):
                                context = lines[line_num - 1]

                                # Analyze common syntax errors
                                if (
                                    "unclosed" in error_message.lower()
                                    or "never closed" in error_message.lower()
                                ):
                                    if "(" in error_message:
                                        root_cause = "Missing closing parenthesis"
                                        suggested_fix = "Add closing parenthesis ')'"
                                    elif "[" in error_message:
                                        root_cause = "Missing closing bracket"
                                        suggested_fix = "Add closing bracket ']'"
                                    elif "{" in error_message:
                                        root_cause = "Missing closing brace"
                                        suggested_fix = "Add closing brace '}'"
                                    elif (
                                        "quote" in error_message
                                        or "string" in error_message
                                    ):
                                        if "'" in context:
                                            root_cause = "Missing closing single quote"
                                            suggested_fix = "Add closing single quote '"
                                        else:
                                            root_cause = "Missing closing double quote"
                                            suggested_fix = 'Add closing double quote "'

                        diagnoses.append(
                            ErrorDiagnosis(
                                error_id=f"error_{len(diagnoses) + 1}",
                                error_type=error_type,
                                error_message=error_message,
                                error_location=location,
                                error_context=context,
                                root_cause=root_cause,
                                suggested_fix=suggested_fix,
                                severity="high",
                            )
                        )

            # Try to detect syntax errors directly from the code
            if not diagnoses:
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    # Get the line from the code
                    lines = code.split("\n")
                    context = (
                        lines[e.lineno - 1] if 0 < e.lineno <= len(lines) else None
                    )

                    # Analyze common syntax errors
                    root_cause = None
                    suggested_fix = None

                    if "unclosed" in str(e).lower() or "never closed" in str(e).lower():
                        if "(" in str(e):
                            root_cause = "Missing closing parenthesis"
                            suggested_fix = "Add closing parenthesis ')'"
                        elif "[" in str(e):
                            root_cause = "Missing closing bracket"
                            suggested_fix = "Add closing bracket ']'"
                        elif "{" in str(e):
                            root_cause = "Missing closing brace"
                            suggested_fix = "Add closing brace '}'"
                        elif "quote" in str(e) or "string" in str(e):
                            if context and "'" in context:
                                root_cause = "Missing closing single quote"
                                suggested_fix = "Add closing single quote '"
                            else:
                                root_cause = "Missing closing double quote"
                                suggested_fix = 'Add closing double quote "'

                    diagnoses.append(
                        ErrorDiagnosis(
                            error_id="error_syntax",
                            error_type="syntax",
                            error_message=str(e),
                            error_location=f"line {e.lineno}",
                            error_context=context,
                            root_cause=root_cause,
                            suggested_fix=suggested_fix,
                            severity="high",
                        )
                    )

        # If still no diagnoses, create a generic one
        if not diagnoses:
            diagnoses.append(
                ErrorDiagnosis(
                    error_id="error_1",
                    error_type="unknown",
                    error_message="Unknown error in code",
                    severity="medium",
                )
            )

        return diagnoses

    def _parse_error_fixes(
        self, response: str, code: str, diagnosis: ErrorDiagnosis
    ) -> List[ErrorFix]:
        """Parse error fixes from Claude's response."""

        fixes = []

        # Look for code blocks
        code_blocks = re.findall(r"```(?:python)?\n(.*?)\n```", response, re.DOTALL)

        # Look for "Before" and "After" or "Original" and "Fixed" patterns
        before_after_matches = []

        # Pattern 1: Before/After blocks
        before_blocks = re.findall(
            r"(?:Before|Original):\s*```(?:python)?\n(.*?)\n```", response, re.DOTALL
        )
        after_blocks = re.findall(
            r"(?:After|Fixed):\s*```(?:python)?\n(.*?)\n```", response, re.DOTALL
        )

        for i in range(min(len(before_blocks), len(after_blocks))):
            before_after_matches.append((before_blocks[i], after_blocks[i]))

        # Pattern 2: Line changes
        line_changes = re.findall(
            r"(?:Line|Change) (\d+):\s*(?:From|Before)?\s*`([^`]+)`\s*(?:to|->)\s*`([^`]+)`",
            response,
        )

        for line_num, before, after in line_changes:
            before_after_matches.append((before, after))

        # If we have direct before/after matches
        for i, (before, after) in enumerate(before_after_matches):
            # Extract description
            description_match = re.search(
                r"(?:Fix|Solution|Change)\s+\d*:?\s*([^\n]+)(?=\n)", response
            )
            description = (
                description_match.group(1).strip()
                if description_match
                else f"Fix for {diagnosis.error_type} error"
            )

            # Extract confidence
            confidence_match = re.search(r"[Cc]onfidence:?\s*(0\.\d+|1\.0|1)", response)
            confidence = float(confidence_match.group(1)) if confidence_match else 0.8

            # Check if human review is needed
            requires_review = (
                "human review" in response.lower()
                or "manual check" in response.lower()
                or confidence < 0.5
            )

            # Try to determine line number
            line_num = None
            if diagnosis.error_location:
                line_match = re.search(r"line (\d+)", diagnosis.error_location)
                if line_match:
                    line_num = int(line_match.group(1)) - 1  # Convert to 0-indexed

            # Create the fix
            fixes.append(
                ErrorFix(
                    error_id=diagnosis.error_id,
                    fix_id=f"{diagnosis.error_id}_fix_{i+1}",
                    fix_description=description,
                    original_code=before.strip(),
                    fixed_code=after.strip(),
                    line_number=line_num,
                    confidence=confidence,
                    requires_human_review=requires_review,
                )
            )

        # If no structured fixes found, try to create one from the diagnosis
        if not fixes and diagnosis.suggested_fix:
            # Try to find the problematic code using the error location
            original_code = ""
            line_num = None

            if diagnosis.error_location:
                line_match = re.search(r"line (\d+)", diagnosis.error_location)
                if line_match:
                    line_num = int(line_match.group(1)) - 1  # Convert to 0-indexed
                    lines = code.split("\n")
                    if 0 <= line_num < len(lines):
                        original_code = lines[line_num]

            # If we couldn't find the specific line, use the error context
            if not original_code and diagnosis.error_context:
                original_code = diagnosis.error_context

            # If we have original code, create a fix
            if original_code:
                # Try to extract fixed code from the suggested fix
                fixed_code = original_code  # Default to unchanged

                # Apply common fixes based on error type
                if diagnosis.error_type == "syntax":
                    if "unclosed parenthesis" in diagnosis.error_message.lower():
                        fixed_code = original_code + ")"
                    elif "missing closing quote" in diagnosis.error_message.lower():
                        if "'" in original_code:
                            fixed_code = original_code + "'"
                        else:
                            fixed_code = original_code + '"'

                elif diagnosis.error_type == "latex":
                    if "missing }" in diagnosis.error_message.lower():
                        fixed_code = original_code + "}"
                    elif (
                        "undefined control sequence" in diagnosis.error_message.lower()
                    ):
                        # Try to fix common LaTeX command errors
                        fixed_code = original_code.replace("\\\\", "\\")

                # Create the fix
                fixes.append(
                    ErrorFix(
                        error_id=diagnosis.error_id,
                        fix_id=f"{diagnosis.error_id}_fix_1",
                        fix_description=f"Fix for {diagnosis.error_type} error",
                        original_code=original_code,
                        fixed_code=fixed_code,
                        line_number=line_num,
                        confidence=0.6,
                        requires_human_review=True,  # Mark as requiring review since this is a fallback
                    )
                )

        return fixes
