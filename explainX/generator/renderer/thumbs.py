"""
T6.3: Thumbnail and poster frame generation.

Extracts representative frames from videos and creates thumbnails
in multiple sizes for different use cases.
"""

import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

from .config import THUMBNAIL_SETTINGS
import subprocess


@dataclass(frozen=True)
class ThumbnailSpec:
    """Specification for a thumbnail to generate."""

    width: int
    height: int
    time_s: float = 1.0  # Time position to extract frame from
    format: str = "jpg"
    quality: int = 85


@dataclass(frozen=True)
class ThumbnailResult:
    """Result of thumbnail generation."""

    success: bool
    thumbnail_path: Optional[Path] = None
    width: int = 0
    height: int = 0
    file_size_bytes: int = 0
    extraction_time_s: float = 0.0
    source_time_s: float = 0.0
    command: str = ""
    error_message: str = ""


class ThumbnailGenerator:
    """T6.3: Thumbnail generator using FFmpeg."""

    def __init__(self, temp_dir: Path = None):
        """Initialize thumbnail generator."""
        import tempfile

        self.temp_dir = temp_dir or Path(tempfile.mkdtemp(prefix="thumbnails_"))
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

    def generate_thumbnail(
        self, video_path: Path, output_path: Path, spec: ThumbnailSpec
    ) -> ThumbnailResult:
        """
        Generate a single thumbnail from video.

        Args:
            video_path: Source video file
            output_path: Output thumbnail file path
            spec: Thumbnail specification

        Returns:
            ThumbnailResult with generation details
        """
        start_time = time.time()

        try:
            # Validate input
            if not video_path.exists():
                return ThumbnailResult(
                    success=False,
                    extraction_time_s=time.time() - start_time,
                    error_message=f"Source video not found: {video_path}",
                )

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build FFmpeg command for frame extraction
            cmd = [
                "ffmpeg",
                "-i",
                str(video_path),
                "-ss",
                str(spec.time_s),  # Seek to time position
                "-frames:v",
                "1",  # Extract exactly 1 frame
                "-vf",
                f"scale={spec.width}:{spec.height}",  # Resize
                "-f",
                "image2",  # Image format
                "-y",
                str(output_path),  # Overwrite output
            ]

            # Add quality/format specific options
            if spec.format.lower() == "jpg":
                cmd.extend(["-q:v", str(100 - spec.quality)])  # FFmpeg quality scale
            elif spec.format.lower() == "png":
                # PNG uses compression level instead of quality
                cmd.extend(["-compression_level", "6"])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60  # 1 minute timeout
            )

            extraction_time = time.time() - start_time

            if result.returncode == 0 and output_path.exists():
                file_size = output_path.stat().st_size

                return ThumbnailResult(
                    success=True,
                    thumbnail_path=output_path,
                    width=spec.width,
                    height=spec.height,
                    file_size_bytes=file_size,
                    extraction_time_s=extraction_time,
                    source_time_s=spec.time_s,
                    command=" ".join(cmd),
                )
            else:
                return ThumbnailResult(
                    success=False,
                    extraction_time_s=extraction_time,
                    command=" ".join(cmd),
                    error_message=f"FFmpeg failed with exit code {result.returncode}: {result.stderr.strip()}",
                )

        except Exception as e:
            return ThumbnailResult(
                success=False,
                extraction_time_s=time.time() - start_time,
                error_message=f"Thumbnail generation failed: {str(e)}",
            )

    def generate_multiple_thumbnails(
        self,
        video_path: Path,
        output_dir: Path,
        specs: List[ThumbnailSpec],
        name_prefix: str = "thumb",
    ) -> List[ThumbnailResult]:
        """
        Generate multiple thumbnails with different specifications.

        Args:
            video_path: Source video file
            output_dir: Output directory for thumbnails
            specs: List of thumbnail specifications
            name_prefix: Prefix for thumbnail filenames

        Returns:
            List of ThumbnailResult, one per specification
        """
        results = []
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, spec in enumerate(specs):
            # Create filename with size and format
            filename = f"{name_prefix}_{spec.width}x{spec.height}.{spec.format}"
            output_path = output_dir / filename

            result = self.generate_thumbnail(video_path, output_path, spec)
            results.append(result)

        return results

    def generate_poster_frame(
        self,
        video_path: Path,
        output_path: Path,
        time_s: float = None,
        size: Tuple[int, int] = None,
    ) -> ThumbnailResult:
        """
        Generate a high-quality poster frame.

        Args:
            video_path: Source video file
            output_path: Output poster frame path
            time_s: Time position (defaults to config setting)
            size: Output size (defaults to large thumbnail size)

        Returns:
            ThumbnailResult
        """
        if time_s is None:
            time_s = THUMBNAIL_SETTINGS["poster_frame_time_s"]

        if size is None:
            # Use largest thumbnail size as default
            size = max(THUMBNAIL_SETTINGS["thumbnail_sizes"])

        spec = ThumbnailSpec(
            width=size[0],
            height=size[1],
            time_s=time_s,
            format="jpg",
            quality=95,  # High quality for poster
        )

        return self.generate_thumbnail(video_path, output_path, spec)

    def extract_frame_sequence(
        self,
        video_path: Path,
        output_dir: Path,
        start_s: float,
        duration_s: float,
        fps: float = 1.0,
        size: Tuple[int, int] = None,
    ) -> List[ThumbnailResult]:
        """
        Extract a sequence of frames at regular intervals.

        Args:
            video_path: Source video file
            output_dir: Output directory for frames
            start_s: Start time in seconds
            duration_s: Duration to extract frames over
            fps: Frame extraction rate (frames per second)
            size: Output frame size (optional)

        Returns:
            List of ThumbnailResult for extracted frames
        """
        results = []
        output_dir.mkdir(parents=True, exist_ok=True)

        # Calculate frame positions
        frame_interval_s = 1.0 / fps
        num_frames = int(duration_s * fps)

        for i in range(num_frames):
            time_pos = start_s + (i * frame_interval_s)

            # Create frame specification
            if size:
                width, height = size
            else:
                width, height = 640, 360  # Default size

            spec = ThumbnailSpec(
                width=width, height=height, time_s=time_pos, format="jpg", quality=85
            )

            # Output filename with frame number
            filename = f"frame_{i:04d}.jpg"
            output_path = output_dir / filename

            result = self.generate_thumbnail(video_path, output_path, spec)
            results.append(result)

            if not result.success:
                # Stop on first failure
                break

        return results

    def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """Get basic video information for thumbnail planning."""
        try:
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                str(video_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                import json

                probe_data = json.loads(result.stdout)

                # Find video stream
                video_stream = None
                for stream in probe_data.get("streams", []):
                    if stream.get("codec_type") == "video":
                        video_stream = stream
                        break

                if video_stream:
                    duration = float(probe_data.get("format", {}).get("duration", 0))
                    width = int(video_stream.get("width", 0))
                    height = int(video_stream.get("height", 0))

                    return {
                        "duration_s": duration,
                        "width": width,
                        "height": height,
                        "aspect_ratio": width / height if height > 0 else 1.0,
                        "has_video": True,
                    }

        except Exception:
            pass

        return {
            "duration_s": 0.0,
            "width": 0,
            "height": 0,
            "aspect_ratio": 1.0,
            "has_video": False,
        }


def generate_standard_thumbnails(
    video_path: Path,
    output_dir: Path,
    video_name: str = None,
    poster_time_s: float = None,
) -> List[ThumbnailResult]:
    """
    T6.3: Generate standard set of thumbnails for a video.

    Creates poster frame, midpoint frame, and multiple sizes as per T6.3 spec.

    Args:
        video_path: Source video file
        output_dir: Output directory
        video_name: Base name for thumbnails (defaults to video stem)
        poster_time_s: Time for poster frame extraction

    Returns:
        List of ThumbnailResult for all generated thumbnails
    """
    if video_name is None:
        video_name = video_path.stem

    if poster_time_s is None:
        poster_time_s = THUMBNAIL_SETTINGS["poster_frame_time_s"]

    results = []

    with ThumbnailGenerator() as generator:
        # T6.3: Get video info for midpoint calculation
        video_info = generator.get_video_info(video_path)
        video_duration = video_info.get("duration_s", 0)

        # T6.3: Generate poster frame (first frame after scene begins - avoid black)
        poster_time = max(1.0, poster_time_s)  # At least 1 second to avoid black frames
        poster_result = generator.generate_poster_frame(
            video_path=video_path,
            output_path=output_dir / f"{video_name}_poster.png",
            time_s=poster_time,
            size=(1280, 720),  # High quality poster
        )
        if poster_result.success:
            results.append(poster_result)

        # T6.3: Generate midpoint frame
        if video_duration > 2.0:  # Only if video is long enough
            midpoint_time = video_duration / 2.0
            mid_result = generator.generate_poster_frame(
                video_path=video_path,
                output_path=output_dir / f"{video_name}_mid.png",
                time_s=midpoint_time,
                size=(1280, 720),
            )
            if mid_result.success:
                results.append(mid_result)

        # Generate thumbnails for each configured size
        specs = []
        for width, height in THUMBNAIL_SETTINGS["thumbnail_sizes"]:
            specs.append(
                ThumbnailSpec(
                    width=width,
                    height=height,
                    time_s=poster_time,
                    format=THUMBNAIL_SETTINGS["format"],
                    quality=THUMBNAIL_SETTINGS["quality"],
                )
            )

        thumb_results = generator.generate_multiple_thumbnails(
            video_path=video_path,
            output_dir=output_dir,
            specs=specs,
            name_prefix=video_name,
        )
        results.extend(thumb_results)

    return results


def extract_video_poster(
    video_path: Path, poster_path: Path, time_s: float = None
) -> ThumbnailResult:
    """
    Extract a single high-quality poster frame.

    Args:
        video_path: Source video
        poster_path: Output poster path
        time_s: Time position for extraction

    Returns:
        ThumbnailResult
    """
    with ThumbnailGenerator() as generator:
        return generator.generate_poster_frame(
            video_path=video_path, output_path=poster_path, time_s=time_s
        )


def generate_contact_sheet(
    video_path: Path,
    output_path: Path,
    num_frames: int = 5,
    grid_cols: int = 3,
    frame_size: Tuple[int, int] = (320, 180),
) -> ThumbnailResult:
    """
    T6.3: Generate contact sheet with multiple frames from video.

    Args:
        video_path: Source video file
        output_path: Output contact sheet path
        num_frames: Number of frames to extract (default 5)
        grid_cols: Number of columns in grid (default 3)
        frame_size: Size of each frame (width, height)

    Returns:
        ThumbnailResult for the contact sheet
    """
    try:
        with ThumbnailGenerator() as generator:
            video_info = generator.get_video_info(video_path)
            duration = video_info.get("duration_s", 0)

            if duration <= 0:
                return ThumbnailResult(
                    success=False,
                    error_message="Cannot determine video duration for contact sheet",
                )

            # Calculate frame positions evenly distributed
            frame_times = []
            if num_frames == 1:
                frame_times = [duration * 0.5]
            else:
                for i in range(num_frames):
                    # Distribute frames from 10% to 90% of video duration
                    pos = 0.1 + (0.8 * i / (num_frames - 1))
                    frame_times.append(duration * pos)

            # Create temp directory for individual frames
            import tempfile

            temp_dir = Path(tempfile.mkdtemp(prefix="contact_sheet_"))

            try:
                # Extract individual frames
                frame_paths = []
                for i, time_pos in enumerate(frame_times):
                    frame_path = temp_dir / f"frame_{i:02d}.jpg"

                    spec = ThumbnailSpec(
                        width=frame_size[0],
                        height=frame_size[1],
                        time_s=time_pos,
                        format="jpg",
                        quality=85,
                    )

                    result = generator.generate_thumbnail(video_path, frame_path, spec)
                    if result.success:
                        frame_paths.append(frame_path)

                if not frame_paths:
                    return ThumbnailResult(
                        success=False,
                        error_message="Failed to extract any frames for contact sheet",
                    )

                # Use ffmpeg to create contact sheet grid
                grid_rows = (len(frame_paths) + grid_cols - 1) // grid_cols

                cmd = [
                    "ffmpeg",
                    "-y",  # Overwrite output
                ]

                # Add input frames
                for frame_path in frame_paths:
                    cmd.extend(["-i", str(frame_path)])

                # Create filter for tiling
                filter_inputs = "".join(f"[{i}:v]" for i in range(len(frame_paths)))
                tile_filter = f"{filter_inputs}tile={grid_cols}x{grid_rows}[out]"

                cmd.extend(
                    ["-filter_complex", tile_filter, "-map", "[out]", str(output_path)]
                )

                start_time = time.time()
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                processing_time = time.time() - start_time

                if result.returncode == 0 and output_path.exists():
                    file_size = output_path.stat().st_size
                    return ThumbnailResult(
                        success=True,
                        thumbnail_path=output_path,
                        width=frame_size[0] * grid_cols,
                        height=frame_size[1] * grid_rows,
                        file_size_bytes=file_size,
                        extraction_time_s=processing_time,
                        source_time_s=0.0,  # Multiple source times
                        command=" ".join(cmd),
                    )
                else:
                    return ThumbnailResult(
                        success=False,
                        extraction_time_s=processing_time,
                        error_message=f"Contact sheet generation failed: {result.stderr}",
                    )

            finally:
                # Cleanup temp directory
                import shutil

                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

    except Exception as e:
        return ThumbnailResult(
            success=False, error_message=f"Contact sheet generation error: {str(e)}"
        )


def calculate_thumbnail_time(
    video_duration_s: float, position: str = "golden_ratio"
) -> float:
    """
    Calculate optimal time position for thumbnail extraction.

    Args:
        video_duration_s: Video duration in seconds
        position: Position strategy ("start", "middle", "golden_ratio", "end")

    Returns:
        Time in seconds for thumbnail extraction
    """
    if video_duration_s <= 0:
        return 1.0

    if position == "start":
        return min(1.0, video_duration_s * 0.1)
    elif position == "middle":
        return video_duration_s * 0.5
    elif position == "golden_ratio":
        # Use golden ratio (≈0.618) for aesthetically pleasing position
        return video_duration_s * 0.618
    elif position == "end":
        return max(video_duration_s - 1.0, video_duration_s * 0.9)
    else:
        return min(1.0, video_duration_s * 0.1)
