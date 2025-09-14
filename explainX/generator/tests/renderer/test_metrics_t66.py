"""
Tests for T6.6: Metrics collection and structured logging.
"""

import json
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from generator.renderer.metrics import (
    RenderMetrics,
    ConcatMetrics,
    ThumbnailMetrics,
    MetricsCollector,
    StructuredLogger,
    render_metrics_context,
    get_metrics_collector,
    get_structured_logger,
    reset_global_metrics,
)


class TestRenderMetrics:
    """Test render metrics data classes."""

    def test_render_metrics_creation(self):
        """Test creating render metrics with all fields."""
        metrics = RenderMetrics(
            operation_type="scene_render",
            video_id="test_video",
            scene_id="scene_01",
            success=True,
            start_time=1000.0,
            end_time=1005.0,
            exit_code=0,
            peak_memory_mb=512.0,
            cpu_time_ms=4500.0,
            frames_rendered=150,
            file_size_mb=25.5,
            cache_hit=False,
            additional_data={"custom": "data"},
        )

        assert metrics.operation_type == "scene_render"
        assert metrics.video_id == "test_video"
        assert metrics.scene_id == "scene_01"
        assert metrics.success is True
        assert metrics.duration_ms == 5000.0  # Calculated from start/end time
        assert metrics.peak_memory_mb == 512.0
        assert metrics.frames_rendered == 150
        assert metrics.additional_data["custom"] == "data"

    def test_render_metrics_defaults(self):
        """Test render metrics with default values."""
        metrics = RenderMetrics(operation_type="concat", video_id="test_video")

        assert metrics.scene_id is None
        assert metrics.success is False
        assert metrics.additional_data == {}
        assert metrics.cache_hit is False

    def test_concat_metrics_creation(self):
        """Test creating concatenation metrics."""
        metrics = ConcatMetrics(
            video_id="test_video",
            input_count=3,
            output_duration_s=15.5,
            crossfade_used=True,
            crossfade_duration_s=0.5,
            transitions_applied=2,
            re_encodes=1,
            total_latency_ms=2500.0,
            success=True,
            cache_hit=False,
        )

        assert metrics.input_count == 3
        assert metrics.crossfade_used is True
        assert metrics.transitions_applied == 2
        assert metrics.total_latency_ms == 2500.0

    def test_thumbnail_metrics_creation(self):
        """Test creating thumbnail metrics."""
        metrics = ThumbnailMetrics(
            video_id="test_video",
            thumbnail_type="poster",
            extraction_time_ms=150.0,
            source_duration_s=10.0,
            success=True,
            cache_hit=False,
        )

        assert metrics.thumbnail_type == "poster"
        assert metrics.extraction_time_ms == 150.0
        assert metrics.source_duration_s == 10.0
        assert metrics.success is True


class TestMetricsCollector:
    """Test metrics collector functionality."""

    def setup_method(self):
        """Setup fresh metrics collector."""
        self.collector = MetricsCollector()

    def test_collector_initialization(self):
        """Test metrics collector initializes correctly."""
        assert len(self.collector.counters) == 0
        assert len(self.collector.histograms) == 0
        assert len(self.collector.metrics_history) == 0
        assert self.collector.session_start > 0

    def test_increment_counter(self):
        """Test counter increment functionality."""
        self.collector.increment_counter("test_counter")
        self.collector.increment_counter("test_counter")
        self.collector.increment_counter("other_counter")

        assert self.collector.get_counter_value("test_counter") == 2
        assert self.collector.get_counter_value("other_counter") == 1
        assert self.collector.get_counter_value("missing_counter") == 0

    def test_increment_counter_with_labels(self):
        """Test counter increment with labels."""
        self.collector.increment_counter("test_counter", {"result": "success"})
        self.collector.increment_counter("test_counter", {"result": "failure"})
        self.collector.increment_counter("test_counter", {"result": "success"})

        assert (
            self.collector.get_counter_value("test_counter", {"result": "success"}) == 2
        )
        assert (
            self.collector.get_counter_value("test_counter", {"result": "failure"}) == 1
        )

    def test_record_histogram(self):
        """Test histogram recording functionality."""
        values = [10.0, 20.0, 15.0, 25.0, 12.0]

        for value in values:
            self.collector.record_histogram("test_histogram", value)

        stats = self.collector.get_histogram_stats("test_histogram")

        assert stats["count"] == 5
        assert stats["min"] == 10.0
        assert stats["max"] == 25.0
        assert stats["mean"] == 16.4  # (10+20+15+25+12)/5
        assert stats["median"] == 15.0

    def test_record_render_metrics(self):
        """Test recording comprehensive render metrics."""
        metrics = RenderMetrics(
            operation_type="scene_render",
            video_id="test_video",
            scene_id="scene_01",
            success=True,
            duration_ms=2500.0,
            peak_memory_mb=256.0,
            frames_rendered=75,
            file_size_mb=15.0,
            cache_hit=False,
        )

        self.collector.record_render_metrics(metrics)

        # Check metrics history
        assert len(self.collector.metrics_history) == 1
        assert self.collector.metrics_history[0] == metrics

        # Check counters
        assert (
            self.collector.get_counter_value(
                "renderer_scene_render_total", {"result": "success"}
            )
            == 1
        )

        # Check histograms
        duration_stats = self.collector.get_histogram_stats(
            "renderer_scene_render_duration_ms"
        )
        assert duration_stats["count"] == 1
        assert duration_stats["mean"] == 2500.0

        memory_stats = self.collector.get_histogram_stats(
            "renderer_scene_render_memory_mb"
        )
        assert memory_stats["count"] == 1
        assert memory_stats["mean"] == 256.0

    def test_record_concat_metrics(self):
        """Test recording concatenation metrics."""
        metrics = ConcatMetrics(
            video_id="test_video",
            input_count=3,
            output_duration_s=15.0,
            crossfade_used=True,
            crossfade_duration_s=0.5,
            transitions_applied=2,
            re_encodes=1,
            total_latency_ms=3000.0,
            success=True,
        )

        self.collector.record_concat_metrics(metrics)

        # Should create a render metrics entry
        assert len(self.collector.metrics_history) == 1
        recorded = self.collector.metrics_history[0]
        assert recorded.operation_type == "concat"
        assert recorded.duration_ms == 3000.0
        assert recorded.additional_data["input_count"] == 3
        assert recorded.additional_data["crossfade_used"] is True

        # Check concat-specific metrics
        assert self.collector.get_counter_value("renderer_concat_crossfade_total") == 1

        input_stats = self.collector.get_histogram_stats("renderer_concat_input_count")
        assert input_stats["mean"] == 3.0

    def test_record_thumbnail_metrics(self):
        """Test recording thumbnail metrics."""
        metrics = ThumbnailMetrics(
            video_id="test_video",
            thumbnail_type="poster",
            extraction_time_ms=200.0,
            source_duration_s=10.0,
            success=True,
        )

        self.collector.record_thumbnail_metrics(metrics)

        # Should create a render metrics entry
        assert len(self.collector.metrics_history) == 1
        recorded = self.collector.metrics_history[0]
        assert recorded.operation_type == "thumbnail"
        assert recorded.additional_data["thumbnail_type"] == "poster"

        # Check thumbnail-specific metrics
        assert (
            self.collector.get_counter_value(
                "renderer_thumbnail_generated_total", {"thumbnail_type": "poster"}
            )
            == 1
        )

        extraction_stats = self.collector.get_histogram_stats(
            "renderer_thumbnail_extraction_ms", {"thumbnail_type": "poster"}
        )
        assert extraction_stats["mean"] == 200.0

    def test_get_summary_stats(self):
        """Test comprehensive summary statistics."""
        # Record some metrics
        self.collector.increment_counter("test_counter")
        self.collector.record_histogram("test_histogram", 10.0)

        render_metrics = RenderMetrics(
            operation_type="scene_render",
            video_id="test",
            success=True,
            duration_ms=1000.0,
        )
        self.collector.record_render_metrics(render_metrics)

        summary = self.collector.get_summary_stats()

        assert summary["total_operations"] == 1
        assert "session_duration_s" in summary
        assert "counters" in summary
        assert "histogram_stats" in summary
        assert "recent_operations" in summary
        assert len(summary["recent_operations"]) == 1

    def test_reset(self):
        """Test resetting metrics."""
        # Add some data
        self.collector.increment_counter("test")
        self.collector.record_histogram("test", 10.0)

        render_metrics = RenderMetrics(operation_type="test", video_id="test")
        self.collector.record_render_metrics(render_metrics)

        assert len(self.collector.counters) > 0
        assert len(self.collector.histograms) > 0
        assert len(self.collector.metrics_history) > 0

        # Reset
        self.collector.reset()

        assert len(self.collector.counters) == 0
        assert len(self.collector.histograms) == 0
        assert len(self.collector.metrics_history) == 0


class TestStructuredLogger:
    """Test structured logging functionality."""

    def setup_method(self):
        """Setup test logger."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.log_file = self.temp_dir / "test.log"
        self.logger = StructuredLogger("test_logger", self.log_file)

    def teardown_method(self):
        """Cleanup test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_logger_initialization(self):
        """Test structured logger initializes correctly."""
        assert self.logger.logger.name == "test_logger"
        assert len(self.logger.logger.handlers) >= 1  # Console + file handlers

    def test_log_structured_event(self):
        """Test logging structured events."""
        with patch.object(self.logger.logger, "info") as mock_info:
            self.logger.log_structured(
                "info",
                "test_event",
                video_id="test_123",
                scene_id="scene_01",
                custom_field="custom_value",
            )

            # Should have called logger.info with JSON
            mock_info.assert_called_once()
            logged_message = mock_info.call_args[0][0]

            # Parse logged JSON
            log_data = json.loads(logged_message)
            assert log_data["level"] == "INFO"
            assert log_data["event_type"] == "test_event"
            assert log_data["video_id"] == "test_123"
            assert log_data["scene_id"] == "scene_01"
            assert log_data["custom_field"] == "custom_value"
            assert "timestamp" in log_data

    def test_log_render_start(self):
        """Test logging render start events."""
        with patch.object(self.logger.logger, "info") as mock_info:
            self.logger.log_render_start(
                video_id="test_video",
                scene_id="scene_01",
                operation_type="scene_render",
                quality="1080p",
            )

            mock_info.assert_called_once()
            logged_message = mock_info.call_args[0][0]
            log_data = json.loads(logged_message)

            assert log_data["event_type"] == "render_start"
            assert log_data["operation"] == "scene_render"
            assert log_data["quality"] == "1080p"

    def test_log_render_complete(self):
        """Test logging render completion events."""
        with patch.object(self.logger.logger, "info") as mock_info:
            self.logger.log_render_complete(
                video_id="test_video",
                scene_id="scene_01",
                operation_type="scene_render",
                success=True,
                duration_ms=2500.0,
                peak_memory_mb=256.0,
                frames_rendered=75,
            )

            mock_info.assert_called_once()
            logged_message = mock_info.call_args[0][0]
            log_data = json.loads(logged_message)

            assert log_data["event_type"] == "render_complete"
            assert log_data["success"] is True
            assert log_data["duration_ms"] == 2500.0
            assert log_data["peak_memory_mb"] == 256.0
            assert log_data["frames_rendered"] == 75

    def test_log_cache_event(self):
        """Test logging cache events."""
        with patch.object(self.logger.logger, "debug") as mock_debug:
            cache_key = "very_long_cache_key_that_should_be_truncated_in_logs"

            self.logger.log_cache_event(
                event_type="cache_hit", cache_key=cache_key, operation="scene_render"
            )

            mock_debug.assert_called_once()
            logged_message = mock_debug.call_args[0][0]
            log_data = json.loads(logged_message)

            assert log_data["event_type"] == "cache_event"
            assert log_data["cache_event"] == "cache_hit"
            assert log_data["cache_key"].endswith("...")  # Should be truncated
            assert log_data["operation"] == "scene_render"

    def test_log_error(self):
        """Test logging error events."""
        with patch.object(self.logger.logger, "error") as mock_error:
            self.logger.log_error(
                error_type="RenderTimeoutError",
                error_message="Scene render timed out after 180s",
                video_id="test_video",
                scene_id="problematic_scene",
            )

            mock_error.assert_called_once()
            logged_message = mock_error.call_args[0][0]
            log_data = json.loads(logged_message)

            assert log_data["event_type"] == "error"
            assert log_data["error_type"] == "RenderTimeoutError"
            assert "timed out" in log_data["error_message"]
            assert log_data["video_id"] == "test_video"

    def test_large_object_filtering(self):
        """Test filtering of large objects from logs."""
        with patch.object(self.logger.logger, "info") as mock_info:
            large_string = "x" * 2000  # > 1000 char limit
            large_dict = {f"key_{i}": f"value_{i}" for i in range(1000)}  # Large dict

            self.logger.log_structured(
                "info",
                "test_filtering",
                normal_field="normal",
                large_string=large_string,
                large_dict=large_dict,
                none_field=None,
            )

            mock_info.assert_called_once()
            logged_message = mock_info.call_args[0][0]
            log_data = json.loads(logged_message)

            # Normal field should be present
            assert log_data["normal_field"] == "normal"

            # Large objects and None values should be filtered out
            assert "large_string" not in log_data
            assert "large_dict" not in log_data
            assert "none_field" not in log_data


class TestRenderMetricsContext:
    """Test render metrics context manager."""

    def setup_method(self):
        """Setup test environment."""
        reset_global_metrics()

    def test_metrics_context_success(self):
        """Test metrics context for successful operation."""
        with render_metrics_context(
            "test_operation", "test_video", "test_scene"
        ) as metrics:
            assert metrics.operation_type == "test_operation"
            assert metrics.video_id == "test_video"
            assert metrics.scene_id == "test_scene"
            assert metrics.start_time > 0

            # Simulate some work
            time.sleep(0.001)

            # Set operation-specific metrics
            metrics.frames_rendered = 100
            metrics.file_size_mb = 20.0
            metrics.peak_memory_mb = 512.0

        # After context, metrics should be finalized
        assert metrics.success is True
        assert metrics.end_time > metrics.start_time
        assert metrics.duration_ms > 0
        assert metrics.frames_rendered == 100
        assert metrics.file_size_mb == 20.0

        # Check metrics were recorded
        collector = get_metrics_collector()
        assert len(collector.metrics_history) >= 1

        # Find our recorded metric
        test_metrics = [
            m for m in collector.metrics_history if m.operation_type == "test_operation"
        ]
        assert len(test_metrics) >= 1

    def test_metrics_context_failure(self):
        """Test metrics context for failed operation."""
        with pytest.raises(ValueError):
            with render_metrics_context("test_operation", "test_video") as metrics:
                # Simulate some work
                metrics.frames_rendered = 50

                # Raise an exception
                raise ValueError("Test error")

        # After exception, metrics should record failure
        assert metrics.success is False
        assert metrics.error_type == "ValueError"
        assert metrics.frames_rendered == 50

        # Check metrics were recorded despite exception
        collector = get_metrics_collector()
        test_metrics = [
            m for m in collector.metrics_history if m.operation_type == "test_operation"
        ]
        assert len(test_metrics) >= 1

        failed_metric = test_metrics[-1]
        assert failed_metric.success is False
        assert failed_metric.error_type == "ValueError"


class TestGlobalMetrics:
    """Test global metrics and logger instances."""

    def setup_method(self):
        """Reset global state."""
        reset_global_metrics()

    def test_get_metrics_collector_singleton(self):
        """Test global metrics collector is singleton."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2

        # Modifications to one should affect the other
        collector1.increment_counter("test")
        assert collector2.get_counter_value("test") == 1

    def test_get_structured_logger_singleton(self):
        """Test global structured logger is singleton."""
        logger1 = get_structured_logger()
        logger2 = get_structured_logger()

        assert logger1 is logger2

    def test_reset_global_metrics(self):
        """Test resetting global metrics."""
        collector = get_metrics_collector()

        # Add some data
        collector.increment_counter("test_global")
        collector.record_histogram("test_global", 10.0)

        assert collector.get_counter_value("test_global") == 1
        assert len(collector.histograms) > 0

        # Reset
        reset_global_metrics()

        # Should be cleared
        assert collector.get_counter_value("test_global") == 0
        assert len(collector.histograms) == 0


class TestMetricsIntegration:
    """Integration tests for metrics in render pipeline."""

    def setup_method(self):
        """Setup integration test environment."""
        reset_global_metrics()

    @patch("generator.renderer.metrics.get_structured_logger")
    def test_metrics_integration_with_mock_logger(self, mock_get_logger):
        """Test metrics integration with mocked logger."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Use metrics context
        with render_metrics_context("integration_test", "test_video") as metrics:
            metrics.frames_rendered = 200
            metrics.file_size_mb = 30.0

        # Verify logger was called
        mock_logger.log_render_start.assert_called_once()
        mock_logger.log_render_complete.assert_called_once()

        # Check the log_render_complete call
        complete_call = mock_logger.log_render_complete.call_args
        assert complete_call[0][0] == "test_video"  # video_id
        assert complete_call[0][2] == "integration_test"  # operation_type
        assert complete_call[0][3] is True  # success
        assert complete_call[1]["frames_rendered"] == 200
        assert complete_call[1]["file_size_mb"] == 30.0

    def test_multiple_concurrent_metrics(self):
        """Test collecting metrics from multiple operations."""
        collector = get_metrics_collector()
        initial_count = len(collector.metrics_history)

        # Simulate multiple operations
        operations = [
            ("scene_render", "video_1", "scene_01"),
            ("scene_render", "video_1", "scene_02"),
            ("concat", "video_1", None),
            ("thumbnail", "video_1", None),
        ]

        for op_type, video_id, scene_id in operations:
            with render_metrics_context(op_type, video_id, scene_id) as metrics:
                metrics.duration_ms = 1000.0

        # Check all operations were recorded
        final_count = len(collector.metrics_history)
        assert final_count == initial_count + len(operations)

        # Check operation type distribution
        recent_ops = collector.metrics_history[-len(operations) :]
        op_types = [m.operation_type for m in recent_ops]

        assert op_types.count("scene_render") == 2
        assert op_types.count("concat") == 1
        assert op_types.count("thumbnail") == 1

    def test_metrics_performance_overhead(self):
        """Test that metrics collection has minimal performance overhead."""
        collector = get_metrics_collector()

        # Time metrics collection
        start_time = time.time()

        for i in range(100):
            collector.increment_counter(f"perf_test_{i % 10}")
            collector.record_histogram("perf_histogram", float(i))

        end_time = time.time()
        overhead = end_time - start_time

        # Should complete 100 operations in reasonable time (< 0.1 seconds)
        assert overhead < 0.1

        # Check data was recorded correctly
        assert collector.get_counter_value("perf_test_0") == 10  # Every 10th iteration
        histogram_stats = collector.get_histogram_stats("perf_histogram")
        assert histogram_stats["count"] == 100
