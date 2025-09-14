"""
Tests for style pack loading and validation.

This module tests the StyleLoader class and related functionality
for loading, validating, and merging style packs.
"""

import json
import pytest
import tempfile
import sys
from pathlib import Path

# Add the parent directories to the path
sys.path.append(str(Path(__file__).parent.parent))

from style.loader import (
    StyleLoader,
    StyleValidationError,
    load_style_pack,
    validate_style_dict,
)
from style.models import StylePack, TitlePosition


class TestStyleLoader:
    """Test cases for StyleLoader."""

    @pytest.fixture
    def loader(self):
        """Create a StyleLoader instance for testing."""
        return StyleLoader()

    @pytest.fixture
    def valid_minimal_style(self):
        """Minimal valid style pack data."""
        return {
            "version": "1.0",
            "name": "test_style",
            "colors": {
                "primary_text": "#111111",
                "accent": "#2563EB",
                "background": "#FFFFFF",
            },
        }

    @pytest.fixture
    def valid_complete_style(self):
        """Complete valid style pack data."""
        return {
            "version": "1.0",
            "name": "complete_test",
            "description": "Complete test style pack",
            "typography": {
                "title_font": ["Inter", "Arial"],
                "body_font": ["Inter", "Arial"],
                "math_font": ["Computer Modern"],
                "title_scale": 0.9,
                "subtitle_scale": 0.7,
                "text_scale": 0.8,
                "eq_scale": 0.95,
            },
            "colors": {
                "primary_text": "#111111",
                "secondary_text": "#374151",
                "accent": "#2563EB",
                "background": "#FFFFFF",
                "highlight": "#F59E0B",
                "warning": "#DC2626",
                "success": "#16A34A",
                "grid": "#9CA3AF",
            },
            "layout": {
                "margins": {"top": 0.6, "right": 0.6, "bottom": 0.6, "left": 0.7},
                "title_position": "top",
                "max_line_length_chars": 120,
                "bullet_leading": 0.5,
            },
            "graph_defaults": {
                "axes": {
                    "include_numbers": False,
                    "stroke_width": 2.0,
                    "color": "#111111",
                },
                "x_range": [-3, 3, 1],
                "y_range": [-1, 9, 1],
            },
            "camera3d": {"elevation": 45.0, "azimuth": 45.0, "distance": 6.0},
            "animations": {"default_wait_s": 0.2, "write_speed": 1.0},
        }

    def test_valid_minimal_style_loading(self, loader, valid_minimal_style):
        """Test loading a minimal valid style pack."""
        style_pack = loader.load_from_dict(valid_minimal_style)

        # Check required fields
        assert style_pack.version == "1.0"
        assert style_pack.name == "test_style"
        assert style_pack.colors.primary_text == "#111111"
        assert style_pack.colors.accent == "#2563EB"
        assert style_pack.colors.background == "#FFFFFF"

        # Check defaults are applied
        assert style_pack.typography.title_scale == 0.9
        assert style_pack.layout.title_position == TitlePosition.TOP
        assert style_pack.animations.default_wait_s == 0.2

    def test_valid_complete_style_loading(self, loader, valid_complete_style):
        """Test loading a complete valid style pack."""
        style_pack = loader.load_from_dict(valid_complete_style)

        # Check all fields are properly loaded
        assert style_pack.version == "1.0"
        assert style_pack.name == "complete_test"
        assert style_pack.description == "Complete test style pack"

        # Typography
        assert style_pack.typography.title_font == ["Inter", "Arial"]
        assert style_pack.typography.title_scale == 0.9

        # Colors (normalized to uppercase)
        assert style_pack.colors.primary_text == "#111111"
        assert style_pack.colors.secondary_text == "#374151"

        # Layout
        assert style_pack.layout.margins.top == 0.6
        assert style_pack.layout.title_position == TitlePosition.TOP

        # Graph defaults
        assert style_pack.graph_defaults.x_range == [-3.0, 3.0, 1.0]
        assert not style_pack.graph_defaults.axes.include_numbers

    def test_schema_validation_errors(self, loader):
        """Test that schema validation catches errors."""
        invalid_cases = [
            # Missing required version
            (
                {
                    "name": "test",
                    "colors": {
                        "primary_text": "#111111",
                        "accent": "#222222",
                        "background": "#FFFFFF",
                    },
                },
                "version",
            ),
            # Missing required name
            (
                {
                    "version": "1.0",
                    "colors": {
                        "primary_text": "#111111",
                        "accent": "#222222",
                        "background": "#FFFFFF",
                    },
                },
                "name",
            ),
            # Missing required colors
            ({"version": "1.0", "name": "test"}, "colors"),
            # Missing required color fields
            (
                {
                    "version": "1.0",
                    "name": "test",
                    "colors": {"primary_text": "#111111"},
                },
                "background",
            ),  # background is required and will be caught first
            # Invalid version format
            (
                {
                    "version": "not.a.version",
                    "name": "test",
                    "colors": {
                        "primary_text": "#111111",
                        "accent": "#222222",
                        "background": "#FFFFFF",
                    },
                },
                "version",
            ),
        ]

        for invalid_style, expected_error_field in invalid_cases:
            with pytest.raises(StyleValidationError) as exc_info:
                loader.load_from_dict(invalid_style)
            error_msg = str(exc_info.value)
            assert expected_error_field in error_msg.lower()

    def test_color_normalization(self, loader):
        """Test that colors are properly normalized."""
        style_data = {
            "version": "1.0",
            "name": "color_test",
            "colors": {
                "primary_text": "#ff0000",  # Lowercase
                "accent": "#AbCdEf",  # Mixed case
                "background": "#FFFFFF",  # Already uppercase
            },
        }

        style_pack = loader.load_from_dict(style_data)

        # All colors should be normalized to uppercase
        assert style_pack.colors.primary_text == "#FF0000"
        assert style_pack.colors.accent == "#ABCDEF"
        assert style_pack.colors.background == "#FFFFFF"

    def test_invalid_color_format(self, loader):
        """Test that invalid color formats are rejected."""
        invalid_color_cases = [
            "blue",  # Not hex
            "FF0000",  # Missing #
            "#FF00",  # Too short
            "#FF0000AA",  # Too long
            "#GGHHII",  # Invalid hex chars
        ]

        for invalid_color in invalid_color_cases:
            style_data = {
                "version": "1.0",
                "name": "test",
                "colors": {
                    "primary_text": invalid_color,
                    "accent": "#2563EB",
                    "background": "#FFFFFF",
                },
            }

            with pytest.raises(StyleValidationError):
                loader.load_from_dict(style_data)

    def test_scale_factor_validation(self, loader):
        """Test that scale factors are validated."""
        # Valid scales
        valid_scales = [0.4, 1.0, 2.0, 0.9]
        for scale in valid_scales:
            style_data = {
                "version": "1.0",
                "name": "test",
                "typography": {"title_scale": scale},
                "colors": {
                    "primary_text": "#111111",
                    "accent": "#222222",
                    "background": "#FFFFFF",
                },
            }
            style_pack = loader.load_from_dict(style_data)
            assert style_pack.typography.title_scale == scale

        # Invalid scales
        invalid_scales = [0.3, 2.1, -1.0, 0.0]
        for scale in invalid_scales:
            style_data = {
                "version": "1.0",
                "name": "test",
                "typography": {"title_scale": scale},
                "colors": {
                    "primary_text": "#111111",
                    "accent": "#222222",
                    "background": "#FFFFFF",
                },
            }
            with pytest.raises(StyleValidationError):
                loader.load_from_dict(style_data)

    def test_font_list_validation(self, loader):
        """Test that font lists are validated."""
        # Valid font lists
        style_data = {
            "version": "1.0",
            "name": "test",
            "typography": {"title_font": ["Inter", "Arial", "Helvetica"]},
            "colors": {
                "primary_text": "#111111",
                "accent": "#222222",
                "background": "#FFFFFF",
            },
        }
        style_pack = loader.load_from_dict(style_data)
        assert style_pack.typography.title_font == ["Inter", "Arial", "Helvetica"]

        # Invalid font lists
        invalid_font_lists = [
            [],  # Empty list
            [""],  # Empty font name
            ["Arial"] * 6,  # Too many fonts
            ["A" * 51],  # Font name too long
        ]

        for invalid_fonts in invalid_font_lists:
            style_data = {
                "version": "1.0",
                "name": "test",
                "typography": {"title_font": invalid_fonts},
                "colors": {
                    "primary_text": "#111111",
                    "accent": "#222222",
                    "background": "#FFFFFF",
                },
            }
            with pytest.raises(StyleValidationError):
                loader.load_from_dict(style_data)

    def test_load_from_file(self, loader, valid_complete_style):
        """Test loading a style pack from a file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(valid_complete_style, f)
            temp_path = f.name

        try:
            style_pack = loader.load_from_file(temp_path)
            assert style_pack.name == "complete_test"
            assert style_pack.version == "1.0"
        finally:
            Path(temp_path).unlink()  # Clean up

    def test_load_from_nonexistent_file(self, loader):
        """Test loading from non-existent file raises appropriate error."""
        with pytest.raises(StyleValidationError) as exc_info:
            loader.load_from_file("nonexistent_file.json")
        assert "not found" in str(exc_info.value)

    def test_load_from_invalid_json_file(self, loader):
        """Test loading from invalid JSON file raises appropriate error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json content")
            temp_path = f.name

        try:
            with pytest.raises(StyleValidationError) as exc_info:
                loader.load_from_file(temp_path)
            assert "Invalid JSON" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_merge_styles(self, loader, valid_minimal_style):
        """Test merging styles with override values."""
        # Create a base style pack
        base_style = loader.load_from_dict(valid_minimal_style)

        # Override some values
        override_data = {
            "colors": {"accent": "#FF0000"},  # Change accent color
            "typography": {"title_scale": 1.2},  # Change title scale
        }

        merged_style = loader.merge_styles(base_style, override_data)

        # Check that overrides were applied
        assert merged_style.colors.accent == "#FF0000"
        assert merged_style.typography.title_scale == 1.2

        # Check that other values remain the same
        assert merged_style.colors.primary_text == "#111111"
        assert merged_style.name == "test_style"  # From base

    def test_convenience_functions(self, valid_minimal_style):
        """Test convenience functions work correctly."""
        # Test load_style_pack function
        style_pack = load_style_pack(valid_minimal_style)
        assert isinstance(style_pack, StylePack)
        assert style_pack.name == "test_style"

        # Test validate_style_dict function
        validate_style_dict(valid_minimal_style)  # Should not raise

        # Test invalid style validation
        invalid_style = {"invalid": "style"}
        with pytest.raises(StyleValidationError):
            validate_style_dict(invalid_style)


class TestRealWorldExamples:
    """Test with real-world style pack examples."""

    def test_edu_default_v1_sample(self):
        """Test loading the edu_default_v1 sample file."""
        samples_dir = Path(__file__).parent.parent / "style" / "samples"
        edu_default_path = samples_dir / "edu_default_v1.json"

        if edu_default_path.exists():
            style_pack = load_style_pack(edu_default_path)

            assert style_pack.name == "edu_default_v1"
            assert style_pack.version == "1.0"
            assert style_pack.colors.primary_text == "#111111"
            assert style_pack.typography.title_font == [
                "Inter",
                "Noto Sans",
                "DejaVu Sans",
            ]
            assert style_pack.layout.title_position == TitlePosition.TOP

    def test_dark_high_contrast_sample(self):
        """Test loading the dark_high_contrast sample file."""
        samples_dir = Path(__file__).parent.parent / "style" / "samples"
        dark_style_path = samples_dir / "dark_high_contrast.json"

        if dark_style_path.exists():
            style_pack = load_style_pack(dark_style_path)

            assert style_pack.name == "dark_high_contrast"
            assert style_pack.version == "1.0"
            assert (
                style_pack.colors.primary_text == "#FFFFFF"
            )  # White text for dark theme
            assert style_pack.colors.background == "#000000"  # Black background
            assert style_pack.typography.title_font == ["Roboto", "Arial", "Helvetica"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
