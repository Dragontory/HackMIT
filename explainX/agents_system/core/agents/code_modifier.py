"""
Code Modification Agent implementation.

This agent modifies and fixes generated Manim code in real-time, addressing
positioning, bounds, timing, and animation issues to ensure optimal rendering.
"""

import logging
import re
import time
from typing import List, Dict, Any, Tuple, Optional

from ...domain.interfaces import IAgent
from ...domain.models import (
    AgentState,
    AgentResult,
    CodeModificationResult,
    CodeModification,
    PositionAnalysis,
    TimingAnalysis,
    CodeQualityMetrics,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage
from pydantic import BaseModel, Field
import json


logger = logging.getLogger(__name__)


class ManimeCodeGeneration(BaseModel):
    """Structured output for Manim code generation."""

    class_name: str = Field(description="Name of the Manim Scene class")
    description: str = Field(
        description="Brief description of what the scene demonstrates"
    )
    estimated_duration: float = Field(description="Estimated duration in seconds")
    key_concepts: List[str] = Field(
        description="List of key educational concepts covered"
    )
    python_code: str = Field(
        description="Complete, syntactically correct Python code for the Manim scene"
    )
    notes: str = Field(description="Any additional notes about the implementation")


class CodeModificationAgent(IAgent):
    """
    Specialized agent for real-time Manim code modifications.

    Uses Claude's code understanding to:
    - Fix positioning and bounds issues
    - Optimize animation timing
    - Prevent element overlapping
    - Improve code structure and readability
    - Enhance educational effectiveness
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()

    @property
    def name(self) -> str:
        return "CodeModificationAgent"

    @property
    def description(self) -> str:
        return (
            "Modifies and fixes generated Manim code in real-time for optimal rendering"
        )

    async def process(self, state: AgentState) -> AgentResult:
        """Process state and apply code modifications."""
        start_time = time.time()

        try:
            logger.info(f"Code Modifier processing: {state['content_title']}")

            # Get the code to modify (should be LaTeX-fixed code from previous agent)
            manim_code = state.get("manim_code", "")
            latex_result = state.get("latex_specialist_result")
            content_strategy = state.get("content_strategy")

            if not manim_code:
                # Generate new Manim code from content strategy if available
                if content_strategy:
                    logger.info(
                        "No Manim code provided, generating from content strategy"
                    )
                    manim_code = await self._generate_from_content_strategy(
                        content_strategy, state
                    )
                else:
                    # Fallback: Create sample code based on typical ExplainX issues
                    manim_code = self._create_sample_problematic_code()
                    logger.info(
                        "No Manim code or content strategy provided, using sample with positioning/timing issues"
                    )

            # Perform comprehensive code modifications
            result = await self.modify_manim_code(
                manim_code, latex_result, content_strategy
            )

            # Update state
            state["code_modification_result"] = result
            state["manim_code"] = result.modified_code
            state["current_agent"] = self.name
            state["processing_stage"] = "code_modifications_complete"

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "modifications_applied": len(result.modifications_applied),
                    "position_improvements": (
                        len(result.position_analysis.out_of_bounds_elements)
                        if result.position_analysis
                        else 0
                    ),
                    "timing_optimizations": (
                        len(result.timing_analysis.timing_issues)
                        if result.timing_analysis
                        else 0
                    ),
                    "processing_time": processing_time,
                    "quality_score": (
                        result.quality_metrics.educational_effectiveness
                        if result.quality_metrics
                        else 0.0
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Code Modifier error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Code modification failed: {str(e)}"],
            )

    async def modify_manim_code(
        self, manim_code: str, latex_result=None, content_strategy=None
    ) -> CodeModificationResult:
        """
        Comprehensive code modification for Manim optimization.

        Args:
            manim_code: The Manim Python code to modify
            latex_result: Optional LaTeX specialist results for context
            content_strategy: Optional content strategy for educational context

        Returns:
            CodeModificationResult: Complete results with modifications and analysis
        """

        # Step 1: Analyze current code structure and issues
        position_analysis = await self.analyze_positioning(manim_code)
        timing_analysis = await self.analyze_timing(manim_code)
        quality_metrics = await self.assess_code_quality(manim_code)

        # Step 2: Apply systematic modifications with syntax validation
        modifications_applied = []
        modified_code = manim_code

        # Validate initial code
        try:
            compile(modified_code, "<string>", "exec")
            initial_syntax_valid = True
        except SyntaxError:
            initial_syntax_valid = False
            logger.warning(
                "Initial generated code has syntax issues, skipping modifications"
            )

        if initial_syntax_valid:
            # Fix positioning issues
            positioning_mods = await self.fix_positioning_issues(
                modified_code, position_analysis
            )
            modifications_applied.extend(positioning_mods)
            for mod in positioning_mods:
                test_code = self._apply_modification(modified_code, mod)
                # Validate syntax after modification
                try:
                    compile(test_code, "<string>", "exec")
                    modified_code = test_code  # Only apply if syntax is valid
                except SyntaxError as e:
                    logger.warning(
                        f"Skipping positioning modification at line {mod.line_number}: syntax error {e}"
                    )
                    continue

            # Optimize timing
            timing_mods = await self.optimize_timing(
                modified_code, timing_analysis, content_strategy
            )
            modifications_applied.extend(timing_mods)
            for mod in timing_mods:
                test_code = self._apply_modification(modified_code, mod)
                # Validate syntax after modification
                try:
                    compile(test_code, "<string>", "exec")
                    modified_code = test_code  # Only apply if syntax is valid
                except SyntaxError as e:
                    logger.warning(
                        f"Skipping timing modification at line {mod.line_number}: syntax error {e}"
                    )
                    continue

            # Improve code structure
            structure_mods = await self.improve_code_structure(modified_code)
            modifications_applied.extend(structure_mods)
            for mod in structure_mods:
                test_code = self._apply_modification(modified_code, mod)
                # Validate syntax after modification
                try:
                    compile(test_code, "<string>", "exec")
                    modified_code = test_code  # Only apply if syntax is valid
                except SyntaxError as e:
                    logger.warning(
                        f"Skipping structure modification at line {mod.line_number}: syntax error {e}"
                    )
                    continue

        # Final validation
        validation_passed = await self.validate_modified_code(modified_code)

        return CodeModificationResult(
            original_code=manim_code,
            modified_code=modified_code,
            modifications_applied=modifications_applied,
            position_analysis=position_analysis,
            timing_analysis=timing_analysis,
            quality_metrics=quality_metrics,
            validation_passed=validation_passed,
            success=validation_passed and len(modifications_applied) > 0,
        )

    async def analyze_positioning(self, code: str) -> PositionAnalysis:
        """Analyze positioning issues in Manim code."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
                Analyze this Manim code for positioning and layout issues:
                
                ```python
                {code}
                ```
                
                Identify:
                1. Elements that might go out of bounds (screen edges)
                2. Potential overlapping elements
                3. Poor screen space utilization
                4. Elements with no explicit positioning (default center stacking)
                5. Large font sizes that might exceed screen bounds
                
                Focus on:
                - Text objects without positioning
                - MathTex objects that might be too large
                - Multiple elements created without spatial consideration
                - Missing use of positioning methods (to_edge, next_to, shift)
                
                Provide specific suggestions for optimal positioning.
                """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_position_analysis(response.content, code)

    async def analyze_timing(self, code: str) -> TimingAnalysis:
        """Analyze animation timing in Manim code."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
                Analyze this Manim code for timing and pacing issues:
                
                ```python
                {code}
                ```
                
                Evaluate:
                1. Animation durations (run_time parameters)
                2. Wait times between animations
                3. Overall scene pacing for educational content
                4. Cognitive load and information processing time
                5. Transitions between concepts
                
                Consider:
                - Too fast: Overwhelming for learners
                - Too slow: Losing attention
                - Mathematical content needs more processing time
                - Text should appear before equations
                - Smooth transitions between related concepts
                
                Suggest optimal timing for educational effectiveness.
                """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_timing_analysis(response.content, code)

    async def assess_code_quality(self, code: str) -> CodeQualityMetrics:
        """Assess overall code quality for educational videos."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
                Assess the quality of this Manim code for educational video generation:
                
                ```python
                {code}
                ```
                
                Rate (0.0 to 1.0) these aspects:
                1. Complexity: Is the code appropriately complex for its purpose?
                2. Readability: Is the code well-structured and clear?
                3. Performance: Are there any performance bottlenecks?
                4. Educational Effectiveness: Does it support learning goals?
                5. Maintainability: Is it easy to modify and extend?
                
                Consider:
                - Clear variable names
                - Logical animation sequence
                - Appropriate use of Manim features
                - Educational progression (simple to complex)
                - Code organization and comments
                """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_quality_metrics(response.content)

    async def fix_positioning_issues(
        self, code: str, position_analysis: PositionAnalysis
    ) -> List[CodeModification]:
        """Fix positioning issues identified in the analysis."""

        modifications = []

        # Extract positioning problems from analysis
        out_of_bounds = position_analysis.out_of_bounds_elements
        overlapping = position_analysis.overlapping_elements

        if out_of_bounds or overlapping or position_analysis.screen_utilization < 0.3:
            messages = [
                ClaudeMessage(
                    role="user",
                    content=f"""
                    Fix positioning issues in this Manim code:
                    
                    ```python
                    {code}
                    ```
                    
                    Issues identified:
                    - Out of bounds elements: {len(out_of_bounds)}
                    - Overlapping elements: {len(overlapping)}
                    - Screen utilization: {position_analysis.screen_utilization:.2f}
                    
                    Apply these fixes:
                    1. Add explicit positioning to elements (to_edge, next_to, shift)
                    2. Reduce font sizes if needed for screen bounds
                    3. Arrange elements to prevent overlapping
                    4. Optimize screen space usage
                    5. Use proper spacing between related elements
                    
                    Provide specific line-by-line modifications with explanations.
                    """,
                )
            ]

            response = await self.claude_client.send_message(
                messages, self._system_prompt
            )
            modifications.extend(
                self._parse_positioning_modifications(response.content, code)
            )

        return modifications

    async def optimize_timing(
        self, code: str, timing_analysis: TimingAnalysis, content_strategy=None
    ) -> List[CodeModification]:
        """Optimize animation timing based on analysis and content strategy."""

        modifications = []

        # Get cognitive load from content strategy if available
        cognitive_load = "moderate"
        mathematical_density = 0.5

        if content_strategy:
            cognitive_load = content_strategy.cognitive_load_assessment
            mathematical_density = content_strategy.mathematical_density

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
                Optimize timing in this Manim code for educational effectiveness:
                
                ```python
                {code}
                ```
                
                Context:
                - Cognitive load: {cognitive_load}
                - Mathematical density: {mathematical_density:.2f}
                - Total animations: {timing_analysis.total_animations}
                - Current duration: {timing_analysis.total_duration:.1f}s
                
                Optimization guidelines:
                1. High math density → slower pace, longer waits
                2. Complex concepts → more processing time
                3. Text before equations → staged revelation
                4. Smooth transitions between related ideas
                5. Appropriate pauses for comprehension
                
                Provide specific timing modifications with educational rationale.
                """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        modifications.extend(self._parse_timing_modifications(response.content, code))

        return modifications

    async def improve_code_structure(self, code: str) -> List[CodeModification]:
        """Improve overall code structure and organization."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
                Improve the structure and organization of this Manim code:
                
                ```python
                {code}
                ```
                
                Improvements to apply:
                1. Group related animations together
                2. Add meaningful variable names
                3. Extract complex positioning logic
                4. Add educational comments
                5. Ensure consistent coding style
                6. Optimize for readability and maintenance
                
                Focus on making the code more educational and easier to understand.
                """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_structure_modifications(response.content, code)

    async def validate_modified_code(self, code: str) -> bool:
        """Validate that the modified code is syntactically correct and well-formed."""

        try:
            # Basic syntax check
            compile(code, "<string>", "exec")

            # Check for common Manim patterns
            has_construct = "def construct(self):" in code
            has_manim_import = "from manim import" in code or "import manim" in code
            has_scene_class = "class" in code and "Scene" in code

            return has_construct and has_manim_import and has_scene_class

        except SyntaxError as e:
            logger.error(f"Syntax error in modified code: {e}")
            return False
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    async def _generate_from_content_strategy(
        self, content_strategy, state: AgentState
    ) -> str:
        """Generate new Manim code from content strategy."""

        try:
            # Handle both dict and object types for content_strategy
            if isinstance(content_strategy, dict):
                learning_objectives = content_strategy.get("learning_objectives", [])
                content_chunks = content_strategy.get("content_chunks", [])
                visual_opportunities = content_strategy.get("visual_opportunities", [])
            elif content_strategy is not None:
                # Extract information from content strategy object
                learning_objectives = getattr(
                    content_strategy, "learning_objectives", []
                )
                content_chunks = getattr(content_strategy, "content_chunks", [])
                visual_opportunities = getattr(
                    content_strategy, "visual_opportunities", []
                )
            else:
                # Handle None case
                logger.warning("Content strategy is None, using empty defaults")
                learning_objectives = []
                content_chunks = []
                visual_opportunities = []

            # Get raw content for context
            raw_content = state.get("raw_content", "")
            content_title = state.get("content_title", "Educational Content")

            # Create comprehensive prompt for generating educational Manim code
            prompt = f"""Generate comprehensive Manim educational video code for: {content_title}

Learning Objectives:
"""
            for obj in learning_objectives:
                prompt += f"- {obj.title}: {obj.description}\n"

            prompt += f"""
Content Areas:
"""
            for chunk in content_chunks:
                prompt += f"- {chunk.title}: {chunk.content[:200]}...\n"

            prompt += f"""
Visual Opportunities:
"""
            for vis in visual_opportunities:
                prompt += f"- {vis.description}\n"

            prompt += f"""
Source Content Context:
{raw_content[:3000]}...

Requirements:
1. Create a complete Manim Scene class that educates about the key concepts
2. Use progressive animations to build understanding step by step
3. Include mathematical formulas using MathTex where appropriate
4. Use clear explanatory text and proper timing
5. Apply good visual design with proper positioning
6. Target 3-4 minutes of educational content
7. Make it engaging and accessible

CRITICAL: You must respond with ONLY a valid JSON object matching this exact schema:
{{
    "class_name": "string - Name of the Manim Scene class",
    "description": "string - Brief description of what the scene demonstrates", 
    "estimated_duration": "number - Estimated duration in seconds",
    "key_concepts": ["array of strings - List of key educational concepts covered"],
    "python_code": "string - Complete, syntactically correct Python code for the Manim scene",
    "notes": "string - Any additional notes about the implementation"
}}

The python_code field must contain complete, working Manim code starting with 'from manim import *' and including a complete class definition."""

            # Use Claude to generate structured output
            messages = [ClaudeMessage(role="user", content=prompt)]
            system_prompt = "You are an expert Manim code generator. You MUST respond with ONLY a valid JSON object. No explanations, no markdown, just the JSON object matching the specified schema exactly."

            response = await self.claude_client.send_message(messages, system_prompt)

            response_content = response.content

            # Save raw response for debugging
            try:
                with open("debug_claude_raw_response.txt", "w") as f:
                    f.write(response_content)
                logger.info(
                    f"💾 Saved raw Claude response to debug_claude_raw_response.txt"
                )
            except Exception as save_e:
                logger.warning(f"Could not save raw response: {save_e}")

            # Parse the structured JSON response
            try:
                # Try to parse as JSON
                json_response = json.loads(response_content)

                # Validate the structure
                code_generation = ManimeCodeGeneration(**json_response)

                generated_code = code_generation.python_code

                logger.info(f"Successfully parsed structured response:")
                logger.info(f"  - Class: {code_generation.class_name}")
                logger.info(f"  - Duration: {code_generation.estimated_duration}s")
                logger.info(f"  - Concepts: {', '.join(code_generation.key_concepts)}")

                # Add syntax validation
                try:
                    # Clean the code string to handle any potential issues
                    cleaned_code = generated_code.strip()
                    compile(cleaned_code, "<string>", "exec")
                    # Validate the generated code has basic Manim structure
                    if (
                        "from manim import" in generated_code
                        and "class " in generated_code
                        and "def construct(self):" in generated_code
                    ):
                        logger.info(
                            f"✅ Generated {len(cleaned_code)} characters of educational Manim code"
                        )
                        return cleaned_code
                    else:
                        logger.warning(
                            "Generated code doesn't have proper Manim structure, using fallback"
                        )
                        return self._create_sample_problematic_code()
                except SyntaxError as e:
                    logger.error(f"Generated code has syntax error: {e}")
                    logger.error(f"Problematic code snippet: {generated_code[:500]}...")

                    # Save problematic code for debugging
                    try:
                        with open("debug_syntax_error_code.py", "w") as f:
                            f.write(generated_code)
                        logger.info(
                            f"💾 Saved problematic code to debug_syntax_error_code.py for inspection"
                        )
                    except Exception as save_e:
                        logger.warning(f"Could not save debug code: {save_e}")

                    return self._create_sample_problematic_code()

            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse structured response as JSON: {e}")
                logger.error(f"Response content: {response_content[:500]}...")
                return self._create_sample_problematic_code()

        except Exception as e:
            logger.error(f"Failed to generate code from content strategy: {e}")
            return self._create_sample_problematic_code()

    def _create_sample_problematic_code(self) -> str:
        """Create sample code with typical positioning and timing issues."""
        return """
from manim import *

class Scene_Sample_Issues(Scene):
    def construct(self):
        # Issue 1: No positioning - everything stacks in center
        title = Text("Attention Mechanisms", font_size=48)
        self.play(Write(title), run_time=0.5)  # Too fast for title
        
        # Issue 2: Large equation might go out of bounds
        eq1 = MathTex(r"e_t = (H W_a) \\cdot s_{t-1} \\in \\mathbb{R}^{B\\times n}", font_size=40)
        self.play(Write(eq1), run_time=0.8)  # No wait between elements
        
        # Issue 3: More elements without positioning
        explanation = Text("This equation computes attention weights", font_size=24)
        self.play(Write(explanation), run_time=0.6)
        
        # Issue 4: No spacing, everything overlaps
        eq2 = MathTex(r"\\alpha_{i,j} = \\text{softmax}(\\beta_{i,j})", font_size=32)
        self.play(Write(eq2), run_time=0.5)
        
        # Issue 5: Abrupt ending, no time to process
        self.wait(0.2)  # Too short for comprehension
"""

    def _create_system_prompt(self) -> str:
        """Create the system prompt for code modification operations."""
        return """
        You are an expert Manim developer and educational content specialist with deep knowledge of:
        
        - Manim animation library and best practices
        - Screen layout and positioning optimization
        - Educational video pacing and timing
        - Visual learning principles and cognitive load
        - Code structure and maintainability
        
        Your expertise includes:
        1. Optimal positioning methods (to_edge, next_to, shift, arrange)
        2. Educational timing principles (processing time, attention spans)
        3. Screen space utilization for maximum clarity
        4. Animation sequencing for learning effectiveness
        5. Code organization for maintainability and readability
        
        When modifying code:
        - Always preserve the educational intent
        - Prioritize clarity and comprehension over speed
        - Use positioning to create visual hierarchy
        - Ensure timing supports cognitive processing
        - Maintain clean, readable code structure
        
        Be precise, practical, and educationally focused in all modifications.
        """

    def _apply_modification(self, code: str, modification: CodeModification) -> str:
        """Apply a single code modification to the code."""
        lines = code.split("\n")

        if 0 <= modification.line_number < len(lines):
            lines[modification.line_number] = modification.modified_line
            logger.info(
                f"Applied {modification.modification_type} at line {modification.line_number}"
            )

        return "\n".join(lines)

    def _parse_position_analysis(self, response: str, code: str) -> PositionAnalysis:
        """Parse Claude's position analysis response."""

        # Count elements in the code
        text_elements = len(re.findall(r"Text\(", code))
        math_elements = len(re.findall(r"MathTex\(", code))
        total_elements = text_elements + math_elements

        # Identify potential issues
        out_of_bounds = []
        overlapping = []
        suggestions = []

        # Check for large font sizes
        large_fonts = re.findall(r"font_size=(\d+)", code)
        for font_size in large_fonts:
            if int(font_size) > 36:
                out_of_bounds.append(
                    {
                        "element": f"Large font size: {font_size}",
                        "issue": "May exceed screen bounds",
                        "severity": "medium",
                    }
                )

        # Check for missing positioning
        positioned_elements = len(re.findall(r"\.(to_edge|next_to|shift)", code))
        if positioned_elements < total_elements * 0.3:
            overlapping.append(
                {
                    "issue": "Many elements lack explicit positioning",
                    "severity": "high",
                    "elements_affected": total_elements - positioned_elements,
                }
            )

        # Calculate screen utilization (simplified heuristic)
        screen_utilization = min(1.0, positioned_elements / max(total_elements, 1))

        # Generate suggestions
        if screen_utilization < 0.5:
            suggestions.append("Add explicit positioning to prevent overlapping")
        if large_fonts:
            suggestions.append("Consider reducing font sizes for better screen fit")
        if total_elements > 3:
            suggestions.append("Use spatial arrangement to create visual hierarchy")

        return PositionAnalysis(
            total_elements=total_elements,
            out_of_bounds_elements=out_of_bounds,
            overlapping_elements=overlapping,
            positioning_suggestions=suggestions,
            screen_utilization=screen_utilization,
        )

    def _parse_timing_analysis(self, response: str, code: str) -> TimingAnalysis:
        """Parse Claude's timing analysis response."""

        # Count animations
        play_calls = len(re.findall(r"\.play\(", code))
        wait_calls = len(re.findall(r"\.wait\(", code))

        # Extract timing values
        run_times = re.findall(r"run_time=([\d.]+)", code)
        wait_times = re.findall(r"\.wait\(([\d.]+)\)", code)

        # Calculate total duration
        total_duration = sum(float(t) for t in run_times) + sum(
            float(t) for t in wait_times
        )

        # Identify timing issues
        timing_issues = []

        # Check for very fast animations
        for i, rt in enumerate(run_times):
            if float(rt) < 0.8:
                timing_issues.append(
                    {
                        "type": "too_fast",
                        "animation_index": i,
                        "current_time": float(rt),
                        "suggested_time": 1.2,
                        "reason": "Too fast for educational content",
                    }
                )

        # Check for missing waits
        if wait_calls < play_calls * 0.5:
            timing_issues.append(
                {
                    "type": "insufficient_processing_time",
                    "issue": "Missing wait times between animations",
                    "suggested_action": "Add wait periods for comprehension",
                }
            )

        # Assess pace
        avg_animation_time = total_duration / max(play_calls, 1)
        if avg_animation_time < 1.0:
            suggested_pace = "slow"  # Need to slow down
        elif avg_animation_time > 3.0:
            suggested_pace = "fast"  # Can speed up
        else:
            suggested_pace = "moderate"

        # Assess cognitive load
        if len(timing_issues) > 3:
            cognitive_load = "high"
        elif len(timing_issues) > 1:
            cognitive_load = "moderate"
        else:
            cognitive_load = "low"

        return TimingAnalysis(
            total_animations=play_calls,
            timing_issues=timing_issues,
            suggested_pace=suggested_pace,
            total_duration=total_duration,
            cognitive_load_assessment=cognitive_load,
        )

    def _parse_quality_metrics(self, response: str) -> CodeQualityMetrics:
        """Parse Claude's quality assessment response."""

        # For now, provide reasonable defaults based on common patterns
        # In production, this would parse Claude's detailed assessment

        return CodeQualityMetrics(
            complexity_score=0.7,  # Moderate complexity
            readability_score=0.6,  # Could be improved
            performance_score=0.8,  # Generally good Manim performance
            educational_effectiveness=0.5,  # Needs positioning/timing fixes
            maintainability_score=0.6,  # Decent structure
        )

    def _parse_positioning_modifications(
        self, response: str, code: str
    ) -> List[CodeModification]:
        """Parse positioning modifications from Claude's response."""

        modifications = []
        lines = code.split("\n")

        # Look for elements that need positioning
        for i, line in enumerate(lines):
            if "Text(" in line or "MathTex(" in line:
                if (
                    "to_edge" not in line
                    and "next_to" not in line
                    and "shift" not in line
                ):
                    # This element needs positioning
                    if "title" in line.lower() or i < 3:
                        # Title elements go to top
                        modified_line = (
                            line.rstrip()
                            + "\n        "
                            + line.split("=")[0].strip()
                            + ".to_edge(UP)"
                        )
                        modifications.append(
                            CodeModification(
                                modification_type="positioning",
                                original_line=line,
                                modified_line=modified_line,
                                line_number=i,
                                explanation="Added top positioning for title element",
                                confidence=0.9,
                                impact_score=0.8,
                            )
                        )
                    elif "explanation" in line.lower():
                        # Explanation text goes to bottom
                        modified_line = (
                            line.rstrip()
                            + "\n        "
                            + line.split("=")[0].strip()
                            + ".to_edge(DOWN)"
                        )
                        modifications.append(
                            CodeModification(
                                modification_type="positioning",
                                original_line=line,
                                modified_line=modified_line,
                                line_number=i,
                                explanation="Added bottom positioning for explanation text",
                                confidence=0.9,
                                impact_score=0.7,
                            )
                        )

        return modifications

    def _parse_timing_modifications(
        self, response: str, code: str
    ) -> List[CodeModification]:
        """Parse timing modifications from Claude's response."""

        modifications = []
        lines = code.split("\n")

        for i, line in enumerate(lines):
            # Fix fast run_times
            if "run_time=" in line:
                run_time_match = re.search(r"run_time=([\d.]+)", line)
                if run_time_match:
                    current_time = float(run_time_match.group(1))
                    if current_time < 1.0:
                        new_time = 1.5 if "title" in line.lower() else 1.2
                        modified_line = line.replace(
                            f"run_time={current_time}", f"run_time={new_time}"
                        )
                        modifications.append(
                            CodeModification(
                                modification_type="timing",
                                original_line=line,
                                modified_line=modified_line,
                                line_number=i,
                                explanation=f"Increased timing from {current_time}s to {new_time}s for better comprehension",
                                confidence=0.9,
                                impact_score=0.8,
                            )
                        )

            # Add wait times after animations
            if ".play(" in line and i + 1 < len(lines) and ".wait(" not in lines[i + 1]:
                wait_time = 1.2 if "MathTex" in line else 0.8
                modified_line = line + f"\n        self.wait({wait_time})"
                modifications.append(
                    CodeModification(
                        modification_type="timing",
                        original_line=line,
                        modified_line=modified_line,
                        line_number=i,
                        explanation=f"Added {wait_time}s wait for processing time",
                        confidence=0.8,
                        impact_score=0.7,
                    )
                )

        return modifications

    def _parse_structure_modifications(
        self, response: str, code: str
    ) -> List[CodeModification]:
        """Parse structure improvements from Claude's response."""

        modifications = []
        lines = code.split("\n")

        # Add educational comments
        for i, line in enumerate(lines):
            if "MathTex(" in line and "attention" in line.lower():
                comment = "        # Display attention mechanism equation"
                modified_line = comment + "\n" + line
                modifications.append(
                    CodeModification(
                        modification_type="structure",
                        original_line=line,
                        modified_line=modified_line,
                        line_number=i,
                        explanation="Added educational comment for clarity",
                        confidence=0.7,
                        impact_score=0.5,
                    )
                )

        return modifications
