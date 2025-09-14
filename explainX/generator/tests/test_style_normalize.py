"""
Tests for style pack normalization utilities.

This module tests the normalization functions for colors, fonts, scales,
and other style pack values.
"""

import pytest
import sys
from pathlib import Path

# Add the parent directories to the path
sys.path.append(str(Path(__file__).parent.parent))

from style.normalize import (
    StyleNormalizationError,
    normalize_hex_color,
    normalize_font_list,
    normalize_scale_factor,
    normalize_margin,
    normalize_range_array,
    normalize_angle,
    normalize_positive_number,
    normalize_integer,
    apply_defaults_to_dict,
)


class TestNormalizeHexColor:
    """Test cases for hex color normalization."""

    def test_valid_colors(self):
        """Test that valid hex colors are normalized properly."""
        test_cases = [
            ("#FF0000", "#FF0000"),  # Already uppercase
            ("#ff0000", "#FF0000"),  # Lowercase to uppercase
            ("#AbCdEf", "#ABCDEF"),  # Mixed case to uppercase
            ("#123456", "#123456"),  # Numbers
            ("#ffffff", "#FFFFFF"),  # All F's
            ("#000000", "#000000"),  # All zeros
        ]

        for input_color, expected in test_cases:
            result = normalize_hex_color(input_color, "test_field")
            assert (
                result == expected
            ), f"Expected {expected}, got {result} for input {input_color}"

    def test_invalid_colors(self):
        """Test that invalid hex colors raise appropriate errors."""
        invalid_cases = [
            ("blue", "must start with #"),
            ("FF0000", "must start with #"),
            ("#FF00", "must be exactly 7 characters"),
            ("#FF0000AA", "must be exactly 7 characters"),
            ("#GGHHII", "must contain only valid hex characters"),
            ("#FF00Z0", "must contain only valid hex characters"),
            (123, "must be a string"),
            (None, "must be a string"),
            ("", "must start with #"),
            ("#", "must be exactly 7 characters"),
            ("  #FF0000  ", "#FF0000"),  # Should handle whitespace
        ]

        for invalid_color, expected_error in invalid_cases:
            if expected_error.startswith("#"):
                # This is actually a valid case (whitespace handling)
                result = normalize_hex_color(invalid_color, "test_field")
                assert result == expected_error
            else:
                with pytest.raises(StyleNormalizationError) as exc_info:
                    normalize_hex_color(invalid_color, "test_field")
                assert expected_error in str(exc_info.value)


class TestNormalizeFontList:
    """Test cases for font list normalization."""

    def test_valid_font_lists(self):
        """Test that valid font lists are normalized properly."""
        test_cases = [
            (["Arial"], ["Arial"]),
            (["Arial", "Helvetica"], ["Arial", "Helvetica"]),
            (["  Inter  ", "Noto Sans"], ["Inter", "Noto Sans"]),  # Whitespace trimming
            (
                ["Inter", "Noto Sans", "DejaVu Sans", "Arial", "Helvetica"],
                ["Inter", "Noto Sans", "DejaVu Sans", "Arial", "Helvetica"],
            ),  # Max 5 fonts
        ]

        for input_fonts, expected in test_cases:
            result = normalize_font_list(input_fonts, "test_field")
            assert result == expected, f"Expected {expected}, got {result}"

    def test_invalid_font_lists(self):
        """Test that invalid font lists raise appropriate errors."""
        invalid_cases = [
            ([], "cannot be empty"),
            ("not_a_list", "must be a list"),
            (None, "must be a list"),
            ([123], "must be a string"),
            ([""], "cannot be empty or whitespace-only"),
            (["  "], "cannot be empty or whitespace-only"),
            (["Arial", "", "Helvetica"], "cannot be empty or whitespace-only"),
            (["A" * 51], "font name too long"),  # Over 50 characters
            (["Arial"] * 6, "cannot have more than 5 font fallbacks"),  # Over 5 fonts
        ]

        for invalid_fonts, expected_error in invalid_cases:
            with pytest.raises(StyleNormalizationError) as exc_info:
                normalize_font_list(invalid_fonts, "test_field")
            assert expected_error in str(exc_info.value)


class TestNormalizeScaleFactor:
    """Test cases for scale factor normalization."""

    def test_valid_scale_factors(self):
        """Test that valid scale factors are normalized properly."""
        test_cases = [
            (0.4, 0.4),  # Min value
            (2.0, 2.0),  # Max value
            (1.0, 1.0),  # Middle value
            (0.9, 0.9),  # Typical value
            (1, 1.0),  # Integer to float conversion
        ]

        for input_scale, expected in test_cases:
            result = normalize_scale_factor(input_scale, "test_field")
            assert result == expected, f"Expected {expected}, got {result}"

    def test_invalid_scale_factors(self):
        """Test that invalid scale factors raise appropriate errors."""
        invalid_cases = [
            (0.3, "must be between 0.4 and 2.0"),  # Too small
            (2.1, "must be between 0.4 and 2.0"),  # Too large
            ("not_a_number", "must be a number"),
            (None, "must be a number"),
        ]

        for invalid_scale, expected_error in invalid_cases:
            with pytest.raises(StyleNormalizationError) as exc_info:
                normalize_scale_factor(invalid_scale, "test_field")
            assert expected_error in str(exc_info.value)


class TestNormalizeMargin:
    """Test cases for margin normalization."""

    def test_valid_margins(self):
        """Test that valid margins are normalized properly."""
        test_cases = [
            (0.0, 0.0),  # Min value
            (2.5, 2.5),  # Max value
            (0.6, 0.6),  # Typical value
            (1, 1.0),  # Integer to float conversion
        ]

        for input_margin, expected in test_cases:
            result = normalize_margin(input_margin, "test_field")
            assert result == expected, f"Expected {expected}, got {result}"

    def test_invalid_margins(self):
        """Test that invalid margins raise appropriate errors."""
        invalid_cases = [
            (-0.1, "must be between 0 and 2.5"),  # Negative
            (2.6, "must be between 0 and 2.5"),  # Too large
            ("not_a_number", "must be a number"),
        ]

        for invalid_margin, expected_error in invalid_cases:
            with pytest.raises(StyleNormalizationError) as exc_info:
                normalize_margin(invalid_margin, "test_field")
            assert expected_error in str(exc_info.value)


class TestNormalizeRangeArray:
    """Test cases for range array normalization."""

    def test_valid_ranges(self):
        """Test that valid range arrays are normalized properly."""
        test_cases = [
            ([-3, 3, 1], [-3.0, 3.0, 1.0]),
            ([-5.5, 10.2, 0.5], [-5.5, 10.2, 0.5]),
            ([0, 100, 10], [0.0, 100.0, 10.0]),
        ]

        for input_range, expected in test_cases:
            result = normalize_range_array(input_range, "test_field")
            assert result == expected, f"Expected {expected}, got {result}"

    def test_invalid_ranges(self):
        """Test that invalid range arrays raise appropriate errors."""
        invalid_cases = [
            ("not_a_list", "must be a list"),
            ([1, 2], "must have exactly 3 values"),  # Too few values
            ([1, 2, 3, 4], "must have exactly 3 values"),  # Too many values
            ([5, 3, 1], "min (5.0) must be less than max (3.0)"),  # Min >= max
            ([1, 5, 0], "step must be positive"),  # Zero step
            ([1, 5, -1], "step must be positive"),  # Negative step
            (["not", "numbers", "here"], "all values must be numbers"),
        ]

        for invalid_range, expected_error in invalid_cases:
            with pytest.raises(StyleNormalizationError) as exc_info:
                normalize_range_array(invalid_range, "test_field")
            assert expected_error in str(exc_info.value)


class TestNormalizeAngle:
    """Test cases for angle normalization."""

    def test_valid_angles(self):
        """Test that valid angles are normalized properly."""
        test_cases = [
            (0, 0.0),  # Min for azimuth
            (360, 360.0),  # Max for azimuth
            (45, 45.0),  # Typical value
            (-90, -90.0),  # Min for elevation
            (90, 90.0),  # Max for elevation
        ]

        for input_angle, expected in test_cases:
            result = normalize_angle(input_angle, "test_field", -90, 360)
            assert result == expected, f"Expected {expected}, got {result}"

    def test_invalid_angles(self):
        """Test that invalid angles raise appropriate errors."""
        invalid_cases = [
            (-91, "must be between -90 and 360 degrees"),  # Too small
            (361, "must be between -90 and 360 degrees"),  # Too large
            ("not_a_number", "must be a number"),
        ]

        for invalid_angle, expected_error in invalid_cases:
            with pytest.raises(StyleNormalizationError) as exc_info:
                normalize_angle(invalid_angle, "test_field", -90, 360)
            assert expected_error in str(exc_info.value)


class TestNormalizeInteger:
    """Test cases for integer normalization."""

    def test_valid_integers(self):
        """Test that valid integers are normalized properly."""
        test_cases = [
            (50, 50),  # Min value
            (200, 200),  # Max value
            (120, 120),  # Typical value
            (100.0, 100),  # Float that's really an int
        ]

        for input_int, expected in test_cases:
            result = normalize_integer(input_int, "test_field", 50, 200)
            assert result == expected, f"Expected {expected}, got {result}"

    def test_invalid_integers(self):
        """Test that invalid integers raise appropriate errors."""
        invalid_cases = [
            (49, "must be between 50 and 200"),  # Too small
            (201, "must be between 50 and 200"),  # Too large
            (100.5, "must be a whole number"),  # Non-integer float
            ("not_a_number", "must be a number"),
        ]

        for invalid_int, expected_error in invalid_cases:
            with pytest.raises(StyleNormalizationError) as exc_info:
                normalize_integer(invalid_int, "test_field", 50, 200)
            assert expected_error in str(exc_info.value)


class TestApplyDefaultsToDict:
    """Test cases for applying defaults to dictionaries."""

    def test_simple_merge(self):
        """Test simple dictionary merging."""
        data = {"a": 1, "b": 2}
        defaults = {"b": 10, "c": 3}
        result = apply_defaults_to_dict(data, defaults)
        expected = {"a": 1, "b": 2, "c": 3}  # data overrides defaults
        assert result == expected

    def test_nested_merge(self):
        """Test nested dictionary merging."""
        data = {"colors": {"primary": "#FF0000"}, "layout": {"margins": {"top": 1.0}}}
        defaults = {
            "colors": {"primary": "#000000", "secondary": "#CCCCCC"},
            "layout": {"margins": {"top": 0.5, "left": 0.7}, "position": "center"},
        }
        result = apply_defaults_to_dict(data, defaults)
        expected = {
            "colors": {"primary": "#FF0000", "secondary": "#CCCCCC"},
            "layout": {"margins": {"top": 1.0, "left": 0.7}, "position": "center"},
        }
        assert result == expected

    def test_empty_data(self):
        """Test merging with empty data dictionary."""
        data = {}
        defaults = {"a": 1, "b": {"c": 2}}
        result = apply_defaults_to_dict(data, defaults)
        assert result == defaults

    def test_empty_defaults(self):
        """Test merging with empty defaults dictionary."""
        data = {"a": 1, "b": {"c": 2}}
        defaults = {}
        result = apply_defaults_to_dict(data, defaults)
        assert result == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
