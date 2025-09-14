"""
T6: Error types for the video renderer.

Defines custom exception classes for render operations with structured
error information for debugging and logging.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class RenderSceneError(Exception):
    """Error during scene rendering with Manim."""

    scene_id: str
    class_name: str
    exit_code: Optional[int] = None
    stderr_excerpt: str = ""
    stdout_excerpt: str = ""
    render_time_s: float = 0.0

    def __post_init__(self):
        message = f"Scene render failed: {self.scene_id} (class: {self.class_name})"
        if self.exit_code is not None:
            message += f" - exit code {self.exit_code}"
        if self.stderr_excerpt:
            message += f" - {self.stderr_excerpt[:200]}"
        super().__init__(message)


@dataclass
class RenderTimeoutError(Exception):
    """Scene rendering exceeded time limit."""

    scene_id: str
    timeout_s: int
    elapsed_s: float = 0.0

    def __post_init__(self):
        message = f"Scene render timeout: {self.scene_id} ({self.elapsed_s:.1f}s > {self.timeout_s}s)"
        super().__init__(message)


@dataclass
class RenderOOMError(Exception):
    """Scene rendering exceeded memory limit."""

    scene_id: str
    memory_limit_mb: int
    peak_memory_mb: float = 0.0

    def __post_init__(self):
        message = f"Scene render OOM: {self.scene_id} ({self.peak_memory_mb:.1f}MB > {self.memory_limit_mb}MB)"
        super().__init__(message)


@dataclass
class ConcatError(Exception):
    """Error during video concatenation."""

    input_count: int
    crossfade_s: Optional[float] = None
    exit_code: Optional[int] = None
    stderr_excerpt: str = ""
    processing_time_s: float = 0.0

    def __post_init__(self):
        message = f"Video concatenation failed: {self.input_count} inputs"
        if self.crossfade_s is not None:
            message += f" with {self.crossfade_s}s crossfade"
        if self.exit_code is not None:
            message += f" - exit code {self.exit_code}"
        if self.stderr_excerpt:
            message += f" - {self.stderr_excerpt[:200]}"
        super().__init__(message)


@dataclass
class ThumbnailError(Exception):
    """Error during thumbnail generation."""

    video_path: str
    thumbnail_type: str  # "poster", "midpoint", "contact_sheet"
    exit_code: Optional[int] = None
    stderr_excerpt: str = ""
    processing_time_s: float = 0.0

    def __post_init__(self):
        message = (
            f"Thumbnail generation failed: {self.thumbnail_type} from {self.video_path}"
        )
        if self.exit_code is not None:
            message += f" - exit code {self.exit_code}"
        if self.stderr_excerpt:
            message += f" - {self.stderr_excerpt[:200]}"
        super().__init__(message)


@dataclass
class ValidationError(Exception):
    """Input validation error."""

    field: str
    value: Any
    constraint: str

    def __post_init__(self):
        message = f"Validation failed: {self.field} = {self.value!r} violates {self.constraint}"
        super().__init__(message)


@dataclass
class CacheError(Exception):
    """Cache operation error."""

    operation: str  # "get", "put", "clear"
    cache_key: str = ""
    underlying_error: str = ""

    def __post_init__(self):
        message = f"Cache {self.operation} failed"
        if self.cache_key:
            message += f" for key {self.cache_key[:16]}..."
        if self.underlying_error:
            message += f": {self.underlying_error}"
        super().__init__(message)


# Error factory functions for easy creation
def create_scene_timeout_error(
    scene_id: str, timeout_s: int, elapsed_s: float
) -> RenderTimeoutError:
    """Create a RenderTimeoutError with scene context."""
    return RenderTimeoutError(
        scene_id=scene_id, timeout_s=timeout_s, elapsed_s=elapsed_s
    )


def create_scene_oom_error(
    scene_id: str, limit_mb: int, peak_mb: float
) -> RenderOOMError:
    """Create a RenderOOMError with memory context."""
    return RenderOOMError(
        scene_id=scene_id, memory_limit_mb=limit_mb, peak_memory_mb=peak_mb
    )


def create_concat_error(
    input_count: int, crossfade_s: Optional[float], exit_code: int, stderr: str
) -> ConcatError:
    """Create a ConcatError with concatenation context."""
    return ConcatError(
        input_count=input_count,
        crossfade_s=crossfade_s,
        exit_code=exit_code,
        stderr_excerpt=stderr[:500] if stderr else "",
    )


def create_thumbnail_error(
    video_path: str, thumbnail_type: str, exit_code: int, stderr: str
) -> ThumbnailError:
    """Create a ThumbnailError with thumbnail context."""
    return ThumbnailError(
        video_path=video_path,
        thumbnail_type=thumbnail_type,
        exit_code=exit_code,
        stderr_excerpt=stderr[:500] if stderr else "",
    )
