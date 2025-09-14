"""
Enhanced preview naming, existence checks, and cleanup for T5.5.
Manages Manim output detection, size limits, and re-encoding.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import subprocess
import json
import shutil

# T5.5 Constants
MAX_PREVIEW_MB = 10  # Max preview MP4: 10 MB
MANIM_OUTPUT_PATTERNS = [
    # T5.5: Manim default output patterns
    "media/videos/{filename}/{quality}/{class_name}.mp4",
    "media/videos/main/{quality}/{class_name}.mp4",  # Common pattern
    "{quality}/{class_name}.mp4",  # Simple pattern
    "videos/{quality}/{class_name}.mp4",  # Alternative structure
]
MANIM_QUALITY_DIRS = [
    "480p15",
    "720p30",
    "1080p60",
    "low_quality",
    "medium_quality",
    "high_quality",
]


@dataclass(frozen=True)
class PreviewArtifacts:
    """Container for generated preview artifacts."""

    preview_mp4: Optional[Path] = None
    first_frame_png: Optional[Path] = None

    def exists(self) -> bool:
        """Check if all artifacts exist."""
        return (self.preview_mp4 is None or self.preview_mp4.exists()) and (
            self.first_frame_png is None or self.first_frame_png.exists()
        )

    def cleanup(self) -> None:
        """Clean up generated artifacts."""
        if self.preview_mp4 and self.preview_mp4.exists():
            try:
                self.preview_mp4.unlink()
            except Exception:
                pass

        if self.first_frame_png and self.first_frame_png.exists():
            try:
                self.first_frame_png.unlink()
            except Exception:
                pass


class ArtifactManager:
    """Enhanced T5.5 artifacts manager with size limits and re-encoding."""

    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.artifacts_dir = work_dir / "artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)
        self.temp_dir = work_dir / "temp_artifacts"
        self.temp_dir.mkdir(exist_ok=True)

    def get_artifact_paths(self, scene_id: str, class_name: str) -> PreviewArtifacts:
        """T5.5: Get expected artifact paths with standardized naming."""
        # T5.5: Use scene_id for consistent naming: scene_<id>_preview.mp4, scene_<id>_frame0.png
        safe_scene_id = self._sanitize_filename(scene_id)

        # T5.5 naming convention
        preview_mp4 = self.artifacts_dir / f"scene_{safe_scene_id}_preview.mp4"
        first_frame_png = self.artifacts_dir / f"scene_{safe_scene_id}_frame0.png"

        return PreviewArtifacts(
            preview_mp4=preview_mp4, first_frame_png=first_frame_png
        )

    def detect_manim_output(
        self, class_name: str, source_filename: str = "main"
    ) -> Optional[Path]:
        """
        T5.5: Detect Manim output files using known patterns.
        Searches for patterns like: artifacts/media/videos/main/480p15/Scene_sec_01.mp4
        """
        search_dirs = [self.work_dir, self.artifacts_dir, self.work_dir / "media"]

        for base_dir in search_dirs:
            if not base_dir.exists():
                continue

            # Try each known pattern
            for pattern in MANIM_OUTPUT_PATTERNS:
                for quality in MANIM_QUALITY_DIRS:
                    # Format the pattern
                    try:
                        relative_path = pattern.format(
                            filename=source_filename,
                            quality=quality,
                            class_name=class_name,
                        )
                        video_path = base_dir / relative_path

                        if video_path.exists():
                            return video_path

                    except KeyError:
                        # Pattern doesn't match, skip
                        continue

        # Fallback: recursive search for any MP4 files
        for base_dir in search_dirs:
            if not base_dir.exists():
                continue

            mp4_files = list(base_dir.rglob("*.mp4"))
            if mp4_files:
                # Return most recent file that might match our class
                candidates = [f for f in mp4_files if class_name in f.name]
                if candidates:
                    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    return candidates[0]

                # Or just the most recent MP4
                mp4_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                return mp4_files[0]

        return None

    def process_manim_output(
        self, class_name: str, scene_id: str, source_filename: str = "main"
    ) -> Optional[PreviewArtifacts]:
        """
        T5.5: Process Manim output with size limits and re-encoding.

        Steps:
        1. Detect Manim output file
        2. Check size limits (10MB max)
        3. Re-encode if oversized using ffmpeg
        4. Copy/symlink to standard names
        5. Extract first frame
        """
        # Step 1: Detect Manim output
        source_video = self.detect_manim_output(class_name, source_filename)
        if not source_video:
            return None

        # Get target artifact paths
        artifacts = self.get_artifact_paths(scene_id, class_name)

        try:
            # Step 2 & 3: Check size and re-encode if needed
            processed_video = self._ensure_size_limit(
                source_video, artifacts.preview_mp4
            )

            # Step 4: Already handled by _ensure_size_limit (copies to target)

            # Step 5: Extract first frame
            if artifacts.first_frame_png:
                frame_success = self.extract_first_frame(
                    processed_video, artifacts.first_frame_png
                )
                if not frame_success:
                    # Return artifacts even if frame extraction failed
                    return PreviewArtifacts(
                        preview_mp4=processed_video, first_frame_png=None
                    )

            return artifacts

        except Exception as e:
            # Clean up on failure
            if artifacts.preview_mp4 and artifacts.preview_mp4.exists():
                artifacts.preview_mp4.unlink()
            if artifacts.first_frame_png and artifacts.first_frame_png.exists():
                artifacts.first_frame_png.unlink()
            return None

    def _ensure_size_limit(self, source_video: Path, target_video: Path) -> Path:
        """T5.5: Ensure video is under size limit, re-encode if necessary."""
        # Check source size
        source_size_mb = source_video.stat().st_size / (1024 * 1024)

        if source_size_mb <= MAX_PREVIEW_MB:
            # Under limit, just copy/symlink
            shutil.copy2(source_video, target_video)
            return target_video

        # Over limit, re-encode to reduce size
        return self._reencode_video(source_video, target_video)

    def _reencode_video(self, source_video: Path, target_video: Path) -> Path:
        """T5.5: Re-encode video with lower bitrate to meet size limits."""
        try:
            # Use ffmpeg to re-encode with lower bitrate
            # Target bitrate calculation: aim for ~8MB to leave margin
            target_bitrate = "500k"  # Conservative bitrate

            command = [
                "ffmpeg",
                "-i",
                str(source_video),
                "-c:v",
                "libx264",  # H.264 codec
                "-b:v",
                target_bitrate,  # Video bitrate
                "-c:a",
                "aac",  # Audio codec
                "-b:a",
                "64k",  # Low audio bitrate
                "-movflags",
                "+faststart",  # Web optimization
                "-preset",
                "medium",  # Encoding speed vs quality
                "-crf",
                "28",  # Quality (higher = smaller file)
                "-maxrate",
                "600k",  # Max bitrate spikes
                "-bufsize",
                "1200k",  # Buffer size
                "-y",  # Overwrite output
                str(target_video),
            ]

            result = subprocess.run(
                command, capture_output=True, text=True, timeout=60  # 1 minute timeout
            )

            if result.returncode == 0 and target_video.exists():
                # Verify the re-encoded file is actually smaller
                new_size_mb = target_video.stat().st_size / (1024 * 1024)
                if new_size_mb <= MAX_PREVIEW_MB:
                    return target_video
                else:
                    # Still too big, try more aggressive settings
                    return self._reencode_aggressive(source_video, target_video)
            else:
                # Re-encoding failed, fallback to copy
                shutil.copy2(source_video, target_video)
                return target_video

        except Exception:
            # Fallback to copy on any error
            shutil.copy2(source_video, target_video)
            return target_video

    def _reencode_aggressive(self, source_video: Path, target_video: Path) -> Path:
        """More aggressive re-encoding for very large files."""
        try:
            command = [
                "ffmpeg",
                "-i",
                str(source_video),
                "-c:v",
                "libx264",
                "-b:v",
                "300k",  # Very low bitrate
                "-c:a",
                "aac",
                "-b:a",
                "32k",  # Very low audio
                "-s",
                "640x480",  # Reduce resolution
                "-r",
                "15",  # Reduce frame rate
                "-crf",
                "32",  # Higher compression
                "-preset",
                "slow",  # Better compression
                "-y",
                str(target_video),
            ]

            result = subprocess.run(
                command, capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0 and target_video.exists():
                return target_video
            else:
                # Last resort: just copy
                shutil.copy2(source_video, target_video)
                return target_video

        except Exception:
            shutil.copy2(source_video, target_video)
            return target_video

    def extract_first_frame(self, video_path: Path, output_path: Path) -> bool:
        """T5.5: Extract first frame using ffmpeg -frames:v 1 or -s option."""
        if not video_path.exists():
            return False

        try:
            # T5.5: Use ffmpeg with -frames:v 1 as specified
            command = [
                "ffmpeg",
                "-i",
                str(video_path),
                "-frames:v",
                "1",  # T5.5: Extract exactly 1 frame
                "-f",
                "image2",
                "-q:v",
                "2",  # High quality PNG
                "-y",  # Overwrite output
                str(output_path),
            ]

            result = subprocess.run(
                command, capture_output=True, text=True, timeout=15  # Increased timeout
            )

            return result.returncode == 0 and output_path.exists()

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

    def verify_video_quality(self, video_path: Path) -> dict:
        """Verify video quality and extract metadata."""
        if not video_path.exists():
            return {"valid": False, "error": "File does not exist"}

        try:
            import subprocess

            # Use ffprobe to get video info
            command = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(video_path),
            ]

            result = subprocess.run(command, capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                return {"valid": False, "error": "ffprobe failed"}

            import json

            probe_data = json.loads(result.stdout)

            # Extract basic info
            format_info = probe_data.get("format", {})
            video_streams = [
                s
                for s in probe_data.get("streams", [])
                if s.get("codec_type") == "video"
            ]

            if not video_streams:
                return {"valid": False, "error": "No video streams found"}

            video_stream = video_streams[0]

            return {
                "valid": True,
                "duration": float(format_info.get("duration", 0)),
                "size_bytes": int(format_info.get("size", 0)),
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "fps": video_stream.get("r_frame_rate", "unknown"),
                "codec": video_stream.get("codec_name", "unknown"),
            }

        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            json.JSONDecodeError,
            Exception,
        ) as e:
            return {"valid": False, "error": str(e)}

    def cleanup_artifacts(self, artifacts: PreviewArtifacts) -> None:
        """Clean up generated artifacts."""
        artifacts.cleanup()

    def cleanup_work_dir(self) -> None:
        """Clean up entire work directory."""
        try:
            import shutil

            if self.work_dir.exists():
                shutil.rmtree(self.work_dir)
        except Exception:
            # Best-effort cleanup
            pass

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem safety."""
        # Replace problematic characters
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in "-_":
                safe_chars.append(char)
            else:
                safe_chars.append("_")

        sanitized = "".join(safe_chars)

        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:50]

        # Ensure not empty
        if not sanitized:
            sanitized = "scene"

        return sanitized


def get_manim_output_files(
    work_dir: Path, class_name: str
) -> tuple[Optional[Path], Optional[Path]]:
    """
    Enhanced T5.5: Find Manim output files using improved detection patterns.
    Returns (video_path, media_dir).
    """
    # Create temporary artifact manager for detection
    temp_manager = ArtifactManager(work_dir)

    # Use enhanced detection
    detected_video = temp_manager.detect_manim_output(class_name)

    if detected_video:
        # Return video and its parent directory as media_dir
        media_dir = detected_video.parent
        return detected_video, media_dir

    # Fallback to original logic for backwards compatibility
    media_dir = work_dir / "media"
    if not media_dir.exists():
        return None, None

    # Look for video files
    video_patterns = [f"{class_name}.mp4", f"{class_name}.mov", "*.mp4", "*.mov"]

    for pattern in video_patterns:
        if "*" in pattern:
            matches = list(media_dir.rglob(pattern))
            if matches:
                return matches[0], media_dir
        else:
            video_path = media_dir / pattern
            if video_path.exists():
                return video_path, media_dir

    # Search recursively
    video_files = []
    for ext in [".mp4", ".mov"]:
        video_files.extend(media_dir.rglob(f"*{ext}"))

    if video_files:
        # Return most recent
        video_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return video_files[0], media_dir

    return None, media_dir
