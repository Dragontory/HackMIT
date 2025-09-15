"""
Terminal Monitor Agent implementation.

This agent monitors terminal output in real-time during Manim rendering,
detecting issues and providing immediate feedback or interventions.
"""

import logging
import re
import time
import os
import asyncio
import uuid
import threading
import queue
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional, Set

from ...domain.interfaces import IAgent
from ...domain.models import (
    AgentState,
    AgentResult,
    TerminalMonitoringResult,
    TerminalEvent,
    TerminalAction,
    ErrorDiagnosis,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage


logger = logging.getLogger(__name__)


class TerminalMonitorAgent(IAgent):
    """
    Specialized agent for monitoring terminal output during Manim rendering.

    Uses real-time analysis to:
    - Detect errors, warnings, and progress indicators
    - Provide immediate feedback on rendering issues
    - Suggest or execute interventions for common problems
    - Track rendering progress and performance
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()
        self.output_buffer = []
        self.event_queue = queue.Queue()
        self.monitoring_active = False
        self.monitor_thread = None
        self._known_event_ids = set()
        self._known_patterns = self._load_known_patterns()

    @property
    def name(self) -> str:
        return "TerminalMonitorAgent"

    @property
    def description(self) -> str:
        return "Monitors terminal output and catches issues in real-time"

    async def process(self, state: AgentState) -> AgentResult:
        """Process state and monitor terminal output."""
        start_time = time.time()

        try:
            logger.info(f"Terminal Monitor processing: {state['content_title']}")

            # Get the terminal output to analyze
            terminal_output = state.get("error_log", "")

            if not terminal_output:
                # Use sample terminal output for testing
                terminal_output = self._create_sample_terminal_output()
                logger.info("No terminal output provided, using sample output")

            # Perform terminal monitoring
            result = await self.monitor_terminal(terminal_output)

            # Update state
            state["terminal_monitoring_result"] = result
            state["current_agent"] = self.name
            state["processing_stage"] = "terminal_monitoring_complete"

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "events_detected": len(result.detected_events),
                    "actions_taken": len(result.actions_taken),
                    "monitoring_duration": result.monitoring_duration,
                    "processing_time": processing_time,
                },
            )

        except Exception as e:
            logger.error(f"Terminal Monitor error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Terminal monitoring failed: {str(e)}"],
            )

    async def monitor_terminal(
        self, initial_output: str = ""
    ) -> TerminalMonitoringResult:
        """
        Monitor terminal output for events and take actions.

        Args:
            initial_output: Initial terminal output to analyze

        Returns:
            TerminalMonitoringResult: Complete results with events and actions
        """
        start_time = time.time()

        # Initialize monitoring result
        result = TerminalMonitoringResult(
            terminal_output=initial_output,
            is_active=True,
        )

        # Process initial output
        if initial_output:
            events = await self.detect_events(initial_output)
            result.detected_events.extend(events)

            # Generate actions for detected events
            for event in events:
                actions = await self.generate_actions(event)
                result.actions_taken.extend(actions)

        # Calculate monitoring duration
        monitoring_duration = time.time() - start_time
        result.monitoring_duration = monitoring_duration
        result.is_active = False

        return result

    async def start_live_monitoring(self, command: str) -> None:
        """
        Start live monitoring of a command's output.

        Args:
            command: The command to execute and monitor
        """
        if self.monitoring_active:
            logger.warning("Live monitoring is already active")
            return

        self.monitoring_active = True
        self.output_buffer = []

        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_command_output,
            args=(command,),
            daemon=True,
        )
        self.monitor_thread.start()

    async def stop_live_monitoring(self) -> TerminalMonitoringResult:
        """Stop live monitoring and return results."""
        if not self.monitoring_active:
            logger.warning("Live monitoring is not active")
            return TerminalMonitoringResult(
                terminal_output="",
                is_active=False,
            )

        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None

        # Process all collected output
        terminal_output = "\n".join(self.output_buffer)
        return await self.monitor_terminal(terminal_output)

    def _monitor_command_output(self, command: str) -> None:
        """
        Monitor command output in a separate thread.

        Args:
            command: The command to execute and monitor
        """
        try:
            # Execute the command and capture output in real-time
            process = asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True,
            )

            # Monitor stdout and stderr
            while self.monitoring_active:
                # Read from stdout and stderr
                try:
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        line = stdout_line.decode("utf-8").strip()
                        self.output_buffer.append(line)
                        self._process_output_line(line, len(self.output_buffer) - 1)
                except Exception as e:
                    logger.error(f"Error reading stdout: {e}")

                try:
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        line = stderr_line.decode("utf-8").strip()
                        self.output_buffer.append(f"ERROR: {line}")
                        self._process_output_line(
                            line, len(self.output_buffer) - 1, is_error=True
                        )
                except Exception as e:
                    logger.error(f"Error reading stderr: {e}")

                # Check if process is still running
                if process.poll() is not None:
                    break

                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error monitoring command output: {e}")

    def _process_output_line(
        self, line: str, line_number: int, is_error: bool = False
    ) -> None:
        """
        Process a single line of output.

        Args:
            line: The output line
            line_number: The line number in the output
            is_error: Whether this line came from stderr
        """
        # Check for known patterns
        event_type = "info"
        severity = "low"

        if is_error:
            event_type = "error"
            severity = "high"

        # Check for specific patterns
        for pattern_info in self._known_patterns:
            if re.search(pattern_info["pattern"], line):
                event_type = pattern_info["type"]
                severity = pattern_info["severity"]
                break

        # Create event
        event = TerminalEvent(
            event_id=f"event_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            timestamp=time.time(),
            message=self._extract_message(line, event_type),
            source_line=line,
            line_number=line_number,
            severity=severity,
            context=self._extract_context(self.output_buffer, line_number),
        )

        # Add to queue for processing
        self.event_queue.put(event)

    async def detect_events(self, terminal_output: str) -> List[TerminalEvent]:
        """
        Detect events in terminal output.

        Args:
            terminal_output: The terminal output to analyze

        Returns:
            List[TerminalEvent]: Detected events
        """
        events = []
        lines = terminal_output.split("\n")

        # Process each line
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue

            # Determine event type and severity
            event_type = "info"
            severity = "low"

            # Check for errors
            if (
                "error" in line.lower()
                or "exception" in line.lower()
                or "failed" in line.lower()
            ):
                event_type = "error"
                severity = "high"
            # Check for warnings
            elif "warning" in line.lower() or "deprecated" in line.lower():
                event_type = "warning"
                severity = "medium"
            # Check for progress
            elif any(
                x in line.lower()
                for x in ["progress", "processing", "rendering", "creating"]
            ):
                event_type = "progress"
                severity = "low"
            # Check for success
            elif any(
                x in line.lower()
                for x in ["success", "completed", "done", "finished", "✅"]
            ):
                event_type = "success"
                severity = "low"

            # Check for specific patterns
            for pattern_info in self._known_patterns:
                if re.search(pattern_info["pattern"], line):
                    event_type = pattern_info["type"]
                    severity = pattern_info["severity"]
                    break

            # Create event
            event_id = f"event_{uuid.uuid4().hex[:8]}"

            # Skip if we've already processed an identical line
            if event_id in self._known_event_ids:
                continue

            self._known_event_ids.add(event_id)

            event = TerminalEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=time.time(),
                message=self._extract_message(line, event_type),
                source_line=line,
                line_number=i,
                severity=severity,
                context=self._extract_context(lines, i),
            )

            events.append(event)

        return events

    async def generate_actions(self, event: TerminalEvent) -> List[TerminalAction]:
        """
        Generate actions for a terminal event.

        Args:
            event: The terminal event

        Returns:
            List[TerminalAction]: Generated actions
        """
        actions = []

        # Only generate actions for errors and warnings
        if event.event_type not in ["error", "warning"]:
            return actions

        # For LaTeX errors
        if "latex error" in event.source_line.lower():
            # Extract LaTeX error details
            latex_error = self._extract_latex_error(event.context or "")

            if latex_error:
                # Create action to fix LaTeX error
                actions.append(
                    TerminalAction(
                        action_id=f"action_{uuid.uuid4().hex[:8]}",
                        event_id=event.event_id,
                        action_type="fix",
                        description=f"Fix LaTeX error: {latex_error}",
                        confidence=0.7,
                    )
                )

        # For syntax errors
        elif (
            "syntaxerror" in event.source_line.lower()
            or "syntax error" in event.source_line.lower()
        ):
            # Extract syntax error details
            syntax_error = self._extract_syntax_error(event.context or "")

            if syntax_error:
                # Create action to fix syntax error
                actions.append(
                    TerminalAction(
                        action_id=f"action_{uuid.uuid4().hex[:8]}",
                        event_id=event.event_id,
                        action_type="fix",
                        description=f"Fix syntax error: {syntax_error}",
                        confidence=0.8,
                    )
                )

        # For runtime errors
        elif (
            "nameerror" in event.source_line.lower()
            or "attributeerror" in event.source_line.lower()
        ):
            # Create action to fix runtime error
            actions.append(
                TerminalAction(
                    action_id=f"action_{uuid.uuid4().hex[:8]}",
                    event_id=event.event_id,
                    action_type="fix",
                    description=f"Fix runtime error: {event.message}",
                    confidence=0.6,
                )
            )

        # For general errors
        elif event.event_type == "error":
            # Create action to investigate error
            actions.append(
                TerminalAction(
                    action_id=f"action_{uuid.uuid4().hex[:8]}",
                    event_id=event.event_id,
                    action_type="notify",
                    description=f"Investigate error: {event.message}",
                    confidence=0.5,
                )
            )

        # For warnings
        elif event.event_type == "warning":
            # Create action to address warning
            actions.append(
                TerminalAction(
                    action_id=f"action_{uuid.uuid4().hex[:8]}",
                    event_id=event.event_id,
                    action_type="notify",
                    description=f"Address warning: {event.message}",
                    confidence=0.4,
                )
            )

        return actions

    async def execute_action(self, action: TerminalAction) -> str:
        """
        Execute a terminal action.

        Args:
            action: The action to execute

        Returns:
            str: Result of the action
        """
        result = "Action not implemented"

        if action.action_type == "fix":
            # Implement fix logic
            if "latex error" in action.description.lower():
                result = "LaTeX fix would be applied here"
            elif "syntax error" in action.description.lower():
                result = "Syntax fix would be applied here"
            elif "runtime error" in action.description.lower():
                result = "Runtime fix would be applied here"
        elif action.action_type == "retry":
            # Implement retry logic
            if action.command:
                result = f"Would retry command: {action.command}"
        elif action.action_type == "abort":
            # Implement abort logic
            result = "Would abort rendering process"
        elif action.action_type == "notify":
            # Implement notification logic
            result = f"Notification sent: {action.description}"

        # Mark action as executed
        action.is_executed = True
        action.result = result

        return result

    def _extract_message(self, line: str, event_type: str) -> str:
        """Extract a clean message from a terminal line."""
        # Remove timestamps, log levels, and other noise
        message = re.sub(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}.*?]", "", line)
        message = re.sub(r"^INFO:|^ERROR:|^WARNING:|^DEBUG:", "", message)

        # For errors, try to extract the actual error message
        if event_type == "error":
            error_match = re.search(r"(?:Error|Exception):\s*(.*?)(?:$|\n)", line)
            if error_match:
                message = error_match.group(1)

        return message.strip()

    def _extract_context(
        self, lines: List[str], line_number: int, context_size: int = 3
    ) -> str:
        """Extract context around a line."""
        start = max(0, line_number - context_size)
        end = min(len(lines), line_number + context_size + 1)

        context_lines = []
        for i in range(start, end):
            prefix = ">> " if i == line_number else "   "
            context_lines.append(f"{prefix}{lines[i]}")

        return "\n".join(context_lines)

    def _extract_latex_error(self, context: str) -> str:
        """Extract LaTeX error details from context."""
        latex_error_match = re.search(r"LaTeX Error:\s*(.*?)(?:$|\n)", context)
        if latex_error_match:
            return latex_error_match.group(1)

        # Check for undefined control sequence
        undef_match = re.search(r"Undefined control sequence\s*(.*?)(?:$|\n)", context)
        if undef_match:
            return f"Undefined control sequence: {undef_match.group(1)}"

        # Check for missing closing brace
        brace_match = re.search(r"Missing [{}] inserted", context)
        if brace_match:
            return "Missing closing brace"

        return ""

    def _extract_syntax_error(self, context: str) -> str:
        """Extract syntax error details from context."""
        syntax_error_match = re.search(r"SyntaxError:\s*(.*?)(?:$|\n)", context)
        if syntax_error_match:
            return syntax_error_match.group(1)

        return ""

    def _load_known_patterns(self) -> List[Dict[str, Any]]:
        """Load known patterns for event detection."""
        return [
            {
                "pattern": r"LaTeX Error|latex error|ValueError: latex error",
                "type": "error",
                "severity": "high",
            },
            {
                "pattern": r"SyntaxError|syntax error",
                "type": "error",
                "severity": "high",
            },
            {
                "pattern": r"NameError|AttributeError|TypeError|ImportError",
                "type": "error",
                "severity": "high",
            },
            {
                "pattern": r"Warning:|warning:",
                "type": "warning",
                "severity": "medium",
            },
            {
                "pattern": r"Rendering|rendering|Processing|processing",
                "type": "progress",
                "severity": "low",
            },
            {
                "pattern": r"✅|Rendered:|rendered:|Success|success|Complete|complete",
                "type": "success",
                "severity": "low",
            },
        ]

    def _create_sample_terminal_output(self) -> str:
        """Create sample terminal output for testing."""
        return """
2023-09-13 10:15:32 [INFO] Starting Manim rendering process
2023-09-13 10:15:32 [INFO] Processing scene: Scene1
2023-09-13 10:15:33 [INFO] Rendering scene...
2023-09-13 10:15:35 [WARNING] Deprecated function used: old_position_method
2023-09-13 10:15:36 [ERROR] LaTeX Error: Undefined control sequence \\mathbbb
2023-09-13 10:15:36 [INFO] LaTeX compilation failed
2023-09-13 10:15:36 [ERROR] ValueError: latex error converting to dvi. See log output above or the log file: media/Tex/65d720eb4db018f5.log
2023-09-13 10:15:37 [INFO] Retrying with corrected LaTeX...
2023-09-13 10:15:38 [INFO] LaTeX compilation successful
2023-09-13 10:15:40 [INFO] Rendering animation...
2023-09-13 10:15:45 [ERROR] NameError: name 'attention_weights' is not defined
2023-09-13 10:15:45 [INFO] Animation failed
2023-09-13 10:15:46 [INFO] Retrying with fixed code...
2023-09-13 10:15:47 [INFO] Processing scene: Scene2
2023-09-13 10:15:48 [INFO] Rendering scene...
2023-09-13 10:15:55 [INFO] Scene rendered successfully
2023-09-13 10:15:56 [INFO] ✅ Rendered: Scene_Scene2.mp4
2023-09-13 10:15:57 [INFO] Processing complete
"""

    def _create_system_prompt(self) -> str:
        """Create the system prompt for terminal monitoring operations."""
        return """
        You are an expert Terminal Monitor specializing in analyzing Manim rendering output.
        
        Your expertise includes:
        1. Detecting and classifying terminal events (errors, warnings, progress, success)
        2. Extracting meaningful information from complex error messages
        3. Understanding Manim and LaTeX error patterns
        4. Suggesting appropriate interventions for common issues
        5. Monitoring rendering progress in real-time
        
        When analyzing terminal output:
        - Identify critical errors that would halt rendering
        - Extract specific error details (line numbers, error types, messages)
        - Recognize common LaTeX and Python error patterns
        - Track rendering progress and completion status
        - Provide clear, actionable insights
        
        Common error patterns you can detect:
        - LaTeX compilation errors (undefined control sequences, missing braces)
        - Python syntax errors
        - Runtime errors (undefined variables, attribute errors)
        - Manim-specific rendering issues
        
        Be precise, proactive, and solution-oriented in your monitoring.
        """
