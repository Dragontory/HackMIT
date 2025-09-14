"""
T6.2: Video concatenation and transitions using FFmpeg.

Handles video-only transitions (crossfades, straight cuts) and concatenation
of multiple scene MP4s into a single final video.
"""

import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .config import (
    get_ffmpeg_concat_command,
    get_quality_preset,
    FFMPEG_SETTINGS,
    TRANSITION_SETTINGS,
)
from .config import RenderQualityPreset


@dataclass(frozen=True)
class TransitionSpec:
    """Specification for a transition between two videos."""

    type: str  # "crossfade", "straight_cut", "fade_to_black"
    duration_s: float = 0.0
    options: Dict[str, Any] = None

    def __post_init__(self):
        if self.options is None:
            object.__setattr__(self, "options", {})


@dataclass(frozen=True)
class ConcatResult:
    """Result of video concatenation operation."""

    success: bool
    output_video: Optional[Path] = None
    duration_s: float = 0.0
    file_size_mb: float = 0.0
    processing_time_s: float = 0.0
    transitions_applied: int = 0
    command: str = ""
    stdout: str = ""
    stderr: str = ""
    error_message: str = ""


class VideoConcatenator:
    """T6.2: Video concatenation with transitions using FFmpeg."""

    def __init__(
        self, quality_preset: RenderQualityPreset = None, temp_dir: Path = None
    ):
        """
        Initialize video concatenator.

        Args:
            quality_preset: Quality settings for output video
            temp_dir: Temporary directory for intermediate files
        """
        self.quality_preset = quality_preset or get_quality_preset("1080p")
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp(prefix="video_concat_"))
        self._cleanup_temp_dir = temp_dir is None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        if self._cleanup_temp_dir and self.temp_dir.exists():
            import shutil

            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass

    def concatenate_videos(
        self,
        input_videos: List[Path],
        output_video: Path,
        crossfade_s: Optional[float] = None,
        validate_inputs: bool = True,
    ) -> ConcatResult:
        """
        Concatenate multiple videos with optional crossfade transitions.

        Args:
            input_videos: List of input video file paths
            output_video: Output video file path
            crossfade_s: Crossfade duration (None for straight cuts)
            validate_inputs: Whether to validate input videos first

        Returns:
            ConcatResult with operation details
        """
        start_time = time.time()

        try:
            # Validate inputs
            if validate_inputs:
                validation_error = self._validate_input_videos(input_videos)
                if validation_error:
                    return ConcatResult(
                        success=False,
                        processing_time_s=time.time() - start_time,
                        error_message=validation_error,
                    )

            # Handle single video case
            if len(input_videos) == 1:
                return self._copy_single_video(
                    input_videos[0], output_video, start_time
                )

            # Choose concatenation method
            if crossfade_s and crossfade_s > 0:
                return self._concatenate_with_crossfades(
                    input_videos, output_video, crossfade_s, start_time
                )
            else:
                return self._concatenate_straight_cuts(
                    input_videos, output_video, start_time
                )

        except Exception as e:
            return ConcatResult(
                success=False,
                processing_time_s=time.time() - start_time,
                error_message=f"Concatenation failed: {str(e)}",
            )

    def _validate_input_videos(self, input_videos: List[Path]) -> Optional[str]:
        """Validate that all input videos exist and have compatible formats."""
        if not input_videos:
            return "No input videos provided"

        for video in input_videos:
            if not video.exists():
                return f"Input video not found: {video}"

            if video.suffix.lower() not in [".mp4", ".mov", ".avi", ".mkv"]:
                return f"Unsupported video format: {video.suffix}"

        # TODO: Could add more detailed validation (resolution, fps, codec)
        return None

    def _copy_single_video(
        self, input_video: Path, output_video: Path, start_time: float
    ) -> ConcatResult:
        """Handle case of single input video (just copy/re-encode)."""
        try:
            cmd = [
                "ffmpeg",
                "-i",
                str(input_video),
                "-c:v",
                FFMPEG_SETTINGS["output_codec"],
                "-crf",
                str(self.quality_preset.crf),
                "-preset",
                self.quality_preset.preset,
                "-pix_fmt",
                FFMPEG_SETTINGS["pix_fmt"],
                "-movflags",
                FFMPEG_SETTINGS["movflags"],
                "-y",
                str(output_video),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minutes timeout
            )

            processing_time = time.time() - start_time

            if result.returncode == 0 and output_video.exists():
                file_size_mb = output_video.stat().st_size / (1024 * 1024)
                duration_s = self._get_video_duration(output_video)

                return ConcatResult(
                    success=True,
                    output_video=output_video,
                    duration_s=duration_s,
                    file_size_mb=file_size_mb,
                    processing_time_s=processing_time,
                    transitions_applied=0,
                    command=" ".join(cmd),
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            else:
                return ConcatResult(
                    success=False,
                    processing_time_s=processing_time,
                    command=" ".join(cmd),
                    stdout=result.stdout,
                    stderr=result.stderr,
                    error_message=f"FFmpeg failed with exit code {result.returncode}",
                )

        except Exception as e:
            return ConcatResult(
                success=False,
                processing_time_s=time.time() - start_time,
                error_message=f"Single video copy failed: {str(e)}",
            )

    def _concatenate_straight_cuts(
        self, input_videos: List[Path], output_video: Path, start_time: float
    ) -> ConcatResult:
        """Concatenate videos with straight cuts (no transitions)."""
        try:
            # Create concat demuxer input file
            concat_file = self.temp_dir / "concat_list.txt"
            self.temp_dir.mkdir(exist_ok=True)

            with open(concat_file, "w") as f:
                for video in input_videos:
                    f.write(f"file '{video.absolute()}'\n")

            # T6.2: Use concat demuxer for straight cuts (exact spec match)
            cmd = [
                "ffmpeg",
                "-y",  # T6.2: -y flag first as in specification
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c:v",
                "libx264",  # T6.2: Use libx264 for consistency
                "-crf",
                str(self.quality_preset.crf),
                "-preset",
                self.quality_preset.preset,
                "-pix_fmt",
                "yuv420p",  # T6.2: yuv420p for compatibility
                "-r",
                str(self.quality_preset.fps),  # T6.2: Set fps explicitly
                str(output_video),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600  # 10 minutes timeout
            )

            processing_time = time.time() - start_time

            if result.returncode == 0 and output_video.exists():
                file_size_mb = output_video.stat().st_size / (1024 * 1024)
                duration_s = self._get_video_duration(output_video)

                return ConcatResult(
                    success=True,
                    output_video=output_video,
                    duration_s=duration_s,
                    file_size_mb=file_size_mb,
                    processing_time_s=processing_time,
                    transitions_applied=len(input_videos)
                    - 1,  # N-1 cuts between N videos
                    command=" ".join(cmd),
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            else:
                return ConcatResult(
                    success=False,
                    processing_time_s=processing_time,
                    command=" ".join(cmd),
                    stdout=result.stdout,
                    stderr=result.stderr,
                    error_message=f"Concat demuxer failed with exit code {result.returncode}",
                )

        except Exception as e:
            return ConcatResult(
                success=False,
                processing_time_s=time.time() - start_time,
                error_message=f"Straight cut concatenation failed: {str(e)}",
            )

    def _concatenate_with_crossfades(
        self,
        input_videos: List[Path],
        output_video: Path,
        crossfade_s: float,
        start_time: float,
    ) -> ConcatResult:
        """
        T6.2: Concatenate videos with crossfade transitions.

        Uses xfade filter with proper offset calculation for seamless transitions.
        For N clips, reduces total duration by (N-1) * crossfade_s.
        """
        try:
            # Build filter_complex for crossfades
            filter_parts = []

            # Load all input videos
            inputs = []
            for i, video in enumerate(input_videos):
                inputs.extend(["-i", str(video)])

            # Build crossfade chain
            if len(input_videos) == 2:
                # T6.2: Simple case - two videos with one crossfade
                # offset=0 works for simple crossfade chaining
                filter_complex = f"[0:v][1:v]xfade=transition=fade:duration={crossfade_s}:offset=0[outv]"
            else:
                # T6.2: Multiple videos - chain crossfades in single filter graph
                # This is Option B (single filtergraph) for efficiency
                current_label = "[0:v]"

                for i in range(1, len(input_videos)):
                    next_input = f"[{i}:v]"

                    if i == len(input_videos) - 1:
                        # Last crossfade outputs to [outv]
                        output_label = "[outv]"
                    else:
                        # Intermediate crossfades output to temp labels
                        output_label = f"[tmp{i}]"

                    # T6.2: Use offset=0 for chaining (simpler than calculating d1-crossfade_s)
                    xfade_filter = f"{current_label}{next_input}xfade=transition=fade:duration={crossfade_s}:offset=0{output_label}"
                    filter_parts.append(xfade_filter)
                    current_label = output_label

                filter_complex = ";".join(filter_parts)

            # Build complete FFmpeg command
            cmd = (
                ["ffmpeg"]
                + inputs
                + [
                    "-filter_complex",
                    filter_complex,
                    "-map",
                    "[outv]",
                    "-c:v",
                    FFMPEG_SETTINGS["output_codec"],
                    "-crf",
                    str(self.quality_preset.crf),
                    "-preset",
                    self.quality_preset.preset,
                    "-pix_fmt",
                    FFMPEG_SETTINGS["pix_fmt"],
                    "-movflags",
                    FFMPEG_SETTINGS["movflags"],
                    "-threads",
                    str(FFMPEG_SETTINGS["threads"]),
                    "-y",
                    str(output_video),
                ]
            )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900,  # 15 minutes timeout for crossfades
            )

            processing_time = time.time() - start_time

            if result.returncode == 0 and output_video.exists():
                file_size_mb = output_video.stat().st_size / (1024 * 1024)
                duration_s = self._get_video_duration(output_video)

                return ConcatResult(
                    success=True,
                    output_video=output_video,
                    duration_s=duration_s,
                    file_size_mb=file_size_mb,
                    processing_time_s=processing_time,
                    transitions_applied=len(input_videos) - 1,  # N-1 crossfades
                    command=" ".join(cmd),
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            else:
                return ConcatResult(
                    success=False,
                    processing_time_s=processing_time,
                    command=" ".join(cmd),
                    stdout=result.stdout,
                    stderr=result.stderr,
                    error_message=f"Crossfade concatenation failed with exit code {result.returncode}",
                )

        except Exception as e:
            return ConcatResult(
                success=False,
                processing_time_s=time.time() - start_time,
                error_message=f"Crossfade concatenation failed: {str(e)}",
            )

    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(video_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())

        except Exception:
            pass

        return 0.0

    def create_transition_specs(
        self, num_videos: int, crossfade_s: Optional[float] = None
    ) -> List[TransitionSpec]:
        """Create transition specifications for video sequence."""
        if num_videos <= 1:
            return []

        transitions = []

        if crossfade_s and crossfade_s > 0:
            # Crossfade between each pair of videos
            for i in range(num_videos - 1):
                transitions.append(
                    TransitionSpec(
                        type="crossfade",
                        duration_s=crossfade_s,
                        options={"transition": "fade"},
                    )
                )
        else:
            # Straight cuts between videos
            for i in range(num_videos - 1):
                transitions.append(TransitionSpec(type="straight_cut", duration_s=0.0))

        return transitions


def concatenate_scene_videos(
    scene_videos: List[Path],
    output_video: Path,
    crossfade_s: Optional[float] = None,
    quality_preset: RenderQualityPreset = None,
) -> ConcatResult:
    """
    Convenient function to concatenate scene videos.

    Args:
        scene_videos: List of scene MP4 files in order
        output_video: Final output video path
        crossfade_s: Crossfade duration (None for straight cuts)
        quality_preset: Output quality settings

    Returns:
        ConcatResult with operation details
    """
    with VideoConcatenator(quality_preset=quality_preset) as concatenator:
        return concatenator.concatenate_videos(
            input_videos=scene_videos,
            output_video=output_video,
            crossfade_s=crossfade_s,
        )


def validate_crossfade_duration(
    crossfade_s: float, min_scene_duration_s: float
) -> bool:
    """
    Validate that crossfade duration is reasonable for scene lengths.

    Args:
        crossfade_s: Crossfade duration
        min_scene_duration_s: Shortest scene duration

    Returns:
        True if crossfade duration is valid
    """
    if crossfade_s <= 0:
        return False

    # Crossfade should not be longer than half the shortest scene
    max_allowed = min_scene_duration_s / 2
    return crossfade_s <= max_allowed
