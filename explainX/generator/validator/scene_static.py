"""
Static validation of scene JSON and style packs (T5.1).

Re-runs T1 schema validation and performs additional content checks.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, TYPE_CHECKING

import jsonschema

if TYPE_CHECKING:
    from generator.style.models import StylePack

from .errors import ValidationError, ContentLengthError, StyleBoundsError, RangeError


def validate_scene_json(scene_json: dict) -> None:
    """
    Re-run T1 schema validation on scene_json to catch any accidental drift.
    Also perform additional content checks.
    """
    # Step 1: Schema validation using T1 schema
    schema_path = Path(__file__).parent.parent / "compiler" / "schema.json"

    if not schema_path.exists():
        raise ValidationError(
            "schema", "Scene DSL schema file not found", str(schema_path)
        )

    with open(schema_path) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(scene_json, schema)
    except jsonschema.ValidationError as e:
        field_path = _get_field_path(e)
        raise ValidationError(field_path, str(e.message), e.instance)
    except jsonschema.SchemaError as e:
        raise ValidationError("schema", f"Invalid schema: {e.message}")

    # Step 2: Content-specific validation
    _validate_content_lengths(scene_json)
    _validate_asset_references(scene_json)
    _validate_ranges(scene_json)


def validate_style_pack(style_pack: "StylePack") -> None:
    """
    Style checks:
    - Required colors exist
    - Scales within bounds
    - Graph ranges coherent (min < max, step > 0)
    """
    # Check required colors exist
    required_colors = ["primary_text", "background", "accent"]
    for color_name in required_colors:
        color_value = getattr(style_pack.colors, color_name, None)
        if not color_value:
            raise ValidationError(
                f"colors.{color_name}", "Required color is missing", color_value
            )

        if not _is_valid_color(color_value):
            raise ValidationError(
                f"colors.{color_name}", "Invalid color format", color_value
            )

    # Check scales within bounds
    if hasattr(style_pack, "text_scale"):
        _check_scale_bounds("text_scale", style_pack.text_scale)

    if hasattr(style_pack, "title_scale"):
        _check_scale_bounds("title_scale", style_pack.title_scale)

    if hasattr(style_pack, "eq_scale"):
        _check_scale_bounds("eq_scale", style_pack.eq_scale)


def _validate_content_lengths(scene_json: dict) -> None:
    """Check text and LaTeX lengths within caps."""
    MAX_TEXT_LENGTH = 500
    MAX_LATEX_LENGTH = 1000

    timeline = scene_json.get("timeline", [])

    for i, operation in enumerate(timeline):
        op_type = operation.get("op", "")

        # Check text operations
        if "text" in operation:
            text = operation["text"]
            if len(text) > MAX_TEXT_LENGTH:
                raise ContentLengthError(
                    f"timeline[{i}].text", len(text), MAX_TEXT_LENGTH, text
                )

        # Check LaTeX operations
        if "latex" in operation:
            latex = operation["latex"]
            if len(latex) > MAX_LATEX_LENGTH:
                raise ContentLengthError(
                    f"timeline[{i}].latex", len(latex), MAX_LATEX_LENGTH, latex
                )


def _validate_asset_references(scene_json: dict) -> None:
    """Ensure asset refs are sha256: format only."""
    SHA256_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")

    timeline = scene_json.get("timeline", [])

    for i, operation in enumerate(timeline):
        if "ref" in operation:
            asset_ref = operation["ref"]
            if not SHA256_PATTERN.match(asset_ref):
                raise ValidationError(
                    f"timeline[{i}].ref",
                    "Asset reference must be in format 'sha256:64-char-hex'",
                    asset_ref,
                )


def _validate_ranges(scene_json: dict) -> None:
    """Check that ranges are coherent (min < max)."""
    timeline = scene_json.get("timeline", [])

    for i, operation in enumerate(timeline):
        op_type = operation.get("op", "")

        # Check operations that use min/max ranges
        if op_type in ["graph2d", "axes2d", "surface3d", "vector3d"]:
            # Check x-axis range
            _check_param_range(operation, f"timeline[{i}]", "x_min", "x_max")
            # Check y-axis range
            _check_param_range(operation, f"timeline[{i}]", "y_min", "y_max")

            # Check z-axis range for 3D operations
            if op_type in ["surface3d", "vector3d"]:
                _check_param_range(operation, f"timeline[{i}]", "z_min", "z_max")


# _check_axis_range removed - schema uses separate min/max properties, not arrays


def _check_param_range(
    operation: dict, field_prefix: str, min_key: str, max_key: str
) -> None:
    """Check parameter range with separate min/max keys."""
    if min_key in operation and max_key in operation:
        min_val = operation[min_key]
        max_val = operation[max_key]

        if min_val >= max_val:
            raise RangeError(f"{field_prefix}.{min_key},{max_key}", min_val, max_val)


def _check_scale_bounds(field_name: str, scale_value: float) -> None:
    """Check that scale values are within reasonable bounds."""
    MIN_SCALE = 0.1
    MAX_SCALE = 5.0

    if not (MIN_SCALE <= scale_value <= MAX_SCALE):
        raise StyleBoundsError(field_name, scale_value, MIN_SCALE, MAX_SCALE)


def _is_valid_color(color: str) -> bool:
    """Check if color is in valid hex format."""
    if not isinstance(color, str):
        return False

    # Check hex color format (#RRGGBB or #RGB)
    hex_pattern = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    return bool(hex_pattern.match(color))


def _get_field_path(validation_error: jsonschema.ValidationError) -> str:
    """Extract field path from jsonschema ValidationError."""
    if validation_error.absolute_path:
        path_parts = []
        for part in validation_error.absolute_path:
            if isinstance(part, int):
                path_parts[-1] += f"[{part}]"
            else:
                path_parts.append(str(part))
        return ".".join(path_parts)
    else:
        return "root"
