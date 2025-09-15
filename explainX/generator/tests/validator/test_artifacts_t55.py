"""
Comprehensive T5.5 tests for enhanced artifacts manager.
Tests Manim output detection, size limits, and re-encoding scenarios.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import shutil

import pytest

from generator.validator.artifacts import (
    ArtifactManager,
    PreviewArtifacts,
    get_manim_output_files,
    MAX_PREVIEW_MB,
)


class TestT55EnhancedArtifacts:
    """T5.5 specific tests for enhanced artifacts manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.artifacts_manager = ArtifactManager(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_t55_artifact_naming_convention(self):
        """T5.5: Test standardized naming: scene_<id>_preview.mp4, scene_<id>_frame0.png."""
        scene_id = "sec_01"
        class_name = "Scene_sec_01"

        artifacts = self.artifacts_manager.get_artifact_paths(scene_id, class_name)

        # T5.5: Verify naming convention
        assert artifacts.preview_mp4.name == "scene_sec_01_preview.mp4"
        assert artifacts.first_frame_png.name == "scene_sec_01_frame0.png"

        # Should be in artifacts directory
        assert artifacts.preview_mp4.parent == self.artifacts_manager.artifacts_dir
        assert artifacts.first_frame_png.parent == self.artifacts_manager.artifacts_dir

    def test_manim_output_pattern_detection(self):
        """T5.5: Test detection of Manim default output patterns."""
        class_name = "Scene_sec_01"

        # Create test Manim output structure: artifacts/media/videos/main/480p15/Scene_sec_01.mp4
        manim_output_dir = (
            self.temp_dir / "artifacts" / "media" / "videos" / "main" / "480p15"
        )
        manim_output_dir.mkdir(parents=True, exist_ok=True)

        test_video = manim_output_dir / f"{class_name}.mp4"
        test_video.write_text("fake video content")  # Create fake video

        # Test detection
        detected = self.artifacts_manager.detect_manim_output(class_name)

        assert detected == test_video

    def test_multiple_pattern_fallback(self):
        """T5.5: Test fallback through multiple Manim output patterns."""
        class_name = "Scene_test"

        # Create alternative pattern: work_dir/media/videos/720p30/Scene_test.mp4
        alt_output_dir = self.temp_dir / "media" / "videos" / "720p30"
        alt_output_dir.mkdir(parents=True, exist_ok=True)

        test_video = alt_output_dir / f"{class_name}.mp4"
        test_video.write_text("fake video content")

        # Test detection with alternative pattern
        detected = self.artifacts_manager.detect_manim_output(class_name)

        assert detected == test_video

    def test_size_limit_compliance(self):
        """T5.5: Test video size limit enforcement (10MB max)."""
        # Create a mock large video file (simulated)
        large_video = self.temp_dir / "large_video.mp4"
        large_video.write_bytes(b"0" * (15 * 1024 * 1024))  # 15MB fake content

        target_video = self.temp_dir / "target.mp4"

        with patch("generator.validator.artifacts.subprocess.run") as mock_subprocess:
            # Mock successful re-encoding
            mock_subprocess.return_value.returncode = 0

            # Mock that target file is created and smaller
            def create_smaller_file(*args, **kwargs):
                # Simulate ffmpeg creating a smaller file
                target_video.write_bytes(b"0" * (8 * 1024 * 1024))  # 8MB
                return Mock(returncode=0)

            mock_subprocess.side_effect = create_smaller_file

            # Test size limit enforcement
            result = self.artifacts_manager._ensure_size_limit(
                large_video, target_video
            )

            assert result == target_video
            assert target_video.exists()

            # Verify ffmpeg was called for re-encoding
            assert mock_subprocess.called
            call_args = mock_subprocess.call_args[0][0]
            assert "ffmpeg" in call_args

    def test_under_size_limit_no_reencoding(self):
        """T5.5: Test that videos under size limit are just copied."""
        # Create a small video file
        small_video = self.temp_dir / "small_video.mp4"
        small_video.write_bytes(b"0" * (5 * 1024 * 1024))  # 5MB

        target_video = self.temp_dir / "target.mp4"

        # Test no re-encoding needed
        result = self.artifacts_manager._ensure_size_limit(small_video, target_video)

        assert result == target_video
        assert target_video.exists()
        # Should be same size (just copied)
        assert target_video.stat().st_size == small_video.stat().st_size

    def test_reencoding_failure_fallback(self):
        """T5.5: Test fallback behavior when re-encoding fails."""
        large_video = self.temp_dir / "large_video.mp4"
        large_video.write_bytes(b"0" * (15 * 1024 * 1024))  # 15MB

        target_video = self.temp_dir / "target.mp4"

        with patch("generator.validator.artifacts.subprocess.run") as mock_subprocess:
            # Mock failed re-encoding
            mock_subprocess.return_value.returncode = 1

            # Test fallback to copy
            result = self.artifacts_manager._ensure_size_limit(
                large_video, target_video
            )

            assert result == target_video
            assert target_video.exists()
            # Should fallback to copy (same size)
            assert target_video.stat().st_size == large_video.stat().st_size

    def test_aggressive_reencoding_fallback(self):
        """T5.5: Test aggressive re-encoding when standard re-encoding insufficient."""
        large_video = self.temp_dir / "very_large_video.mp4"
        large_video.write_bytes(b"0" * (50 * 1024 * 1024))  # 50MB

        target_video = self.temp_dir / "target.mp4"

        call_count = 0

        def mock_ffmpeg_calls(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First call (standard re-encoding) - still too big
                target_video.write_bytes(b"0" * (12 * 1024 * 1024))  # Still 12MB
                return Mock(returncode=0)
            else:
                # Second call (aggressive re-encoding) - small enough
                target_video.write_bytes(b"0" * (8 * 1024 * 1024))  # 8MB
                return Mock(returncode=0)

        with patch(
            "generator.validator.artifacts.subprocess.run",
            side_effect=mock_ffmpeg_calls,
        ):
            result = self.artifacts_manager._ensure_size_limit(
                large_video, target_video
            )

            assert result == target_video
            assert call_count == 2  # Should have called both standard and aggressive

            # Verify aggressive encoding parameters were used in second call
            # (This would require more detailed mocking to verify exact parameters)

    def test_first_frame_extraction_t55(self):
        """T5.5: Test first frame extraction using ffmpeg -frames:v 1."""
        video_path = self.temp_dir / "test_video.mp4"
        video_path.write_text("fake video")  # Create fake video file

        frame_path = self.temp_dir / "frame0.png"

        with patch("generator.validator.artifacts.subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0

            # Mock frame file creation
            def create_frame(*args, **kwargs):
                frame_path.write_text("fake png")
                return Mock(returncode=0)

            mock_subprocess.side_effect = create_frame

            # Test frame extraction
            success = self.artifacts_manager.extract_first_frame(video_path, frame_path)

            assert success is True
            assert frame_path.exists()

            # T5.5: Verify -frames:v 1 parameter was used
            call_args = mock_subprocess.call_args[0][0]
            assert "-frames:v" in call_args
            assert "1" in call_args

    def test_complete_process_manim_output(self):
        """T5.5: Test complete processing pipeline."""
        class_name = "Scene_test_complete"
        scene_id = "test_complete"

        # Create mock Manim output
        manim_dir = self.temp_dir / "artifacts" / "media" / "videos" / "main" / "480p15"
        manim_dir.mkdir(parents=True, exist_ok=True)

        source_video = manim_dir / f"{class_name}.mp4"
        source_video.write_bytes(b"0" * (8 * 1024 * 1024))  # 8MB (under limit)

        with patch.object(
            self.artifacts_manager, "extract_first_frame", return_value=True
        ):
            # Test complete processing
            artifacts = self.artifacts_manager.process_manim_output(
                class_name=class_name, scene_id=scene_id, source_filename="main"
            )

            assert artifacts is not None
            assert artifacts.preview_mp4.exists()
            assert artifacts.first_frame_png.exists()

            # T5.5: Verify naming convention
            assert artifacts.preview_mp4.name == f"scene_{scene_id}_preview.mp4"
            assert artifacts.first_frame_png.name == f"scene_{scene_id}_frame0.png"

    def test_no_manim_output_found(self):
        """T5.5: Test handling when no Manim output is found."""
        result = self.artifacts_manager.process_manim_output(
            class_name="NonexistentScene", scene_id="missing", source_filename="main"
        )

        assert result is None

    def test_frame_extraction_failure_graceful(self):
        """T5.5: Test graceful handling when frame extraction fails."""
        class_name = "Scene_frame_fail"
        scene_id = "frame_fail"

        # Create mock Manim output
        manim_dir = self.temp_dir / "media"
        manim_dir.mkdir(exist_ok=True)

        source_video = manim_dir / f"{class_name}.mp4"
        source_video.write_bytes(b"0" * (5 * 1024 * 1024))  # 5MB

        with patch.object(
            self.artifacts_manager, "extract_first_frame", return_value=False
        ):
            # Test processing with frame extraction failure
            artifacts = self.artifacts_manager.process_manim_output(
                class_name=class_name, scene_id=scene_id
            )

            assert artifacts is not None
            assert artifacts.preview_mp4.exists()  # Video should still be processed
            assert artifacts.first_frame_png is None  # Frame should be None on failure

    def test_enhanced_get_manim_output_files(self):
        """T5.5: Test enhanced get_manim_output_files function."""
        class_name = "Scene_enhanced_test"

        # Create test Manim output
        media_dir = self.temp_dir / "media" / "videos" / "enhanced_test" / "720p30"
        media_dir.mkdir(parents=True, exist_ok=True)

        test_video = media_dir / f"{class_name}.mp4"
        test_video.write_text("test video")

        # Test enhanced detection
        video_path, found_media_dir = get_manim_output_files(self.temp_dir, class_name)

        assert video_path == test_video
        assert found_media_dir == media_dir

    def test_oversized_video_processing_end_to_end(self):
        """T5.5: End-to-end test with oversized video requiring re-encoding."""
        class_name = "Scene_oversized"
        scene_id = "oversized"

        # Create large mock Manim output
        manim_dir = self.temp_dir / "media"
        manim_dir.mkdir(exist_ok=True)

        large_video = manim_dir / f"{class_name}.mp4"
        large_video.write_bytes(b"0" * (15 * 1024 * 1024))  # 15MB (oversized)

        with patch("generator.validator.artifacts.subprocess.run") as mock_subprocess:
            # Mock successful re-encoding and frame extraction
            def mock_subprocess_calls(command, *args, **kwargs):
                if "ffmpeg" in command and "-frames:v" in command:
                    # Frame extraction
                    frame_path = Path(command[-1])
                    frame_path.write_text("fake frame")
                    return Mock(returncode=0)
                else:
                    # Video re-encoding
                    target_path = Path(command[-1])
                    target_path.write_bytes(b"0" * (8 * 1024 * 1024))  # 8MB
                    return Mock(returncode=0)

            mock_subprocess.side_effect = mock_subprocess_calls

            # Test complete processing with re-encoding
            artifacts = self.artifacts_manager.process_manim_output(
                class_name=class_name, scene_id=scene_id
            )

            assert artifacts is not None
            assert artifacts.preview_mp4.exists()
            assert artifacts.first_frame_png.exists()

            # Verify final video is under size limit
            final_size_mb = artifacts.preview_mp4.stat().st_size / (1024 * 1024)
            assert final_size_mb <= MAX_PREVIEW_MB

    def test_filename_sanitization(self):
        """T5.5: Test filename sanitization for filesystem safety."""
        # Test with problematic characters
        problematic_id = "scene-with/bad\\chars:and|symbols"
        safe_name = self.artifacts_manager._sanitize_filename(problematic_id)

        # Should contain only safe characters
        assert all(c.isalnum() or c in "-_" for c in safe_name)
        assert len(safe_name) <= 50  # Length limit
        assert safe_name != ""  # Not empty

    def test_artifact_cleanup_on_failure(self):
        """T5.5: Test that artifacts are cleaned up when processing fails."""
        class_name = "Scene_cleanup_test"
        scene_id = "cleanup_test"

        # Create mock Manim output
        manim_dir = self.temp_dir / "media"
        manim_dir.mkdir(exist_ok=True)

        source_video = manim_dir / f"{class_name}.mp4"
        source_video.write_bytes(b"0" * (5 * 1024 * 1024))  # 5MB

        # Mock that processing fails after creating some artifacts
        with patch.object(
            self.artifacts_manager, "extract_first_frame"
        ) as mock_extract:
            mock_extract.side_effect = Exception("Frame extraction failed")

            # This should fail and clean up
            artifacts = self.artifacts_manager.process_manim_output(
                class_name=class_name, scene_id=scene_id
            )

            assert artifacts is None

            # Verify cleanup occurred (no artifact files left behind)
            artifact_files = list(
                self.artifacts_manager.artifacts_dir.glob(f"scene_{scene_id}*")
            )
            assert len(artifact_files) == 0
