"""
Basic validation tests for T7 video QC components.

Tests the core functionality of all T7 components to ensure they work correctly
and integrate properly with the overall system.
"""

import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from generator.video_qc import (
    QCInput,
    QCResult,
    qc_and_package,
    VideoProbe,
    VideoMetadata,
    QCSettings,
    VideoQC,
    QCIssue,
    ManifestBuilder,
    VideoManifest,
    ExtendedThumbnailGenerator,
)


class TestBasicValidation:
    """Basic validation tests for T7 components."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_video = self.temp_dir / "test_video.mp4"

        # Create a minimal test video file (just empty file for now)
        self.test_video.write_bytes(b"fake video content for testing")

    def teardown_method(self):
        """Cleanup test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_qc_input_validation(self):
        """Test QC input validation."""
        # Valid input
        qc_input = QCInput(
            video_id="test_video_123",
            final_mp4=self.test_video,
            thumbs=[],
            out_dir=self.temp_dir / "output",
        )

        assert qc_input.video_id == "test_video_123"
        assert qc_input.final_mp4 == self.test_video
        assert qc_input.out_dir == self.temp_dir / "output"

        # Invalid input (empty video_id)
        with pytest.raises(ValueError, match="video_id is required"):
            QCInput(
                video_id="", final_mp4=self.test_video, thumbs=[], out_dir=self.temp_dir
            )

    def test_qc_result_defaults(self):
        """Test QC result with default values."""
        result = QCResult(ok=True)

        assert result.ok is True
        assert result.manifest is None
        assert result.extra_thumbs == []
        assert result.issues == []
        assert result.logs == {}

    def test_video_metadata_properties(self):
        """Test video metadata properties."""
        metadata = VideoMetadata(
            duration_s=10.5,
            width=1920,
            height=1080,
            fps=30.0,
            frame_count=315,
            codec="h264",
            pixel_format="yuv420p",
        )

        assert metadata.resolution == "1920x1080"
        assert metadata.aspect_ratio == 1920 / 1080
        assert metadata.duration_s == 10.5
        assert metadata.frame_count == 315

    def test_qc_issue_creation(self):
        """Test QC issue creation."""
        issue = QCIssue(
            issue_type="black_frame",
            severity="warning",
            start_time_s=5.0,
            duration_s=1.5,
            message="Black frame sequence detected",
            metadata={"threshold": 0.1},
        )

        assert issue.issue_type == "black_frame"
        assert issue.severity == "warning"
        assert issue.start_time_s == 5.0
        assert issue.duration_s == 1.5
        assert issue.metadata["threshold"] == 0.1

    def test_qc_settings_defaults(self):
        """Test QC settings default values."""
        settings = QCSettings()

        assert settings.black_threshold == 0.1
        assert settings.black_duration_threshold == 0.5
        assert settings.freeze_duration_threshold == 0.5
        assert settings.enable_black_detection is True
        assert settings.enable_freeze_detection is True
        assert settings.enable_spec_validation is True

    def test_video_manifest_creation(self):
        """Test video manifest creation."""
        manifest = VideoManifest(
            video_id="test_123",
            created_at="2023-01-01T00:00:00Z",
            file_path="test.mp4",
            file_size_bytes=1024000,
            hash_sha256="abc123" * 10 + "abcd",  # 64-char hex
            duration_s=15.0,
            resolution="1920x1080",
            width=1920,
            height=1080,
            fps=30.0,
            frame_count=450,
            codec="h264",
            pixel_format="yuv420p",
        )

        assert manifest.video_id == "test_123"
        assert manifest.resolution == "1920x1080"
        assert manifest.hash_sha256.startswith("abc123")
        assert len(manifest.hash_sha256) == 64

    @patch("generator.video_qc.probe.subprocess.run")
    def test_video_probe_mocked(self, mock_subprocess):
        """Test video probe with mocked ffprobe."""
        # Mock ffprobe stream output
        stream_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "duration": "10.5",
                    "avg_frame_rate": "30/1",
                    "nb_frames": "315",
                    "pix_fmt": "yuv420p",
                }
            ]
        }

        # Mock ffprobe format output
        format_output = {
            "format": {
                "duration": "10.5",
                "bit_rate": "3500000",
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            }
        }

        # Configure mock to return different outputs for different calls
        mock_subprocess.side_effect = [
            Mock(stdout=json.dumps(stream_output), stderr=""),
            Mock(stdout=json.dumps(format_output), stderr=""),
        ]

        probe = VideoProbe()
        metadata = probe.probe_video(self.test_video)

        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.duration_s == 10.5
        assert metadata.fps == 30.0
        assert metadata.frame_count == 315
        assert metadata.codec == "h264"
        assert metadata.pixel_format == "yuv420p"

    @patch("generator.video_qc.qc.subprocess.run")
    def test_qc_checks_mocked(self, mock_subprocess):
        """Test QC checks with mocked ffmpeg."""
        # Mock ffmpeg output (no issues found)
        mock_subprocess.return_value = Mock(
            stderr="[blackdetect] No black frames detected\n[freezedetect] No frozen frames detected",
            returncode=0,
        )

        qc_checker = VideoQC()
        issues = qc_checker.run_qc_checks(self.test_video)

        # Should return empty list if no issues found
        assert isinstance(issues, list)

    def test_manifest_builder_initialization(self):
        """Test manifest builder initialization."""
        builder = ManifestBuilder()

        assert builder.processor_version == "1.0.0"
        assert hasattr(builder, "probe")

    def test_thumbnail_generator_initialization(self):
        """Test thumbnail generator initialization."""
        generator = ExtendedThumbnailGenerator()

        assert generator.timeout_s == 60
        assert hasattr(generator, "probe")

    def test_qc_input_file_validation(self):
        """Test QC input file existence validation."""
        # Test with non-existent file
        non_existent = self.temp_dir / "non_existent.mp4"

        qc_input = QCInput(
            video_id="test_missing",
            final_mp4=non_existent,
            thumbs=[],
            out_dir=self.temp_dir,
        )

        # The input can be created, but validation should catch missing file
        assert qc_input.final_mp4 == non_existent
        assert not qc_input.final_mp4.exists()

    def test_component_integration(self):
        """Test that all components can be imported and instantiated."""
        # Test all main components can be created
        probe = VideoProbe()
        qc_checker = VideoQC()
        manifest_builder = ManifestBuilder()
        thumbnail_generator = ExtendedThumbnailGenerator()

        assert probe is not None
        assert qc_checker is not None
        assert manifest_builder is not None
        assert thumbnail_generator is not None

        # Test settings can be configured
        settings = QCSettings(
            black_threshold=0.05,
            freeze_duration_threshold=1.0,
            enable_black_detection=False,
        )

        qc_checker_with_settings = VideoQC(settings)
        assert qc_checker_with_settings.settings.black_threshold == 0.05
        assert qc_checker_with_settings.settings.enable_black_detection is False

    @patch("generator.video_qc.orchestrator.QCOrchestrator")
    def test_main_entry_point(self, mock_orchestrator):
        """Test main entry point delegates correctly."""
        # Mock orchestrator
        mock_instance = Mock()
        mock_orchestrator.return_value = mock_instance

        mock_result = QCResult(
            ok=True,
            manifest=self.temp_dir / "manifest.json",
            extra_thumbs=[],
            issues=[],
            logs={},
        )
        mock_instance.run_qc_pipeline.return_value = mock_result

        # Create test input
        qc_input = QCInput(
            video_id="test_entry_point",
            final_mp4=self.test_video,
            thumbs=[],
            out_dir=self.temp_dir / "output",
        )

        # Call main entry point
        result = qc_and_package(qc_input)

        # Verify delegation
        mock_orchestrator.assert_called_once()
        mock_instance.run_qc_pipeline.assert_called_once_with(qc_input)
        assert result.ok is True
