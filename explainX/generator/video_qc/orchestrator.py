"""
T7.5: End-to-end QC orchestrator.

Coordinates all video QC components (probe, QC checks, metadata, thumbnails)
into a complete quality control and delivery preparation pipeline.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from . import QCInput, QCResult
from .probe import VideoProbe, VideoMetadata
from .qc import VideoQC, QCSettings, QCIssue
from .metadata import ManifestBuilder, VideoManifest
from .thumbs import ExtendedThumbnailGenerator, ThumbnailResult


class QCOrchestrator:
    """T7.5: Complete video QC and delivery preparation orchestrator."""

    def __init__(
        self,
        qc_settings: QCSettings = None,
        logger: logging.Logger = None,
    ):
        """
        Initialize QC orchestrator.

        Args:
            qc_settings: Quality control settings
            logger: Logger instance
        """
        self.qc_settings = qc_settings or QCSettings()
        self.logger = logger or self._setup_logger()

        # Initialize components
        self.probe = VideoProbe()
        self.qc_checker = VideoQC(self.qc_settings)
        self.manifest_builder = ManifestBuilder()
        self.thumbnail_generator = ExtendedThumbnailGenerator()

    def _setup_logger(self) -> logging.Logger:
        """Setup default logger for QC operations."""
        logger = logging.getLogger("video_qc")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def run_qc_pipeline(self, qc_input: QCInput) -> QCResult:
        """
        Execute complete QC and delivery preparation pipeline.

        Args:
            qc_input: QC input specification

        Returns:
            QCResult with QC results and delivery artifacts
        """
        start_time = time.time()
        logs = {
            "video_id": qc_input.video_id,
            "input_file": str(qc_input.final_mp4),
            "start_time": start_time,
        }

        self.logger.info(f"Starting QC pipeline for video: {qc_input.video_id}")

        try:
            # Step 1: Probe video metadata
            self.logger.info("Step 1: Probing video metadata")
            video_metadata, probe_time = self._probe_video_with_timing(
                qc_input.final_mp4
            )

            logs["probe_time_s"] = probe_time
            logs["video_metadata"] = {
                "duration_s": video_metadata.duration_s,
                "resolution": video_metadata.resolution,
                "fps": video_metadata.fps,
                "codec": video_metadata.codec,
                "frame_count": video_metadata.frame_count,
            }

            # Step 2: Run QC checks
            self.logger.info("Step 2: Running quality control checks")
            qc_issues, qc_time = self._run_qc_checks_with_timing(
                qc_input.final_mp4, video_metadata
            )

            logs["qc_time_s"] = qc_time
            logs["qc_issues_found"] = len(qc_issues)

            # Log QC issues summary
            if qc_issues:
                qc_summary = self.qc_checker.get_qc_summary(qc_issues)
                logs["qc_summary"] = qc_summary
                self.logger.warning(
                    f"Found {len(qc_issues)} QC issues: " f"{qc_summary['by_severity']}"
                )
            else:
                self.logger.info("No QC issues found")

            # Step 3: Generate extended thumbnails
            self.logger.info("Step 3: Generating extended thumbnails")
            extra_thumbs, thumb_time = self._generate_thumbnails_with_timing(
                qc_input.final_mp4, qc_input.out_dir, qc_input.video_id
            )

            logs["thumbnail_time_s"] = thumb_time
            logs["thumbnails_generated"] = len(extra_thumbs)

            # Step 4: Create metadata manifest
            self.logger.info("Step 4: Creating metadata manifest")
            manifest_path, manifest_time = self._create_manifest_with_timing(
                qc_input, video_metadata, qc_issues, extra_thumbs
            )

            logs["manifest_time_s"] = manifest_time
            logs["manifest_path"] = str(manifest_path)

            # Success!
            total_time = time.time() - start_time
            logs["total_duration_s"] = total_time
            logs["success"] = True

            # Collect issue messages for result
            issue_messages = [issue.message for issue in qc_issues]

            self.logger.info(
                f"QC pipeline completed for {qc_input.video_id} "
                f"({total_time:.1f}s, {len(qc_issues)} issues)"
            )

            return QCResult(
                ok=True,
                manifest=manifest_path,
                extra_thumbs=[
                    r.output_path for r in extra_thumbs if r.success and r.output_path
                ],
                issues=issue_messages,
                logs=logs,
            )

        except Exception as e:
            error_msg = f"QC pipeline failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return self._create_error_result(error_msg, logs, start_time)

    def _probe_video_with_timing(self, video_path: Path) -> tuple[VideoMetadata, float]:
        """Probe video metadata with timing."""
        start_time = time.time()

        try:
            metadata = self.probe.probe_video(video_path)
            probe_time = time.time() - start_time

            self.logger.info(
                f"Video probed: {metadata.resolution} @ {metadata.fps:.1f}fps, "
                f"{metadata.duration_s:.1f}s ({metadata.frame_count} frames)"
            )

            return metadata, probe_time

        except Exception as e:
            probe_time = time.time() - start_time
            self.logger.error(f"Video probing failed: {str(e)}")

            # Return minimal metadata on failure
            minimal_metadata = VideoMetadata(
                duration_s=0.0,
                width=0,
                height=0,
                fps=0.0,
                frame_count=0,
                codec="unknown",
                pixel_format="unknown",
            )

            return minimal_metadata, probe_time

    def _run_qc_checks_with_timing(
        self, video_path: Path, video_metadata: VideoMetadata
    ) -> tuple[List[QCIssue], float]:
        """Run QC checks with timing."""
        start_time = time.time()

        try:
            # Create expected specs from video metadata for validation
            expected_specs = {
                "width": video_metadata.width,
                "height": video_metadata.height,
                "fps": video_metadata.fps,
                "fps_tolerance": 0.1,
                "codec": "h264",  # Expected codec
                "pixel_format": "yuv420p",  # Expected pixel format
                "min_duration_s": 0.1,  # Minimum acceptable duration
            }

            qc_issues = self.qc_checker.run_qc_checks(video_path, expected_specs)
            qc_time = time.time() - start_time

            # Log issues by severity
            if qc_issues:
                by_severity = {"critical": 0, "error": 0, "warning": 0}
                for issue in qc_issues:
                    by_severity[issue.severity] += 1

                self.logger.info(
                    f"QC checks completed: {len(qc_issues)} issues "
                    f"(critical: {by_severity['critical']}, "
                    f"error: {by_severity['error']}, "
                    f"warning: {by_severity['warning']})"
                )
            else:
                self.logger.info("QC checks completed: no issues found")

            return qc_issues, qc_time

        except Exception as e:
            qc_time = time.time() - start_time
            self.logger.error(f"QC checks failed: {str(e)}")

            # Return error issue on failure
            error_issue = QCIssue(
                issue_type="qc_check_failed",
                severity="warning",
                start_time_s=0.0,
                duration_s=0.0,
                message=f"QC check execution failed: {str(e)}",
            )

            return [error_issue], qc_time

    def _generate_thumbnails_with_timing(
        self, video_path: Path, output_dir: Path, video_id: str
    ) -> tuple[List[ThumbnailResult], float]:
        """Generate extended thumbnails with timing."""
        start_time = time.time()

        try:
            # Create thumbnails subdirectory
            thumbs_dir = output_dir / "thumbnails"
            thumbs_dir.mkdir(parents=True, exist_ok=True)

            # Generate standard QC thumbnails
            thumbnail_results = self.thumbnail_generator.generate_standard_thumbnails(
                video_path=video_path,
                output_dir=thumbs_dir,
                video_name=video_id,
            )

            thumb_time = time.time() - start_time

            # Log results
            successful_thumbs = [r for r in thumbnail_results if r.success]
            failed_thumbs = [r for r in thumbnail_results if not r.success]

            self.logger.info(
                f"Thumbnail generation completed: {len(successful_thumbs)} successful, "
                f"{len(failed_thumbs)} failed"
            )

            if failed_thumbs:
                for result in failed_thumbs:
                    self.logger.warning(f"Thumbnail failed: {result.error_message}")

            return thumbnail_results, thumb_time

        except Exception as e:
            thumb_time = time.time() - start_time
            self.logger.error(f"Thumbnail generation failed: {str(e)}")

            # Return empty list on failure
            return [], thumb_time

    def _create_manifest_with_timing(
        self,
        qc_input: QCInput,
        video_metadata: VideoMetadata,
        qc_issues: List[QCIssue],
        thumbnail_results: List[ThumbnailResult],
    ) -> tuple[Path, float]:
        """Create metadata manifest with timing."""
        start_time = time.time()

        try:
            # Collect successful thumbnail paths
            successful_thumbs = [
                r.output_path
                for r in thumbnail_results
                if r.success and r.output_path and r.output_path.exists()
            ]

            # Include original thumbnails from T6 if provided
            all_thumbs = list(qc_input.thumbs) + successful_thumbs

            # Calculate total processing time (approximate)
            processing_time = (
                time.time()
                - start_time
                + sum(getattr(r, "generation_time_s", 0) for r in thumbnail_results)
            )

            # Create manifest
            manifest_path = self.manifest_builder.create_delivery_manifest(
                video_path=qc_input.final_mp4,
                video_id=qc_input.video_id,
                output_dir=qc_input.out_dir,
                qc_issues=qc_issues,
                thumbnails=all_thumbs,
                processing_time_s=processing_time,
            )

            manifest_time = time.time() - start_time

            self.logger.info(f"Manifest created: {manifest_path}")

            return manifest_path, manifest_time

        except Exception as e:
            manifest_time = time.time() - start_time
            self.logger.error(f"Manifest creation failed: {str(e)}")

            # Return None path on failure
            return None, manifest_time

    def _create_error_result(
        self, error_message: str, logs: Dict[str, Any], start_time: float
    ) -> QCResult:
        """Create error result with logs."""
        logs.update(
            {
                "success": False,
                "error_message": error_message,
                "total_duration_s": time.time() - start_time,
            }
        )

        return QCResult(
            ok=False,
            manifest=None,
            extra_thumbs=[],
            issues=[error_message],
            logs=logs,
        )

    def validate_input(self, qc_input: QCInput) -> List[str]:
        """
        Validate QC input before processing.

        Args:
            qc_input: QC input to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check video file exists
        if not qc_input.final_mp4.exists():
            errors.append(f"Video file not found: {qc_input.final_mp4}")
        elif qc_input.final_mp4.stat().st_size == 0:
            errors.append("Video file is empty")

        # Check output directory can be created
        try:
            qc_input.out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create output directory: {str(e)}")

        # Check thumbnail files exist (if provided)
        for thumb_path in qc_input.thumbs:
            if not thumb_path.exists():
                errors.append(f"Thumbnail file not found: {thumb_path}")

        return errors

    def get_qc_settings(self) -> QCSettings:
        """Get current QC settings."""
        return self.qc_settings

    def update_qc_settings(self, new_settings: QCSettings):
        """Update QC settings and reinitialize QC checker."""
        self.qc_settings = new_settings
        self.qc_checker = VideoQC(self.qc_settings)
        self.logger.info("QC settings updated")


def qc_and_package(qc_input: QCInput) -> QCResult:
    """
    Main entry point for T7 video QC and delivery preparation.

    Probe video, run QC, generate metadata manifest + extra thumbs.

    Args:
        qc_input: Complete QC input specification

    Returns:
        QCResult with QC results and delivery artifacts
    """
    orchestrator = QCOrchestrator()
    return orchestrator.run_qc_pipeline(qc_input)


def run_video_qc_pipeline(
    video_path: Path,
    video_id: str,
    output_dir: Path,
    existing_thumbs: List[Path] = None,
    qc_settings: QCSettings = None,
) -> QCResult:
    """
    Convenience function to run video QC pipeline.

    Args:
        video_path: Path to video file
        video_id: Video identifier
        output_dir: Output directory
        existing_thumbs: Existing thumbnail files
        qc_settings: QC settings

    Returns:
        QCResult with processing results
    """
    qc_input = QCInput(
        video_id=video_id,
        final_mp4=video_path,
        thumbs=existing_thumbs or [],
        out_dir=output_dir,
    )

    if qc_settings:
        orchestrator = QCOrchestrator(qc_settings=qc_settings)
        return orchestrator.run_qc_pipeline(qc_input)
    else:
        return qc_and_package(qc_input)


def quick_qc_check(video_path: Path) -> Dict[str, Any]:
    """
    Quick QC check that returns basic results.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with basic QC results
    """
    try:
        # Quick probe
        probe = VideoProbe()
        video_info = probe.get_basic_info(video_path)

        # Quick QC check
        qc_checker = VideoQC()
        issues = qc_checker.run_qc_checks(video_path)

        return {
            "video_info": video_info,
            "issues_count": len(issues),
            "has_critical_issues": any(
                issue.severity == "critical" for issue in issues
            ),
            "has_errors": any(issue.severity == "error" for issue in issues),
            "issues": [issue.message for issue in issues],
        }

    except Exception as e:
        return {
            "error": str(e),
            "video_info": {},
            "issues_count": 1,
            "has_critical_issues": True,
            "issues": [f"QC check failed: {str(e)}"],
        }
