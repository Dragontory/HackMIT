"""
Normalization utilities for style pack values.

This module provides functions to normalize and validate style pack values
including colors, numeric ranges, font names, and other styling parameters.
"""

import re
from typing import Any, Dict, List, Union


class StyleNormalizationError(Exception):
    """Exception raised when style value normalization fails."""

    def __init__(self, field_path: str, value: Any, reason: str):
        self.field_path = field_path
        self.value = value
        self.reason = reason
        super().__init__(f"Error normalizing {field_path}: {reason} (got: {value})")


def normalize_hex_color(color: Union[str, Any], field_path: str = "") -> str:
    """
    Normalize and validate a hex color value.

    Args:
        color: Color value to normalize (expected to be string)
        field_path: Field path for error reporting

    Returns:
        Normalized hex color in uppercase format (#RRGGBB)

    Raises:
        StyleNormalizationError: If color is invalid
    """
    if not isinstance(color, str):
        raise StyleNormalizationError(field_path, color, "must be a string")

    # Remove whitespace
    color = color.strip()

    # Check basic format
    if not color.startswith("#"):
        raise StyleNormalizationError(field_path, color, "must start with #")

    hex_part = color[1:]

    # Check length
    if len(hex_part) != 6:
        raise StyleNormalizationError(
            field_path, color, "must be exactly 7 characters (#RRGGBB)"
        )

    # Check hex characters
    if not re.match(r"^[0-9A-Fa-f]{6}$", hex_part):
        raise StyleNormalizationError(
            field_path, color, "must contain only valid hex characters (0-9, A-F)"
        )

    # Return normalized uppercase version
    return f"#{hex_part.upper()}"


def normalize_font_list(
    fonts: Union[List[str], Any], field_path: str = ""
) -> List[str]:
    """
    Normalize and validate a list of font family names.

    Args:
        fonts: Font list to normalize
        field_path: Field path for error reporting

    Returns:
        Normalized list of font family names

    Raises:
        StyleNormalizationError: If font list is invalid
    """
    if not isinstance(fonts, list):
        raise StyleNormalizationError(field_path, fonts, "must be a list")

    if not fonts:
        raise StyleNormalizationError(field_path, fonts, "cannot be empty")

    if len(fonts) > 5:
        raise StyleNormalizationError(
            field_path, fonts, "cannot have more than 5 font fallbacks"
        )

    normalized_fonts = []
    for i, font in enumerate(fonts):
        if not isinstance(font, str):
            raise StyleNormalizationError(
                f"{field_path}[{i}]", font, "must be a string"
            )

        # Normalize font name: strip whitespace, validate not empty
        normalized_font = font.strip()
        if not normalized_font:
            raise StyleNormalizationError(
                f"{field_path}[{i}]", font, "cannot be empty or whitespace-only"
            )

        if len(normalized_font) > 50:
            raise StyleNormalizationError(
                f"{field_path}[{i}]", font, "font name too long (max 50 characters)"
            )

        normalized_fonts.append(normalized_font)

    return normalized_fonts


def normalize_scale_factor(
    scale: Union[float, int, Any],
    field_path: str = "",
    min_val: float = 0.4,
    max_val: float = 2.0,
) -> float:
    """
    Normalize and validate a scale factor value.

    Args:
        scale: Scale value to normalize
        field_path: Field path for error reporting
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Normalized scale factor as float

    Raises:
        StyleNormalizationError: If scale is invalid
    """
    if not isinstance(scale, (int, float)):
        raise StyleNormalizationError(field_path, scale, "must be a number")

    scale = float(scale)

    if not min_val <= scale <= max_val:
        raise StyleNormalizationError(
            field_path, scale, f"must be between {min_val} and {max_val}"
        )

    return scale


def normalize_margin(margin: Union[float, int, Any], field_path: str = "") -> float:
    """
    Normalize and validate a margin value.

    Args:
        margin: Margin value to normalize
        field_path: Field path for error reporting

    Returns:
        Normalized margin as float

    Raises:
        StyleNormalizationError: If margin is invalid
    """
    if not isinstance(margin, (int, float)):
        raise StyleNormalizationError(field_path, margin, "must be a number")

    margin = float(margin)

    if not 0 <= margin <= 2.5:
        raise StyleNormalizationError(field_path, margin, "must be between 0 and 2.5")

    return margin


def normalize_range_array(
    range_array: Union[List[Union[int, float]], Any], field_path: str = ""
) -> List[float]:
    """
    Normalize and validate a range array [min, max, step].

    Args:
        range_array: Range array to normalize
        field_path: Field path for error reporting

    Returns:
        Normalized range as [float, float, float]

    Raises:
        StyleNormalizationError: If range is invalid
    """
    if not isinstance(range_array, list):
        raise StyleNormalizationError(field_path, range_array, "must be a list")

    if len(range_array) != 3:
        raise StyleNormalizationError(
            field_path, range_array, "must have exactly 3 values [min, max, step]"
        )

    try:
        min_val, max_val, step = [float(x) for x in range_array]
    except (ValueError, TypeError):
        raise StyleNormalizationError(
            field_path, range_array, "all values must be numbers"
        )

    if min_val >= max_val:
        raise StyleNormalizationError(
            field_path,
            range_array,
            f"min ({min_val}) must be less than max ({max_val})",
        )

    if step <= 0:
        raise StyleNormalizationError(
            field_path, range_array, f"step must be positive (got {step})"
        )

    return [min_val, max_val, step]


def normalize_angle(
    angle: Union[float, int, Any],
    field_path: str = "",
    min_val: float = -90,
    max_val: float = 360,
) -> float:
    """
    Normalize and validate an angle value.

    Args:
        angle: Angle value to normalize
        field_path: Field path for error reporting
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Normalized angle as float

    Raises:
        StyleNormalizationError: If angle is invalid
    """
    if not isinstance(angle, (int, float)):
        raise StyleNormalizationError(field_path, angle, "must be a number")

    angle = float(angle)

    if not min_val <= angle <= max_val:
        raise StyleNormalizationError(
            field_path, angle, f"must be between {min_val} and {max_val} degrees"
        )

    return angle


def normalize_positive_number(
    value: Union[float, int, Any],
    field_path: str = "",
    min_val: float = 0.0,
    max_val: float = float("inf"),
) -> float:
    """
    Normalize and validate a positive number.

    Args:
        value: Value to normalize
        field_path: Field path for error reporting
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)

    Returns:
        Normalized value as float

    Raises:
        StyleNormalizationError: If value is invalid
    """
    if not isinstance(value, (int, float)):
        raise StyleNormalizationError(field_path, value, "must be a number")

    value = float(value)

    if not min_val <= value <= max_val:
        range_desc = (
            f"between {min_val} and {max_val}"
            if max_val != float("inf")
            else f"at least {min_val}"
        )
        raise StyleNormalizationError(field_path, value, f"must be {range_desc}")

    return value


def normalize_integer(
    value: Union[int, float, Any],
    field_path: str = "",
    min_val: int = 0,
    max_val: int = 1000,
) -> int:
    """
    Normalize and validate an integer value.

    Args:
        value: Value to normalize
        field_path: Field path for error reporting
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Normalized value as int

    Raises:
        StyleNormalizationError: If value is invalid
    """
    if not isinstance(value, (int, float)):
        raise StyleNormalizationError(field_path, value, "must be a number")

    # Check if it's effectively an integer
    if isinstance(value, float) and not value.is_integer():
        raise StyleNormalizationError(field_path, value, "must be a whole number")

    value = int(value)

    if not min_val <= value <= max_val:
        raise StyleNormalizationError(
            field_path, value, f"must be between {min_val} and {max_val}"
        )

    return value


def color_tuple(rgb_hex: str) -> tuple[int, int, int]:
    """
    Convert hex color to RGB tuple with values 0-255.

    Args:
        rgb_hex: Hex color string (e.g., "#FF0000" or "#2563EB")

    Returns:
        Tuple of (red, green, blue) values from 0-255

    Raises:
        ValueError: If hex color format is invalid
    """
    if not isinstance(rgb_hex, str):
        raise ValueError("Color must be a string")

    if not rgb_hex.startswith("#"):
        raise ValueError("Color must start with #")

    if len(rgb_hex) != 7:
        raise ValueError("Color must be exactly 7 characters (#RRGGBB)")

    hex_part = rgb_hex[1:]
    if not re.match(r"^[0-9A-Fa-f]{6}$", hex_part):
        raise ValueError("Color must contain only valid hex characters")

    # Convert hex to RGB
    r = int(hex_part[0:2], 16)
    g = int(hex_part[2:4], 16)
    b = int(hex_part[4:6], 16)

    return (r, g, b)


def apply_defaults_to_dict(
    data: Dict[str, Any], defaults: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply default values to a dictionary, merging nested dictionaries.

    Args:
        data: Original data dictionary
        defaults: Default values dictionary

    Returns:
        Dictionary with defaults applied
    """
    result = defaults.copy()

    for key, value in data.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = apply_defaults_to_dict(value, result[key])
        else:
            # Override with provided value
            result[key] = value

    return result
