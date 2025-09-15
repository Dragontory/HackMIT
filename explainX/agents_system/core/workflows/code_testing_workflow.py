"""
LangGraph workflow for code testing operations.

This workflow orchestrates the Code Testing Agent to systematically
test Manim code before full rendering, catching errors early in the pipeline.
"""

import logging
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...domain.models import AgentState, AgentResult
from ...infrastructure.config import AgentConfig
from ...infrastructure.anthropic.client import AnthropicClient
from ..agents.code_tester import CodeTestingAgent


logger = logging.getLogger(__name__)


class CodeTestingWorkflow:
    """
    LangGraph workflow for comprehensive code testing.

    This workflow orchestrates the Code Testing Agent to:
    1. Generate test cases for Manim code
    2. Execute tests in a sandbox environment
    3. Analyze test results and provide diagnostics
    4. Generate improvement suggestions
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.claude_client = AnthropicClient(config.anthropic)
        self.code_tester = CodeTestingAgent(self.claude_client)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""

        # Define the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes (processing steps)
        workflow.add_node("generate_test_cases", self._generate_test_cases_node)
        workflow.add_node("execute_tests", self._execute_tests_node)
        workflow.add_node("analyze_results", self._analyze_results_node)
        workflow.add_node("generate_suggestions", self._generate_suggestions_node)
        workflow.add_node("finalize_results", self._finalize_results_node)

        # Define the flow
        workflow.set_entry_point("generate_test_cases")

        workflow.add_edge("generate_test_cases", "execute_tests")
        workflow.add_edge("execute_tests", "analyze_results")
        workflow.add_conditional_edges(
            "analyze_results",
            self._should_retry_tests,
            {"retry": "execute_tests", "continue": "generate_suggestions"},
        )
        workflow.add_edge("generate_suggestions", "finalize_results")
        workflow.add_edge("finalize_results", END)

        # Add memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def _generate_test_cases_node(self, state: AgentState) -> AgentState:
        """Generate test cases for the Manim code."""
        logger.info("Generating test cases for Manim code")

        try:
            # Get code to test
            manim_code = state.get("manim_code", "")

            if not manim_code:
                # Use the code tester to generate sample code
                manim_code = self.code_tester._create_sample_code()
                state["manim_code"] = manim_code
                state["processing_stage"] = "sample_code_generated"
                logger.info("Generated sample code for testing")

            # Generate test cases
            test_cases = await self.code_tester.generate_test_cases(manim_code)

            # Store test cases in state
            state["agent_messages"].append(
                {
                    "agent": "test_case_generator",
                    "status": "completed",
                    "message": f"Generated {len(test_cases)} test cases",
                    "metadata": {
                        "test_cases_count": len(test_cases),
                        "test_types": [tc.test_name for tc in test_cases],
                    },
                }
            )

            state["processing_stage"] = "test_cases_generated"
            logger.info(f"Generated {len(test_cases)} test cases")

        except Exception as e:
            logger.error(f"Test case generation error: {e}")
            state["errors"].append(f"Test case generation failed: {str(e)}")
            state["processing_stage"] = "test_case_generation_failed"

        return state

    async def _execute_tests_node(self, state: AgentState) -> AgentState:
        """Execute tests on the Manim code."""
        logger.info("Executing Code Testing Agent")

        try:
            # Process the code with the code tester
            result = await self.code_tester.process(state)

            if result.success:
                logger.info("Code testing completed successfully")

                test_result = result.data
                state["agent_messages"].append(
                    {
                        "agent": "code_tester",
                        "status": "success",
                        "message": f"Completed {len(test_result.test_cases)} tests",
                        "metadata": {
                            "test_cases_count": len(test_result.test_cases),
                            "test_cases_passed": sum(
                                1 for tc in test_result.test_cases if tc.passed
                            ),
                            "syntax_valid": test_result.syntax_valid,
                            "render_valid": test_result.render_valid,
                            "object_creation_valid": test_result.object_creation_valid,
                            "animation_valid": test_result.animation_valid,
                            "processing_time": test_result.processing_time,
                        },
                    }
                )

                # Log test results
                for test_case in test_result.test_cases:
                    status = "PASSED" if test_case.passed else "FAILED"
                    logger.info(
                        f"Test {test_case.test_id} ({test_case.test_name}): {status}"
                    )
                    if not test_case.passed and test_case.error_message:
                        logger.error(f"  Error: {test_case.error_message}")
            else:
                logger.error(f"Code testing failed: {result.errors}")
                state["errors"].extend(result.errors)

        except Exception as e:
            logger.error(f"Test execution error: {e}")
            state["errors"].append(f"Test execution failed: {str(e)}")

        return state

    async def _analyze_results_node(self, state: AgentState) -> AgentState:
        """Analyze the test results."""
        logger.info("Analyzing test results")

        try:
            test_result = state.get("code_testing_result")

            if not test_result:
                state["errors"].append("No test results to analyze")
                state["processing_stage"] = "analysis_failed"
                return state

            # Count passed and failed tests
            passed_tests = sum(1 for tc in test_result.test_cases if tc.passed)
            total_tests = len(test_result.test_cases)

            # Analyze test results
            critical_failures = []
            warnings = []

            # Check for critical failures
            if not test_result.syntax_valid:
                critical_failures.append("Syntax validation failed")

            if not test_result.object_creation_valid:
                critical_failures.append("Object creation failed")

            # Check for warnings
            if not test_result.animation_valid:
                warnings.append("Animation sequence has issues")

            if not test_result.render_valid:
                warnings.append("Rendering test failed")

            # Update state with analysis
            state["agent_messages"].append(
                {
                    "agent": "test_analyzer",
                    "status": "completed" if not critical_failures else "warning",
                    "message": f"Analyzed {total_tests} tests: {passed_tests} passed, {total_tests - passed_tests} failed",
                    "metadata": {
                        "passed_tests": passed_tests,
                        "total_tests": total_tests,
                        "pass_rate": (
                            passed_tests / total_tests if total_tests > 0 else 0
                        ),
                        "critical_failures": critical_failures,
                        "warnings": warnings,
                        "syntax_valid": test_result.syntax_valid,
                        "object_creation_valid": test_result.object_creation_valid,
                        "animation_valid": test_result.animation_valid,
                        "render_valid": test_result.render_valid,
                    },
                }
            )

            # Add critical failures and warnings to state
            state["errors"].extend(critical_failures)
            state["warnings"].extend(warnings)

            if critical_failures:
                state["processing_stage"] = "critical_test_failures"
                logger.error(f"Critical test failures: {', '.join(critical_failures)}")
            elif warnings:
                state["processing_stage"] = "test_warnings"
                logger.warning(f"Test warnings: {', '.join(warnings)}")
            else:
                state["processing_stage"] = "tests_passed"
                logger.info(f"All {total_tests} tests passed")

        except Exception as e:
            logger.error(f"Result analysis error: {e}")
            state["errors"].append(f"Result analysis failed: {str(e)}")
            state["processing_stage"] = "analysis_failed"

        return state

    async def _generate_suggestions_node(self, state: AgentState) -> AgentState:
        """Generate improvement suggestions based on test results."""
        logger.info("Generating improvement suggestions")

        try:
            test_result = state.get("code_testing_result")

            if not test_result:
                state["warnings"].append("No test results for suggestion generation")
                return state

            # Get suggestions from the test result
            suggestions = test_result.suggestions

            # Add suggestions to state
            state["agent_messages"].append(
                {
                    "agent": "suggestion_generator",
                    "status": "completed",
                    "message": f"Generated {len(suggestions)} improvement suggestions",
                    "metadata": {
                        "suggestions_count": len(suggestions),
                        "suggestions": suggestions,
                    },
                }
            )

            logger.info(f"Generated {len(suggestions)} improvement suggestions")

        except Exception as e:
            logger.error(f"Suggestion generation error: {e}")
            state["errors"].append(f"Suggestion generation failed: {str(e)}")

        return state

    async def _finalize_results_node(self, state: AgentState) -> AgentState:
        """Finalize the code testing workflow results."""
        logger.info("Finalizing code testing results")

        state["processing_stage"] = "code_testing_completed"
        state["current_agent"] = "workflow_complete"

        # Create comprehensive summary
        test_result = state.get("code_testing_result")
        if test_result:
            # Calculate test statistics
            passed_tests = sum(1 for tc in test_result.test_cases if tc.passed)
            total_tests = len(test_result.test_cases)
            pass_rate = passed_tests / total_tests if total_tests > 0 else 0

            # Group test results by type
            test_results_by_type = {}
            for tr in test_result.manim_test_results:
                if tr.test_type not in test_results_by_type:
                    test_results_by_type[tr.test_type] = {"passed": 0, "failed": 0}

                if tr.success:
                    test_results_by_type[tr.test_type]["passed"] += 1
                else:
                    test_results_by_type[tr.test_type]["failed"] += 1

            state["agent_messages"].append(
                {
                    "agent": "workflow_summary",
                    "status": "completed",
                    "summary": {
                        "total_tests": total_tests,
                        "passed_tests": passed_tests,
                        "failed_tests": total_tests - passed_tests,
                        "pass_rate": pass_rate,
                        "test_results_by_type": test_results_by_type,
                        "syntax_valid": test_result.syntax_valid,
                        "render_valid": test_result.render_valid,
                        "object_creation_valid": test_result.object_creation_valid,
                        "animation_valid": test_result.animation_valid,
                        "suggestions_count": len(test_result.suggestions),
                        "processing_time": test_result.processing_time,
                    },
                }
            )

        logger.info("Code testing workflow completed")
        return state

    def _should_retry_tests(self, state: AgentState) -> Literal["retry", "continue"]:
        """Determine if tests should be retried."""

        # Check if we have critical errors that warrant retry
        test_result = state.get("code_testing_result")

        if not test_result:
            return "continue"  # No result to retry

        # Check for specific retryable issues
        retryable_issues = [
            "ImportError",
            "ModuleNotFoundError",
            "FileNotFoundError",
            "PermissionError",
            "TimeoutError",
        ]

        # Check if any test has these issues
        has_retryable_issue = False
        for test_case in test_result.test_cases:
            if not test_case.passed and test_case.error_message:
                if any(issue in test_case.error_message for issue in retryable_issues):
                    has_retryable_issue = True
                    break

        # Don't retry more than once
        retry_count = sum(
            1 for msg in state["agent_messages"] if msg.get("agent") == "code_tester"
        )

        if has_retryable_issue and retry_count < 2:
            logger.info("Retrying tests due to retryable issues")
            return "retry"
        else:
            return "continue"

    async def test_code(self, manim_code: str) -> AgentResult:
        """
        Test Manim code using the complete workflow.

        Args:
            manim_code: The Manim Python code to test

        Returns:
            AgentResult: Complete code testing results
        """
        logger.info("Starting code testing workflow")

        # Initialize state
        initial_state = {
            "raw_content": "",
            "content_title": "Code Testing Session",
            "content_strategy": None,
            "latex_specialist_result": None,
            "code_modification_result": None,
            "code_testing_result": None,
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
                        "thread_id": f"code_testing_{hash(manim_code[:100])}"
                    }
                },
            )

            # Determine success
            test_result = final_state.get("code_testing_result")
            success = (
                final_state["processing_stage"] == "code_testing_completed"
                and test_result is not None
                and test_result.success
                and not final_state["errors"]
            )

            return AgentResult(
                success=success,
                data=test_result,
                errors=final_state["errors"],
                warnings=final_state["warnings"],
                metadata={
                    "workflow_state": final_state["processing_stage"],
                    "agent_messages": final_state["agent_messages"],
                    "total_processing_steps": len(final_state["agent_messages"]),
                    "test_cases_count": (
                        len(test_result.test_cases) if test_result else 0
                    ),
                    "test_cases_passed": (
                        sum(1 for tc in test_result.test_cases if tc.passed)
                        if test_result
                        else 0
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Code testing workflow execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Workflow execution failed: {str(e)}"],
            )
