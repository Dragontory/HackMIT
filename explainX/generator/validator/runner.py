"""
Sandboxed Manim execution to generate preview artifacts.
"""

import time
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

from .artifacts import ArtifactManager, PreviewArtifacts, get_manim_output_files
from .reporter import ErrorReporter
from .sandbox import SandboxEnvironment, SandboxLimits, ProcessMonitor
from .manim_config import get_manim_config


def run_manim_preview(
    source_text: str,
    class_name: str,
    work_dir: Path,
    q_level: Literal["low", "preview"] = "preview",
    video_id: str = "default",
    scene_id: str = "scene",
) -> Tuple[Optional[PreviewArtifacts], Dict, List[Dict]]:
    """
    Run Manim in sandbox to generate preview artifacts.

    Returns:
        - PreviewArtifacts or None if failed
        - logs dict with stdout, stderr, timings, resource_usage
        - issues list with structured problems
    """
    start_time = time.time()
    logs = {"stdout": "", "stderr": "", "timings": {}, "resource_usage": {}}
    issues = []

    # Set up sandbox limits based on quality level - matching T5.3 specs
    if q_level == "low":
        limits = SandboxLimits(
            timeout_seconds=25,  # Default 25s per scene preview
            max_memory_mb=1536,  # 1.5GB memory limit
            max_output_size=512 * 1024,
        )
        manim_quality = "l"  # Low quality
        resolution = "854,480"
    else:  # preview
        limits = SandboxLimits(
            timeout_seconds=25,  # Default 25s per scene preview
            max_memory_mb=1536,  # 1.5GB memory limit
            max_output_size=1024 * 1024,
        )
        manim_quality = "l"  # Use low quality for fast previews
        resolution = "854,480"

    artifact_manager = ArtifactManager(work_dir)
    reporter = ErrorReporter()

    try:
        # Create specific temp folder structure: /tmp/job_<video_id>/<scene_id>/
        import tempfile

        base_temp = Path(tempfile.gettempdir()) / f"job_{video_id}" / scene_id
        base_temp.mkdir(parents=True, exist_ok=True)

        # Override sandbox to use our specific temp structure
        with SandboxEnvironment(limits) as sandbox:
            # Replace sandbox temp dir with our structured one
            if sandbox.temp_dir and sandbox.temp_dir.exists():
                import shutil

                shutil.rmtree(sandbox.temp_dir)
            sandbox.temp_dir = base_temp

            logs["timings"]["sandbox_setup"] = time.time() - start_time

            # Create required subdirectories
            artifacts_dir = base_temp / "artifacts"
            artifacts_dir.mkdir(exist_ok=True)

            # Write main.py (not scene.py as per T5.3 spec)
            main_py = sandbox.write_file("main.py", source_text)
            logs["timings"]["file_write"] = time.time() - start_time

            # Write manim.cfg for consistent settings
            manim_cfg_content = get_manim_config(q_level)
            sandbox.write_file("manim.cfg", manim_cfg_content)

            # T5.6: Prepare exact Manim command with environment as specified
            # Default: manim -q l -r 854,480 main.py {class_name} --disable_caching --media_dir artifacts --output_dir artifacts
            manim_command = [
                "manim",
                "-q",
                manim_quality,  # -q l for low quality
                "-r",
                resolution,  # -r 480p wide for speed
                str(main_py),
                class_name,
                "--disable_caching",  # Disable Manim cache to avoid cross-test pollution
                "--media_dir",
                str(artifacts_dir),
                "--output_dir",
                str(artifacts_dir),
            ]

            # T5.6: Minimal environment with font cache handling
            import os

            env = os.environ.copy()

            # Set MPLCONFIGDIR to temp folder to avoid font cache races
            env["MPLCONFIGDIR"] = str(sandbox.temp_dir / "mpl_config")
            Path(env["MPLCONFIGDIR"]).mkdir(exist_ok=True)

            # Optionally disable Cairo Pango if needed
            # env["MANIM_DISABLE_CAIRO_PANGO"] = "1"

            # Execute Manim with environment
            execution_start = time.time()
            exit_code, stdout, stderr = sandbox.execute_command(manim_command, env=env)
            execution_time = time.time() - execution_start

            logs["stdout"] = stdout
            logs["stderr"] = stderr
            logs["timings"]["manim_execution"] = execution_time
            logs["timings"]["total"] = time.time() - start_time

            # T5.4 & T5.5: Enhanced execution parsing with metadata
            cmd_string = " ".join(manim_command)

            # Calculate resource metrics (basic)
            duration_ms = execution_time * 1000
            cpu_time_ms = (
                duration_ms  # Simplified - actual implementation would track CPU time
            )
            rss_peak_mb = 0  # Would be populated by ProcessMonitor if available

            # T5.4: Parse execution results with enhanced metadata
            execution_issues = reporter.parse_execution_logs(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                cmd=cmd_string,
                duration_ms=duration_ms,
                cpu_time_ms=cpu_time_ms,
                rss_peak_mb=rss_peak_mb,
            )
            issues.extend(execution_issues)

            # If execution failed, return early
            if exit_code != 0:
                logs["resource_usage"] = {"exit_code": exit_code}
                return None, logs, issues

            # T5.5: Enhanced artifact processing with size limits and re-encoding
            artifacts = artifact_manager.process_manim_output(
                class_name=class_name,
                scene_id=scene_id,
                source_filename="main",  # T5.3 uses main.py
            )

            if not artifacts:
                issues.append(
                    {
                        "type": "no_output",
                        "field": "manim_output",
                        "message": "Manim completed but no video output could be processed",
                        "value": None,
                        "severity": "error",
                        "kind": "no_output",  # T5.4 field
                        "hint": "Check Manim execution and output directory structure",  # T5.4 field
                    }
                )
                return None, logs, issues

            # T5.5: Verify processed video quality and size
            if artifacts.preview_mp4:
                video_info = artifact_manager.verify_video_quality(
                    artifacts.preview_mp4
                )
                if not video_info["valid"]:
                    issues.append(
                        {
                            "type": "invalid_video",
                            "field": "video_output",
                            "message": f"Processed video is invalid: {video_info.get('error', 'Unknown error')}",
                            "value": video_info,
                            "severity": "error",
                            "kind": "invalid_video",  # T5.4 field
                            "hint": "Check video encoding and ffmpeg installation",  # T5.4 field
                        }
                    )
                    return None, logs, issues

                # Log video info and size compliance
                logs["resource_usage"]["video_info"] = video_info
                video_size_mb = artifacts.preview_mp4.stat().st_size / (1024 * 1024)
                logs["resource_usage"]["video_size_mb"] = video_size_mb
                logs["resource_usage"]["size_compliant"] = (
                    video_size_mb <= 10
                )  # T5.5: 10MB limit

            # Check frame extraction
            if artifacts.first_frame_png is None:
                issues.append(
                    {
                        "type": "frame_extraction_failed",
                        "field": "first_frame",
                        "message": "Failed to extract first frame from video",
                        "value": None,
                        "severity": "warning",
                        "kind": "frame_extraction_failed",  # T5.4 field
                        "hint": "Check video format and ffmpeg installation",  # T5.4 field
                    }
                )

            logs["timings"]["artifact_processing"] = time.time() - start_time

            return artifacts, logs, issues

    except Exception as e:
        issues.append(
            {
                "type": "sandbox_error",
                "field": "execution",
                "message": f"Sandbox execution failed: {e}",
                "value": str(e),
                "severity": "error",
            }
        )

        logs["timings"]["total"] = time.time() - start_time
        return None, logs, issues


def validate_manim_installation() -> Dict[str, any]:
    """Check if Manim is properly installed and accessible."""
    try:
        import subprocess

        # Check manim command
        result = subprocess.run(
            ["manim", "--version"], capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0:
            version = result.stdout.strip()
            return {"available": True, "version": version, "command": "manim"}
        else:
            return {"available": False, "error": result.stderr, "command": "manim"}

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        return {"available": False, "error": str(e), "command": "manim"}


def validate_ffmpeg_installation() -> Dict[str, any]:
    """Check if FFmpeg is available for video processing."""
    try:
        import subprocess

        # Check ffmpeg command
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split("\n")[0]
            return {"available": True, "version": first_line, "command": "ffmpeg"}
        else:
            return {"available": False, "error": result.stderr, "command": "ffmpeg"}

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        return {"available": False, "error": str(e), "command": "ffmpeg"}


def check_system_dependencies() -> Dict[str, Dict[str, any]]:
    """Check all required system dependencies."""
    return {
        "manim": validate_manim_installation(),
        "ffmpeg": validate_ffmpeg_installation(),
    }
