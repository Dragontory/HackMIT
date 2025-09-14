"""
LangGraph workflow for animation direction operations.

This workflow orchestrates the Animation Director Agent to systematically
analyze, direct, and enhance animations for maximum educational impact.
"""

import logging
import time
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...domain.models import AgentState, AgentResult
from ...infrastructure.config import AgentConfig
from ...infrastructure.anthropic.client import AnthropicClient
from ..agents.animation_director import AnimationDirectorAgent


logger = logging.getLogger(__name__)


class AnimationDirectionWorkflow:
    """
    LangGraph workflow for comprehensive animation direction.

    This workflow orchestrates the Animation Director Agent to:
    1. Analyze educational flow and create timeline
    2. Create detailed animation sequences
    3. Generate educational enhancements
    4. Create timing adjustments for optimal learning
    5. Add narrative elements for better understanding
    6. Apply all improvements to create directed code
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.claude_client = AnthropicClient(config.anthropic)
        self.animation_director = AnimationDirectorAgent(self.claude_client)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""

        # Define the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes (processing steps)
        workflow.add_node("analyze_flow", self._analyze_flow_node)
        workflow.add_node("create_sequences", self._create_sequences_node)
        workflow.add_node("generate_enhancements", self._generate_enhancements_node)
        workflow.add_node("adjust_timing", self._adjust_timing_node)
        workflow.add_node("add_narrative", self._add_narrative_node)
        workflow.add_node("apply_direction", self._apply_direction_node)
        workflow.add_node("finalize_results", self._finalize_results_node)

        # Define the flow
        workflow.set_entry_point("analyze_flow")

        workflow.add_edge("analyze_flow", "create_sequences")
        workflow.add_edge("create_sequences", "generate_enhancements")
        workflow.add_edge("generate_enhancements", "adjust_timing")
        workflow.add_edge("adjust_timing", "add_narrative")
        workflow.add_edge("add_narrative", "apply_direction")
        workflow.add_edge("apply_direction", "finalize_results")
        workflow.add_edge("finalize_results", END)

        # Add memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def _analyze_flow_node(self, state: AgentState) -> AgentState:
        """Analyze educational flow and create animation timeline."""
        logger.info("Analyzing educational flow")

        try:
            # Get code
            manim_code = state.get("manim_code", "")

            if not manim_code:
                # Use the animation director to generate sample code
                manim_code = self.animation_director._create_sample_manim_code()
                state["manim_code"] = manim_code
                state["processing_stage"] = "sample_code_generated"
                logger.info("Generated sample Manim code for demonstration")

            # Get content strategy for educational context
            content_strategy = state.get("content_strategy")

            # Analyze educational flow
            timeline = await self.animation_director.analyze_educational_flow(
                manim_code, content_strategy
            )

            # Store results in state
            state["agent_messages"].append(
                {
                    "agent": "flow_analyzer",
                    "status": "completed",
                    "message": "Analyzed educational flow",
                    "metadata": {
                        "timeline_title": timeline.title,
                        "learning_objectives": len(timeline.learning_objectives),
                        "concept_flow": len(timeline.concept_flow),
                        "educational_approach": timeline.educational_approach,
                        "target_audience": timeline.target_audience,
                    },
                }
            )

            # Create initial animation direction result
            state["animation_direction_result"] = {
                "original_code": manim_code,
                "directed_code": manim_code,
                "timeline": timeline,
                "sequences": [],
                "educational_enhancements": [],
                "timing_adjustments": [],
                "narrative_elements": [],
                "pacing_improvements": [],
                "success": False,
                "processing_time": 0.0,
            }

            state["processing_stage"] = "flow_analyzed"
            logger.info(f"Analyzed educational flow: {timeline.title}")

        except Exception as e:
            logger.error(f"Flow analysis failed: {e}")
            state["errors"].append(f"Flow analysis failed: {str(e)}")
            state["processing_stage"] = "analysis_failed"

        return state

    async def _create_sequences_node(self, state: AgentState) -> AgentState:
        """Create detailed animation sequences."""
        logger.info("Creating animation sequences")

        try:
            # Get animation direction result
            direction_result = state.get("animation_direction_result")

            if not direction_result:
                state["errors"].append("No animation direction result to sequence")
                state["processing_stage"] = "sequence_creation_failed"
                return state

            # Get code and timeline
            manim_code = direction_result.get(
                "original_code", state.get("manim_code", "")
            )
            timeline = direction_result.get("timeline")

            # Create animation sequences
            sequences = await self.animation_director.create_animation_sequences(
                manim_code, timeline
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "sequence_creator",
                    "status": "completed",
                    "message": f"Created {len(sequences)} animation sequences",
                    "metadata": {
                        "sequences_created": len(sequences),
                        "total_duration": sum(seq.duration for seq in sequences),
                        "complexity_levels": {
                            seq.complexity_level: 1 for seq in sequences
                        },
                    },
                }
            )

            # Update animation direction result
            direction_result["sequences"] = sequences

            state["processing_stage"] = "sequences_created"
            logger.info(f"Created {len(sequences)} animation sequences")

        except Exception as e:
            logger.error(f"Sequence creation failed: {e}")
            state["errors"].append(f"Sequence creation failed: {str(e)}")
            state["processing_stage"] = "sequence_creation_failed"

        return state

    async def _generate_enhancements_node(self, state: AgentState) -> AgentState:
        """Generate educational enhancements."""
        logger.info("Generating educational enhancements")

        try:
            # Get animation direction result
            direction_result = state.get("animation_direction_result")

            if not direction_result:
                state["errors"].append("No animation direction result to enhance")
                state["processing_stage"] = "enhancement_generation_failed"
                return state

            # Get code, timeline, and sequences
            manim_code = direction_result.get(
                "original_code", state.get("manim_code", "")
            )
            timeline = direction_result.get("timeline")
            sequences = direction_result.get("sequences", [])

            # Generate educational enhancements
            educational_enhancements = (
                await self.animation_director.generate_educational_enhancements(
                    manim_code, timeline, sequences
                )
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "enhancement_generator",
                    "status": "completed",
                    "message": f"Generated {len(educational_enhancements)} educational enhancements",
                    "metadata": {
                        "enhancements_generated": len(educational_enhancements),
                        "categories": {
                            enh.get("category", "unknown"): 1
                            for enh in educational_enhancements
                        },
                    },
                }
            )

            # Update animation direction result
            direction_result["educational_enhancements"] = educational_enhancements

            state["processing_stage"] = "enhancements_generated"
            logger.info(
                f"Generated {len(educational_enhancements)} educational enhancements"
            )

        except Exception as e:
            logger.error(f"Enhancement generation failed: {e}")
            state["errors"].append(f"Enhancement generation failed: {str(e)}")
            state["processing_stage"] = "enhancement_generation_failed"

        return state

    async def _adjust_timing_node(self, state: AgentState) -> AgentState:
        """Create timing adjustments for optimal learning."""
        logger.info("Creating timing adjustments")

        try:
            # Get animation direction result
            direction_result = state.get("animation_direction_result")

            if not direction_result:
                state["errors"].append("No animation direction result to adjust")
                state["processing_stage"] = "timing_adjustment_failed"
                return state

            # Get code, timeline, and sequences
            manim_code = direction_result.get(
                "original_code", state.get("manim_code", "")
            )
            timeline = direction_result.get("timeline")
            sequences = direction_result.get("sequences", [])

            # Create timing adjustments
            timing_adjustments = (
                await self.animation_director.create_timing_adjustments(
                    manim_code, timeline, sequences
                )
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "timing_adjuster",
                    "status": "completed",
                    "message": f"Created {len(timing_adjustments)} timing adjustments",
                    "metadata": {
                        "adjustments_created": len(timing_adjustments),
                        "categories": {
                            adj.get("category", "unknown"): 1
                            for adj in timing_adjustments
                        },
                    },
                }
            )

            # Update animation direction result
            direction_result["timing_adjustments"] = timing_adjustments

            state["processing_stage"] = "timing_adjusted"
            logger.info(f"Created {len(timing_adjustments)} timing adjustments")

        except Exception as e:
            logger.error(f"Timing adjustment failed: {e}")
            state["errors"].append(f"Timing adjustment failed: {str(e)}")
            state["processing_stage"] = "timing_adjustment_failed"

        return state

    async def _add_narrative_node(self, state: AgentState) -> AgentState:
        """Add narrative elements for better understanding."""
        logger.info("Adding narrative elements")

        try:
            # Get animation direction result
            direction_result = state.get("animation_direction_result")

            if not direction_result:
                state["errors"].append("No animation direction result to narrate")
                state["processing_stage"] = "narrative_addition_failed"
                return state

            # Get code, timeline, and sequences
            manim_code = direction_result.get(
                "original_code", state.get("manim_code", "")
            )
            timeline = direction_result.get("timeline")
            sequences = direction_result.get("sequences", [])

            # Add narrative elements
            narrative_elements = await self.animation_director.add_narrative_elements(
                manim_code, timeline, sequences
            )

            # Generate pacing improvements
            pacing_improvements = (
                await self.animation_director.generate_pacing_improvements(
                    manim_code, timeline, sequences
                )
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "narrative_creator",
                    "status": "completed",
                    "message": f"Added {len(narrative_elements)} narrative elements and {len(pacing_improvements)} pacing improvements",
                    "metadata": {
                        "narrative_elements": len(narrative_elements),
                        "pacing_improvements": len(pacing_improvements),
                    },
                }
            )

            # Update animation direction result
            direction_result["narrative_elements"] = narrative_elements
            direction_result["pacing_improvements"] = pacing_improvements

            state["processing_stage"] = "narrative_added"
            logger.info(f"Added {len(narrative_elements)} narrative elements")

        except Exception as e:
            logger.error(f"Narrative addition failed: {e}")
            state["errors"].append(f"Narrative addition failed: {str(e)}")
            state["processing_stage"] = "narrative_addition_failed"

        return state

    async def _apply_direction_node(self, state: AgentState) -> AgentState:
        """Apply all direction improvements to create directed code."""
        logger.info("Applying direction improvements")

        try:
            # Get animation direction result
            direction_result = state.get("animation_direction_result")

            if not direction_result:
                state["errors"].append("No animation direction result to apply")
                state["processing_stage"] = "direction_application_failed"
                return state

            # Get code and improvements
            manim_code = direction_result.get(
                "original_code", state.get("manim_code", "")
            )
            educational_enhancements = direction_result.get(
                "educational_enhancements", []
            )
            timing_adjustments = direction_result.get("timing_adjustments", [])
            narrative_elements = direction_result.get("narrative_elements", [])
            pacing_improvements = direction_result.get("pacing_improvements", [])

            # Apply direction improvements
            directed_code = await self.animation_director.apply_direction_improvements(
                manim_code,
                educational_enhancements,
                timing_adjustments,
                narrative_elements,
                pacing_improvements,
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "direction_applier",
                    "status": "completed",
                    "message": "Applied direction improvements",
                    "metadata": {
                        "improvements_applied": len(educational_enhancements)
                        + len(timing_adjustments)
                        + len(narrative_elements)
                        + len(pacing_improvements),
                        "code_changed": directed_code != manim_code,
                        "code_size_change": len(directed_code) - len(manim_code),
                    },
                }
            )

            # Update animation direction result
            direction_result["directed_code"] = directed_code

            # Update state with directed code
            state["manim_code"] = directed_code

            state["processing_stage"] = "direction_applied"
            logger.info("Applied direction improvements to code")

        except Exception as e:
            logger.error(f"Direction application failed: {e}")
            state["errors"].append(f"Direction application failed: {str(e)}")
            state["processing_stage"] = "direction_application_failed"

        return state

    async def _finalize_results_node(self, state: AgentState) -> AgentState:
        """Finalize the animation direction workflow results."""
        logger.info("Finalizing animation direction results")

        # Get animation direction result
        direction_result = state.get("animation_direction_result")

        if direction_result:
            # Determine success
            success = (
                direction_result.get("directed_code")
                != direction_result.get("original_code")
                and len(direction_result.get("sequences", [])) > 0
            )

            # Update success flag
            direction_result["success"] = success

            # Create comprehensive summary
            sequences = direction_result.get("sequences", [])
            educational_enhancements = direction_result.get(
                "educational_enhancements", []
            )
            timing_adjustments = direction_result.get("timing_adjustments", [])
            narrative_elements = direction_result.get("narrative_elements", [])
            pacing_improvements = direction_result.get("pacing_improvements", [])

            state["agent_messages"].append(
                {
                    "agent": "workflow_summary",
                    "status": "completed",
                    "summary": {
                        "sequences_created": len(sequences),
                        "educational_enhancements": len(educational_enhancements),
                        "timing_adjustments": len(timing_adjustments),
                        "narrative_elements": len(narrative_elements),
                        "pacing_improvements": len(pacing_improvements),
                        "total_improvements": len(educational_enhancements)
                        + len(timing_adjustments)
                        + len(narrative_elements)
                        + len(pacing_improvements),
                        "code_directed": direction_result.get("directed_code")
                        != direction_result.get("original_code"),
                        "success": success,
                    },
                }
            )

        state["processing_stage"] = "animation_direction_completed"
        state["current_agent"] = "workflow_complete"

        logger.info("Animation direction workflow completed")
        return state

    async def direct_animations(
        self, manim_code: str = "", content_strategy: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Direct animations using the complete workflow.

        Args:
            manim_code: The Manim Python code to analyze and direct
            content_strategy: Optional content strategy for educational context

        Returns:
            AgentResult: Complete animation direction results
        """
        logger.info("Starting animation direction workflow")

        # Initialize state
        initial_state = {
            "raw_content": "",
            "content_title": "Animation Direction Session",
            "content_strategy": content_strategy,
            "latex_specialist_result": None,
            "code_modification_result": None,
            "code_testing_result": None,
            "error_surgery_result": None,
            "terminal_monitoring_result": None,
            "visual_composition_result": None,
            "rendering_optimization_result": None,
            "animation_direction_result": None,
            "manim_code": manim_code,
            "error_log": "",
            "current_agent": "",
            "processing_stage": "initialized",
            "errors": [],
            "warnings": [],
            "agent_messages": [],
        }

        try:
            # Execute the workflow
            final_state = await self.workflow.ainvoke(
                initial_state,
                config={
                    "configurable": {
                        "thread_id": f"animation_direction_{hash(manim_code[:100])}"
                    }
                },
            )

            # Determine success
            direction_result = final_state.get("animation_direction_result")
            success = (
                final_state["processing_stage"] == "animation_direction_completed"
                and direction_result is not None
                and direction_result.get("success", False)
                and not final_state["errors"]
            )

            return AgentResult(
                success=success,
                data=direction_result,
                errors=final_state["errors"],
                warnings=final_state["warnings"],
                metadata={
                    "workflow_state": final_state["processing_stage"],
                    "agent_messages": final_state["agent_messages"],
                    "total_processing_steps": len(final_state["agent_messages"]),
                    "sequences_created": (
                        len(direction_result.get("sequences", []))
                        if direction_result
                        else 0
                    ),
                    "total_improvements": (
                        len(direction_result.get("educational_enhancements", []))
                        + len(direction_result.get("timing_adjustments", []))
                        + len(direction_result.get("narrative_elements", []))
                        + len(direction_result.get("pacing_improvements", []))
                        if direction_result
                        else 0
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Animation direction workflow execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Workflow execution failed: {str(e)}"],
            )
