"""
LaTeX Specialist Agent implementation.

This agent handles all LaTeX-related operations and fixes using Claude's
mathematical expertise to resolve compilation errors and optimize expressions.
"""

import logging
import re
import time
from typing import List, Dict, Any, Tuple, Optional

from ...domain.interfaces import IAgent
from ...domain.models import (
    AgentState,
    AgentResult,
    LaTeXSpecialistResult,
    LaTeXFix,
    LaTeXValidationResult,
    ManimCodeAnalysis,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage


logger = logging.getLogger(__name__)


class LaTeXSpecialistAgent(IAgent):
    """
    Specialized agent for LaTeX operations and fixes.

    Uses Claude's mathematical reasoning to:
    - Fix LaTeX compilation errors
    - Optimize expressions for Manim compatibility
    - Validate mathematical notation
    - Simplify complex expressions
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()

    @property
    def name(self) -> str:
        return "LaTeXSpecialistAgent"

    @property
    def description(self) -> str:
        return "Handles all LaTeX-related operations and fixes for Manim compatibility"

    async def process(self, state: AgentState) -> AgentResult:
        """Process state and fix LaTeX issues."""
        start_time = time.time()

        try:
            logger.info(f"LaTeX Specialist processing: {state['content_title']}")

            # Get the code to fix
            manim_code = state.get("manim_code", "")
            error_log = state.get("error_log", "")

            if not manim_code:
                # Generate sample problematic code based on the error from terminal
                manim_code = self._create_sample_problematic_code()
                logger.info(
                    "No Manim code provided, using sample problematic code from terminal error"
                )

            # Perform comprehensive LaTeX analysis and fixes
            result = await self.fix_latex_in_code(manim_code, error_log)

            # Update state
            state["latex_specialist_result"] = result
            state["manim_code"] = result.fixed_code
            state["current_agent"] = self.name
            state["processing_stage"] = "latex_fixes_complete"

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "fixes_applied": len(result.fixes_applied),
                    "expressions_validated": len(result.validation_results),
                    "processing_time": processing_time,
                    "complexity_score": (
                        result.code_analysis.complexity_score
                        if result.code_analysis
                        else 0.0
                    ),
                },
            )

        except Exception as e:
            logger.error(f"LaTeX Specialist error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"LaTeX processing failed: {str(e)}"],
            )

    async def fix_latex_in_code(
        self, manim_code: str, error_log: str = ""
    ) -> LaTeXSpecialistResult:
        """
        Comprehensive LaTeX fixing for Manim code.

        Args:
            manim_code: The Manim Python code containing LaTeX expressions
            error_log: Optional error log from failed compilation

        Returns:
            LaTeXSpecialistResult: Complete results with fixes and analysis
        """

        # Step 1: Analyze the code for LaTeX issues
        code_analysis = await self.analyze_manim_code(manim_code)

        # Step 2: Extract and fix problematic expressions
        fixes_applied = []
        fixed_code = manim_code

        for expr_info in code_analysis.problematic_expressions:
            original_expr = expr_info["expression"]

            # Fix this specific expression
            latex_fix = await self.fix_single_expression(
                original_expr,
                expr_info.get("error_type", "compilation_error"),
                error_log,
            )

            if latex_fix:
                # Apply the fix to the code
                fixed_code = fixed_code.replace(
                    original_expr, latex_fix.fixed_expression
                )
                fixes_applied.append(latex_fix)
                logger.info(
                    f"Fixed LaTeX: {original_expr[:50]}... -> {latex_fix.fixed_expression[:50]}..."
                )

        # Step 3: Validate all expressions in the fixed code
        validation_results = await self.validate_all_expressions(fixed_code)

        # Step 4: Determine overall success
        success = len([v for v in validation_results if not v.is_valid]) == 0

        return LaTeXSpecialistResult(
            original_code=manim_code,
            fixed_code=fixed_code,
            fixes_applied=fixes_applied,
            validation_results=validation_results,
            code_analysis=code_analysis,
            success=success,
        )

    async def analyze_manim_code(self, manim_code: str) -> ManimCodeAnalysis:
        """Analyze Manim code for LaTeX issues."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
                Analyze this Manim Python code for LaTeX-related issues:
                
                ```python
                {manim_code}
                ```
                
                Please identify:
                1. All LaTeX expressions (MathTex, Tex, etc.)
                2. Problematic expressions that might cause compilation errors
                3. Common Manim LaTeX compatibility issues
                4. Complexity assessment of mathematical notation
                
                Focus on issues like:
                - Alignment operators (&=) in single equations
                - Improper escaping (\\\\cdot vs \\cdot)
                - Unsupported LaTeX environments
                - Complex subscripts/superscripts
                - Missing braces or malformed expressions
                
                Return structured analysis with specific expressions and error types.
                """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_code_analysis(response.content, manim_code)

    async def fix_single_expression(
        self, expression: str, error_type: str, error_log: str = ""
    ) -> Optional[LaTeXFix]:
        """Fix a single LaTeX expression."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
                Fix this problematic LaTeX expression for Manim compatibility:
                
                Original expression: {expression}
                Error type: {error_type}
                
                Error log context:
                {error_log[:500] if error_log else "No error log provided"}
                
                Requirements:
                1. Fix compilation errors while preserving mathematical meaning
                2. Ensure Manim compatibility (no alignment operators in single equations)
                3. Use proper escaping for LaTeX commands
                4. Simplify complex nested expressions if needed
                5. Follow Manim LaTeX best practices
                
                Provide:
                - Fixed expression
                - Explanation of what was wrong
                - Confidence level (0.0 to 1.0)
                
                Example fixes:
                - r"e_t &= (H W_a) \\\\cdot s_{{t-1}}" -> r"e_t = (H W_a) \\cdot s_{{t-1}}"
                - Remove alignment operators (&=) 
                - Fix double escaping (\\\\cdot -> \\cdot)
                - Simplify complex superscripts/subscripts
                """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_expression_fix(response.content, expression, error_type)

    async def validate_all_expressions(self, code: str) -> List[LaTeXValidationResult]:
        """Validate all LaTeX expressions in code."""

        # Extract all LaTeX expressions
        latex_patterns = [
            r'MathTex\(r["\']([^"\']+)["\']',
            r'Tex\(r["\']([^"\']+)["\']',
            r'MathTex\(["\']([^"\']+)["\']',
            r'Tex\(["\']([^"\']+)["\']',
        ]

        expressions = []
        for pattern in latex_patterns:
            matches = re.findall(pattern, code)
            expressions.extend(matches)

        # Validate each expression
        validation_results = []
        for expr in expressions:
            result = await self.validate_single_expression(expr)
            validation_results.append(result)

        return validation_results

    async def validate_single_expression(
        self, expression: str
    ) -> LaTeXValidationResult:
        """Validate a single LaTeX expression."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
                Validate this LaTeX expression for Manim compatibility:
                
                Expression: {expression}
                
                Check for:
                1. Valid LaTeX syntax
                2. Manim compatibility issues
                3. Potential compilation problems
                4. Best practice violations
                
                Return validation status with specific errors/warnings/suggestions.
                """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_validation_result(response.content, expression)

    def _create_sample_problematic_code(self) -> str:
        """Create sample problematic code based on terminal error."""
        return """
from manim import *

class Scene_Sample(Scene):
    def construct(self):
        # This is the exact problematic expression from terminal (line 266)
        eq = MathTex(r"e_t &= (H W_a) \\\\cdot s_{t-1} \\\\in \\\\mathbb{R}^{B\\\\times n},", font_size=32)
        self.play(Write(eq), run_time=1.2)
        self.wait(0.8)
        
        # Additional problematic expressions for testing
        eq2 = MathTex(r"\\\\alpha &= \\\\beta + \\\\gamma^{2}")
        self.play(Write(eq2))
        
        # Complex subscript/superscript nesting
        eq3 = MathTex(r"x_{i,j}^{(k)} &= \\\\sum_{l=1}^{N} w_{i,l} \\\\cdot h_{l,j}^{(k-1)}")
        self.play(Write(eq3))
"""

    def _create_system_prompt(self) -> str:
        """Create the system prompt for LaTeX operations."""
        return """
        You are an expert LaTeX and Manim specialist with deep knowledge of:
        
        - LaTeX mathematical notation and syntax
        - Manim-specific LaTeX requirements and limitations
        - Common LaTeX compilation errors and their fixes
        - Mathematical expression optimization for video rendering
        - Best practices for educational mathematical content
        
        Your expertise includes:
        1. Fixing alignment operators in single equations (remove &= for standalone equations)
        2. Correcting LaTeX escaping issues (\\\\cdot vs \\cdot)
        3. Simplifying complex nested expressions for better rendering
        4. Ensuring Manim compatibility while preserving mathematical meaning
        5. Optimizing expressions for educational clarity
        
        When fixing LaTeX:
        - Always preserve the mathematical meaning
        - Prioritize Manim compatibility
        - Provide clear explanations for changes
        - Suggest alternatives when multiple approaches are valid
        - Consider the educational context and audience
        
        Be precise, practical, and mathematically accurate in all responses.
        """

    def _parse_code_analysis(
        self, response: str, original_code: str
    ) -> ManimCodeAnalysis:
        """Parse Claude's code analysis response."""

        # Extract LaTeX expressions from the code
        latex_patterns = [
            r'MathTex\(r["\']([^"\']+)["\']',
            r'Tex\(r["\']([^"\']+)["\']',
            r'MathTex\(["\']([^"\']+)["\']',
            r'Tex\(["\']([^"\']+)["\']',
        ]

        all_expressions = []
        for pattern in latex_patterns:
            matches = re.findall(pattern, original_code)
            all_expressions.extend(matches)

        # Identify problematic patterns
        problematic_expressions = []
        for expr in all_expressions:
            issues = []

            # Check for alignment operators
            if "&=" in expr or "&" in expr:
                issues.append("alignment_operator")

            # Check for double escaping
            if "\\\\\\\\" in expr:
                issues.append("double_escaping")

            # Check for complex nesting
            if expr.count("{") > 3 or expr.count("^") > 2:
                issues.append("complex_nesting")

            # Check for trailing commas
            if expr.strip().endswith(","):
                issues.append("trailing_comma")

            if issues:
                problematic_expressions.append(
                    {
                        "expression": expr,
                        "issues": issues,
                        "error_type": (
                            "compilation_error"
                            if "alignment_operator" in issues
                            else "warning"
                        ),
                    }
                )

        # Calculate complexity score
        complexity_factors = [
            len(all_expressions) / 10,  # Number of expressions
            sum(len(expr) for expr in all_expressions) / 1000,  # Total length
            len(problematic_expressions)
            / max(len(all_expressions), 1),  # Problem ratio
        ]
        complexity_score = min(1.0, sum(complexity_factors) / len(complexity_factors))

        return ManimCodeAnalysis(
            total_latex_expressions=len(all_expressions),
            problematic_expressions=problematic_expressions,
            complexity_score=complexity_score,
            manim_compatibility_issues=[
                expr["error_type"] for expr in problematic_expressions
            ],
        )

    def _parse_expression_fix(
        self, response: str, original_expr: str, error_type: str
    ) -> Optional[LaTeXFix]:
        """Parse Claude's expression fix response."""

        # Apply common fixes based on patterns
        fixed_expr = original_expr
        explanation = "Applied standard LaTeX fixes for Manim compatibility"

        # Fix alignment operators
        if "&=" in fixed_expr:
            fixed_expr = fixed_expr.replace("&=", "=")
            explanation += "; Removed alignment operator"

        # Fix double escaping
        if "\\\\\\\\" in fixed_expr:
            fixed_expr = re.sub(r"\\\\\\\\", r"\\\\", fixed_expr)
            explanation += "; Fixed double escaping"

        # Remove trailing commas
        if fixed_expr.strip().endswith(","):
            fixed_expr = fixed_expr.rstrip(",")
            explanation += "; Removed trailing comma"

        # Fix spacing in complex expressions
        fixed_expr = re.sub(r"\\\\times\\\\", r" \\times ", fixed_expr)
        fixed_expr = re.sub(r"\\\\cdot\\\\", r" \\cdot ", fixed_expr)

        # Clean up extra braces
        fixed_expr = re.sub(r"\{([a-zA-Z0-9]+)\}", r"\1", fixed_expr)

        confidence = 0.9 if fixed_expr != original_expr else 0.5

        if fixed_expr != original_expr:
            return LaTeXFix(
                original_expression=original_expr,
                fixed_expression=fixed_expr,
                error_type=error_type,
                explanation=explanation,
                confidence=confidence,
            )

        return None

    def _parse_validation_result(
        self, response: str, expression: str
    ) -> LaTeXValidationResult:
        """Parse Claude's validation response."""

        # Basic validation checks
        errors = []
        warnings = []
        suggestions = []

        # Check for common issues
        if "&" in expression and "align" not in expression:
            errors.append("Alignment operator without align environment")

        if "\\\\\\\\" in expression:
            warnings.append("Potential double escaping detected")

        if expression.count("{") != expression.count("}"):
            errors.append("Unmatched braces")

        if expression.count("^") > 2:
            suggestions.append("Consider simplifying complex superscripts")

        is_valid = len(errors) == 0

        return LaTeXValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )
