"""
T5.7: Metrics and structured logging for validator observability.
Provides counters, histograms, and structured logs for dashboards.
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict


# T5.7: Metrics storage (in-memory for this implementation)
# In production, this would integrate with Prometheus, StatsD, etc.
class MetricsCollector:
    """Collects validation metrics for observability."""

    def __init__(self):
        # Counters
        self.success_total = 0
        self.failure_total = Counter()  # by kind
        self.timeout_total = 0
        self.retry_total = 0

        # Histograms (stored as lists for percentile calculation)
        self.duration_ms = []
        self.rss_peak_mb = []

        # Internal tracking
        self._reset_time = time.time()

    def increment_success(self):
        """Increment validator_success_total counter."""
        self.success_total += 1

    def increment_failure(self, kind: str):
        """Increment validator_failure_total counter by kind."""
        self.failure_total[kind] += 1

    def increment_timeout(self):
        """Increment validator_timeout_total counter."""
        self.timeout_total += 1

    def increment_retry(self):
        """Increment validator_retry_total counter."""
        self.retry_total += 1

    def record_duration(self, duration_ms: float):
        """Record validation duration for histogram."""
        self.duration_ms.append(duration_ms)
        # Keep only last 1000 samples to prevent memory growth
        if len(self.duration_ms) > 1000:
            self.duration_ms = self.duration_ms[-1000:]

    def record_memory(self, rss_peak_mb: float):
        """Record peak memory usage for histogram."""
        if rss_peak_mb > 0:  # Only record valid memory measurements
            self.rss_peak_mb.append(rss_peak_mb)
            # Keep only last 1000 samples
            if len(self.rss_peak_mb) > 1000:
                self.rss_peak_mb = self.rss_peak_mb[-1000:]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary for dashboards."""

        def percentile(data, p):
            if not data:
                return 0.0
            sorted_data = sorted(data)
            k = (len(sorted_data) - 1) * p / 100
            f = int(k)
            c = k - f
            if f + 1 < len(sorted_data):
                return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
            return sorted_data[f]

        return {
            "counters": {
                "validator_success_total": self.success_total,
                "validator_failure_total": dict(self.failure_total),
                "validator_timeout_total": self.timeout_total,
                "validator_retry_total": self.retry_total,
            },
            "histograms": {
                "validator_duration_ms": {
                    "count": len(self.duration_ms),
                    "p50": percentile(self.duration_ms, 50),
                    "p95": percentile(self.duration_ms, 95),
                    "p99": percentile(self.duration_ms, 99),
                    "max": max(self.duration_ms) if self.duration_ms else 0,
                },
                "validator_rss_peak_mb": {
                    "count": len(self.rss_peak_mb),
                    "p50": percentile(self.rss_peak_mb, 50),
                    "p95": percentile(self.rss_peak_mb, 95),
                    "p99": percentile(self.rss_peak_mb, 99),
                    "max": max(self.rss_peak_mb) if self.rss_peak_mb else 0,
                },
            },
            "metadata": {
                "reset_time": self._reset_time,
                "uptime_seconds": time.time() - self._reset_time,
            },
        }

    def reset_metrics(self):
        """Reset all metrics (for testing)."""
        self.__init__()


# Global metrics instance
metrics = MetricsCollector()


@dataclass
class StructuredLogEntry:
    """T5.7: Structured log entry for validation events."""

    video_id: str
    scene_id: str
    result: str  # "success", "failure", "timeout", "retry"
    duration_ms: float
    rss_peak_mb: float = 0.0
    exit_code: int = 0
    error_kind: Optional[str] = None
    attempt: int = 1
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string for logging."""
        return json.dumps(self.to_dict())


class StructuredLogger:
    """T5.7: Structured logger for validation events."""

    def __init__(self, logger_name: str = "validator"):
        self.logger = logging.getLogger(logger_name)

        # Ensure structured logging format
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_validation_event(self, entry: StructuredLogEntry):
        """Log a structured validation event."""
        self.logger.info(f"VALIDATION_EVENT: {entry.to_json()}")

    def log_success(
        self,
        video_id: str,
        scene_id: str,
        duration_ms: float,
        rss_peak_mb: float = 0.0,
        attempt: int = 1,
    ):
        """Log successful validation."""
        entry = StructuredLogEntry(
            video_id=video_id,
            scene_id=scene_id,
            result="success",
            duration_ms=duration_ms,
            rss_peak_mb=rss_peak_mb,
            attempt=attempt,
        )
        self.log_validation_event(entry)

    def log_failure(
        self,
        video_id: str,
        scene_id: str,
        duration_ms: float,
        error_kind: str,
        exit_code: int = 0,
        rss_peak_mb: float = 0.0,
        attempt: int = 1,
    ):
        """Log failed validation."""
        entry = StructuredLogEntry(
            video_id=video_id,
            scene_id=scene_id,
            result="failure",
            duration_ms=duration_ms,
            rss_peak_mb=rss_peak_mb,
            exit_code=exit_code,
            error_kind=error_kind,
            attempt=attempt,
        )
        self.log_validation_event(entry)

    def log_timeout(
        self, video_id: str, scene_id: str, duration_ms: float, attempt: int = 1
    ):
        """Log timeout event."""
        entry = StructuredLogEntry(
            video_id=video_id,
            scene_id=scene_id,
            result="timeout",
            duration_ms=duration_ms,
            attempt=attempt,
        )
        self.log_validation_event(entry)

    def log_retry(
        self,
        video_id: str,
        scene_id: str,
        duration_ms: float,
        error_kind: str,
        attempt: int,
    ):
        """Log retry attempt."""
        entry = StructuredLogEntry(
            video_id=video_id,
            scene_id=scene_id,
            result="retry",
            duration_ms=duration_ms,
            error_kind=error_kind,
            attempt=attempt,
        )
        self.log_validation_event(entry)


# Global structured logger instance
structured_logger = StructuredLogger()


@contextmanager
def validation_metrics_context(video_id: str, scene_id: str, attempt: int = 1):
    """
    T5.7: Context manager for automatic metrics collection and logging.

    Usage:
        with validation_metrics_context("vid123", "scene_01") as ctx:
            # Do validation work
            ctx.set_exit_code(1)
            ctx.set_rss_peak_mb(256.5)
            # Context will automatically log and record metrics on exit
    """

    class MetricsContext:
        def __init__(self):
            self.start_time = time.time()
            self.exit_code = 0
            self.rss_peak_mb = 0.0
            self.error_kind = None
            self.success = False

        def set_success(self):
            self.success = True

        def set_exit_code(self, code: int):
            self.exit_code = code

        def set_rss_peak_mb(self, mb: float):
            self.rss_peak_mb = mb

        def set_error_kind(self, kind: str):
            self.error_kind = kind

    ctx = MetricsContext()

    try:
        yield ctx

        # If we get here without exception and success not explicitly set
        if not ctx.success and ctx.exit_code == 0 and not ctx.error_kind:
            ctx.success = True

    except Exception as e:
        # Auto-detect error kind from exception
        if not ctx.error_kind:
            ctx.error_kind = type(e).__name__

    finally:
        # Calculate duration
        duration_ms = (time.time() - ctx.start_time) * 1000

        # Record metrics and logs
        if ctx.success:
            metrics.increment_success()
            structured_logger.log_success(
                video_id, scene_id, duration_ms, ctx.rss_peak_mb, attempt
            )
        else:
            error_kind = ctx.error_kind or "unknown_error"
            metrics.increment_failure(error_kind)
            structured_logger.log_failure(
                video_id,
                scene_id,
                duration_ms,
                error_kind,
                ctx.exit_code,
                ctx.rss_peak_mb,
                attempt,
            )

        # Record histograms
        metrics.record_duration(duration_ms)
        if ctx.rss_peak_mb > 0:
            metrics.record_memory(ctx.rss_peak_mb)


def get_metrics_summary() -> Dict[str, Any]:
    """Get current metrics summary for dashboard endpoints."""
    return metrics.get_metrics_summary()


def reset_metrics():
    """Reset metrics (for testing)."""
    metrics.reset_metrics()


# Convenience functions for direct metric recording
def record_success(
    video_id: str, scene_id: str, duration_ms: float, rss_peak_mb: float = 0.0
):
    """Record successful validation metrics."""
    metrics.increment_success()
    metrics.record_duration(duration_ms)
    if rss_peak_mb > 0:
        metrics.record_memory(rss_peak_mb)
    structured_logger.log_success(video_id, scene_id, duration_ms, rss_peak_mb)


def record_failure(
    video_id: str,
    scene_id: str,
    duration_ms: float,
    error_kind: str,
    exit_code: int = 0,
    rss_peak_mb: float = 0.0,
):
    """Record failed validation metrics."""
    metrics.increment_failure(error_kind)
    metrics.record_duration(duration_ms)
    if rss_peak_mb > 0:
        metrics.record_memory(rss_peak_mb)
    structured_logger.log_failure(
        video_id, scene_id, duration_ms, error_kind, exit_code, rss_peak_mb
    )


def record_timeout(video_id: str, scene_id: str, duration_ms: float):
    """Record timeout metrics."""
    metrics.increment_timeout()
    metrics.record_duration(duration_ms)
    structured_logger.log_timeout(video_id, scene_id, duration_ms)


def record_retry(
    video_id: str, scene_id: str, duration_ms: float, error_kind: str, attempt: int
):
    """Record retry attempt metrics."""
    metrics.increment_retry()
    structured_logger.log_retry(video_id, scene_id, duration_ms, error_kind, attempt)
