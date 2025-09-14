"""
LangGraph workflow for LaTeX fixing operations.

This workflow orchestrates the LaTeX Specialist Agent to systematically
fix LaTeX compilation errors in Manim code.
"""

import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...domain.models import AgentState, AgentResult
from ...infrastructure.config import AgentConfig
from ...infrastructure.anthropic.client import AnthropicClient
from ..agents.latex_specialist import LaTeXSpecialistAgent


logger = logging.getLogger(__name__)


class LaTeXFixingWorkflow:
    """
    LangGraph workflow for fixing LaTeX compilation errors.

    This workflow orchestrates the LaTeX Specialist Agent to:
    1. Analyze Manim code for LaTeX issues
    2. Fix problematic expressions systematically
    3. Validate all expressions for Manim compatibility
    4. Provide detailed reports on fixes applied
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.claude_client = AnthropicClient(config.anthropic)
        self.latex_specialist = LaTeXSpecialistAgent(self.claude_client)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""

        # Define the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes (processing steps)
        workflow.add_node("analyze_code", self._analyze_code_node)
        workflow.add_node("fix_latex", self._fix_latex_node)
        workflow.add_node("validate_fixes", self._validate_fixes_node)
        workflow.add_node("finalize_results", self._finalize_results_node)

        # Define the flow
        workflow.set_entry_point("analyze_code")

        workflow.add_edge("analyze_code", "fix_latex")
        workflow.add_conditional_edges(
            "fix_latex",
            self._should_retry_fixes,
            {"retry": "fix_latex", "continue": "validate_fixes"},
        )
        workflow.add_edge("validate_fixes", "finalize_results")
        workflow.add_edge("finalize_results", END)

        # Add memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def _analyze_code_node(self, state: AgentState) -> AgentState:
        """Analyze the provided code for LaTeX issues."""
        logger.info("Analyzing Manim code for LaTeX issues")

        try:
            # Get code and error information
            manim_code = state.get("manim_code", "")
            error_log = state.get("error_log", "")

            if not manim_code:
                # Use the LaTeX specialist to generate sample problematic code
                state["manim_code"] = (
                    self.latex_specialist._create_sample_problematic_code()
                )
                state["processing_stage"] = "code_analysis_sample_generated"
                logger.info("Generated sample problematic code for demonstration")

            # Analyze the code
            code_analysis = await self.latex_specialist.analyze_manim_code(
                state["manim_code"]
            )

            # Store analysis results in state
            state["agent_messages"].append(
                {
                    "agent": "code_analyzer",
                    "status": "completed",
                    "message": "Code analysis completed",
                    "metadata": {
                        "total_expressions": code_analysis.total_latex_expressions,
                        "problematic_expressions": len(
                            code_analysis.problematic_expressions
                        ),
                        "complexity_score": code_analysis.complexity_score,
                        "issues_found": code_analysis.manim_compatibility_issues,
                    },
                }
            )

            state["processing_stage"] = "code_analysis_complete"
            logger.info(
                f"Analysis complete: {code_analysis.total_latex_expressions} expressions, "
                f"{len(code_analysis.problematic_expressions)} problematic"
            )

        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            state["errors"].append(f"Code analysis failed: {str(e)}")
            state["processing_stage"] = "code_analysis_failed"

        return state

    async def _fix_latex_node(self, state: AgentState) -> AgentState:
        """Execute LaTeX fixes using the specialist agent."""
        logger.info("Executing LaTeX Specialist Agent")

        try:
            # Process the code with the LaTeX specialist
            result = await self.latex_specialist.process(state)

            if result.success:
                logger.info("LaTeX fixes applied successfully")

                latex_result = result.data
                state["agent_messages"].append(
                    {
                        "agent": "latex_specialist",
                        "status": "success",
                        "message": f"Applied {len(latex_result.fixes_applied)} LaTeX fixes",
                        "metadata": {
                            "fixes_applied": len(latex_result.fixes_applied),
                            "expressions_validated": len(
                                latex_result.validation_results
                            ),
                            "processing_time": latex_result.processing_time,
                            "success": latex_result.success,
                        },
                    }
                )

                # Log specific fixes for transparency
                for fix in latex_result.fixes_applied:
                    logger.info(
                        f"Fixed {fix.error_type}: {fix.original_expression[:50]}... -> "
                        f"{fix.fixed_expression[:50]}... (confidence: {fix.confidence:.2f})"
                    )
            else:
                logger.error(f"LaTeX specialist failed: {result.errors}")
                state["errors"].extend(result.errors)

        except Exception as e:
            logger.error(f"LaTeX specialist node error: {e}")
            state["errors"].append(f"LaTeX specialist execution failed: {str(e)}")

        return state

    async def _validate_fixes_node(self, state: AgentState) -> AgentState:
        """Validate the applied LaTeX fixes."""
        logger.info("Validating LaTeX fixes")

        try:
            latex_result = state.get("latex_specialist_result")

            if not latex_result:
                state["errors"].append("No LaTeX specialist result to validate")
                state["processing_stage"] = "validation_failed"
                return state

            # Count validation results
            valid_expressions = sum(
                1 for v in latex_result.validation_results if v.is_valid
            )
            total_expressions = len(latex_result.validation_results)

            validation_success = valid_expressions == total_expressions

            state["agent_messages"].append(
                {
                    "agent": "validator",
                    "status": "success" if validation_success else "warning",
                    "message": f"Validated {valid_expressions}/{total_expressions} expressions",
                    "metadata": {
                        "valid_expressions": valid_expressions,
                        "total_expressions": total_expressions,
                        "validation_success": validation_success,
                        "fixes_applied": len(latex_result.fixes_applied),
                    },
                }
            )

            if validation_success:
                state["processing_stage"] = "validation_passed"
                logger.info(
                    f"All {total_expressions} expressions validated successfully"
                )
            else:
                state["processing_stage"] = "validation_partial"
                invalid_count = total_expressions - valid_expressions
                logger.warning(
                    f"{invalid_count} expressions still have validation issues"
                )

                # Add specific validation errors
                for v_result in latex_result.validation_results:
                    if not v_result.is_valid:
                        state["warnings"].extend(v_result.errors)

        except Exception as e:
            logger.error(f"Validation error: {e}")
            state["errors"].append(f"Validation failed: {str(e)}")
            state["processing_stage"] = "validation_failed"

        return state

    async def _finalize_results_node(self, state: AgentState) -> AgentState:
        """Finalize the LaTeX fixing workflow results."""
        logger.info("Finalizing LaTeX fixing results")

        state["processing_stage"] = "latex_fixing_completed"
        state["current_agent"] = "workflow_complete"

        # Create comprehensive summary
        latex_result = state.get("latex_specialist_result")
        if latex_result:
            state["agent_messages"].append(
                {
                    "agent": "workflow_summary",
                    "status": "completed",
                    "summary": {
                        "total_fixes_applied": len(latex_result.fixes_applied),
                        "expressions_processed": (
                            latex_result.code_analysis.total_latex_expressions
                            if latex_result.code_analysis
                            else 0
                        ),
                        "validation_success": latex_result.success,
                        "processing_time": latex_result.processing_time,
                        "code_complexity": (
                            latex_result.code_analysis.complexity_score
                            if latex_result.code_analysis
                            else 0.0
                        ),
                        "original_code_length": len(latex_result.original_code),
                        "fixed_code_length": len(latex_result.fixed_code),
                    },
                }
            )

        logger.info("LaTeX fixing workflow completed")
        return state

    def _should_retry_fixes(self, state: AgentState) -> str:
        """Determine if LaTeX fixes should be retried."""

        # Check if we have critical errors that warrant retry
        latex_result = state.get("latex_specialist_result")

        if not latex_result:
            return "continue"  # No result to retry

        # Count failed validations
        failed_validations = sum(
            1 for v in latex_result.validation_results if not v.is_valid
        )
        total_validations = len(latex_result.validation_results)

        # Retry if more than 50% of validations failed and we haven't retried yet
        retry_count = sum(
            1
            for msg in state["agent_messages"]
            if msg.get("agent") == "latex_specialist"
        )

        if failed_validations > (total_validations * 0.5) and retry_count < 2:
            logger.info(
                f"Retrying LaTeX fixes: {failed_validations}/{total_validations} validations failed"
            )
            return "retry"
        else:
            return "continue"

    async def fix_latex_code(
        self, manim_code: str = "", error_log: str = ""
    ) -> AgentResult:
        """
        Fix LaTeX issues in Manim code using the complete workflow.

        Args:
            manim_code: The Manim Python code containing LaTeX expressions
            error_log: Optional error log from failed compilation

        Returns:
            AgentResult: Complete LaTeX fixing results
        """
        logger.info("Starting LaTeX fixing workflow")

        # Initialize state
        initial_state = {
            "raw_content": "",
            "content_title": "LaTeX Fixing Session",
            "content_strategy": None,
            "latex_specialist_result": None,
            "manim_code": manim_code,
            "error_log": error_log,
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
                        "thread_id": f"latex_fixing_{hash(manim_code[:100])}"
                    }
                },
            )

            # Determine success
            latex_result = final_state.get("latex_specialist_result")
            success = (
                final_state["processing_stage"] == "latex_fixing_completed"
                and latex_result is not None
                and latex_result.success
                and not final_state["errors"]
            )

            return AgentResult(
                success=success,
                data=latex_result,
                errors=final_state["errors"],
                warnings=final_state["warnings"],
                metadata={
                    "workflow_state": final_state["processing_stage"],
                    "agent_messages": final_state["agent_messages"],
                    "total_processing_steps": len(final_state["agent_messages"]),
                    "fixes_applied": (
                        len(latex_result.fixes_applied) if latex_result else 0
                    ),
                },
            )

        except Exception as e:
            logger.error(f"LaTeX fixing workflow execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Workflow execution failed: {str(e)}"],
            )
