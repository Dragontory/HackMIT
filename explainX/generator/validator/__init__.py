"""
Ticket 5: Validator and Dry-Run Runner

Validates scene JSON, style packs, and generated Python source.
Runs sandboxed Manim execution to produce preview artifacts.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TYPE_CHECKING, Optional, List, Dict

if TYPE_CHECKING:
    from generator.style.models import StylePack

from .errors import ValidationError, ValidationIssue, SourceSafetyError
from .scene_static import validate_scene_json, validate_style_pack
from .source_safety import check_source_safety, validate_source_safety
from .runner import run_manim_preview
from .artifacts import PreviewArtifacts
from .sandbox import SandboxLimits


@dataclass(frozen=True)
class ValidateInput:
    """Input for scene validation."""

    video_id: str
    scene_id: str
    scene_json: dict  # already T1-valid from earlier stage
    style: "StylePack"  # from T2
    source_text: str  # Python source from T4 for this scene
    class_name: str  # e.g., "Scene_sec_01"
    work_dir: Path  # base temp dir for this job
    q_level: Literal["low", "preview"] = "preview"


@dataclass(frozen=True)
class ValidateResult:
    """Result of scene validation."""

    ok: bool
    preview_mp4: Optional[Path]
    first_frame_png: Optional[Path]
    logs: dict  # stdout, stderr, timings, resource usage
    issues: List[Dict]  # structured warnings or non-fatal notes


def validate_scene(vin: ValidateInput) -> ValidateResult:
    """
    Main entry point for scene validation.

    1) Static checks on JSON and style
    2) Safety scan of Python source
    3) Dry-run Manim in sandbox to produce a preview
    4) Return artifacts or structured errors
    """
    issues = []
    logs = {"stdout": "", "stderr": "", "timings": {}, "resource_usage": {}}

    try:
        # Step 1: Static validation
        validate_scene_json(vin.scene_json)
        validate_style_pack(vin.style)

        # Step 2: Source safety checks
        try:
            validate_source_safety(vin.source_text)
        except SourceSafetyError as e:
            # Add the safety error to issues
            safety_issue = ValidationIssue(
                type="source_safety",
                field=getattr(e, "field", "source"),
                message=str(e),
                value=getattr(e, "value", None),
                severity="error",
            )
            issues.append(safety_issue.to_dict())
            return ValidateResult(
                ok=False,
                preview_mp4=None,
                first_frame_png=None,
                logs=logs,
                issues=issues,
            )

        # Step 3: Sandboxed Manim execution
        artifacts, run_logs, run_issues = run_manim_preview(
            source_text=vin.source_text,
            class_name=vin.class_name,
            work_dir=vin.work_dir,
            q_level=vin.q_level,
            video_id=vin.video_id,
            scene_id=vin.scene_id,
        )

        # Merge logs and issues
        logs.update(run_logs)
        issues.extend(run_issues)

        return ValidateResult(
            ok=True,
            preview_mp4=artifacts.preview_mp4 if artifacts else None,
            first_frame_png=artifacts.first_frame_png if artifacts else None,
            logs=logs,
            issues=issues,
        )

    except ValidationError as e:
        issues.append(
            {
                "type": "validation_error",
                "field": e.field,
                "message": e.message,
                "value": e.value,
            }
        )

        return ValidateResult(
            ok=False, preview_mp4=None, first_frame_png=None, logs=logs, issues=issues
        )

    except Exception as e:
        issues.append(
            {
                "type": "unexpected_error",
                "message": str(e),
                "field": None,
                "value": None,
            }
        )

        return ValidateResult(
            ok=False, preview_mp4=None, first_frame_png=None, logs=logs, issues=issues
        )


__all__ = [
    "ValidateInput",
    "ValidateResult",
    "validate_scene",
    "ValidationError",
    "ValidationIssue",
    "SandboxLimits",
]
