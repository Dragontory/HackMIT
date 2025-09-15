"""
Interfaces for the ExplainX agent system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .models import AgentState, AgentResult, ContentStrategy


class IAgent(ABC):
    """Base interface for all agents in the system."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Agent description and capabilities."""
        pass

    @abstractmethod
    async def process(self, state: AgentState) -> AgentResult:
        """
        Process the current state and return results.

        Args:
            state: Current agent state

        Returns:
            AgentResult: Processing results and updated data
        """
        pass


class IContentAnalyzer(IAgent):
    """Interface for content analysis agents."""

    @abstractmethod
    async def analyze_content(self, content: str, title: str) -> ContentStrategy:
        """
        Analyze content and create learning strategy.

        Args:
            content: Raw content to analyze
            title: Content title/topic

        Returns:
            ContentStrategy: Comprehensive content analysis and recommendations
        """
        pass

    @abstractmethod
    async def identify_learning_objectives(self, content: str) -> List[Dict[str, Any]]:
        """Extract and prioritize learning objectives."""
        pass

    @abstractmethod
    async def assess_difficulty_progression(self, content: str) -> List[str]:
        """Determine optimal difficulty progression."""
        pass

    @abstractmethod
    async def recommend_visualizations(self, content: str) -> List[Dict[str, Any]]:
        """Identify visualization opportunities."""
        pass


class ICodeModifier(IAgent):
    """Interface for code modification agents."""

    @abstractmethod
    async def fix_latex_errors(self, code: str, error_log: str) -> AgentResult:
        """Fix LaTeX compilation errors in code."""
        pass

    @abstractmethod
    async def optimize_positioning(self, code: str) -> AgentResult:
        """Fix positioning and bounds issues."""
        pass

    @abstractmethod
    async def enhance_animations(self, code: str) -> AgentResult:
        """Improve animation quality and timing."""
        pass


class IVisualComposer(IAgent):
    """Interface for visual composition agents."""

    @abstractmethod
    async def compose_layout(self, elements: List[Dict[str, Any]]) -> AgentResult:
        """Create optimal visual layout."""
        pass

    @abstractmethod
    async def prevent_overlaps(self, layout_data: Dict[str, Any]) -> AgentResult:
        """Ensure no visual elements overlap."""
        pass

    @abstractmethod
    async def optimize_typography(
        self, text_elements: List[Dict[str, Any]]
    ) -> AgentResult:
        """Optimize text sizing and positioning."""
        pass


class IErrorSurgeon(IAgent):
    """Interface for error detection and fixing agents."""

    @abstractmethod
    async def diagnose_error(self, error_log: str, code: str) -> AgentResult:
        """Diagnose and categorize errors."""
        pass

    @abstractmethod
    async def fix_error(
        self, error_type: str, code: str, context: Dict[str, Any]
    ) -> AgentResult:
        """Apply specific fixes for categorized errors."""
        pass


class IWorkflowOrchestrator(ABC):
    """Interface for workflow orchestration."""

    @abstractmethod
    async def execute_workflow(self, initial_state: AgentState) -> AgentResult:
        """Execute complete agent workflow."""
        pass

    @abstractmethod
    async def add_agent(self, agent: IAgent, position: Optional[str] = None) -> None:
        """Add agent to workflow."""
        pass

    @abstractmethod
    async def remove_agent(self, agent_name: str) -> None:
        """Remove agent from workflow."""
        pass
