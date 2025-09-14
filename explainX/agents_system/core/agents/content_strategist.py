"""
Content Strategist Agent implementation.

This agent analyzes educational content and creates optimal learning strategies
using Claude's advanced reasoning capabilities.
"""

import logging
import re
from typing import List, Dict, Any

from ...domain.interfaces import IContentAnalyzer
from ...domain.models import (
    AgentState,
    AgentResult,
    ContentStrategy,
    ContentChunk,
    LearningObjective,
    VisualizationOpportunity,
    AnimationRecommendation,
    DifficultyLevel,
    ContentType,
    VisualizationType,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage


logger = logging.getLogger(__name__)


class ContentStrategistAgent(IContentAnalyzer):
    """
    Analyzes educational content and creates comprehensive learning strategies.

    Uses Claude's reasoning to:
    - Extract learning objectives
    - Identify optimal content chunking
    - Recommend visualizations and animations
    - Assess cognitive load and difficulty progression
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()

    @property
    def name(self) -> str:
        return "ContentStrategistAgent"

    @property
    def description(self) -> str:
        return "Analyzes educational content and creates optimal learning strategies for video generation"

    async def process(self, state: AgentState) -> AgentResult:
        """Process content and create learning strategy."""
        try:
            logger.info(f"Content Strategist processing: {state['content_title']}")

            # Analyze content and create strategy
            strategy = await self.analyze_content(
                state["raw_content"], state["content_title"]
            )

            # Update state
            state["content_strategy"] = strategy
            state["current_agent"] = self.name
            state["processing_stage"] = "content_analysis_complete"

            return AgentResult(
                success=True,
                data=strategy,
                metadata={
                    "agent": self.name,
                    "learning_objectives_count": len(strategy.learning_objectives),
                    "content_chunks_count": len(strategy.content_chunks),
                    "visualization_opportunities": len(strategy.visual_opportunities),
                    "animation_recommendations": len(
                        strategy.animation_recommendations
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Content Strategist error: {e}")
            return AgentResult(
                success=False, data=None, errors=[f"Content analysis failed: {str(e)}"]
            )

    async def analyze_content(self, content: str, title: str) -> ContentStrategy:
        """Perform comprehensive content analysis."""

        # Get parallel analysis from Claude
        learning_objectives = await self.identify_learning_objectives(content)
        difficulty_progression = await self.assess_difficulty_progression(content)
        visualizations = await self.recommend_visualizations(content)
        animations = await self.recommend_animations(content)
        content_chunks = await self.create_content_chunks(content)

        # Calculate metrics
        mathematical_density = self._calculate_mathematical_density(content)
        conceptual_complexity = self._assess_conceptual_complexity(content)
        practical_relevance = self._assess_practical_relevance(content)

        # Estimate timing
        total_time = sum(chunk.estimated_reading_time for chunk in content_chunks)
        recommended_scenes = max(3, min(len(content_chunks), 8))  # 3-8 scenes optimal

        # Assess cognitive load
        cognitive_load = self._assess_cognitive_load(
            mathematical_density, conceptual_complexity, len(learning_objectives)
        )

        return ContentStrategy(
            learning_objectives=learning_objectives,
            content_chunks=content_chunks,
            difficulty_progression=difficulty_progression,
            visual_opportunities=visualizations,
            animation_recommendations=animations,
            total_estimated_time=total_time,
            recommended_scene_count=recommended_scenes,
            cognitive_load_assessment=cognitive_load,
            mathematical_density=mathematical_density,
            conceptual_complexity=conceptual_complexity,
            practical_relevance=practical_relevance,
        )

    async def identify_learning_objectives(
        self, content: str
    ) -> List[LearningObjective]:
        """Extract and prioritize learning objectives."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
            Analyze this educational content and extract 3-5 clear learning objectives.
            
            Content:
            {content[:3000]}...
            
            For each learning objective, provide:
            1. Title (concise, action-oriented)
            2. Description (what students will learn)
            3. Difficulty level (beginner/intermediate/advanced)
            4. Estimated time in minutes
            5. Prerequisites (if any)
            
            Focus on objectives that are:
            - Measurable and specific
            - Appropriate for video-based learning
            - Building upon each other logically
            
            Return as structured data.
            """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_learning_objectives(response.content)

    async def assess_difficulty_progression(
        self, content: str
    ) -> List[DifficultyLevel]:
        """Determine optimal difficulty progression."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
            Analyze this content and recommend the optimal difficulty progression
            for educational video scenes.
            
            Content preview:
            {content[:2000]}...
            
            Consider:
            - Cognitive load theory
            - Prerequisites and dependencies
            - Mathematical complexity
            - Conceptual abstractions
            
            Recommend a sequence of difficulty levels that builds understanding progressively.
            """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_difficulty_progression(response.content)

    async def recommend_visualizations(
        self, content: str
    ) -> List[VisualizationOpportunity]:
        """Identify opportunities for effective visualizations."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
            Identify the most impactful visualization opportunities in this educational content.
            
            Content:
            {content[:3000]}...
            
            For each visualization opportunity, specify:
            1. Concept to visualize
            2. Type (diagram/graph/flowchart/equation/animation/code_snippet)
            3. Educational value description
            4. Priority (high/medium/low)
            5. Implementation complexity (simple/moderate/complex)
            
            Focus on visualizations that:
            - Clarify complex concepts
            - Show relationships and processes
            - Make abstract ideas concrete
            - Address common misconceptions
            """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_visualizations(response.content)

    async def recommend_animations(self, content: str) -> List[AnimationRecommendation]:
        """Recommend animations for dynamic educational content."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
            Recommend specific animations that would enhance learning for this content.
            
            Content:
            {content[:3000]}...
            
            For each animation, specify:
            1. Concept to animate
            2. Animation type (2d/3d/hybrid)
            3. Educational value (essential/helpful/optional)
            4. Complexity (simple/moderate/complex)
            5. Description of the animation
            
            Focus on animations that:
            - Show processes and transformations
            - Demonstrate temporal relationships
            - Make abstract concepts tangible
            - Engage visual learners
            """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_animations(response.content)

    async def create_content_chunks(self, content: str) -> List[ContentChunk]:
        """Create optimal content chunks for video scenes."""

        messages = [
            ClaudeMessage(
                role="user",
                content=f"""
            Break this educational content into 3-6 coherent chunks suitable for video scenes.
            
            Content:
            {content}
            
            For each chunk:
            1. Unique ID
            2. Descriptive title
            3. Content excerpt (key points)
            4. Content type (conceptual/mathematical/practical/historical)
            5. Difficulty level
            6. Estimated reading time in minutes
            7. Key concepts covered
            8. Mathematical concepts (if any)
            
            Ensure each chunk:
            - Has a clear focus and learning goal
            - Builds logically on previous chunks
            - Is suitable for 2-4 minute video segments
            - Maintains conceptual coherence
            """,
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)
        return self._parse_content_chunks(response.content)

    def _create_system_prompt(self) -> str:
        """Create the system prompt for content analysis."""
        return """
        You are an expert educational content strategist specializing in video-based learning.
        
        Your expertise includes:
        - Cognitive load theory and instructional design
        - Mathematical education and visualization
        - Learning objective design and assessment
        - Content chunking and progression planning
        - Visual learning and multimedia instruction
        
        When analyzing content:
        1. Prioritize clarity and logical progression
        2. Consider diverse learning styles
        3. Identify optimal visualization opportunities
        4. Ensure appropriate cognitive load
        5. Design for video-based delivery
        
        Always provide structured, actionable recommendations that can be implemented
        by downstream agents in the video generation pipeline.
        """

    def _calculate_mathematical_density(self, content: str) -> float:
        """Calculate the density of mathematical content."""
        # Count mathematical indicators
        math_patterns = [
            r"\$[^$]+\$",  # LaTeX inline math
            r"\\[a-zA-Z]+\{",  # LaTeX commands
            r"\b(?:equation|formula|theorem|proof|lemma)\b",  # Mathematical terms
            r"\b(?:matrix|vector|function|derivative|integral)\b",
            r"[=≠<>≤≥±∞∑∏∫∂∇]",  # Mathematical symbols
        ]

        total_matches = 0
        for pattern in math_patterns:
            total_matches += len(re.findall(pattern, content, re.IGNORECASE))

        # Normalize by content length
        words = len(content.split())
        return min(1.0, total_matches / max(words / 100, 1))  # Cap at 1.0

    def _assess_conceptual_complexity(self, content: str) -> float:
        """Assess the conceptual complexity of content."""
        # Count complexity indicators
        complex_patterns = [
            r"\b(?:algorithm|optimization|convergence|complexity)\b",
            r"\b(?:abstract|theoretical|paradigm|framework)\b",
            r"\b(?:implies|therefore|consequently|furthermore)\b",
            r"[,;:]",  # Sentence complexity indicators
        ]

        total_complexity = 0
        for pattern in complex_patterns:
            total_complexity += len(re.findall(pattern, content, re.IGNORECASE))

        words = len(content.split())
        return min(1.0, total_complexity / max(words / 50, 1))

    def _assess_practical_relevance(self, content: str) -> float:
        """Assess the practical relevance of content."""
        practical_patterns = [
            r"\b(?:application|implementation|example|practice)\b",
            r"\b(?:real-world|industry|problem|solution)\b",
            r"\b(?:code|programming|software|system)\b",
            r"\b(?:use case|scenario|project|experiment)\b",
        ]

        total_practical = 0
        for pattern in practical_patterns:
            total_practical += len(re.findall(pattern, content, re.IGNORECASE))

        words = len(content.split())
        return min(1.0, total_practical / max(words / 100, 1))

    def _assess_cognitive_load(
        self, math_density: float, complexity: float, objectives_count: int
    ) -> str:
        """Assess overall cognitive load."""
        # Weighted scoring
        score = (
            math_density * 0.4 + complexity * 0.4 + min(objectives_count / 10, 1) * 0.2
        )

        if score < 0.3:
            return "low"
        elif score < 0.7:
            return "moderate"
        else:
            return "high"

    def _parse_learning_objectives(self, response: str) -> List[LearningObjective]:
        """Parse learning objectives from Claude's response."""
        # This is a simplified parser - in production, you'd want more robust parsing
        objectives = []

        # Extract structured data from response
        # For now, create some sample objectives based on content
        objectives.append(
            LearningObjective(
                objective_id="obj_core_concepts",
                title="Understand Core Concepts",
                description="Learn fundamental concepts and terminology",
                difficulty="easy",
                time_estimate=5.0,
                prerequisites=[],
            )
        )

        objectives.append(
            LearningObjective(
                objective_id="obj_apply_math",
                title="Apply Mathematical Principles",
                description="Apply mathematical concepts to solve problems",
                difficulty="medium",
                time_estimate=8.0,
                prerequisites=["Understand Core Concepts"],
            )
        )

        return objectives

    def _parse_difficulty_progression(self, response: str) -> List[DifficultyLevel]:
        """Parse difficulty progression from Claude's response."""
        # Sample progression - in production, parse from Claude's response
        return [
            DifficultyLevel.BEGINNER,
            DifficultyLevel.INTERMEDIATE,
            DifficultyLevel.ADVANCED,
        ]

    def _parse_visualizations(self, response: str) -> List[VisualizationOpportunity]:
        """Parse visualization opportunities from Claude's response."""
        # Sample visualization - in production, parse from Claude's response
        return [
            VisualizationOpportunity(
                concept="Mathematical Formula",
                visualization_type=VisualizationType.EQUATION,
                description="Render complex equations clearly",
                priority="high",
                estimated_complexity="moderate",
            )
        ]

    def _parse_animations(self, response: str) -> List[AnimationRecommendation]:
        """Parse animation recommendations from Claude's response."""
        # Sample animation - in production, parse from Claude's response
        return [
            AnimationRecommendation(
                concept="Process Flow",
                animation_type="2d",
                description="Animate step-by-step process",
                educational_value="helpful",
                complexity="moderate",
            )
        ]

    def _parse_content_chunks(self, response: str) -> List[ContentChunk]:
        """Parse content chunks from Claude's response."""
        # Sample chunks - in production, parse from Claude's response
        return [
            ContentChunk(
                id="chunk_001",
                title="Introduction and Motivation",
                content="Overview of key concepts and their importance",
                content_type=ContentType.CONCEPTUAL,
                difficulty=DifficultyLevel.BEGINNER,
                estimated_reading_time=3,
                key_concepts=["foundations", "motivation"],
                mathematical_concepts=[],
            ),
            ContentChunk(
                id="chunk_002",
                title="Mathematical Foundations",
                content="Core mathematical principles and formulations",
                content_type=ContentType.MATHEMATICAL,
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_reading_time=5,
                key_concepts=["equations", "proofs"],
                mathematical_concepts=["linear algebra", "calculus"],
            ),
        ]
