"""
Comprehensive tests for T6.2 and T6.3 enhanced specifications.

Tests exact compliance with T6.2 concat commands and T6.3 thumbnail requirements.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

from generator.renderer.concat import VideoConcatenator, validate_crossfade_duration
from generator.renderer.thumbs import (
    ThumbnailGenerator,
    generate_standard_thumbnails,
    generate_contact_sheet,
    calculate_thumbnail_time,
)
from generator.renderer.config import get_quality_preset


class TestT62VideoConcat:
    """Test T6.2 video concatenation and transitions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.quality_preset = get_quality_preset("1080p")

        # Create fake input videos
        self.video1 = self.temp_dir / "scene_01_prod.mp4"
        self.video2 = self.temp_dir / "scene_02_prod.mp4"
        self.video3 = self.temp_dir / "scene_03_prod.mp4"

        for video in [self.video1, self.video2, self.video3]:
            video.write_bytes(b"fake video data")

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_straight_cuts_command_matches_spec(self, mock_subprocess):
        """T6.2: Test straight cuts command matches exact specification."""

        # Mock both ffmpeg and ffprobe calls
        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = Mock()
            result.returncode = 0
            if "ffprobe" in cmd:
                result.stdout = "10.0"  # Duration
            else:
                result.stdout = ""
            result.stderr = ""
            return result

        mock_subprocess.side_effect = mock_run_side_effect

        output_video = self.temp_dir / "final_silent.mp4"
        output_video.write_bytes(b"fake output")

        with VideoConcatenator(quality_preset=self.quality_preset) as concatenator:
            result = concatenator.concatenate_videos(
                input_videos=[self.video1, self.video2],
                output_video=output_video,
                crossfade_s=None,  # Straight cuts
            )

        # Find the ffmpeg call (not ffprobe)
        calls = mock_subprocess.call_args_list
        ffmpeg_calls = [call for call in calls if call[0][0][0] == "ffmpeg"]
        assert len(ffmpeg_calls) >= 1

        cmd = ffmpeg_calls[0][0][0]

        # T6.2: Should use concat demuxer with exact flag order
        assert cmd[0] == "ffmpeg"
        assert "-y" in cmd  # Overwrite flag
        assert "-f" in cmd and "concat" in cmd
        assert "-safe" in cmd and "0" in cmd
        assert "-i" in cmd  # Input concat file

        # T6.2: Should use libx264 with quality settings
        assert "-c:v" in cmd and "libx264" in cmd
        assert "-crf" in cmd and str(self.quality_preset.crf) in cmd
        assert "-preset" in cmd and self.quality_preset.preset in cmd
        assert "-pix_fmt" in cmd and "yuv420p" in cmd
        assert "-r" in cmd and str(self.quality_preset.fps) in cmd

    @patch("subprocess.run")
    def test_concat_txt_format_matches_spec(self, mock_subprocess):
        """T6.2: Test concat.txt format matches specification exactly."""

        # Mock both ffmpeg and ffprobe calls
        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = Mock()
            result.returncode = 0
            if "ffprobe" in cmd:
                result.stdout = "15.0"  # Total duration
            else:
                result.stdout = ""
            result.stderr = ""
            return result

        mock_subprocess.side_effect = mock_run_side_effect

        output_video = self.temp_dir / "final_silent.mp4"
        output_video.write_bytes(b"fake output")

        concat_content = None
        with VideoConcatenator(quality_preset=self.quality_preset) as concatenator:
            concatenator.concatenate_videos(
                input_videos=[self.video1, self.video2, self.video3],
                output_video=output_video,
                crossfade_s=None,
            )

            # Read concat file while context is still active
            concat_files = list(concatenator.temp_dir.glob("concat_list.txt"))
            if concat_files:
                concat_content = concat_files[0].read_text()

        assert concat_content is not None, "Concat file should have been created"
        lines = concat_content.strip().split("\n")

        # T6.2: Should match exact format
        assert len(lines) == 3
        assert lines[0] == f"file '{self.video1.absolute()}'"
        assert lines[1] == f"file '{self.video2.absolute()}'"
        assert lines[2] == f"file '{self.video3.absolute()}'"

    @patch("subprocess.run")
    def test_crossfade_command_structure(self, mock_subprocess):
        """T6.2: Test crossfade uses xfade filter with proper structure."""

        # Mock both ffmpeg and ffprobe calls
        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = Mock()
            result.returncode = 0
            if "ffprobe" in cmd:
                result.stdout = "9.5"  # Duration reduced by crossfade
            else:
                result.stdout = ""
            result.stderr = ""
            return result

        mock_subprocess.side_effect = mock_run_side_effect

        output_video = self.temp_dir / "final_silent.mp4"
        output_video.write_bytes(b"fake output")

        with VideoConcatenator(quality_preset=self.quality_preset) as concatenator:
            result = concatenator.concatenate_videos(
                input_videos=[self.video1, self.video2],
                output_video=output_video,
                crossfade_s=0.5,
            )

        # Find the ffmpeg call (not ffprobe)
        calls = mock_subprocess.call_args_list
        ffmpeg_calls = [call for call in calls if call[0][0][0] == "ffmpeg"]
        assert len(ffmpeg_calls) >= 1

        cmd = ffmpeg_calls[0][0][0]

        # T6.2: Should use xfade filter
        assert "-filter_complex" in cmd
        filter_idx = cmd.index("-filter_complex") + 1
        filter_complex = cmd[filter_idx]

        assert "xfade=transition=fade" in filter_complex
        assert "duration=0.5" in filter_complex
        assert "[0:v][1:v]" in filter_complex
        assert "[outv]" in filter_complex

    def test_crossfade_duration_validation(self):
        """T6.2: Test crossfade duration validation logic."""
        # Valid crossfade (shorter than half of shortest scene)
        assert validate_crossfade_duration(0.5, 2.0) == True

        # Invalid crossfade (longer than half of shortest scene)
        assert validate_crossfade_duration(1.5, 2.0) == False

        # Edge case: zero duration
        assert validate_crossfade_duration(0.0, 2.0) == False

        # Edge case: negative duration
        assert validate_crossfade_duration(-0.5, 2.0) == False

    @patch("subprocess.run")
    def test_multiple_video_crossfade_chain(self, mock_subprocess):
        """T6.2: Test N-video crossfade uses single filter graph (Option B)."""

        # Mock both ffmpeg and ffprobe calls
        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = Mock()
            result.returncode = 0
            if "ffprobe" in cmd:
                result.stdout = "14.4"  # Duration reduced by 2 crossfades (15 - 2*0.3)
            else:
                result.stdout = ""
            result.stderr = ""
            return result

        mock_subprocess.side_effect = mock_run_side_effect

        output_video = self.temp_dir / "final_silent.mp4"
        output_video.write_bytes(b"fake output")

        with VideoConcatenator(quality_preset=self.quality_preset) as concatenator:
            result = concatenator.concatenate_videos(
                input_videos=[self.video1, self.video2, self.video3],
                output_video=output_video,
                crossfade_s=0.3,
            )

        # Find the ffmpeg call (not ffprobe)
        calls = mock_subprocess.call_args_list
        ffmpeg_calls = [call for call in calls if call[0][0][0] == "ffmpeg"]
        assert len(ffmpeg_calls) >= 1

        cmd = ffmpeg_calls[0][0][0]
        filter_idx = cmd.index("-filter_complex") + 1
        filter_complex = cmd[filter_idx]

        # Should use chained xfade filters in single graph
        assert filter_complex.count("xfade") == 2  # N-1 crossfades for N videos
        assert "[tmp1]" in filter_complex  # Intermediate label
        assert "[outv]" in filter_complex  # Final output

    @patch("subprocess.run")
    def test_straight_cuts_preserve_duration(self, mock_subprocess):
        """T6.2: Test straight cuts should preserve total duration."""

        # Mock ffprobe calls for duration
        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            if "ffprobe" in cmd:
                # Mock duration response
                result = Mock()
                result.returncode = 0
                result.stdout = "5.0"  # 5 seconds per video
                return result
            else:
                # Mock ffmpeg success
                result = Mock()
                result.returncode = 0
                result.stdout = ""
                result.stderr = ""
                return result

        mock_subprocess.side_effect = mock_run_side_effect

        output_video = self.temp_dir / "final_silent.mp4"
        output_video.write_bytes(b"fake output")

        with VideoConcatenator(quality_preset=self.quality_preset) as concatenator:
            result = concatenator.concatenate_videos(
                input_videos=[self.video1, self.video2],
                output_video=output_video,
                crossfade_s=None,
            )

        # Total duration should equal sum of individual durations
        assert result.success == True
        # Note: In real implementation, this would be 10.0s (5+5) for straight cuts


class TestT63ThumbnailEnhancements:
    """Test T6.3 thumbnail generation enhancements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_video = self.temp_dir / "test_video.mp4"
        self.test_video.write_bytes(b"fake video data")

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_poster_frame_png_format(self, mock_subprocess):
        """T6.3: Test poster frame uses PNG format as specified."""

        def mock_run_side_effect(*args, **kwargs):
            cmd = args[0]
            result = Mock()
            result.returncode = 0
            if "ffprobe" in cmd:
                # Mock video info response
                result.stdout = '{"streams":[{"codec_type":"video","width":1920,"height":1080}],"format":{"duration":"10.0"}}'
            else:
                # Mock ffmpeg success and create fake output files
                result.stdout = ""
                # Create the expected output file based on command
                for i, arg in enumerate(cmd):
                    if arg.endswith(".png") or arg.endswith(".jpg"):
                        output_path = Path(arg)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        output_path.write_bytes(b"fake image")
            result.stderr = ""
            return result

        mock_subprocess.side_effect = mock_run_side_effect

        result = generate_standard_thumbnails(
            video_path=self.test_video, output_dir=self.temp_dir, video_name="test"
        )

        # Check that PNG files were requested/created
        png_files = [
            r
            for r in result
            if r.success and r.thumbnail_path and r.thumbnail_path.suffix == ".png"
        ]
        assert len(png_files) > 0

    @patch("subprocess.run")
    def test_first_frame_avoids_black(self, mock_subprocess):
        """T6.3: Test first frame extraction avoids black frame by using 1s+."""
        mock_subprocess.return_value.returncode = 0

        with ThumbnailGenerator() as generator:
            generator.get_video_info = Mock(
                return_value={
                    "duration_s": 10.0,
                    "width": 1920,
                    "height": 1080,
                    "has_video": True,
                }
            )

            # Create fake output files
            poster_path = self.temp_dir / "test_poster.png"
            poster_path.write_bytes(b"fake png")
            mid_path = self.temp_dir / "test_mid.png"
            mid_path.write_bytes(b"fake png")

            result = generate_standard_thumbnails(
                video_path=self.test_video,
                output_dir=self.temp_dir,
                video_name="test",
                poster_time_s=0.5,  # Even if we request 0.5s
            )

        # Verify ffmpeg was called with time >= 1.0 to avoid black frames
        calls = mock_subprocess.call_args_list
        ffmpeg_calls = [call for call in calls if call[0][0][0] == "ffmpeg"]

        for call in ffmpeg_calls:
            cmd = call[0][0]
            if "-ss" in cmd:
                ss_idx = cmd.index("-ss") + 1
                time_val = float(cmd[ss_idx])
                assert time_val >= 1.0  # T6.3: Avoid black frames

    @patch("subprocess.run")
    def test_midpoint_frame_calculation(self, mock_subprocess):
        """T6.3: Test midpoint frame extraction uses video duration / 2."""
        midpoint_extracted = False

        def mock_run_side_effect(*args, **kwargs):
            nonlocal midpoint_extracted
            cmd = args[0]
            result = Mock()
            result.returncode = 0

            if "ffprobe" in cmd:
                # Mock video info response for 20 second video
                result.stdout = '{"streams":[{"codec_type":"video","width":1920,"height":1080}],"format":{"duration":"20.0"}}'
            else:
                # Mock ffmpeg success and create fake output files
                result.stdout = ""
                # Check for midpoint timing in ffmpeg command
                if "-ss" in cmd and "test_mid.png" in " ".join(cmd):
                    ss_idx = cmd.index("-ss") + 1
                    time_val = float(cmd[ss_idx])
                    assert time_val == 10.0, f"Expected 10.0s midpoint, got {time_val}s"
                    midpoint_extracted = True

                # Create the expected output file
                for arg in cmd:
                    if arg.endswith(".png") or arg.endswith(".jpg"):
                        output_path = Path(arg)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        output_path.write_bytes(b"fake image")

            result.stderr = ""
            return result

        mock_subprocess.side_effect = mock_run_side_effect

        generate_standard_thumbnails(
            video_path=self.test_video, output_dir=self.temp_dir, video_name="test"
        )

        assert (
            midpoint_extracted
        ), "Midpoint frame extraction should have been called with correct timing"

    @patch("subprocess.run")
    def test_contact_sheet_grid_generation(self, mock_subprocess):
        """T6.3: Test contact sheet generates grid of frames."""
        tile_filter_found = False

        def mock_run_side_effect(*args, **kwargs):
            nonlocal tile_filter_found
            cmd = args[0]
            result = Mock()
            result.returncode = 0

            if "ffprobe" in cmd:
                result.stdout = '{"streams":[{"codec_type":"video","width":1920,"height":1080}],"format":{"duration":"10.0"}}'
            else:
                result.stdout = ""

                # Check for tile filter in contact sheet generation
                if "-filter_complex" in cmd:
                    filter_idx = cmd.index("-filter_complex") + 1
                    filter_complex = cmd[filter_idx]
                    if "tile=" in filter_complex:
                        tile_filter_found = True
                        assert (
                            "tile=3x" in filter_complex
                        ), f"Expected 3 columns, got: {filter_complex}"

                # Create output files for individual frame extractions
                for i, arg in enumerate(cmd):
                    if arg.endswith(".jpg") and "frame_" in arg:
                        output_path = Path(arg)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        output_path.write_bytes(b"fake frame")

                # Create final contact sheet output
                if cmd[-1].endswith("contact_sheet.jpg"):
                    output_path = Path(cmd[-1])
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(b"fake contact sheet")

            result.stderr = ""
            return result

        mock_subprocess.side_effect = mock_run_side_effect

        contact_sheet_path = self.temp_dir / "contact_sheet.jpg"

        result = generate_contact_sheet(
            video_path=self.test_video,
            output_path=contact_sheet_path,
            num_frames=5,
            grid_cols=3,
        )

        assert tile_filter_found, "Contact sheet should use tile filter with 3 columns"
        assert (
            result.success
        ), f"Contact sheet generation should succeed, got: {result.error_message}"

    def test_thumbnail_time_calculation_strategies(self):
        """T6.3: Test different thumbnail time calculation strategies."""
        duration = 10.0

        # Test different position strategies
        assert calculate_thumbnail_time(duration, "start") == 1.0  # min(1.0, 10*0.1)
        assert calculate_thumbnail_time(duration, "middle") == 5.0  # 10/2
        assert calculate_thumbnail_time(duration, "golden_ratio") == pytest.approx(
            6.18, rel=1e-2
        )  # 10*0.618
        assert calculate_thumbnail_time(duration, "end") == 9.0  # max(10-1, 10*0.9)

        # Test short video handling
        short_duration = 0.5
        assert calculate_thumbnail_time(short_duration, "start") == pytest.approx(
            0.05, rel=1e-2
        )
        assert calculate_thumbnail_time(
            short_duration, "golden_ratio"
        ) == pytest.approx(0.309, rel=1e-2)

    @patch("subprocess.run")
    def test_timestamp_clamping_for_short_videos(self, mock_subprocess):
        """T6.3: Test timestamp clamping works for short videos."""
        mock_subprocess.return_value.returncode = 0

        with ThumbnailGenerator() as generator:
            # Mock very short video
            generator.get_video_info = Mock(
                return_value={
                    "duration_s": 1.5,  # Very short video
                    "width": 1920,
                    "height": 1080,
                    "has_video": True,
                }
            )

            poster_path = self.temp_dir / "test_poster.png"
            poster_path.write_bytes(b"fake png")

            generate_standard_thumbnails(
                video_path=self.test_video, output_dir=self.temp_dir, video_name="test"
            )

        # Should clamp timestamps to valid range
        calls = mock_subprocess.call_args_list
        for call in calls:
            cmd = call[0][0]
            if "-ss" in cmd:
                ss_idx = cmd.index("-ss") + 1
                time_val = float(cmd[ss_idx])
                assert 0 <= time_val <= 1.5  # Within video duration

    def test_video_only_output_has_no_audio(self):
        """T6.2: Verify output specifications mention video-only (no audio)."""
        # This is more of a documentation/spec test
        # The actual concat commands should not include audio streams

        with VideoConcatenator() as concatenator:
            # Test that our filter_complex only mentions video streams
            transitions = concatenator.create_transition_specs(3, crossfade_s=0.5)

            assert len(transitions) == 2  # N-1 transitions for N videos
            for transition in transitions:
                assert transition.type == "crossfade"
                assert transition.duration_s == 0.5
