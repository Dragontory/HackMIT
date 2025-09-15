"""
LangGraph workflow for code modification operations.

This workflow orchestrates the Code Modification Agent to systematically
improve Manim code quality, positioning, timing, and educational effectiveness.
"""

import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...domain.models import AgentState, AgentResult
from ...infrastructure.config import AgentConfig
from ...infrastructure.anthropic.client import AnthropicClient
from ..agents.code_modifier import CodeModificationAgent


logger = logging.getLogger(__name__)


class CodeModificationWorkflow:
    """
    LangGraph workflow for comprehensive code modification.

    This workflow orchestrates the Code Modification Agent to:
    1. Analyze code for positioning, timing, and quality issues
    2. Apply systematic improvements for optimal rendering
    3. Validate modifications for educational effectiveness
    4. Provide detailed reports on improvements made
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.claude_client = AnthropicClient(config.anthropic)
        self.code_modifier = CodeModificationAgent(self.claude_client)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""

        # Define the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes (processing steps)
        workflow.add_node("analyze_code_issues", self._analyze_code_issues_node)
        workflow.add_node("apply_modifications", self._apply_modifications_node)
        workflow.add_node("validate_improvements", self._validate_improvements_node)
        workflow.add_node("finalize_results", self._finalize_results_node)

        # Define the flow
        workflow.set_entry_point("analyze_code_issues")

        workflow.add_edge("analyze_code_issues", "apply_modifications")
        workflow.add_conditional_edges(
            "apply_modifications",
            self._should_retry_modifications,
            {"retry": "apply_modifications", "continue": "validate_improvements"},
        )
        workflow.add_edge("validate_improvements", "finalize_results")
        workflow.add_edge("finalize_results", END)

        # Add memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def _analyze_code_issues_node(self, state: AgentState) -> AgentState:
        """Analyze the provided code for modification opportunities."""
        logger.info("Analyzing Manim code for improvement opportunities")

        try:
            # Get code and context
            manim_code = state.get("manim_code", "")
            latex_result = state.get("latex_specialist_result")
            content_strategy = state.get("content_strategy")

            if not manim_code:
                # Use the code modifier to generate sample problematic code
                state["manim_code"] = (
                    self.code_modifier._create_sample_problematic_code()
                )
                state["processing_stage"] = "code_analysis_sample_generated"
                logger.info("Generated sample problematic code for demonstration")

            # Analyze the code comprehensively
            position_analysis = await self.code_modifier.analyze_positioning(
                state["manim_code"]
            )
            timing_analysis = await self.code_modifier.analyze_timing(
                state["manim_code"]
            )
            quality_metrics = await self.code_modifier.assess_code_quality(
                state["manim_code"]
            )

            # Store analysis results in state
            state["agent_messages"].append(
                {
                    "agent": "code_analyzer",
                    "status": "completed",
                    "message": "Code analysis completed",
                    "metadata": {
                        "total_elements": position_analysis.total_elements,
                        "positioning_issues": len(
                            position_analysis.out_of_bounds_elements
                        )
                        + len(position_analysis.overlapping_elements),
                        "timing_issues": len(timing_analysis.timing_issues),
                        "screen_utilization": position_analysis.screen_utilization,
                        "educational_effectiveness": quality_metrics.educational_effectiveness,
                        "suggested_pace": timing_analysis.suggested_pace,
                    },
                }
            )

            state["processing_stage"] = "code_analysis_complete"
            logger.info(
                f"Analysis complete: {position_analysis.total_elements} elements, "
                f"{len(position_analysis.out_of_bounds_elements)} positioning issues, "
                f"{len(timing_analysis.timing_issues)} timing issues"
            )

        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            state["errors"].append(f"Code analysis failed: {str(e)}")
            state["processing_stage"] = "code_analysis_failed"

        return state

    async def _apply_modifications_node(self, state: AgentState) -> AgentState:
        """Execute code modifications using the Code Modification Agent."""
        logger.info("Executing Code Modification Agent")

        try:
            # Process the code with the code modifier
            result = await self.code_modifier.process(state)

            if result.success:
                logger.info("Code modifications applied successfully")

                mod_result = result.data
                state["agent_messages"].append(
                    {
                        "agent": "code_modifier",
                        "status": "success",
                        "message": f"Applied {len(mod_result.modifications_applied)} code modifications",
                        "metadata": {
                            "modifications_applied": len(
                                mod_result.modifications_applied
                            ),
                            "position_improvements": (
                                len(mod_result.position_analysis.out_of_bounds_elements)
                                if mod_result.position_analysis
                                else 0
                            ),
                            "timing_optimizations": (
                                len(mod_result.timing_analysis.timing_issues)
                                if mod_result.timing_analysis
                                else 0
                            ),
                            "processing_time": mod_result.processing_time,
                            "quality_improvement": (
                                mod_result.quality_metrics.educational_effectiveness
                                if mod_result.quality_metrics
                                else 0.0
                            ),
                        },
                    }
                )

                # Log specific modifications for transparency
                for mod in mod_result.modifications_applied:
                    logger.info(
                        f"Applied {mod.modification_type} modification at line {mod.line_number}: "
                        f"{mod.explanation} (confidence: {mod.confidence:.2f})"
                    )
            else:
                logger.error(f"Code modifier failed: {result.errors}")
                state["errors"].extend(result.errors)

        except Exception as e:
            logger.error(f"Code modifier node error: {e}")
            state["errors"].append(f"Code modifier execution failed: {str(e)}")

        return state

    async def _validate_improvements_node(self, state: AgentState) -> AgentState:
        """Validate the applied code modifications."""
        logger.info("Validating code modifications")

        try:
            mod_result = state.get("code_modification_result")

            if not mod_result:
                state["errors"].append("No code modification result to validate")
                state["processing_stage"] = "validation_failed"
                return state

            # Assess improvement quality
            improvements_count = len(mod_result.modifications_applied)
            validation_passed = mod_result.validation_passed

            # Calculate improvement metrics
            position_improvements = (
                len(mod_result.position_analysis.out_of_bounds_elements)
                if mod_result.position_analysis
                else 0
            )
            timing_improvements = (
                len(mod_result.timing_analysis.timing_issues)
                if mod_result.timing_analysis
                else 0
            )
            quality_score = (
                mod_result.quality_metrics.educational_effectiveness
                if mod_result.quality_metrics
                else 0.0
            )

            state["agent_messages"].append(
                {
                    "agent": "validator",
                    "status": "success" if validation_passed else "warning",
                    "message": f"Validated {improvements_count} modifications",
                    "metadata": {
                        "total_modifications": improvements_count,
                        "validation_passed": validation_passed,
                        "position_improvements": position_improvements,
                        "timing_improvements": timing_improvements,
                        "quality_score": quality_score,
                        "code_compiles": validation_passed,
                    },
                }
            )

            if validation_passed and improvements_count > 0:
                state["processing_stage"] = "validation_passed"
                logger.info(
                    f"All {improvements_count} modifications validated successfully"
                )
            else:
                state["processing_stage"] = "validation_partial"
                logger.warning(
                    f"Validation issues detected with {improvements_count} modifications"
                )

                if not validation_passed:
                    state["warnings"].append(
                        "Modified code may have syntax or structural issues"
                    )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            state["errors"].append(f"Validation failed: {str(e)}")
            state["processing_stage"] = "validation_failed"

        return state

    async def _finalize_results_node(self, state: AgentState) -> AgentState:
        """Finalize the code modification workflow results."""
        logger.info("Finalizing code modification results")

        state["processing_stage"] = "code_modification_completed"
        state["current_agent"] = "workflow_complete"

        # Create comprehensive summary
        mod_result = state.get("code_modification_result")
        if mod_result:
            # Categorize modifications by type
            mod_by_type = {}
            for mod in mod_result.modifications_applied:
                mod_type = mod.modification_type
                if mod_type not in mod_by_type:
                    mod_by_type[mod_type] = 0
                mod_by_type[mod_type] += 1

            state["agent_messages"].append(
                {
                    "agent": "workflow_summary",
                    "status": "completed",
                    "summary": {
                        "total_modifications": len(mod_result.modifications_applied),
                        "modifications_by_type": mod_by_type,
                        "validation_success": mod_result.validation_passed,
                        "processing_time": mod_result.processing_time,
                        "original_code_length": len(mod_result.original_code),
                        "modified_code_length": len(mod_result.modified_code),
                        "quality_improvement": (
                            mod_result.quality_metrics.educational_effectiveness
                            if mod_result.quality_metrics
                            else 0.0
                        ),
                        "screen_utilization": (
                            mod_result.position_analysis.screen_utilization
                            if mod_result.position_analysis
                            else 0.0
                        ),
                        "timing_optimization": (
                            mod_result.timing_analysis.suggested_pace
                            if mod_result.timing_analysis
                            else "unknown"
                        ),
                    },
                }
            )

        logger.info("Code modification workflow completed")
        return state

    def _should_retry_modifications(self, state: AgentState) -> str:
        """Determine if code modifications should be retried."""

        # Check if we have critical errors that warrant retry
        mod_result = state.get("code_modification_result")

        if not mod_result:
            return "continue"  # No result to retry

        # Retry conditions
        validation_failed = not mod_result.validation_passed
        no_improvements = len(mod_result.modifications_applied) == 0
        low_quality = (
            mod_result.quality_metrics.educational_effectiveness < 0.3
            if mod_result.quality_metrics
            else False
        )

        # Don't retry more than once
        retry_count = sum(
            1 for msg in state["agent_messages"] if msg.get("agent") == "code_modifier"
        )

        if (validation_failed or no_improvements or low_quality) and retry_count < 2:
            logger.info(
                f"Retrying code modifications: validation={validation_failed}, "
                f"improvements={not no_improvements}, quality_ok={not low_quality}"
            )
            return "retry"
        else:
            return "continue"

    async def modify_code(
        self, manim_code: str = "", latex_result=None, content_strategy=None
    ) -> AgentResult:
        """
        Modify Manim code using the complete workflow.

        Args:
            manim_code: The Manim Python code to modify
            latex_result: Optional LaTeX specialist results for context
            content_strategy: Optional content strategy for educational context

        Returns:
            AgentResult: Complete code modification results
        """
        logger.info("Starting code modification workflow")

        # Initialize state
        initial_state = {
            "raw_content": "",
            "content_title": "Code Modification Session",
            "content_strategy": content_strategy,
            "latex_specialist_result": latex_result,
            "code_modification_result": None,
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
                        "thread_id": f"code_modification_{hash(manim_code[:100])}"
                    }
                },
            )

            # Determine success
            mod_result = final_state.get("code_modification_result")
            success = (
                final_state["processing_stage"] == "code_modification_completed"
                and mod_result is not None
                and mod_result.success
                and not final_state["errors"]
            )

            return AgentResult(
                success=success,
                data=mod_result,
                errors=final_state["errors"],
                warnings=final_state["warnings"],
                metadata={
                    "workflow_state": final_state["processing_stage"],
                    "agent_messages": final_state["agent_messages"],
                    "total_processing_steps": len(final_state["agent_messages"]),
                    "modifications_applied": (
                        len(mod_result.modifications_applied) if mod_result else 0
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Code modification workflow execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Workflow execution failed: {str(e)}"],
            )
