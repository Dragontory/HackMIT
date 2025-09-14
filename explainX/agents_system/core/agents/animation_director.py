"""
Animation Director Agent implementation.

This agent analyzes Manim code and directs animations for maximum educational impact,
focusing on timing, pacing, narrative flow, and educational effectiveness.
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
    AnimationDirectionResult,
    AnimationSequence,
    AnimationTimeline,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage


logger = logging.getLogger(__name__)


class AnimationDirectorAgent(IAgent):
    """
    Specialized agent for directing animations in Manim code for maximum educational impact.

    Uses Claude's educational understanding to:
    - Analyze educational flow and concept progression
    - Design optimal animation timing and pacing
    - Create narrative structure for better learning
    - Coordinate multiple visual elements for clarity
    - Enhance educational effectiveness through strategic direction
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()

    @property
    def name(self) -> str:
        return "AnimationDirectorAgent"

    @property
    def description(self) -> str:
        return "Directs and coordinates animations for maximum educational impact"

    async def process(self, state: AgentState) -> AgentResult:
        """Process state and direct animations for educational impact."""
        start_time = time.time()

        try:
            logger.info(f"Animation Director processing: {state['content_title']}")

            # Get the code to analyze and direct
            manim_code = state.get("manim_code", "")

            if not manim_code:
                # Create sample code for testing
                manim_code = self._create_sample_manim_code()
                logger.info("No Manim code provided, using sample code")

            # Get content strategy for educational context
            content_strategy = state.get("content_strategy")

            # Perform animation direction
            result = await self.direct_animations(manim_code, content_strategy)

            # Update state
            state["animation_direction_result"] = result
            state["manim_code"] = result.directed_code
            state["current_agent"] = self.name
            state["processing_stage"] = "animation_direction_complete"

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "sequences_created": len(result.sequences),
                    "educational_enhancements": len(result.educational_enhancements),
                    "timing_adjustments": len(result.timing_adjustments),
                    "narrative_elements": len(result.narrative_elements),
                    "processing_time": processing_time,
                },
            )

        except Exception as e:
            logger.error(f"Animation Director error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Animation direction failed: {str(e)}"],
            )

    async def direct_animations(
        self, manim_code: str, content_strategy: Optional[Dict[str, Any]] = None
    ) -> AnimationDirectionResult:
        """
        Direct animations in Manim code for maximum educational impact.

        Args:
            manim_code: The Manim Python code to analyze and direct
            content_strategy: Optional content strategy for educational context

        Returns:
            AnimationDirectionResult: Complete results with timeline and enhancements
        """

        # Step 1: Analyze educational flow and create timeline
        timeline = await self.analyze_educational_flow(manim_code, content_strategy)

        # Step 2: Create animation sequences
        sequences = await self.create_animation_sequences(manim_code, timeline)

        # Step 3: Generate educational enhancements
        educational_enhancements = await self.generate_educational_enhancements(
            manim_code, timeline, sequences
        )

        # Step 4: Create timing adjustments
        timing_adjustments = await self.create_timing_adjustments(
            manim_code, timeline, sequences
        )

        # Step 5: Add narrative elements
        narrative_elements = await self.add_narrative_elements(
            manim_code, timeline, sequences
        )

        # Step 6: Generate pacing improvements
        pacing_improvements = await self.generate_pacing_improvements(
            manim_code, timeline, sequences
        )

        # Step 7: Apply all improvements to create directed code
        directed_code = await self.apply_direction_improvements(
            manim_code,
            educational_enhancements,
            timing_adjustments,
            narrative_elements,
            pacing_improvements,
        )

        # Determine success
        success = len(sequences) > 0 and directed_code != manim_code

        return AnimationDirectionResult(
            original_code=manim_code,
            directed_code=directed_code,
            timeline=timeline,
            sequences=sequences,
            educational_enhancements=educational_enhancements,
            timing_adjustments=timing_adjustments,
            narrative_elements=narrative_elements,
            pacing_improvements=pacing_improvements,
            success=success,
        )

    def _create_sample_manim_code(self) -> str:
        """Create sample Manim code for testing."""

        return """
from manim import *

class EducationalScene(Scene):
    def construct(self):
        # Title
        title = Text("Learning Mathematics", font_size=48)
        self.play(Write(title))
        self.wait(1)
        
        # Formula introduction
        formula = MathTex(r"f(x) = x^2 + 2x + 1")
        formula.next_to(title, DOWN, buff=1)
        self.play(Write(formula))
        self.wait(1)
        
        # Graph
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 10, 2],
            x_length=6,
            y_length=4
        )
        graph = axes.plot(lambda x: x**2 + 2*x + 1, color=BLUE)
        
        self.play(Create(axes))
        self.play(Create(graph))
        self.wait(2)
"""

    async def analyze_educational_flow(
        self, code: str, content_strategy: Optional[Dict[str, Any]] = None
    ) -> AnimationTimeline:
        """Analyze the educational flow and create an animation timeline."""

        # Prepare context for Claude
        context_parts = ["I need to analyze the educational flow in this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        if content_strategy:
            context_parts.append("Content strategy context:")
            context_parts.append(
                f"- Learning objectives: {getattr(content_strategy, 'learning_objectives', [])}"
            )
            context_parts.append(
                f"- Target audience: {getattr(content_strategy, 'target_audience', 'general')}"
            )
            context_parts.append(
                f"- Complexity level: {getattr(content_strategy, 'complexity_level', 'medium')}"
            )

        context_parts.append(
            "Please analyze the educational flow and create a comprehensive timeline. "
            "Focus on concept progression, learning objectives, and optimal educational approach."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract timeline
        return self._parse_animation_timeline(response.content, code)

    async def create_animation_sequences(
        self, code: str, timeline: AnimationTimeline
    ) -> List[AnimationSequence]:
        """Create detailed animation sequences based on the timeline."""

        # Prepare context for Claude
        context_parts = ["I need to create animation sequences for this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Educational timeline:")
        context_parts.append(f"- Title: {timeline.title}")
        context_parts.append(f"- Learning objectives: {timeline.learning_objectives}")
        context_parts.append(f"- Concept flow: {timeline.concept_flow}")
        context_parts.append(f"- Educational approach: {timeline.educational_approach}")

        context_parts.append(
            "Please create detailed animation sequences that follow the educational timeline. "
            "Each sequence should have a clear educational purpose and optimal timing."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract sequences
        return self._parse_animation_sequences(response.content, timeline)

    async def generate_educational_enhancements(
        self, code: str, timeline: AnimationTimeline, sequences: List[AnimationSequence]
    ) -> List[Dict[str, Any]]:
        """Generate educational enhancements for the animation."""

        # Prepare context for Claude
        context_parts = ["I need educational enhancements for this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Current animation sequences:")
        for i, seq in enumerate(sequences, 1):
            context_parts.append(f"{i}. {seq.name} - {seq.educational_purpose}")

        context_parts.append(
            "Please suggest specific educational enhancements that will improve learning outcomes. "
            "Focus on clarity, concept reinforcement, and pedagogical effectiveness."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract enhancements
        return self._parse_educational_enhancements(response.content)

    async def create_timing_adjustments(
        self, code: str, timeline: AnimationTimeline, sequences: List[AnimationSequence]
    ) -> List[Dict[str, Any]]:
        """Create timing adjustments for optimal learning pace."""

        # Prepare context for Claude
        context_parts = ["I need timing adjustments for this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Animation timeline:")
        context_parts.append(f"- Total duration: {timeline.total_duration} seconds")
        context_parts.append(f"- Pacing strategy: {timeline.pacing_strategy}")

        context_parts.append("Current sequences:")
        for seq in sequences:
            context_parts.append(
                f"- {seq.name}: {seq.duration}s ({seq.complexity_level})"
            )

        context_parts.append(
            "Please suggest timing adjustments to optimize learning pace. "
            "Consider cognitive load, concept complexity, and attention span."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract timing adjustments
        return self._parse_timing_adjustments(response.content)

    async def add_narrative_elements(
        self, code: str, timeline: AnimationTimeline, sequences: List[AnimationSequence]
    ) -> List[Dict[str, Any]]:
        """Add narrative elements to enhance understanding."""

        # Prepare context for Claude
        context_parts = ["I need narrative elements for this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Educational context:")
        context_parts.append(f"- Target audience: {timeline.target_audience}")
        context_parts.append(f"- Learning objectives: {timeline.learning_objectives}")
        context_parts.append(f"- Concept flow: {timeline.concept_flow}")

        context_parts.append(
            "Please suggest narrative elements that will enhance understanding. "
            "Include text overlays, explanatory animations, and transitional elements."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract narrative elements
        return self._parse_narrative_elements(response.content)

    async def generate_pacing_improvements(
        self, code: str, timeline: AnimationTimeline, sequences: List[AnimationSequence]
    ) -> List[Dict[str, Any]]:
        """Generate pacing improvements for better learning flow."""

        # Prepare context for Claude
        context_parts = ["I need pacing improvements for this Manim code:"]
        context_parts.append(f"```python\n{code}\n```")

        context_parts.append("Current pacing:")
        for seq in sequences:
            context_parts.append(f"- {seq.name}: {seq.duration}s")

        context_parts.append(
            "Please suggest pacing improvements for optimal learning flow. "
            "Consider attention span, concept difficulty, and natural breaks."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract pacing improvements
        return self._parse_pacing_improvements(response.content)

    def _create_system_prompt(self) -> str:
        """Create the system prompt for animation direction operations."""

        return """
        You are an expert Animation Director specializing in educational Manim animations.
        
        Your expertise includes:
        1. Educational flow and concept progression
        2. Optimal animation timing and pacing
        3. Narrative structure for enhanced learning
        4. Visual coordination for maximum clarity
        5. Strategic direction for educational effectiveness
        
        When analyzing Manim code:
        - Identify educational concepts and their relationships
        - Assess current animation timing and flow
        - Evaluate narrative structure and clarity
        - Consider cognitive load and learning progression
        - Analyze visual coordination and emphasis
        
        When directing animations:
        - Create logical concept progression
        - Design optimal timing for comprehension
        - Develop narrative elements that enhance understanding
        - Coordinate visual elements for maximum impact
        - Ensure educational objectives are met
        
        Be educational, strategic, and learner-focused in your direction.
        """

    async def apply_direction_improvements(
        self,
        code: str,
        educational_enhancements: List[Dict[str, Any]],
        timing_adjustments: List[Dict[str, Any]],
        narrative_elements: List[Dict[str, Any]],
        pacing_improvements: List[Dict[str, Any]],
    ) -> str:
        """Apply all direction improvements to the Manim code."""

        if not any(
            [
                educational_enhancements,
                timing_adjustments,
                narrative_elements,
                pacing_improvements,
            ]
        ):
            return code

        # Prepare context for Claude
        context_parts = [
            "I need to apply these direction improvements to this Manim code:"
        ]
        context_parts.append(f"```python\n{code}\n```")

        # Add educational enhancements
        if educational_enhancements:
            context_parts.append("Educational enhancements:")
            for enhancement in educational_enhancements:
                context_parts.append(f"- {enhancement.get('description', '')}")

        # Add timing adjustments
        if timing_adjustments:
            context_parts.append("Timing adjustments:")
            for adjustment in timing_adjustments:
                context_parts.append(f"- {adjustment.get('description', '')}")

        # Add narrative elements
        if narrative_elements:
            context_parts.append("Narrative elements:")
            for element in narrative_elements:
                context_parts.append(f"- {element.get('description', '')}")

        # Add pacing improvements
        if pacing_improvements:
            context_parts.append("Pacing improvements:")
            for improvement in pacing_improvements:
                context_parts.append(f"- {improvement.get('description', '')}")

        context_parts.append(
            "Please apply these improvements to create a directed version of the code. "
            "Focus on educational effectiveness, optimal timing, and clear narrative flow."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Extract the directed code from the response
        return self._extract_directed_code(response.content, code)

    def _parse_animation_timeline(self, response: str, code: str) -> AnimationTimeline:
        """Parse animation timeline from Claude's response."""

        timeline_id = f"timeline_{uuid.uuid4().hex[:8]}"
        title = "Animation Timeline"

        # Try to extract title
        title_match = re.search(
            r"(?:Title|Timeline)[:\s]*(.*?)(?:\n|$)", response, re.IGNORECASE
        )
        if title_match:
            title = title_match.group(1).strip()

        # Extract learning objectives
        learning_objectives = []
        objectives_section = re.search(
            r"(?:Learning objectives|Objectives)[:\s]*(.*?)(?=\n\n|\n[A-Z]|\Z)",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if objectives_section:
            objectives_text = objectives_section.group(1).strip()
            objectives = re.findall(
                r"[-*]\s+(.*?)(?=[-*]|\n\n|\Z)", objectives_text, re.DOTALL
            )
            learning_objectives = [obj.strip() for obj in objectives if obj.strip()]

        # Extract concept flow
        concept_flow = []
        flow_section = re.search(
            r"(?:Concept flow|Flow)[:\s]*(.*?)(?=\n\n|\n[A-Z]|\Z)",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if flow_section:
            flow_text = flow_section.group(1).strip()
            concepts = re.findall(r"[-*]\s+(.*?)(?=[-*]|\n\n|\Z)", flow_text, re.DOTALL)
            concept_flow = [concept.strip() for concept in concepts if concept.strip()]

        # Extract educational approach
        educational_approach = "progressive"
        approach_match = re.search(
            r"(?:Educational approach|Approach)[:\s]*(.*?)(?:\n|$)",
            response,
            re.IGNORECASE,
        )
        if approach_match:
            educational_approach = approach_match.group(1).strip()

        # Extract target audience
        target_audience = "general"
        audience_match = re.search(
            r"(?:Target audience|Audience)[:\s]*(.*?)(?:\n|$)", response, re.IGNORECASE
        )
        if audience_match:
            target_audience = audience_match.group(1).strip()

        # Extract pacing strategy
        pacing_strategy = "balanced"
        pacing_match = re.search(
            r"(?:Pacing strategy|Pacing)[:\s]*(.*?)(?:\n|$)", response, re.IGNORECASE
        )
        if pacing_match:
            pacing_strategy = pacing_match.group(1).strip()

        return AnimationTimeline(
            timeline_id=timeline_id,
            title=title,
            learning_objectives=learning_objectives,
            concept_flow=concept_flow,
            educational_approach=educational_approach,
            target_audience=target_audience,
            pacing_strategy=pacing_strategy,
        )

    def _parse_animation_sequences(
        self, response: str, timeline: AnimationTimeline
    ) -> List[AnimationSequence]:
        """Parse animation sequences from Claude's response."""

        sequences = []

        # Look for sequence blocks
        sequence_blocks = re.findall(
            r"(?:Sequence|Animation)[^\n]*?:(.*?)(?=(?:Sequence|Animation)|$)",
            response,
            re.DOTALL | re.IGNORECASE,
        )

        if not sequence_blocks:
            # Try to find numbered sequences
            sequence_blocks = re.findall(
                r"\d+[.]\s+(.*?)(?=\d+[.]|\Z)", response, re.DOTALL
            )

        for i, block in enumerate(sequence_blocks):
            sequence_id = f"sequence_{uuid.uuid4().hex[:8]}"
            name = f"Sequence {i+1}"

            # Try to extract sequence name
            name_match = re.search(r"^(.*?)(?:\n|$)", block.strip())
            if name_match:
                name = name_match.group(1).strip()

            # Extract educational purpose
            purpose_match = re.search(
                r"(?:Purpose|Educational purpose)[:\s]*(.*?)(?:\n|$)",
                block,
                re.IGNORECASE,
            )
            educational_purpose = (
                purpose_match.group(1).strip() if purpose_match else ""
            )

            # Extract target concept
            concept_match = re.search(
                r"(?:Target concept|Concept)[:\s]*(.*?)(?:\n|$)", block, re.IGNORECASE
            )
            target_concept = concept_match.group(1).strip() if concept_match else ""

            # Extract duration
            duration_match = re.search(
                r"(?:Duration)[:\s]*(\d+\.?\d*)", block, re.IGNORECASE
            )
            duration = float(duration_match.group(1)) if duration_match else 3.0

            # Extract complexity level
            complexity_level = "medium"
            complexity_match = re.search(
                r"(?:Complexity|Level)[:\s]*(beginner|medium|advanced)",
                block,
                re.IGNORECASE,
            )
            if complexity_match:
                complexity_level = complexity_match.group(1).lower()

            # Create animations list (simplified for now)
            animations = [{"type": "general", "description": name}]

            sequence = AnimationSequence(
                sequence_id=sequence_id,
                name=name,
                animations=animations,
                duration=duration,
                educational_purpose=educational_purpose,
                target_concept=target_concept,
                complexity_level=complexity_level,
            )

            sequences.append(sequence)

        return sequences

    def _parse_educational_enhancements(self, response: str) -> List[Dict[str, Any]]:
        """Parse educational enhancements from Claude's response."""

        enhancements = []

        # Look for numbered or bulleted enhancements
        enhancement_matches = re.findall(
            r"(?:\d+[.:]|\*|-)\s+(.*?)(?=(?:\d+[.:]|\*|-)|$)", response, re.DOTALL
        )

        for i, match in enumerate(enhancement_matches):
            description = match.strip().split("\n")[0].strip()

            if len(description) < 10:  # Skip short descriptions
                continue

            enhancement = {
                "id": f"enhancement_{uuid.uuid4().hex[:8]}",
                "description": description,
                "category": "educational",
                "priority": i + 1,
            }

            enhancements.append(enhancement)

        return enhancements

    def _parse_timing_adjustments(self, response: str) -> List[Dict[str, Any]]:
        """Parse timing adjustments from Claude's response."""

        adjustments = []

        # Look for timing-related suggestions
        timing_matches = re.findall(
            r"(?:\d+[.:]|\*|-)\s+(.*?)(?=(?:\d+[.:]|\*|-)|$)", response, re.DOTALL
        )

        for i, match in enumerate(timing_matches):
            description = match.strip().split("\n")[0].strip()

            if len(description) < 10:
                continue

            adjustment = {
                "id": f"timing_{uuid.uuid4().hex[:8]}",
                "description": description,
                "category": "timing",
                "priority": i + 1,
            }

            adjustments.append(adjustment)

        return adjustments

    def _parse_narrative_elements(self, response: str) -> List[Dict[str, Any]]:
        """Parse narrative elements from Claude's response."""

        elements = []

        # Look for narrative suggestions
        narrative_matches = re.findall(
            r"(?:\d+[.:]|\*|-)\s+(.*?)(?=(?:\d+[.:]|\*|-)|$)", response, re.DOTALL
        )

        for i, match in enumerate(narrative_matches):
            description = match.strip().split("\n")[0].strip()

            if len(description) < 10:
                continue

            element = {
                "id": f"narrative_{uuid.uuid4().hex[:8]}",
                "description": description,
                "category": "narrative",
                "priority": i + 1,
            }

            elements.append(element)

        return elements

    def _parse_pacing_improvements(self, response: str) -> List[Dict[str, Any]]:
        """Parse pacing improvements from Claude's response."""

        improvements = []

        # Look for pacing suggestions
        pacing_matches = re.findall(
            r"(?:\d+[.:]|\*|-)\s+(.*?)(?=(?:\d+[.:]|\*|-)|$)", response, re.DOTALL
        )

        for i, match in enumerate(pacing_matches):
            description = match.strip().split("\n")[0].strip()

            if len(description) < 10:
                continue

            improvement = {
                "id": f"pacing_{uuid.uuid4().hex[:8]}",
                "description": description,
                "category": "pacing",
                "priority": i + 1,
            }

            improvements.append(improvement)

        return improvements

    def _extract_directed_code(self, response: str, original_code: str) -> str:
        """Extract directed code from Claude's response."""

        # Look for code blocks
        code_blocks = re.findall(r"```(?:python)?\n(.*?)\n```", response, re.DOTALL)

        if code_blocks:
            # Use the largest code block (most likely the complete code)
            return max(code_blocks, key=len)

        # If no code block found, return the original code
        return original_code
