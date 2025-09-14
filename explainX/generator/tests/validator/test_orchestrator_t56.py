"""
Comprehensive T5.6 tests for orchestration glue and retry behavior.
Tests flaky error detection, retry policies, and NeedsRepair handling.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from generator.validator.orchestrator import (
    orchestrate_validation,
    validate_scene_with_orchestration,
    _should_retry,
    FLAKY_ERROR_PATTERNS,
    FLAKY_EXIT_CODES,
    NO_RETRY_ERROR_TYPES,
)
from generator.validator.errors import (
    ValidationError,
    SourceSafetyError,
    NeedsRepair,
    RunnerTimeoutError,
    RunnerOOMError,
    RunnerExecutionError,
)
from generator.validator import ValidateInput, ValidateResult
from generator.style.models import ColorPalette, StylePack


class TestT56Orchestration:
    """T5.6 specific tests for orchestration with retry policies."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.colors = ColorPalette(
            primary_text="#000000", background="#FFFFFF", accent="#2563EB"
        )
        self.style = StylePack(version="1.0", name="test", colors=self.colors)

        self.valid_scene = {
            "scene_id": "test_scene",
            "timeline": [{"op": "title", "text": "Test", "pos": "center"}],
        }

        self.safe_source = """from manim import *
class Scene_Test(Scene):
    def construct(self):
        title = Text("Test", font=BODY_FONT)
        self.play(Write(title))"""

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)

    def _create_validate_input(
        self, scene_json=None, source_text=None
    ) -> ValidateInput:
        """Create ValidateInput for testing."""
        return ValidateInput(
            video_id="test_video",
            scene_id="test_scene",
            scene_json=scene_json or self.valid_scene,
            style=self.style,
            source_text=source_text or self.safe_source,
            class_name="Scene_Test",
            work_dir=self.temp_dir,
        )

    def test_successful_orchestration(self):
        """T5.6: Test successful validation through complete orchestration."""
        vin = self._create_validate_input()

        # Mock all components to succeed
        with patch("generator.validator.orchestrator.validate_scene_json"), patch(
            "generator.validator.orchestrator.validate_style_pack"
        ), patch("generator.validator.orchestrator.validate_source_safety"), patch(
            "generator.validator.orchestrator.run_manim_preview"
        ) as mock_runner:

            # Mock successful Manim execution
            mock_artifacts = Mock()
            mock_artifacts.preview_mp4 = self.temp_dir / "preview.mp4"
            mock_artifacts.first_frame_png = self.temp_dir / "frame0.png"

            mock_runner.return_value = (
                mock_artifacts,
                {"resource_usage": {"exit_code": 0, "rss_peak_mb": 128.0}},
                [],  # No issues
            )

            # Test orchestration
            result = orchestrate_validation(vin)

            assert result.ok is True
            assert result.preview_mp4 == mock_artifacts.preview_mp4
            assert result.first_frame_png == mock_artifacts.first_frame_png
            assert "success" in result.logs
            assert result.logs["success"] is True

    def test_validation_error_no_retry(self):
        """T5.6: Test that validation errors are not retried."""
        vin = self._create_validate_input()

        with patch(
            "generator.validator.orchestrator.validate_scene_json"
        ) as mock_validate:
            mock_validate.side_effect = ValidationError("timeline", "Invalid timeline")

            # Should raise NeedsRepair without retry
            with pytest.raises(NeedsRepair) as exc_info:
                orchestrate_validation(vin)

            payload = exc_info.value.payload
            assert payload["scene_id"] == "test_scene"
            assert len(payload["errors"]) == 1
            assert payload["errors"][0]["kind"] == "validation_error"

            # Should only call validate_scene_json once (no retry)
            assert mock_validate.call_count == 1

    def test_source_safety_error_no_retry(self):
        """T5.6: Test that source safety errors are not retried."""
        vin = self._create_validate_input()

        with patch("generator.validator.orchestrator.validate_scene_json"), patch(
            "generator.validator.orchestrator.validate_style_pack"
        ), patch(
            "generator.validator.orchestrator.validate_source_safety"
        ) as mock_safety:

            mock_safety.side_effect = SourceSafetyError(
                "source", "Unsafe import detected"
            )

            # Should raise NeedsRepair without retry
            with pytest.raises(NeedsRepair) as exc_info:
                orchestrate_validation(vin)

            payload = exc_info.value.payload
            assert payload["scene_id"] == "test_scene"
            assert len(payload["errors"]) == 1
            assert payload["errors"][0]["kind"] == "source_safety"

            # Should only call validate_source_safety once (no retry)
            assert mock_safety.call_count == 1

    def test_flaky_latex_error_with_retry_success(self):
        """T5.6: Test flaky LaTeX error triggers retry and succeeds on second attempt."""
        vin = self._create_validate_input()

        call_count = 0

        def mock_runner_flaky(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First call: fail with flaky LaTeX error
                return (
                    None,
                    {
                        "stderr": "LaTeX Error: emergency stop",
                        "resource_usage": {"exit_code": 1, "rss_peak_mb": 128.0},
                    },
                    [
                        {
                            "type": "latex_error",
                            "kind": "latex_error",
                            "field": "timeline[0].latex",
                            "message": "LaTeX compilation failed: emergency stop",
                            "severity": "error",
                        }
                    ],
                )
            else:
                # Second call: succeed
                mock_artifacts = Mock()
                mock_artifacts.preview_mp4 = self.temp_dir / "preview.mp4"
                mock_artifacts.first_frame_png = self.temp_dir / "frame0.png"

                return (
                    mock_artifacts,
                    {"resource_usage": {"exit_code": 0, "rss_peak_mb": 128.0}},
                    [],
                )

        with patch("generator.validator.orchestrator.validate_scene_json"), patch(
            "generator.validator.orchestrator.validate_style_pack"
        ), patch("generator.validator.orchestrator.validate_source_safety"), patch(
            "generator.validator.orchestrator.run_manim_preview",
            side_effect=mock_runner_flaky,
        ):

            # Test orchestration with retry
            result = orchestrate_validation(vin)

            assert result.ok is True
            assert call_count == 2  # Should have been called twice

    def test_flaky_font_warning_with_retry_failure(self):
        """T5.6: Test flaky font error retries but still fails."""
        vin = self._create_validate_input()

        def mock_runner_consistently_flaky(*args, **kwargs):
            # Always fail with flaky font error
            return (
                None,
                {
                    "stderr": "font warning: could not load font",
                    "resource_usage": {"exit_code": 1, "rss_peak_mb": 128.0},
                },
                [
                    {
                        "type": "font_error",
                        "kind": "font_error",
                        "field": "rendering",
                        "message": "Font loading failed",
                        "severity": "error",
                    }
                ],
            )

        with patch("generator.validator.orchestrator.validate_scene_json"), patch(
            "generator.validator.orchestrator.validate_style_pack"
        ), patch("generator.validator.orchestrator.validate_source_safety"), patch(
            "generator.validator.orchestrator.run_manim_preview",
            side_effect=mock_runner_consistently_flaky,
        ):

            # Should retry once then raise NeedsRepair
            with pytest.raises(NeedsRepair) as exc_info:
                orchestrate_validation(vin)

            payload = exc_info.value.payload
            assert payload["scene_id"] == "test_scene"
            assert "font warning" in payload["stderr_excerpt"]

    def test_should_retry_logic_flaky_patterns(self):
        """T5.6: Test _should_retry logic for various flaky patterns."""
        # Test flaky exit codes
        assert (
            _should_retry(
                [{"type": "some_error", "kind": "some_error", "severity": "error"}],
                {"resource_usage": {"exit_code": 1}},  # Flaky exit code
            )
            is True
        )

        # Test flaky error patterns in stderr
        for pattern in FLAKY_ERROR_PATTERNS[:3]:  # Test first few patterns
            assert (
                _should_retry(
                    [{"type": "some_error", "kind": "some_error", "severity": "error"}],
                    {"stderr": f"Some error with {pattern} occurred"},
                )
                is True
            )

        # Test flaky patterns in error messages
        assert (
            _should_retry(
                [
                    {
                        "type": "some_error",
                        "kind": "some_error",
                        "message": "LaTeX error: emergency stop occurred",
                        "severity": "error",
                    }
                ],
                {},
            )
            is True
        )

    def test_should_retry_logic_non_retryable_errors(self):
        """T5.6: Test _should_retry logic rejects non-retryable errors."""
        # Test non-retryable error types
        for error_type in NO_RETRY_ERROR_TYPES[:3]:  # Test first few
            assert (
                _should_retry(
                    [{"type": error_type, "kind": error_type, "severity": "error"}],
                    {"resource_usage": {"exit_code": 1}},
                )
                is False
            )

    def test_should_retry_logic_no_flaky_indicators(self):
        """T5.6: Test _should_retry logic for normal errors without flaky indicators."""
        assert (
            _should_retry(
                [{"type": "normal_error", "kind": "normal_error", "severity": "error"}],
                {"stderr": "Normal error message", "resource_usage": {"exit_code": 0}},
            )
            is False
        )

    def test_max_retries_respected(self):
        """T5.6: Test that max_retries parameter is respected."""
        vin = self._create_validate_input()

        def mock_runner_always_flaky(*args, **kwargs):
            return (
                None,
                {
                    "stderr": "font warning: transient issue",
                    "resource_usage": {"exit_code": 1},
                },
                [
                    {
                        "type": "font_error",
                        "kind": "font_error",
                        "field": "rendering",
                        "message": "Font issue",
                        "severity": "error",
                    }
                ],
            )

        with patch("generator.validator.orchestrator.validate_scene_json"), patch(
            "generator.validator.orchestrator.validate_style_pack"
        ), patch("generator.validator.orchestrator.validate_source_safety"), patch(
            "generator.validator.orchestrator.run_manim_preview",
            side_effect=mock_runner_always_flaky,
        ) as mock_runner:

            # Test with max_retries=0 (no retries)
            with pytest.raises(NeedsRepair):
                orchestrate_validation(vin, max_retries=0)

            # Should only call runner once
            assert mock_runner.call_count == 1

    def test_validate_scene_with_orchestration_wrapper(self):
        """T5.6: Test high-level validation wrapper function."""
        vin = self._create_validate_input()

        with patch(
            "generator.validator.orchestrator.orchestrate_validation"
        ) as mock_orchestrate:
            mock_result = ValidateResult(
                ok=True, preview_mp4=None, first_frame_png=None, logs={}, issues=[]
            )
            mock_orchestrate.return_value = mock_result

            # Test successful wrapper call
            result = validate_scene_with_orchestration(vin)

            assert result == mock_result
            mock_orchestrate.assert_called_once_with(vin, max_retries=1)

    def test_validate_scene_wrapper_handles_unexpected_exceptions(self):
        """T5.6: Test wrapper converts unexpected exceptions to NeedsRepair."""
        vin = self._create_validate_input()

        with patch(
            "generator.validator.orchestrator.orchestrate_validation"
        ) as mock_orchestrate:
            mock_orchestrate.side_effect = RuntimeError("Unexpected error")

            # Should convert to NeedsRepair
            with pytest.raises(NeedsRepair) as exc_info:
                validate_scene_with_orchestration(vin)

            payload = exc_info.value.payload
            assert payload["scene_id"] == "test_scene"
            assert payload["errors"][0]["kind"] == "orchestration_error"
            assert "Unexpected error" in payload["stderr_excerpt"]

    def test_needs_repair_from_issues_creation(self):
        """T5.6: Test NeedsRepair.from_issues class method."""
        issues = [
            {
                "type": "latex_error",
                "kind": "latex_error",
                "field": "timeline[0].latex",
                "message": "LaTeX compilation failed",
                "severity": "error",
            },
            {
                "type": "warning",
                "kind": "warning",
                "field": "general",
                "message": "Minor warning",
                "severity": "warning",
            },
        ]

        stderr_excerpt = "LaTeX Error: Missing $ inserted\nSome more stderr content..."

        # Test creation from issues
        needs_repair = NeedsRepair.from_issues("test_scene", issues, stderr_excerpt)

        payload = needs_repair.payload
        assert payload["scene_id"] == "test_scene"
        assert len(payload["errors"]) == 1  # Only error-level issues
        assert payload["errors"][0]["kind"] == "latex_error"
        assert payload["errors"][0]["field"] == "timeline[0].latex"
        assert len(payload["stderr_excerpt"]) <= 500  # Truncated to 500 chars

    def test_retry_metrics_integration(self):
        """T5.6: Test that retry attempts are properly recorded in metrics."""
        vin = self._create_validate_input()

        call_count = 0

        def mock_runner_retry_once(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # Fail first time with retryable error
                return (
                    None,
                    {
                        "stderr": "cairo error occurred",
                        "resource_usage": {"exit_code": 1},
                    },
                    [
                        {
                            "type": "cairo_error",
                            "kind": "cairo_error",
                            "severity": "error",
                        }
                    ],
                )
            else:
                # Succeed second time
                mock_artifacts = Mock()
                return (mock_artifacts, {"resource_usage": {"exit_code": 0}}, [])

        with patch("generator.validator.orchestrator.validate_scene_json"), patch(
            "generator.validator.orchestrator.validate_style_pack"
        ), patch("generator.validator.orchestrator.validate_source_safety"), patch(
            "generator.validator.orchestrator.run_manim_preview",
            side_effect=mock_runner_retry_once,
        ), patch(
            "generator.validator.orchestrator.record_retry"
        ) as mock_record_retry:

            # Test orchestration
            result = orchestrate_validation(vin)

            assert result.ok is True
            # Verify retry was recorded
            mock_record_retry.assert_called_once()
            call_args = mock_record_retry.call_args
            assert call_args[0][0] == "test_video"  # video_id
            assert call_args[0][1] == "test_scene"  # scene_id
            assert call_args[0][3] == "cairo_error"  # error_kind
            assert call_args[0][4] == 1  # attempt number

    def test_orchestration_with_multiple_error_types(self):
        """T5.6: Test orchestration with multiple error types in single execution."""
        vin = self._create_validate_input()

        mixed_issues = [
            {
                "type": "latex_error",
                "kind": "latex_error",
                "field": "timeline[0].latex",
                "message": "LaTeX failed",
                "severity": "error",
            },
            {
                "type": "asset_missing",
                "kind": "asset_missing",
                "field": "timeline[1].ref",
                "message": "Asset not found",
                "severity": "error",
            },
            {
                "type": "warning",
                "kind": "warning",
                "field": "general",
                "message": "Minor issue",
                "severity": "warning",
            },
        ]

        with patch("generator.validator.orchestrator.validate_scene_json"), patch(
            "generator.validator.orchestrator.validate_style_pack"
        ), patch("generator.validator.orchestrator.validate_source_safety"), patch(
            "generator.validator.orchestrator.run_manim_preview"
        ) as mock_runner:

            mock_runner.return_value = (
                None,
                {"stderr": "Multiple errors"},
                mixed_issues,
            )

            # Should raise NeedsRepair with multiple errors
            with pytest.raises(NeedsRepair) as exc_info:
                orchestrate_validation(vin)

            payload = exc_info.value.payload
            assert len(payload["errors"]) == 2  # Only error-level issues
            error_kinds = [e["kind"] for e in payload["errors"]]
            assert "latex_error" in error_kinds
            assert "asset_missing" in error_kinds
