"""
ExplainX Multi-Agent System

A clean architecture implementation using Anthropic Claude + LangGraph
for educational video generation with intelligent agent coordination.
"""

__version__ = "1.0.0"

from .infrastructure.config import AgentConfig

# TODO: Import these when implemented
# from .application.services import AgentOrchestrator
# from .core.agents import LaTeXSpecialistAgent, CodeModifierAgent, VisualComposerAgent

__all__ = [
    "AgentConfig",
    # TODO: Add these when implemented
    # "AgentOrchestrator",
    # "LaTeXSpecialistAgent",
    # "CodeModifierAgent",
    # "VisualComposerAgent",
]
