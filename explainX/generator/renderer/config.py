"""
T6: Renderer configuration and quality presets.
Defines production quality settings and resource limits.
"""

from typing import Dict, Any, List


# Define RenderQualityPreset locally to avoid circular import
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RenderQualityPreset:
    """Quality preset for video rendering."""

    width: int
    height: int
    fps: int
    crf: int  # Constant Rate Factor for H.264
    preset: str  # FFmpeg preset (ultrafast, fast, medium, slow, veryslow)
    bitrate: Optional[str] = None  # Target bitrate (e.g., "2M", "5M")


# T6.1: Production quality presets
QUALITY_PRESETS: Dict[str, RenderQualityPreset] = {
    "1080p": RenderQualityPreset(
        width=1920,
        height=1080,
        fps=30,
        crf=18,  # High quality
        preset="medium",
        bitrate="5M",  # Target 5 Mbps
    ),
    "720p": RenderQualityPreset(
        width=1280,
        height=720,
        fps=30,
        crf=20,  # Good quality
        preset="medium",
        bitrate="3M",  # Target 3 Mbps
    ),
    "480p": RenderQualityPreset(
        width=854,
        height=480,
        fps=30,
        crf=23,  # Standard quality
        preset="fast",
        bitrate="1M",  # Target 1 Mbps
    ),
}

# T6.1: Resource limits for production rendering
RENDER_LIMITS = {
    "timeout_s": 180,  # 3 minutes per scene
    "memory_mb": 2048,  # 2GB memory cap
    "cpu_cores": 1,  # Single core to avoid resource contention
    "temp_disk_mb": 1024,  # 1GB temp disk usage
    "max_output_mb": 500,  # 500MB max per scene output
}

# T6.2: Transition settings
TRANSITION_SETTINGS = {
    "crossfade": {
        "default_duration_s": 0.5,
        "min_duration_s": 0.1,
        "max_duration_s": 2.0,
    },
    "straight_cut": {
        "blend_frames": 0,  # No blending for straight cuts
    },
}

# T6.3: Thumbnail settings
THUMBNAIL_SETTINGS = {
    "poster_frame_time_s": 1.0,  # Extract frame at 1s mark
    "thumbnail_sizes": [
        (320, 180),  # Small thumbnail
        (640, 360),  # Medium thumbnail
        (1280, 720),  # Large thumbnail/poster
    ],
    "format": "jpg",
    "quality": 85,
}

# T6.4: Caching configuration
CACHE_SETTINGS = {
    "enabled": True,
    "max_size_gb": 10.0,  # 10GB cache limit
    "ttl_hours": 24 * 7,  # 1 week TTL
    "hash_algorithm": "sha256",
    "cache_key_version": "1.0",  # Increment to invalidate cache
}

# T6: General render settings
RENDER_SETTINGS = {
    "manim_command_base": ["manim"],
    "manim_quality_flag": {
        "1080p": "-q h",  # High quality
        "720p": "-q m",  # Medium quality
        "480p": "-q l",  # Low quality
    },
    "disable_preview": True,  # No preview window in production
    "disable_caching": True,  # Disable Manim's internal cache
    "log_level": "ERROR",  # Minimal Manim logging
    "temp_prefix": "manim_prod_",  # Temp directory prefix
}

# T6: FFmpeg settings for concatenation
FFMPEG_SETTINGS = {
    "concat_method": "filter_complex",  # Use filter_complex for crossfades
    "output_codec": "libx264",
    "output_format": "mp4",
    "movflags": "+faststart",  # Web-optimized MP4
    "pix_fmt": "yuv420p",  # Broad compatibility
    "threads": 2,  # 2 threads for encoding
}

# T6: Validation settings
VALIDATION_SETTINGS = {
    "min_scene_duration_s": 0.1,
    "max_scene_duration_s": 300,  # 5 minutes per scene
    "max_total_duration_s": 1800,  # 30 minutes total video
    "required_fps": [15, 24, 30, 60],
    "max_resolution": (3840, 2160),  # 4K max
}


def get_quality_preset(quality: str) -> RenderQualityPreset:
    """Get quality preset by name."""
    if quality not in QUALITY_PRESETS:
        raise ValueError(
            f"Unknown quality preset: {quality}. Available: {list(QUALITY_PRESETS.keys())}"
        )
    return QUALITY_PRESETS[quality]


def get_manim_command(
    quality: str,
    main_py_path: str,
    class_name: str,
    output_dir: str,
    media_dir: str,
    custom_resolution: str = None,
) -> List[str]:
    """
    Build Manim command for production rendering.

    Args:
        quality: Quality preset name ("1080p", "720p", etc.)
        main_py_path: Path to the Python file with scene class
        class_name: Name of the scene class to render
        output_dir: Directory for output files
        media_dir: Directory for media assets
        custom_resolution: Optional custom resolution string (e.g., "1920,1080")

    Returns:
        Complete Manim command as list of strings
    """
    preset = get_quality_preset(quality)

    # Base command
    cmd = RENDER_SETTINGS["manim_command_base"].copy()

    # Quality flag
    quality_flag = RENDER_SETTINGS["manim_quality_flag"].get(quality, "-q m")
    cmd.extend(quality_flag.split())

    # Resolution
    resolution = custom_resolution or f"{preset.width},{preset.height}"
    cmd.extend(["-r", resolution])

    # No preview in production
    if RENDER_SETTINGS["disable_preview"]:
        # Note: -p is for preview, we want to avoid it in production
        pass

    # Disable caching for deterministic builds
    if RENDER_SETTINGS["disable_caching"]:
        cmd.append("--disable_caching")

    # Directories
    cmd.extend(
        [
            "--media_dir",
            media_dir,
            "--output_dir",
            output_dir,
        ]
    )

    # Source file and class
    cmd.extend([main_py_path, class_name])

    return cmd


def get_ffmpeg_concat_command(
    input_videos: List[str],
    output_video: str,
    crossfade_duration_s: float = None,
    quality_preset: RenderQualityPreset = None,
) -> List[str]:
    """
    Build FFmpeg command for video concatenation with optional crossfades.

    Args:
        input_videos: List of input video file paths
        output_video: Output video file path
        crossfade_duration_s: Crossfade duration (None for straight cuts)
        quality_preset: Quality settings for output

    Returns:
        Complete FFmpeg command as list of strings
    """
    cmd = ["ffmpeg"]

    # Input files
    for video in input_videos:
        cmd.extend(["-i", video])

    if crossfade_duration_s and len(input_videos) > 1:
        # Use filter_complex for crossfades
        cmd.append("-filter_complex")

        # Build crossfade filter chain
        filter_parts = []
        current_stream = "[0:v]"

        for i in range(1, len(input_videos)):
            fade_filter = f"[{current_stream}][{i}:v]xfade=transition=fade:duration={crossfade_duration_s}:offset=0"
            output_stream = f"[v{i}]" if i < len(input_videos) - 1 else "[outv]"
            filter_parts.append(f"{fade_filter}{output_stream}")
            current_stream = f"[v{i}]"

        cmd.append(";".join(filter_parts))
        cmd.extend(["-map", "[outv]"])

    else:
        # Straight concatenation using concat demuxer would be better,
        # but for now use simple approach
        if len(input_videos) == 1:
            # Single input, just copy
            cmd.extend(["-c", "copy"])
        else:
            # Multiple inputs, re-encode (simplified approach)
            pass

    # Output codec and quality settings
    if quality_preset:
        cmd.extend(
            [
                "-c:v",
                FFMPEG_SETTINGS["output_codec"],
                "-crf",
                str(quality_preset.crf),
                "-preset",
                quality_preset.preset,
            ]
        )
        if quality_preset.bitrate:
            cmd.extend(["-b:v", quality_preset.bitrate])

    # Output format settings
    cmd.extend(
        [
            "-pix_fmt",
            FFMPEG_SETTINGS["pix_fmt"],
            "-movflags",
            FFMPEG_SETTINGS["movflags"],
            "-f",
            FFMPEG_SETTINGS["output_format"],
            "-threads",
            str(FFMPEG_SETTINGS["threads"]),
        ]
    )

    # Overwrite output
    cmd.extend(["-y", output_video])

    return cmd


def validate_render_input(render_input) -> None:
    """Validate render input against configuration limits."""
    # Check if it has the required attributes (duck typing)
    required_attrs = ["video_id", "scenes", "quality", "fps", "crossfade_s"]
    for attr in required_attrs:
        if not hasattr(render_input, attr):
            raise TypeError(f"render_input missing required attribute: {attr}")

    # Check scene count
    if len(render_input.scenes) == 0:
        raise ValueError("At least one scene is required")

    # Check quality preset exists
    if render_input.quality not in QUALITY_PRESETS:
        raise ValueError(f"Unknown quality: {render_input.quality}")

    # Check FPS
    if render_input.fps not in VALIDATION_SETTINGS["required_fps"]:
        raise ValueError(f"Unsupported fps: {render_input.fps}")

    # Estimate total duration
    total_est_duration = sum(scene.est_duration_s for scene in render_input.scenes)
    if total_est_duration > VALIDATION_SETTINGS["max_total_duration_s"]:
        raise ValueError(
            f"Estimated total duration {total_est_duration}s exceeds maximum {VALIDATION_SETTINGS['max_total_duration_s']}s"
        )

    # Check individual scene durations
    for scene in render_input.scenes:
        if scene.est_duration_s < VALIDATION_SETTINGS["min_scene_duration_s"]:
            raise ValueError(
                f"Scene {scene.scene_id} duration {scene.est_duration_s}s too short"
            )
        if scene.est_duration_s > VALIDATION_SETTINGS["max_scene_duration_s"]:
            raise ValueError(
                f"Scene {scene.scene_id} duration {scene.est_duration_s}s too long"
            )

    # Check crossfade settings
    if render_input.crossfade_s is not None:
        min_crossfade = TRANSITION_SETTINGS["crossfade"]["min_duration_s"]
        max_crossfade = TRANSITION_SETTINGS["crossfade"]["max_duration_s"]
        if not (min_crossfade <= render_input.crossfade_s <= max_crossfade):
            raise ValueError(
                f"Crossfade duration {render_input.crossfade_s}s must be between {min_crossfade}s and {max_crossfade}s"
            )
