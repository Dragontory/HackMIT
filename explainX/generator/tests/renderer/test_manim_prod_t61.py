"""
Comprehensive tests for T6.1: Production Manim renderer.
Tests quality presets, resource limits, and deterministic output.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from generator.renderer.manim_prod import (
    ProductionManimRenderer,
    ProductionRenderResult,
    render_scene_production,
    batch_render_scenes,
)
from generator.renderer import SceneRenderItem
from generator.renderer.config import get_quality_preset, get_manim_command


class TestT61ProductionRenderer:
    """T6.1 specific tests for production Manim rendering."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create test scene file
        self.test_scene_content = """from manim import *

class TestScene_Simple(Scene):
    def construct(self):
        title = Text("Test Scene", font_size=48)
        self.play(Write(title), run_time=0.5)
        self.wait(0.5)"""

        self.test_main_py = self.temp_dir / "test_scene.py"
        self.test_main_py.write_text(self.test_scene_content)

        self.scene_item = SceneRenderItem(
            scene_id="test_simple",
            class_name="TestScene_Simple",
            main_py=self.test_main_py,
            est_duration_s=1.5,
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)

    def test_quality_preset_configuration(self):
        """T6.1: Test quality presets are correctly configured."""
        # Test 1080p preset
        preset_1080p = get_quality_preset("1080p")
        assert preset_1080p.width == 1920
        assert preset_1080p.height == 1080
        assert preset_1080p.fps == 30
        assert preset_1080p.crf == 18  # High quality

        # Test 720p preset
        preset_720p = get_quality_preset("720p")
        assert preset_720p.width == 1280
        assert preset_720p.height == 720
        assert preset_720p.crf == 20  # Good quality

        # Test unknown preset raises error
        with pytest.raises(ValueError, match="Unknown quality preset"):
            get_quality_preset("unknown_quality")

    def test_manim_command_generation(self):
        """T6.1: Test Manim command generation with quality settings."""
        cmd = get_manim_command(
            quality="1080p",
            main_py_path="/test/main.py",
            class_name="TestScene",
            output_dir="/output",
            media_dir="/media",
        )

        # Should include quality flag
        assert "-q" in cmd
        assert "h" in cmd  # High quality for 1080p

        # Should include resolution
        assert "-r" in cmd
        resolution_idx = cmd.index("-r") + 1
        assert cmd[resolution_idx] == "1920,1080"

        # Should disable caching
        assert "--disable_caching" in cmd

        # Should include directories
        assert "--media_dir" in cmd
        assert "--output_dir" in cmd

        # Should include source and class
        assert "/test/main.py" in cmd
        assert "TestScene" in cmd

    def test_production_renderer_initialization(self):
        """T6.1: Test production renderer initialization."""
        renderer = ProductionManimRenderer(
            quality="720p", timeout_s=120, memory_mb=1024
        )

        assert renderer.quality == "720p"
        assert renderer.timeout_s == 120
        assert renderer.memory_mb == 1024
        assert renderer.quality_preset.width == 1280
        assert renderer.quality_preset.height == 720

    @patch("generator.renderer.manim_prod.SandboxEnvironment")
    def test_successful_render(self, mock_sandbox_class):
        """T6.1: Test successful scene rendering."""
        # Mock sandbox environment
        mock_sandbox = Mock()
        mock_sandbox_class.return_value.__enter__.return_value = mock_sandbox
        mock_sandbox.temp_dir = self.temp_dir / "sandbox"
        mock_sandbox.temp_dir.mkdir(exist_ok=True)

        # Mock write_file to return path
        mock_sandbox.write_file.return_value = mock_sandbox.temp_dir / "main.py"

        # Mock successful execution
        mock_sandbox.execute_command.return_value = (0, "Success output", "")

        # Create fake output video
        fake_output_dir = (
            mock_sandbox.temp_dir / "media" / "videos" / "main" / "1080p60"
        )
        fake_output_dir.mkdir(parents=True, exist_ok=True)
        fake_video = fake_output_dir / "TestScene_Simple.mp4"
        fake_video.write_bytes(b"fake video data")

        # Test rendering
        with ProductionManimRenderer(quality="1080p") as renderer:
            with patch.object(renderer, "_get_video_metadata") as mock_metadata:
                mock_metadata.return_value = {
                    "duration_s": 1.5,
                    "resolution": (1920, 1080),
                    "fps": 30.0,
                    "frame_count": 45,
                }

                result = renderer.render_scene(self.scene_item)

        # Verify result
        assert result.success is True
        assert result.output_mp4 is not None
        assert result.duration_s == 1.5
        assert result.resolution == (1920, 1080)
        assert result.fps == 30.0
        assert result.frame_count == 45
        assert result.exit_code == 0

    @patch("generator.renderer.manim_prod.SandboxEnvironment")
    def test_render_failure_handling(self, mock_sandbox_class):
        """T6.1: Test handling of render failures."""
        # Mock sandbox environment
        mock_sandbox = Mock()
        mock_sandbox_class.return_value.__enter__.return_value = mock_sandbox
        mock_sandbox.temp_dir = self.temp_dir / "sandbox"
        mock_sandbox.temp_dir.mkdir(exist_ok=True)
        mock_sandbox.write_file.return_value = mock_sandbox.temp_dir / "main.py"

        # Mock failed execution
        mock_sandbox.execute_command.return_value = (1, "", "LaTeX Error: Missing $")

        # Test rendering
        with ProductionManimRenderer(quality="1080p") as renderer:
            result = renderer.render_scene(self.scene_item)

        # Verify failure handling
        assert result.success is False
        assert result.exit_code == 1
        assert "LaTeX Error" in result.error_message
        assert result.output_mp4 is None

    @patch("generator.renderer.manim_prod.SandboxEnvironment")
    def test_timeout_handling(self, mock_sandbox_class):
        """T6.1: Test timeout handling."""
        # Mock sandbox environment that times out
        mock_sandbox = Mock()
        mock_sandbox_class.return_value.__enter__.return_value = mock_sandbox
        mock_sandbox.temp_dir = self.temp_dir / "sandbox"
        mock_sandbox.temp_dir.mkdir(exist_ok=True)
        mock_sandbox.write_file.return_value = mock_sandbox.temp_dir / "main.py"

        # Mock timeout (negative exit code indicates process was killed)
        mock_sandbox.execute_command.return_value = (
            -1,
            "",
            "Process timed out after 180 seconds",
        )

        # Test rendering with short timeout
        with ProductionManimRenderer(quality="1080p", timeout_s=5) as renderer:
            result = renderer.render_scene(self.scene_item)

        # Verify timeout handling
        assert result.success is False
        assert result.exit_code == -1
        assert result.error_message.startswith("Manim process killed")

    def test_video_output_detection_patterns(self):
        """T6.1: Test detection of Manim output files."""
        with ProductionManimRenderer(quality="1080p") as renderer:
            # Create test media directory structure
            media_dir = self.temp_dir / "media"

            # Test standard 1080p pattern
            output_dir = media_dir / "videos" / "main" / "1080p60"
            output_dir.mkdir(parents=True, exist_ok=True)
            test_video = output_dir / "TestScene_Simple.mp4"
            test_video.write_bytes(b"test video")

            # Test detection
            found_video = renderer._find_output_video(media_dir, "TestScene_Simple")
            assert found_video == test_video

            # Test fallback pattern
            alt_dir = media_dir / "videos" / "high_quality"
            alt_dir.mkdir(parents=True, exist_ok=True)
            alt_video = alt_dir / "TestScene_Simple.mp4"
            alt_video.write_bytes(b"alt video")

            # Remove original and test fallback
            test_video.unlink()
            found_video = renderer._find_output_video(media_dir, "TestScene_Simple")
            assert found_video == alt_video

    def test_error_message_parsing(self):
        """T6.1: Test parsing of error messages from Manim output."""
        with ProductionManimRenderer(quality="1080p") as renderer:
            # Test LaTeX error parsing
            stderr = "Some output\nLaTeX Error: Missing \\begin{document}\nMore output"
            error_msg = renderer._parse_error_message(stderr, "", 1)
            assert "LaTeX Error: Missing \\begin{document}" in error_msg

            # Test Python error parsing
            stderr = "Traceback\nNameError: name 'undefined_var' is not defined\n"
            error_msg = renderer._parse_error_message(stderr, "", 1)
            assert "NameError: name 'undefined_var' is not defined" in error_msg

            # Test generic error
            error_msg = renderer._parse_error_message("", "", 1)
            assert "exit code 1" in error_msg

    @patch("subprocess.run")
    def test_video_metadata_extraction(self, mock_subprocess):
        """T6.1: Test video metadata extraction using ffprobe."""
        # Mock ffprobe output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
        {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "nb_frames": "45"
                }
            ],
            "format": {
                "duration": "1.5"
            }
        }
        """
        mock_subprocess.return_value = mock_result

        # Create fake video file
        test_video = self.temp_dir / "test.mp4"
        test_video.write_bytes(b"fake video")

        with ProductionManimRenderer(quality="1080p") as renderer:
            metadata = renderer._get_video_metadata(test_video)

        assert metadata["duration_s"] == 1.5
        assert metadata["resolution"] == (1920, 1080)
        assert metadata["fps"] == 30.0
        assert metadata["frame_count"] == 45

    def test_fps_parsing(self):
        """T6.1: Test FPS string parsing from ffprobe."""
        with ProductionManimRenderer(quality="1080p") as renderer:
            # Test fraction format
            assert renderer._parse_fps("30/1") == 30.0
            assert renderer._parse_fps("24000/1001") == pytest.approx(23.976, rel=1e-2)

            # Test decimal format
            assert renderer._parse_fps("29.97") == 29.97

            # Test invalid format (should return default)
            default_fps = renderer.quality_preset.fps
            assert renderer._parse_fps("invalid") == default_fps
            assert renderer._parse_fps("30/0") == default_fps

    def test_render_scene_production_convenience_function(self):
        """T6.1: Test convenience function for rendering single scenes."""
        output_dir = self.temp_dir / "output"

        with patch(
            "generator.renderer.manim_prod.ProductionManimRenderer"
        ) as MockRenderer:
            mock_renderer = Mock()
            MockRenderer.return_value.__enter__.return_value = mock_renderer

            expected_result = ProductionRenderResult(success=True)
            mock_renderer.render_scene.return_value = expected_result

            result = render_scene_production(
                scene_item=self.scene_item,
                quality="720p",
                output_dir=output_dir,
                timeout_s=120,
            )

            assert result == expected_result
            MockRenderer.assert_called_once_with(quality="720p", timeout_s=120)

    def test_batch_render_scenes(self):
        """T6.1: Test batch rendering of multiple scenes."""
        # Create additional scene
        scene2 = SceneRenderItem(
            scene_id="test_second",
            class_name="TestScene_Second",
            main_py=self.test_main_py,
            est_duration_s=2.0,
        )

        scenes = [self.scene_item, scene2]
        output_dir = self.temp_dir / "output"

        with patch(
            "generator.renderer.manim_prod.ProductionManimRenderer"
        ) as MockRenderer:
            mock_renderer = Mock()
            MockRenderer.return_value.__enter__.return_value = mock_renderer

            # Mock successful renders
            mock_renderer.render_scene.side_effect = [
                ProductionRenderResult(success=True, output_mp4=Path("scene1.mp4")),
                ProductionRenderResult(success=True, output_mp4=Path("scene2.mp4")),
            ]

            results = batch_render_scenes(
                scenes=scenes,
                quality="1080p",
                output_dir=output_dir,
                timeout_per_scene_s=180,
            )

            assert len(results) == 2
            assert all(r.success for r in results)
            assert mock_renderer.render_scene.call_count == 2

    def test_batch_render_early_exit_on_critical_failure(self):
        """T6.1: Test batch rendering stops on critical failures."""
        scene2 = SceneRenderItem(
            scene_id="test_second",
            class_name="TestScene_Second",
            main_py=self.test_main_py,
            est_duration_s=2.0,
        )

        scenes = [self.scene_item, scene2]

        with patch(
            "generator.renderer.manim_prod.ProductionManimRenderer"
        ) as MockRenderer:
            mock_renderer = Mock()
            MockRenderer.return_value.__enter__.return_value = mock_renderer

            # First scene fails critically (process killed)
            mock_renderer.render_scene.side_effect = [
                ProductionRenderResult(success=False, exit_code=-9),  # SIGKILL
                ProductionRenderResult(success=True),  # This shouldn't be reached
            ]

            results = batch_render_scenes(scenes=scenes)

            # Should stop after first critical failure
            assert len(results) == 1
            assert not results[0].success
            assert results[0].exit_code == -9

    def test_resource_limits_configuration(self):
        """T6.1: Test resource limits are properly configured."""
        with patch("generator.renderer.manim_prod.SandboxEnvironment") as MockSandbox:
            mock_sandbox = Mock()
            MockSandbox.return_value.__enter__.return_value = mock_sandbox

            # Test custom limits
            renderer = ProductionManimRenderer(timeout_s=300, memory_mb=4096)

            # Trigger render to check sandbox limits
            mock_sandbox.write_file.return_value = Path("/tmp/main.py")
            mock_sandbox.execute_command.return_value = (0, "", "")

            renderer.render_scene(self.scene_item)

            # Verify sandbox was created with correct limits
            MockSandbox.assert_called_once()
            call_args = MockSandbox.call_args
            limits = call_args[1]["limits"]  # SandboxLimits passed as keyword arg

            assert limits.timeout_seconds == 300
            assert limits.max_memory_mb == 4096

    def test_production_environment_setup(self):
        """T6.1: Test production environment variables are set correctly."""
        with ProductionManimRenderer(quality="1080p") as renderer:
            # Create mock sandbox
            mock_sandbox = Mock()
            mock_sandbox.temp_dir = self.temp_dir / "sandbox"
            mock_sandbox.temp_dir.mkdir(exist_ok=True)

            env = renderer._get_production_environment(mock_sandbox)

            # Check environment variables
            assert env["MANIM_LOG_LEVEL"] == "ERROR"
            assert env["MANIMGL_LOG_LEVEL"] == "ERROR"
            assert env["MANIM_DISABLE_CACHING"] == "1"
            assert env["MANIM_QUALITY"] == "1080p"
            assert env["TMPDIR"] == str(mock_sandbox.temp_dir)

            # Check matplotlib config directory is set
            assert "MPLCONFIGDIR" in env
            mpl_dir = Path(env["MPLCONFIGDIR"])
            assert mpl_dir.exists()
            assert mpl_dir.parent == mock_sandbox.temp_dir

    def test_deterministic_render_settings(self):
        """T6.1: Test renders produce deterministic output."""
        # This test verifies that the same input produces the same command
        cmd1 = get_manim_command(
            quality="1080p",
            main_py_path="/test/main.py",
            class_name="TestScene",
            output_dir="/output",
            media_dir="/media",
        )

        cmd2 = get_manim_command(
            quality="1080p",
            main_py_path="/test/main.py",
            class_name="TestScene",
            output_dir="/output",
            media_dir="/media",
        )

        # Commands should be identical
        assert cmd1 == cmd2

        # Should always include disable_caching for deterministic builds
        assert "--disable_caching" in cmd1
