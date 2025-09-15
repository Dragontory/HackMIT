"""
Educational Design Agent implementation.

This agent analyzes content and designs optimal educational flows and scene structures
based on learning science principles and pedagogical best practices.
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
    EducationalDesignResult,
    EducationalFlow,
    SceneStructure,
    LearningSegment,
    LearningObjective,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage


logger = logging.getLogger(__name__)


class EducationalDesignAgent(IAgent):
    """
    Specialized agent for designing educational flow and scene structure.

    Uses Claude's understanding of learning science and pedagogy to:
    - Analyze content for learning objectives
    - Design optimal educational flows
    - Structure scenes for maximum retention
    - Apply pedagogical best practices
    - Create engaging learning progressions
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()

    @property
    def name(self) -> str:
        return "EducationalDesignAgent"

    @property
    def description(self) -> str:
        return "Designs educational flow and scene structure"

    async def process(self, state: AgentState) -> AgentResult:
        """Process state and design educational flow and structure."""
        start_time = time.time()

        try:
            logger.info(f"Educational Design processing: {state['content_title']}")

            # Get content to analyze and design
            content = state.get("raw_content", "")
            if not content:
                content = state.get("manim_code", "")

            if not content:
                # Create sample content for testing
                content = self._create_sample_content()
                logger.info("No content provided, using sample content")

            # Get content strategy for context
            content_strategy = state.get("content_strategy")

            # Perform educational design
            result = await self.design_educational_flow(content, content_strategy)

            # Update state
            state["educational_design_result"] = result
            state["current_agent"] = self.name
            state["processing_stage"] = "educational_design_complete"

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "scenes_designed": len(result.scene_structures),
                    "learning_objectives": len(result.learning_objectives),
                    "design_principles": len(result.design_principles),
                    "flow_duration": result.designed_flow.total_duration,
                    "processing_time": processing_time,
                },
            )

        except Exception as e:
            logger.error(f"Educational Design error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Educational design failed: {str(e)}"],
            )

    async def design_educational_flow(
        self, content: str, content_strategy: Optional[Dict[str, Any]] = None
    ) -> EducationalDesignResult:
        """
        Design educational flow and scene structure for content.

        Args:
            content: The content to analyze and design educational flow for
            content_strategy: Optional content strategy for context

        Returns:
            EducationalDesignResult: Complete educational design with flow and structures
        """

        # Step 1: Analyze content for learning objectives
        learning_objectives = await self.analyze_learning_objectives(
            content, content_strategy
        )

        # Step 2: Design overall educational flow
        educational_flow = await self.design_overall_flow(
            content, learning_objectives, content_strategy
        )

        # Step 3: Structure individual scenes
        scene_structures = await self.structure_scenes(
            content, educational_flow, learning_objectives
        )

        # Step 4: Generate design principles and justifications
        design_principles = await self.generate_design_principles(
            content, educational_flow, scene_structures
        )

        # Step 5: Create pedagogical justifications
        pedagogical_justifications = self._generate_pedagogical_justifications(
            educational_flow, scene_structures
        )

        # Step 6: Generate implementation guidance
        accessibility_considerations = self._generate_accessibility_considerations(
            educational_flow
        )
        assessment_recommendations = self._generate_assessment_recommendations(
            learning_objectives, educational_flow
        )
        engagement_strategies = self._generate_engagement_strategies(scene_structures)
        implementation_notes = self._generate_implementation_notes(
            educational_flow, scene_structures
        )

        # Determine success
        success = len(learning_objectives) > 0 and len(scene_structures) > 0

        return EducationalDesignResult(
            original_content=content,
            designed_flow=educational_flow,
            scene_structures=scene_structures,
            learning_objectives=learning_objectives,
            design_principles=design_principles,
            pedagogical_justifications=pedagogical_justifications,
            accessibility_considerations=accessibility_considerations,
            assessment_recommendations=assessment_recommendations,
            engagement_strategies=engagement_strategies,
            implementation_notes=implementation_notes,
            success=success,
        )

    async def analyze_learning_objectives(
        self, content: str, content_strategy: Optional[Dict[str, Any]] = None
    ) -> List[LearningObjective]:
        """Analyze content to identify and structure learning objectives."""

        # Prepare context for Claude
        context_parts = ["I need to analyze this content for learning objectives:"]
        context_parts.append(f"```\n{content}\n```")

        if content_strategy:
            context_parts.append("Content strategy context:")
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
            "Please identify specific, measurable learning objectives following Bloom's taxonomy. "
            "Consider cognitive levels, difficulty progression, and time estimates."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract learning objectives
        return self._parse_learning_objectives(response.content)

    async def design_overall_flow(
        self,
        content: str,
        learning_objectives: List[LearningObjective],
        content_strategy: Optional[Dict[str, Any]] = None,
    ) -> EducationalFlow:
        """Design the overall educational flow structure."""

        # Prepare context for Claude
        context_parts = ["I need to design an educational flow for this content:"]
        context_parts.append(f"```\n{content}\n```")

        context_parts.append("Learning objectives:")
        for obj in learning_objectives:
            context_parts.append(
                f"- {obj.title}: {obj.description} ({obj.cognitive_level})"
            )

        if content_strategy:
            context_parts.append("Strategy context:")
            context_parts.append(
                f"- Target audience: {getattr(content_strategy, 'target_audience', 'general')}"
            )
            context_parts.append(
                f"- Duration target: {getattr(content_strategy, 'duration_target', 60)} minutes"
            )

        context_parts.append(
            "Please design a comprehensive educational flow with pedagogical framework, "
            "learning theory application, and engagement strategies."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract educational flow
        return self._parse_educational_flow(response.content, learning_objectives)

    async def structure_scenes(
        self,
        content: str,
        educational_flow: EducationalFlow,
        learning_objectives: List[LearningObjective],
    ) -> List[SceneStructure]:
        """Structure individual scenes with pedagogical design."""

        # Prepare context for Claude
        context_parts = ["I need to structure scenes for this educational flow:"]
        context_parts.append(f"```\n{content}\n```")

        context_parts.append("Educational flow overview:")
        context_parts.append(f"- Framework: {educational_flow.pedagogical_framework}")
        context_parts.append(f"- Learning theory: {educational_flow.learning_theory}")
        context_parts.append(f"- Difficulty curve: {educational_flow.difficulty_curve}")
        context_parts.append(
            f"- Total duration: {educational_flow.total_duration} minutes"
        )

        context_parts.append("Learning objectives to address:")
        for obj in learning_objectives:
            context_parts.append(
                f"- {obj.title} ({obj.cognitive_level}, {obj.time_estimate}min)"
            )

        context_parts.append(
            "Please create detailed scene structures with learning segments, "
            "pacing strategies, and engagement techniques."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract scene structures
        return self._parse_scene_structures(response.content, educational_flow)

    async def generate_design_principles(
        self,
        content: str,
        educational_flow: EducationalFlow,
        scene_structures: List[SceneStructure],
    ) -> List[str]:
        """Generate the design principles applied in the educational design."""

        # Prepare context for Claude
        context_parts = ["I need design principles for this educational design:"]
        context_parts.append(
            f"Educational framework: {educational_flow.pedagogical_framework}"
        )
        context_parts.append(f"Learning theory: {educational_flow.learning_theory}")
        context_parts.append(f"Number of scenes: {len(scene_structures)}")

        context_parts.append("Scene types:")
        for scene in scene_structures:
            context_parts.append(f"- {scene.title}: {scene.scene_type}")

        context_parts.append(
            "Please identify the key educational design principles that were applied "
            "and explain how they enhance learning effectiveness."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to extract design principles
        return self._parse_design_principles(response.content)

    def _generate_pedagogical_justifications(
        self, educational_flow: EducationalFlow, scene_structures: List[SceneStructure]
    ) -> List[str]:
        """Generate pedagogical justifications for design choices."""

        justifications = []

        # Framework justification
        if educational_flow.pedagogical_framework == "constructivist":
            justifications.append(
                "Constructivist framework chosen to allow learners to build knowledge actively"
            )
        elif educational_flow.pedagogical_framework == "cognitivist":
            justifications.append(
                "Cognitivist framework applied to focus on mental processes and information processing"
            )

        # Learning theory justification
        if educational_flow.learning_theory == "active":
            justifications.append(
                "Active learning theory implemented to engage learners in hands-on activities"
            )

        # Scene structure justifications
        for scene in scene_structures:
            if scene.opening_strategy == "hook":
                justifications.append(
                    f"Hook opening strategy in '{scene.title}' to capture immediate attention"
                )
            if scene.scaffolding_level == "heavy":
                justifications.append(
                    f"Heavy scaffolding in '{scene.title}' to support complex concept acquisition"
                )

        return justifications

    def _generate_accessibility_considerations(
        self, educational_flow: EducationalFlow
    ) -> List[str]:
        """Generate accessibility considerations for the educational design."""

        considerations = []

        # Visual accessibility
        considerations.append("Provide alternative text for visual elements")
        considerations.append("Use high contrast colors for better visibility")
        considerations.append("Include captions for audio content")

        # Cognitive accessibility
        if educational_flow.difficulty_curve == "spiral":
            considerations.append(
                "Spiral curriculum design supports learners with different paces"
            )

        considerations.append(
            "Multiple representation modes for diverse learning styles"
        )
        considerations.append("Clear navigation and consistent structure")

        # Temporal accessibility
        if educational_flow.total_duration > 30:
            considerations.append("Provide breaks and chunking for sustained attention")

        return considerations

    def _generate_assessment_recommendations(
        self,
        learning_objectives: List[LearningObjective],
        educational_flow: EducationalFlow,
    ) -> List[str]:
        """Generate assessment recommendations based on learning objectives."""

        recommendations = []

        # Formative assessment
        if educational_flow.assessment_strategy in ["formative", "both"]:
            recommendations.append(
                "Include frequent formative checks throughout content"
            )
            recommendations.append("Use interactive elements for immediate feedback")

        # Objective-based assessments
        for obj in learning_objectives:
            if obj.cognitive_level == "remember":
                recommendations.append(f"Use recall questions for '{obj.title}'")
            elif obj.cognitive_level == "apply":
                recommendations.append(f"Include practice exercises for '{obj.title}'")
            elif obj.cognitive_level == "analyze":
                recommendations.append(f"Design analysis tasks for '{obj.title}'")

        recommendations.append("Provide rubrics for clear evaluation criteria")
        recommendations.append("Allow multiple attempts for mastery learning")

        return recommendations

    def _generate_engagement_strategies(
        self, scene_structures: List[SceneStructure]
    ) -> List[str]:
        """Generate engagement strategies based on scene designs."""

        strategies = []

        for scene in scene_structures:
            if scene.opening_strategy == "hook":
                strategies.append(f"Use attention-grabbing hooks in '{scene.title}'")

            if scene.interaction_points:
                strategies.append(f"Interactive elements scheduled in '{scene.title}'")

            if scene.pacing_strategy == "varied":
                strategies.append(
                    f"Varied pacing maintains engagement in '{scene.title}'"
                )

        # General strategies
        strategies.append("Use storytelling elements to create narrative flow")
        strategies.append("Include visual metaphors for abstract concepts")
        strategies.append("Gamification elements for motivation")

        return strategies

    def _generate_implementation_notes(
        self, educational_flow: EducationalFlow, scene_structures: List[SceneStructure]
    ) -> List[str]:
        """Generate implementation notes for the educational design."""

        notes = []

        # Flow implementation
        notes.append(
            f"Implement {educational_flow.pedagogical_framework} framework consistently"
        )
        notes.append(
            f"Maintain {educational_flow.difficulty_curve} difficulty progression"
        )

        # Scene implementation
        total_segments = sum(len(scene.learning_segments) for scene in scene_structures)
        notes.append(
            f"Coordinate {total_segments} learning segments across {len(scene_structures)} scenes"
        )

        # Technical notes
        if educational_flow.total_duration > 45:
            notes.append("Consider breaking into multiple sessions for long content")

        notes.append("Track learner progress through the educational flow")
        notes.append("Provide clear transitions between scenes and segments")

        return notes

    def _create_sample_content(self) -> str:
        """Create sample content for testing."""

        return """
        Title: Introduction to Machine Learning
        
        Content:
        Machine learning is a subset of artificial intelligence that enables computers 
        to learn and make decisions from data without being explicitly programmed.
        
        Key concepts include:
        1. Supervised Learning - Learning from labeled examples
        2. Unsupervised Learning - Finding patterns in unlabeled data
        3. Reinforcement Learning - Learning through trial and error
        
        Applications:
        - Image recognition
        - Natural language processing
        - Recommendation systems
        - Autonomous vehicles
        
        Mathematical foundations:
        - Linear algebra for data representation
        - Statistics for probability and inference
        - Calculus for optimization algorithms
        """

    def _create_system_prompt(self) -> str:
        """Create the system prompt for educational design operations."""

        return """
        You are an expert Educational Design Specialist with deep knowledge of learning science, pedagogy, and instructional design.
        
        Your expertise includes:
        1. Learning theories (behaviorist, cognitivist, constructivist, connectivist)
        2. Pedagogical frameworks and best practices
        3. Bloom's taxonomy and cognitive levels
        4. Instructional design models (ADDIE, SAM, Gagne's 9 Events)
        5. Engagement and motivation strategies
        6. Assessment and evaluation methods
        7. Accessibility and universal design for learning
        8. Cognitive load theory and attention management
        
        When designing educational flows:
        - Apply evidence-based learning principles
        - Consider learner cognitive load and attention span
        - Design for diverse learning styles and abilities
        - Structure content for optimal retention and transfer
        - Include formative assessment opportunities
        - Plan for engagement and motivation
        - Ensure logical progression and scaffolding
        
        Key design principles to consider:
        - Chunking: Break content into manageable segments
        - Spaced repetition: Reinforce key concepts
        - Active learning: Engage learners in meaningful activities
        - Multimodal presentation: Use various representations
        - Immediate feedback: Provide timely responses
        - Personalization: Adapt to individual needs
        - Social learning: Include collaborative elements
        
        When structuring scenes:
        - Start with clear learning objectives
        - Use appropriate opening and closing strategies
        - Plan transitions and pacing carefully
        - Include interaction and engagement points
        - Consider scaffolding and support needs
        - Design for accessibility and inclusion
        
        Be pedagogically sound, learner-centered, and evidence-based in your designs.
        """

    def _parse_learning_objectives(self, response: str) -> List[LearningObjective]:
        """Parse learning objectives from Claude's response."""

        objectives = []

        # Look for objective blocks
        objective_blocks = re.findall(
            r"(?:Objective|Learning objective)[^\n]*?:(.*?)(?=(?:Objective|Learning objective)|$)",
            response,
            re.DOTALL | re.IGNORECASE,
        )

        if not objective_blocks:
            # Try numbered format
            objective_blocks = re.findall(
                r"\d+[.]\s+(.*?)(?=\d+[.]|\Z)", response, re.DOTALL
            )

        for i, block in enumerate(objective_blocks):
            objective_id = f"obj_{uuid.uuid4().hex[:8]}"

            # Extract title
            title = f"Learning Objective {i+1}"
            title_match = re.search(
                r"(?:Title|Objective)[:\s]*(.*?)(?:\n|$)", block, re.IGNORECASE
            )
            if title_match:
                title = title_match.group(1).strip()
            elif block.strip():
                # Use first line as title
                title = block.strip().split("\n")[0]

            # Extract description
            description = ""
            desc_match = re.search(
                r"(?:Description|Detail)[:\s]*(.*?)(?:\n|$)", block, re.IGNORECASE
            )
            if desc_match:
                description = desc_match.group(1).strip()
            elif len(block.strip().split("\n")) > 1:
                description = block.strip().split("\n")[1]

            # Extract cognitive level
            cognitive_level = "understand"
            cognitive_match = re.search(
                r"(?:Cognitive level|Level|Bloom)[:\s]*(remember|understand|apply|analyze|evaluate|create)",
                block,
                re.IGNORECASE,
            )
            if cognitive_match:
                cognitive_level = cognitive_match.group(1).lower()

            # Extract difficulty
            difficulty = "medium"
            difficulty_match = re.search(
                r"(?:Difficulty)[:\s]*(easy|medium|hard)", block, re.IGNORECASE
            )
            if difficulty_match:
                difficulty = difficulty_match.group(1).lower()

            # Extract time estimate
            time_estimate = 3.0
            time_match = re.search(
                r"(?:Time|Duration)[:\s]*(\d+\.?\d*)", block, re.IGNORECASE
            )
            if time_match:
                time_estimate = float(time_match.group(1))

            # Extract concepts
            concepts = []
            concepts_section = re.search(
                r"(?:Concepts|Topics)[:\s]*(.*?)(?=\n\n|\n[A-Z]|\Z)",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            if concepts_section:
                concept_items = re.findall(
                    r"[-*]\s+(.*?)(?=[-*]|\n\n|\Z)",
                    concepts_section.group(1),
                    re.DOTALL,
                )
                concepts = [item.strip() for item in concept_items if item.strip()]

            objective = LearningObjective(
                objective_id=objective_id,
                title=title,
                description=description,
                cognitive_level=cognitive_level,
                difficulty=difficulty,
                time_estimate=time_estimate,
                concepts=concepts,
            )

            objectives.append(objective)

        return objectives

    def _parse_educational_flow(
        self, response: str, learning_objectives: List[LearningObjective]
    ) -> EducationalFlow:
        """Parse educational flow from Claude's response."""

        flow_id = f"flow_{uuid.uuid4().hex[:8]}"
        title = "Educational Flow"

        # Extract title
        title_match = re.search(
            r"(?:Title|Flow)[:\s]*(.*?)(?:\n|$)", response, re.IGNORECASE
        )
        if title_match:
            title = title_match.group(1).strip()

        # Extract pedagogical framework
        pedagogical_framework = "constructivist"
        framework_match = re.search(
            r"(?:Framework|Pedagogical framework)[:\s]*(behaviorist|cognitivist|constructivist)",
            response,
            re.IGNORECASE,
        )
        if framework_match:
            pedagogical_framework = framework_match.group(1).lower()

        # Extract learning theory
        learning_theory = "active"
        theory_match = re.search(
            r"(?:Learning theory|Theory)[:\s]*(passive|active|experiential|social)",
            response,
            re.IGNORECASE,
        )
        if theory_match:
            learning_theory = theory_match.group(1).lower()

        # Extract difficulty curve
        difficulty_curve = "spiral"
        curve_match = re.search(
            r"(?:Difficulty curve|Curve)[:\s]*(linear|spiral|branching|adaptive)",
            response,
            re.IGNORECASE,
        )
        if curve_match:
            difficulty_curve = curve_match.group(1).lower()

        # Extract engagement pattern
        engagement_pattern = "peaks_valleys"
        engagement_match = re.search(
            r"(?:Engagement pattern|Pattern)[:\s]*(constant|peaks_valleys|crescendo)",
            response,
            re.IGNORECASE,
        )
        if engagement_match:
            engagement_pattern = engagement_match.group(1).lower()

        # Extract duration
        total_duration = (
            sum(obj.time_estimate for obj in learning_objectives)
            if learning_objectives
            else 60.0
        )
        duration_match = re.search(
            r"(?:Duration|Total duration)[:\s]*(\d+\.?\d*)", response, re.IGNORECASE
        )
        if duration_match:
            total_duration = float(duration_match.group(1))

        # Extract target audience
        target_audience = "general"
        audience_match = re.search(
            r"(?:Target audience|Audience)[:\s]*(beginner|intermediate|advanced|mixed|general)",
            response,
            re.IGNORECASE,
        )
        if audience_match:
            target_audience = audience_match.group(1).lower()

        return EducationalFlow(
            flow_id=flow_id,
            title=title,
            overall_learning_objectives=learning_objectives,
            pedagogical_framework=pedagogical_framework,
            learning_theory=learning_theory,
            difficulty_curve=difficulty_curve,
            engagement_pattern=engagement_pattern,
            total_duration=total_duration,
            target_audience=target_audience,
        )

    def _parse_scene_structures(
        self, response: str, educational_flow: EducationalFlow
    ) -> List[SceneStructure]:
        """Parse scene structures from Claude's response."""

        scene_structures = []

        # Look for scene blocks
        scene_blocks = re.findall(
            r"(?:Scene|Structure)[^\n]*?:(.*?)(?=(?:Scene|Structure)|$)",
            response,
            re.DOTALL | re.IGNORECASE,
        )

        if not scene_blocks:
            # Try numbered format
            scene_blocks = re.findall(
                r"\d+[.]\s+(.*?)(?=\d+[.]|\Z)", response, re.DOTALL
            )

        for i, block in enumerate(scene_blocks):
            scene_id = f"scene_{uuid.uuid4().hex[:8]}"
            title = f"Scene {i+1}"

            # Extract title
            title_match = re.search(
                r"(?:Title|Scene)[:\s]*(.*?)(?:\n|$)", block, re.IGNORECASE
            )
            if title_match:
                title = title_match.group(1).strip()

            # Extract scene type
            scene_type = "instructional"
            type_match = re.search(
                r"(?:Type|Scene type)[:\s]*(instructional|assessment|review|introduction)",
                block,
                re.IGNORECASE,
            )
            if type_match:
                scene_type = type_match.group(1).lower()

            # Extract opening strategy
            opening_strategy = "hook"
            opening_match = re.search(
                r"(?:Opening|Opening strategy)[:\s]*(hook|objective|review|question)",
                block,
                re.IGNORECASE,
            )
            if opening_match:
                opening_strategy = opening_match.group(1).lower()

            # Extract closing strategy
            closing_strategy = "summary"
            closing_match = re.search(
                r"(?:Closing|Closing strategy)[:\s]*(summary|transition|assessment|reinforcement)",
                block,
                re.IGNORECASE,
            )
            if closing_match:
                closing_strategy = closing_match.group(1).lower()

            # Extract pacing strategy
            pacing_strategy = "varied"
            pacing_match = re.search(
                r"(?:Pacing|Pacing strategy)[:\s]*(constant|varied|accelerating|decelerating)",
                block,
                re.IGNORECASE,
            )
            if pacing_match:
                pacing_strategy = pacing_match.group(1).lower()

            # Extract duration
            duration = educational_flow.total_duration / max(len(scene_blocks), 1)
            duration_match = re.search(
                r"(?:Duration)[:\s]*(\d+\.?\d*)", block, re.IGNORECASE
            )
            if duration_match:
                duration = float(duration_match.group(1))

            # Extract scaffolding level
            scaffolding_level = "medium"
            scaffolding_match = re.search(
                r"(?:Scaffolding|Support)[:\s]*(none|light|medium|heavy)",
                block,
                re.IGNORECASE,
            )
            if scaffolding_match:
                scaffolding_level = scaffolding_match.group(1).lower()

            # Create learning segments (simplified for now)
            learning_segments = [
                LearningSegment(
                    segment_id=f"segment_{uuid.uuid4().hex[:8]}",
                    title=f"{title} Content",
                    duration=duration * 0.8,  # Most of the scene
                ),
                LearningSegment(
                    segment_id=f"segment_{uuid.uuid4().hex[:8]}",
                    title=f"{title} Assessment",
                    content_type="assessment",
                    duration=duration * 0.2,  # Small assessment portion
                ),
            ]

            scene_structure = SceneStructure(
                scene_id=scene_id,
                title=title,
                learning_segments=learning_segments,
                scene_type=scene_type,
                opening_strategy=opening_strategy,
                closing_strategy=closing_strategy,
                pacing_strategy=pacing_strategy,
                total_duration=duration,
                scaffolding_level=scaffolding_level,
            )

            scene_structures.append(scene_structure)

        return scene_structures

    def _parse_design_principles(self, response: str) -> List[str]:
        """Parse design principles from Claude's response."""

        principles = []

        # Look for principle lists
        principle_matches = re.findall(
            r"(?:\d+[.:]|\*|-)\s+(.*?)(?=(?:\d+[.:]|\*|-)|$)", response, re.DOTALL
        )

        for match in principle_matches:
            principle = match.strip().split("\n")[0].strip()

            if len(principle) > 10:  # Filter out short descriptions
                principles.append(principle)

        # If no structured list found, look for key phrases
        if not principles:
            principle_patterns = [
                r"(.*chunking.*)",
                r"(.*scaffolding.*)",
                r"(.*active learning.*)",
                r"(.*formative assessment.*)",
                r"(.*cognitive load.*)",
                r"(.*engagement.*)",
            ]

            for pattern in principle_patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                for match in matches:
                    if match.strip() and len(match.strip()) > 20:
                        principles.append(match.strip())

        return principles[:10]  # Limit to top 10 principles
