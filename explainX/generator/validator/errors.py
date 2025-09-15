"""
Typed exceptions and error payloads for validation.
"""

from dataclasses import dataclass
from typing import Any, Optional


class ValidationError(Exception):
    """Raised when validation fails with a specific field path."""

    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"{field}: {message}")


class SourceSafetyError(ValidationError):
    """Raised when source code contains unsafe patterns."""

    pass


class SandboxError(Exception):
    """Raised when sandboxed execution fails."""

    def __init__(
        self, message: str, stdout: str = "", stderr: str = "", exit_code: int = -1
    ):
        self.message = message
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        super().__init__(message)


@dataclass(frozen=True)
class ValidationIssue:
    """Structured representation of a validation issue."""

    type: str  # "validation_error", "warning", "safety_issue", etc.
    field: Optional[str]  # JSON field path like "timeline[0].latex"
    message: str  # Human-readable description
    value: Any = None  # The problematic value
    severity: str = "error"  # "error", "warning", "info"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "field": self.field,
            "message": self.message,
            "value": self.value,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class SafetyIssue:
    """Specific type of issue for source code safety."""

    pattern: str  # The disallowed pattern found
    line_number: int  # Where it was found
    context: str  # Surrounding code context
    message: str  # Why it's unsafe

    def to_validation_issue(self) -> ValidationIssue:
        """Convert to generic ValidationIssue."""
        return ValidationIssue(
            type="safety_issue",
            field=f"source_line_{self.line_number}",
            message=f"Unsafe pattern '{self.pattern}': {self.message}",
            value=self.context,
            severity="error",
        )


class ContentLengthError(ValidationError):
    """Raised when content exceeds maximum allowed length."""

    def __init__(
        self, field: str, actual_length: int, max_length: int, content: str = ""
    ):
        message = f"Content length {actual_length} exceeds maximum {max_length}"
        super().__init__(
            field, message, content[:100] + "..." if len(content) > 100 else content
        )
        self.actual_length = actual_length
        self.max_length = max_length


class StyleBoundsError(ValidationError):
    """Raised when style values are outside acceptable bounds."""

    def __init__(self, field: str, value: float, min_val: float, max_val: float):
        message = f"Value {value} is outside bounds [{min_val}, {max_val}]"
        super().__init__(field, message, value)
        self.value = value
        self.min_val = min_val
        self.max_val = max_val


class RangeError(ValidationError):
    """Raised when range values are incoherent (min >= max, step <= 0, etc.)."""

    def __init__(self, field: str, min_val: float, max_val: float, step: float = None):
        if step is not None:
            message = f"Invalid range: min={min_val}, max={max_val}, step={step}"
        else:
            message = f"Invalid range: min={min_val} >= max={max_val}"
        super().__init__(field, message, {"min": min_val, "max": max_val, "step": step})
        self.min_val = min_val
        self.max_val = max_val
        self.step = step


# T5.6: Enhanced exception classes for orchestration and runner details
@dataclass
class RunnerTimeoutError(Exception):
    """Runner process timeout error."""

    seconds: int
    message: str = "Process timed out"

    def __post_init__(self):
        super().__init__(f"Process timed out after {self.seconds} seconds")


@dataclass
class RunnerOOMError(Exception):
    """Runner out-of-memory error."""

    mb: int
    message: str = "Out of memory"

    def __post_init__(self):
        super().__init__(f"Process exceeded memory limit of {self.mb} MB")


@dataclass
class RunnerExecutionError(Exception):
    """Runner execution error with exit code and stderr."""

    exit_code: int
    stderr_excerpt: str
    message: str = "Execution failed"

    def __post_init__(self):
        super().__init__(f"Process failed with exit code {self.exit_code}")


@dataclass
class NeedsRepair(Exception):
    """
    T5.6: Exception indicating scene needs repair with compact payload.

    Used to signal that validation failed and the scene should be sent
    to the repair agent with structured error information.
    """

    payload: dict

    def __post_init__(self):
        scene_id = self.payload.get("scene_id", "unknown")
        error_count = len(self.payload.get("errors", []))
        super().__init__(f"Scene {scene_id} needs repair ({error_count} errors)")

    @classmethod
    def from_issues(
        cls, scene_id: str, issues: list, stderr_excerpt: str = ""
    ) -> "NeedsRepair":
        """Create NeedsRepair from validation issues."""
        # Convert issues to compact error format
        errors = []
        for issue in issues:
            if issue.get("severity") == "error":
                error = {
                    "kind": issue.get("kind", issue.get("type", "unknown")),
                    "message": issue.get("message", "Unknown error"),
                    "field": issue.get("field", "unknown"),
                }
                errors.append(error)

        payload = {
            "scene_id": scene_id,
            "errors": errors,
            "stderr_excerpt": (
                stderr_excerpt[-500:] if stderr_excerpt else ""
            ),  # Last 500 chars
        }

        return cls(payload=payload)
