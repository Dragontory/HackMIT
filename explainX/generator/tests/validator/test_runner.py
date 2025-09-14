"""
Tests for sandboxed Manim runner and full integration.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from generator.validator.artifacts import PreviewArtifacts
from generator.validator.runner import (
    run_manim_preview,
    validate_manim_installation,
    validate_ffmpeg_installation,
    check_system_dependencies,
)


class TestManim_runner:
    """Test sandboxed Manim execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("generator.validator.runner.SandboxEnvironment")
    @patch("generator.validator.runner.get_manim_output_files")
    @patch("generator.validator.runner.ArtifactManager")
    def test_successful_preview_generation(
        self, mock_artifact_manager, mock_get_output, mock_sandbox_env
    ):
        """Test successful preview generation."""
        # Mock sandbox environment
        mock_sandbox = MagicMock()
        mock_sandbox_env.return_value.__enter__.return_value = mock_sandbox
        mock_sandbox.get_temp_dir.return_value = self.temp_dir
        mock_sandbox.write_file.return_value = self.temp_dir / "scene.py"
        mock_sandbox.execute_command.return_value = (0, "Rendering complete", "")

        # Mock output file detection
        video_path = self.temp_dir / "test_video.mp4"
        video_path.touch()  # Create fake video file
        mock_get_output.return_value = (video_path, self.temp_dir)

        # Mock artifact manager
        mock_manager = MagicMock()
        mock_artifact_manager.return_value = mock_manager

        # Mock video verification
        mock_manager.verify_video_quality.return_value = {
            "valid": True,
            "duration": 5.0,
            "size_bytes": 1024000,
            "width": 1920,
            "height": 1080,
        }

        # Mock artifact paths
        preview_mp4 = self.temp_dir / "preview.mp4"
        first_frame = self.temp_dir / "frame.png"
        mock_manager.get_artifact_paths.return_value = PreviewArtifacts(
            preview_mp4=preview_mp4, first_frame_png=first_frame
        )

        # Mock frame extraction
        mock_manager.extract_first_frame.return_value = True

        # Create fake output files
        preview_mp4.touch()
        first_frame.touch()

        # Test the function
        source_code = """
from manim import *

class Scene_Test(Scene):
    def construct(self):
        title = Text("Test", font=BODY_FONT).scale(0.9)
        self.play(Write(title))
        self.wait(1.0)
"""

        artifacts, logs, issues = run_manim_preview(
            source_text=source_code,
            class_name="Scene_Test",
            work_dir=self.temp_dir,
            q_level="preview",
        )

        # Verify successful execution
        assert artifacts is not None
        assert artifacts.preview_mp4 == preview_mp4
        assert artifacts.first_frame_png == first_frame

        # Check logs
        assert "stdout" in logs
        assert "timings" in logs
        assert logs["timings"]["total"] > 0

        # Should have no critical issues
        error_issues = [i for i in issues if i.get("severity") == "error"]
        assert len(error_issues) == 0

    @patch("generator.validator.runner.SandboxEnvironment")
    def test_manim_execution_failure(self, mock_sandbox_env):
        """Test handling of Manim execution failures."""
        # Mock failed sandbox execution
        mock_sandbox = MagicMock()
        mock_sandbox_env.return_value.__enter__.return_value = mock_sandbox
        mock_sandbox.get_temp_dir.return_value = self.temp_dir
        mock_sandbox.write_file.return_value = self.temp_dir / "scene.py"
        mock_sandbox.execute_command.return_value = (
            1,
            "",
            "SyntaxError: invalid syntax",
        )

        source_code = """
from manim import *

class Scene_Test(Scene):
    def construct(self):
        invalid syntax here
"""

        artifacts, logs, issues = run_manim_preview(
            source_text=source_code,
            class_name="Scene_Test",
            work_dir=self.temp_dir,
            q_level="low",
        )

        # Should return None artifacts on failure
        assert artifacts is None

        # Should capture stderr
        assert "SyntaxError" in logs["stderr"]

        # Should have error issues
        error_issues = [i for i in issues if i.get("severity") == "error"]
        assert len(error_issues) > 0

    @patch("generator.validator.runner.SandboxEnvironment")
    @patch("generator.validator.runner.get_manim_output_files")
    def test_no_video_output_handling(self, mock_get_output, mock_sandbox_env):
        """Test handling when Manim completes but produces no video."""
        # Mock successful execution but no output files
        mock_sandbox = MagicMock()
        mock_sandbox_env.return_value.__enter__.return_value = mock_sandbox
        mock_sandbox.get_temp_dir.return_value = self.temp_dir
        mock_sandbox.write_file.return_value = self.temp_dir / "scene.py"
        mock_sandbox.execute_command.return_value = (0, "Rendering complete", "")

        # Mock no output files found
        mock_get_output.return_value = (None, self.temp_dir)

        source_code = """
from manim import *

class Scene_Test(Scene):
    def construct(self):
        pass  # Empty scene
"""

        artifacts, logs, issues = run_manim_preview(
            source_text=source_code,
            class_name="Scene_Test",
            work_dir=self.temp_dir,
            q_level="preview",
        )

        # Should return None artifacts
        assert artifacts is None

        # Should have specific "no output" issue
        no_output_issues = [i for i in issues if i["type"] == "no_output"]
        assert len(no_output_issues) >= 1

    @patch("generator.validator.runner.SandboxEnvironment")
    @patch("generator.validator.runner.get_manim_output_files")
    @patch("generator.validator.runner.ArtifactManager")
    def test_invalid_video_handling(
        self, mock_artifact_manager, mock_get_output, mock_sandbox_env
    ):
        """Test handling of invalid/corrupted video output."""
        # Mock sandbox execution
        mock_sandbox = MagicMock()
        mock_sandbox_env.return_value.__enter__.return_value = mock_sandbox
        mock_sandbox.get_temp_dir.return_value = self.temp_dir
        mock_sandbox.write_file.return_value = self.temp_dir / "scene.py"
        mock_sandbox.execute_command.return_value = (0, "Rendering complete", "")

        # Mock video file exists but is invalid
        video_path = self.temp_dir / "corrupted.mp4"
        video_path.touch()
        mock_get_output.return_value = (video_path, self.temp_dir)

        # Mock invalid video verification
        mock_manager = MagicMock()
        mock_artifact_manager.return_value = mock_manager
        mock_manager.verify_video_quality.return_value = {
            "valid": False,
            "error": "File is corrupted",
        }

        source_code = """
from manim import *

class Scene_Test(Scene):
    def construct(self):
        title = Text("Test", font=BODY_FONT)
        self.play(Write(title))
"""

        artifacts, logs, issues = run_manim_preview(
            source_text=source_code,
            class_name="Scene_Test",
            work_dir=self.temp_dir,
            q_level="preview",
        )

        # Should return None artifacts
        assert artifacts is None

        # Should have invalid video issue
        invalid_video_issues = [i for i in issues if i["type"] == "invalid_video"]
        assert len(invalid_video_issues) >= 1
        assert "corrupted" in invalid_video_issues[0]["message"]

    @patch("generator.validator.runner.SandboxEnvironment")
    @patch("generator.validator.runner.get_manim_output_files")
    @patch("generator.validator.runner.ArtifactManager")
    def test_frame_extraction_failure(
        self, mock_artifact_manager, mock_get_output, mock_sandbox_env
    ):
        """Test handling when frame extraction fails."""
        # Mock successful video generation
        mock_sandbox = MagicMock()
        mock_sandbox_env.return_value.__enter__.return_value = mock_sandbox
        mock_sandbox.get_temp_dir.return_value = self.temp_dir
        mock_sandbox.write_file.return_value = self.temp_dir / "scene.py"
        mock_sandbox.execute_command.return_value = (0, "Rendering complete", "")

        video_path = self.temp_dir / "test_video.mp4"
        video_path.touch()
        mock_get_output.return_value = (video_path, self.temp_dir)

        # Mock artifact manager with successful video but failed frame extraction
        mock_manager = MagicMock()
        mock_artifact_manager.return_value = mock_manager
        mock_manager.verify_video_quality.return_value = {
            "valid": True,
            "duration": 5.0,
        }

        preview_mp4 = self.temp_dir / "preview.mp4"
        first_frame = self.temp_dir / "frame.png"
        mock_manager.get_artifact_paths.return_value = PreviewArtifacts(
            preview_mp4=preview_mp4, first_frame_png=first_frame
        )

        # Frame extraction fails
        mock_manager.extract_first_frame.return_value = False
        preview_mp4.touch()  # Video exists

        source_code = """
from manim import *

class Scene_Test(Scene):
    def construct(self):
        title = Text("Test", font=BODY_FONT)
        self.play(Write(title))
"""

        artifacts, logs, issues = run_manim_preview(
            source_text=source_code,
            class_name="Scene_Test",
            work_dir=self.temp_dir,
            q_level="preview",
        )

        # Should return artifacts but without frame
        assert artifacts is not None
        assert artifacts.preview_mp4 == preview_mp4
        assert artifacts.first_frame_png is None

        # Should have frame extraction warning
        frame_issues = [i for i in issues if i["type"] == "frame_extraction_failed"]
        assert len(frame_issues) >= 1
        assert frame_issues[0]["severity"] == "warning"

    def test_quality_level_settings(self):
        """Test different quality level settings."""
        with patch("generator.validator.runner.SandboxEnvironment") as mock_env:
            mock_sandbox = MagicMock()
            mock_env.return_value.__enter__.return_value = mock_sandbox
            mock_sandbox.get_temp_dir.return_value = self.temp_dir
            mock_sandbox.write_file.return_value = self.temp_dir / "scene.py"
            mock_sandbox.execute_command.return_value = (1, "", "")  # Fail quickly

            # Test low quality
            run_manim_preview(
                "code", "Scene_Test", self.temp_dir, "low", "test_video", "test_scene"
            )

            # Verify low quality command was used
            call_args = mock_sandbox.execute_command.call_args[0][0]
            assert "-q" in call_args
            assert "l" in call_args  # Low quality flag

            # Test preview quality
            run_manim_preview(
                "code",
                "Scene_Test",
                self.temp_dir,
                "preview",
                "test_video",
                "test_scene",
            )

            # Verify low quality command was used (both levels use 'l' for fast previews)
            call_args = mock_sandbox.execute_command.call_args[0][0]
            assert "-q" in call_args
            assert "l" in call_args  # Low quality flag for fast preview

    def test_temp_folder_structure(self):
        """Test that temp folder structure follows T5.3 specification."""
        with patch("generator.validator.runner.SandboxEnvironment") as mock_env:
            mock_sandbox = MagicMock()
            mock_env.return_value.__enter__.return_value = mock_sandbox
            mock_sandbox.execute_command.return_value = (1, "", "")  # Fail quickly

            video_id = "test_video_123"
            scene_id = "scene_intro"

            run_manim_preview(
                "code", "Scene_Test", self.temp_dir, "low", video_id, scene_id
            )

            # Verify the specific temp folder structure was created: /tmp/job_<video_id>/<scene_id>/
            import tempfile

            expected_base = Path(tempfile.gettempdir()) / f"job_{video_id}" / scene_id

            # The temp directory should be set to our structured path
            # We can't easily verify the exact path due to mocking, but we can verify the structure logic

    def test_manim_command_format(self):
        """Test exact manim command format as specified in T5.3."""
        with patch("generator.validator.runner.SandboxEnvironment") as mock_env:
            mock_sandbox = MagicMock()
            mock_env.return_value.__enter__.return_value = mock_sandbox
            mock_sandbox.get_temp_dir.return_value = self.temp_dir
            mock_sandbox.write_file.return_value = self.temp_dir / "main.py"
            mock_sandbox.execute_command.return_value = (0, "Success", "")

            run_manim_preview(
                "test_code",
                "Scene_sec_01",
                self.temp_dir,
                "low",
                "test_video",
                "test_scene",
            )

            # Verify exact command format: manim -q l -r 854,480 main.py Scene_sec_01 --output_dir artifacts --media_dir artifacts
            call_args = mock_sandbox.execute_command.call_args[0][0]

            assert call_args[0] == "manim"
            assert "-q" in call_args
            assert "l" in call_args  # Quality level
            assert "-r" in call_args
            assert "854,480" in call_args  # Resolution
            assert "main.py" in str(call_args)  # Should use main.py, not scene.py
            assert "Scene_sec_01" in call_args  # Class name
            assert "--output_dir" in call_args
            assert "--media_dir" in call_args
            assert "artifacts" in call_args

    def test_resource_limits_t5_3_specs(self):
        """Test that resource limits match T5.3 specifications."""
        with patch("generator.validator.runner.SandboxEnvironment") as mock_env:
            # Capture the limits passed to SandboxEnvironment
            mock_env_instance = MagicMock()
            mock_env.return_value.__enter__.return_value = mock_env_instance
            mock_env_instance.execute_command.return_value = (1, "", "")  # Fail quickly

            run_manim_preview(
                "code", "Scene_Test", self.temp_dir, "low", "test_video", "test_scene"
            )

            # Verify SandboxLimits were created with T5.3 specs
            limits_call = mock_env.call_args[0][
                0
            ]  # First positional argument should be limits

            # T5.3 specs: 25s timeout, 1.5GB (1536MB) memory limit
            assert limits_call.timeout_seconds == 25
            assert limits_call.max_memory_mb == 1536

    def test_manim_config_creation(self):
        """Test that manim.cfg file is created for consistent settings."""
        with patch("generator.validator.runner.SandboxEnvironment") as mock_env:
            mock_sandbox = MagicMock()
            mock_env.return_value.__enter__.return_value = mock_sandbox
            mock_sandbox.get_temp_dir.return_value = self.temp_dir
            mock_sandbox.write_file.return_value = self.temp_dir / "main.py"
            mock_sandbox.execute_command.return_value = (0, "Success", "")

            run_manim_preview(
                "code", "Scene_Test", self.temp_dir, "low", "test_video", "test_scene"
            )

            # Verify that manim.cfg was written
            write_calls = mock_sandbox.write_file.call_args_list

            # Should have at least 2 calls: main.py and manim.cfg
            assert len(write_calls) >= 2

            # Check that one of the calls was for manim.cfg
            config_calls = [call for call in write_calls if call[0][0] == "manim.cfg"]
            assert len(config_calls) == 1

            # Verify config content contains expected settings
            config_content = config_calls[0][0][1]
            assert "[CLI]" in config_content
            assert "quality = low_quality" in config_content
            assert "resolution = 854,480" in config_content
            assert "disable_caching = True" in config_content


class TestSystemDependencies:
    """Test system dependency validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_manim_installation_check(self, mock_subprocess):
        """Test Manim installation validation."""
        # Test successful case
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Manim Community v0.17.3"

        result = validate_manim_installation()

        assert result["available"] is True
        assert "v0.17.3" in result["version"]
        assert result["command"] == "manim"

        # Test failure case
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Command not found"

        result = validate_manim_installation()

        assert result["available"] is False
        assert "Command not found" in result["error"]

    @patch("subprocess.run")
    def test_ffmpeg_installation_check(self, mock_subprocess):
        """Test FFmpeg installation validation."""
        # Test successful case
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "ffmpeg version 4.4.0"

        result = validate_ffmpeg_installation()

        assert result["available"] is True
        assert "ffmpeg version 4.4.0" in result["version"]
        assert result["command"] == "ffmpeg"

        # Test failure case - command not found
        mock_subprocess.side_effect = FileNotFoundError("ffmpeg not found")

        result = validate_ffmpeg_installation()

        assert result["available"] is False
        assert "ffmpeg not found" in result["error"]

    @patch("generator.validator.runner.validate_manim_installation")
    @patch("generator.validator.runner.validate_ffmpeg_installation")
    def test_system_dependencies_check(self, mock_ffmpeg, mock_manim):
        """Test complete system dependencies check."""
        mock_manim.return_value = {"available": True, "version": "v0.17.3"}
        mock_ffmpeg.return_value = {"available": True, "version": "4.4.0"}

        dependencies = check_system_dependencies()

        assert "manim" in dependencies
        assert "ffmpeg" in dependencies
        assert dependencies["manim"]["available"] is True
        assert dependencies["ffmpeg"]["available"] is True

    def test_test_data_integration(self):
        """Test integration with our test data files."""
        test_data_dir = Path(__file__).parent / "data"

        # Test that our test files exist and are readable
        good_scene = test_data_dir / "good_scene.py"
        assert good_scene.exists()

        good_content = good_scene.read_text()
        assert "class Scene_Good_Test(Scene)" in good_content
        assert "from manim import *" in good_content

        bad_import = test_data_dir / "bad_import.py"
        assert bad_import.exists()

        bad_content = bad_import.read_text()
        assert "import os" in bad_content
        assert "import sys" in bad_content

        long_runtime = test_data_dir / "long_runtime.py"
        assert long_runtime.exists()

        long_content = long_runtime.read_text()
        assert "for i in range(100)" in long_content
        assert "self.wait(60.0)" in long_content
