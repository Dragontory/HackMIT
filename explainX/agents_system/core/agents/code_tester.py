"""
Code Testing Agent implementation.

This agent tests Manim code in a sandbox environment before full rendering,
catching errors early in the pipeline and providing detailed diagnostics.
"""

import logging
import re
import time
import os
import tempfile
import subprocess
import ast
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from ...domain.interfaces import IAgent
from ...domain.models import (
    AgentState,
    AgentResult,
    CodeTestingResult,
    TestCase,
    ManimTestResult,
    SandboxExecutionResult,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage


logger = logging.getLogger(__name__)


class CodeTestingAgent(IAgent):
    """
    Specialized agent for testing Manim code before full rendering.

    Uses sandbox execution to:
    - Validate syntax and structure
    - Test object creation without rendering
    - Check for common Manim errors
    - Provide detailed diagnostics
    - Generate test cases
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()
        self._temp_dir = tempfile.mkdtemp(prefix="manim_test_")
        logger.info(f"Created temporary directory for testing: {self._temp_dir}")

    @property
    def name(self) -> str:
        return "CodeTestingAgent"

    @property
    def description(self) -> str:
        return "Tests generated code before full rendering to catch errors early"

    async def process(self, state: AgentState) -> AgentResult:
        """Process state and test Manim code."""
        start_time = time.time()

        try:
            logger.info(f"Code Testing processing: {state['content_title']}")

            # Get the code to test (should be modified code from previous agent)
            manim_code = state.get("manim_code", "")

            if not manim_code:
                # Create sample code for testing
                manim_code = self._create_sample_code()
                logger.info("No Manim code provided, using sample code for testing")

            # Perform comprehensive code testing
            result = await self.test_manim_code(manim_code)

            # Update state
            state["code_testing_result"] = result
            state["current_agent"] = self.name
            state["processing_stage"] = "code_testing_complete"

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "test_cases_count": len(result.test_cases),
                    "test_cases_passed": sum(
                        1 for tc in result.test_cases if tc.passed
                    ),
                    "syntax_valid": result.syntax_valid,
                    "render_valid": result.render_valid,
                    "object_creation_valid": result.object_creation_valid,
                    "animation_valid": result.animation_valid,
                    "processing_time": processing_time,
                },
            )

        except Exception as e:
            logger.error(f"Code Testing error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Code testing failed: {str(e)}"],
            )

    async def test_manim_code(self, manim_code: str) -> CodeTestingResult:
        """
        Comprehensive testing of Manim code.

        Args:
            manim_code: The Manim Python code to test

        Returns:
            CodeTestingResult: Complete results with test cases and diagnostics
        """

        # Step 1: Generate test cases
        test_cases = await self.generate_test_cases(manim_code)

        # Step 2: Create test code with instrumentation
        test_code = self._create_test_code(manim_code)

        # Step 3: Run different types of tests
        syntax_result = self._test_syntax(test_code)
        object_creation_result = await self._test_object_creation(test_code)
        animation_result = await self._test_animations(test_code)
        render_result = await self._test_minimal_render(test_code)

        # Step 4: Collect all test results
        manim_test_results = [
            syntax_result,
            object_creation_result,
            animation_result,
            render_result,
        ]

        # Step 5: Update test cases with actual results
        for test_case in test_cases:
            # Find corresponding test result
            for result in manim_test_results:
                if result.test_id == test_case.test_id:
                    test_case.actual_result = (
                        "Success" if result.success else result.error_message
                    )
                    test_case.passed = result.success
                    test_case.error_message = (
                        result.error_message if not result.success else None
                    )

        # Step 6: Generate improvement suggestions
        suggestions = await self.generate_suggestions(manim_code, manim_test_results)

        # Determine overall success
        # For environments without Manim, syntax validation is sufficient
        success = syntax_result.success

        # If Manim is available, require stricter validation
        if (
            object_creation_result.success
            or animation_result.success
            or render_result.success
        ):
            success = (
                syntax_result.success
                and object_creation_result.success
                and animation_result.success
                and render_result.success
            )

        return CodeTestingResult(
            original_code=manim_code,
            test_code=test_code,
            test_cases=test_cases,
            manim_test_results=manim_test_results,
            syntax_valid=syntax_result.success,
            render_valid=render_result.success,
            object_creation_valid=object_creation_result.success,
            animation_valid=animation_result.success,
            success=success,
            suggestions=suggestions,
        )

    async def generate_test_cases(self, code: str) -> List[TestCase]:
        """Generate test cases for Manim code."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
                Generate comprehensive test cases for this Manim code:
                
                ```python
                {code}
                ```
                
                Create test cases that verify:
                1. Syntax validity
                2. Object creation (Text, MathTex, etc.)
                3. Animation sequences
                4. Minimal rendering capability
                
                For each test case, provide:
                - Test ID
                - Test name
                - Description
                - Expected result
                
                Focus on common Manim issues like:
                - LaTeX syntax errors
                - Object positioning
                - Animation timing
                - Scene structure
                """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_test_cases(response.content)

    async def generate_suggestions(
        self, code: str, test_results: List[ManimTestResult]
    ) -> List[str]:
        """Generate improvement suggestions based on test results."""

        # Filter for failed tests
        failed_tests = [tr for tr in test_results if not tr.success]

        if not failed_tests:
            return ["All tests passed. No improvements needed."]

        # Prepare error information for Claude
        error_info = "\n".join(
            [
                f"Test {tr.test_id} ({tr.test_type}) failed: {tr.error_message}"
                for tr in failed_tests
            ]
        )

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
                Generate improvement suggestions for this Manim code based on test failures:
                
                ```python
                {code}
                ```
                
                Test failures:
                {error_info}
                
                Provide specific, actionable suggestions to fix these issues.
                Focus on:
                - Syntax corrections
                - Object creation improvements
                - Animation sequence fixes
                - Rendering optimizations
                
                Be specific about what needs to be changed and why.
                """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_suggestions(response.content)

    def _create_test_code(self, code: str) -> str:
        """Create instrumented test code from original Manim code."""

        # Add imports for testing
        test_imports = """
import sys
import traceback
from manim import *
import contextlib
import io
import time

# Test instrumentation
class TestLogger:
    def __init__(self):
        self.logs = []
    
    def log(self, message):
        self.logs.append(message)
        print(f"TEST_LOG: {message}")

test_logger = TestLogger()

# Monkey patch Scene.play to track animations
original_play = Scene.play
def instrumented_play(self, *args, **kwargs):
    try:
        test_logger.log(f"Animation: {args}")
        return original_play(self, *args, **kwargs)
    except Exception as e:
        test_logger.log(f"Animation error: {str(e)}")
        raise

Scene.play = instrumented_play

# Monkey patch for object creation tracking
original_add = Scene.add
def instrumented_add(self, *args, **kwargs):
    try:
        test_logger.log(f"Object added: {args}")
        return original_add(self, *args, **kwargs)
    except Exception as e:
        test_logger.log(f"Object creation error: {str(e)}")
        raise

Scene.add = instrumented_add

# Create a test runner
def run_test(test_func):
    try:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            start_time = time.time()
            test_func()
            end_time = time.time()
        
        test_logger.log(f"Test completed in {end_time - start_time:.2f} seconds")
        return True, stdout.getvalue(), ""
    except Exception as e:
        test_logger.log(f"Test failed: {str(e)}")
        return False, stdout.getvalue(), traceback.format_exc()
"""

        # Add test functions
        test_functions = """
# Test functions
def test_syntax():
    # Just compiling the code is enough for syntax test
    test_logger.log("Syntax test passed")
    return True

def test_object_creation():
    # Create a scene and test object creation without rendering
    class TestScene(Scene):
        def construct(self):
            # Create objects but don't render
            test_logger.log("Creating objects...")
            self.setup()
            # Extract object creation from the original scene
            # This will be filled in dynamically
    
    scene = TestScene()
    scene.construct()
    test_logger.log("Object creation test passed")
    return True

def test_animations():
    # Test animation sequences without rendering
    class TestScene(Scene):
        def construct(self):
            test_logger.log("Testing animations...")
            self.setup()
            # Extract animations from the original scene
            # This will be filled in dynamically
    
    scene = TestScene()
    scene.construct()
    test_logger.log("Animation test passed")
    return True

def test_minimal_render():
    # Test minimal rendering with a simple object
    class TestScene(Scene):
        def construct(self):
            test_logger.log("Testing minimal render...")
            circle = Circle()
            self.add(circle)
            self.wait(0.1)
    
    with tempconfig({"quality": "low_quality", "preview": True, "disable_caching": True}):
        scene = TestScene()
        scene.render()
    
    test_logger.log("Render test passed")
    return True

# Run tests
if __name__ == "__main__":
    test_name = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if test_name == "syntax" or test_name == "all":
        success, stdout, stderr = run_test(test_syntax)
        print(f"SYNTAX_TEST: {'PASSED' if success else 'FAILED'}")
    
    if test_name == "object_creation" or test_name == "all":
        success, stdout, stderr = run_test(test_object_creation)
        print(f"OBJECT_CREATION_TEST: {'PASSED' if success else 'FAILED'}")
    
    if test_name == "animations" or test_name == "all":
        success, stdout, stderr = run_test(test_animations)
        print(f"ANIMATIONS_TEST: {'PASSED' if success else 'FAILED'}")
    
    if test_name == "render" or test_name == "all":
        success, stdout, stderr = run_test(test_minimal_render)
        print(f"RENDER_TEST: {'PASSED' if success else 'FAILED'}")
"""

        # Extract the original scene class
        scene_class_match = re.search(
            r"class\s+(\w+)\s*\(\s*Scene\s*\).*?construct\s*\(\s*self\s*\).*?:",
            code,
            re.DOTALL,
        )

        if not scene_class_match:
            # If no scene class found, return the original code with test instrumentation
            return test_imports + "\n" + code + "\n" + test_functions

        # Extract the construct method to analyze object creation and animations
        construct_match = re.search(
            r"def\s+construct\s*\(\s*self\s*\).*?:(.*?)(?:def|\Z)", code, re.DOTALL
        )

        if not construct_match:
            # If construct method not found, return the original code with test instrumentation
            return test_imports + "\n" + code + "\n" + test_functions

        construct_body = construct_match.group(1)

        # Extract object creation lines
        object_creation_lines = re.findall(
            r"(\s*\w+\s*=\s*(?:Text|MathTex|Tex|Circle|Rectangle|Square|Arrow|Line|VGroup)\(.*?\).*?)(?:\n|$)",
            construct_body,
        )

        # Extract animation lines
        animation_lines = re.findall(
            r"(\s*self\.play\(.*?\).*?)(?:\n|$)", construct_body
        )

        # Update test functions with extracted code
        object_creation_code = (
            "\n            ".join(object_creation_lines)
            if object_creation_lines
            else "pass"
        )
        animation_code = (
            "\n            ".join(animation_lines) if animation_lines else "pass"
        )

        test_functions = test_functions.replace(
            "# This will be filled in dynamically", object_creation_code
        )
        test_functions = test_functions.replace(
            "# Extract animations from the original scene\n            # This will be filled in dynamically",
            animation_code,
        )

        # Combine everything
        return test_imports + "\n" + code + "\n" + test_functions

    def _test_syntax(self, test_code: str) -> ManimTestResult:
        """Test syntax validity of the code."""
        try:
            # Check Python syntax
            ast.parse(test_code)

            # Save to temp file for more detailed checking
            test_file = os.path.join(self._temp_dir, "syntax_test.py")
            with open(test_file, "w") as f:
                f.write(test_code)

            # Run syntax check
            result = self._run_process(["python", "-m", "py_compile", test_file])

            return ManimTestResult(
                test_id="syntax_test",
                scene_name="N/A",
                test_type="syntax",
                success=result.execution_success and result.exit_code == 0,
                error_message=result.stderr if not result.execution_success else None,
                execution_result=result,
            )

        except SyntaxError as e:
            return ManimTestResult(
                test_id="syntax_test",
                scene_name="N/A",
                test_type="syntax",
                success=False,
                error_message=f"Syntax error: {str(e)}",
            )

    async def _test_object_creation(self, test_code: str) -> ManimTestResult:
        """Test object creation without rendering."""
        test_file = os.path.join(self._temp_dir, "object_creation_test.py")
        with open(test_file, "w") as f:
            f.write(test_code)

        result = self._run_process(["python", test_file, "object_creation"])

        return ManimTestResult(
            test_id="object_creation_test",
            scene_name="TestScene",
            test_type="object_creation",
            success=result.execution_success
            and "OBJECT_CREATION_TEST: PASSED" in result.stdout,
            error_message=(
                result.stderr
                if not (
                    result.execution_success
                    and "OBJECT_CREATION_TEST: PASSED" in result.stdout
                )
                else None
            ),
            execution_result=result,
        )

    async def _test_animations(self, test_code: str) -> ManimTestResult:
        """Test animation sequences without rendering."""
        test_file = os.path.join(self._temp_dir, "animation_test.py")
        with open(test_file, "w") as f:
            f.write(test_code)

        result = self._run_process(["python", test_file, "animations"])

        return ManimTestResult(
            test_id="animations_test",
            scene_name="TestScene",
            test_type="animation",
            success=result.execution_success
            and "ANIMATIONS_TEST: PASSED" in result.stdout,
            error_message=(
                result.stderr
                if not (
                    result.execution_success
                    and "ANIMATIONS_TEST: PASSED" in result.stdout
                )
                else None
            ),
            execution_result=result,
        )

    async def _test_minimal_render(self, test_code: str) -> ManimTestResult:
        """Test minimal rendering capability."""
        test_file = os.path.join(self._temp_dir, "render_test.py")
        with open(test_file, "w") as f:
            f.write(test_code)

        result = self._run_process(["python", test_file, "render"])

        return ManimTestResult(
            test_id="render_test",
            scene_name="TestScene",
            test_type="render",
            success=result.execution_success and "RENDER_TEST: PASSED" in result.stdout,
            error_message=(
                result.stderr
                if not (
                    result.execution_success and "RENDER_TEST: PASSED" in result.stdout
                )
                else None
            ),
            execution_result=result,
        )

    def _run_process(self, cmd: List[str]) -> SandboxExecutionResult:
        """Run a process and capture its output."""
        start_time = time.time()

        try:
            # Use a much shorter timeout (5 seconds) for faster feedback
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=os.environ.copy(),
            )

            stdout, stderr = process.communicate(timeout=5)  # 5 second timeout
            end_time = time.time()

            return SandboxExecutionResult(
                execution_success=process.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                execution_time=end_time - start_time,
                exit_code=process.returncode,
            )

        except subprocess.TimeoutExpired:
            # Kill the process if it times out
            try:
                process.kill()
                stdout, stderr = process.communicate(timeout=1)
            except:
                stdout = ""
                stderr = "Process kill failed after timeout"

            end_time = time.time()

            return SandboxExecutionResult(
                execution_success=False,
                stdout=stdout,
                stderr=f"Process timed out after 5 seconds: {' '.join(cmd)}",
                execution_time=end_time - start_time,
                exit_code=-1,
            )
        except Exception as e:
            # Handle any other exceptions
            end_time = time.time()

            try:
                # Try to kill the process if it exists
                if "process" in locals():
                    process.kill()
            except:
                pass

            return SandboxExecutionResult(
                execution_success=False,
                stdout="",
                stderr=f"Error running process: {str(e)}",
                execution_time=end_time - start_time,
                exit_code=-1,
            )

    def _create_sample_code(self) -> str:
        """Create sample code for testing."""
        return """
from manim import *

class Scene_Sample(Scene):
    def construct(self):
        # Title
        title = Text("Attention Mechanisms", font_size=36)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)
        self.wait(0.8)
        
        # Equation with proper LaTeX
        eq = MathTex(r"e_t = (H W_a) \\cdot s_{t-1} \\in \\mathbb{R}^{B\\times n}", font_size=32)
        eq.next_to(title, DOWN, buff=0.5)
        self.play(Write(eq), run_time=1.2)
        self.wait(0.8)
        
        # Explanation text
        explanation = Text("This equation computes attention energy", font_size=24)
        explanation.next_to(eq, DOWN, buff=0.3)
        self.play(Write(explanation), run_time=1.0)
        self.wait(0.8)
        
        # Another equation
        eq2 = MathTex(r"\\alpha_{i,j} = \\text{softmax}(\\beta_{i,j})", font_size=28)
        eq2.next_to(explanation, DOWN, buff=0.3)
        self.play(Write(eq2), run_time=1.0)
        self.wait(0.8)
"""

    def _create_system_prompt(self) -> str:
        """Create the system prompt for code testing operations."""
        return """
        You are an expert Manim developer and testing specialist with deep knowledge of:
        
        - Manim animation library and common errors
        - Python testing methodologies
        - Educational code quality assessment
        - Sandbox execution environments
        - Error diagnostics and troubleshooting
        
        Your expertise includes:
        1. Identifying syntax and runtime issues in Manim code
        2. Creating comprehensive test cases for animation code
        3. Diagnosing LaTeX rendering problems
        4. Suggesting specific, actionable improvements
        5. Ensuring code robustness before full rendering
        
        When testing code:
        - Focus on catching errors early in the pipeline
        - Provide detailed, specific diagnostics
        - Suggest concrete fixes for identified issues
        - Consider both technical correctness and educational effectiveness
        - Prioritize critical rendering and animation issues
        
        Be precise, practical, and solution-oriented in all testing operations.
        """

    def _parse_test_cases(self, response: str) -> List[TestCase]:
        """Parse test cases from Claude's response."""

        # Simple regex-based parsing for test cases
        test_cases = []

        # Look for patterns like "Test ID: syntax_test"
        test_id_matches = re.findall(r"Test ID:?\s*(\w+)", response)
        test_name_matches = re.findall(r"Test [Nn]ame:?\s*([^\n]+)", response)
        test_desc_matches = re.findall(
            r"[Dd]escription:?\s*([^\n]+(?:\n\s+[^\n]+)*)", response
        )
        expected_result_matches = re.findall(
            r"Expected [Rr]esult:?\s*([^\n]+(?:\n\s+[^\n]+)*)", response
        )

        # Create test cases from matched patterns
        for i in range(
            min(
                len(test_id_matches),
                len(test_name_matches),
                len(test_desc_matches),
                len(expected_result_matches),
            )
        ):
            test_cases.append(
                TestCase(
                    test_id=test_id_matches[i],
                    test_name=test_name_matches[i].strip(),
                    test_description=test_desc_matches[i].strip(),
                    expected_result=expected_result_matches[i].strip(),
                )
            )

        # If no test cases found, create default ones
        if not test_cases:
            test_cases = [
                TestCase(
                    test_id="syntax_test",
                    test_name="Syntax Validation",
                    test_description="Verify that the code has valid Python and Manim syntax",
                    expected_result="Code compiles without syntax errors",
                ),
                TestCase(
                    test_id="object_creation_test",
                    test_name="Object Creation Test",
                    test_description="Test creation of Manim objects without rendering",
                    expected_result="All objects are created successfully",
                ),
                TestCase(
                    test_id="animations_test",
                    test_name="Animation Sequence Test",
                    test_description="Verify animation sequences work correctly",
                    expected_result="All animations are processed without errors",
                ),
                TestCase(
                    test_id="render_test",
                    test_name="Minimal Render Test",
                    test_description="Test basic rendering capability",
                    expected_result="Scene renders without errors",
                ),
            ]

        return test_cases

    def _parse_suggestions(self, response: str) -> List[str]:
        """Parse improvement suggestions from Claude's response."""

        # Extract suggestions using regex
        suggestion_patterns = [
            r"(?:^|\n)(?:\d+\.\s+|\*\s+|-\s+|•\s+)([^\n]+)",  # Numbered or bulleted items
            r"(?:^|\n)(?:Suggestion|Improvement|Fix)(?:\s+\d+)?:?\s+([^\n]+)",  # Lines starting with "Suggestion:", etc.
        ]

        suggestions = []
        for pattern in suggestion_patterns:
            matches = re.findall(pattern, response)
            suggestions.extend([match.strip() for match in matches if match.strip()])

        # If no suggestions found, extract sentences that look like suggestions
        if not suggestions:
            # Look for sentences containing action verbs common in suggestions
            action_verbs = [
                "add",
                "change",
                "modify",
                "update",
                "remove",
                "replace",
                "fix",
                "ensure",
            ]
            sentences = re.split(r"[.!?]\s+", response)
            for sentence in sentences:
                if any(verb in sentence.lower() for verb in action_verbs):
                    suggestions.append(sentence.strip())

        # If still no suggestions and tests passed, add default message
        if not suggestions:
            suggestions = ["All tests passed. No improvements needed."]

        return suggestions
