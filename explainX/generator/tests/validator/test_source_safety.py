"""
Tests for source code safety checks.
"""

from pathlib import Path

import pytest

from generator.validator.source_safety import (
    check_source_safety,
    validate_source_safety,
)
from generator.validator.errors import SourceSafetyError


class TestSourceSafety:
    """Test AST-based source code safety scanning."""

    def test_safe_manim_code_passes(self):
        """Safe Manim code should pass all safety checks."""
        safe_code = """
from manim import *
import numpy as np

class Scene_Test(Scene):
    def construct(self):
        title = Text("Safe Code", font=BODY_FONT).scale(0.9)
        self.play(Write(title))
        
        eq = MathTex(r"y = x^2").scale(0.95)
        self.play(Write(eq))
        
        self.wait(1.0)
"""

        issues = check_source_safety(safe_code)
        assert len(issues) == 0

    def test_disallowed_import_detected(self):
        """Disallowed imports should be detected."""
        unsafe_code = """
from manim import *
import os  # DISALLOWED
import sys  # DISALLOWED

class Scene_Test(Scene):
    def construct(self):
        pass
"""

        issues = check_source_safety(unsafe_code)

        # Should find at least 2 import issues
        import_issues = [
            i for i in issues if i["type"] in ["import_error", "safety_issue"]
        ]
        assert len(import_issues) >= 2

        # Check specific disallowed modules
        issue_messages = [i["message"] for i in issues]
        assert any("os" in msg for msg in issue_messages)
        assert any("sys" in msg for msg in issue_messages)

    def test_dangerous_function_calls_detected(self):
        """Dangerous function calls should be detected."""
        unsafe_code = """
from manim import *

class Scene_Test(Scene):
    def construct(self):
        result = eval("print('hello')")  # DANGEROUS
        exec("import os")  # DANGEROUS
        data = open("/etc/passwd").read()  # DANGEROUS
"""

        issues = check_source_safety(unsafe_code)

        # Should detect dangerous function calls
        dangerous_calls = [
            i
            for i in issues
            if i["type"] in ["safety_issue", "dangerous_pattern"]
            and any(func in i["message"].lower() for func in ["eval", "exec", "open"])
        ]
        assert len(dangerous_calls) >= 3

    def test_attribute_access_safety(self):
        """Dangerous attribute access should be detected."""
        unsafe_code = """
from manim import *

class Scene_Test(Scene):
    def construct(self):
        cls = self.__class__  # DANGEROUS
        module = self.__module__  # DANGEROUS
        builtins = __builtins__  # DANGEROUS
"""

        issues = check_source_safety(unsafe_code)

        # Should detect dangerous attribute access
        attr_issues = [
            i
            for i in issues
            if i["type"] == "safety_issue" and "attribute" in i["message"].lower()
        ]
        assert len(attr_issues) >= 1

    def test_complex_lambda_rejected(self):
        """Overly complex lambda expressions should be rejected."""
        complex_lambda_code = """
from manim import *
import numpy as np

class Scene_Test(Scene):
    def construct(self):
        axes = Axes()
        # Very complex lambda with many operations
        graph = axes.plot(
            lambda x: x**2 + np.sin(x) + np.cos(x) + np.tan(x) + 
                      np.log(abs(x)+1) + np.exp(-x) + x**3 + x**4 + 
                      np.sqrt(abs(x)) + np.arcsin(np.tanh(x))
        )
        self.play(Create(graph))
"""

        issues = check_source_safety(complex_lambda_code)

        # Should detect overly complex lambda
        lambda_issues = [
            i
            for i in issues
            if i["type"] == "safety_issue" and "lambda" in i["message"].lower()
        ]
        assert len(lambda_issues) >= 1

    def test_line_length_limits(self):
        """Lines exceeding length limits should generate warnings."""
        long_line_code = f"""
from manim import *

class Scene_Test(Scene):
    def construct(self):
        title = Text("{'A' * 300}", font=BODY_FONT).scale(0.9)  # Very long line
        self.play(Write(title))
"""

        issues = check_source_safety(long_line_code)

        # Should detect long line
        line_length_issues = [i for i in issues if i["type"] == "line_length_exceeded"]
        assert len(line_length_issues) >= 1
        assert line_length_issues[0]["severity"] == "warning"

    def test_total_line_count_limits(self):
        """Files with too many lines should be rejected."""
        many_lines = "\n".join(
            [f"# Line {i}" for i in range(600)]
        )  # Exceeds MAX_TOTAL_LINES
        long_file_code = f"""
from manim import *

class Scene_Test(Scene):
    def construct(self):
{many_lines}
        pass
"""

        issues = check_source_safety(long_file_code)

        # Should detect excessive line count
        line_count_issues = [i for i in issues if i["type"] == "line_count_exceeded"]
        assert len(line_count_issues) >= 1
        assert line_count_issues[0]["severity"] == "error"

    def test_syntax_error_handling(self):
        """Syntax errors should be caught and reported."""
        syntax_error_code = """
from manim import *

class Scene_Test(Scene):
    def construct(self):
        title = Text("Missing quote, font=BODY_FONT)  # Missing opening quote
        self.play(Write(title))
"""

        issues = check_source_safety(syntax_error_code)

        # Should detect syntax error
        syntax_issues = [i for i in issues if i["type"] == "syntax_error"]
        assert len(syntax_issues) >= 1
        assert syntax_issues[0]["severity"] == "error"

    def test_test_data_files_safety(self):
        """Test our test data files for expected safety results."""
        test_data_dir = Path(__file__).parent / "data"

        # Test good_scene.py - should pass
        good_scene = (test_data_dir / "good_scene.py").read_text()
        good_issues = check_source_safety(good_scene)
        assert len([i for i in good_issues if i["severity"] == "error"]) == 0

        # Test bad_import.py - should fail with import issues
        bad_import = (test_data_dir / "bad_import.py").read_text()
        bad_issues = check_source_safety(bad_import)
        error_issues = [i for i in bad_issues if i["severity"] == "error"]
        assert len(error_issues) >= 1

        # Should specifically catch os, sys, subprocess imports
        import_error_messages = [i["message"] for i in error_issues]
        assert any("os" in msg for msg in import_error_messages)

    def test_unknown_import_handling(self):
        """Unknown but not explicitly disallowed imports should be flagged."""
        unknown_import_code = """
from manim import *
import unknown_module  # Not in ALLOWED_IMPORTS or DISALLOWED_IMPORTS

class Scene_Test(Scene):
    def construct(self):
        pass
"""

        issues = check_source_safety(unknown_import_code)

        # Should flag unknown import
        unknown_issues = [i for i in issues if "unknown_module" in i["message"]]
        assert len(unknown_issues) >= 1

    def test_path_traversal_detection(self):
        """Path traversal attempts should be detected."""
        traversal_code = """
from manim import *

class Scene_Test(Scene):
    def construct(self):
        # Various path traversal attempts in strings
        data1 = "../../../etc/passwd"
        data2 = "~/sensitive/file"
        data3 = "/etc/shadow"
        data4 = "/tmp/dangerous"
        data5 = "/proc/version"
"""

        issues = check_source_safety(traversal_code)

        # Should detect path traversal patterns
        path_issues = [
            i
            for i in issues
            if i["type"] == "dangerous_pattern"
            and any(
                pattern in i["message"].lower()
                for pattern in ["path", "directory", "traversal", "access"]
            )
        ]
        assert len(path_issues) >= 3  # Should catch ../, /etc/, /proc/ etc.

    def test_validate_source_safety_raises_error(self):
        """validate_source_safety should raise SourceSafetyError for unsafe code."""
        unsafe_code = """
from manim import *
import os  # UNSAFE

class Scene_Test(Scene):
    def construct(self):
        os.getcwd()  # Should trigger error
"""

        with pytest.raises(SourceSafetyError) as exc_info:
            validate_source_safety(unsafe_code)

        assert exc_info.value.field is not None
        assert "os" in str(exc_info.value)

    def test_validate_source_safety_passes_safe_code(self):
        """validate_source_safety should pass safe code without exception."""
        safe_code = """
from manim import *
import numpy as np

class Scene_Test(Scene):
    def construct(self):
        title = Text("Safe Code", font=BODY_FONT).scale(0.9)
        self.play(Write(title))
        self.wait(1.0)
"""

        # Should not raise any exception
        try:
            validate_source_safety(safe_code)
        except SourceSafetyError:
            pytest.fail("validate_source_safety raised SourceSafetyError for safe code")

    def test_comprehensive_security_patterns(self):
        """Test detection of comprehensive security patterns."""
        malicious_code = """
from manim import *
import subprocess  # DISALLOWED
import pickle      # DISALLOWED

class Scene_Test(Scene):
    def construct(self):
        # File system access attempts
        result = open("/etc/passwd", "r")  # DANGEROUS
        
        # Code execution attempts  
        exec("import os; os.system('rm -rf /')")  # DANGEROUS
        eval("__import__('os').system('ls')")     # DANGEROUS
        
        # Path traversal
        path = "../../../sensitive/data"  # DANGEROUS
        
        # Attribute access to dangerous objects
        cls = self.__class__  # DANGEROUS
        module = self.__module__  # DANGEROUS
        
        # Network/system modules
        import socket  # DISALLOWED (if detected as import)
"""

        issues = check_source_safety(malicious_code)

        # Count different types of security violations
        error_issues = [i for i in issues if i.get("severity") == "error"]

        # Should detect multiple security issues
        assert len(error_issues) >= 5

        # Check for specific categories of issues
        issue_messages = [i["message"].lower() for i in error_issues]

        # Should detect import violations
        assert any("subprocess" in msg or "pickle" in msg for msg in issue_messages)

        # Should detect dangerous function calls
        assert any(
            "open" in msg or "eval" in msg or "exec" in msg for msg in issue_messages
        )

        # Should detect path traversal
        assert any("path" in msg or "../" in msg for msg in issue_messages)

    def test_lambda_complexity_enforcement(self):
        """Ensure lambda complexity limits are properly enforced."""
        # This should be within limits (simple lambda)
        simple_lambda_code = """
from manim import *
import numpy as np

class Scene_Test(Scene):
    def construct(self):
        axes = Axes()
        graph = axes.plot(lambda x: x**2 + 1)  # Simple, should pass
        self.play(Create(graph))
"""

        simple_issues = check_source_safety(simple_lambda_code)
        lambda_errors = [
            i for i in simple_issues if "lambda" in i.get("message", "").lower()
        ]
        assert len(lambda_errors) == 0

        # This should exceed limits (very complex lambda)
        complex_lambda_code = """
from manim import *
import numpy as np

class Scene_Test(Scene):
    def construct(self):
        axes = Axes()
        # Extremely complex lambda with many operations
        graph = axes.plot(
            lambda x: (x**2 + np.sin(x) + np.cos(x) + np.tan(x) + 
                      np.log(abs(x)+1) + np.exp(-x) + x**3 + x**4 + 
                      np.sqrt(abs(x)) + np.arcsin(np.tanh(x)) +
                      x**5 + x**6 + np.sinh(x) + np.cosh(x))  # Way too many operations
        )
        self.play(Create(graph))
"""

        complex_issues = check_source_safety(complex_lambda_code)
        lambda_errors = [
            i
            for i in complex_issues
            if "lambda" in i.get("message", "").lower() and i.get("severity") == "error"
        ]
        assert len(lambda_errors) >= 1
