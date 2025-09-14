"""
LangGraph workflow for error surgery operations.

This workflow orchestrates the Error Surgeon Agent to systematically
diagnose and fix specific errors in Manim code.
"""

import logging
import ast
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...domain.models import AgentState, AgentResult
from ...infrastructure.config import AgentConfig
from ...infrastructure.anthropic.client import AnthropicClient
from ..agents.error_surgeon import ErrorSurgeonAgent


logger = logging.getLogger(__name__)


class ErrorSurgeryWorkflow:
    """
    LangGraph workflow for comprehensive error surgery.

    This workflow orchestrates the Error Surgeon Agent to:
    1. Diagnose specific errors in Manim code
    2. Generate targeted fixes for each error
    3. Apply surgical fixes without disrupting working code
    4. Validate fixes and handle unfixable errors
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.claude_client = AnthropicClient(config.anthropic)
        self.error_surgeon = ErrorSurgeonAgent(self.claude_client)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""

        # Define the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes (processing steps)
        workflow.add_node("diagnose_errors", self._diagnose_errors_node)
        workflow.add_node("generate_fixes", self._generate_fixes_node)
        workflow.add_node("apply_fixes", self._apply_fixes_node)
        workflow.add_node("validate_fixes", self._validate_fixes_node)
        workflow.add_node("finalize_results", self._finalize_results_node)

        # Define the flow
        workflow.set_entry_point("diagnose_errors")

        workflow.add_edge("diagnose_errors", "generate_fixes")
        workflow.add_edge("generate_fixes", "apply_fixes")
        workflow.add_edge("apply_fixes", "validate_fixes")
        workflow.add_conditional_edges(
            "validate_fixes",
            self._should_retry_fixes,
            {"retry": "generate_fixes", "continue": "finalize_results"},
        )
        workflow.add_edge("finalize_results", END)

        # Add memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def _diagnose_errors_node(self, state: AgentState) -> AgentState:
        """Diagnose errors in the Manim code."""
        logger.info("Diagnosing errors in Manim code")

        try:
            # Get code and error context
            manim_code = state.get("manim_code", "")
            error_log = state.get("error_log", "")
            testing_result = state.get("code_testing_result")

            if not manim_code:
                # Use the error surgeon to generate sample code with errors
                manim_code, error_log = (
                    self.error_surgeon._create_sample_code_with_errors()
                )
                state["manim_code"] = manim_code
                state["error_log"] = error_log
                state["processing_stage"] = "sample_code_generated"
                logger.info("Generated sample code with errors for demonstration")

            # Diagnose errors
            error_diagnoses = await self.error_surgeon.diagnose_errors(
                manim_code, error_log, testing_result
            )

            # Store diagnoses in state
            state["agent_messages"].append(
                {
                    "agent": "error_diagnostician",
                    "status": "completed",
                    "message": f"Diagnosed {len(error_diagnoses)} errors",
                    "metadata": {
                        "error_count": len(error_diagnoses),
                        "error_types": [ed.error_type for ed in error_diagnoses],
                        "severity_levels": [ed.severity for ed in error_diagnoses],
                    },
                }
            )

            # Create initial error surgery result
            state["error_surgery_result"] = {
                "original_code": manim_code,
                "fixed_code": manim_code,  # Start with original code
                "error_diagnoses": error_diagnoses,
                "applied_fixes": [],
                "unfixable_errors": [],
                "success": False,
                "requires_human_intervention": False,
            }

            state["processing_stage"] = "errors_diagnosed"
            logger.info(f"Diagnosed {len(error_diagnoses)} errors")

        except Exception as e:
            logger.error(f"Error diagnosis failed: {e}")
            state["errors"].append(f"Error diagnosis failed: {str(e)}")
            state["processing_stage"] = "diagnosis_failed"

        return state

    async def _generate_fixes_node(self, state: AgentState) -> AgentState:
        """Generate fixes for diagnosed errors."""
        logger.info("Generating fixes for diagnosed errors")

        try:
            # Get error surgery result
            surgery_result = state.get("error_surgery_result")

            if not surgery_result:
                state["errors"].append("No error diagnoses to generate fixes for")
                state["processing_stage"] = "fix_generation_failed"
                return state

            # Get code and diagnoses
            manim_code = surgery_result.get("fixed_code", state.get("manim_code", ""))
            error_diagnoses = surgery_result.get("error_diagnoses", [])

            # Generate fixes for each error
            all_fixes = []
            unfixable_errors = []

            for diagnosis in error_diagnoses:
                # Skip errors that already have fixes
                if any(
                    fix.error_id == diagnosis.error_id
                    for fix in surgery_result.get("applied_fixes", [])
                ):
                    continue

                # Skip errors already marked as unfixable
                if diagnosis in surgery_result.get("unfixable_errors", []):
                    unfixable_errors.append(diagnosis)
                    continue

                # Generate fixes
                fixes = await self.error_surgeon.generate_fixes(manim_code, diagnosis)

                if fixes:
                    all_fixes.extend(fixes)
                else:
                    unfixable_errors.append(diagnosis)

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "fix_generator",
                    "status": "completed",
                    "message": f"Generated {len(all_fixes)} fixes for {len(error_diagnoses)} errors",
                    "metadata": {
                        "fixes_generated": len(all_fixes),
                        "unfixable_errors": len(unfixable_errors),
                        "fix_confidence": sum(fix.confidence for fix in all_fixes)
                        / max(len(all_fixes), 1),
                    },
                }
            )

            # Update error surgery result
            surgery_result["all_fixes"] = all_fixes
            surgery_result["unfixable_errors"] = unfixable_errors

            state["processing_stage"] = "fixes_generated"
            logger.info(
                f"Generated {len(all_fixes)} fixes, {len(unfixable_errors)} unfixable errors"
            )

        except Exception as e:
            logger.error(f"Fix generation failed: {e}")
            state["errors"].append(f"Fix generation failed: {str(e)}")
            state["processing_stage"] = "fix_generation_failed"

        return state

    async def _apply_fixes_node(self, state: AgentState) -> AgentState:
        """Apply generated fixes to the code."""
        logger.info("Applying fixes to Manim code")

        try:
            # Get error surgery result
            surgery_result = state.get("error_surgery_result")

            if not surgery_result:
                state["errors"].append("No fixes to apply")
                state["processing_stage"] = "fix_application_failed"
                return state

            # Get code and fixes
            manim_code = surgery_result.get("fixed_code", state.get("manim_code", ""))
            all_fixes = surgery_result.get("all_fixes", [])

            # Sort fixes by confidence (highest first) and line number (if available)
            sorted_fixes = sorted(
                all_fixes,
                key=lambda fix: (
                    -fix.confidence,
                    fix.line_number if fix.line_number is not None else float("inf"),
                ),
            )

            # First, apply syntax fixes (they're usually simpler and more reliable)
            syntax_fixes = [
                fix
                for fix in sorted_fixes
                if any(
                    diag.error_type == "syntax"
                    for diag in surgery_result.get("error_diagnoses", [])
                    if diag.error_id == fix.error_id
                )
            ]

            # Then apply other fixes
            other_fixes = [fix for fix in sorted_fixes if fix not in syntax_fixes]

            # Apply fixes in order: syntax first, then others
            prioritized_fixes = syntax_fixes + other_fixes

            # Apply fixes
            fixed_code = manim_code
            applied_fixes = surgery_result.get("applied_fixes", [])

            for fix in prioritized_fixes:
                # Skip fixes that require human review for now
                if fix.requires_human_review:
                    continue

                # Skip fixes that have already been applied
                if any(af.fix_id == fix.fix_id for af in applied_fixes):
                    continue

                # Apply the fix
                try:
                    fixed_code = self.error_surgeon._apply_fix(fixed_code, fix)
                    fix.is_applied = True
                    applied_fixes.append(fix)

                    # For syntax fixes, validate after each fix
                    if any(
                        diag.error_type == "syntax"
                        for diag in surgery_result.get("error_diagnoses", [])
                        if diag.error_id == fix.error_id
                    ):
                        try:
                            ast.parse(fixed_code)
                            # If we've fixed the syntax error, break out of the loop
                            logger.info(f"Syntax fix successful: {fix.fix_description}")
                        except SyntaxError:
                            # If syntax is still invalid, continue with other fixes
                            pass
                except Exception as e:
                    logger.error(f"Failed to apply fix {fix.fix_id}: {e}")
                    fix.is_applied = False

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "fix_applier",
                    "status": "completed",
                    "message": f"Applied {len(applied_fixes)} fixes",
                    "metadata": {
                        "fixes_applied": len(applied_fixes),
                        "fixes_remaining": len(all_fixes) - len(applied_fixes),
                        "syntax_fixes_applied": len(
                            [f for f in applied_fixes if f in syntax_fixes]
                        ),
                        "code_changed": fixed_code != manim_code,
                    },
                }
            )

            # Update error surgery result
            surgery_result["fixed_code"] = fixed_code
            surgery_result["applied_fixes"] = applied_fixes

            state["processing_stage"] = "fixes_applied"
            logger.info(f"Applied {len(applied_fixes)} fixes")

        except Exception as e:
            logger.error(f"Fix application failed: {e}")
            state["errors"].append(f"Fix application failed: {str(e)}")
            state["processing_stage"] = "fix_application_failed"

        return state

    async def _validate_fixes_node(self, state: AgentState) -> AgentState:
        """Validate the applied fixes."""
        logger.info("Validating applied fixes")

        try:
            # Get error surgery result
            surgery_result = state.get("error_surgery_result")

            if not surgery_result:
                state["errors"].append("No fixes to validate")
                state["processing_stage"] = "fix_validation_failed"
                return state

            # Get fixed code and applied fixes
            fixed_code = surgery_result.get("fixed_code", "")
            applied_fixes = surgery_result.get("applied_fixes", [])
            unfixable_errors = surgery_result.get("unfixable_errors", [])

            # Basic validation: check if code is syntactically valid
            try:
                ast.parse(fixed_code)
                syntax_valid = True
            except SyntaxError:
                syntax_valid = False

            # Check if there are still unfixed errors
            has_unfixed_errors = len(unfixable_errors) > 0

            # Check if human intervention is required
            requires_human_intervention = has_unfixed_errors or any(
                fix.requires_human_review for fix in surgery_result.get("all_fixes", [])
            )

            # Determine success
            success = len(applied_fixes) > 0 and syntax_valid

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "fix_validator",
                    "status": "completed" if success else "warning",
                    "message": f"Validated {len(applied_fixes)} fixes",
                    "metadata": {
                        "syntax_valid": syntax_valid,
                        "has_unfixed_errors": has_unfixed_errors,
                        "requires_human_intervention": requires_human_intervention,
                        "success": success,
                    },
                }
            )

            # Update error surgery result
            surgery_result["success"] = success
            surgery_result["requires_human_intervention"] = requires_human_intervention

            if success:
                state["processing_stage"] = "fixes_validated"
                logger.info(f"Successfully validated {len(applied_fixes)} fixes")
            else:
                state["processing_stage"] = "validation_failed"
                if not syntax_valid:
                    state["warnings"].append("Fixed code still has syntax errors")
                if has_unfixed_errors:
                    state["warnings"].append(
                        f"There are {len(unfixable_errors)} unfixable errors"
                    )
                logger.warning(
                    f"Fix validation issues: syntax_valid={syntax_valid}, unfixed_errors={has_unfixed_errors}"
                )

        except Exception as e:
            logger.error(f"Fix validation failed: {e}")
            state["errors"].append(f"Fix validation failed: {str(e)}")
            state["processing_stage"] = "validation_failed"

        return state

    async def _finalize_results_node(self, state: AgentState) -> AgentState:
        """Finalize the error surgery workflow results."""
        logger.info("Finalizing error surgery results")

        # Get error surgery result
        surgery_result = state.get("error_surgery_result")

        if surgery_result:
            # Update state with final code
            state["manim_code"] = surgery_result.get(
                "fixed_code", state.get("manim_code", "")
            )

            # Create comprehensive summary
            applied_fixes = surgery_result.get("applied_fixes", [])
            unfixable_errors = surgery_result.get("unfixable_errors", [])

            # Group fixes by error type
            fixes_by_type = {}
            for fix in applied_fixes:
                error_type = next(
                    (
                        d.error_type
                        for d in surgery_result.get("error_diagnoses", [])
                        if d.error_id == fix.error_id
                    ),
                    "unknown",
                )
                if error_type not in fixes_by_type:
                    fixes_by_type[error_type] = []
                fixes_by_type[error_type].append(fix)

            state["agent_messages"].append(
                {
                    "agent": "workflow_summary",
                    "status": "completed",
                    "summary": {
                        "errors_diagnosed": len(
                            surgery_result.get("error_diagnoses", [])
                        ),
                        "fixes_applied": len(applied_fixes),
                        "unfixable_errors": len(unfixable_errors),
                        "fixes_by_type": {k: len(v) for k, v in fixes_by_type.items()},
                        "requires_human_intervention": surgery_result.get(
                            "requires_human_intervention", False
                        ),
                        "success": surgery_result.get("success", False),
                    },
                }
            )

        state["processing_stage"] = "error_surgery_completed"
        state["current_agent"] = "workflow_complete"

        logger.info("Error surgery workflow completed")
        return state

    def _should_retry_fixes(self, state: AgentState) -> Literal["retry", "continue"]:
        """Determine if fix generation should be retried."""

        # Get error surgery result
        surgery_result = state.get("error_surgery_result")

        if not surgery_result:
            return "continue"  # No result to retry

        # Check if we have applied any fixes
        applied_fixes = surgery_result.get("applied_fixes", [])

        # Check if there are still errors to fix
        unfixed_diagnoses = [
            d
            for d in surgery_result.get("error_diagnoses", [])
            if not any(
                fix.error_id == d.error_id and fix.is_applied for fix in applied_fixes
            )
            and d not in surgery_result.get("unfixable_errors", [])
        ]

        # Don't retry more than once
        retry_count = sum(
            1 for msg in state["agent_messages"] if msg.get("agent") == "fix_generator"
        )

        if unfixed_diagnoses and retry_count < 2:
            logger.info(
                f"Retrying fix generation for {len(unfixed_diagnoses)} unfixed errors"
            )
            return "retry"
        else:
            return "continue"

    async def fix_errors(
        self, manim_code: str, error_log: str = "", testing_result=None
    ) -> AgentResult:
        """
        Fix errors in Manim code using the complete workflow.

        Args:
            manim_code: The Manim Python code to fix
            error_log: Error log from previous rendering attempt
            testing_result: Results from Code Testing Agent

        Returns:
            AgentResult: Complete error surgery results
        """
        logger.info("Starting error surgery workflow")

        # Initialize state
        initial_state = {
            "raw_content": "",
            "content_title": "Error Surgery Session",
            "content_strategy": None,
            "latex_specialist_result": None,
            "code_modification_result": None,
            "code_testing_result": testing_result,
            "error_surgery_result": None,
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
                        "thread_id": f"error_surgery_{hash(manim_code[:100])}"
                    }
                },
            )

            # Determine success
            surgery_result = final_state.get("error_surgery_result")
            success = (
                final_state["processing_stage"] == "error_surgery_completed"
                and surgery_result is not None
                and surgery_result.get("success", False)
                and not final_state["errors"]
            )

            return AgentResult(
                success=success,
                data=surgery_result,
                errors=final_state["errors"],
                warnings=final_state["warnings"],
                metadata={
                    "workflow_state": final_state["processing_stage"],
                    "agent_messages": final_state["agent_messages"],
                    "total_processing_steps": len(final_state["agent_messages"]),
                    "errors_diagnosed": (
                        len(surgery_result.get("error_diagnoses", []))
                        if surgery_result
                        else 0
                    ),
                    "fixes_applied": (
                        len(surgery_result.get("applied_fixes", []))
                        if surgery_result
                        else 0
                    ),
                    "requires_human_intervention": (
                        surgery_result.get("requires_human_intervention", False)
                        if surgery_result
                        else True
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Error surgery workflow execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Workflow execution failed: {str(e)}"],
            )
