"""
LangGraph workflow for terminal monitoring operations.

This workflow orchestrates the Terminal Monitor Agent to systematically
monitor terminal output and catch issues in real-time during Manim rendering.
"""

import logging
import time
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...domain.models import AgentState, AgentResult
from ...infrastructure.config import AgentConfig
from ...infrastructure.anthropic.client import AnthropicClient
from ..agents.terminal_monitor import TerminalMonitorAgent


logger = logging.getLogger(__name__)


class TerminalMonitoringWorkflow:
    """
    LangGraph workflow for comprehensive terminal monitoring.

    This workflow orchestrates the Terminal Monitor Agent to:
    1. Detect events in terminal output
    2. Generate actions for critical events
    3. Execute interventions when necessary
    4. Provide real-time feedback on rendering progress
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.claude_client = AnthropicClient(config.anthropic)
        self.terminal_monitor = TerminalMonitorAgent(self.claude_client)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""

        # Define the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes (processing steps)
        workflow.add_node("detect_events", self._detect_events_node)
        workflow.add_node("generate_actions", self._generate_actions_node)
        workflow.add_node("execute_actions", self._execute_actions_node)
        workflow.add_node("finalize_results", self._finalize_results_node)

        # Define the flow
        workflow.set_entry_point("detect_events")

        workflow.add_edge("detect_events", "generate_actions")
        workflow.add_edge("generate_actions", "execute_actions")
        workflow.add_conditional_edges(
            "execute_actions",
            self._should_continue_monitoring,
            {"continue": "detect_events", "finalize": "finalize_results"},
        )
        workflow.add_edge("finalize_results", END)

        # Add memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def _detect_events_node(self, state: AgentState) -> AgentState:
        """Detect events in terminal output."""
        logger.info("Detecting events in terminal output")

        try:
            # Get terminal output
            terminal_output = state.get("error_log", "")

            if not terminal_output:
                # Use the terminal monitor to generate sample output
                terminal_output = self.terminal_monitor._create_sample_terminal_output()
                state["error_log"] = terminal_output
                state["processing_stage"] = "sample_output_generated"
                logger.info("Generated sample terminal output for demonstration")

            # Initialize terminal monitoring result if not present
            from ...domain.models import TerminalMonitoringResult

            if "terminal_monitoring_result" not in state:
                state["terminal_monitoring_result"] = TerminalMonitoringResult(
                    terminal_output=terminal_output,
                    detected_events=[],
                    actions_taken=[],
                    monitoring_duration=0.0,
                    is_active=True,
                    success=True,
                )

            # Detect events
            events = await self.terminal_monitor.detect_events(terminal_output)

            # Add new events to the result
            existing_event_ids = {
                e.event_id for e in state["terminal_monitoring_result"].detected_events
            }
            new_events = [e for e in events if e.event_id not in existing_event_ids]

            state["terminal_monitoring_result"].detected_events.extend(new_events)

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "event_detector",
                    "status": "completed",
                    "message": f"Detected {len(new_events)} new events",
                    "metadata": {
                        "new_events": len(new_events),
                        "total_events": len(
                            state["terminal_monitoring_result"].detected_events
                        ),
                        "error_events": sum(
                            1 for e in new_events if e.event_type == "error"
                        ),
                        "warning_events": sum(
                            1 for e in new_events if e.event_type == "warning"
                        ),
                    },
                }
            )

            state["processing_stage"] = "events_detected"
            logger.info(f"Detected {len(new_events)} new events")

        except Exception as e:
            logger.error(f"Event detection failed: {e}")
            state["errors"].append(f"Event detection failed: {str(e)}")
            state["processing_stage"] = "event_detection_failed"

        return state

    async def _generate_actions_node(self, state: AgentState) -> AgentState:
        """Generate actions for detected events."""
        logger.info("Generating actions for detected events")

        try:
            # Get terminal monitoring result
            monitoring_result = state.get("terminal_monitoring_result")

            if not monitoring_result:
                state["errors"].append("No monitoring result to generate actions for")
                state["processing_stage"] = "action_generation_failed"
                return state

            # Get events that don't have actions yet
            events_with_actions = {
                action.event_id for action in monitoring_result.actions_taken
            }

            events_without_actions = [
                event
                for event in monitoring_result.detected_events
                if event.event_id not in events_with_actions
            ]

            # Generate actions for each event
            all_actions = []

            for event in events_without_actions:
                # Only generate actions for errors and warnings
                if event.event_type in ["error", "warning"]:
                    actions = await self.terminal_monitor.generate_actions(event)
                    all_actions.extend(actions)

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "action_generator",
                    "status": "completed",
                    "message": f"Generated {len(all_actions)} actions",
                    "metadata": {
                        "actions_generated": len(all_actions),
                        "events_processed": len(events_without_actions),
                        "fix_actions": sum(
                            1 for a in all_actions if a.action_type == "fix"
                        ),
                        "notify_actions": sum(
                            1 for a in all_actions if a.action_type == "notify"
                        ),
                    },
                }
            )

            # Update monitoring result
            monitoring_result.actions_taken.extend(all_actions)

            state["processing_stage"] = "actions_generated"
            logger.info(f"Generated {len(all_actions)} actions")

        except Exception as e:
            logger.error(f"Action generation failed: {e}")
            state["errors"].append(f"Action generation failed: {str(e)}")
            state["processing_stage"] = "action_generation_failed"

        return state

    async def _execute_actions_node(self, state: AgentState) -> AgentState:
        """Execute generated actions."""
        logger.info("Executing actions")

        try:
            # Get terminal monitoring result
            monitoring_result = state.get("terminal_monitoring_result")

            if not monitoring_result:
                state["errors"].append("No monitoring result to execute actions for")
                state["processing_stage"] = "action_execution_failed"
                return state

            # Get actions that haven't been executed yet
            unexecuted_actions = [
                action
                for action in monitoring_result.actions_taken
                if not action.is_executed
            ]

            # Execute actions
            for action in unexecuted_actions:
                result = await self.terminal_monitor.execute_action(action)
                action.result = result
                action.is_executed = True

            # Update state
            state["agent_messages"].append(
                {
                    "agent": "action_executor",
                    "status": "completed",
                    "message": f"Executed {len(unexecuted_actions)} actions",
                    "metadata": {
                        "actions_executed": len(unexecuted_actions),
                        "total_actions": len(monitoring_result.actions_taken),
                    },
                }
            )

            state["processing_stage"] = "actions_executed"
            logger.info(f"Executed {len(unexecuted_actions)} actions")

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            state["errors"].append(f"Action execution failed: {str(e)}")
            state["processing_stage"] = "action_execution_failed"

        return state

    async def _finalize_results_node(self, state: AgentState) -> AgentState:
        """Finalize the terminal monitoring workflow results."""
        logger.info("Finalizing terminal monitoring results")

        # Get terminal monitoring result
        monitoring_result = state.get("terminal_monitoring_result")

        if monitoring_result:
            # Update monitoring status
            monitoring_result.is_active = False

            # Calculate monitoring duration
            monitoring_result.monitoring_duration = time.time() - state.get(
                "start_time", time.time()
            )

            # Create comprehensive summary
            events_by_type = {}
            for event in monitoring_result.detected_events:
                if event.event_type not in events_by_type:
                    events_by_type[event.event_type] = 0
                events_by_type[event.event_type] += 1

            actions_by_type = {}
            for action in monitoring_result.actions_taken:
                if action.action_type not in actions_by_type:
                    actions_by_type[action.action_type] = 0
                actions_by_type[action.action_type] += 1

            state["agent_messages"].append(
                {
                    "agent": "workflow_summary",
                    "status": "completed",
                    "summary": {
                        "total_events": len(monitoring_result.detected_events),
                        "events_by_type": events_by_type,
                        "total_actions": len(monitoring_result.actions_taken),
                        "actions_by_type": actions_by_type,
                        "monitoring_duration": monitoring_result.monitoring_duration,
                        "success": monitoring_result.success,
                    },
                }
            )

        state["processing_stage"] = "terminal_monitoring_completed"
        state["current_agent"] = "workflow_complete"

        logger.info("Terminal monitoring workflow completed")
        return state

    def _should_continue_monitoring(
        self, state: AgentState
    ) -> Literal["continue", "finalize"]:
        """Determine if monitoring should continue."""

        # Get terminal monitoring result
        monitoring_result = state.get("terminal_monitoring_result")

        if not monitoring_result:
            return "finalize"

        # Check if monitoring is still active
        if not monitoring_result.is_active:
            return "finalize"

        # Check if we've reached the maximum number of iterations
        iteration_count = sum(
            1 for msg in state["agent_messages"] if msg.get("agent") == "event_detector"
        )

        if iteration_count >= 5:  # Limit to 5 iterations for now
            return "finalize"

        # Check if there are new events to process
        new_events = len(monitoring_result.detected_events)
        processed_events = sum(
            1 for action in monitoring_result.actions_taken if action.is_executed
        )

        if new_events > processed_events:
            return "continue"

        return "finalize"

    async def monitor_terminal(self, terminal_output: str = "") -> AgentResult:
        """
        Monitor terminal output using the complete workflow.

        Args:
            terminal_output: The terminal output to monitor

        Returns:
            AgentResult: Complete terminal monitoring results
        """
        logger.info("Starting terminal monitoring workflow")

        # Initialize state
        initial_state = {
            "raw_content": "",
            "content_title": "Terminal Monitoring Session",
            "content_strategy": None,
            "latex_specialist_result": None,
            "code_modification_result": None,
            "code_testing_result": None,
            "error_surgery_result": None,
            "terminal_monitoring_result": None,
            "manim_code": "",
            "error_log": terminal_output,
            "current_agent": "",
            "processing_stage": "initialized",
            "errors": [],
            "warnings": [],
            "agent_messages": [],
            "start_time": time.time(),
        }

        try:
            # Execute the workflow
            final_state = await self.workflow.ainvoke(
                initial_state,
                config={
                    "configurable": {
                        "thread_id": f"terminal_monitoring_{hash(terminal_output[:100])}"
                    }
                },
            )

            # Determine success
            monitoring_result = final_state.get("terminal_monitoring_result")
            success = (
                final_state["processing_stage"] == "terminal_monitoring_completed"
                and monitoring_result is not None
                and not final_state["errors"]
            )

            return AgentResult(
                success=success,
                data=monitoring_result,
                errors=final_state["errors"],
                warnings=final_state["warnings"],
                metadata={
                    "workflow_state": final_state["processing_stage"],
                    "agent_messages": final_state["agent_messages"],
                    "total_processing_steps": len(final_state["agent_messages"]),
                    "events_detected": (
                        len(monitoring_result.detected_events)
                        if monitoring_result
                        else 0
                    ),
                    "actions_taken": (
                        len(monitoring_result.actions_taken) if monitoring_result else 0
                    ),
                    "monitoring_duration": (
                        monitoring_result.monitoring_duration
                        if monitoring_result
                        else 0.0
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Terminal monitoring workflow execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Workflow execution failed: {str(e)}"],
            )

    async def start_live_monitoring(self, command: str) -> None:
        """
        Start live monitoring of a command's output.

        Args:
            command: The command to execute and monitor
        """
        await self.terminal_monitor.start_live_monitoring(command)

    async def stop_live_monitoring(self) -> AgentResult:
        """
        Stop live monitoring and return results.

        Returns:
            AgentResult: Terminal monitoring results
        """
        monitoring_result = await self.terminal_monitor.stop_live_monitoring()

        return AgentResult(
            success=True,
            data=monitoring_result,
            metadata={
                "events_detected": len(monitoring_result.detected_events),
                "actions_taken": len(monitoring_result.actions_taken),
                "monitoring_duration": monitoring_result.monitoring_duration,
            },
        )
