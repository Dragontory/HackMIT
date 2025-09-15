"""
AST scan and disallowed patterns for generated Python source safety.
"""

import ast
import re
from typing import List, Set

from .errors import SafetyIssue, SourceSafetyError


# Disallowed imports - anything beyond manim and basic math
DISALLOWED_IMPORTS = {
    "os",
    "sys",
    "subprocess",
    "eval",
    "exec",
    "compile",
    "open",
    "file",
    "__import__",
    "input",
    "raw_input",
    "socket",
    "urllib",
    "requests",
    "http",
    "ftplib",
    "smtplib",
    "pickle",
    "marshal",
    "shelve",
    "dbm",
}

# Allowed imports for Manim scenes
ALLOWED_IMPORTS = {"manim", "numpy", "math", "cmath", "random", "typing"}

# Disallowed function calls
DISALLOWED_FUNCTIONS = {
    "eval",
    "exec",
    "compile",
    "open",
    "file",
    "input",
    "raw_input",
    "__import__",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
    "globals",
    "locals",
    "vars",
}

# Disallowed attributes - prevent access to dangerous internals
DISALLOWED_ATTRIBUTES = {
    "__class__",
    "__bases__",
    "__dict__",
    "__doc__",
    "__module__",
    "__file__",
    "__builtins__",
}

# Maximum allowed line length and total lines
MAX_LINE_LENGTH = 200
MAX_TOTAL_LINES = 500

# Maximum lambda complexity (number of operations)
MAX_LAMBDA_OPS = 10


def check_source_safety(source_text: str) -> List[dict]:
    """
    Scan Python source for unsafe patterns using AST analysis.
    Returns list of safety issues as dicts.
    """
    issues = []

    try:
        # Parse the source code
        tree = ast.parse(source_text)
    except SyntaxError as e:
        issues.append(
            {
                "type": "syntax_error",
                "field": f"source_line_{e.lineno}",
                "message": f"Syntax error: {e.msg}",
                "value": e.text,
                "severity": "error",
            }
        )
        return issues

    # Basic line-level checks
    lines = source_text.split("\n")
    issues.extend(_check_line_safety(lines))

    # AST-based checks
    visitor = SafetyVisitor()
    visitor.visit(tree)

    for safety_issue in visitor.issues:
        issues.append(safety_issue.to_validation_issue().to_dict())

    return issues


def validate_source_safety(source_text: str) -> None:
    """
    Validate source code safety and raise SourceSafetyError if issues found.
    This is the main validation function that should be used in the pipeline.
    """
    issues = check_source_safety(source_text)

    # Filter for only error-level issues
    error_issues = [i for i in issues if i.get("severity") == "error"]

    if error_issues:
        # Raise SourceSafetyError with the first critical issue
        first_error = error_issues[0]
        raise SourceSafetyError(
            field=first_error.get("field", "source"),
            message=first_error.get("message", "Source code safety violation"),
            value=first_error.get("value"),
        )


def _check_line_safety(lines: List[str]) -> List[dict]:
    """Check individual lines for safety issues."""
    issues = []

    # Check total line count
    if len(lines) > MAX_TOTAL_LINES:
        issues.append(
            {
                "type": "line_count_exceeded",
                "field": "source_total_lines",
                "message": f"Source has {len(lines)} lines, exceeding maximum {MAX_TOTAL_LINES}",
                "value": len(lines),
                "severity": "error",
            }
        )

    for i, line in enumerate(lines, 1):
        # Check line length
        if len(line) > MAX_LINE_LENGTH:
            issues.append(
                {
                    "type": "line_length_exceeded",
                    "field": f"source_line_{i}",
                    "message": f"Line length {len(line)} exceeds maximum {MAX_LINE_LENGTH}",
                    "value": line[:100] + "..." if len(line) > 100 else line,
                    "severity": "warning",
                }
            )

        # Check for dangerous string patterns
        dangerous_patterns = [
            (r"__.*__", "Dunder method access"),
            (r"eval\s*\(", "eval() call"),
            (r"exec\s*\(", "exec() call"),
            (r"open\s*\(", "file open() call"),
            (r"import\s+os", "os module import"),
            (r"import\s+sys", "sys module import"),
            (r"subprocess", "subprocess usage"),
            (r"\.\./", "Path traversal attempt with ../"),
            (r"~\/", "Home directory access attempt"),
            (r"\/etc\/", "System directory access"),
            (r"\/tmp\/", "Temp directory access"),
            (r"\/proc\/", "Process directory access"),
        ]

        for pattern, message in dangerous_patterns:
            if re.search(pattern, line):
                issues.append(
                    {
                        "type": "dangerous_pattern",
                        "field": f"source_line_{i}",
                        "message": message,
                        "value": line.strip(),
                        "severity": "error",
                    }
                )

    return issues


class SafetyVisitor(ast.NodeVisitor):
    """AST visitor to check for unsafe code patterns."""

    def __init__(self):
        self.issues: List[SafetyIssue] = []
        self.current_line = 1

    def visit_Import(self, node):
        """Check import statements."""
        self.current_line = node.lineno

        for alias in node.names:
            module_name = alias.name.split(".")[0]  # Get top-level module

            if module_name in DISALLOWED_IMPORTS:
                self.issues.append(
                    SafetyIssue(
                        pattern=f"import {alias.name}",
                        line_number=node.lineno,
                        context=f"import {alias.name}",
                        message=f"Import of '{module_name}' is not allowed",
                    )
                )
            elif module_name not in ALLOWED_IMPORTS:
                self.issues.append(
                    SafetyIssue(
                        pattern=f"import {alias.name}",
                        line_number=node.lineno,
                        context=f"import {alias.name}",
                        message=f"Unknown import '{module_name}' - only {ALLOWED_IMPORTS} are allowed",
                    )
                )

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Check from X import Y statements."""
        self.current_line = node.lineno

        if node.module:
            module_name = node.module.split(".")[0]

            if module_name in DISALLOWED_IMPORTS:
                self.issues.append(
                    SafetyIssue(
                        pattern=f"from {node.module} import ...",
                        line_number=node.lineno,
                        context=f"from {node.module} import ...",
                        message=f"Import from '{module_name}' is not allowed",
                    )
                )
            elif module_name not in ALLOWED_IMPORTS:
                self.issues.append(
                    SafetyIssue(
                        pattern=f"from {node.module} import ...",
                        line_number=node.lineno,
                        context=f"from {node.module} import ...",
                        message=f"Unknown module '{module_name}' - only {ALLOWED_IMPORTS} are allowed",
                    )
                )

        self.generic_visit(node)

    def visit_Call(self, node):
        """Check function calls."""
        self.current_line = node.lineno

        # Check direct function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in DISALLOWED_FUNCTIONS:
                self.issues.append(
                    SafetyIssue(
                        pattern=f"{func_name}()",
                        line_number=node.lineno,
                        context=f"Function call: {func_name}()",
                        message=f"Function '{func_name}' is not allowed",
                    )
                )

        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Check attribute access."""
        self.current_line = node.lineno

        if node.attr in DISALLOWED_ATTRIBUTES:
            self.issues.append(
                SafetyIssue(
                    pattern=f"*.{node.attr}",
                    line_number=node.lineno,
                    context=f"Attribute access: {node.attr}",
                    message=f"Access to attribute '{node.attr}' is not allowed",
                )
            )

        self.generic_visit(node)

    def visit_Lambda(self, node):
        """Check lambda expressions for complexity."""
        self.current_line = node.lineno

        # Count operations in lambda body
        op_counter = OperationCounter()
        op_counter.visit(node.body)

        if op_counter.count > MAX_LAMBDA_OPS:
            self.issues.append(
                SafetyIssue(
                    pattern="lambda",
                    line_number=node.lineno,
                    context=f"Lambda with {op_counter.count} operations",
                    message=f"Lambda too complex: {op_counter.count} operations exceeds maximum {MAX_LAMBDA_OPS}",
                )
            )

        self.generic_visit(node)


class OperationCounter(ast.NodeVisitor):
    """Count operations in AST nodes."""

    def __init__(self):
        self.count = 0

    def visit_BinOp(self, node):
        """Binary operations: +, -, *, /, etc."""
        self.count += 1
        self.generic_visit(node)

    def visit_UnaryOp(self, node):
        """Unary operations: -, not, ~"""
        self.count += 1
        self.generic_visit(node)

    def visit_Compare(self, node):
        """Comparison operations: ==, <, >, etc."""
        self.count += 1
        self.generic_visit(node)

    def visit_Call(self, node):
        """Function calls."""
        self.count += 1
        self.generic_visit(node)

    def visit_Subscript(self, node):
        """Array/dict subscripts: a[b]"""
        self.count += 1
        self.generic_visit(node)
