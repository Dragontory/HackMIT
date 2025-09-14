"""
T6: Final Manim Render, Video Transitions, and Concatenation.

Complete production video rendering pipeline:
- T6.1: Production Manim renders (silent, per-scene)
- T6.2: Video-only transitions and concatenation
- T6.3: Thumbnail generation and poster frames
- T6.4: Content-addressed caching
- T6.5: End-to-end orchestration with metrics

Builds on T1-T5 for validated scenes and generates final MP4 videos.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Literal, Dict, Any

__version__ = "1.0.0"


@dataclass(frozen=True)
class SceneRenderItem:
    """Individual scene to render in production quality."""

    scene_id: str
    class_name: str  # e.g., "Scene_sec_01"
    main_py: Path  # path to generated source from T4
    est_duration_s: float = 10.0  # estimated duration for resource allocation


@dataclass(frozen=True)
class RenderInput:
    """Complete input specification for video rendering."""

    video_id: str
    scenes: List[SceneRenderItem]  # in final playback order
    out_dir: Path
    quality: Literal["1080p", "720p"] = "1080p"
    fps: int = 30
    crossfade_s: Optional[float] = None  # None => straight cuts, else seconds

    def __post_init__(self):
        """Validate render input parameters."""
        if not self.scenes:
            raise ValueError("At least one scene is required")
        if self.fps not in [15, 24, 30, 60]:
            raise ValueError(f"Unsupported fps: {self.fps}")
        if self.crossfade_s is not None and self.crossfade_s <= 0:
            raise ValueError(f"crossfade_s must be positive: {self.crossfade_s}")


@dataclass(frozen=True)
class RenderResult:
    """Result of complete video rendering pipeline."""

    ok: bool
    final_mp4: Optional[Path] = None
    scene_mp4s: List[Path] = None
    thumbs: List[Path] = None
    logs: Dict[str, Any] = None

    def __post_init__(self):
        # Initialize mutable defaults safely
        if self.scene_mp4s is None:
            object.__setattr__(self, "scene_mp4s", [])
        if self.thumbs is None:
            object.__setattr__(self, "thumbs", [])
        if self.logs is None:
            object.__setattr__(self, "logs", {})


# Export main entry point and components
from .orchestrator import render_video_no_audio
from .config import RenderQualityPreset
from .thumbs import generate_contact_sheet

# Error types for T6.6
from .errors import (
    RenderSceneError,
    RenderTimeoutError,
    RenderOOMError,
    ConcatError,
    ThumbnailError,
    ValidationError,
    CacheError,
)

# Metrics and logging for T6.6
from .metrics import (
    get_metrics_collector,
    get_structured_logger,
    render_metrics_context,
    reset_global_metrics,
)

# Cache functionality for T6.4
from .cache import RenderCache, get_default_cache

__all__ = [
    # Core interfaces
    "SceneRenderItem",
    "RenderInput",
    "RenderResult",
    "RenderQualityPreset",
    # Main functions
    "render_video_no_audio",
    "generate_contact_sheet",
    # Error types (T6.6)
    "RenderSceneError",
    "RenderTimeoutError",
    "RenderOOMError",
    "ConcatError",
    "ThumbnailError",
    "ValidationError",
    "CacheError",
    # Metrics and logging (T6.6)
    "get_metrics_collector",
    "get_structured_logger",
    "render_metrics_context",
    "reset_global_metrics",
    # Cache (T6.4)
    "RenderCache",
    "get_default_cache",
]
