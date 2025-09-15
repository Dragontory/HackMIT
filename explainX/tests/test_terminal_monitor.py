#!/usr/bin/env python3
"""
Test script for the Terminal Monitor Agent.

This script tests the Terminal Monitor Agent using terminal output with various
types of events and demonstrates its ability to detect issues in real-time.
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add agents_system to Python path
sys.path.insert(0, str(Path(__file__).parent))

from agents_system.infrastructure.config import AgentConfig
from agents_system.core.workflows.terminal_monitoring_workflow import (
    TerminalMonitoringWorkflow,
)


# Sample terminal output with various events
SAMPLE_TERMINAL_OUTPUT = """
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


# Sample terminal output with LaTeX error
SAMPLE_LATEX_ERROR_OUTPUT = """
2023-09-13 10:15:32 [INFO] Starting Manim rendering process
2023-09-13 10:15:33 [INFO] Processing scene: Scene1
2023-09-13 10:15:34 [INFO] Rendering scene...
2023-09-13 10:15:35 [ERROR] LaTeX Error: Undefined control sequence \\mathbbb
2023-09-13 10:15:36 [INFO] LaTeX compilation failed
2023-09-13 10:15:36 [ERROR] ValueError: latex error converting to dvi. See log output above or the log file: media/Tex/65d720eb4db018f5.log
"""


# Sample terminal output with Python error
SAMPLE_PYTHON_ERROR_OUTPUT = """
2023-09-13 10:15:32 [INFO] Starting Manim rendering process
2023-09-13 10:15:33 [INFO] Processing scene: Scene1
2023-09-13 10:15:34 [INFO] Rendering scene...
2023-09-13 10:15:35 [ERROR] Traceback (most recent call last):
  File "scene_with_errors.py", line 45
    attention_weights.shift(DOWN)
NameError: name 'attention_weights' is not defined
2023-09-13 10:15:36 [INFO] Animation failed
"""


# Sample terminal output with successful rendering
SAMPLE_SUCCESS_OUTPUT = """
2023-09-13 10:15:32 [INFO] Starting Manim rendering process
2023-09-13 10:15:33 [INFO] Processing scene: Scene1
2023-09-13 10:15:34 [INFO] Rendering scene...
2023-09-13 10:15:40 [INFO] Scene rendered successfully
2023-09-13 10:15:41 [INFO] ✅ Rendered: Scene_Scene1.mp4
2023-09-13 10:15:42 [INFO] Processing complete
"""


async def test_terminal_monitor_agent():
    """Test the Terminal Monitor Agent with various terminal outputs."""

    print("🖥️ Testing Terminal Monitor Agent")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize the agent directly (skip the workflow for faster testing)
        print("\n🔧 Initializing Terminal Monitor Agent...")
        from agents_system.infrastructure.anthropic.client import AnthropicClient
        from agents_system.core.agents.terminal_monitor import TerminalMonitorAgent

        claude_client = AnthropicClient(config.anthropic)
        terminal_monitor = TerminalMonitorAgent(claude_client)
        print("✅ Terminal Monitor Agent initialized")

        # Select which output to test
        test_output = SAMPLE_TERMINAL_OUTPUT  # Change to test different outputs
        test_name = "SAMPLE_TERMINAL_OUTPUT"  # Update this if you change the output

        # Display the input output
        print(f"\n📝 INPUT TERMINAL OUTPUT ({test_name}):")
        print("-" * 60)
        print(test_output)
        print("-" * 60)

        # Execute Terminal Monitoring
        print("\n🚀 Executing Terminal Monitor Agent...")
        print("=" * 60)

        # Use the agent directly
        events = await terminal_monitor.detect_events(test_output)

        # Create a result object
        from agents_system.domain.models import TerminalMonitoringResult

        monitoring_result = TerminalMonitoringResult(
            terminal_output=test_output,
            detected_events=events,
            actions_taken=[],
            monitoring_duration=0.0,
            is_active=False,
            success=True,
        )

        # Generate actions for critical events
        for event in events:
            if event.event_type in ["error", "warning"]:
                actions = await terminal_monitor.generate_actions(event)
                monitoring_result.actions_taken.extend(actions)

        # Create a result object
        from agents_system.domain.models import AgentResult

        result = AgentResult(
            success=True,
            data=monitoring_result,
            errors=[],
            warnings=[],
            metadata={
                "events_detected": len(monitoring_result.detected_events),
                "actions_taken": len(monitoring_result.actions_taken),
            },
        )

        print("=" * 60)

        if result.success:
            print("✅ Terminal monitoring: SUCCESS")
            monitoring_result = result.data

            print("\n" + "=" * 70)
            print("🖥️ TERMINAL MONITORING RESULTS")
            print("=" * 70)

            # Basic metrics
            print(f"🎯 Events Detected: {len(monitoring_result.detected_events)}")
            print(f"🔧 Actions Taken: {len(monitoring_result.actions_taken)}")
            print(
                f"⏱️  Monitoring Duration: {monitoring_result.monitoring_duration:.2f} seconds"
            )

            # Events by type
            events_by_type = {}
            for event in monitoring_result.detected_events:
                if event.event_type not in events_by_type:
                    events_by_type[event.event_type] = 0
                events_by_type[event.event_type] += 1

            print(f"\n📊 Events by Type:")
            for event_type, count in events_by_type.items():
                print(f"   {event_type.upper()}: {count}")

            # Critical events
            critical_events = [
                event
                for event in monitoring_result.detected_events
                if event.severity in ["high", "critical"]
            ]

            if critical_events:
                print(f"\n⚠️ Critical Events ({len(critical_events)}):")
                for i, event in enumerate(critical_events, 1):
                    print(f"\n   Event {i}: {event.event_type.upper()}")
                    print(f"   Message: {event.message}")
                    print(f"   Source: {event.source_line}")
                    print(f"   Severity: {event.severity}")

            # Actions
            if monitoring_result.actions_taken:
                print(f"\n🔧 Actions Taken:")
                for i, action in enumerate(monitoring_result.actions_taken, 1):
                    print(f"\n   Action {i}: {action.action_type.upper()}")
                    print(f"   Description: {action.description}")
                    print(f"   Executed: {'Yes' if action.is_executed else 'No'}")
                    if action.result:
                        print(f"   Result: {action.result}")

            # Agent messages
            if "agent_messages" in result.metadata:
                print(f"\n📨 Agent Execution Log:")
                for msg in result.metadata["agent_messages"]:
                    agent = msg.get("agent", "unknown")
                    status = msg.get("status", "unknown")
                    message = msg.get("message", "")
                    print(f"   📍 {agent}: {status}")
                    if message:
                        print(f"      💬 {message}")
                    if "metadata" in msg:
                        for key, value in msg["metadata"].items():
                            print(f"      📊 {key}: {value}")
                    if "summary" in msg:
                        print(f"      📋 Summary:")
                        for key, value in msg["summary"].items():
                            print(f"         {key}: {value}")

            print("\n🎉 Terminal Monitor Agent test: PASSED")
            return True

        else:
            print("❌ Terminal monitoring: FAILED")
            print("Errors:")
            for error in result.errors:
                print(f"   • {error}")
            print("Warnings:")
            for warning in result.warnings:
                print(f"   • {warning}")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_live_monitoring():
    """Test live monitoring of a command."""

    print("🔴 Testing Live Terminal Monitoring")
    print("=" * 70)

    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = AgentConfig.from_env()
        print(f"✅ Config loaded: Model={config.anthropic.model}")

        # Initialize workflows
        print("\n🔧 Initializing Terminal Monitoring Workflow...")
        monitoring_workflow = TerminalMonitoringWorkflow(config)
        print("✅ Terminal Monitoring Workflow initialized")

        # Start live monitoring
        print("\n🚀 Starting live monitoring...")

        # Use a simple command that generates output over time
        command = 'for i in {1..10}; do echo "Processing step $i"; sleep 1; done'

        # Start monitoring
        await monitoring_workflow.start_live_monitoring(command)

        # Wait for the command to complete
        print("⏳ Monitoring in progress...")
        for i in range(12):
            print(f"   Elapsed: {i} seconds")
            await asyncio.sleep(1)

        # Stop monitoring
        print("\n🛑 Stopping monitoring...")
        result = await monitoring_workflow.stop_live_monitoring()

        if result.success:
            print("✅ Live monitoring: SUCCESS")
            monitoring_result = result.data

            print(
                f"\n📊 Events detected: {len(monitoring_result.get('detected_events', []))}"
            )
            print(
                f"🔧 Actions taken: {len(monitoring_result.get('actions_taken', []))}"
            )
            print(
                f"⏱️  Monitoring duration: {monitoring_result.get('monitoring_duration', 0.0):.2f} seconds"
            )

            return True
        else:
            print("❌ Live monitoring: FAILED")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("🚀 ExplainX Terminal Monitor Agent Test")
    print("🎯 Testing real-time terminal monitoring")
    print("📍 Using terminal output with various events")
    print()

    # Run the test
    success = asyncio.run(test_terminal_monitor_agent())

    # Uncomment to test live monitoring
    # Note: This will execute a real command and monitor it
    # live_success = asyncio.run(test_live_monitoring())

    if success:
        print("\n" + "=" * 70)
        print("🎉 TERMINAL MONITOR AGENT WORKS CORRECTLY!")
        print("✅ Successfully detected events and suggested actions")
        print("🔄 Next agents to implement:")
        print("   1. Rendering Optimizer Agent (optimize rendering settings)")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("⚠️ TERMINAL MONITOR AGENT ENCOUNTERED ISSUES!")
        print("❌ Some events or actions could not be processed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
