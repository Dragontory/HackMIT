"""
Dimension Specialist Agent implementation.

This agent analyzes Manim code to make intelligent decisions about 2D vs 3D
representations, optimizing educational effectiveness and implementation complexity.
"""

import logging
import re
import time
import uuid
from typing import List, Dict, Any, Optional

from ...domain.interfaces import IAgent
from ...domain.models import (
    AgentState,
    AgentResult,
    DimensionSpecializationResult,
    DimensionAnalysis,
    DimensionTransformation,
    DimensionRecommendation,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage


logger = logging.getLogger(__name__)


class DimensionSpecialistAgent(IAgent):
    """
    Specialized agent for handling 2D vs 3D animation decisions in Manim code.

    Uses Claude's spatial reasoning and educational understanding to:
    - Analyze concepts for dimensional requirements
    - Evaluate educational benefits of 2D vs 3D representations
    - Make intelligent dimension choices based on complexity and audience
    - Transform between 2D and 3D implementations
    - Optimize performance while maintaining educational effectiveness
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()

    @property
    def name(self) -> str:
        return "DimensionSpecialistAgent"

    @property
    def description(self) -> str:
        return "Handles 2D vs 3D animation decisions and implementations"

    async def process(self, state: AgentState) -> AgentResult:
        """Process state and specialize dimensional representations."""
        start_time = time.time()

        try:
            logger.info(f"Dimension Specialist processing: {state['content_title']}")

            # Get the code to analyze and specialize
            manim_code = state.get("manim_code", "")

            if not manim_code:
                # Create sample code for testing
                manim_code = self._create_sample_manim_code()
                logger.info("No Manim code provided, using sample code")

            # Get content strategy for context
            content_strategy = state.get("content_strategy")

            # Perform dimension specialization
            result = await self.specialize_dimensions(manim_code, content_strategy)

            # Update state
            state["dimension_specialization_result"] = result
            state["manim_code"] = result.specialized_code
            state["current_agent"] = self.name
            state["processing_stage"] = "dimension_specialization_complete"

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "analyses_created": len(result.dimension_analyses),
                    "transformations_applied": len(result.applied_transformations),
                    "recommendations_made": len(result.recommendations),
                    "overall_strategy": result.overall_dimension_strategy,
                    "processing_time": processing_time,
                },
            )

        except Exception as e:
            logger.error(f"Dimension Specialist error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Dimension specialization failed: {str(e)}"],
            )

    async def specialize_dimensions(
        self, manim_code: str, content_strategy: Optional[Dict[str, Any]] = None
    ) -> DimensionSpecializationResult:
        """
        Specialize dimensional representations in Manim code.

        Args:
            manim_code: The Manim Python code to analyze and specialize
            content_strategy: Optional content strategy for educational context

        Returns:
            DimensionSpecializationResult: Complete results with analyses and transformations
        """

        # Step 1: Analyze dimensional requirements
        dimension_analyses = await self.analyze_dimensional_requirements(
            manim_code, content_strategy
        )

        # Step 2: Generate dimension recommendations
        recommendations = await self.generate_dimension_recommendations(
            manim_code, dimension_analyses, content_strategy
        )

        # Step 3: Create dimension transformations
        transformations = await self.create_dimension_transformations(
            manim_code, dimension_analyses, recommendations
        )

        # Step 4: Apply transformations to code
        specialized_code, applied_transformations = (
            await self.apply_dimension_transformations(manim_code, transformations)
        )

        # Step 5: Determine overall strategy
        overall_strategy = self._determine_overall_strategy(
            dimension_analyses, applied_transformations
        )

        # Step 6: Generate performance and educational considerations
        performance_considerations = self._generate_performance_considerations(
            applied_transformations
        )
        educational_improvements = self._generate_educational_improvements(
            dimension_analyses, applied_transformations
        )
        implementation_notes = self._generate_implementation_notes(
            applied_transformations
        )

        # Determine success
        success = len(dimension_analyses) > 0 and (
            specialized_code != manim_code or len(applied_transformations) > 0
        )

        return DimensionSpecializationResult(
            original_code=manim_code,
            specialized_code=specialized_code,
            dimension_analyses=dimension_analyses,
            transformations=transformations,
            recommendations=recommendations,
            applied_transformations=applied_transformations,
            overall_dimension_strategy=overall_strategy,
            performance_considerations=performance_considerations,
            educational_improvements=educational_improvements,
            implementation_notes=implementation_notes,
            success=success,
        )

    async def analyze_dimensional_requirements(
        self, code: str, content_strategy: Optional[Dict[str, Any]] = None
    ) -> List[DimensionAnalysis]:
        """Analyze the dimensional requirements of concepts in the code."""

        # Prepare context for Claude
        context_parts = [
            "I need to analyze dimensional requirements for this Manim code:"
        ]
        context_parts.append(f"```python\n{code}\n```")

        if content_strategy:
            context_parts.append("Educational context:")
            context_parts.append(
                f"- Target audience: {getattr(content_strategy, 'target_audience', 'general')}"
            )
            context_parts.append(
                f"- Complexity level: {getattr(content_strategy, 'complexity_level', 'medium')}"
            )
            context_parts.append(
                f"- Learning objectives: {getattr(content_strategy, 'learning_objectives', [])}"
            )

        context_parts.append(
            "Please analyze each visual element and concept to determine optimal dimensional representation. "
            "Consider educational benefits, implementation complexity, and audience appropriateness for 2D vs 3D."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract dimension analyses
        return self._parse_dimension_analyses(response.content)

    async def generate_dimension_recommendations(
        self,
        code: str,
        analyses: List[DimensionAnalysis],
        content_strategy: Optional[Dict[str, Any]] = None,
    ) -> List[DimensionRecommendation]:
        """Generate recommendations for dimensional implementations."""

        # Prepare context for Claude
        context_parts = ["I need dimension recommendations based on this analysis:"]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Dimension analyses:")
        for analysis in analyses:
            context_parts.append(
                f"- {analysis.element_type}: {analysis.content_description}"
            )
            context_parts.append(
                f"  Current: {analysis.current_dimension}, Recommended: {analysis.recommended_dimension}"
            )
            context_parts.append(f"  Reasoning: {analysis.reasoning}")

        context_parts.append(
            "Please provide specific implementation recommendations for improving dimensional representations. "
            "Include practical steps, code examples, and consideration of trade-offs."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract recommendations
        return self._parse_dimension_recommendations(response.content)

    async def create_dimension_transformations(
        self,
        code: str,
        analyses: List[DimensionAnalysis],
        recommendations: List[DimensionRecommendation],
    ) -> List[DimensionTransformation]:
        """Create specific transformations for dimensional changes."""

        # Prepare context for Claude
        context_parts = ["I need to create dimension transformations for this code:"]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Based on these analyses and recommendations:")
        for analysis in analyses:
            if analysis.recommended_dimension != analysis.current_dimension:
                context_parts.append(
                    f"- Transform {analysis.element_type} from {analysis.current_dimension} to {analysis.recommended_dimension}"
                )

        for rec in recommendations:
            context_parts.append(
                f"- {rec.concept_name}: {rec.recommended_implementation}"
            )

        context_parts.append(
            "Please create specific transformations with code changes, imports, and configuration. "
            "Consider performance impact and implementation complexity."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract transformations
        return self._parse_dimension_transformations(response.content)

    async def apply_dimension_transformations(
        self, code: str, transformations: List[DimensionTransformation]
    ) -> tuple[str, List[DimensionTransformation]]:
        """Apply dimension transformations to the code."""

        if not transformations:
            return code, []

        # Filter high-priority transformations
        applicable_transformations = [
            t
            for t in transformations
            if t.implementation_complexity in ["easy", "medium"]
            and t.performance_impact != "high"
        ]

        if not applicable_transformations:
            return code, []

        # Prepare context for Claude
        context_parts = [
            "I need to apply these dimension transformations to this Manim code:"
        ]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Transformations to apply:")
        for i, transformation in enumerate(applicable_transformations, 1):
            context_parts.append(f"{i}. {transformation.description}")
            context_parts.append(
                f"   Type: {transformation.source_dimension} → {transformation.target_dimension}"
            )
            if transformation.code_changes:
                context_parts.append(f"   Changes: {transformation.code_changes}")
            if transformation.import_changes:
                context_parts.append(
                    f"   Imports: {', '.join(transformation.import_changes)}"
                )

        context_parts.append(
            "Please apply these transformations to create specialized dimensional code. "
            "Ensure the code remains functional and follows Manim best practices."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Extract the specialized code from the response
        specialized_code = self._extract_specialized_code(response.content, code)

        # Mark transformations as applied if the code changed
        applied_transformations = []
        if specialized_code != code:
            applied_transformations = applicable_transformations

        return specialized_code, applied_transformations

    def _determine_overall_strategy(
        self,
        analyses: List[DimensionAnalysis],
        applied_transformations: List[DimensionTransformation],
    ) -> str:
        """Determine the overall dimensional strategy."""

        if not analyses:
            return "2D"

        # Count recommendations
        dimension_counts = {"2D": 0, "3D": 0, "mixed": 0}

        for analysis in analyses:
            recommended = analysis.recommended_dimension
            if recommended in dimension_counts:
                dimension_counts[recommended] += 1

        # Determine strategy based on majority
        max_count = max(dimension_counts.values())
        strategies = [
            dim for dim, count in dimension_counts.items() if count == max_count
        ]

        # Prefer mixed if there's a tie between 2D and 3D
        if "2D" in strategies and "3D" in strategies:
            return "mixed"

        return strategies[0] if strategies else "2D"

    def _generate_performance_considerations(
        self, applied_transformations: List[DimensionTransformation]
    ) -> List[str]:
        """Generate performance considerations."""

        considerations = []

        for transformation in applied_transformations:
            if transformation.performance_impact == "high":
                considerations.append(
                    f"High performance impact from {transformation.description}"
                )
            elif transformation.estimated_time_cost > 2.0:
                considerations.append(
                    f"Increased render time ({transformation.estimated_time_cost:.1f}x) from {transformation.description}"
                )

        # Add general considerations
        if any(t.target_dimension == "3D" for t in applied_transformations):
            considerations.append("3D rendering requires more computational resources")
            considerations.append(
                "Consider using lower quality settings for faster iteration"
            )

        return considerations

    def _generate_educational_improvements(
        self,
        analyses: List[DimensionAnalysis],
        applied_transformations: List[DimensionTransformation],
    ) -> List[str]:
        """Generate educational improvements."""

        improvements = []

        for transformation in applied_transformations:
            if transformation.educational_impact == "high":
                improvements.append(
                    f"Significant educational enhancement from {transformation.description}"
                )
            elif transformation.quality_improvement > 0.3:
                improvements.append(
                    f"Improved visual clarity from {transformation.description}"
                )

        # Add analysis-based improvements
        for analysis in analyses:
            if analysis.educational_benefit_3d > analysis.educational_benefit_2d + 0.2:
                improvements.append(
                    f"3D representation significantly enhances understanding of {analysis.content_description}"
                )

        return improvements

    def _generate_implementation_notes(
        self, applied_transformations: List[DimensionTransformation]
    ) -> List[str]:
        """Generate implementation notes."""

        notes = []

        for transformation in applied_transformations:
            if transformation.implementation_complexity == "hard":
                notes.append(
                    f"Complex implementation required for {transformation.description}"
                )

            if transformation.import_changes:
                notes.append(
                    f"Additional imports needed: {', '.join(transformation.import_changes)}"
                )

            if transformation.camera_config:
                notes.append(
                    f"Camera configuration changes required for {transformation.description}"
                )

        return notes

    def _create_sample_manim_code(self) -> str:
        """Create sample Manim code for testing."""

        return """
from manim import *

class GeometryVisualization(Scene):
    def construct(self):
        # Title
        title = Text("3D Geometry Concepts", font_size=48)
        self.play(Write(title))
        self.wait(1)
        
        # 2D circle that could benefit from 3D representation
        circle = Circle(radius=2, color=BLUE)
        circle_label = Text("Circle", font_size=24)
        circle_label.next_to(circle, DOWN)
        
        self.play(Create(circle))
        self.play(Write(circle_label))
        self.wait(1)
        
        # Vector that could be shown in 3D
        vector = Arrow(ORIGIN, [2, 2, 0], color=RED)
        vector_label = Text("Vector", font_size=24)
        vector_label.next_to(vector.get_end(), UP)
        
        self.play(Create(vector))
        self.play(Write(vector_label))
        self.wait(1)
        
        # Mathematical equation
        equation = MathTex(r"x^2 + y^2 + z^2 = r^2")
        equation.to_edge(UP)
        
        self.play(Write(equation))
        self.wait(2)
"""

    def _create_system_prompt(self) -> str:
        """Create the system prompt for dimension specialization operations."""

        return """
        You are an expert Dimension Specialist for Manim animations with deep understanding of spatial reasoning and educational visualization.
        
        Your expertise includes:
        1. Spatial reasoning and dimensional analysis
        2. Educational benefits of 2D vs 3D representations
        3. Manim's 2D and 3D capabilities and limitations
        4. Performance implications of dimensional choices
        5. Audience-appropriate complexity decisions
        
        When analyzing dimensional requirements:
        - Consider the inherent spatial nature of concepts
        - Evaluate educational benefits of depth, rotation, and perspective
        - Assess audience readiness for 3D complexity
        - Balance visual clarity with implementation complexity
        - Consider performance and rendering implications
        
        Common indicators for 3D representation:
        - Spatial concepts (vectors, geometry, topology)
        - Multi-variable functions and surfaces
        - Physical simulations and mechanics
        - Complex mathematical objects (manifolds, transformations)
        - Concepts requiring depth perception
        
        Common indicators for 2D representation:
        - Simple algebraic concepts
        - Beginner-level mathematics
        - Performance-critical applications
        - Concepts well-represented in plane
        - Sequential or procedural explanations
        
        When recommending transformations:
        - Provide specific Manim code changes
        - Consider ThreeDScene vs Scene classes
        - Account for camera positioning and movement
        - Include necessary imports (ThreeDAxes, Surface, etc.)
        - Balance educational impact with implementation cost
        
        Be precise, educational, and performance-conscious in your recommendations.
        """

    def _parse_dimension_analyses(self, response: str) -> List[DimensionAnalysis]:
        """Parse dimension analyses from Claude's response."""

        analyses = []

        # Look for analysis blocks
        analysis_blocks = re.findall(
            r"(?:Analysis|Element)[^\n]*?:(.*?)(?=(?:Analysis|Element)|$)",
            response,
            re.DOTALL | re.IGNORECASE,
        )

        if not analysis_blocks:
            # Try numbered format
            analysis_blocks = re.findall(
                r"\d+[.]\s+(.*?)(?=\d+[.]|\Z)", response, re.DOTALL
            )

        for i, block in enumerate(analysis_blocks):
            element_id = f"element_{uuid.uuid4().hex[:8]}"

            # Extract element type
            element_type = "mobject"
            type_match = re.search(
                r"(?:Type|Element type)[:\s]*(.*?)(?:\n|$)", block, re.IGNORECASE
            )
            if type_match:
                element_type = type_match.group(1).strip()

            # Extract content description
            content_description = ""
            desc_match = re.search(
                r"(?:Description|Content)[:\s]*(.*?)(?:\n|$)", block, re.IGNORECASE
            )
            if desc_match:
                content_description = desc_match.group(1).strip()
            elif block.strip():
                # Use first line as description
                content_description = block.strip().split("\n")[0]

            # Extract current dimension
            current_dimension = "2D"
            current_match = re.search(
                r"(?:Current|Current dimension)[:\s]*(2D|3D|mixed)",
                block,
                re.IGNORECASE,
            )
            if current_match:
                current_dimension = current_match.group(1)

            # Extract recommended dimension
            recommended_dimension = "2D"
            rec_match = re.search(
                r"(?:Recommended|Recommendation)[:\s]*(2D|3D|mixed)",
                block,
                re.IGNORECASE,
            )
            if rec_match:
                recommended_dimension = rec_match.group(1)

            # Extract scores
            complexity_score = 0.5
            complexity_match = re.search(
                r"(?:Complexity)[:\s]*(\d+\.?\d*)", block, re.IGNORECASE
            )
            if complexity_match:
                complexity_score = min(float(complexity_match.group(1)), 1.0)

            # Extract educational benefits
            benefit_2d = 0.5
            benefit_3d = 0.5

            benefit_2d_match = re.search(
                r"(?:2D benefit|Educational benefit 2D)[:\s]*(\d+\.?\d*)",
                block,
                re.IGNORECASE,
            )
            if benefit_2d_match:
                benefit_2d = min(float(benefit_2d_match.group(1)), 1.0)

            benefit_3d_match = re.search(
                r"(?:3D benefit|Educational benefit 3D)[:\s]*(\d+\.?\d*)",
                block,
                re.IGNORECASE,
            )
            if benefit_3d_match:
                benefit_3d = min(float(benefit_3d_match.group(1)), 1.0)

            # Extract reasoning
            reasoning = ""
            reasoning_match = re.search(
                r"(?:Reasoning|Rationale)[:\s]*(.*?)(?=\n\n|\n[A-Z]|\Z)",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            if reasoning_match:
                reasoning = reasoning_match.group(1).strip()

            analysis = DimensionAnalysis(
                element_id=element_id,
                element_type=element_type,
                content_description=content_description,
                current_dimension=current_dimension,
                recommended_dimension=recommended_dimension,
                complexity_score=complexity_score,
                educational_benefit_2d=benefit_2d,
                educational_benefit_3d=benefit_3d,
                reasoning=reasoning,
            )

            analyses.append(analysis)

        return analyses

    def _parse_dimension_recommendations(
        self, response: str
    ) -> List[DimensionRecommendation]:
        """Parse dimension recommendations from Claude's response."""

        recommendations = []

        # Look for recommendation blocks
        rec_blocks = re.findall(
            r"(?:Recommendation|Suggest)[^\n]*?:(.*?)(?=(?:Recommendation|Suggest)|$)",
            response,
            re.DOTALL | re.IGNORECASE,
        )

        if not rec_blocks:
            # Try numbered format
            rec_blocks = re.findall(r"\d+[.]\s+(.*?)(?=\d+[.]|\Z)", response, re.DOTALL)

        for i, block in enumerate(rec_blocks):
            recommendation_id = f"rec_{uuid.uuid4().hex[:8]}"

            # Extract concept name
            concept_name = f"Concept {i+1}"
            concept_match = re.search(
                r"(?:Concept|Element|Object)[:\s]*(.*?)(?:\n|$)", block, re.IGNORECASE
            )
            if concept_match:
                concept_name = concept_match.group(1).strip()

            # Extract implementations
            current_impl = "Standard 2D implementation"
            current_match = re.search(
                r"(?:Current|Current implementation)[:\s]*(.*?)(?:\n|$)",
                block,
                re.IGNORECASE,
            )
            if current_match:
                current_impl = current_match.group(1).strip()

            recommended_impl = "Enhanced implementation"
            rec_match = re.search(
                r"(?:Recommended|Recommended implementation)[:\s]*(.*?)(?:\n|$)",
                block,
                re.IGNORECASE,
            )
            if rec_match:
                recommended_impl = rec_match.group(1).strip()

            # Extract dimension choice
            dimension_choice = "2D"
            dim_match = re.search(
                r"(?:Dimension|Choice)[:\s]*(2D|3D|mixed)", block, re.IGNORECASE
            )
            if dim_match:
                dimension_choice = dim_match.group(1)

            # Extract rationale
            rationale = ""
            rationale_match = re.search(
                r"(?:Rationale|Reasoning)[:\s]*(.*?)(?=\n\n|\n[A-Z]|\Z)",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            if rationale_match:
                rationale = rationale_match.group(1).strip()

            # Extract benefits and trade-offs
            benefits = []
            benefits_section = re.search(
                r"(?:Benefits)[:\s]*(.*?)(?=\n\n|\n[A-Z]|\Z)",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            if benefits_section:
                benefit_items = re.findall(
                    r"[-*]\s+(.*?)(?=[-*]|\n\n|\Z)",
                    benefits_section.group(1),
                    re.DOTALL,
                )
                benefits = [item.strip() for item in benefit_items if item.strip()]

            recommendation = DimensionRecommendation(
                recommendation_id=recommendation_id,
                concept_name=concept_name,
                current_implementation=current_impl,
                recommended_implementation=recommended_impl,
                dimension_choice=dimension_choice,
                rationale=rationale,
                benefits=benefits,
            )

            recommendations.append(recommendation)

        return recommendations

    def _parse_dimension_transformations(
        self, response: str
    ) -> List[DimensionTransformation]:
        """Parse dimension transformations from Claude's response."""

        transformations = []

        # Look for transformation blocks
        transform_blocks = re.findall(
            r"(?:Transform|Transformation)[^\n]*?:(.*?)(?=(?:Transform|Transformation)|$)",
            response,
            re.DOTALL | re.IGNORECASE,
        )

        if not transform_blocks:
            # Try numbered format
            transform_blocks = re.findall(
                r"\d+[.]\s+(.*?)(?=\d+[.]|\Z)", response, re.DOTALL
            )

        for i, block in enumerate(transform_blocks):
            transformation_id = f"transform_{uuid.uuid4().hex[:8]}"

            # Extract dimensions
            source_dimension = "2D"
            target_dimension = "3D"

            dim_match = re.search(
                r"(2D|3D)\s*(?:to|→|->\s*)(2D|3D)", block, re.IGNORECASE
            )
            if dim_match:
                source_dimension = dim_match.group(1)
                target_dimension = dim_match.group(2)

            # Extract element type
            element_type = "mobject"
            type_match = re.search(
                r"(?:Type|Element)[:\s]*(.*?)(?:\n|$)", block, re.IGNORECASE
            )
            if type_match:
                element_type = type_match.group(1).strip()

            # Extract transformation type
            transformation_type = "upgrade"
            if source_dimension == "3D" and target_dimension == "2D":
                transformation_type = "downgrade"
            elif source_dimension == target_dimension:
                transformation_type = "enhancement"

            # Extract code changes
            code_changes = ""
            code_match = re.search(r"```(?:python)?\n(.*?)\n```", block, re.DOTALL)
            if code_match:
                code_changes = code_match.group(1).strip()

            # Extract description
            description = f"Transform {element_type} from {source_dimension} to {target_dimension}"
            desc_match = re.search(
                r"(?:Description)[:\s]*(.*?)(?:\n|$)", block, re.IGNORECASE
            )
            if desc_match:
                description = desc_match.group(1).strip()

            # Extract impact assessments
            performance_impact = "medium"
            perf_match = re.search(
                r"(?:Performance impact)[:\s]*(low|medium|high)", block, re.IGNORECASE
            )
            if perf_match:
                performance_impact = perf_match.group(1).lower()

            educational_impact = "medium"
            edu_match = re.search(
                r"(?:Educational impact)[:\s]*(low|medium|high)", block, re.IGNORECASE
            )
            if edu_match:
                educational_impact = edu_match.group(1).lower()

            complexity = "medium"
            complex_match = re.search(
                r"(?:Complexity)[:\s]*(easy|medium|hard)", block, re.IGNORECASE
            )
            if complex_match:
                complexity = complex_match.group(1).lower()

            transformation = DimensionTransformation(
                transformation_id=transformation_id,
                source_dimension=source_dimension,
                target_dimension=target_dimension,
                element_type=element_type,
                transformation_type=transformation_type,
                code_changes=code_changes,
                performance_impact=performance_impact,
                educational_impact=educational_impact,
                implementation_complexity=complexity,
                description=description,
            )

            transformations.append(transformation)

        return transformations

    def _extract_specialized_code(self, response: str, original_code: str) -> str:
        """Extract specialized code from Claude's response."""

        # Look for code blocks
        code_blocks = re.findall(r"```(?:python)?\n(.*?)\n```", response, re.DOTALL)

        if code_blocks:
            # Use the largest code block (most likely the complete code)
            return max(code_blocks, key=len)

        # If no code block found, return the original code
        return original_code
