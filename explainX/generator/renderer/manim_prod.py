"""
T6.1: Production Manim renderer with quality presets and resource limits.

Executes Manim in sandboxed subprocess for final production quality renders.
Builds on T5 isolation model with production-specific configurations.
"""

import os
import time
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass

from generator.validator.sandbox import SandboxEnvironment, SandboxLimits
from .config import (
    get_quality_preset,
    get_manim_command,
    RENDER_LIMITS,
    RENDER_SETTINGS,
)
from . import SceneRenderItem
from .config import RenderQualityPreset


@dataclass(frozen=True)
class ProductionRenderResult:
    """Result of a single scene production render."""

    success: bool
    output_mp4: Optional[Path] = None
    duration_s: float = 0.0
    file_size_mb: float = 0.0
    resolution: Tuple[int, int] = (0, 0)
    fps: float = 0.0
    frame_count: int = 0
    render_time_s: float = 0.0
    peak_memory_mb: float = 0.0
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    error_message: str = ""


class ProductionManimRenderer:
    """T6.1: Production-quality Manim renderer with resource limits."""

    def __init__(
        self,
        quality: str = "1080p",
        timeout_s: int = None,
        memory_mb: int = None,
        work_dir: Path = None,
    ):
        """
        Initialize production renderer.

        Args:
            quality: Quality preset name ("1080p", "720p", etc.)
            timeout_s: Rendering timeout in seconds
            memory_mb: Memory limit in MB
            work_dir: Working directory (temp dir if None)
        """
        self.quality = quality
        self.quality_preset = get_quality_preset(quality)
        self.timeout_s = timeout_s or RENDER_LIMITS["timeout_s"]
        self.memory_mb = memory_mb or RENDER_LIMITS["memory_mb"]
        self.work_dir = work_dir or Path(
            tempfile.mkdtemp(prefix=RENDER_SETTINGS["temp_prefix"])
        )
        self._cleanup_work_dir = work_dir is None  # Only cleanup if we created it

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        if self._cleanup_work_dir and self.work_dir.exists():
            try:
                shutil.rmtree(self.work_dir)
            except Exception:
                # Best effort cleanup
                pass

    def render_scene(
        self, scene_item: SceneRenderItem, output_dir: Path = None
    ) -> ProductionRenderResult:
        """
        Render a single scene in production quality.

        Args:
            scene_item: Scene to render
            output_dir: Output directory for rendered MP4

        Returns:
            ProductionRenderResult with render details and output path
        """
        if output_dir is None:
            output_dir = self.work_dir / "output"

        output_dir.mkdir(parents=True, exist_ok=True)

        # Set up sandbox environment
        sandbox_limits = SandboxLimits(
            timeout_seconds=self.timeout_s,
            max_memory_mb=self.memory_mb,
            max_files=100,
        )

        render_start = time.time()

        try:
            with SandboxEnvironment(limits=sandbox_limits) as sandbox:
                return self._execute_manim_render(
                    sandbox, scene_item, output_dir, render_start
                )

        except Exception as e:
            return ProductionRenderResult(
                success=False,
                error_message=f"Sandbox setup failed: {str(e)}",
                render_time_s=time.time() - render_start,
            )

    def _execute_manim_render(
        self,
        sandbox: SandboxEnvironment,
        scene_item: SceneRenderItem,
        output_dir: Path,
        render_start: float,
    ) -> ProductionRenderResult:
        """Execute the Manim render in sandbox."""
        try:
            # Copy source file to sandbox
            sandbox_main_py = sandbox.write_file(
                "main.py", scene_item.main_py.read_text()
            )

            # Prepare output directories in sandbox
            sandbox_output_dir = sandbox.temp_dir / "output"
            sandbox_media_dir = sandbox.temp_dir / "media"
            sandbox_output_dir.mkdir(exist_ok=True)
            sandbox_media_dir.mkdir(exist_ok=True)

            # Build Manim command
            manim_cmd = get_manim_command(
                quality=self.quality,
                main_py_path=str(sandbox_main_py),
                class_name=scene_item.class_name,
                output_dir=str(sandbox_output_dir),
                media_dir=str(sandbox_media_dir),
            )

            # Set production environment
            env = self._get_production_environment(sandbox)

            # Execute Manim
            exit_code, stdout, stderr = sandbox.execute_command(manim_cmd, env=env)
            render_time = time.time() - render_start

            # Find output video
            output_mp4 = self._find_output_video(
                sandbox_media_dir, scene_item.class_name
            )

            if exit_code == 0 and output_mp4:
                # Copy output to final destination
                final_output = output_dir / f"scene_{scene_item.scene_id}_prod.mp4"
                shutil.copy2(output_mp4, final_output)

                # Get video metadata
                metadata = self._get_video_metadata(final_output)

                return ProductionRenderResult(
                    success=True,
                    output_mp4=final_output,
                    duration_s=metadata.get("duration_s", 0.0),
                    file_size_mb=final_output.stat().st_size / (1024 * 1024),
                    resolution=metadata.get("resolution", (0, 0)),
                    fps=metadata.get("fps", 0.0),
                    frame_count=metadata.get("frame_count", 0),
                    render_time_s=render_time,
                    peak_memory_mb=metadata.get("peak_memory_mb", 0.0),
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                )
            else:
                # Render failed
                error_msg = self._parse_error_message(stderr, stdout, exit_code)
                return ProductionRenderResult(
                    success=False,
                    render_time_s=render_time,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    error_message=error_msg,
                )

        except Exception as e:
            return ProductionRenderResult(
                success=False,
                error_message=f"Render execution failed: {str(e)}",
                render_time_s=time.time() - render_start,
            )

    def _get_production_environment(
        self, sandbox: SandboxEnvironment
    ) -> Dict[str, str]:
        """Get environment variables for production rendering."""
        env = os.environ.copy()

        # Set Manim environment
        env["MANIMGL_LOG_LEVEL"] = RENDER_SETTINGS["log_level"]
        env["MANIM_LOG_LEVEL"] = RENDER_SETTINGS["log_level"]

        # Set temporary directories
        env["TMPDIR"] = str(sandbox.temp_dir)
        env["MPLCONFIGDIR"] = str(sandbox.temp_dir / "mpl_config")
        Path(env["MPLCONFIGDIR"]).mkdir(exist_ok=True)

        # Production-specific settings
        env["MANIM_DISABLE_CACHING"] = "1"  # Ensure no caching
        env["MANIM_QUALITY"] = self.quality

        # Optional: Disable Cairo Pango if needed
        # env["MANIM_DISABLE_CAIRO_PANGO"] = "1"

        return env

    def _find_output_video(self, media_dir: Path, class_name: str) -> Optional[Path]:
        """Find the output MP4 file in Manim's output structure."""
        # Manim typically outputs to: media_dir/videos/main/{quality}/{class_name}.mp4
        quality_dirs = {
            "1080p": ["1080p60", "1080p30", "high_quality"],
            "720p": ["720p60", "720p30", "medium_quality"],
            "480p": ["480p30", "low_quality"],
        }

        search_dirs = quality_dirs.get(
            self.quality, ["high_quality", "medium_quality", "low_quality"]
        )

        # Search in likely locations
        for base_path in [media_dir / "videos" / "main", media_dir / "videos"]:
            if not base_path.exists():
                continue

            for quality_dir in search_dirs:
                video_path = base_path / quality_dir / f"{class_name}.mp4"
                if video_path.exists():
                    return video_path

        # Fallback: search for any MP4 with matching class name
        for mp4_file in media_dir.rglob("*.mp4"):
            if class_name in mp4_file.stem:
                return mp4_file

        return None

    def _get_video_metadata(self, video_path: Path) -> Dict[str, Any]:
        """Extract metadata from video file using ffprobe."""
        try:
            # Use ffprobe to get video information
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
                    return {
                        "duration_s": float(
                            probe_data.get("format", {}).get("duration", 0)
                        ),
                        "resolution": (
                            int(video_stream.get("width", 0)),
                            int(video_stream.get("height", 0)),
                        ),
                        "fps": self._parse_fps(
                            video_stream.get("r_frame_rate", "30/1")
                        ),
                        "frame_count": int(video_stream.get("nb_frames", 0)),
                    }

        except Exception:
            # Fallback to basic file info
            pass

        # Return minimal metadata
        return {
            "duration_s": 0.0,
            "resolution": (self.quality_preset.width, self.quality_preset.height),
            "fps": float(self.quality_preset.fps),
            "frame_count": 0,
        }

    def _parse_fps(self, fps_string: str) -> float:
        """Parse FPS from ffprobe format (e.g., '30/1')."""
        try:
            if "/" in fps_string:
                num, den = fps_string.split("/")
                return float(num) / float(den)
            else:
                return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return float(self.quality_preset.fps)

    def _parse_error_message(self, stderr: str, stdout: str, exit_code: int) -> str:
        """Extract meaningful error message from render output."""
        error_patterns = [
            "LaTeX Error:",
            "FileNotFoundError:",
            "ModuleNotFoundError:",
            "ImportError:",
            "AttributeError:",
            "NameError:",
            "SyntaxError:",
            "IndentationError:",
            "TypeError:",
            "ValueError:",
            "RuntimeError:",
        ]

        # Look for specific errors in stderr
        for line in stderr.split("\n"):
            for pattern in error_patterns:
                if pattern in line:
                    return line.strip()

        # Look in stdout as fallback
        for line in stdout.split("\n"):
            for pattern in error_patterns:
                if pattern in line:
                    return line.strip()

        # Generic error based on exit code
        if exit_code == 1:
            return "Manim execution failed (exit code 1)"
        elif exit_code == 130:
            return "Manim execution interrupted (SIGINT)"
        elif exit_code < 0:
            return f"Manim process killed (signal {-exit_code})"
        else:
            return f"Unknown error (exit code {exit_code})"


def render_scene_production(
    scene_item: SceneRenderItem,
    quality: str = "1080p",
    output_dir: Path = None,
    timeout_s: int = None,
) -> ProductionRenderResult:
    """
    Convenient function to render a single scene in production quality.

    Args:
        scene_item: Scene to render
        quality: Quality preset ("1080p", "720p", etc.)
        output_dir: Output directory
        timeout_s: Render timeout

    Returns:
        ProductionRenderResult
    """
    with ProductionManimRenderer(quality=quality, timeout_s=timeout_s) as renderer:
        return renderer.render_scene(scene_item, output_dir)


def batch_render_scenes(
    scenes: List[SceneRenderItem],
    quality: str = "1080p",
    output_dir: Path = None,
    timeout_per_scene_s: int = None,
) -> List[ProductionRenderResult]:
    """
    Render multiple scenes in batch.

    Args:
        scenes: List of scenes to render
        quality: Quality preset
        output_dir: Output directory
        timeout_per_scene_s: Timeout per scene

    Returns:
        List of ProductionRenderResult, one per scene
    """
    results = []

    with ProductionManimRenderer(
        quality=quality, timeout_s=timeout_per_scene_s
    ) as renderer:
        for scene in scenes:
            result = renderer.render_scene(scene, output_dir)
            results.append(result)

            # Early exit on critical failure
            if not result.success and result.exit_code < 0:
                # Process was killed, might be system issue
                break

    return results
