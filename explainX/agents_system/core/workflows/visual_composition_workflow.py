"""
LangGraph workflow for visual composition operations.

This workflow orchestrates the Visual Composer Agent to systematically
analyze, optimize, and enhance visual elements in Manim animations.
"""

import logging
import time
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...domain.models import AgentState, AgentResult, VisualComposition
from ...infrastructure.config import AgentConfig
from ...infrastructure.anthropic.client import AnthropicClient
from ..agents.visual_composer import VisualComposerAgent


logger = logging.getLogger(__name__)


class VisualCompositionWorkflow:
    """
    LangGraph workflow for comprehensive visual composition.

    This workflow orchestrates the Visual Composer Agent to:
    1. Analyze existing visual elements in Manim code
    2. Generate layout improvements for clarity and aesthetics
    3. Generate animation improvements for coherent flow
    4. Suggest new visual elements to enhance educational value
    5. Apply improvements to create enhanced Manim code
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.claude_client = AnthropicClient(config.anthropic)
        self.visual_composer = VisualComposerAgent(self.claude_client)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""

        # Define the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes (processing steps)
        workflow.add_node("analyze_elements", self._analyze_elements_node)
        workflow.add_node("generate_improvements", self._generate_improvements_node)
        workflow.add_node("generate_suggestions", self._generate_suggestions_node)
        workflow.add_node("apply_improvements", self._apply_improvements_node)
        workflow.add_node("finalize_results", self._finalize_results_node)

        # Define the flow
        workflow.set_entry_point("analyze_elements")

        workflow.add_edge("analyze_elements", "generate_improvements")
        workflow.add_edge("generate_improvements", "generate_suggestions")
        workflow.add_edge("generate_suggestions", "apply_improvements")
        workflow.add_edge("apply_improvements", "finalize_results")
        workflow.add_edge("finalize_results", END)

        # Add memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def _analyze_elements_node(self, state: AgentState) -> AgentState:
        """Analyze visual elements in the Manim code."""
        logger.info("Analyzing visual elements in Manim code")

        try:
            # Get code
            manim_code = state.get("manim_code", "")

            if not manim_code:
                # Use the visual composer to generate sample code
                manim_code = self.visual_composer._create_sample_manim_code()
                state["manim_code"] = manim_code
                state["processing_stage"] = "sample_code_generated"
                logger.info("Generated sample Manim code for demonstration")

            # Analyze visual elements
            compositions = await self.visual_composer.analyze_visual_elements(
                manim_code
            )

            # Store compositions in state
            state["agent_messages"].append(
                {
                    "agent": "element_analyzer",
                    "status": "completed",
                    "message": f"Analyzed {len(compositions)} visual compositions",
                    "metadata": {
                        "compositions_found": len(compositions),
                        "total_elements": sum(
                            len(comp.elements) for comp in compositions
                        ),
                    },
                }
            )

            # Create initial visual composition result
            state["visual_composition_result"] = {
                "original_code": manim_code,
                "enhanced_code": manim_code,
                "compositions": compositions,
                "element_suggestions": [],
                "layout_improvements": [],
                "animation_improvements": [],
                "success": False,
                "processing_time": 0.0,
            }

            state["processing_stage"] = "elements_analyzed"
            logger.info(f"Analyzed {len(compositions)} visual compositions")

        except Exception as e:
            logger.error(f"Element analysis failed: {e}")
            state["errors"].append(f"Element analysis failed: {str(e)}")
            state["processing_stage"] = "analysis_failed"

        return state

    async def _generate_improvements_node(self, state: AgentState) -> AgentState:
        """Generate layout and animation improvements."""
        logger.info("Generating visual improvements")

        try:
            # Get visual composition result
            composition_result = state.get("visual_composition_result")

            if not composition_result:
                state["errors"].append("No visual composition result to improve")
                state["processing_stage"] = "improvement_generation_failed"
                return state

            # Get code and compositions
            manim_code = composition_result.get(
                "original_code", state.get("manim_code", "")
            )
            compositions = composition_result.get("compositions", [])

            # Generate layout improvements
            layout_improvements = (
                await self.visual_composer.generate_layout_improvements(
                    manim_code, compositions
                )
            )

            # Generate animation improvements
            animation_improvements = (
                await self.visual_composer.generate_animation_improvements(
                    manim_code, compositions
                )
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "improvement_generator",
                    "status": "completed",
                    "message": f"Generated {len(layout_improvements) + len(animation_improvements)} improvements",
                    "metadata": {
                        "layout_improvements": len(layout_improvements),
                        "animation_improvements": len(animation_improvements),
                    },
                }
            )

            # Update visual composition result
            composition_result["layout_improvements"] = layout_improvements
            composition_result["animation_improvements"] = animation_improvements

            state["processing_stage"] = "improvements_generated"
            logger.info(
                f"Generated {len(layout_improvements)} layout and {len(animation_improvements)} animation improvements"
            )

        except Exception as e:
            logger.error(f"Improvement generation failed: {e}")
            state["errors"].append(f"Improvement generation failed: {str(e)}")
            state["processing_stage"] = "improvement_generation_failed"

        return state

    async def _generate_suggestions_node(self, state: AgentState) -> AgentState:
        """Generate suggestions for new visual elements."""
        logger.info("Generating visual element suggestions")

        try:
            # Get visual composition result
            composition_result = state.get("visual_composition_result")

            if not composition_result:
                state["errors"].append("No visual composition result to enhance")
                state["processing_stage"] = "suggestion_generation_failed"
                return state

            # Get code and compositions
            manim_code = composition_result.get(
                "original_code", state.get("manim_code", "")
            )
            compositions = composition_result.get("compositions", [])

            # Generate element suggestions
            element_suggestions = (
                await self.visual_composer.generate_element_suggestions(
                    manim_code, compositions
                )
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "suggestion_generator",
                    "status": "completed",
                    "message": f"Generated {len(element_suggestions)} element suggestions",
                    "metadata": {
                        "element_suggestions": len(element_suggestions),
                        "suggestion_types": {
                            suggestion["element_type"]: 1
                            for suggestion in element_suggestions
                        },
                    },
                }
            )

            # Update visual composition result
            composition_result["element_suggestions"] = element_suggestions

            state["processing_stage"] = "suggestions_generated"
            logger.info(f"Generated {len(element_suggestions)} element suggestions")

        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            state["errors"].append(f"Suggestion generation failed: {str(e)}")
            state["processing_stage"] = "suggestion_generation_failed"

        return state

    async def _apply_improvements_node(self, state: AgentState) -> AgentState:
        """Apply improvements to the Manim code."""
        logger.info("Applying visual improvements")

        try:
            # Get visual composition result
            composition_result = state.get("visual_composition_result")

            if not composition_result:
                state["errors"].append("No visual composition result to apply")
                state["processing_stage"] = "improvement_application_failed"
                return state

            # Get code and improvements
            manim_code = composition_result.get(
                "original_code", state.get("manim_code", "")
            )
            layout_improvements = composition_result.get("layout_improvements", [])
            animation_improvements = composition_result.get(
                "animation_improvements", []
            )

            # Apply improvements
            enhanced_code = await self.visual_composer.apply_improvements(
                manim_code, layout_improvements, animation_improvements
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "improvement_applier",
                    "status": "completed",
                    "message": "Applied visual improvements",
                    "metadata": {
                        "improvements_applied": len(layout_improvements)
                        + len(animation_improvements),
                        "code_changed": enhanced_code != manim_code,
                        "code_size_change": len(enhanced_code) - len(manim_code),
                    },
                }
            )

            # Update visual composition result
            composition_result["enhanced_code"] = enhanced_code

            # Update state with enhanced code
            state["manim_code"] = enhanced_code

            state["processing_stage"] = "improvements_applied"
            logger.info("Applied visual improvements to code")

        except Exception as e:
            logger.error(f"Improvement application failed: {e}")
            state["errors"].append(f"Improvement application failed: {str(e)}")
            state["processing_stage"] = "improvement_application_failed"

        return state

    async def _finalize_results_node(self, state: AgentState) -> AgentState:
        """Finalize the visual composition workflow results."""
        logger.info("Finalizing visual composition results")

        # Get visual composition result
        composition_result = state.get("visual_composition_result")

        if composition_result:
            # Determine success
            success = (
                composition_result.get("enhanced_code")
                != composition_result.get("original_code")
                and len(composition_result.get("compositions", [])) > 0
            )

            # Update success flag
            composition_result["success"] = success

            # Create comprehensive summary
            compositions = composition_result.get("compositions", [])
            layout_improvements = composition_result.get("layout_improvements", [])
            animation_improvements = composition_result.get(
                "animation_improvements", []
            )
            element_suggestions = composition_result.get("element_suggestions", [])

            # Group elements by type
            elements_by_type = {}
            for comp in compositions:
                for element in comp.elements:
                    if element.element_type not in elements_by_type:
                        elements_by_type[element.element_type] = 0
                    elements_by_type[element.element_type] += 1

            state["agent_messages"].append(
                {
                    "agent": "workflow_summary",
                    "status": "completed",
                    "summary": {
                        "compositions": len(compositions),
                        "total_elements": sum(
                            len(comp.elements) for comp in compositions
                        ),
                        "elements_by_type": elements_by_type,
                        "layout_improvements": len(layout_improvements),
                        "animation_improvements": len(animation_improvements),
                        "element_suggestions": len(element_suggestions),
                        "code_enhanced": success,
                    },
                }
            )

        state["processing_stage"] = "visual_composition_completed"
        state["current_agent"] = "workflow_complete"

        logger.info("Visual composition workflow completed")
        return state

    async def compose_visuals(self, manim_code: str = "") -> AgentResult:
        """
        Compose visual elements using the complete workflow.

        Args:
            manim_code: The Manim Python code to analyze and enhance

        Returns:
            AgentResult: Complete visual composition results
        """
        logger.info("Starting visual composition workflow")

        # Initialize state
        initial_state = {
            "raw_content": "",
            "content_title": "Visual Composition Session",
            "content_strategy": None,
            "latex_specialist_result": None,
            "code_modification_result": None,
            "code_testing_result": None,
            "error_surgery_result": None,
            "terminal_monitoring_result": None,
            "visual_composition_result": None,
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
                        "thread_id": f"visual_composition_{hash(manim_code[:100])}"
                    }
                },
            )

            # Determine success
            composition_result = final_state.get("visual_composition_result")
            success = (
                final_state["processing_stage"] == "visual_composition_completed"
                and composition_result is not None
                and composition_result.get("success", False)
                and not final_state["errors"]
            )

            return AgentResult(
                success=success,
                data=composition_result,
                errors=final_state["errors"],
                warnings=final_state["warnings"],
                metadata={
                    "workflow_state": final_state["processing_stage"],
                    "agent_messages": final_state["agent_messages"],
                    "total_processing_steps": len(final_state["agent_messages"]),
                    "compositions_created": (
                        len(composition_result.get("compositions", []))
                        if composition_result
                        else 0
                    ),
                    "improvements_made": (
                        len(composition_result.get("layout_improvements", []))
                        + len(composition_result.get("animation_improvements", []))
                        if composition_result
                        else 0
                    ),
                    "suggestions_made": (
                        len(composition_result.get("element_suggestions", []))
                        if composition_result
                        else 0
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Visual composition workflow execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Workflow execution failed: {str(e)}"],
            )
