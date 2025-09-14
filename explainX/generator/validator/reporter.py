"""
Enhanced reporter and error normalization for T5.4.
Converts Manim execution logs to typed, structured issues ready for repair agents.
"""

import re
from typing import List, Dict, Any, Optional


class ErrorReporter:
    """
    Enhanced error reporter for T5.4 specifications.
    Converts Manim execution logs to typed structured validation issues.
    """

    def __init__(self):
        # T5.4 Enhanced error patterns with typed issues
        self.error_patterns = [
            # T5.4: LaTeX compilation problems
            (
                r"LaTeX Error: (.+)",
                "latex_error",
                lambda m: {
                    "message": f"LaTeX compilation failed: {m.group(1)}",
                    "snippet": m.group(1),
                    "hint": "Check LaTeX syntax in MathTex or Tex objects",
                },
            ),
            (
                r"Package .+ Error: (.+)",
                "latex_error",
                lambda m: {
                    "message": f"LaTeX package error: {m.group(1)}",
                    "snippet": m.group(1),
                    "hint": "LaTeX package issue - check math expressions",
                },
            ),
            (
                r"! (.+)",  # LaTeX error indicator
                "latex_error",
                lambda m: {
                    "message": f"LaTeX error: {m.group(1)}",
                    "snippet": m.group(1),
                    "hint": "Review MathTex/Tex content for syntax errors",
                },
            ),
            # T5.4: Missing asset paths
            (
                r"FileNotFoundError.*['\"]([^'\"]+\.(png|jpg|jpeg|gif|mp4|mov|svg))['\"]",
                "asset_missing",
                lambda m: {
                    "message": f"Asset file not found: {m.group(1)}",
                    "path": m.group(1),
                    "hint": f"Ensure asset file exists at path: {m.group(1)}",
                },
            ),
            (
                r"No such file or directory: ['\"]([^'\"]+\.(png|jpg|jpeg|gif|mp4|mov|svg))['\"]",
                "asset_missing",
                lambda m: {
                    "message": f"Missing asset: {m.group(1)}",
                    "path": m.group(1),
                    "hint": "Check asset path and file permissions",
                },
            ),
            (
                r"Cannot load image .+['\"]([^'\"]+)['\"]",
                "asset_missing",
                lambda m: {
                    "message": f"Cannot load image: {m.group(1)}",
                    "path": m.group(1),
                    "hint": "Verify image format and accessibility",
                },
            ),
            # T5.4: Scene class not found
            (
                r"No scene named ['\"](.+)['\"] found",
                "class_missing",
                lambda m: {
                    "message": f"Scene class not found: {m.group(1)}",
                    "class_name": m.group(1),
                    "hint": f"Ensure class '{m.group(1)}' exists and inherits from Scene",
                },
            ),
            (
                r"Scene .+ not found",
                "class_missing",
                lambda m: {
                    "message": f"Scene class missing: {m.group(0)}",
                    "class_name": "",
                    "hint": "Check scene class name and definition",
                },
            ),
            (
                r"AttributeError: module .+ has no attribute ['\"](.+)['\"]",
                "class_missing",
                lambda m: {
                    "message": f"Class or function not found: {m.group(1)}",
                    "class_name": m.group(1),
                    "hint": f"Check if '{m.group(1)}' is properly defined",
                },
            ),
            # T5.4: Python exceptions with enhanced context
            (
                r"NameError: name ['\"](.+)['\"] is not defined",
                "python_error",
                lambda m: {
                    "message": f"Name not defined: {m.group(1)}",
                    "error_type": "NameError",
                    "hint": f"Define variable '{m.group(1)}' or check imports",
                },
            ),
            (
                r"(.+Error): (.+)",
                "python_error",
                lambda m: {
                    "message": f"{m.group(1)}: {m.group(2).strip()}",
                    "error_type": m.group(1),
                    "hint": "Check Python syntax and logic",
                },
            ),
            # Legacy/additional Manim-specific errors
            (
                r"ModuleNotFoundError: No module named '(.+)'",
                "python_error",
                lambda m: {
                    "message": f"Missing required module: {m.group(1)}",
                    "error_type": "ModuleNotFoundError",
                    "hint": f"Install or import module: {m.group(1)}",
                },
            ),
            # Attribute errors (enhanced for better context)
            (
                r"AttributeError: '(.+)' object has no attribute '(.+)'",
                "python_error",
                lambda m: {
                    "message": f"'{m.group(1)}' has no attribute '{m.group(2)}'",
                    "error_type": "AttributeError",
                    "hint": f"Check {m.group(1)} object methods or imports",
                },
            ),
            # FFmpeg/rendering errors
            (
                r"ffmpeg.*error.*",
                "rendering_error",
                lambda m: {
                    "message": "FFmpeg error during video generation",
                    "hint": "Check video encoding settings or ffmpeg installation",
                },
            ),
            # Timeout indicators
            (
                r".*(timeout|timed out).*",
                "timeout_error",
                lambda m: {
                    "message": "Operation timed out",
                    "hint": "Reduce scene complexity or increase timeout limit",
                },
            ),
        ]

        # Patterns for extracting line numbers
        self.line_number_patterns = [r"line (\d+)", r", line (\d+)", r"\.py:(\d+)"]

        # Warning patterns
        self.warning_patterns = [
            (r"Warning: (.+)", "warning", lambda m: {"message": m.group(1)}),
            (r"UserWarning: (.+)", "user_warning", lambda m: {"message": m.group(1)}),
        ]

    def parse_execution_logs(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
        cmd: str = "",
        duration_ms: float = 0.0,
        cpu_time_ms: float = 0.0,
        rss_peak_mb: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Enhanced T5.4 execution log parser.
        Parse execution logs and convert to typed structured issues.

        Args:
            stdout: Process stdout
            stderr: Process stderr
            exit_code: Process exit code
            cmd: Command string that was executed
            duration_ms: Total execution duration in milliseconds
            cpu_time_ms: CPU time used in milliseconds
            rss_peak_mb: Peak memory usage in MB

        Returns:
            List of typed issue dictionaries with T5.4 metadata
        """
        issues = []

        # Combine stdout and stderr for analysis
        combined_output = stdout + "\n" + stderr
        lines = combined_output.split("\n")

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check for error patterns
            error_issue = self._parse_error_line(line, i + 1)
            if error_issue:
                # T5.4: Add execution metadata to each issue
                error_issue.update(
                    {
                        "cmd": cmd,
                        "exit_code": exit_code,
                        "duration_ms": duration_ms,
                        "cpu_time_ms": cpu_time_ms,
                        "rss_peak_mb": rss_peak_mb,
                    }
                )
                issues.append(error_issue)
                continue

            # Check for warning patterns
            warning_issue = self._parse_warning_line(line, i + 1)
            if warning_issue:
                # T5.4: Add execution metadata to warnings too
                warning_issue.update(
                    {
                        "cmd": cmd,
                        "exit_code": exit_code,
                        "duration_ms": duration_ms,
                        "cpu_time_ms": cpu_time_ms,
                        "rss_peak_mb": rss_peak_mb,
                    }
                )
                issues.append(warning_issue)

        # If exit code indicates failure but no specific errors found
        if exit_code != 0 and not issues:
            issues.append(
                {
                    "type": "execution_failure",
                    "field": "exit_code",
                    "message": f"Process failed with exit code {exit_code}",
                    "value": exit_code,
                    "severity": "error",
                    "context": (
                        stderr[-200:] if stderr else stdout[-200:] if stdout else ""
                    ),
                    # T5.4: Include execution metadata
                    "cmd": cmd,
                    "exit_code": exit_code,
                    "duration_ms": duration_ms,
                    "cpu_time_ms": cpu_time_ms,
                    "rss_peak_mb": rss_peak_mb,
                    "hint": "Check command execution and process limits",
                }
            )

        return issues

    def _parse_error_line(
        self, line: str, line_number: int
    ) -> Optional[Dict[str, Any]]:
        """Enhanced T5.4 error line parser with typed issues."""
        for pattern, error_type, extract_func in self.error_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                extracted = extract_func(match)

                # Try to find source line number
                source_line = self._extract_line_number(line)

                # T5.4: Build structured issue with required fields
                issue = {
                    "type": error_type,  # This becomes "kind" for T5.4
                    "kind": error_type,  # Explicit T5.4 field
                    "field": (
                        f"source_line_{source_line}" if source_line else "execution"
                    ),
                    "message": extracted.get(
                        "message", "Unknown error"
                    ),  # T5.4 required
                    "hint": extracted.get(
                        "hint", "Review error context and fix"
                    ),  # T5.4 required
                    "value": extracted,
                    "severity": "error",
                    "context": line,
                    "log_line": line_number,
                }

                # Add source line if available (T5.4 "line if available")
                if source_line:
                    issue["line"] = source_line

                return issue

        return None

    def _parse_warning_line(
        self, line: str, line_number: int
    ) -> Optional[Dict[str, Any]]:
        """Enhanced T5.4 warning line parser."""
        for pattern, warning_type, extract_func in self.warning_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                extracted = extract_func(match)

                # T5.4: Structured warning with required fields
                return {
                    "type": warning_type,
                    "kind": warning_type,  # T5.4 explicit kind field
                    "field": "execution",
                    "message": extracted.get(
                        "message", "Warning occurred"
                    ),  # T5.4 required
                    "hint": "Review warning and consider fixing if needed",  # T5.4 required
                    "value": extracted,
                    "severity": "warning",
                    "context": line,
                    "log_line": line_number,
                }

        return None

    def _extract_line_number(self, line: str) -> Optional[int]:
        """Try to extract source code line number from error message."""
        for pattern in self.line_number_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None

    def summarize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of all issues."""
        if not issues:
            return {
                "total_issues": 0,
                "errors": 0,
                "warnings": 0,
                "summary": "No issues found",
            }

        error_count = sum(1 for issue in issues if issue.get("severity") == "error")
        warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")

        # Get most common error types
        error_types = {}
        for issue in issues:
            error_type = issue.get("type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Create summary message
        if error_count > 0:
            most_common = max(error_types.items(), key=lambda x: x[1])
            summary = f"Validation failed with {error_count} error(s), most common: {most_common[0]}"
        elif warning_count > 0:
            summary = f"Validation passed with {warning_count} warning(s)"
        else:
            summary = "Validation passed successfully"

        return {
            "total_issues": len(issues),
            "errors": error_count,
            "warnings": warning_count,
            "error_types": error_types,
            "summary": summary,
        }
