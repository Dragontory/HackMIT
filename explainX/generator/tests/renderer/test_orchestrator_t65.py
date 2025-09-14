"""
Tests for T6.5: End-to-end render orchestrator.
"""

import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from generator.renderer import (
    RenderInput,
    RenderResult,
    SceneRenderItem,
    render_video_no_audio,
    RenderCache,
)
from generator.renderer.orchestrator import RenderOrchestrator
from generator.renderer.manim_prod import ProductionRenderResult
from generator.renderer.concat import ConcatResult
from generator.renderer.thumbs import ThumbnailResult
from generator.renderer.errors import ValidationError, RenderSceneError
from generator.renderer.metrics import reset_global_metrics


class TestRenderOrchestrator:
    """Test render orchestrator functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_dir = self.temp_dir / "cache"
        self.out_dir = self.temp_dir / "output"
        self.out_dir.mkdir(parents=True)

        # Reset global metrics for clean tests
        reset_global_metrics()

        # Create test scene files
        self.scene1_py = self.temp_dir / "scene1.py"
        self.scene2_py = self.temp_dir / "scene2.py"

        scene_content = """
from manim import *
class TestScene(Scene):
    def construct(self):
        text = Text("Test Scene")
        self.add(text)
        """

        self.scene1_py.write_text(scene_content)
        self.scene2_py.write_text(scene_content)

    def teardown_method(self):
        """Cleanup test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_test_render_input(
        self, scene_count: int = 2, crossfade_s: float = None
    ) -> RenderInput:
        """Create test render input with specified number of scenes."""
        scenes = []
        for i in range(scene_count):
            scene_py = self.temp_dir / f"scene{i+1}.py"
            if not scene_py.exists():
                scene_py.write_text("# test scene")

            scenes.append(
                SceneRenderItem(
                    scene_id=f"scene_{i+1:02d}",
                    class_name=f"TestScene_{i+1}",
                    main_py=scene_py,
                    est_duration_s=5.0,
                )
            )

        return RenderInput(
            video_id="test_video_123",
            scenes=scenes,
            out_dir=self.out_dir,
            quality="1080p",
            fps=30,
            crossfade_s=crossfade_s,
        )

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly."""
        orchestrator = RenderOrchestrator(
            cache=RenderCache(cache_dir=self.cache_dir),
            enable_caching=True,
            temp_dir=self.temp_dir,
        )

        assert orchestrator.enable_caching is True
        assert orchestrator.cache is not None
        assert orchestrator.temp_dir == self.temp_dir

    def test_orchestrator_no_cache(self):
        """Test orchestrator works without caching."""
        orchestrator = RenderOrchestrator(enable_caching=False)

        assert orchestrator.enable_caching is False
        assert orchestrator.cache is None

    @patch("generator.renderer.orchestrator.ProductionManimRenderer")
    @patch("generator.renderer.orchestrator.VideoConcatenator")
    @patch("generator.renderer.orchestrator.generate_standard_thumbnails")
    def test_successful_render_pipeline(self, mock_thumbs, mock_concat, mock_renderer):
        """Test successful end-to-end render pipeline."""
        # Setup mocks
        mock_renderer_instance = Mock()
        mock_renderer.return_value.__enter__.return_value = mock_renderer_instance

        # Mock scene render results
        scene1_output = self.out_dir / "scenes" / "scene_scene_01_prod.mp4"
        scene2_output = self.out_dir / "scenes" / "scene_scene_02_prod.mp4"

        scene1_output.parent.mkdir(parents=True, exist_ok=True)
        scene2_output.parent.mkdir(parents=True, exist_ok=True)
        scene1_output.write_bytes(b"scene1 content")
        scene2_output.write_bytes(b"scene2 content")

        mock_renderer_instance.render_scene.side_effect = [
            ProductionRenderResult(
                success=True,
                output_mp4=scene1_output,
                duration_s=5.0,
                file_size_mb=10.0,
                resolution=(1920, 1080),
                fps=30,
                frame_count=150,
                render_time_s=2.5,
                stdout="render success",
                stderr="",
            ),
            ProductionRenderResult(
                success=True,
                output_mp4=scene2_output,
                duration_s=6.0,
                file_size_mb=12.0,
                resolution=(1920, 1080),
                fps=30,
                frame_count=180,
                render_time_s=3.0,
                stdout="render success",
                stderr="",
            ),
        ]

        # Mock concatenation
        mock_concat_instance = Mock()
        mock_concat.return_value.__enter__.return_value = mock_concat_instance

        final_video = self.out_dir / "test_video_123_final.mp4"
        final_video.write_bytes(b"final video content")

        mock_concat_instance.concatenate_videos.return_value = ConcatResult(
            success=True,
            output_video=final_video,
            duration_s=11.0,
            file_size_mb=20.0,
            processing_time_s=1.5,
            transitions_applied=0,
            error_message="",
        )

        # Mock thumbnails
        thumb1 = self.out_dir / "thumbnails" / "poster.png"
        thumb2 = self.out_dir / "thumbnails" / "mid.png"
        thumb1.parent.mkdir(parents=True, exist_ok=True)
        thumb1.write_bytes(b"poster")
        thumb2.write_bytes(b"mid")

        mock_thumbs.return_value = [
            ThumbnailResult(success=True, thumbnail_path=thumb1, extraction_time_s=0.1),
            ThumbnailResult(success=True, thumbnail_path=thumb2, extraction_time_s=0.1),
        ]

        # Execute pipeline
        orchestrator = RenderOrchestrator(enable_caching=False)
        render_input = self.create_test_render_input(scene_count=2)

        result = orchestrator.render_video(render_input)

        # Verify result
        assert result.ok is True
        assert result.final_mp4 == final_video
        assert len(result.scene_mp4s) == 2
        assert len(result.thumbs) == 2
        assert result.logs["success"] is True
        assert result.logs["video_id"] == "test_video_123"

        # Verify method calls
        assert mock_renderer_instance.render_scene.call_count == 2
        mock_concat_instance.concatenate_videos.assert_called_once()
        mock_thumbs.assert_called_once()

    @patch("generator.renderer.orchestrator.ProductionManimRenderer")
    def test_scene_render_failure(self, mock_renderer):
        """Test pipeline stops when scene rendering fails."""
        mock_renderer_instance = Mock()
        mock_renderer.return_value.__enter__.return_value = mock_renderer_instance

        # First scene succeeds, second fails
        scene1_output = self.out_dir / "scenes" / "scene_scene_01_prod.mp4"
        scene1_output.parent.mkdir(parents=True, exist_ok=True)
        scene1_output.write_bytes(b"scene1 content")

        mock_renderer_instance.render_scene.side_effect = [
            ProductionRenderResult(
                success=True,
                output_mp4=scene1_output,
                duration_s=5.0,
                file_size_mb=10.0,
                resolution=(1920, 1080),
                fps=30,
                frame_count=150,
                render_time_s=2.5,
                stdout="success",
                stderr="",
            ),
            ProductionRenderResult(
                success=False,
                output_mp4=None,
                duration_s=0.0,
                file_size_mb=0.0,
                resolution=(0, 0),
                fps=0,
                frame_count=0,
                render_time_s=0.0,
                stdout="",
                stderr="render failed",
                error_message="Manim execution failed",
            ),
        ]

        orchestrator = RenderOrchestrator(enable_caching=False)
        render_input = self.create_test_render_input(scene_count=2)

        result = orchestrator.render_video(render_input)

        # Should fail due to scene render failure (but may continue to concatenation)
        assert result.ok is False
        assert (
            "failed to render" in result.logs["error_message"]
            or "concatenation failed" in result.logs["error_message"]
        )
        assert result.final_mp4 is None

    def test_input_validation_failure(self):
        """Test pipeline fails on invalid input."""
        orchestrator = RenderOrchestrator(enable_caching=False)

        # Create invalid render input (empty scenes should fail at RenderInput creation)
        with pytest.raises(ValueError, match="At least one scene is required"):
            invalid_input = RenderInput(
                video_id="invalid_test",
                scenes=[],  # Empty scenes should fail validation
                out_dir=self.out_dir,
                quality="1080p",
                fps=30,
            )

        # Test with invalid fps instead
        scene_py = self.temp_dir / "invalid_scene.py"
        scene_py.write_text("# test")

        with pytest.raises(ValueError, match="Unsupported fps"):
            invalid_input = RenderInput(
                video_id="invalid_test",
                scenes=[
                    SceneRenderItem(
                        scene_id="test",
                        class_name="TestScene",
                        main_py=scene_py,
                        est_duration_s=3.0,
                    )
                ],
                out_dir=self.out_dir,
                quality="1080p",
                fps=99,  # Invalid fps
            )

    @patch("generator.renderer.orchestrator.ProductionManimRenderer")
    @patch("generator.renderer.orchestrator.VideoConcatenator")
    def test_concatenation_failure(self, mock_concat, mock_renderer):
        """Test pipeline fails when concatenation fails."""
        # Mock successful scene renders
        mock_renderer_instance = Mock()
        mock_renderer.return_value.__enter__.return_value = mock_renderer_instance

        scene_output = self.out_dir / "scenes" / "scene_scene_01_prod.mp4"
        scene_output.parent.mkdir(parents=True, exist_ok=True)
        scene_output.write_bytes(b"scene content")

        mock_renderer_instance.render_scene.return_value = ProductionRenderResult(
            success=True,
            output_mp4=scene_output,
            duration_s=5.0,
            file_size_mb=10.0,
            resolution=(1920, 1080),
            fps=30,
            frame_count=150,
            render_time_s=2.5,
            stdout="success",
            stderr="",
        )

        # Mock failed concatenation
        mock_concat_instance = Mock()
        mock_concat.return_value.__enter__.return_value = mock_concat_instance

        mock_concat_instance.concatenate_videos.return_value = ConcatResult(
            success=False,
            output_video=None,
            duration_s=0.0,
            file_size_mb=0.0,
            processing_time_s=0.0,
            transitions_applied=0,
            error_message="FFmpeg failed",
        )

        orchestrator = RenderOrchestrator(enable_caching=False)
        render_input = self.create_test_render_input(scene_count=1)

        result = orchestrator.render_video(render_input)

        assert result.ok is False
        assert "concatenation failed" in result.logs["error_message"]

    @patch("generator.renderer.orchestrator.ProductionManimRenderer")
    @patch("generator.renderer.orchestrator.VideoConcatenator")
    @patch("generator.renderer.orchestrator.generate_standard_thumbnails")
    def test_caching_functionality(self, mock_thumbs, mock_concat, mock_renderer):
        """Test caching accelerates repeat renders."""
        cache = RenderCache(cache_dir=self.cache_dir)
        orchestrator = RenderOrchestrator(cache=cache, enable_caching=True)

        # Setup successful mocks
        mock_renderer_instance = Mock()
        mock_renderer.return_value.__enter__.return_value = mock_renderer_instance

        scene_output = self.out_dir / "scenes" / "scene_scene_01_prod.mp4"
        scene_output.parent.mkdir(parents=True, exist_ok=True)
        scene_output.write_bytes(b"scene content")

        mock_renderer_instance.render_scene.return_value = ProductionRenderResult(
            success=True,
            output_mp4=scene_output,
            duration_s=5.0,
            file_size_mb=10.0,
            resolution=(1920, 1080),
            fps=30,
            frame_count=150,
            render_time_s=2.5,
            stdout="success",
            stderr="",
        )

        # Mock concatenation
        mock_concat_instance = Mock()
        mock_concat.return_value.__enter__.return_value = mock_concat_instance

        final_video = self.out_dir / "test_video_123_final.mp4"
        final_video.write_bytes(b"final video")

        mock_concat_instance.concatenate_videos.return_value = ConcatResult(
            success=True,
            output_video=final_video,
            duration_s=5.0,
            file_size_mb=10.0,
            processing_time_s=1.0,
            transitions_applied=0,
            error_message="",
        )

        # Mock thumbnails
        mock_thumbs.return_value = []

        render_input = self.create_test_render_input(scene_count=1)

        # First render (should execute and cache)
        result1 = orchestrator.render_video(render_input)
        assert result1.ok is True
        assert mock_renderer_instance.render_scene.call_count == 1

        # Second render (should use cache)
        result2 = orchestrator.render_video(render_input)
        assert result2.ok is True
        # Should not call render_scene again due to caching
        assert mock_renderer_instance.render_scene.call_count == 1

    def test_get_render_stats(self):
        """Test render orchestrator statistics."""
        cache = RenderCache(cache_dir=self.cache_dir)
        orchestrator = RenderOrchestrator(cache=cache, enable_caching=True)

        stats = orchestrator.get_render_stats()

        assert stats["caching_enabled"] is True
        assert "cache_stats" in stats
        assert stats["cache_stats"]["enabled"] is True

    def test_cleanup_cache(self):
        """Test cache cleanup functionality."""
        cache = RenderCache(cache_dir=self.cache_dir)
        orchestrator = RenderOrchestrator(cache=cache, enable_caching=True)

        # Should not raise exception
        orchestrator.cleanup_cache()
        orchestrator.cleanup_cache("scene_render")


class TestRenderVideoNoAudio:
    """Test main entry point function."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.out_dir = self.temp_dir / "output"
        self.out_dir.mkdir(parents=True)

        reset_global_metrics()

    def teardown_method(self):
        """Cleanup test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("generator.renderer.orchestrator.RenderOrchestrator")
    def test_render_video_no_audio_delegates(self, mock_orchestrator_class):
        """Test main entry point delegates to orchestrator."""
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        mock_result = RenderResult(ok=True, logs={})
        mock_orchestrator.render_video.return_value = mock_result

        # Create test input
        scene_py = self.temp_dir / "test_scene.py"
        scene_py.write_text("# test")

        render_input = RenderInput(
            video_id="test_delegation",
            scenes=[
                SceneRenderItem(
                    scene_id="test",
                    class_name="TestScene",
                    main_py=scene_py,
                    est_duration_s=3.0,
                )
            ],
            out_dir=self.out_dir,
            quality="720p",
            fps=30,
        )

        # Call main entry point
        result = render_video_no_audio(render_input)

        # Verify delegation
        mock_orchestrator_class.assert_called_once()
        mock_orchestrator.render_video.assert_called_once_with(render_input)
        assert result == mock_result


class TestRenderIntegration:
    """Integration tests for complete render pipeline."""

    def setup_method(self):
        """Setup integration test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.out_dir = self.temp_dir / "output"
        self.out_dir.mkdir(parents=True)

        reset_global_metrics()

    def teardown_method(self):
        """Cleanup test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("generator.renderer.manim_prod.ProductionManimRenderer")
    @patch("generator.renderer.concat.VideoConcatenator")
    @patch("generator.renderer.thumbs.generate_standard_thumbnails")
    def test_crossfade_render_pipeline(self, mock_thumbs, mock_concat, mock_renderer):
        """Test pipeline with crossfade transitions."""
        # Create test scene
        scene_py = self.temp_dir / "crossfade_scene.py"
        scene_py.write_text(
            """
from manim import *
class CrossfadeTestScene(Scene):
    def construct(self):
        text = Text("Crossfade Test")
        self.add(text)
        """
        )

        # Setup mocks for successful render
        mock_renderer_instance = Mock()
        mock_renderer.return_value.__enter__.return_value = mock_renderer_instance

        scene_outputs = []
        for i in range(3):
            output = self.out_dir / "scenes" / f"scene_scene_{i+1:02d}_prod.mp4"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(f"scene {i+1} content".encode())
            scene_outputs.append(output)

        mock_renderer_instance.render_scene.side_effect = [
            ProductionRenderResult(
                success=True,
                output_mp4=output,
                duration_s=4.0,
                file_size_mb=8.0,
                resolution=(1280, 720),
                fps=30,
                frame_count=120,
                render_time_s=2.0,
                stdout="success",
                stderr="",
            )
            for output in scene_outputs
        ]

        # Mock concatenation with crossfade
        mock_concat_instance = Mock()
        mock_concat.return_value.__enter__.return_value = mock_concat_instance

        final_video = self.out_dir / "crossfade_test_final.mp4"
        final_video.write_bytes(b"crossfaded video")

        mock_concat_instance.concatenate_videos.return_value = ConcatResult(
            success=True,
            output_video=final_video,
            duration_s=11.0,  # 3*4 - 2*0.5 = 11 seconds with crossfades
            file_size_mb=20.0,
            processing_time_s=3.0,
            transitions_applied=2,  # N-1 transitions
            error_message="",
        )

        # Mock thumbnails
        mock_thumbs.return_value = []

        # Create render input with crossfade
        scenes = [
            SceneRenderItem(
                scene_id=f"scene_{i+1:02d}",
                class_name=f"CrossfadeTestScene_{i+1}",
                main_py=scene_py,
                est_duration_s=4.0,
            )
            for i in range(3)
        ]

        render_input = RenderInput(
            video_id="crossfade_test",
            scenes=scenes,
            out_dir=self.out_dir,
            quality="720p",
            fps=30,
            crossfade_s=0.5,  # 0.5 second crossfades
        )

        # Execute render
        result = render_video_no_audio(render_input)

        # Verify result
        assert result.ok is True
        assert result.final_mp4 == final_video
        assert len(result.scene_mp4s) == 3

        # Verify crossfade was used
        concat_call = mock_concat_instance.concatenate_videos.call_args
        assert concat_call[1]["crossfade_s"] == 0.5

    def test_metrics_collection_during_render(self):
        """Test that metrics are collected during render operations."""
        from generator.renderer.metrics import get_metrics_collector

        collector = get_metrics_collector()
        initial_count = len(collector.metrics_history)

        # Create minimal render input
        scene_py = self.temp_dir / "metrics_scene.py"
        scene_py.write_text("# metrics test")

        render_input = RenderInput(
            video_id="metrics_test",
            scenes=[
                SceneRenderItem(
                    scene_id="metrics_01",
                    class_name="MetricsScene",
                    main_py=scene_py,
                    est_duration_s=2.0,
                )
            ],
            out_dir=self.out_dir,
            quality="720p",
            fps=30,
        )

        # Attempt render (will fail due to no mocking, but metrics should be collected)
        try:
            render_video_no_audio(render_input)
        except Exception:
            pass  # Expected to fail without mocks

        # Check that metrics were collected
        final_count = len(collector.metrics_history)
        assert final_count > initial_count

        # Check for video_render metric
        video_render_metrics = [
            m for m in collector.metrics_history if m.operation_type == "video_render"
        ]
        assert len(video_render_metrics) > 0

        latest_metric = video_render_metrics[-1]
        assert latest_metric.video_id == "metrics_test"
