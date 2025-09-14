"""
T7.3: Metadata manifest builder with SHA256 hashing.

Generates comprehensive metadata manifests for video files including
file hashes, video properties, and delivery information in JSON format.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from .probe import VideoMetadata, VideoProbe
from .qc import QCIssue


@dataclass(frozen=True)
class VideoManifest:
    """Comprehensive video metadata manifest."""

    # Basic identification
    video_id: str
    created_at: str  # ISO 8601 timestamp

    # File information
    file_path: str
    file_size_bytes: int
    hash_sha256: str
    hash_md5: Optional[str] = None

    # Video properties
    duration_s: float = 0.0
    resolution: str = "0x0"
    width: int = 0
    height: int = 0
    fps: float = 0.0
    frame_count: int = 0
    codec: str = "unknown"
    pixel_format: str = "unknown"
    bitrate_kbps: Optional[int] = None
    container_format: str = "mp4"
    aspect_ratio: float = 0.0

    # Quality control
    qc_passed: bool = True
    qc_issues_count: int = 0
    qc_critical_issues: int = 0
    qc_error_issues: int = 0
    qc_warning_issues: int = 0

    # Thumbnails and assets
    thumbnails: List[str] = None
    contact_sheet: Optional[str] = None

    # Processing metadata
    processing_time_s: float = 0.0
    processor_version: str = "1.0.0"

    def __post_init__(self):
        if self.thumbnails is None:
            object.__setattr__(self, "thumbnails", [])


class ManifestBuilder:
    """T7.3: Video metadata manifest builder."""

    def __init__(self, processor_version: str = "1.0.0"):
        """
        Initialize manifest builder.

        Args:
            processor_version: Version of the processing pipeline
        """
        self.processor_version = processor_version
        self.probe = VideoProbe()

    def build_manifest(
        self,
        video_path: Path,
        video_id: str,
        qc_issues: List[QCIssue] = None,
        thumbnails: List[Path] = None,
        contact_sheet: Path = None,
        processing_time_s: float = 0.0,
        include_md5: bool = False,
    ) -> VideoManifest:
        """
        Build comprehensive video manifest.

        Args:
            video_path: Path to video file
            video_id: Unique video identifier
            qc_issues: List of quality control issues
            thumbnails: List of thumbnail files
            contact_sheet: Path to contact sheet file
            processing_time_s: Total processing time
            include_md5: Whether to include MD5 hash (slower)

        Returns:
            VideoManifest with all metadata
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Get file information
        file_stats = video_path.stat()
        file_size_bytes = file_stats.st_size

        # Calculate file hashes
        hash_sha256 = self._calculate_sha256(video_path)
        hash_md5 = self._calculate_md5(video_path) if include_md5 else None

        # Get video metadata
        try:
            video_metadata = self.probe.probe_video(video_path)
        except Exception:
            # Create minimal metadata if probing fails
            video_metadata = VideoMetadata(
                duration_s=0.0,
                width=0,
                height=0,
                fps=0.0,
                frame_count=0,
                codec="unknown",
                pixel_format="unknown",
                bitrate_kbps=None,
                container_format="mp4",
            )

        # Process QC issues
        qc_issues = qc_issues or []
        qc_summary = self._summarize_qc_issues(qc_issues)

        # Process thumbnails
        thumbnail_paths = []
        if thumbnails:
            thumbnail_paths = [
                str(thumb.name) for thumb in thumbnails if thumb.exists()
            ]

        contact_sheet_name = None
        if contact_sheet and contact_sheet.exists():
            contact_sheet_name = str(contact_sheet.name)

        # Create manifest
        return VideoManifest(
            video_id=video_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            file_path=str(video_path.name),
            file_size_bytes=file_size_bytes,
            hash_sha256=hash_sha256,
            hash_md5=hash_md5,
            duration_s=video_metadata.duration_s,
            resolution=video_metadata.resolution,
            width=video_metadata.width,
            height=video_metadata.height,
            fps=video_metadata.fps,
            frame_count=video_metadata.frame_count,
            codec=video_metadata.codec,
            pixel_format=video_metadata.pixel_format,
            bitrate_kbps=video_metadata.bitrate_kbps,
            container_format=video_metadata.container_format,
            aspect_ratio=video_metadata.aspect_ratio,
            qc_passed=qc_summary["passed"],
            qc_issues_count=qc_summary["total"],
            qc_critical_issues=qc_summary["critical"],
            qc_error_issues=qc_summary["error"],
            qc_warning_issues=qc_summary["warning"],
            thumbnails=thumbnail_paths,
            contact_sheet=contact_sheet_name,
            processing_time_s=processing_time_s,
            processor_version=self.processor_version,
        )

    def save_manifest(self, manifest: VideoManifest, output_path: Path) -> bool:
        """
        Save manifest to JSON file.

        Args:
            manifest: Video manifest to save
            output_path: Path for output JSON file

        Returns:
            True if saved successfully
        """
        try:
            # Convert to dictionary and format for JSON
            manifest_dict = asdict(manifest)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save as pretty-printed JSON
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(manifest_dict, f, indent=2, ensure_ascii=False)

            return True

        except Exception:
            return False

    def load_manifest(self, manifest_path: Path) -> VideoManifest:
        """
        Load manifest from JSON file.

        Args:
            manifest_path: Path to JSON manifest file

        Returns:
            VideoManifest object
        """
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_dict = json.load(f)

        return VideoManifest(**manifest_dict)

    def verify_file_integrity(self, video_path: Path, manifest: VideoManifest) -> bool:
        """
        Verify video file integrity against manifest.

        Args:
            video_path: Path to video file
            manifest: Video manifest with expected hash

        Returns:
            True if file integrity is verified
        """
        if not video_path.exists():
            return False

        # Check file size
        current_size = video_path.stat().st_size
        if current_size != manifest.file_size_bytes:
            return False

        # Check SHA256 hash
        current_hash = self._calculate_sha256(video_path)
        if current_hash != manifest.hash_sha256:
            return False

        return True

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        hash_sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of file."""
        hash_md5 = hashlib.md5()

        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def _summarize_qc_issues(self, qc_issues: List[QCIssue]) -> Dict[str, Any]:
        """Summarize QC issues for manifest."""
        summary = {
            "total": len(qc_issues),
            "critical": 0,
            "error": 0,
            "warning": 0,
            "passed": True,
        }

        for issue in qc_issues:
            if issue.severity == "critical":
                summary["critical"] += 1
                summary["passed"] = False
            elif issue.severity == "error":
                summary["error"] += 1
                summary["passed"] = False
            elif issue.severity == "warning":
                summary["warning"] += 1

        return summary

    def create_delivery_manifest(
        self,
        video_path: Path,
        video_id: str,
        output_dir: Path,
        qc_issues: List[QCIssue] = None,
        thumbnails: List[Path] = None,
        contact_sheet: Path = None,
        processing_time_s: float = 0.0,
    ) -> Path:
        """
        Create and save delivery manifest.

        Args:
            video_path: Path to video file
            video_id: Unique video identifier
            output_dir: Directory for manifest file
            qc_issues: QC issues found
            thumbnails: Thumbnail files
            contact_sheet: Contact sheet file
            processing_time_s: Processing time

        Returns:
            Path to saved manifest file
        """
        manifest = self.build_manifest(
            video_path=video_path,
            video_id=video_id,
            qc_issues=qc_issues,
            thumbnails=thumbnails,
            contact_sheet=contact_sheet,
            processing_time_s=processing_time_s,
        )

        manifest_path = output_dir / "manifest.json"
        success = self.save_manifest(manifest, manifest_path)

        if not success:
            raise RuntimeError(f"Failed to save manifest to {manifest_path}")

        return manifest_path

    def validate_manifest_schema(self, manifest_dict: Dict[str, Any]) -> List[str]:
        """
        Validate manifest dictionary against expected schema.

        Args:
            manifest_dict: Manifest as dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Required fields
        required_fields = [
            "video_id",
            "created_at",
            "file_path",
            "file_size_bytes",
            "hash_sha256",
            "duration_s",
            "resolution",
            "width",
            "height",
            "fps",
            "frame_count",
            "codec",
        ]

        for field in required_fields:
            if field not in manifest_dict:
                errors.append(f"Missing required field: {field}")
            elif manifest_dict[field] is None:
                errors.append(f"Required field is null: {field}")

        # Type validation
        type_checks = {
            "video_id": str,
            "file_size_bytes": int,
            "hash_sha256": str,
            "duration_s": (int, float),
            "width": int,
            "height": int,
            "fps": (int, float),
            "frame_count": int,
            "qc_passed": bool,
        }

        for field, expected_type in type_checks.items():
            if field in manifest_dict:
                value = manifest_dict[field]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"Field {field} has wrong type: expected {expected_type}, got {type(value)}"
                    )

        # Value validation
        if "hash_sha256" in manifest_dict:
            hash_val = manifest_dict["hash_sha256"]
            if not isinstance(hash_val, str) or len(hash_val) != 64:
                errors.append("hash_sha256 must be 64-character hex string")

        if "duration_s" in manifest_dict:
            duration = manifest_dict["duration_s"]
            if isinstance(duration, (int, float)) and duration < 0:
                errors.append("duration_s must be non-negative")

        return errors


def create_video_manifest(
    video_path: Path,
    video_id: str,
    output_dir: Path,
    qc_issues: List[QCIssue] = None,
    thumbnails: List[Path] = None,
    processing_time_s: float = 0.0,
) -> Path:
    """
    Convenience function to create video manifest.

    Args:
        video_path: Path to video file
        video_id: Video identifier
        output_dir: Output directory
        qc_issues: QC issues found
        thumbnails: Thumbnail files
        processing_time_s: Processing time

    Returns:
        Path to created manifest file
    """
    builder = ManifestBuilder()
    return builder.create_delivery_manifest(
        video_path=video_path,
        video_id=video_id,
        output_dir=output_dir,
        qc_issues=qc_issues,
        thumbnails=thumbnails,
        processing_time_s=processing_time_s,
    )


def calculate_file_hash(file_path: Path) -> str:
    """
    Convenience function to calculate SHA256 hash.

    Args:
        file_path: Path to file

    Returns:
        SHA256 hash as hex string
    """
    builder = ManifestBuilder()
    return builder._calculate_sha256(file_path)
