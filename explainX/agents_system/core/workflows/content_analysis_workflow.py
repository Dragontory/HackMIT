"""
LangGraph workflow for content analysis using the Content Strategist Agent.
"""

import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...domain.models import AgentState, AgentResult
from ...infrastructure.config import AgentConfig
from ...infrastructure.anthropic.client import AnthropicClient
from ..agents.content_strategist import ContentStrategistAgent


logger = logging.getLogger(__name__)


class ContentAnalysisWorkflow:
    """
    LangGraph workflow for analyzing educational content.

    This workflow orchestrates the Content Strategist Agent to:
    1. Analyze input content
    2. Create learning strategies
    3. Generate recommendations for downstream agents
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.claude_client = AnthropicClient(config.anthropic)
        self.content_strategist = ContentStrategistAgent(self.claude_client)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""

        # Define the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes (agents)
        workflow.add_node("content_strategist", self._content_strategist_node)
        workflow.add_node("validate_strategy", self._validate_strategy_node)
        workflow.add_node("finalize_results", self._finalize_results_node)

        # Define the flow
        workflow.set_entry_point("content_strategist")

        workflow.add_edge("content_strategist", "validate_strategy")
        workflow.add_conditional_edges(
            "validate_strategy",
            self._should_retry_analysis,
            {"retry": "content_strategist", "continue": "finalize_results"},
        )
        workflow.add_edge("finalize_results", END)

        # Add memory for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def _content_strategist_node(self, state: AgentState) -> AgentState:
        """Execute the Content Strategist Agent."""
        logger.info("Executing Content Strategist Agent")

        try:
            # Process content with the strategist
            result = await self.content_strategist.process(state)

            if result.success:
                logger.info("Content strategy created successfully")
                state["agent_messages"].append(
                    {
                        "agent": "content_strategist",
                        "status": "success",
                        "metadata": result.metadata,
                    }
                )
            else:
                logger.error(f"Content strategist failed: {result.errors}")
                state["errors"].extend(result.errors)

        except Exception as e:
            logger.error(f"Content strategist node error: {e}")
            state["errors"].append(f"Content strategist execution failed: {str(e)}")

        return state

    async def _validate_strategy_node(self, state: AgentState) -> AgentState:
        """Validate the generated content strategy."""
        logger.info("Validating content strategy")

        if state["content_strategy"] is None:
            state["errors"].append("No content strategy generated")
            state["processing_stage"] = "validation_failed"
            return state

        strategy = state["content_strategy"]

        # Validation checks
        validation_errors = []

        if not strategy.learning_objectives:
            validation_errors.append("No learning objectives defined")

        if not strategy.content_chunks:
            validation_errors.append("No content chunks created")

        if strategy.recommended_scene_count < 1:
            validation_errors.append("Invalid scene count recommendation")

        if strategy.cognitive_load_assessment not in ["low", "moderate", "high"]:
            validation_errors.append("Invalid cognitive load assessment")

        # Add validation results
        if validation_errors:
            state["errors"].extend(validation_errors)
            state["processing_stage"] = "validation_failed"
            logger.warning(f"Strategy validation failed: {validation_errors}")
        else:
            state["processing_stage"] = "validation_passed"
            logger.info("Content strategy validation passed")

            # Add validation success message
            state["agent_messages"].append(
                {
                    "agent": "validator",
                    "status": "success",
                    "message": "Content strategy validated successfully",
                    "metadata": {
                        "learning_objectives": len(strategy.learning_objectives),
                        "content_chunks": len(strategy.content_chunks),
                        "recommended_scenes": strategy.recommended_scene_count,
                        "cognitive_load": strategy.cognitive_load_assessment,
                    },
                }
            )

        return state

    async def _finalize_results_node(self, state: AgentState) -> AgentState:
        """Finalize the workflow results."""
        logger.info("Finalizing content analysis results")

        state["processing_stage"] = "completed"
        state["current_agent"] = "workflow_complete"

        # Add final summary
        if state["content_strategy"]:
            strategy = state["content_strategy"]
            state["agent_messages"].append(
                {
                    "agent": "workflow_summary",
                    "status": "completed",
                    "summary": {
                        "total_learning_objectives": len(strategy.learning_objectives),
                        "total_content_chunks": len(strategy.content_chunks),
                        "recommended_scenes": strategy.recommended_scene_count,
                        "estimated_duration": strategy.total_estimated_time,
                        "cognitive_load": strategy.cognitive_load_assessment,
                        "mathematical_density": strategy.mathematical_density,
                        "visualization_opportunities": len(
                            strategy.visual_opportunities
                        ),
                        "animation_recommendations": len(
                            strategy.animation_recommendations
                        ),
                    },
                }
            )

        logger.info("Content analysis workflow completed")
        return state

    def _should_retry_analysis(self, state: AgentState) -> str:
        """Determine if analysis should be retried."""

        # Check for critical errors that warrant retry
        critical_errors = ["API timeout", "Connection failed", "Authentication error"]

        has_critical_error = any(
            any(critical in error for critical in critical_errors)
            for error in state["errors"]
        )

        # Don't retry more than once
        retry_count = sum(
            1
            for msg in state["agent_messages"]
            if msg.get("agent") == "content_strategist"
        )

        if has_critical_error and retry_count < 2:
            logger.info("Retrying content analysis due to critical error")
            return "retry"
        else:
            return "continue"

    async def analyze_content(self, content: str, title: str) -> AgentResult:
        """
        Analyze content using the complete workflow.

        Args:
            content: Raw content to analyze
            title: Content title/topic

        Returns:
            AgentResult: Complete analysis results
        """
        logger.info(f"Starting content analysis workflow for: {title}")

        # Initialize state
        initial_state = {
            "raw_content": content,
            "content_title": title,
            "content_strategy": None,
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
                    "configurable": {"thread_id": f"content_analysis_{hash(title)}"}
                },
            )

            # Determine success
            success = (
                final_state["processing_stage"] == "completed"
                and final_state["content_strategy"] is not None
                and not final_state["errors"]
            )

            return AgentResult(
                success=success,
                data=final_state["content_strategy"],
                errors=final_state["errors"],
                warnings=final_state["warnings"],
                metadata={
                    "workflow_state": final_state["processing_stage"],
                    "agent_messages": final_state["agent_messages"],
                    "total_processing_steps": len(final_state["agent_messages"]),
                },
            )

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Workflow execution failed: {str(e)}"],
            )
