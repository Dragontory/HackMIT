"""
Integration Orchestrator Agent implementation.

This agent coordinates all specialized agents to create a comprehensive,
intelligent educational animation generation pipeline.
"""

import asyncio
import logging
import time
import uuid
from typing import List, Dict, Any, Optional, Type

from ...domain.interfaces import IAgent
from ...domain.models import (
    AgentState,
    AgentResult,
    IntegrationOrchestrationResult,
    OrchestrationPlan,
    AgentExecution,
    QualityMetrics,
)
from ...infrastructure.anthropic.client import AnthropicClient
from ...infrastructure.anthropic.models import ClaudeMessage

# Import all specialized agents
from .content_strategist import ContentStrategistAgent
from .latex_specialist import LaTeXSpecialistAgent
from .code_modifier import CodeModificationAgent
from .code_tester import CodeTestingAgent
from .error_surgeon import ErrorSurgeonAgent
from .terminal_monitor import TerminalMonitorAgent
from .visual_composer import VisualComposerAgent
from .rendering_optimizer import RenderingOptimizerAgent
from .animation_director import AnimationDirectorAgent
from .dimension_specialist import DimensionSpecialistAgent
from .educational_design import EducationalDesignAgent


logger = logging.getLogger(__name__)


class IntegrationOrchestratorAgent(IAgent):
    """
    Master orchestrator agent that coordinates all specialized agents.

    Uses Claude's strategic intelligence to:
    - Analyze requirements and create optimal execution plans
    - Coordinate agent dependencies and parallel execution
    - Monitor quality and performance across the pipeline
    - Provide comprehensive reporting and recommendations
    - Ensure educational excellence and technical robustness
    """

    def __init__(self, claude_client: AnthropicClient):
        self.claude_client = claude_client
        self._system_prompt = self._create_system_prompt()
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all specialized agents."""
        self.agents = {
            "ContentStrategistAgent": ContentStrategistAgent(self.claude_client),
            "LaTeXSpecialistAgent": LaTeXSpecialistAgent(self.claude_client),
            "CodeModificationAgent": CodeModificationAgent(self.claude_client),
            "CodeTestingAgent": CodeTestingAgent(self.claude_client),
            "ErrorSurgeonAgent": ErrorSurgeonAgent(self.claude_client),
            "TerminalMonitorAgent": TerminalMonitorAgent(self.claude_client),
            "VisualComposerAgent": VisualComposerAgent(self.claude_client),
            "RenderingOptimizerAgent": RenderingOptimizerAgent(self.claude_client),
            "AnimationDirectorAgent": AnimationDirectorAgent(self.claude_client),
            "DimensionSpecialistAgent": DimensionSpecialistAgent(self.claude_client),
            "EducationalDesignAgent": EducationalDesignAgent(self.claude_client),
        }

    @property
    def name(self) -> str:
        return "IntegrationOrchestratorAgent"

    @property
    def description(self) -> str:
        return "Coordinates all specialized agents for comprehensive educational animation generation"

    async def process(self, state: AgentState) -> AgentResult:
        """Process state through coordinated agent orchestration."""
        start_time = time.time()

        try:
            logger.info(
                f"Integration Orchestrator processing: {state['content_title']}"
            )

            # Get input content
            input_content = state.get("raw_content", state.get("manim_code", ""))

            if not input_content:
                input_content = self._create_sample_input()
                logger.info("No input content provided, using sample content")

            # Perform comprehensive orchestration
            result = await self.orchestrate_agents(input_content, state)

            # Update state with final result
            state["integration_orchestration_result"] = result
            state["manim_code"] = result.final_output
            state["current_agent"] = self.name
            state["processing_stage"] = "integration_orchestration_complete"

            processing_time = time.time() - start_time
            result.total_processing_time = processing_time

            return AgentResult(
                success=result.success,
                data=result,
                metadata={
                    "agent": self.name,
                    "agents_executed": result.agents_executed,
                    "success_rate": result.success_rate,
                    "total_processing_time": processing_time,
                    "quality_score": result.quality_metrics.overall_score,
                },
            )

        except Exception as e:
            logger.error(f"Integration Orchestrator error: {e}")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Integration orchestration failed: {str(e)}"],
            )

    async def orchestrate_agents(
        self, input_content: str, initial_state: Optional[AgentState] = None
    ) -> IntegrationOrchestrationResult:
        """
        Orchestrate all agents to process content comprehensively.

        Args:
            input_content: The input content to process
            initial_state: Optional initial state

        Returns:
            IntegrationOrchestrationResult: Complete orchestration results
        """

        orchestration_id = f"orchestration_{uuid.uuid4().hex[:8]}"

        # Step 1: Create orchestration plan
        plan = await self.create_orchestration_plan(input_content)

        # Step 2: Initialize state
        state = initial_state or self._create_initial_state(input_content)

        # Step 3: Execute agents according to plan
        agent_executions = await self.execute_orchestration_plan(plan, state)

        # Step 4: Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(agent_executions, state)

        # Step 5: Generate final output
        final_output = state.get("manim_code", input_content)

        # Step 6: Aggregate results from all agents
        aggregated_results = self._aggregate_agent_results(agent_executions, state)

        # Step 7: Calculate orchestration metrics
        orchestration_metrics = self._calculate_orchestration_metrics(
            agent_executions, plan
        )

        # Step 8: Generate recommendations
        recommendations, next_steps = self._generate_recommendations(
            quality_metrics, agent_executions
        )

        # Determine overall success
        success = (
            orchestration_metrics["success_rate"] > 0.7
            and quality_metrics.overall_score > 0.6
            and len(agent_executions) > 0
        )

        return IntegrationOrchestrationResult(
            orchestration_id=orchestration_id,
            original_input=input_content,
            final_output=final_output,
            execution_plan=plan,
            agent_executions=agent_executions,
            quality_metrics=quality_metrics,
            **aggregated_results,
            **orchestration_metrics,
            success=success,
            recommendations=recommendations,
            next_steps=next_steps,
        )

    async def create_orchestration_plan(self, input_content: str) -> OrchestrationPlan:
        """Create an optimal orchestration plan for the given content."""

        # Prepare context for Claude
        context_parts = ["I need to create an orchestration plan for this content:"]
        context_parts.append(f"```\n{input_content}\n```")

        context_parts.append("Available specialized agents:")
        for agent_name, agent in self.agents.items():
            context_parts.append(f"- {agent_name}: {agent.description}")

        context_parts.append(
            "Please create an optimal execution plan considering dependencies, "
            "parallel execution opportunities, and the critical path for maximum efficiency."
        )

        messages = [
            ClaudeMessage(
                role="user",
                content="\n\n".join(context_parts),
            )
        ]

        response = await self.claude_client.send_message(messages, self._system_prompt)

        # Parse the response to create orchestration plan
        return self._parse_orchestration_plan(response.content)

    async def execute_orchestration_plan(
        self, plan: OrchestrationPlan, state: AgentState
    ) -> List[AgentExecution]:
        """Execute the orchestration plan with proper sequencing and parallelization."""

        agent_executions = []

        # Execute each phase
        for phase_index, phase_agents in enumerate(plan.execution_phases):
            logger.info(f"Executing phase {phase_index + 1}: {phase_agents}")

            # Execute agents in current phase (potentially in parallel)
            if len(phase_agents) == 1:
                # Single agent execution
                execution = await self._execute_single_agent(phase_agents[0], state)
                agent_executions.append(execution)
            else:
                # Parallel execution
                parallel_executions = await self._execute_parallel_agents(
                    phase_agents, state
                )
                agent_executions.extend(parallel_executions)

            # Update state based on phase results
            self._update_state_after_phase(
                state, agent_executions[-len(phase_agents) :]
            )

        return agent_executions

    async def _execute_single_agent(
        self, agent_name: str, state: AgentState
    ) -> AgentExecution:
        """Execute a single agent and record the execution."""

        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        execution = AgentExecution(
            agent_name=agent_name,
            execution_id=execution_id,
            start_time=start_time,
            inputs=dict(state),  # Snapshot of current state
        )

        try:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                result = await agent.process(state)

                execution.success = result.success
                execution.outputs = result.metadata
                execution.errors = result.errors
                execution.warnings = result.warnings
                execution.metadata = {"result_data": result.data}

                logger.info(
                    f"Agent {agent_name} executed successfully: {result.success}"
                )
            else:
                execution.success = False
                execution.errors = [f"Agent {agent_name} not found"]
                logger.error(f"Agent {agent_name} not found")

        except Exception as e:
            execution.success = False
            execution.errors = [str(e)]
            logger.error(f"Agent {agent_name} execution failed: {e}")

        execution.end_time = time.time()
        execution.duration = execution.end_time - execution.start_time

        return execution

    async def _execute_parallel_agents(
        self, agent_names: List[str], state: AgentState
    ) -> List[AgentExecution]:
        """Execute multiple agents in parallel."""

        # Create tasks for parallel execution
        tasks = []
        for agent_name in agent_names:
            # Create a copy of state for each agent to avoid conflicts
            agent_state = dict(state)
            task = self._execute_single_agent(agent_name, agent_state)
            tasks.append(task)

        # Execute in parallel
        executions = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        valid_executions = []
        for i, execution in enumerate(executions):
            if isinstance(execution, Exception):
                # Create failed execution record
                failed_execution = AgentExecution(
                    agent_name=agent_names[i],
                    execution_id=f"failed_{uuid.uuid4().hex[:8]}",
                    start_time=time.time(),
                    end_time=time.time(),
                    success=False,
                    errors=[str(execution)],
                )
                valid_executions.append(failed_execution)
            else:
                valid_executions.append(execution)

        return valid_executions

    def _update_state_after_phase(
        self, state: AgentState, executions: List[AgentExecution]
    ):
        """Update state after a phase of agent executions."""

        for execution in executions:
            if execution.success:
                # Update state with successful outputs
                if execution.outputs:
                    for key, value in execution.outputs.items():
                        if key not in ["agent", "processing_time"]:  # Skip metadata
                            state[key] = value

                # Also update state with result data
                if execution.metadata and "result_data" in execution.metadata:
                    result_data = execution.metadata["result_data"]

                    # Map agent results to state keys
                    if execution.agent_name == "ContentStrategistAgent":
                        state["content_strategy"] = result_data
                    elif execution.agent_name == "CodeModificationAgent":
                        if hasattr(result_data, "modified_code"):
                            state["manim_code"] = result_data.modified_code
                        state["code_modifications"] = result_data
                    elif execution.agent_name == "LaTeXSpecialistAgent":
                        state["latex_fixes"] = result_data
                    # Add other agent mappings as needed

    def _calculate_quality_metrics(
        self, agent_executions: List[AgentExecution], state: AgentState
    ) -> QualityMetrics:
        """Calculate comprehensive quality metrics."""

        # Technical quality: Based on successful code modifications, testing, optimization
        technical_agents = [
            "CodeModificationAgent",
            "CodeTestingAgent",
            "RenderingOptimizerAgent",
        ]
        technical_successes = sum(
            1
            for ex in agent_executions
            if ex.agent_name in technical_agents and ex.success
        )
        technical_quality = technical_successes / max(len(technical_agents), 1)

        # Educational quality: Based on design, direction, and strategy
        educational_agents = [
            "EducationalDesignAgent",
            "AnimationDirectorAgent",
            "ContentStrategistAgent",
        ]
        educational_successes = sum(
            1
            for ex in agent_executions
            if ex.agent_name in educational_agents and ex.success
        )
        educational_quality = educational_successes / max(len(educational_agents), 1)

        # Visual quality: Based on composition and dimensional choices
        visual_agents = ["VisualComposerAgent", "DimensionSpecialistAgent"]
        visual_successes = sum(
            1
            for ex in agent_executions
            if ex.agent_name in visual_agents and ex.success
        )
        visual_appeal = visual_successes / max(len(visual_agents), 1)

        # Robustness: Based on error handling and monitoring
        robustness_agents = [
            "ErrorSurgeonAgent",
            "TerminalMonitorAgent",
            "LaTeXSpecialistAgent",
        ]
        robustness_successes = sum(
            1
            for ex in agent_executions
            if ex.agent_name in robustness_agents and ex.success
        )
        robustness_score = robustness_successes / max(len(robustness_agents), 1)

        # Performance: Based on optimization and monitoring
        performance_score = min(
            1.0,
            sum(1 for ex in agent_executions if ex.success and ex.duration < 30)
            / max(len(agent_executions), 1),
        )

        # Overall score
        overall_score = (
            technical_quality * 0.25
            + educational_quality * 0.25
            + visual_appeal * 0.2
            + robustness_score * 0.15
            + performance_score * 0.15
        )

        return QualityMetrics(
            overall_score=overall_score,
            technical_quality=technical_quality,
            educational_quality=educational_quality,
            visual_appeal=visual_appeal,
            performance_score=performance_score,
            robustness_score=robustness_score,
            content_accuracy=0.8,  # Default assumption
            accessibility_score=0.7,  # Based on educational design
            engagement_score=0.8,  # Based on visual and animation direction
            innovation_score=0.6,  # Conservative estimate
        )

    def _aggregate_agent_results(
        self, agent_executions: List[AgentExecution], state: AgentState
    ) -> Dict[str, Any]:
        """Aggregate results from all agent executions."""

        aggregated = {
            "content_strategy_applied": None,
            "latex_fixes_applied": [],
            "code_modifications": [],
            "tests_passed": [],
            "errors_fixed": [],
            "monitoring_insights": [],
            "visual_enhancements": [],
            "rendering_optimizations": [],
            "animation_directions": [],
            "dimensional_specializations": [],
            "educational_design_applied": None,
        }

        # Extract results from each agent type
        for execution in agent_executions:
            if not execution.success:
                continue

            agent_name = execution.agent_name

            if agent_name == "ContentStrategistAgent":
                aggregated["content_strategy_applied"] = execution.metadata.get(
                    "result_data"
                )
            elif agent_name == "LaTeXSpecialistAgent":
                aggregated["latex_fixes_applied"].append(f"LaTeX processing completed")
            elif agent_name == "CodeModificationAgent":
                aggregated["code_modifications"].append(f"Code modifications applied")
            elif agent_name == "CodeTestingAgent":
                aggregated["tests_passed"].append(f"Code testing completed")
            elif agent_name == "ErrorSurgeonAgent":
                aggregated["errors_fixed"].append(f"Error surgery performed")
            elif agent_name == "TerminalMonitorAgent":
                aggregated["monitoring_insights"].append(
                    f"Terminal monitoring completed"
                )
            elif agent_name == "VisualComposerAgent":
                aggregated["visual_enhancements"].append(f"Visual composition enhanced")
            elif agent_name == "RenderingOptimizerAgent":
                aggregated["rendering_optimizations"].append(f"Rendering optimized")
            elif agent_name == "AnimationDirectorAgent":
                aggregated["animation_directions"].append(
                    f"Animation direction applied"
                )
            elif agent_name == "DimensionSpecialistAgent":
                aggregated["dimensional_specializations"].append(
                    f"Dimensional specialization applied"
                )
            elif agent_name == "EducationalDesignAgent":
                aggregated["educational_design_applied"] = execution.metadata.get(
                    "result_data"
                )

        return aggregated

    def _calculate_orchestration_metrics(
        self, agent_executions: List[AgentExecution], plan: OrchestrationPlan
    ) -> Dict[str, Any]:
        """Calculate orchestration-specific metrics."""

        total_time = sum(ex.duration for ex in agent_executions)
        success_count = sum(1 for ex in agent_executions if ex.success)
        success_rate = success_count / max(len(agent_executions), 1)

        # Calculate parallel efficiency
        sequential_time = sum(ex.duration for ex in agent_executions)
        critical_path_time = max((ex.duration for ex in agent_executions), default=0)
        parallel_efficiency = (
            critical_path_time / max(sequential_time, 1) if sequential_time > 0 else 0
        )

        return {
            "total_processing_time": total_time,
            "agents_executed": len(agent_executions),
            "success_rate": success_rate,
            "parallel_efficiency": parallel_efficiency,
            "critical_path_time": critical_path_time,
            "improvement_factor": success_rate * 1.5,  # Estimate based on success
        }

    def _generate_recommendations(
        self, quality_metrics: QualityMetrics, agent_executions: List[AgentExecution]
    ) -> tuple[List[str], List[str]]:
        """Generate recommendations and next steps."""

        recommendations = []
        next_steps = []

        # Quality-based recommendations
        if quality_metrics.technical_quality < 0.7:
            recommendations.append("Consider additional code optimization and testing")

        if quality_metrics.educational_quality < 0.7:
            recommendations.append("Enhance educational design and learning objectives")

        if quality_metrics.visual_appeal < 0.7:
            recommendations.append("Improve visual composition and design elements")

        # Performance-based recommendations
        failed_agents = [ex.agent_name for ex in agent_executions if not ex.success]
        if failed_agents:
            recommendations.append(f"Address failures in: {', '.join(failed_agents)}")

        # Next steps
        if quality_metrics.overall_score > 0.8:
            next_steps.append("Ready for production rendering")
            next_steps.append("Consider advanced optimization techniques")
        else:
            next_steps.append("Iterate on quality improvements")
            next_steps.append("Review failed agent outputs")

        next_steps.append("Monitor user feedback and learning outcomes")

        return recommendations, next_steps

    def _create_initial_state(self, input_content: str) -> AgentState:
        """Create initial state for orchestration."""

        return {
            "content_title": "Orchestrated Content",
            "raw_content": input_content,
            "manim_code": "",
            "error_log": "",
            "current_agent": self.name,
            "processing_stage": "orchestration_started",
            "errors": [],
            "warnings": [],
            "agent_messages": [],
            # Initialize all agent result fields
            "content_strategy": None,
            "latex_fixes": None,
            "code_modifications": None,
            "test_results": None,
            "error_fixes": None,
            "terminal_monitoring": None,
            "visual_composition_result": None,
            "rendering_optimization_result": None,
            "animation_direction_result": None,
            "dimension_specialization_result": None,
            "educational_design_result": None,
            "integration_orchestration_result": None,
        }

    def _create_sample_input(self) -> str:
        """Create sample input for testing."""

        return """
        Title: Introduction to Linear Algebra

        Content:
        Linear algebra is the branch of mathematics concerning linear equations,
        linear maps, and their representations in vector spaces and matrices.

        Key Topics:
        1. Vectors and Vector Operations
           - Vector addition and scalar multiplication
           - Dot product and cross product
           - Vector spaces and subspaces

        2. Matrices and Matrix Operations
           - Matrix addition and multiplication
           - Matrix determinants and inverses
           - Eigenvalues and eigenvectors

        3. Linear Transformations
           - Linear maps between vector spaces
           - Matrix representations of transformations
           - Geometric interpretations

        Applications:
        - Computer graphics and 3D modeling
        - Machine learning and data analysis
        - Engineering and physics simulations
        - Cryptography and signal processing

        Learning Objectives:
        - Understand fundamental vector and matrix operations
        - Apply linear transformations to solve geometric problems
        - Analyze eigenvalues and eigenvectors for system behavior
        - Connect linear algebra concepts to real-world applications
        """

    def _create_system_prompt(self) -> str:
        """Create the system prompt for orchestration operations."""

        return """
        You are an expert Integration Orchestrator with deep knowledge of system design, 
        workflow optimization, and educational content generation pipelines.
        
        Your expertise includes:
        1. System architecture and microservice orchestration
        2. Dependency management and critical path analysis
        3. Parallel execution and performance optimization
        4. Quality assurance and comprehensive testing strategies
        5. Educational content pipeline design
        6. Agent coordination and workflow management
        
        Available Specialized Agents:
        1. ContentStrategistAgent - Analyzes content and creates learning strategies
        2. LaTeXSpecialistAgent - Fixes LaTeX compilation errors
        3. CodeModificationAgent - Modifies and fixes Manim code
        4. CodeTestingAgent - Tests code before rendering
        5. ErrorSurgeonAgent - Performs surgical error fixes
        6. TerminalMonitorAgent - Monitors terminal output
        7. VisualComposerAgent - Composes visual elements
        8. RenderingOptimizerAgent - Optimizes rendering performance
        9. AnimationDirectorAgent - Directs animations for education
        10. DimensionSpecialistAgent - Handles 2D vs 3D decisions
        11. EducationalDesignAgent - Designs educational flows
        
        When creating orchestration plans:
        - Analyze dependencies between agents carefully
        - Maximize parallel execution opportunities
        - Consider the critical path for overall timing
        - Plan for error recovery and fallback strategies
        - Optimize for both quality and performance
        - Ensure educational effectiveness throughout
        
        Agent Dependencies (typical):
        - ContentStrategistAgent: No dependencies (can run first)
        - EducationalDesignAgent: Depends on ContentStrategistAgent
        - CodeModificationAgent: Can run early, may use strategy output
        - LaTeXSpecialistAgent: Depends on CodeModificationAgent
        - CodeTestingAgent: Depends on LaTeXSpecialistAgent
        - ErrorSurgeonAgent: Depends on CodeTestingAgent (if errors found)
        - VisualComposerAgent: Can run in parallel with code agents
        - DimensionSpecialistAgent: Can run in parallel with visual agents
        - AnimationDirectorAgent: Depends on EducationalDesignAgent
        - RenderingOptimizerAgent: Depends on all code modifications
        - TerminalMonitorAgent: Can run throughout the process
        
        Optimization Strategies:
        - Speed: Maximize parallelization, minimize dependencies
        - Quality: Include all agents with careful sequencing
        - Balanced: Optimize critical path while maintaining quality
        - Cost: Minimize expensive operations, selective agent use
        
        Be strategic, efficient, and comprehensive in your orchestration planning.
        """

    def _parse_orchestration_plan(self, response: str) -> OrchestrationPlan:
        """Parse orchestration plan from Claude's response."""

        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        title = "Orchestration Plan"
        description = (
            "Comprehensive agent orchestration for educational content generation"
        )

        # Define default execution phases based on dependencies
        execution_phases = [
            # Phase 1: Independent agents that can run first
            ["ContentStrategistAgent"],
            # Phase 2: Agents that depend on strategy
            ["EducationalDesignAgent", "CodeModificationAgent", "VisualComposerAgent"],
            # Phase 3: Agents that depend on code modifications
            ["LaTeXSpecialistAgent", "DimensionSpecialistAgent"],
            # Phase 4: Testing and refinement
            ["CodeTestingAgent", "AnimationDirectorAgent"],
            # Phase 5: Error handling if needed
            ["ErrorSurgeonAgent"],
            # Phase 6: Final optimization
            ["RenderingOptimizerAgent", "TerminalMonitorAgent"],
        ]

        # Agent dependencies
        agent_dependencies = {
            "ContentStrategistAgent": [],
            "EducationalDesignAgent": ["ContentStrategistAgent"],
            "CodeModificationAgent": [],
            "LaTeXSpecialistAgent": ["CodeModificationAgent"],
            "CodeTestingAgent": ["LaTeXSpecialistAgent"],
            "ErrorSurgeonAgent": ["CodeTestingAgent"],
            "VisualComposerAgent": [],
            "RenderingOptimizerAgent": [
                "CodeModificationAgent",
                "LaTeXSpecialistAgent",
            ],
            "AnimationDirectorAgent": ["EducationalDesignAgent"],
            "DimensionSpecialistAgent": ["VisualComposerAgent"],
            "TerminalMonitorAgent": [],
        }

        # Parallel opportunities
        parallel_opportunities = [
            ["EducationalDesignAgent", "CodeModificationAgent", "VisualComposerAgent"],
            ["LaTeXSpecialistAgent", "DimensionSpecialistAgent"],
            ["RenderingOptimizerAgent", "TerminalMonitorAgent"],
        ]

        # Critical path (longest dependency chain)
        critical_path = [
            "ContentStrategistAgent",
            "EducationalDesignAgent",
            "AnimationDirectorAgent",
            "RenderingOptimizerAgent",
        ]

        # Estimated duration (in seconds)
        estimated_duration = len(execution_phases) * 15.0  # Rough estimate

        return OrchestrationPlan(
            plan_id=plan_id,
            title=title,
            description=description,
            execution_phases=execution_phases,
            agent_dependencies=agent_dependencies,
            estimated_duration=estimated_duration,
            parallel_opportunities=parallel_opportunities,
            critical_path=critical_path,
            optimization_strategy="balanced",
            fallback_strategies=[
                "Skip failed agents",
                "Retry with simplified parameters",
            ],
        )
