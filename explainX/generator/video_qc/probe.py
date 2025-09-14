"""
T7.1: FFprobe wrapper for video metadata collection.

Provides functions to extract comprehensive video metadata using ffprobe,
including duration, resolution, fps, codec information, and frame counts.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass(frozen=True)
class VideoMetadata:
    """Structured video metadata from ffprobe."""

    duration_s: float
    width: int
    height: int
    fps: float
    frame_count: int
    codec: str
    pixel_format: str
    bitrate_kbps: Optional[int] = None
    container_format: str = "mp4"

    @property
    def resolution(self) -> str:
        """Get resolution as WxH string."""
        return f"{self.width}x{self.height}"

    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio as width/height."""
        return self.width / self.height if self.height > 0 else 0.0


class VideoProbe:
    """T7.1: FFprobe wrapper for video analysis."""

    def __init__(self, timeout_s: int = 30):
        """
        Initialize video probe.

        Args:
            timeout_s: Timeout for ffprobe operations
        """
        self.timeout_s = timeout_s

    def probe_video(self, video_path: Path) -> VideoMetadata:
        """
        Extract comprehensive video metadata using ffprobe.

        Args:
            video_path: Path to video file

        Returns:
            VideoMetadata with extracted information

        Raises:
            FileNotFoundError: If video file doesn't exist
            subprocess.CalledProcessError: If ffprobe fails
            ValueError: If metadata extraction fails
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Get detailed stream information
        stream_info = self._get_stream_info(video_path)
        format_info = self._get_format_info(video_path)

        # Extract video stream (first video stream found)
        video_stream = None
        for stream in stream_info.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if not video_stream:
            raise ValueError(f"No video stream found in {video_path}")

        # Extract metadata fields
        duration_s = self._extract_duration(video_stream, format_info)
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        fps = self._extract_fps(video_stream)
        frame_count = self._extract_frame_count(video_stream, duration_s, fps)
        codec = video_stream.get("codec_name", "unknown")
        pixel_format = video_stream.get("pix_fmt", "unknown")
        bitrate_kbps = self._extract_bitrate(video_stream, format_info)
        container_format = format_info.get("format_name", "mp4").split(",")[0]

        return VideoMetadata(
            duration_s=duration_s,
            width=width,
            height=height,
            fps=fps,
            frame_count=frame_count,
            codec=codec,
            pixel_format=pixel_format,
            bitrate_kbps=bitrate_kbps,
            container_format=container_format,
        )

    def _get_stream_info(self, video_path: Path) -> Dict[str, Any]:
        """Get stream information from ffprobe."""
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            str(video_path),
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout_s, check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise ValueError(f"ffprobe stream analysis failed: {e.stderr}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse ffprobe stream output: {e}")

    def _get_format_info(self, video_path: Path) -> Dict[str, Any]:
        """Get format information from ffprobe."""
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            str(video_path),
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout_s, check=True
            )
            format_data = json.loads(result.stdout)
            return format_data.get("format", {})
        except subprocess.CalledProcessError as e:
            raise ValueError(f"ffprobe format analysis failed: {e.stderr}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse ffprobe format output: {e}")

    def _extract_duration(
        self, video_stream: Dict[str, Any], format_info: Dict[str, Any]
    ) -> float:
        """Extract video duration from stream or format info."""
        # Try stream duration first
        if "duration" in video_stream:
            try:
                return float(video_stream["duration"])
            except (ValueError, TypeError):
                pass

        # Fallback to format duration
        if "duration" in format_info:
            try:
                return float(format_info["duration"])
            except (ValueError, TypeError):
                pass

        # Last resort: calculate from frame count and fps
        if "nb_frames" in video_stream and "avg_frame_rate" in video_stream:
            try:
                frame_count = int(video_stream["nb_frames"])
                fps = self._parse_frame_rate(video_stream["avg_frame_rate"])
                if fps > 0:
                    return frame_count / fps
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        raise ValueError("Could not determine video duration")

    def _extract_fps(self, video_stream: Dict[str, Any]) -> float:
        """Extract frame rate from video stream."""
        # Try different FPS fields in order of preference
        fps_fields = ["r_frame_rate", "avg_frame_rate", "time_base"]

        for field in fps_fields:
            if field in video_stream:
                try:
                    fps = self._parse_frame_rate(video_stream[field])
                    if fps > 0:
                        return fps
                except (ValueError, TypeError, ZeroDivisionError):
                    continue

        # Default fallback
        return 30.0

    def _parse_frame_rate(self, rate_str: str) -> float:
        """Parse frame rate string (e.g., '30/1', '2997/100')."""
        if "/" in rate_str:
            numerator, denominator = rate_str.split("/", 1)
            return float(numerator) / float(denominator)
        else:
            return float(rate_str)

    def _extract_frame_count(
        self, video_stream: Dict[str, Any], duration_s: float, fps: float
    ) -> int:
        """Extract or calculate frame count."""
        # Try direct frame count first
        if "nb_frames" in video_stream:
            try:
                return int(video_stream["nb_frames"])
            except (ValueError, TypeError):
                pass

        # Calculate from duration and fps
        if duration_s > 0 and fps > 0:
            return int(duration_s * fps)

        return 0

    def _extract_bitrate(
        self, video_stream: Dict[str, Any], format_info: Dict[str, Any]
    ) -> Optional[int]:
        """Extract bitrate in kbps."""
        # Try stream bitrate first
        if "bit_rate" in video_stream:
            try:
                return int(float(video_stream["bit_rate"]) / 1000)  # Convert to kbps
            except (ValueError, TypeError):
                pass

        # Try format bitrate
        if "bit_rate" in format_info:
            try:
                return int(float(format_info["bit_rate"]) / 1000)  # Convert to kbps
            except (ValueError, TypeError):
                pass

        return None

    def get_basic_info(self, video_path: Path) -> Dict[str, Any]:
        """
        Get basic video info as a dictionary (simpler interface).

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with basic video information
        """
        try:
            metadata = self.probe_video(video_path)
            return {
                "duration_s": metadata.duration_s,
                "width": metadata.width,
                "height": metadata.height,
                "fps": metadata.fps,
                "frame_count": metadata.frame_count,
                "codec": metadata.codec,
                "pixel_format": metadata.pixel_format,
                "bitrate_kbps": metadata.bitrate_kbps,
                "resolution": metadata.resolution,
                "aspect_ratio": metadata.aspect_ratio,
                "container_format": metadata.container_format,
            }
        except Exception as e:
            raise ValueError(f"Failed to probe video {video_path}: {str(e)}")

    def verify_video_specs(
        self, video_path: Path, expected_specs: Dict[str, Any]
    ) -> List[str]:
        """
        Verify video meets expected specifications.

        Args:
            video_path: Path to video file
            expected_specs: Dictionary with expected values

        Returns:
            List of issues found (empty if all specs match)
        """
        issues = []

        try:
            metadata = self.probe_video(video_path)

            # Check resolution
            if "width" in expected_specs and metadata.width != expected_specs["width"]:
                issues.append(
                    f"Width mismatch: expected {expected_specs['width']}, got {metadata.width}"
                )

            if (
                "height" in expected_specs
                and metadata.height != expected_specs["height"]
            ):
                issues.append(
                    f"Height mismatch: expected {expected_specs['height']}, got {metadata.height}"
                )

            # Check FPS (with tolerance)
            if "fps" in expected_specs:
                expected_fps = expected_specs["fps"]
                fps_tolerance = expected_specs.get("fps_tolerance", 0.1)
                if abs(metadata.fps - expected_fps) > fps_tolerance:
                    issues.append(
                        f"FPS mismatch: expected {expected_fps}, got {metadata.fps:.2f}"
                    )

            # Check codec
            if "codec" in expected_specs and metadata.codec != expected_specs["codec"]:
                issues.append(
                    f"Codec mismatch: expected {expected_specs['codec']}, got {metadata.codec}"
                )

            # Check pixel format
            if (
                "pixel_format" in expected_specs
                and metadata.pixel_format != expected_specs["pixel_format"]
            ):
                issues.append(
                    f"Pixel format mismatch: expected {expected_specs['pixel_format']}, got {metadata.pixel_format}"
                )

            # Check minimum duration
            if (
                "min_duration_s" in expected_specs
                and metadata.duration_s < expected_specs["min_duration_s"]
            ):
                issues.append(
                    f"Duration too short: expected >= {expected_specs['min_duration_s']}s, got {metadata.duration_s:.2f}s"
                )

            # Check maximum duration
            if (
                "max_duration_s" in expected_specs
                and metadata.duration_s > expected_specs["max_duration_s"]
            ):
                issues.append(
                    f"Duration too long: expected <= {expected_specs['max_duration_s']}s, got {metadata.duration_s:.2f}s"
                )

        except Exception as e:
            issues.append(f"Failed to verify video specs: {str(e)}")

        return issues


def probe_video_file(video_path: Path) -> VideoMetadata:
    """
    Convenience function to probe a video file.

    Args:
        video_path: Path to video file

    Returns:
        VideoMetadata with extracted information
    """
    probe = VideoProbe()
    return probe.probe_video(video_path)


def get_video_info(video_path: Path) -> Dict[str, Any]:
    """
    Convenience function to get basic video info as dict.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video information
    """
    probe = VideoProbe()
    return probe.get_basic_info(video_path)
