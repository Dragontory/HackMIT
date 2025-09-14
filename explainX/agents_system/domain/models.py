"""
Domain models for the ExplainX agent system.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal, TypedDict, Tuple
from enum import Enum


class DifficultyLevel(Enum):
    """Educational difficulty levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ContentType(Enum):
    """Types of educational content."""

    CONCEPTUAL = "conceptual"
    MATHEMATICAL = "mathematical"
    PRACTICAL = "practical"
    HISTORICAL = "historical"


class VisualizationType(Enum):
    """Types of visualizations for educational content."""

    DIAGRAM = "diagram"
    GRAPH = "graph"
    FLOWCHART = "flowchart"
    EQUATION = "equation"
    ANIMATION = "animation"
    CODE_SNIPPET = "code_snippet"


# Note: LearningObjective moved to Educational Design section (line ~685)


@dataclass
class ContentChunk:
    """Represents a chunk of educational content."""

    id: str
    title: str
    content: str
    content_type: ContentType
    difficulty: DifficultyLevel
    estimated_reading_time: int
    key_concepts: List[str] = field(default_factory=list)
    mathematical_concepts: List[str] = field(default_factory=list)


@dataclass
class VisualizationOpportunity:
    """Represents an opportunity for visualization."""

    concept: str
    visualization_type: VisualizationType
    description: str
    priority: Literal["high", "medium", "low"]
    estimated_complexity: Literal["simple", "moderate", "complex"]


@dataclass
class AnimationRecommendation:
    """Represents a recommendation for animation."""

    concept: str
    animation_type: Literal["2d", "3d", "hybrid"]
    description: str
    educational_value: Literal["essential", "helpful", "optional"]
    complexity: Literal["simple", "moderate", "complex"]


@dataclass
class ContentStrategy:
    """Complete content strategy for educational video generation."""

    # Analysis results
    learning_objectives: List[LearningObjective]
    content_chunks: List[ContentChunk]
    difficulty_progression: List[DifficultyLevel]

    # Optimization recommendations
    visual_opportunities: List[VisualizationOpportunity]
    animation_recommendations: List[AnimationRecommendation]

    # Metadata
    total_estimated_time: int
    recommended_scene_count: int
    cognitive_load_assessment: Literal["low", "moderate", "high"]

    # Content quality indicators
    mathematical_density: float  # 0.0 to 1.0
    conceptual_complexity: float  # 0.0 to 1.0
    practical_relevance: float  # 0.0 to 1.0


class AgentState(TypedDict):
    """Represents the state passed between agents in LangGraph workflows."""

    # Input content
    raw_content: str
    content_title: str

    # Content Strategist outputs
    content_strategy: Optional[ContentStrategy]

    # LaTeX Specialist outputs
    latex_specialist_result: Optional[LaTeXSpecialistResult]

    # Code Modification Agent outputs
    code_modification_result: Optional[CodeModificationResult]

    # Code Testing Agent outputs
    code_testing_result: Optional[CodeTestingResult]

    # Error Surgeon Agent outputs
    error_surgery_result: Optional[ErrorSurgeryResult]

    # Terminal Monitor Agent outputs
    terminal_monitoring_result: Optional[TerminalMonitoringResult]

    # Visual Composer Agent outputs
    visual_composition_result: Optional[VisualCompositionResult]

    # Rendering Optimizer Agent outputs
    rendering_optimization_result: Optional[RenderingOptimizationResult]

    # Animation Director Agent outputs
    animation_direction_result: Optional[AnimationDirectionResult]

    # Dimension Specialist Agent outputs
    dimension_specialization_result: Optional[DimensionSpecializationResult]

    # Educational Design Agent outputs
    educational_design_result: Optional[EducationalDesignResult]

    # Integration Orchestrator Agent outputs
    integration_orchestration_result: Optional[IntegrationOrchestrationResult]

    # Code to be processed/fixed
    manim_code: Optional[str]
    error_log: Optional[str]

    # Processing metadata
    current_agent: str
    processing_stage: str
    errors: List[str]
    warnings: List[str]

    # Agent communication
    agent_messages: List[Dict[str, Any]]


@dataclass
class LaTeXFix:
    """Represents a LaTeX expression fix."""

    original_expression: str
    fixed_expression: str
    error_type: str
    explanation: str
    confidence: float  # 0.0 to 1.0


@dataclass
class LaTeXValidationResult:
    """Result of LaTeX expression validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ManimCodeAnalysis:
    """Analysis of Manim code for LaTeX issues."""

    total_latex_expressions: int
    problematic_expressions: List[Dict[str, Any]] = field(default_factory=list)
    complexity_score: float = 0.0  # 0.0 to 1.0
    manim_compatibility_issues: List[str] = field(default_factory=list)


@dataclass
class LaTeXSpecialistResult:
    """Result from LaTeX Specialist Agent operations."""

    original_code: str
    fixed_code: str
    fixes_applied: List[LaTeXFix] = field(default_factory=list)
    validation_results: List[LaTeXValidationResult] = field(default_factory=list)
    code_analysis: Optional[ManimCodeAnalysis] = None
    success: bool = True
    processing_time: float = 0.0


@dataclass
class CodeModification:
    """Represents a code modification applied by the Code Modification Agent."""

    modification_type: str  # positioning, bounds, timing, animation, structure
    original_line: str
    modified_line: str
    line_number: int
    explanation: str
    confidence: float  # 0.0 to 1.0
    impact_score: float  # 0.0 to 1.0 (how significant this change is)


@dataclass
class PositionAnalysis:
    """Analysis of element positioning in Manim code."""

    total_elements: int
    out_of_bounds_elements: List[Dict[str, Any]] = field(default_factory=list)
    overlapping_elements: List[Dict[str, Any]] = field(default_factory=list)
    positioning_suggestions: List[str] = field(default_factory=list)
    screen_utilization: float = 0.0  # 0.0 to 1.0


@dataclass
class TimingAnalysis:
    """Analysis of animation timing in Manim code."""

    total_animations: int
    suggested_pace: str  # slow, moderate, fast
    total_duration: float
    cognitive_load_assessment: str  # low, moderate, high
    timing_issues: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CodeQualityMetrics:
    """Metrics for assessing Manim code quality."""

    complexity_score: float  # 0.0 to 1.0
    readability_score: float  # 0.0 to 1.0
    performance_score: float  # 0.0 to 1.0
    educational_effectiveness: float  # 0.0 to 1.0
    maintainability_score: float  # 0.0 to 1.0


@dataclass
class CodeModificationResult:
    """Result from Code Modification Agent operations."""

    original_code: str
    modified_code: str
    modifications_applied: List[CodeModification] = field(default_factory=list)
    position_analysis: Optional[PositionAnalysis] = None
    timing_analysis: Optional[TimingAnalysis] = None
    quality_metrics: Optional[CodeQualityMetrics] = None
    validation_passed: bool = True
    success: bool = True
    processing_time: float = 0.0


@dataclass
class TestCase:
    """Represents a test case for Manim code."""

    test_id: str
    test_name: str
    test_description: str
    expected_result: str
    actual_result: Optional[str] = None
    passed: bool = False
    error_message: Optional[str] = None


@dataclass
class SandboxExecutionResult:
    """Result of executing code in a sandbox environment."""

    execution_success: bool
    stdout: str
    stderr: str
    execution_time: float
    exit_code: int
    memory_usage: Optional[float] = None


@dataclass
class ManimTestResult:
    """Result of testing Manim code."""

    test_id: str
    scene_name: str
    test_type: str  # syntax, render, object_creation, animation
    success: bool
    error_message: Optional[str] = None
    execution_result: Optional[SandboxExecutionResult] = None
    screenshot_path: Optional[str] = None


@dataclass
class CodeTestingResult:
    """Result from Code Testing Agent operations."""

    original_code: str
    test_code: str
    test_cases: List[TestCase] = field(default_factory=list)
    manim_test_results: List[ManimTestResult] = field(default_factory=list)
    syntax_valid: bool = False
    render_valid: bool = False
    object_creation_valid: bool = False
    animation_valid: bool = False
    success: bool = False
    processing_time: float = 0.0
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ErrorDiagnosis:
    """Detailed diagnosis of a specific error."""

    error_id: str
    error_type: str  # syntax, runtime, latex, manim_specific
    error_message: str
    error_location: Optional[str] = None  # file:line:col
    error_context: Optional[str] = None  # code snippet around error
    severity: str = "high"  # low, medium, high, critical
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class ErrorFix:
    """A specific fix for an error."""

    error_id: str
    fix_id: str
    fix_description: str
    original_code: str
    fixed_code: str
    line_number: Optional[int] = None
    confidence: float = 0.0  # 0.0 to 1.0
    is_applied: bool = False
    requires_human_review: bool = False


@dataclass
class ErrorSurgeryResult:
    """Result from Error Surgeon Agent operations."""

    original_code: str
    fixed_code: str
    error_diagnoses: List[ErrorDiagnosis] = field(default_factory=list)
    applied_fixes: List[ErrorFix] = field(default_factory=list)
    unfixable_errors: List[ErrorDiagnosis] = field(default_factory=list)
    success: bool = False
    processing_time: float = 0.0
    requires_human_intervention: bool = False


@dataclass
class TerminalEvent:
    """A significant event detected in terminal output."""

    event_id: str
    event_type: str  # error, warning, progress, success, info
    timestamp: float
    message: str
    source_line: str
    line_number: int
    severity: str = "medium"  # low, medium, high, critical
    context: Optional[str] = None
    suggested_action: Optional[str] = None


@dataclass
class TerminalAction:
    """An action to take in response to a terminal event."""

    action_id: str
    event_id: str
    action_type: str  # fix, retry, abort, ignore, notify
    description: str
    command: Optional[str] = None
    code_change: Optional[Dict[str, str]] = None  # {file_path: new_content}
    confidence: float = 0.0  # 0.0 to 1.0
    is_executed: bool = False
    result: Optional[str] = None


@dataclass
class TerminalMonitoringResult:
    """Result from Terminal Monitor Agent operations."""

    terminal_output: str
    detected_events: List[TerminalEvent] = field(default_factory=list)
    actions_taken: List[TerminalAction] = field(default_factory=list)
    monitoring_duration: float = 0.0
    is_active: bool = False
    success: bool = True
    processing_time: float = 0.0


@dataclass
class VisualElement:
    """A visual element in a Manim scene."""

    element_id: str
    element_type: str  # text, shape, equation, graph, etc.
    content: str  # The content of the element (e.g., text, LaTeX, code)
    position: Optional[Dict[str, float]] = None  # x, y, z coordinates
    style: Optional[Dict[str, Any]] = None  # color, opacity, etc.
    animations: List[Dict[str, Any]] = field(
        default_factory=list
    )  # Animations to apply
    duration: float = 1.0  # Duration of the element's presence
    dependencies: List[str] = field(
        default_factory=list
    )  # IDs of elements this depends on
    layer: int = 0  # Z-index/layer for composition
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata


@dataclass
class VisualComposition:
    """A composition of visual elements for a Manim scene."""

    composition_id: str
    title: str
    elements: List[VisualElement] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(
        default_factory=list
    )  # Timeline of animations
    duration: float = 0.0  # Total duration of the composition
    resolution: Tuple[int, int] = (1920, 1080)  # Width, height
    background_color: str = "#000000"  # Background color
    camera_config: Dict[str, Any] = field(default_factory=dict)  # Camera configuration
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata


@dataclass
class VisualCompositionResult:
    """Result from Visual Composer Agent operations."""

    original_code: str
    enhanced_code: str
    compositions: List[VisualComposition] = field(default_factory=list)
    element_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    layout_improvements: List[Dict[str, Any]] = field(default_factory=list)
    animation_improvements: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = False
    processing_time: float = 0.0


@dataclass
class RenderingProfile:
    """A profile for rendering settings."""

    profile_id: str
    name: str
    quality: str  # low, medium, high, production
    resolution: Tuple[int, int] = (1920, 1080)  # width, height
    frame_rate: int = 30
    pixel_width: Optional[int] = None  # For specific pixel width
    pixel_height: Optional[int] = None  # For specific pixel height
    preview_mode: bool = False  # Whether to use preview mode
    disable_caching: bool = False  # Whether to disable caching
    transparent: bool = False  # Whether to use transparent background
    write_to_movie: bool = True  # Whether to write to movie file
    save_last_frame: bool = False  # Whether to save only the last frame
    save_pngs: bool = False  # Whether to save PNG frames
    write_all: bool = False  # Whether to write all frames
    format: str = "mp4"  # Output format (mp4, mov, gif, etc.)
    renderer: str = "cairo"  # Renderer to use (cairo, opengl)
    media_dir: Optional[str] = None  # Custom media directory
    log_level: str = "INFO"  # Logging level
    progress_bar: bool = True  # Whether to show progress bar
    command_line_args: List[str] = field(
        default_factory=list
    )  # Additional command line args


@dataclass
class PerformanceMetrics:
    """Performance metrics for a rendering job."""

    total_render_time: float  # Total rendering time in seconds
    frames_rendered: int  # Total number of frames rendered
    average_frame_time: float  # Average time per frame in seconds
    peak_memory_usage: float  # Peak memory usage in MB
    cpu_usage: float  # Average CPU usage percentage
    gpu_usage: Optional[float] = None  # Average GPU usage percentage if available
    bottlenecks: List[str] = field(default_factory=list)  # Identified bottlenecks
    optimization_potential: float = 0.0  # Estimated potential improvement (0.0-1.0)


@dataclass
class OptimizationSuggestion:
    """A suggestion for optimizing rendering performance."""

    suggestion_id: str
    category: str  # quality, resolution, caching, code, hardware
    description: str
    impact: str  # low, medium, high
    implementation_complexity: str  # easy, medium, hard
    estimated_speedup: float  # Estimated speedup factor
    code_changes: Optional[str] = None  # Code changes if applicable
    command_line_args: Optional[List[str]] = None  # Command line args if applicable
    requires_hardware_change: bool = False  # Whether hardware changes are needed
    applied: bool = False  # Whether the suggestion has been applied


@dataclass
class RenderingOptimizationResult:
    """Result from Rendering Optimizer Agent operations."""

    original_code: str
    optimized_code: str
    original_profile: RenderingProfile
    optimized_profile: RenderingProfile
    performance_metrics: Optional[PerformanceMetrics] = None
    optimization_suggestions: List[OptimizationSuggestion] = field(default_factory=list)
    applied_optimizations: List[OptimizationSuggestion] = field(default_factory=list)
    estimated_time_saved: float = 0.0  # Estimated time saved in seconds
    estimated_speedup: float = 1.0  # Estimated speedup factor
    success: bool = False
    processing_time: float = 0.0


@dataclass
class AnimationSequence:
    """A sequence of animations with educational purpose and timing."""

    sequence_id: str
    name: str
    animations: List[Dict[str, Any]]  # List of animation operations
    duration: float  # Total duration in seconds
    start_time: float = 0.0  # Start time in the overall timeline
    educational_purpose: str = ""  # Educational purpose of this sequence
    target_concept: str = ""  # The concept being illustrated
    prerequisite_concepts: List[str] = field(
        default_factory=list
    )  # Concepts that should be understood first
    complexity_level: str = "medium"  # beginner, medium, advanced
    narration: Optional[str] = None  # Narration to accompany this sequence
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnimationTimeline:
    """A timeline of animation sequences with educational flow."""

    timeline_id: str
    title: str
    sequences: List[AnimationSequence] = field(default_factory=list)
    total_duration: float = 0.0  # Total duration in seconds
    learning_objectives: List[str] = field(default_factory=list)  # Learning objectives
    concept_flow: List[str] = field(default_factory=list)  # Flow of concepts
    educational_approach: str = "progressive"  # progressive, comparative, etc.
    target_audience: str = "general"  # general, beginner, advanced, etc.
    pacing_strategy: str = "balanced"  # slow, balanced, fast
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnimationDirectionResult:
    """Result from Animation Director Agent operations."""

    original_code: str
    directed_code: str
    timeline: AnimationTimeline
    sequences: List[AnimationSequence] = field(default_factory=list)
    educational_enhancements: List[Dict[str, Any]] = field(default_factory=list)
    timing_adjustments: List[Dict[str, Any]] = field(default_factory=list)
    narrative_elements: List[Dict[str, Any]] = field(default_factory=list)
    pacing_improvements: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = False
    processing_time: float = 0.0


@dataclass
class DimensionAnalysis:
    """Analysis of dimensional requirements for a concept or animation element."""

    element_id: str
    element_type: str  # mobject, equation, graph, scene, etc.
    content_description: str
    current_dimension: str = "2D"  # 2D, 3D, mixed
    recommended_dimension: str = "2D"  # 2D, 3D, mixed
    complexity_score: float = 0.0  # 0.0-1.0, higher means more complex
    educational_benefit_2d: float = 0.0  # 0.0-1.0, benefit of using 2D
    educational_benefit_3d: float = 0.0  # 0.0-1.0, benefit of using 3D
    implementation_difficulty_2d: float = 0.0  # 0.0-1.0, difficulty in 2D
    implementation_difficulty_3d: float = 0.0  # 0.0-1.0, difficulty in 3D
    visualization_requirements: List[str] = field(
        default_factory=list
    )  # spatial, depth, rotation, etc.
    audience_considerations: List[str] = field(
        default_factory=list
    )  # beginner-friendly, advanced, etc.
    reasoning: str = ""  # Explanation for the recommendation
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DimensionTransformation:
    """A transformation from one dimensional representation to another."""

    transformation_id: str
    source_dimension: str  # 2D, 3D
    target_dimension: str  # 2D, 3D
    element_type: str  # mobject type being transformed
    transformation_type: str  # upgrade, downgrade, enhancement, projection
    code_changes: str = ""  # Required code modifications
    import_changes: List[str] = field(default_factory=list)  # Additional imports needed
    camera_config: Dict[str, Any] = field(
        default_factory=dict
    )  # Camera configuration changes
    lighting_config: Dict[str, Any] = field(
        default_factory=dict
    )  # Lighting configuration for 3D
    performance_impact: str = "medium"  # low, medium, high
    educational_impact: str = "medium"  # low, medium, high
    implementation_complexity: str = "medium"  # easy, medium, hard
    estimated_time_cost: float = 1.0  # Multiplier for rendering time
    quality_improvement: float = 0.0  # -1.0 to 1.0, improvement in visual quality
    description: str = ""  # Human-readable description
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DimensionRecommendation:
    """A recommendation for dimensional implementation."""

    recommendation_id: str
    concept_name: str
    current_implementation: str  # Description of current implementation
    recommended_implementation: str  # Description of recommended implementation
    dimension_choice: str  # 2D, 3D, mixed
    priority: str = "medium"  # low, medium, high
    rationale: str = ""  # Detailed explanation
    benefits: List[str] = field(default_factory=list)  # List of benefits
    trade_offs: List[str] = field(default_factory=list)  # List of trade-offs
    implementation_steps: List[str] = field(
        default_factory=list
    )  # Step-by-step implementation
    code_examples: List[str] = field(default_factory=list)  # Code examples
    resource_requirements: Dict[str, Any] = field(
        default_factory=dict
    )  # Performance requirements
    alternative_approaches: List[str] = field(
        default_factory=list
    )  # Alternative implementations
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DimensionSpecializationResult:
    """Result from Dimension Specialist Agent operations."""

    original_code: str
    specialized_code: str
    dimension_analyses: List[DimensionAnalysis] = field(default_factory=list)
    transformations: List[DimensionTransformation] = field(default_factory=list)
    recommendations: List[DimensionRecommendation] = field(default_factory=list)
    applied_transformations: List[DimensionTransformation] = field(default_factory=list)
    overall_dimension_strategy: str = "2D"  # 2D, 3D, mixed
    performance_considerations: List[str] = field(default_factory=list)
    educational_improvements: List[str] = field(default_factory=list)
    implementation_notes: List[str] = field(default_factory=list)
    success: bool = False
    processing_time: float = 0.0


@dataclass
class LearningObjective:
    """A specific learning objective with measurable outcomes."""

    objective_id: str
    title: str
    description: str
    cognitive_level: str = (
        "understand"  # remember, understand, apply, analyze, evaluate, create
    )
    difficulty: str = "medium"  # easy, medium, hard
    prerequisites: List[str] = field(default_factory=list)  # Required prior knowledge
    concepts: List[str] = field(default_factory=list)  # Key concepts covered
    assessments: List[str] = field(default_factory=list)  # How to measure achievement
    time_estimate: float = 3.0  # Estimated time in minutes
    priority: str = "medium"  # low, medium, high
    tags: List[str] = field(default_factory=list)  # Subject tags
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningSegment:
    """A segment of learning content with specific pedagogical purpose."""

    segment_id: str
    title: str
    learning_objectives: List[LearningObjective] = field(default_factory=list)
    content_type: str = "explanation"  # explanation, example, practice, assessment
    pedagogical_approach: str = (
        "direct"  # direct, inquiry, constructivist, collaborative
    )
    difficulty_progression: str = "gradual"  # sudden, gradual, stepped
    engagement_strategy: str = "visual"  # visual, interactive, narrative, problem-based
    prerequisite_segments: List[str] = field(default_factory=list)  # Dependencies
    duration: float = 5.0  # Duration in minutes
    complexity_level: str = "medium"  # beginner, medium, advanced
    attention_span_consideration: float = 1.0  # Multiplier for attention requirements
    cognitive_load: str = "medium"  # low, medium, high
    retention_techniques: List[str] = field(default_factory=list)  # Memory aids
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SceneStructure:
    """Structure of a Manim scene with educational design principles."""

    scene_id: str
    title: str
    learning_segments: List[LearningSegment] = field(default_factory=list)
    scene_type: str = "instructional"  # instructional, assessment, review, introduction
    opening_strategy: str = "hook"  # hook, objective, review, question
    closing_strategy: str = "summary"  # summary, transition, assessment, reinforcement
    transitions: List[Dict[str, Any]] = field(default_factory=list)  # Scene transitions
    visual_hierarchy: List[str] = field(default_factory=list)  # Visual importance order
    pacing_strategy: str = "varied"  # constant, varied, accelerating, decelerating
    interaction_points: List[Dict[str, Any]] = field(
        default_factory=list
    )  # Engagement moments
    total_duration: float = 15.0  # Total scene duration in minutes
    target_retention: float = 0.8  # Target retention rate (0.0-1.0)
    scaffolding_level: str = "medium"  # none, light, medium, heavy
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EducationalFlow:
    """Complete educational flow design with learning progression."""

    flow_id: str
    title: str
    scenes: List[SceneStructure] = field(default_factory=list)
    overall_learning_objectives: List[LearningObjective] = field(default_factory=list)
    pedagogical_framework: str = (
        "constructivist"  # behaviorist, cognitivist, constructivist
    )
    learning_theory: str = "active"  # passive, active, experiential, social
    difficulty_curve: str = "spiral"  # linear, spiral, branching, adaptive
    engagement_pattern: str = "peaks_valleys"  # constant, peaks_valleys, crescendo
    assessment_strategy: str = "formative"  # none, formative, summative, both
    personalization_level: str = "medium"  # none, light, medium, adaptive
    accessibility_features: List[str] = field(
        default_factory=list
    )  # Accessibility considerations
    total_duration: float = 60.0  # Total flow duration in minutes
    target_audience: str = "general"  # beginner, intermediate, advanced, mixed
    content_sequencing: str = "logical"  # logical, temporal, difficulty, interest
    feedback_mechanisms: List[str] = field(
        default_factory=list
    )  # How feedback is provided
    motivation_strategies: List[str] = field(
        default_factory=list
    )  # Motivation techniques
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EducationalDesignResult:
    """Result from Educational Design Agent operations."""

    original_content: str
    designed_flow: EducationalFlow
    scene_structures: List[SceneStructure] = field(default_factory=list)
    learning_objectives: List[LearningObjective] = field(default_factory=list)
    design_principles: List[str] = field(
        default_factory=list
    )  # Applied design principles
    pedagogical_justifications: List[str] = field(
        default_factory=list
    )  # Why choices were made
    accessibility_considerations: List[str] = field(
        default_factory=list
    )  # Accessibility features
    assessment_recommendations: List[str] = field(
        default_factory=list
    )  # Assessment suggestions
    engagement_strategies: List[str] = field(
        default_factory=list
    )  # Engagement techniques
    implementation_notes: List[str] = field(
        default_factory=list
    )  # Implementation guidance
    success: bool = False
    processing_time: float = 0.0


@dataclass
class AgentExecution:
    """Record of an individual agent execution within the orchestration."""

    agent_name: str
    execution_id: str
    start_time: float
    end_time: float = 0.0
    duration: float = 0.0
    success: bool = False
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Agent dependencies
    parallelizable: bool = True  # Can run in parallel with others


@dataclass
class OrchestrationPlan:
    """A plan for executing agents in optimal order with dependencies."""

    plan_id: str
    title: str
    description: str
    execution_phases: List[List[str]] = field(
        default_factory=list
    )  # Phases of agent execution
    agent_dependencies: Dict[str, List[str]] = field(
        default_factory=dict
    )  # Agent -> [dependencies]
    estimated_duration: float = 0.0  # Total estimated time
    parallel_opportunities: List[List[str]] = field(
        default_factory=list
    )  # Groups that can run in parallel
    critical_path: List[str] = field(default_factory=list)  # Critical path agents
    optimization_strategy: str = "balanced"  # balanced, speed, quality, cost
    fallback_strategies: List[str] = field(default_factory=list)  # Fallback options
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityMetrics:
    """Quality metrics for the overall orchestration result."""

    overall_score: float = 0.0  # 0.0-1.0 overall quality score
    technical_quality: float = 0.0  # Code quality, rendering, optimization
    educational_quality: float = 0.0  # Learning effectiveness, design principles
    content_accuracy: float = 0.0  # Content correctness and completeness
    visual_appeal: float = 0.0  # Visual design and aesthetics
    performance_score: float = 0.0  # Rendering and processing performance
    accessibility_score: float = 0.0  # Accessibility and inclusion features
    engagement_score: float = 0.0  # Engagement and motivation factors
    robustness_score: float = 0.0  # Error handling and reliability
    innovation_score: float = 0.0  # Novel or creative elements
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationOrchestrationResult:
    """Complete result from Integration Orchestrator Agent operations."""

    orchestration_id: str
    original_input: str
    final_output: str  # Final generated content/code
    execution_plan: OrchestrationPlan
    agent_executions: List[AgentExecution] = field(default_factory=list)
    quality_metrics: QualityMetrics = field(default_factory=QualityMetrics)

    # Aggregated results from all agents
    content_strategy_applied: Optional[Dict[str, Any]] = None
    latex_fixes_applied: List[str] = field(default_factory=list)
    code_modifications: List[str] = field(default_factory=list)
    tests_passed: List[str] = field(default_factory=list)
    errors_fixed: List[str] = field(default_factory=list)
    monitoring_insights: List[str] = field(default_factory=list)
    visual_enhancements: List[str] = field(default_factory=list)
    rendering_optimizations: List[str] = field(default_factory=list)
    animation_directions: List[str] = field(default_factory=list)
    dimensional_specializations: List[str] = field(default_factory=list)
    educational_design_applied: Optional[EducationalDesignResult] = None

    # Overall orchestration metrics
    total_processing_time: float = 0.0
    agents_executed: int = 0
    success_rate: float = 0.0  # Percentage of successful agent executions
    parallel_efficiency: float = 0.0  # How well parallelization was utilized
    critical_path_time: float = 0.0  # Time taken by critical path
    improvement_factor: float = 0.0  # Overall improvement over baseline

    # Status and health
    success: bool = False
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Standard result format for agent operations."""

    success: bool
    data: Any
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
