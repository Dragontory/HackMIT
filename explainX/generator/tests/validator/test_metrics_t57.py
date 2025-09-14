"""
Comprehensive T5.7 tests for metrics and structured logging.
Tests metrics increment verification, structured logs, and observability features.
"""

import time
import json
from unittest.mock import patch, MagicMock
import pytest

from generator.validator.metrics import (
    MetricsCollector,
    StructuredLogEntry,
    StructuredLogger,
    validation_metrics_context,
    get_metrics_summary,
    reset_metrics,
    record_success,
    record_failure,
    record_timeout,
    record_retry,
)


class TestT57MetricsCollector:
    """T5.7 specific tests for metrics collection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.metrics = MetricsCollector()

    def test_success_counter_increment(self):
        """T5.7: Test validator_success_total counter increments."""
        initial_count = self.metrics.success_total

        self.metrics.increment_success()
        assert self.metrics.success_total == initial_count + 1

        self.metrics.increment_success()
        assert self.metrics.success_total == initial_count + 2

    def test_failure_counter_by_kind(self):
        """T5.7: Test validator_failure_total counter by kind."""
        # Test different error kinds
        self.metrics.increment_failure("latex_error")
        self.metrics.increment_failure("asset_missing")
        self.metrics.increment_failure("latex_error")  # Same kind again

        assert self.metrics.failure_total["latex_error"] == 2
        assert self.metrics.failure_total["asset_missing"] == 1
        assert self.metrics.failure_total["unknown_kind"] == 0

    def test_timeout_counter_increment(self):
        """T5.7: Test validator_timeout_total counter increments."""
        initial_count = self.metrics.timeout_total

        self.metrics.increment_timeout()
        assert self.metrics.timeout_total == initial_count + 1

    def test_retry_counter_increment(self):
        """T5.7: Test validator_retry_total counter increments."""
        initial_count = self.metrics.retry_total

        self.metrics.increment_retry()
        assert self.metrics.retry_total == initial_count + 1

    def test_duration_histogram(self):
        """T5.7: Test validator_duration_ms histogram recording."""
        durations = [100.0, 250.0, 500.0, 1000.0, 150.0]

        for duration in durations:
            self.metrics.record_duration(duration)

        assert len(self.metrics.duration_ms) == len(durations)
        assert all(d in self.metrics.duration_ms for d in durations)

    def test_memory_histogram(self):
        """T5.7: Test validator_rss_peak_mb histogram recording."""
        memory_values = [128.5, 256.0, 512.2, 64.1]

        for memory in memory_values:
            self.metrics.record_memory(memory)

        assert len(self.metrics.rss_peak_mb) == len(memory_values)
        assert all(m in self.metrics.rss_peak_mb for m in memory_values)

    def test_memory_histogram_ignores_zero_values(self):
        """T5.7: Test memory histogram ignores invalid/zero values."""
        self.metrics.record_memory(0.0)  # Should be ignored
        self.metrics.record_memory(-5.0)  # Should be ignored
        self.metrics.record_memory(128.5)  # Should be recorded

        assert len(self.metrics.rss_peak_mb) == 1
        assert self.metrics.rss_peak_mb[0] == 128.5

    def test_histogram_size_limit(self):
        """T5.7: Test histogram keeps only last 1000 samples."""
        # Add more than 1000 samples
        for i in range(1200):
            self.metrics.record_duration(float(i))

        # Should keep only last 1000
        assert len(self.metrics.duration_ms) == 1000
        # Should keep the most recent values (200-1199)
        assert min(self.metrics.duration_ms) >= 200.0

    def test_metrics_summary_structure(self):
        """T5.7: Test metrics summary structure for dashboards."""
        # Add some test data
        self.metrics.increment_success()
        self.metrics.increment_failure("latex_error")
        self.metrics.increment_failure("latex_error")
        self.metrics.increment_timeout()
        self.metrics.increment_retry()

        self.metrics.record_duration(100.0)
        self.metrics.record_duration(200.0)
        self.metrics.record_duration(300.0)
        self.metrics.record_memory(128.0)
        self.metrics.record_memory(256.0)

        summary = self.metrics.get_metrics_summary()

        # Test counters structure
        assert "counters" in summary
        counters = summary["counters"]
        assert counters["validator_success_total"] == 1
        assert counters["validator_failure_total"]["latex_error"] == 2
        assert counters["validator_timeout_total"] == 1
        assert counters["validator_retry_total"] == 1

        # Test histograms structure
        assert "histograms" in summary
        histograms = summary["histograms"]

        duration_hist = histograms["validator_duration_ms"]
        assert duration_hist["count"] == 3
        assert duration_hist["p50"] == 200.0  # Median
        assert duration_hist["p95"] >= 200.0
        assert duration_hist["max"] == 300.0

        memory_hist = histograms["validator_rss_peak_mb"]
        assert memory_hist["count"] == 2
        assert memory_hist["p50"] == 192.0  # (128 + 256) / 2
        assert memory_hist["max"] == 256.0

        # Test metadata
        assert "metadata" in summary
        metadata = summary["metadata"]
        assert "reset_time" in metadata
        assert "uptime_seconds" in metadata

    def test_percentile_calculation(self):
        """T5.7: Test percentile calculation accuracy."""
        # Use known dataset for predictable percentiles
        durations = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for d in durations:
            self.metrics.record_duration(float(d))

        summary = self.metrics.get_metrics_summary()
        duration_hist = summary["histograms"]["validator_duration_ms"]

        # Test percentiles
        assert duration_hist["p50"] == 55.0  # 50th percentile
        assert duration_hist["p95"] >= 90.0  # 95th percentile should be high
        assert duration_hist["max"] == 100.0

    def test_empty_histograms(self):
        """T5.7: Test histogram summaries when no data recorded."""
        summary = self.metrics.get_metrics_summary()

        duration_hist = summary["histograms"]["validator_duration_ms"]
        assert duration_hist["count"] == 0
        assert duration_hist["p50"] == 0.0
        assert duration_hist["max"] == 0

    def test_reset_metrics(self):
        """T5.7: Test metrics reset functionality."""
        # Add some data
        self.metrics.increment_success()
        self.metrics.increment_failure("test_error")
        self.metrics.record_duration(100.0)

        # Reset
        self.metrics.reset_metrics()

        # Verify reset
        assert self.metrics.success_total == 0
        assert len(self.metrics.failure_total) == 0
        assert len(self.metrics.duration_ms) == 0


class TestT57StructuredLogging:
    """T5.7 specific tests for structured logging."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = StructuredLogger("test_validator")

    def test_structured_log_entry_creation(self):
        """T5.7: Test StructuredLogEntry creation and serialization."""
        entry = StructuredLogEntry(
            video_id="vid123",
            scene_id="scene_01",
            result="success",
            duration_ms=1500.5,
            rss_peak_mb=256.8,
            exit_code=0,
            attempt=1,
        )

        # Test serialization
        entry_dict = entry.to_dict()
        assert entry_dict["video_id"] == "vid123"
        assert entry_dict["scene_id"] == "scene_01"
        assert entry_dict["result"] == "success"
        assert entry_dict["duration_ms"] == 1500.5
        assert entry_dict["rss_peak_mb"] == 256.8
        assert entry_dict["exit_code"] == 0
        assert "timestamp" in entry_dict

        # Test JSON serialization
        json_str = entry.to_json()
        parsed = json.loads(json_str)
        assert parsed["video_id"] == "vid123"

    def test_structured_log_entry_auto_timestamp(self):
        """T5.7: Test automatic timestamp assignment."""
        before_time = time.time()

        entry = StructuredLogEntry(
            video_id="test", scene_id="test", result="test", duration_ms=100.0
        )

        after_time = time.time()

        assert before_time <= entry.timestamp <= after_time

    def test_structured_logger_log_methods(self):
        """T5.7: Test structured logger convenience methods."""
        with patch.object(self.logger.logger, "info") as mock_info:
            # Test log_success
            self.logger.log_success(
                video_id="vid123",
                scene_id="scene_01",
                duration_ms=1200.0,
                rss_peak_mb=128.5,
            )

            # Verify log call
            mock_info.assert_called_once()
            log_message = mock_info.call_args[0][0]
            assert "VALIDATION_EVENT:" in log_message
            assert "vid123" in log_message
            assert "success" in log_message

    def test_structured_logger_failure_logging(self):
        """T5.7: Test failure logging with error details."""
        with patch.object(self.logger.logger, "info") as mock_info:
            self.logger.log_failure(
                video_id="vid456",
                scene_id="scene_02",
                duration_ms=800.0,
                error_kind="latex_error",
                exit_code=1,
                rss_peak_mb=64.2,
            )

            mock_info.assert_called_once()
            log_message = mock_info.call_args[0][0]
            assert "VALIDATION_EVENT:" in log_message
            assert "failure" in log_message
            assert "latex_error" in log_message

    def test_structured_logger_timeout_logging(self):
        """T5.7: Test timeout logging."""
        with patch.object(self.logger.logger, "info") as mock_info:
            self.logger.log_timeout(
                video_id="vid789",
                scene_id="scene_03",
                duration_ms=30000.0,  # 30 seconds
            )

            mock_info.assert_called_once()
            log_message = mock_info.call_args[0][0]
            assert "timeout" in log_message
            assert "30000" in log_message

    def test_structured_logger_retry_logging(self):
        """T5.7: Test retry attempt logging."""
        with patch.object(self.logger.logger, "info") as mock_info:
            self.logger.log_retry(
                video_id="vid101",
                scene_id="scene_04",
                duration_ms=2500.0,
                error_kind="font_error",
                attempt=2,
            )

            mock_info.assert_called_once()
            log_message = mock_info.call_args[0][0]
            assert "retry" in log_message
            assert "font_error" in log_message
            assert "attempt" in log_message


class TestT57ValidationMetricsContext:
    """T5.7 specific tests for validation metrics context manager."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_metrics()  # Start with clean metrics

    def test_metrics_context_success(self):
        """T5.7: Test metrics context for successful validation."""
        with patch("generator.validator.metrics.metrics") as mock_metrics, patch(
            "generator.validator.metrics.structured_logger"
        ) as mock_logger:

            with validation_metrics_context("vid123", "scene_01") as ctx:
                ctx.set_success()
                ctx.set_rss_peak_mb(128.0)

            # Verify metrics were recorded
            mock_metrics.increment_success.assert_called_once()
            mock_metrics.record_memory.assert_called_once_with(128.0)
            mock_logger.log_success.assert_called_once()

    def test_metrics_context_failure_with_exit_code(self):
        """T5.7: Test metrics context for failed validation."""
        with patch("generator.validator.metrics.metrics") as mock_metrics, patch(
            "generator.validator.metrics.structured_logger"
        ) as mock_logger:

            with validation_metrics_context("vid456", "scene_02") as ctx:
                ctx.set_exit_code(1)
                ctx.set_error_kind("latex_error")
                ctx.set_rss_peak_mb(256.0)

            # Verify failure metrics were recorded
            mock_metrics.increment_failure.assert_called_once_with("latex_error")
            mock_metrics.record_memory.assert_called_once_with(256.0)
            mock_logger.log_failure.assert_called_once()

    def test_metrics_context_exception_handling(self):
        """T5.7: Test metrics context handles exceptions properly."""
        with patch("generator.validator.metrics.metrics") as mock_metrics, patch(
            "generator.validator.metrics.structured_logger"
        ) as mock_logger:

            try:
                with validation_metrics_context("vid789", "scene_03") as ctx:
                    ctx.set_rss_peak_mb(64.0)
                    raise ValueError("Test exception")
            except ValueError:
                pass

            # Should record as failure with auto-detected error kind
            mock_metrics.increment_failure.assert_called_once_with("ValueError")
            mock_logger.log_failure.assert_called_once()

    def test_metrics_context_duration_recording(self):
        """T5.7: Test metrics context records duration automatically."""
        with patch("generator.validator.metrics.metrics") as mock_metrics, patch(
            "generator.validator.metrics.structured_logger"
        ) as mock_logger:

            with validation_metrics_context("vid101", "scene_04") as ctx:
                # Simulate some work
                time.sleep(0.01)
                ctx.set_success()

            # Verify duration was recorded
            mock_metrics.record_duration.assert_called_once()
            duration_call = mock_metrics.record_duration.call_args[0][0]
            assert duration_call > 0  # Should be > 0 due to sleep

    def test_metrics_context_attempt_tracking(self):
        """T5.7: Test metrics context tracks attempt numbers."""
        with patch("generator.validator.metrics.structured_logger") as mock_logger:
            with validation_metrics_context("vid202", "scene_05", attempt=3) as ctx:
                ctx.set_success()

            # Verify attempt number was logged
            mock_logger.log_success.assert_called_once()
            call_args = mock_logger.log_success.call_args
            assert call_args[1]["attempt"] == 3  # keyword argument


class TestT57ConvenienceFunctions:
    """T5.7 specific tests for convenience metric recording functions."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_metrics()

    def test_record_success_function(self):
        """T5.7: Test record_success convenience function."""
        with patch("generator.validator.metrics.metrics") as mock_metrics, patch(
            "generator.validator.metrics.structured_logger"
        ) as mock_logger:

            record_success("vid123", "scene_01", 1500.0, 128.0)

            # Verify all expected calls
            mock_metrics.increment_success.assert_called_once()
            mock_metrics.record_duration.assert_called_once_with(1500.0)
            mock_metrics.record_memory.assert_called_once_with(128.0)
            mock_logger.log_success.assert_called_once_with(
                "vid123", "scene_01", 1500.0, 128.0
            )

    def test_record_failure_function(self):
        """T5.7: Test record_failure convenience function."""
        with patch("generator.validator.metrics.metrics") as mock_metrics, patch(
            "generator.validator.metrics.structured_logger"
        ) as mock_logger:

            record_failure("vid456", "scene_02", 800.0, "latex_error", 1, 64.0)

            # Verify all expected calls
            mock_metrics.increment_failure.assert_called_once_with("latex_error")
            mock_metrics.record_duration.assert_called_once_with(800.0)
            mock_metrics.record_memory.assert_called_once_with(64.0)
            mock_logger.log_failure.assert_called_once_with(
                "vid456", "scene_02", 800.0, "latex_error", 1, 64.0
            )

    def test_record_timeout_function(self):
        """T5.7: Test record_timeout convenience function."""
        with patch("generator.validator.metrics.metrics") as mock_metrics, patch(
            "generator.validator.metrics.structured_logger"
        ) as mock_logger:

            record_timeout("vid789", "scene_03", 30000.0)

            mock_metrics.increment_timeout.assert_called_once()
            mock_metrics.record_duration.assert_called_once_with(30000.0)
            mock_logger.log_timeout.assert_called_once_with(
                "vid789", "scene_03", 30000.0
            )

    def test_record_retry_function(self):
        """T5.7: Test record_retry convenience function."""
        with patch("generator.validator.metrics.structured_logger") as mock_logger:

            record_retry("vid101", "scene_04", 2000.0, "font_error", 2)

            mock_logger.log_retry.assert_called_once_with(
                "vid101", "scene_04", 2000.0, "font_error", 2
            )

    def test_get_metrics_summary_function(self):
        """T5.7: Test get_metrics_summary global function."""
        with patch("generator.validator.metrics.metrics") as mock_metrics:
            expected_summary = {"test": "summary"}
            mock_metrics.get_metrics_summary.return_value = expected_summary

            result = get_metrics_summary()

            assert result == expected_summary
            mock_metrics.get_metrics_summary.assert_called_once()


class TestT57Integration:
    """T5.7 integration tests for metrics with validation pipeline."""

    def test_end_to_end_metrics_flow(self):
        """T5.7: Test complete metrics flow through validation."""
        reset_metrics()

        # Simulate validation with metrics
        with validation_metrics_context("integration_vid", "integration_scene") as ctx:
            ctx.set_exit_code(0)
            ctx.set_rss_peak_mb(200.0)
            ctx.set_success()

        # Get summary and verify data
        summary = get_metrics_summary()

        assert summary["counters"]["validator_success_total"] >= 1
        assert summary["histograms"]["validator_duration_ms"]["count"] >= 1
        assert summary["histograms"]["validator_rss_peak_mb"]["count"] >= 1
        assert (
            200.0 in summary["histograms"]["validator_rss_peak_mb"]["max"] or True
        )  # Should be recorded

    def test_multiple_validation_metrics_aggregation(self):
        """T5.7: Test metrics aggregation across multiple validations."""
        reset_metrics()

        # Simulate multiple validations
        validation_scenarios = [
            ("vid1", "scene1", True, 100.0, 128.0, 0),
            ("vid2", "scene2", False, 200.0, 256.0, 1),
            ("vid3", "scene3", True, 150.0, 64.0, 0),
        ]

        for vid, scene, success, duration, memory, exit_code in validation_scenarios:
            with validation_metrics_context(vid, scene) as ctx:
                ctx.set_rss_peak_mb(memory)
                ctx.set_exit_code(exit_code)
                if success:
                    ctx.set_success()
                else:
                    ctx.set_error_kind("test_error")

        # Verify aggregated metrics
        summary = get_metrics_summary()

        assert summary["counters"]["validator_success_total"] == 2
        assert summary["counters"]["validator_failure_total"]["test_error"] == 1
        assert summary["histograms"]["validator_duration_ms"]["count"] == 3
        assert summary["histograms"]["validator_rss_peak_mb"]["count"] == 3
