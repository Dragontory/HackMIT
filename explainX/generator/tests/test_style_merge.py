"""
Tests for style pack merging functionality.

This module tests the merging capabilities of the style pack system,
including base style overrides and complex nested merging scenarios.
"""

import pytest
import sys
from pathlib import Path

# Add the parent directories to the path
sys.path.append(str(Path(__file__).parent.parent))

from style.loader import StyleLoader, load_style_pack
from style.models import StylePack, TitlePosition


class TestStyleMerging:
    """Test cases for style pack merging functionality."""

    @pytest.fixture
    def loader(self):
        """Create a StyleLoader instance for testing."""
        return StyleLoader()

    @pytest.fixture
    def base_style_data(self):
        """Base style pack for merging tests."""
        return {
            "version": "1.0",
            "name": "base_style",
            "description": "Base style for testing",
            "typography": {
                "title_font": ["Arial", "Helvetica"],
                "body_font": ["Arial", "Helvetica"],
                "math_font": ["Computer Modern"],
                "title_scale": 1.0,
                "subtitle_scale": 0.8,
                "text_scale": 0.7,
                "eq_scale": 1.0,
            },
            "colors": {
                "primary_text": "#000000",
                "secondary_text": "#666666",
                "accent": "#0066CC",
                "background": "#FFFFFF",
                "highlight": "#FFFF00",
                "warning": "#FF0000",
                "success": "#00FF00",
                "grid": "#CCCCCC",
            },
            "layout": {
                "margins": {"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.0},
                "title_position": "center",
                "max_line_length_chars": 100,
                "bullet_leading": 0.4,
            },
            "graph_defaults": {
                "axes": {
                    "include_numbers": True,
                    "stroke_width": 1.5,
                    "color": "#000000",
                },
                "x_range": [-5, 5, 1],
                "y_range": [-2, 8, 1],
            },
            "camera3d": {"elevation": 30.0, "azimuth": 30.0, "distance": 8.0},
            "animations": {"default_wait_s": 0.3, "write_speed": 0.8},
        }

    @pytest.fixture
    def base_style_pack(self, loader, base_style_data):
        """Create a StylePack from base style data."""
        return loader.load_from_dict(base_style_data)

    def test_simple_color_override(self, loader, base_style_pack):
        """Test overriding a single color value."""
        override_data = {"colors": {"accent": "#FF00FF"}}  # Change accent to magenta

        merged_style = loader.merge_styles(base_style_pack, override_data)

        # Check that override was applied
        assert merged_style.colors.accent == "#FF00FF"

        # Check that other colors remain unchanged
        assert merged_style.colors.primary_text == "#000000"
        assert merged_style.colors.background == "#FFFFFF"
        assert merged_style.colors.warning == "#FF0000"

        # Check that non-color fields remain unchanged
        assert merged_style.name == "base_style"
        assert merged_style.typography.title_scale == 1.0

    def test_partial_color_override(self, loader, base_style_pack):
        """Test overriding multiple colors while keeping others."""
        override_data = {
            "colors": {
                "primary_text": "#FFFFFF",  # White text
                "background": "#000000",  # Black background
                "accent": "#00FFFF",  # Cyan accent
                # Other colors should remain from base
            }
        }

        merged_style = loader.merge_styles(base_style_pack, override_data)

        # Check overridden colors
        assert merged_style.colors.primary_text == "#FFFFFF"
        assert merged_style.colors.background == "#000000"
        assert merged_style.colors.accent == "#00FFFF"

        # Check colors that should remain from base
        assert merged_style.colors.secondary_text == "#666666"
        assert merged_style.colors.warning == "#FF0000"
        assert merged_style.colors.grid == "#CCCCCC"

    def test_typography_override(self, loader, base_style_pack):
        """Test overriding typography settings."""
        override_data = {
            "typography": {
                "title_font": ["Roboto", "Arial", "Sans-serif"],
                "title_scale": 1.2,
                "eq_scale": 0.9,
                # Other typography settings should remain from base
            }
        }

        merged_style = loader.merge_styles(base_style_pack, override_data)

        # Check overridden typography
        assert merged_style.typography.title_font == ["Roboto", "Arial", "Sans-serif"]
        assert merged_style.typography.title_scale == 1.2
        assert merged_style.typography.eq_scale == 0.9

        # Check typography that should remain from base
        assert merged_style.typography.body_font == ["Arial", "Helvetica"]
        assert merged_style.typography.subtitle_scale == 0.8
        assert merged_style.typography.text_scale == 0.7

    def test_nested_margin_override(self, loader, base_style_pack):
        """Test overriding nested margin values."""
        override_data = {
            "layout": {
                "margins": {
                    "top": 0.5,  # Change top margin
                    "bottom": 0.5,  # Change bottom margin
                    # left and right should remain from base
                }
            }
        }

        merged_style = loader.merge_styles(base_style_pack, override_data)

        # Check overridden margins
        assert merged_style.layout.margins.top == 0.5
        assert merged_style.layout.margins.bottom == 0.5

        # Check margins that should remain from base
        assert merged_style.layout.margins.left == 1.0
        assert merged_style.layout.margins.right == 1.0

        # Check other layout settings remain unchanged
        assert merged_style.layout.title_position == TitlePosition.CENTER
        assert merged_style.layout.max_line_length_chars == 100

    def test_graph_axes_partial_override(self, loader, base_style_pack):
        """Test overriding partial graph axes settings."""
        override_data = {
            "graph_defaults": {
                "axes": {
                    "stroke_width": 3.0,  # Change stroke width
                    "color": "#FF0000",  # Change axes color
                    # include_numbers should remain from base
                },
                "x_range": [-10, 10, 2],  # Change x range
                # y_range should remain from base
            }
        }

        merged_style = loader.merge_styles(base_style_pack, override_data)

        # Check overridden axes settings
        assert merged_style.graph_defaults.axes.stroke_width == 3.0
        assert merged_style.graph_defaults.axes.color == "#FF0000"
        assert merged_style.graph_defaults.x_range == [-10.0, 10.0, 2.0]

        # Check settings that should remain from base
        assert merged_style.graph_defaults.axes.include_numbers is True
        assert merged_style.graph_defaults.y_range == [-2.0, 8.0, 1.0]

    def test_multi_level_override(self, loader, base_style_pack):
        """Test overriding values at multiple nesting levels simultaneously."""
        override_data = {
            "name": "custom_merged_style",  # Top-level override
            "colors": {
                "accent": "#Purple",  # This should cause validation error
                "highlight": "#00FF00",  # Valid override
            },
            "layout": {"title_position": "bottom", "margins": {"top": 0.3}},
            "animations": {"write_speed": 1.5},
        }

        # This should fail due to invalid color format
        with pytest.raises(Exception):  # StyleValidationError or similar
            loader.merge_styles(base_style_pack, override_data)

    def test_valid_multi_level_override(self, loader, base_style_pack):
        """Test valid multi-level override."""
        override_data = {
            "description": "Custom merged style",  # Top-level addition
            "colors": {
                "accent": "#800080",  # Valid purple color
                "highlight": "#00FF00",  # Valid override
            },
            "layout": {"title_position": "bottom", "margins": {"top": 0.3}},
            "animations": {"write_speed": 1.5},
        }

        merged_style = loader.merge_styles(base_style_pack, override_data)

        # Check all overrides were applied
        assert merged_style.description == "Custom merged style"
        assert merged_style.colors.accent == "#800080"
        assert merged_style.colors.highlight == "#00FF00"
        assert merged_style.layout.title_position == TitlePosition.BOTTOM
        assert merged_style.layout.margins.top == 0.3
        assert merged_style.animations.write_speed == 1.5

        # Check that other values remain from base
        assert merged_style.name == "base_style"  # Name not overridden
        assert merged_style.colors.primary_text == "#000000"
        assert merged_style.layout.margins.right == 1.0  # Margin not overridden
        assert merged_style.animations.default_wait_s == 0.3

    def test_load_with_base_style(self, loader, base_style_pack):
        """Test loading a style with a base style parameter."""
        override_style_data = {
            "version": "1.1",
            "name": "override_style",
            "colors": {
                "primary_text": "#222222",  # Slightly lighter than black
                "accent": "#0088FF",  # Different blue
            },
        }

        # Load with base style
        merged_style = loader.load_from_dict(override_style_data, base_style_pack)

        # Check that explicit values from override take precedence
        assert merged_style.version == "1.1"
        assert merged_style.name == "override_style"
        assert merged_style.colors.primary_text == "#222222"
        assert merged_style.colors.accent == "#0088FF"

        # Check that missing values come from base
        assert merged_style.colors.background == "#FFFFFF"  # From base
        assert merged_style.typography.title_scale == 1.0  # From base
        assert merged_style.layout.title_position == TitlePosition.CENTER  # From base

    def test_empty_override(self, loader, base_style_pack):
        """Test merging with empty override data."""
        override_data = {}

        merged_style = loader.merge_styles(base_style_pack, override_data)

        # Should be identical to base style
        assert merged_style.name == base_style_pack.name
        assert merged_style.colors.accent == base_style_pack.colors.accent
        assert (
            merged_style.typography.title_scale
            == base_style_pack.typography.title_scale
        )
        assert (
            merged_style.layout.title_position == base_style_pack.layout.title_position
        )

    def test_complete_section_override(self, loader, base_style_pack):
        """Test overriding a complete section."""
        override_data = {
            "typography": {
                "title_font": ["Comic Sans MS"],  # Completely new typography
                "body_font": ["Comic Sans MS"],
                "math_font": ["Comic Sans MS"],
                "title_scale": 1.5,
                "subtitle_scale": 1.3,
                "text_scale": 1.1,
                "eq_scale": 1.4,
            }
        }

        merged_style = loader.merge_styles(base_style_pack, override_data)

        # Check that entire typography section was replaced
        assert merged_style.typography.title_font == ["Comic Sans MS"]
        assert merged_style.typography.body_font == ["Comic Sans MS"]
        assert merged_style.typography.math_font == ["Comic Sans MS"]
        assert merged_style.typography.title_scale == 1.5
        assert merged_style.typography.subtitle_scale == 1.3
        assert merged_style.typography.text_scale == 1.1
        assert merged_style.typography.eq_scale == 1.4

        # Check that other sections remain unchanged
        assert merged_style.colors.accent == base_style_pack.colors.accent
        assert merged_style.layout.margins.top == base_style_pack.layout.margins.top

    def test_chain_multiple_merges(self, loader):
        """Test chaining multiple merge operations."""
        # Start with minimal base
        base_data = {
            "version": "1.0",
            "name": "chain_base",
            "colors": {
                "primary_text": "#000000",
                "accent": "#0000FF",
                "background": "#FFFFFF",
            },
        }
        base_style = loader.load_from_dict(base_data)

        # First merge: add typography
        first_override = {"typography": {"title_scale": 1.2, "text_scale": 0.9}}
        first_merged = loader.merge_styles(base_style, first_override)

        # Second merge: add layout
        second_override = {
            "layout": {"title_position": "bottom", "bullet_leading": 0.6}
        }
        second_merged = loader.merge_styles(first_merged, second_override)

        # Third merge: modify colors
        third_override = {"colors": {"accent": "#FF00FF"}}  # Change to magenta
        final_merged = loader.merge_styles(second_merged, third_override)

        # Check that all changes accumulated
        assert final_merged.typography.title_scale == 1.2  # From first merge
        assert (
            final_merged.layout.title_position == TitlePosition.BOTTOM
        )  # From second merge
        assert final_merged.colors.accent == "#FF00FF"  # From third merge

        # Check that original values are preserved
        assert final_merged.name == "chain_base"
        assert final_merged.colors.primary_text == "#000000"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
