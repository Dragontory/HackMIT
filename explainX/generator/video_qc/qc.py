"""
T7.2: QC checks for black frames, frozen frames, and validation.

Provides quality control functions to detect common video issues like
black frames, frozen frames, and other quality problems using FFmpeg filters.
"""

import json
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class QCIssue:
    """Represents a quality control issue found in video."""

    issue_type: str  # "black_frame", "frozen_frame", "spec_mismatch", etc.
    severity: str  # "warning", "error", "critical"
    start_time_s: float
    duration_s: float
    message: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


@dataclass(frozen=True)
class QCSettings:
    """Settings for quality control checks."""

    # Black frame detection
    black_threshold: float = 0.1  # Pixel intensity threshold (0-1)
    black_duration_threshold: float = 0.5  # Minimum duration to flag (seconds)

    # Frozen frame detection
    freeze_noise_threshold: float = 0.001  # Noise tolerance for freeze detection
    freeze_duration_threshold: float = 0.5  # Minimum duration to flag (seconds)

    # General settings
    ffmpeg_timeout: int = 300  # 5 minutes timeout for analysis
    enable_black_detection: bool = True
    enable_freeze_detection: bool = True
    enable_spec_validation: bool = True


class VideoQC:
    """T7.2: Video quality control checker."""

    def __init__(self, settings: QCSettings = None):
        """
        Initialize video QC checker.

        Args:
            settings: QC settings configuration
        """
        self.settings = settings or QCSettings()

    def run_qc_checks(
        self, video_path: Path, expected_specs: Dict[str, Any] = None
    ) -> List[QCIssue]:
        """
        Run comprehensive quality control checks on video.

        Args:
            video_path: Path to video file
            expected_specs: Expected video specifications for validation

        Returns:
            List of QC issues found
        """
        issues = []

        if not video_path.exists():
            issues.append(
                QCIssue(
                    issue_type="file_missing",
                    severity="critical",
                    start_time_s=0.0,
                    duration_s=0.0,
                    message=f"Video file not found: {video_path}",
                )
            )
            return issues

        # Check file size
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        if file_size_mb == 0:
            issues.append(
                QCIssue(
                    issue_type="empty_file",
                    severity="critical",
                    start_time_s=0.0,
                    duration_s=0.0,
                    message="Video file is empty",
                )
            )
            return issues

        # Run black frame detection
        if self.settings.enable_black_detection:
            try:
                black_issues = self._detect_black_frames(video_path)
                issues.extend(black_issues)
            except Exception as e:
                issues.append(
                    QCIssue(
                        issue_type="black_detection_failed",
                        severity="warning",
                        start_time_s=0.0,
                        duration_s=0.0,
                        message=f"Black frame detection failed: {str(e)}",
                    )
                )

        # Run frozen frame detection
        if self.settings.enable_freeze_detection:
            try:
                freeze_issues = self._detect_frozen_frames(video_path)
                issues.extend(freeze_issues)
            except Exception as e:
                issues.append(
                    QCIssue(
                        issue_type="freeze_detection_failed",
                        severity="warning",
                        start_time_s=0.0,
                        duration_s=0.0,
                        message=f"Frozen frame detection failed: {str(e)}",
                    )
                )

        # Validate specifications
        if self.settings.enable_spec_validation and expected_specs:
            try:
                spec_issues = self._validate_specifications(video_path, expected_specs)
                issues.extend(spec_issues)
            except Exception as e:
                issues.append(
                    QCIssue(
                        issue_type="spec_validation_failed",
                        severity="warning",
                        start_time_s=0.0,
                        duration_s=0.0,
                        message=f"Specification validation failed: {str(e)}",
                    )
                )

        return issues

    def _detect_black_frames(self, video_path: Path) -> List[QCIssue]:
        """Detect black frame sequences using blackdetect filter."""
        issues = []

        # Use FFmpeg blackdetect filter
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vf",
            f"blackdetect=d={self.settings.black_duration_threshold}:pix_th={self.settings.black_threshold}",
            "-f",
            "null",
            "-",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.settings.ffmpeg_timeout,
            )

            # Parse blackdetect output from stderr
            black_sequences = self._parse_blackdetect_output(result.stderr)

            for start_time, duration in black_sequences:
                if duration >= self.settings.black_duration_threshold:
                    issues.append(
                        QCIssue(
                            issue_type="black_frame",
                            severity="warning" if duration < 2.0 else "error",
                            start_time_s=start_time,
                            duration_s=duration,
                            message=f"Black frame sequence: {duration:.2f}s at {start_time:.2f}s",
                            metadata={
                                "threshold": self.settings.black_threshold,
                                "detection_method": "blackdetect",
                            },
                        )
                    )

        except subprocess.TimeoutExpired:
            issues.append(
                QCIssue(
                    issue_type="black_detection_timeout",
                    severity="warning",
                    start_time_s=0.0,
                    duration_s=0.0,
                    message=f"Black frame detection timed out after {self.settings.ffmpeg_timeout}s",
                )
            )
        except subprocess.CalledProcessError as e:
            # FFmpeg might return non-zero but still provide useful stderr output
            black_sequences = self._parse_blackdetect_output(e.stderr)

            for start_time, duration in black_sequences:
                if duration >= self.settings.black_duration_threshold:
                    issues.append(
                        QCIssue(
                            issue_type="black_frame",
                            severity="warning" if duration < 2.0 else "error",
                            start_time_s=start_time,
                            duration_s=duration,
                            message=f"Black frame sequence: {duration:.2f}s at {start_time:.2f}s",
                            metadata={
                                "threshold": self.settings.black_threshold,
                                "detection_method": "blackdetect",
                            },
                        )
                    )

        return issues

    def _detect_frozen_frames(self, video_path: Path) -> List[QCIssue]:
        """Detect frozen frame sequences using freezedetect filter."""
        issues = []

        # Use FFmpeg freezedetect filter
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vf",
            f"freezedetect=n={self.settings.freeze_noise_threshold}:d={self.settings.freeze_duration_threshold}",
            "-f",
            "null",
            "-",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.settings.ffmpeg_timeout,
            )

            # Parse freezedetect output from stderr
            freeze_sequences = self._parse_freezedetect_output(result.stderr)

            for start_time, duration in freeze_sequences:
                if duration >= self.settings.freeze_duration_threshold:
                    issues.append(
                        QCIssue(
                            issue_type="frozen_frame",
                            severity="warning" if duration < 2.0 else "error",
                            start_time_s=start_time,
                            duration_s=duration,
                            message=f"Frozen frame sequence: {duration:.2f}s at {start_time:.2f}s",
                            metadata={
                                "noise_threshold": self.settings.freeze_noise_threshold,
                                "detection_method": "freezedetect",
                            },
                        )
                    )

        except subprocess.TimeoutExpired:
            issues.append(
                QCIssue(
                    issue_type="freeze_detection_timeout",
                    severity="warning",
                    start_time_s=0.0,
                    duration_s=0.0,
                    message=f"Frozen frame detection timed out after {self.settings.ffmpeg_timeout}s",
                )
            )
        except subprocess.CalledProcessError as e:
            # FFmpeg might return non-zero but still provide useful stderr output
            freeze_sequences = self._parse_freezedetect_output(e.stderr)

            for start_time, duration in freeze_sequences:
                if duration >= self.settings.freeze_duration_threshold:
                    issues.append(
                        QCIssue(
                            issue_type="frozen_frame",
                            severity="warning" if duration < 2.0 else "error",
                            start_time_s=start_time,
                            duration_s=duration,
                            message=f"Frozen frame sequence: {duration:.2f}s at {start_time:.2f}s",
                            metadata={
                                "noise_threshold": self.settings.freeze_noise_threshold,
                                "detection_method": "freezedetect",
                            },
                        )
                    )

        return issues

    def _validate_specifications(
        self, video_path: Path, expected_specs: Dict[str, Any]
    ) -> List[QCIssue]:
        """Validate video meets expected specifications."""
        from .probe import VideoProbe

        issues = []

        try:
            probe = VideoProbe()
            spec_issues = probe.verify_video_specs(video_path, expected_specs)

            for issue_msg in spec_issues:
                issues.append(
                    QCIssue(
                        issue_type="spec_mismatch",
                        severity="error",
                        start_time_s=0.0,
                        duration_s=0.0,
                        message=issue_msg,
                        metadata={"expected_specs": expected_specs},
                    )
                )

        except Exception as e:
            issues.append(
                QCIssue(
                    issue_type="spec_validation_error",
                    severity="warning",
                    start_time_s=0.0,
                    duration_s=0.0,
                    message=f"Specification validation error: {str(e)}",
                )
            )

        return issues

    def _parse_blackdetect_output(self, stderr_output: str) -> List[tuple]:
        """Parse blackdetect filter output to extract black sequences."""
        sequences = []

        # Look for patterns like: [blackdetect @ 0x...] black_start:1.5 black_end:2.0 black_duration:0.5
        pattern = r"\[blackdetect.*?\]\s+black_start:(\d+\.?\d*)\s+black_end:(\d+\.?\d*)\s+black_duration:(\d+\.?\d*)"

        for match in re.finditer(pattern, stderr_output):
            start_time = float(match.group(1))
            end_time = float(match.group(2))
            duration = float(match.group(3))
            sequences.append((start_time, duration))

        return sequences

    def _parse_freezedetect_output(self, stderr_output: str) -> List[tuple]:
        """Parse freezedetect filter output to extract frozen sequences."""
        sequences = []

        # Look for patterns like: [freezedetect @ 0x...] lavfi.freezedetect.freeze_start: 1.5
        # and: [freezedetect @ 0x...] lavfi.freezedetect.freeze_duration: 0.5
        start_pattern = (
            r"\[freezedetect.*?\]\s+lavfi\.freezedetect\.freeze_start:\s*(\d+\.?\d*)"
        )
        duration_pattern = (
            r"\[freezedetect.*?\]\s+lavfi\.freezedetect\.freeze_duration:\s*(\d+\.?\d*)"
        )

        starts = []
        durations = []

        for match in re.finditer(start_pattern, stderr_output):
            starts.append(float(match.group(1)))

        for match in re.finditer(duration_pattern, stderr_output):
            durations.append(float(match.group(1)))

        # Pair up starts and durations (they should appear in sequence)
        for i in range(min(len(starts), len(durations))):
            sequences.append((starts[i], durations[i]))

        return sequences

    def get_qc_summary(self, issues: List[QCIssue]) -> Dict[str, Any]:
        """
        Generate a summary of QC issues.

        Args:
            issues: List of QC issues

        Returns:
            Summary dictionary with counts and categorization
        """
        summary = {
            "total_issues": len(issues),
            "by_severity": {"critical": 0, "error": 0, "warning": 0},
            "by_type": {},
            "critical_issues": [],
            "total_affected_duration_s": 0.0,
        }

        for issue in issues:
            # Count by severity
            summary["by_severity"][issue.severity] += 1

            # Count by type
            issue_type = issue.issue_type
            summary["by_type"][issue_type] = summary["by_type"].get(issue_type, 0) + 1

            # Track critical issues
            if issue.severity == "critical":
                summary["critical_issues"].append(issue.message)

            # Sum affected duration
            summary["total_affected_duration_s"] += issue.duration_s

        # Overall assessment
        if summary["by_severity"]["critical"] > 0:
            summary["overall_status"] = "critical"
        elif summary["by_severity"]["error"] > 0:
            summary["overall_status"] = "error"
        elif summary["by_severity"]["warning"] > 0:
            summary["overall_status"] = "warning"
        else:
            summary["overall_status"] = "pass"

        return summary


def run_video_qc(
    video_path: Path, expected_specs: Dict[str, Any] = None, settings: QCSettings = None
) -> List[QCIssue]:
    """
    Convenience function to run video quality control checks.

    Args:
        video_path: Path to video file
        expected_specs: Expected video specifications
        settings: QC settings

    Returns:
        List of QC issues found
    """
    qc = VideoQC(settings)
    return qc.run_qc_checks(video_path, expected_specs)


def check_for_issues(video_path: Path, settings: QCSettings = None) -> bool:
    """
    Quick check if video has any quality issues.

    Args:
        video_path: Path to video file
        settings: QC settings

    Returns:
        True if issues found, False if clean
    """
    qc = VideoQC(settings)
    issues = qc.run_qc_checks(video_path)
    return len(issues) > 0
