"""
T6.6: Metrics collection and structured logging for video rendering.

Provides comprehensive observability for the rendering pipeline including
latency histograms, success/failure counters, and structured JSON logs.
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter


@dataclass
class RenderMetrics:
    """Metrics for a single render operation."""

    operation_type: str  # "scene_render", "concat", "thumbnail"
    video_id: str
    scene_id: Optional[str] = None
    success: bool = False
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    exit_code: Optional[int] = None
    peak_memory_mb: float = 0.0
    cpu_time_ms: float = 0.0
    frames_rendered: int = 0
    file_size_mb: float = 0.0
    cache_hit: bool = False
    error_type: Optional[str] = None
    additional_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}
        if self.duration_ms == 0.0 and self.end_time > self.start_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class ConcatMetrics:
    """Specialized metrics for concatenation operations."""

    video_id: str
    input_count: int
    output_duration_s: float
    crossfade_used: bool
    crossfade_duration_s: Optional[float]
    transitions_applied: int
    re_encodes: int
    total_latency_ms: float
    success: bool
    cache_hit: bool = False
    error_type: Optional[str] = None


@dataclass
class ThumbnailMetrics:
    """Specialized metrics for thumbnail generation."""

    video_id: str
    thumbnail_type: str  # "poster", "midpoint", "contact_sheet"
    extraction_time_ms: float
    source_duration_s: float
    success: bool
    cache_hit: bool = False
    error_type: Optional[str] = None


class MetricsCollector:
    """T6.6: Comprehensive metrics collection for render operations."""

    def __init__(self):
        """Initialize metrics collector."""
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.metrics_history: List[RenderMetrics] = []
        self.session_start = time.time()

    def increment_counter(self, name: str, labels: Dict[str, str] = None):
        """Increment a named counter with optional labels."""
        key = self._make_metric_key(name, labels)
        self.counters[key] += 1

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a value in a histogram with optional labels."""
        key = self._make_metric_key(name, labels)
        self.histograms[key].append(value)

    def record_render_metrics(self, metrics: RenderMetrics):
        """Record comprehensive render metrics."""
        self.metrics_history.append(metrics)

        # Update counters
        operation = metrics.operation_type
        result = "success" if metrics.success else "failure"

        self.increment_counter(f"renderer_{operation}_total", {"result": result})

        if metrics.cache_hit:
            self.increment_counter(f"renderer_{operation}_cache_hit_total")

        if not metrics.success and metrics.error_type:
            self.increment_counter(
                f"renderer_{operation}_error_total", {"error_type": metrics.error_type}
            )

        # Update histograms
        self.record_histogram(f"renderer_{operation}_duration_ms", metrics.duration_ms)

        if metrics.peak_memory_mb > 0:
            self.record_histogram(
                f"renderer_{operation}_memory_mb", metrics.peak_memory_mb
            )

        if metrics.file_size_mb > 0:
            self.record_histogram(
                f"renderer_{operation}_file_size_mb", metrics.file_size_mb
            )

        if metrics.frames_rendered > 0:
            self.record_histogram(
                f"renderer_{operation}_frames", metrics.frames_rendered
            )

    def record_concat_metrics(self, metrics: ConcatMetrics):
        """Record concatenation-specific metrics."""
        # Convert to generic render metrics
        render_metrics = RenderMetrics(
            operation_type="concat",
            video_id=metrics.video_id,
            success=metrics.success,
            duration_ms=metrics.total_latency_ms,
            cache_hit=metrics.cache_hit,
            error_type=metrics.error_type,
            additional_data={
                "input_count": metrics.input_count,
                "output_duration_s": metrics.output_duration_s,
                "crossfade_used": metrics.crossfade_used,
                "crossfade_duration_s": metrics.crossfade_duration_s,
                "transitions_applied": metrics.transitions_applied,
                "re_encodes": metrics.re_encodes,
            },
        )

        self.record_render_metrics(render_metrics)

        # Additional concat-specific metrics
        self.record_histogram("renderer_concat_input_count", metrics.input_count)
        self.record_histogram(
            "renderer_concat_output_duration_s", metrics.output_duration_s
        )

        if metrics.crossfade_used and metrics.transitions_applied > 0:
            self.increment_counter("renderer_concat_crossfade_total")
            self.record_histogram(
                "renderer_concat_transitions", metrics.transitions_applied
            )

    def record_thumbnail_metrics(self, metrics: ThumbnailMetrics):
        """Record thumbnail-specific metrics."""
        # Convert to generic render metrics
        render_metrics = RenderMetrics(
            operation_type="thumbnail",
            video_id=metrics.video_id,
            success=metrics.success,
            duration_ms=metrics.extraction_time_ms,
            cache_hit=metrics.cache_hit,
            error_type=metrics.error_type,
            additional_data={
                "thumbnail_type": metrics.thumbnail_type,
                "source_duration_s": metrics.source_duration_s,
            },
        )

        self.record_render_metrics(render_metrics)

        # Thumbnail-specific metrics
        labels = {"thumbnail_type": metrics.thumbnail_type}
        self.increment_counter("renderer_thumbnail_generated_total", labels)
        self.record_histogram(
            "renderer_thumbnail_extraction_ms", metrics.extraction_time_ms, labels
        )

    def get_counter_value(self, name: str, labels: Dict[str, str] = None) -> int:
        """Get current value of a counter."""
        key = self._make_metric_key(name, labels)
        return self.counters.get(key, 0)

    def get_histogram_stats(
        self, name: str, labels: Dict[str, str] = None
    ) -> Dict[str, float]:
        """Get statistical summary of a histogram."""
        key = self._make_metric_key(name, labels)
        values = self.histograms.get(key, [])

        if not values:
            return {}

        sorted_values = sorted(values)
        count = len(values)

        return {
            "count": count,
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / count,
            "median": sorted_values[count // 2],
            "p95": sorted_values[int(count * 0.95)] if count > 0 else 0,
            "p99": sorted_values[int(count * 0.99)] if count > 0 else 0,
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get comprehensive summary of all metrics."""
        return {
            "session_duration_s": time.time() - self.session_start,
            "total_operations": len(self.metrics_history),
            "counters": dict(self.counters),
            "histogram_stats": {
                name: self.get_histogram_stats(name) for name in self.histograms.keys()
            },
            "recent_operations": [
                asdict(m) for m in self.metrics_history[-10:]  # Last 10 operations
            ],
        }

    def _make_metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create a metric key with optional labels."""
        if not labels:
            return name
        label_parts = [f"{k}={v}" for k, v in sorted(labels.items())]
        return f"{name}{{{','.join(label_parts)}}}"

    def reset(self):
        """Reset all metrics."""
        self.counters.clear()
        self.histograms.clear()
        self.metrics_history.clear()
        self.session_start = time.time()


class StructuredLogger:
    """T6.6: Structured JSON logging for render operations."""

    def __init__(self, logger_name: str = "video_renderer", log_file: Path = None):
        """
        Initialize structured logger.

        Args:
            logger_name: Name for the logger instance
            log_file: Optional file path for log output
        """
        self.logger = logging.getLogger(logger_name)
        self.setup_logger(log_file)

    def setup_logger(self, log_file: Path = None):
        """Setup logger with JSON formatting."""
        if self.logger.handlers:
            return  # Already configured

        # Create formatter for structured JSON logs
        formatter = logging.Formatter("%(message)s")

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

        # Optional file handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)

        self.logger.setLevel(logging.DEBUG)

    def log_structured(self, level: str, event_type: str, **kwargs):
        """Log a structured event with JSON formatting."""
        log_entry = {
            "timestamp": time.time(),
            "level": level.upper(),
            "event_type": event_type,
            **kwargs,
        }

        # Remove None values and large objects
        filtered_entry = {
            k: v
            for k, v in log_entry.items()
            if v is not None and not self._is_large_object(v)
        }

        log_message = json.dumps(filtered_entry)

        # Use appropriate logging level
        if level.lower() == "error":
            self.logger.error(log_message)
        elif level.lower() == "warning":
            self.logger.warning(log_message)
        elif level.lower() == "info":
            self.logger.info(log_message)
        else:
            self.logger.debug(log_message)

    def log_render_start(
        self, video_id: str, scene_id: Optional[str], operation_type: str, **kwargs
    ):
        """Log the start of a render operation."""
        self.log_structured(
            "info",
            "render_start",
            video_id=video_id,
            scene_id=scene_id,
            operation=operation_type,
            **kwargs,
        )

    def log_render_complete(
        self,
        video_id: str,
        scene_id: Optional[str],
        operation_type: str,
        success: bool,
        duration_ms: float,
        **kwargs,
    ):
        """Log the completion of a render operation."""
        self.log_structured(
            "info" if success else "error",
            "render_complete",
            video_id=video_id,
            scene_id=scene_id,
            operation=operation_type,
            success=success,
            duration_ms=duration_ms,
            **kwargs,
        )

    def log_cache_event(self, event_type: str, cache_key: str, **kwargs):
        """Log cache-related events."""
        self.log_structured(
            "debug",
            "cache_event",
            cache_event=event_type,
            cache_key=cache_key[:16] + "..." if len(cache_key) > 16 else cache_key,
            **kwargs,
        )

    def log_error(self, error_type: str, error_message: str, **kwargs):
        """Log an error event."""
        self.log_structured(
            "error",
            "error",
            error_type=error_type,
            error_message=error_message,
            **kwargs,
        )

    def _is_large_object(self, obj) -> bool:
        """Check if object is too large to log."""
        if isinstance(obj, str) and len(obj) > 1000:
            return True
        if isinstance(obj, (list, dict)) and len(str(obj)) > 2000:
            return True
        return False


# Global metrics collector and logger instances
_global_metrics_collector = None
_global_structured_logger = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


def get_structured_logger() -> StructuredLogger:
    """Get global structured logger instance."""
    global _global_structured_logger
    if _global_structured_logger is None:
        _global_structured_logger = StructuredLogger()
    return _global_structured_logger


@contextmanager
def render_metrics_context(
    operation_type: str, video_id: str, scene_id: Optional[str] = None
) -> ContextManager[RenderMetrics]:
    """
    Context manager for collecting render metrics.

    Usage:
        with render_metrics_context("scene_render", "video_123", "scene_01") as metrics:
            # Do render work
            metrics.frames_rendered = 150
            metrics.file_size_mb = 25.5
            # Success/failure and timing are automatically tracked
    """
    metrics = RenderMetrics(
        operation_type=operation_type,
        video_id=video_id,
        scene_id=scene_id,
        start_time=time.time(),
    )

    logger = get_structured_logger()
    collector = get_metrics_collector()

    # Log start
    logger.log_render_start(video_id, scene_id, operation_type)

    try:
        yield metrics
        metrics.success = True
    except Exception as e:
        metrics.success = False
        metrics.error_type = type(e).__name__
        logger.log_error(
            metrics.error_type, str(e), video_id=video_id, scene_id=scene_id
        )
        raise
    finally:
        metrics.end_time = time.time()
        metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000

        # Log completion
        logger.log_render_complete(
            video_id,
            scene_id,
            operation_type,
            metrics.success,
            metrics.duration_ms,
            peak_memory_mb=metrics.peak_memory_mb,
            frames_rendered=metrics.frames_rendered,
            file_size_mb=metrics.file_size_mb,
            cache_hit=metrics.cache_hit,
        )

        # Record metrics
        collector.record_render_metrics(metrics)


def reset_global_metrics():
    """Reset global metrics (useful for testing)."""
    global _global_metrics_collector
    if _global_metrics_collector:
        _global_metrics_collector.reset()
