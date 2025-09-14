"""
T7: Video QC, Metadata, and Delivery Prep (Video-Only).

Post-processing pipeline for video quality control, metadata generation,
and delivery preparation for silent MP4 videos from the T6 renderer.

Scope:
- Video quality checks (black frames, frozen frames)
- Metadata extraction and manifest generation
- Extended thumbnail and contact sheet creation
- No audio, captions, or intro processing
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

__version__ = "1.0.0"


@dataclass(frozen=True)
class QCInput:
    """Input specification for video quality control and packaging."""

    video_id: str
    final_mp4: Path  # Silent MP4 from Ticket 6
    thumbs: List[Path]  # Poster frames from T6 (optional, for reference)
    out_dir: Path  # Output directory for QC artifacts

    def __post_init__(self):
        """Validate QC input parameters."""
        if not self.video_id:
            raise ValueError("video_id is required")
        if not self.final_mp4:
            raise ValueError("final_mp4 path is required")
        if not self.out_dir:
            raise ValueError("out_dir is required")


@dataclass(frozen=True)
class QCResult:
    """Result of video quality control and packaging."""

    ok: bool
    manifest: Optional[Path] = None  # JSON metadata manifest
    extra_thumbs: List[Path] = None  # Additional thumbnails generated
    issues: List[str] = None  # QC issues found
    logs: Dict[str, Any] = None  # Processing logs and metrics

    def __post_init__(self):
        # Initialize mutable defaults safely
        if self.extra_thumbs is None:
            object.__setattr__(self, "extra_thumbs", [])
        if self.issues is None:
            object.__setattr__(self, "issues", [])
        if self.logs is None:
            object.__setattr__(self, "logs", {})


# Export main entry point and components
from .orchestrator import qc_and_package
from .probe import VideoProbe, VideoMetadata, probe_video_file, get_video_info
from .qc import VideoQC, QCSettings, QCIssue, run_video_qc
from .metadata import ManifestBuilder, VideoManifest, create_video_manifest
from .thumbs import ExtendedThumbnailGenerator, ThumbnailResult, generate_qc_thumbnails

__all__ = [
    "QCInput",
    "QCResult",
    "qc_and_package",
    "VideoProbe",
    "VideoMetadata",
    "probe_video_file",
    "get_video_info",
    "VideoQC",
    "QCSettings",
    "QCIssue",
    "run_video_qc",
    "ManifestBuilder",
    "VideoManifest",
    "create_video_manifest",
    "ExtendedThumbnailGenerator",
    "ThumbnailResult",
    "generate_qc_thumbnails",
]
