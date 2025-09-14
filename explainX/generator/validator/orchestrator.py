"""
T5.6: Orchestration glue and retries for complete scene validation.
Combines T5.1-T5.5 components with intelligent retry policies.
"""

import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from .errors import (
    ValidationError,
    SourceSafetyError,
    RunnerTimeoutError,
    RunnerOOMError,
    RunnerExecutionError,
    NeedsRepair,
)
from .scene_static import validate_scene_json, validate_style_pack
from .source_safety import validate_source_safety
from .runner import run_manim_preview
from .reporter import ErrorReporter
from .artifacts import ArtifactManager
from . import ValidateInput, ValidateResult
from .metrics import validation_metrics_context, record_retry


# T5.6: Flaky error patterns that should trigger retries
FLAKY_ERROR_PATTERNS = [
    # LaTeX random failures
    "latex error: emergency stop",
    "tex capacity exceeded",
    "font not found",
    "font warning",
    "cairo error",
    "pango warning",
    # Temporary resource issues
    "resource temporarily unavailable",
    "connection refused",
    "timeout",
]

# Exit codes that indicate flakiness (not permanent failures)
FLAKY_EXIT_CODES = [
    # LaTeX/font issues
    1,  # General LaTeX error (may be transient)
    130,  # SIGINT (interrupted, could be transient)
    # System resource issues
    125,  # Resource temporarily unavailable
]

# Safety/schema errors that should NOT be retried
NO_RETRY_ERROR_TYPES = [
    "source_safety",
    "validation_error",
    "safety_issue",
    "schema_error",
    "asset_missing",  # Missing files won't appear on retry
    "class_missing",  # Missing classes won't appear on retry
]


def orchestrate_validation(vin: ValidateInput, max_retries: int = 1) -> ValidateResult:
    """
    T5.6: Complete orchestration of scene validation with retry policy.

    Combines all T5.1-T5.5 components:
    - T5.1: Static validation of scene JSON and style pack
    - T5.2: Source safety scanning
    - T5.3: Sandboxed Manim execution
    - T5.4: Enhanced error reporting
    - T5.5: Artifact processing with size limits

    Args:
        vin: ValidateInput with scene data and configuration
        max_retries: Maximum number of retries (default 1)

    Returns:
        ValidateResult on success

    Raises:
        NeedsRepair: When validation fails with structured error payload
        ValidationError: For non-retryable validation failures
        SourceSafetyError: For safety violations (non-retryable)
    """
    start_time = time.time()
    attempt = 0
    last_issues = []
    last_stderr = ""

    while attempt <= max_retries:
        # T5.7: Use metrics context for each attempt
        with validation_metrics_context(
            vin.video_id, vin.scene_id, attempt=attempt + 1
        ) as metrics_ctx:
            try:
                # Reset for each attempt
                issues = []
                logs = {"attempt": attempt + 1}

                # T5.1: Static validation (scene JSON + style pack)
                try:
                    validate_scene_json(vin.scene_json)
                    validate_style_pack(vin.style)
                    logs["static_validation"] = "passed"
                except ValidationError as e:
                    # T5.6: Schema/validation errors are not retryable
                    metrics_ctx.set_error_kind("validation_error")
                    raise NeedsRepair.from_issues(
                        scene_id=vin.scene_id,
                        issues=[
                            {
                                "type": "validation_error",
                                "kind": "validation_error",
                                "field": e.field,
                                "message": e.message,
                                "severity": "error",
                            }
                        ],
                        stderr_excerpt="",
                    )

                # T5.2: Source safety scanning
                try:
                    validate_source_safety(vin.source_text)
                    logs["safety_validation"] = "passed"
                except SourceSafetyError as e:
                    # T5.6: Safety errors are not retryable
                    metrics_ctx.set_error_kind("source_safety")
                    raise NeedsRepair.from_issues(
                        scene_id=vin.scene_id,
                        issues=[
                            {
                                "type": "source_safety",
                                "kind": "source_safety",
                                "field": getattr(e, "field", "source"),
                                "message": str(e),
                                "severity": "error",
                            }
                        ],
                        stderr_excerpt="",
                    )

                # T5.3, T5.4, T5.5: Sandboxed execution with enhanced reporting and artifacts
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

                # T5.7: Update metrics context with execution data
                if "resource_usage" in logs:
                    resource_usage = logs["resource_usage"]
                    metrics_ctx.set_exit_code(resource_usage.get("exit_code", 0))
                    metrics_ctx.set_rss_peak_mb(resource_usage.get("rss_peak_mb", 0.0))

                # Check for errors
                error_issues = [i for i in issues if i.get("severity") == "error"]

                if error_issues:
                    # Store for potential retry decision
                    last_issues = issues
                    last_stderr = logs.get("stderr", "")

                    # T5.6: Check if errors are retryable
                    if attempt < max_retries and _should_retry(error_issues, logs):
                        # T5.7: Record retry attempt
                        error_kind = error_issues[0].get("kind", "unknown")
                        metrics_ctx.set_error_kind(error_kind)
                        record_retry(
                            vin.video_id,
                            vin.scene_id,
                            (time.time() - start_time) * 1000,
                            error_kind,
                            attempt + 1,
                        )
                        attempt += 1
                        logs["retry_reason"] = "Detected flaky error pattern"
                        continue
                    else:
                        # No more retries or non-retryable error
                        error_kind = error_issues[0].get("kind", "unknown")
                        metrics_ctx.set_error_kind(error_kind)
                        raise NeedsRepair.from_issues(
                            scene_id=vin.scene_id,
                            issues=error_issues,
                            stderr_excerpt=last_stderr,
                        )

                # Success case
                total_duration = time.time() - start_time
                logs["total_duration_ms"] = total_duration * 1000
                logs["success"] = True

                # T5.7: Mark success in metrics
                metrics_ctx.set_success()

                return ValidateResult(
                    ok=True,
                    preview_mp4=artifacts.preview_mp4 if artifacts else None,
                    first_frame_png=artifacts.first_frame_png if artifacts else None,
                    logs=logs,
                    issues=issues,  # May include warnings
                )

            except (NeedsRepair, ValidationError, SourceSafetyError):
                # These exceptions should not be retried
                raise
            except Exception as e:
                # Unexpected exceptions - might be worth retrying
                metrics_ctx.set_error_kind("unexpected_error")
                error_issue = {
                    "type": "unexpected_error",
                    "kind": "unexpected_error",
                    "field": "execution",
                    "message": f"Unexpected error: {str(e)}",
                    "severity": "error",
                }

                if attempt < max_retries:
                    attempt += 1
                    continue
                else:
                    raise NeedsRepair.from_issues(
                        scene_id=vin.scene_id,
                        issues=[error_issue],
                        stderr_excerpt=str(e)[:500],
                    )

    # Should not reach here, but safety fallback
    raise NeedsRepair.from_issues(
        scene_id=vin.scene_id, issues=last_issues or [], stderr_excerpt=last_stderr
    )


def _should_retry(error_issues: List[Dict[str, Any]], logs: Dict[str, Any]) -> bool:
    """
    T5.6: Determine if errors warrant a retry based on retry policy.

    Retry rules:
    - One retry if exit code indicates flakiness (LaTeX random fail, font warning)
    - No retry on safety errors or schema errors

    Args:
        error_issues: List of error-level issues
        logs: Execution logs with stderr, exit_code, etc.

    Returns:
        True if should retry, False otherwise
    """
    # Check for non-retryable error types
    for issue in error_issues:
        issue_type = issue.get("type", "")
        issue_kind = issue.get("kind", "")

        if issue_type in NO_RETRY_ERROR_TYPES or issue_kind in NO_RETRY_ERROR_TYPES:
            return False

    # Check for flaky exit codes
    exit_code = logs.get("resource_usage", {}).get("exit_code") or logs.get(
        "exit_code", 0
    )
    if exit_code in FLAKY_EXIT_CODES:
        return True

    # Check for flaky error patterns in stderr
    stderr = logs.get("stderr", "").lower()
    for pattern in FLAKY_ERROR_PATTERNS:
        if pattern in stderr:
            return True

    # Check for flaky patterns in error messages
    for issue in error_issues:
        message = issue.get("message", "").lower()
        for pattern in FLAKY_ERROR_PATTERNS:
            if pattern in message:
                return True

    # Default: don't retry
    return False


def validate_scene_with_orchestration(vin: ValidateInput) -> ValidateResult:
    """
    T5.6: High-level validation entry point with orchestration.

    This is the main entry point that queue workers should use.
    Provides comprehensive validation with retry policies.
    """
    try:
        return orchestrate_validation(vin, max_retries=1)
    except NeedsRepair:
        # Let NeedsRepair bubble up to queue worker
        raise
    except Exception as e:
        # Convert unexpected exceptions to NeedsRepair
        raise NeedsRepair.from_issues(
            scene_id=vin.scene_id,
            issues=[
                {
                    "type": "orchestration_error",
                    "kind": "orchestration_error",
                    "field": "orchestration",
                    "message": f"Orchestration failed: {str(e)}",
                    "severity": "error",
                }
            ],
            stderr_excerpt=str(e)[:500],
        )
