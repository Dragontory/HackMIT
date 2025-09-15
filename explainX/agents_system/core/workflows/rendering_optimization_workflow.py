"""
LangGraph workflow for rendering optimization operations.

This workflow orchestrates the Rendering Optimizer Agent to systematically
analyze, optimize, and enhance rendering settings for Manim animations.
"""

import logging
import time
from typing import Dict, Any, Literal, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...domain.models import AgentState, AgentResult, RenderingProfile
from ...infrastructure.config import AgentConfig
from ...infrastructure.anthropic.client import AnthropicClient
from ..agents.rendering_optimizer import RenderingOptimizerAgent


logger = logging.getLogger(__name__)


class RenderingOptimizationWorkflow:
    """
    LangGraph workflow for comprehensive rendering optimization.

    This workflow orchestrates the Rendering Optimizer Agent to:
    1. Analyze code complexity and resource requirements
    2. Generate optimization suggestions for rendering settings
    3. Apply code optimizations for better performance
    4. Create optimized rendering profiles
    5. Estimate performance improvements
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.claude_client = AnthropicClient(config.anthropic)
        self.rendering_optimizer = RenderingOptimizerAgent(self.claude_client)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""

        # Define the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes (processing steps)
        workflow.add_node("analyze_performance", self._analyze_performance_node)
        workflow.add_node("generate_suggestions", self._generate_suggestions_node)
        workflow.add_node("apply_optimizations", self._apply_optimizations_node)
        workflow.add_node("create_profile", self._create_profile_node)
        workflow.add_node("finalize_results", self._finalize_results_node)

        # Define the flow
        workflow.set_entry_point("analyze_performance")

        workflow.add_edge("analyze_performance", "generate_suggestions")
        workflow.add_edge("generate_suggestions", "apply_optimizations")
        workflow.add_edge("apply_optimizations", "create_profile")
        workflow.add_edge("create_profile", "finalize_results")
        workflow.add_edge("finalize_results", END)

        # Add memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def _analyze_performance_node(self, state: AgentState) -> AgentState:
        """Analyze rendering performance of Manim code."""
        logger.info("Analyzing rendering performance")

        try:
            # Get code
            manim_code = state.get("manim_code", "")

            if not manim_code:
                # Use the rendering optimizer to generate sample code
                manim_code = self.rendering_optimizer._create_sample_manim_code()
                state["manim_code"] = manim_code
                state["processing_stage"] = "sample_code_generated"
                logger.info("Generated sample Manim code for demonstration")

            # Get or create rendering profile
            original_profile = state.get(
                "rendering_profile", self.rendering_optimizer._create_default_profile()
            )

            # Analyze performance
            performance_metrics = await self.rendering_optimizer.analyze_performance(
                manim_code, original_profile
            )

            # Store results in state
            state["agent_messages"].append(
                {
                    "agent": "performance_analyzer",
                    "status": "completed",
                    "message": "Analyzed rendering performance",
                    "metadata": {
                        "total_render_time": (
                            performance_metrics.total_render_time
                            if performance_metrics
                            else "N/A"
                        ),
                        "frames_rendered": (
                            performance_metrics.frames_rendered
                            if performance_metrics
                            else "N/A"
                        ),
                        "average_frame_time": (
                            performance_metrics.average_frame_time
                            if performance_metrics
                            else "N/A"
                        ),
                        "bottlenecks": (
                            len(performance_metrics.bottlenecks)
                            if performance_metrics and performance_metrics.bottlenecks
                            else 0
                        ),
                    },
                }
            )

            # Create initial rendering optimization result
            state["rendering_optimization_result"] = {
                "original_code": manim_code,
                "optimized_code": manim_code,
                "original_profile": original_profile,
                "optimized_profile": original_profile,
                "performance_metrics": performance_metrics,
                "optimization_suggestions": [],
                "applied_optimizations": [],
                "estimated_time_saved": 0.0,
                "estimated_speedup": 1.0,
                "success": False,
                "processing_time": 0.0,
            }

            state["processing_stage"] = "performance_analyzed"
            logger.info("Analyzed rendering performance")

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            state["errors"].append(f"Performance analysis failed: {str(e)}")
            state["processing_stage"] = "analysis_failed"

        return state

    async def _generate_suggestions_node(self, state: AgentState) -> AgentState:
        """Generate optimization suggestions."""
        logger.info("Generating optimization suggestions")

        try:
            # Get rendering optimization result
            optimization_result = state.get("rendering_optimization_result")

            if not optimization_result:
                state["errors"].append("No rendering optimization result to improve")
                state["processing_stage"] = "suggestion_generation_failed"
                return state

            # Get code, profile, and metrics
            manim_code = optimization_result.get(
                "original_code", state.get("manim_code", "")
            )
            original_profile = optimization_result.get("original_profile")
            performance_metrics = optimization_result.get("performance_metrics")

            # Generate optimization suggestions
            optimization_suggestions = (
                await self.rendering_optimizer.generate_optimization_suggestions(
                    manim_code, original_profile, performance_metrics
                )
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "suggestion_generator",
                    "status": "completed",
                    "message": f"Generated {len(optimization_suggestions)} optimization suggestions",
                    "metadata": {
                        "suggestions_generated": len(optimization_suggestions),
                        "suggestion_categories": {
                            suggestion.category: 1
                            for suggestion in optimization_suggestions
                        },
                        "high_impact_suggestions": sum(
                            1 for s in optimization_suggestions if s.impact == "high"
                        ),
                    },
                }
            )

            # Update rendering optimization result
            optimization_result["optimization_suggestions"] = optimization_suggestions

            state["processing_stage"] = "suggestions_generated"
            logger.info(
                f"Generated {len(optimization_suggestions)} optimization suggestions"
            )

        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            state["errors"].append(f"Suggestion generation failed: {str(e)}")
            state["processing_stage"] = "suggestion_generation_failed"

        return state

    async def _apply_optimizations_node(self, state: AgentState) -> AgentState:
        """Apply code optimizations."""
        logger.info("Applying code optimizations")

        try:
            # Get rendering optimization result
            optimization_result = state.get("rendering_optimization_result")

            if not optimization_result:
                state["errors"].append("No rendering optimization result to apply")
                state["processing_stage"] = "optimization_application_failed"
                return state

            # Get code and suggestions
            manim_code = optimization_result.get(
                "original_code", state.get("manim_code", "")
            )
            optimization_suggestions = optimization_result.get(
                "optimization_suggestions", []
            )

            # Apply code optimizations
            optimized_code, applied_optimizations = (
                await self.rendering_optimizer.apply_code_optimizations(
                    manim_code, optimization_suggestions
                )
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "optimization_applier",
                    "status": "completed",
                    "message": "Applied code optimizations",
                    "metadata": {
                        "optimizations_applied": len(applied_optimizations),
                        "code_changed": optimized_code != manim_code,
                        "code_size_change": len(optimized_code) - len(manim_code),
                    },
                }
            )

            # Update rendering optimization result
            optimization_result["optimized_code"] = optimized_code
            optimization_result["applied_optimizations"] = applied_optimizations

            # Update state with optimized code
            state["manim_code"] = optimized_code

            state["processing_stage"] = "optimizations_applied"
            logger.info(f"Applied {len(applied_optimizations)} code optimizations")

        except Exception as e:
            logger.error(f"Optimization application failed: {e}")
            state["errors"].append(f"Optimization application failed: {str(e)}")
            state["processing_stage"] = "optimization_application_failed"

        return state

    async def _create_profile_node(self, state: AgentState) -> AgentState:
        """Create optimized rendering profile."""
        logger.info("Creating optimized rendering profile")

        try:
            # Get rendering optimization result
            optimization_result = state.get("rendering_optimization_result")

            if not optimization_result:
                state["errors"].append("No rendering optimization result to profile")
                state["processing_stage"] = "profile_creation_failed"
                return state

            # Get original profile, suggestions, and applied optimizations
            original_profile = optimization_result.get("original_profile")
            optimization_suggestions = optimization_result.get(
                "optimization_suggestions", []
            )
            applied_optimizations = optimization_result.get("applied_optimizations", [])

            # Create optimized profile
            optimized_profile = await self.rendering_optimizer.create_optimized_profile(
                original_profile, optimization_suggestions, applied_optimizations
            )

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "profile_creator",
                    "status": "completed",
                    "message": "Created optimized rendering profile",
                    "metadata": {
                        "original_quality": original_profile.quality,
                        "optimized_quality": optimized_profile.quality,
                        "original_resolution": f"{original_profile.resolution[0]}x{original_profile.resolution[1]}",
                        "optimized_resolution": f"{optimized_profile.resolution[0]}x{optimized_profile.resolution[1]}",
                        "profile_changes": sum(
                            1
                            for a, b in [
                                (original_profile.quality, optimized_profile.quality),
                                (
                                    original_profile.resolution,
                                    optimized_profile.resolution,
                                ),
                                (
                                    original_profile.frame_rate,
                                    optimized_profile.frame_rate,
                                ),
                                (
                                    original_profile.disable_caching,
                                    optimized_profile.disable_caching,
                                ),
                            ]
                            if a != b
                        ),
                    },
                }
            )

            # Update rendering optimization result
            optimization_result["optimized_profile"] = optimized_profile

            # Update state with optimized profile
            state["rendering_profile"] = optimized_profile

            state["processing_stage"] = "profile_created"
            logger.info("Created optimized rendering profile")

        except Exception as e:
            logger.error(f"Profile creation failed: {e}")
            state["errors"].append(f"Profile creation failed: {str(e)}")
            state["processing_stage"] = "profile_creation_failed"

        return state

    async def _finalize_results_node(self, state: AgentState) -> AgentState:
        """Finalize the rendering optimization workflow results."""
        logger.info("Finalizing rendering optimization results")

        # Get rendering optimization result
        optimization_result = state.get("rendering_optimization_result")

        if optimization_result:
            # Calculate estimated improvements
            applied_optimizations = optimization_result.get("applied_optimizations", [])
            performance_metrics = optimization_result.get("performance_metrics")

            # Add profile optimizations
            profile_optimizations = [
                s
                for s in optimization_result.get("optimization_suggestions", [])
                if s.applied and s not in applied_optimizations
            ]
            all_applied_optimizations = applied_optimizations + profile_optimizations

            # Calculate estimated speedup
            estimated_speedup = self.rendering_optimizer._calculate_estimated_speedup(
                all_applied_optimizations, performance_metrics
            )

            # Calculate estimated time saved
            estimated_time_saved = (
                performance_metrics.total_render_time * (1 - 1 / estimated_speedup)
                if performance_metrics and performance_metrics.total_render_time > 0
                else 0.0
            )

            # Determine success
            success = estimated_speedup > 1.05  # At least 5% improvement

            # Update rendering optimization result
            optimization_result["estimated_speedup"] = estimated_speedup
            optimization_result["estimated_time_saved"] = estimated_time_saved
            optimization_result["success"] = success

            # Create comprehensive summary
            state["agent_messages"].append(
                {
                    "agent": "workflow_summary",
                    "status": "completed",
                    "summary": {
                        "suggestions_generated": len(
                            optimization_result.get("optimization_suggestions", [])
                        ),
                        "optimizations_applied": len(all_applied_optimizations),
                        "estimated_speedup": f"{estimated_speedup:.2f}x",
                        "estimated_time_saved": f"{estimated_time_saved:.2f} seconds",
                        "code_optimized": optimization_result.get("optimized_code")
                        != optimization_result.get("original_code"),
                        "profile_optimized": optimization_result.get(
                            "optimized_profile"
                        )
                        != optimization_result.get("original_profile"),
                        "success": success,
                    },
                }
            )

        state["processing_stage"] = "rendering_optimization_completed"
        state["current_agent"] = "workflow_complete"

        logger.info("Rendering optimization workflow completed")
        return state

    async def optimize_rendering(
        self, manim_code: str = "", original_profile: Optional[RenderingProfile] = None
    ) -> AgentResult:
        """
        Optimize rendering settings using the complete workflow.

        Args:
            manim_code: The Manim Python code to analyze and optimize
            original_profile: The original rendering profile (optional)

        Returns:
            AgentResult: Complete rendering optimization results
        """
        logger.info("Starting rendering optimization workflow")

        # Create default profile if not provided
        if not original_profile:
            original_profile = self.rendering_optimizer._create_default_profile()

        # Initialize state
        initial_state = {
            "raw_content": "",
            "content_title": "Rendering Optimization Session",
            "content_strategy": None,
            "latex_specialist_result": None,
            "code_modification_result": None,
            "code_testing_result": None,
            "error_surgery_result": None,
            "terminal_monitoring_result": None,
            "visual_composition_result": None,
            "rendering_optimization_result": None,
            "manim_code": manim_code,
            "rendering_profile": original_profile,
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
                        "thread_id": f"rendering_optimization_{hash(manim_code[:100])}"
                    }
                },
            )

            # Determine success
            optimization_result = final_state.get("rendering_optimization_result")
            success = (
                final_state["processing_stage"] == "rendering_optimization_completed"
                and optimization_result is not None
                and optimization_result.get("success", False)
                and not final_state["errors"]
            )

            return AgentResult(
                success=success,
                data=optimization_result,
                errors=final_state["errors"],
                warnings=final_state["warnings"],
                metadata={
                    "workflow_state": final_state["processing_stage"],
                    "agent_messages": final_state["agent_messages"],
                    "total_processing_steps": len(final_state["agent_messages"]),
                    "suggestions_generated": (
                        len(optimization_result.get("optimization_suggestions", []))
                        if optimization_result
                        else 0
                    ),
                    "optimizations_applied": (
                        len(optimization_result.get("applied_optimizations", []))
                        if optimization_result
                        else 0
                    ),
                    "estimated_speedup": (
                        optimization_result.get("estimated_speedup", 1.0)
                        if optimization_result
                        else 1.0
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Rendering optimization workflow execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Workflow execution failed: {str(e)}"],
            )
