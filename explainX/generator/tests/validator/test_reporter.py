"""
Tests for error reporter and log parsing.
"""

import pytest

from generator.validator.reporter import ErrorReporter


class TestErrorReporter:
    """Test structured error reporting from execution logs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ErrorReporter()

    def test_parse_python_exception(self):
        """Should parse standard Python exceptions."""
        stderr = """
Traceback (most recent call last):
  File "scene.py", line 15, in construct
    title = Text("Hello", font=NONEXISTENT_FONT)
NameError: name 'NONEXISTENT_FONT' is not defined
"""

        issues = self.reporter.parse_execution_logs("", stderr, 1)

        assert len(issues) >= 1
        name_error = next((i for i in issues if i["type"] == "python_exception"), None)
        assert name_error is not None
        assert "NameError" in name_error["value"]["exception_type"]
        assert "NONEXISTENT_FONT" in name_error["message"]

    def test_parse_module_not_found(self):
        """Should parse ModuleNotFoundError with module name."""
        stderr = """
Traceback (most recent call last):
  File "scene.py", line 2, in <module>
    import nonexistent_module
ModuleNotFoundError: No module named 'nonexistent_module'
"""

        issues = self.reporter.parse_execution_logs("", stderr, 1)

        module_error = next((i for i in issues if i["type"] == "missing_module"), None)
        assert module_error is not None
        assert module_error["value"]["module"] == "nonexistent_module"
        assert "Missing required module" in module_error["message"]

    def test_parse_syntax_error(self):
        """Should parse syntax errors."""
        stderr = """
  File "scene.py", line 8
    title = Text("Hello World" font=BODY_FONT)
                           ^
SyntaxError: invalid syntax
"""

        issues = self.reporter.parse_execution_logs("", stderr, 1)

        syntax_error = next((i for i in issues if i["type"] == "syntax_error"), None)
        assert syntax_error is not None
        assert "Syntax error" in syntax_error["message"]
        assert "invalid syntax" in syntax_error["message"]

    def test_parse_import_error(self):
        """Should parse import errors."""
        stderr = """
Traceback (most recent call last):
  File "scene.py", line 3, in <module>
    from some_module import specific_function
ImportError: cannot import name 'specific_function' from 'some_module'
"""

        issues = self.reporter.parse_execution_logs("", stderr, 1)

        import_error = next((i for i in issues if i["type"] == "import_error"), None)
        assert import_error is not None
        assert "Import error" in import_error["message"]

    def test_parse_attribute_error(self):
        """Should parse attribute errors with object and attribute names."""
        stderr = """
Traceback (most recent call last):
  File "scene.py", line 12, in construct
    title.nonexistent_method()
AttributeError: 'Text' object has no attribute 'nonexistent_method'
"""

        issues = self.reporter.parse_execution_logs("", stderr, 1)

        attr_error = next((i for i in issues if i["type"] == "attribute_error"), None)
        assert attr_error is not None
        assert attr_error["value"]["object_type"] == "Text"
        assert attr_error["value"]["attribute"] == "nonexistent_method"
        assert "'Text' has no attribute 'nonexistent_method'" in attr_error["message"]

    def test_parse_type_error(self):
        """Should parse type errors."""
        stderr = """
Traceback (most recent call last):
  File "scene.py", line 10, in construct
    title.scale("invalid")
TypeError: unsupported operand type(s) for *: 'float' and 'str'
"""

        issues = self.reporter.parse_execution_logs("", stderr, 1)

        type_error = next((i for i in issues if i["type"] == "type_error"), None)
        assert type_error is not None
        assert "Type error" in type_error["message"]
        assert "unsupported operand type" in type_error["message"]

    def test_parse_value_error(self):
        """Should parse value errors."""
        stderr = """
Traceback (most recent call last):
  File "scene.py", line 14, in construct
    axes = Axes(x_range=[5, -5, 1])
ValueError: invalid range: min value greater than max value
"""

        issues = self.reporter.parse_execution_logs("", stderr, 1)

        value_error = next((i for i in issues if i["type"] == "value_error"), None)
        assert value_error is not None
        assert "Value error" in value_error["message"]
        assert "invalid range" in value_error["message"]

    def test_parse_ffmpeg_error(self):
        """Should detect FFmpeg-related errors."""
        stderr = """
[ffmpeg] Error: Failed to encode video
ffmpeg: error while opening codec for output stream
"""

        issues = self.reporter.parse_execution_logs("", stderr, 1)

        ffmpeg_error = next((i for i in issues if i["type"] == "ffmpeg_error"), None)
        assert ffmpeg_error is not None
        assert "FFmpeg error" in ffmpeg_error["message"]

    def test_parse_timeout_error(self):
        """Should detect timeout indicators."""
        stderr = "Process timed out after 30 seconds"

        issues = self.reporter.parse_execution_logs("", stderr, 1)

        timeout_error = next((i for i in issues if i["type"] == "timeout"), None)
        assert timeout_error is not None
        assert "timeout" in timeout_error["message"].lower()

    def test_parse_warnings(self):
        """Should parse warning messages."""
        stdout = """
Scene rendering started...
Warning: Low quality setting may produce pixelated output
UserWarning: Deprecated function used, please use new API
Rendering complete.
"""

        issues = self.reporter.parse_execution_logs(stdout, "", 0)

        warnings = [i for i in issues if i["severity"] == "warning"]
        assert len(warnings) >= 2

        # Check specific warning types
        warning_types = [w["type"] for w in warnings]
        assert "warning" in warning_types
        assert "user_warning" in warning_types

    def test_extract_line_numbers(self):
        """Should extract source line numbers when available."""
        stderr = """
Traceback (most recent call last):
  File "scene.py", line 25, in construct
    invalid_operation()
NameError: name 'invalid_operation' is not defined
"""

        issues = self.reporter.parse_execution_logs("", stderr, 1)

        error_with_line = next(
            (i for i in issues if "source_line_25" in i["field"]), None
        )
        assert error_with_line is not None

    def test_execution_failure_fallback(self):
        """Should report generic execution failure when no specific errors found."""
        stdout = "Some generic output without clear error patterns"
        stderr = "Some generic stderr without clear error patterns"

        issues = self.reporter.parse_execution_logs(stdout, stderr, 1)

        # Should have at least one execution failure issue
        exec_failures = [i for i in issues if i["type"] == "execution_failure"]
        assert len(exec_failures) >= 1
        assert exec_failures[0]["value"] == 1  # exit_code

    def test_successful_execution_no_issues(self):
        """Successful execution should produce no issues."""
        stdout = "Manim rendering complete successfully"
        stderr = ""

        issues = self.reporter.parse_execution_logs(stdout, stderr, 0)

        # Should have no error issues
        errors = [i for i in issues if i["severity"] == "error"]
        assert len(errors) == 0

    def test_summarize_issues(self):
        """Should create accurate issue summaries."""
        # Test with no issues
        no_issues_summary = self.reporter.summarize_issues([])
        assert no_issues_summary["total_issues"] == 0
        assert no_issues_summary["errors"] == 0
        assert no_issues_summary["warnings"] == 0
        assert "No issues found" in no_issues_summary["summary"]

        # Test with mixed issues
        mixed_issues = [
            {"type": "syntax_error", "severity": "error"},
            {"type": "syntax_error", "severity": "error"},
            {"type": "warning", "severity": "warning"},
            {"type": "type_error", "severity": "error"},
        ]

        mixed_summary = self.reporter.summarize_issues(mixed_issues)
        assert mixed_summary["total_issues"] == 4
        assert mixed_summary["errors"] == 3
        assert mixed_summary["warnings"] == 1
        assert mixed_summary["error_types"]["syntax_error"] == 2
        assert mixed_summary["error_types"]["type_error"] == 1
        assert "syntax_error" in mixed_summary["summary"]  # Most common

    def test_complex_error_parsing(self):
        """Should handle complex real-world error scenarios."""
        complex_stderr = """
Traceback (most recent call last):
  File "scene.py", line 8, in <module>
    from manim import *
  File "/path/to/manim/__init__.py", line 45, in <module>
    from .scene.scene import Scene
  File "/path/to/manim/scene/scene.py", line 12, in <module>
    import cairo
ModuleNotFoundError: No module named 'cairo'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "scene.py", line 15, in construct
    self.play(Write(title))
AttributeError: 'Scene_Test' object has no attribute 'play'
"""

        issues = self.reporter.parse_execution_logs("", complex_stderr, 1)

        # Should parse multiple errors
        assert len(issues) >= 2

        # Should find both ModuleNotFoundError and AttributeError
        error_types = [i["type"] for i in issues]
        assert "missing_module" in error_types
        assert "attribute_error" in error_types


class TestT54EnhancedReporter:
    """T5.4 specific tests for enhanced typed error reporting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ErrorReporter()

    def test_latex_error_detection(self):
        """T5.4: Test LaTeX compilation error detection with typed issues."""
        latex_errors = [
            "LaTeX Error: Missing \\begin{document}",
            "Package amsmath Error: Multiple \\label's: `eq:duplicate'",
            "! Undefined control sequence \\invalidcommand",
        ]

        for error_text in latex_errors:
            issues = self.reporter.parse_execution_logs(
                stdout="",
                stderr=error_text,
                exit_code=1,
                cmd="manim -q l test.py Scene_Test",
                duration_ms=5000.0,
                cpu_time_ms=4500.0,
                rss_peak_mb=128.0,
            )

            # Should detect latex_error type
            latex_issues = [i for i in issues if i.get("kind") == "latex_error"]
            assert len(latex_issues) >= 1, f"Failed to detect LaTeX error: {error_text}"

            # T5.4: Verify required fields
            issue = latex_issues[0]
            assert "message" in issue  # T5.4 required
            assert "hint" in issue  # T5.4 required
            assert "kind" in issue  # T5.4 required
            assert "snippet" in issue.get("value", {})  # T5.4: LaTeX snippet
            assert issue["cmd"] == "manim -q l test.py Scene_Test"  # T5.4: cmd string

    def test_asset_missing_detection(self):
        """T5.4: Test missing asset detection with path extraction."""
        asset_errors = [
            "FileNotFoundError: [Errno 2] No such file or directory: '/path/to/missing.png'",
            "No such file or directory: '/assets/logo.svg'",
            "Cannot load image from '/images/background.jpg'",
        ]

        for error_text in asset_errors:
            issues = self.reporter.parse_execution_logs(
                stdout="",
                stderr=error_text,
                exit_code=1,
                cmd="manim -q l test.py Scene_Test",
                duration_ms=3000.0,
            )

            # Should detect asset_missing type
            asset_issues = [i for i in issues if i.get("kind") == "asset_missing"]
            assert (
                len(asset_issues) >= 1
            ), f"Failed to detect missing asset: {error_text}"

            # T5.4: Verify required fields
            issue = asset_issues[0]
            assert "message" in issue
            assert "hint" in issue
            assert "path" in issue.get("value", {})  # T5.4: asset path

    def test_class_missing_detection(self):
        """T5.4: Test scene class not found detection."""
        class_errors = [
            "No scene named 'MissingScene' found",
            "AttributeError: module 'main' has no attribute 'InvalidScene'",
            "Scene InvalidClass not found in module",
        ]

        for error_text in class_errors:
            issues = self.reporter.parse_execution_logs(
                stdout="",
                stderr=error_text,
                exit_code=1,
                cmd="manim -q l main.py InvalidScene",
            )

            # Should detect class_missing type
            class_issues = [i for i in issues if i.get("kind") == "class_missing"]
            assert (
                len(class_issues) >= 1
            ), f"Failed to detect missing class: {error_text}"

            # T5.4: Verify required fields
            issue = class_issues[0]
            assert "message" in issue
            assert "hint" in issue

    def test_python_error_enhanced(self):
        """T5.4: Test enhanced python_error detection with error_type."""
        python_errors = [
            "NameError: name 'undefined_variable' is not defined",
            "TypeError: Text() missing 1 required positional argument: 'text'",
        ]

        for error_text in python_errors:
            issues = self.reporter.parse_execution_logs(
                stdout="",
                stderr=error_text + " (main.py, line 15)",  # Add line info
                exit_code=1,
                cmd="manim -q l main.py Scene_Test",
                rss_peak_mb=95.0,
            )

            # Should detect python_error type (enhanced patterns come first)
            python_issues = [i for i in issues if i.get("kind") == "python_error"]
            assert (
                len(python_issues) >= 1
            ), f"Failed to detect Python error: {error_text}"

            # T5.4: Verify required fields
            issue = python_issues[0]
            assert "message" in issue
            assert "hint" in issue
            assert "error_type" in issue.get("value", {})  # T5.4: error type
            assert "line" in issue  # T5.4: line if available

    def test_t54_execution_metadata(self):
        """T5.4: Test that all issues include execution metadata."""
        stderr = "SyntaxError: invalid syntax"

        issues = self.reporter.parse_execution_logs(
            stdout="Debug output",
            stderr=stderr,
            exit_code=1,
            cmd="manim -q l -r 854,480 main.py Scene_Test --output_dir artifacts",
            duration_ms=15000.0,
            cpu_time_ms=12000.0,
            rss_peak_mb=256.0,
        )

        assert len(issues) >= 1
        issue = issues[0]

        # T5.4: Verify all metadata fields are included
        assert (
            issue["cmd"]
            == "manim -q l -r 854,480 main.py Scene_Test --output_dir artifacts"
        )
        assert issue["exit_code"] == 1
        assert issue["duration_ms"] == 15000.0
        assert issue["cpu_time_ms"] == 12000.0
        assert issue["rss_peak_mb"] == 256.0

    def test_stable_short_messages(self):
        """T5.4: Test messages are stable and ready for repair agents."""
        test_cases = [
            ("LaTeX Error: Undefined control sequence", "latex_error"),
            ("FileNotFoundError: '/path/missing.png'", "asset_missing"),
            ("AttributeError: 'Scene' object has no attribute 'foo'", "python_error"),
            ("No scene named 'Test' found", "class_missing"),
        ]

        for error_text, expected_kind in test_cases:
            issues = self.reporter.parse_execution_logs("", error_text, 1)

            # Find issue of expected kind
            matching_issues = [i for i in issues if i.get("kind") == expected_kind]
            assert (
                len(matching_issues) >= 1
            ), f"Failed to detect {expected_kind}: {error_text}"

            issue = matching_issues[0]
            # T5.4: Messages should be stable, short, and informative
            assert len(issue["message"]) > 10  # Not too short
            assert len(issue["message"]) < 200  # Not too long
            assert expected_kind.replace("_", " ") in issue["message"].lower() or any(
                word in issue["message"].lower() for word in expected_kind.split("_")
            )  # Descriptive

    def test_comprehensive_mixed_errors(self):
        """T5.4: Test scenario with multiple error types in single execution."""
        complex_stderr = """
LaTeX Error: Missing $ inserted
FileNotFoundError: [Errno 2] No such file or directory: '/missing/asset.png'  
NameError: name 'invalid_var' is not defined (main.py, line 23)
No scene named 'WrongScene' found
Warning: Deprecated function usage
        """

        issues = self.reporter.parse_execution_logs(
            stdout="",
            stderr=complex_stderr,
            exit_code=1,
            cmd="manim -q l main.py WrongScene",
            duration_ms=8000.0,
            cpu_time_ms=7200.0,
            rss_peak_mb=180.0,
        )

        # Should detect all error types
        error_kinds = [i.get("kind") for i in issues if i.get("kind")]

        assert "latex_error" in error_kinds
        assert "asset_missing" in error_kinds
        assert "python_error" in error_kinds
        assert "class_missing" in error_kinds

        # Verify all have T5.4 required fields
        for issue in issues:
            if issue.get("severity") == "error":
                assert "kind" in issue
                assert "message" in issue
                assert "hint" in issue
                # All errors should have execution metadata
                assert "cmd" in issue
                assert "duration_ms" in issue

    def test_backwards_compatibility_maintained(self):
        """T5.4: Test enhanced reporter maintains backwards compatibility."""
        # Test old-style method call without metadata
        issues = self.reporter.parse_execution_logs("", "SyntaxError: test", 1)
        assert len(issues) >= 1

        # Should still have basic fields for backwards compatibility
        issue = issues[0]
        assert "type" in issue
        assert "message" in issue
        assert "severity" in issue

        # Enhanced fields should have defaults
        assert issue.get("cmd", "") == ""
        assert issue.get("duration_ms", 0.0) == 0.0
