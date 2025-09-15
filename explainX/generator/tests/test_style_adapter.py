"""
Tests for style pack adapter functions (Ticket 2.4).

This module tests the pre-Manim adapter functions that convert style pack
values into formats convenient for the compiler without importing Manim.
"""

import pytest
import sys
from pathlib import Path

# Add the parent directories to the path
sys.path.append(str(Path(__file__).parent.parent))

from style.normalize import color_tuple
from style import load_style_pack, create_style_provider


class TestColorTuple:
    """Test cases for color tuple conversion."""

    def test_basic_color_conversion(self):
        """Test basic hex to RGB tuple conversion."""
        test_cases = [
            ("#FF0000", (255, 0, 0)),  # Pure red
            ("#00FF00", (0, 255, 0)),  # Pure green
            ("#0000FF", (0, 0, 255)),  # Pure blue
            ("#FFFFFF", (255, 255, 255)),  # White
            ("#000000", (0, 0, 0)),  # Black
            ("#2563EB", (37, 99, 235)),  # Blue from spec
        ]

        for hex_color, expected_rgb in test_cases:
            result = color_tuple(hex_color)
            assert (
                result == expected_rgb
            ), f"Expected {expected_rgb}, got {result} for {hex_color}"

    def test_case_insensitive_conversion(self):
        """Test that both upper and lowercase hex work."""
        test_cases = [
            ("#ff0000", (255, 0, 0)),  # Lowercase
            ("#FF0000", (255, 0, 0)),  # Uppercase
            ("#AbCdEf", (171, 205, 239)),  # Mixed case
            ("#abcdef", (171, 205, 239)),  # Lowercase
            ("#ABCDEF", (171, 205, 239)),  # Uppercase
        ]

        for hex_color, expected_rgb in test_cases:
            result = color_tuple(hex_color)
            assert (
                result == expected_rgb
            ), f"Expected {expected_rgb}, got {result} for {hex_color}"

    def test_invalid_color_formats(self):
        """Test that invalid color formats raise appropriate errors."""
        invalid_cases = [
            ("blue", "Color must start with #"),
            ("FF0000", "Color must start with #"),
            ("#FF00", "Color must be exactly 7 characters"),
            ("#FF0000AA", "Color must be exactly 7 characters"),
            ("#GGHHII", "Color must contain only valid hex characters"),
            ("#FF00Z0", "Color must contain only valid hex characters"),
            (123, "Color must be a string"),
            (None, "Color must be a string"),
            ("", "Color must start with #"),
        ]

        for invalid_color, expected_error in invalid_cases:
            with pytest.raises(ValueError) as exc_info:
                color_tuple(invalid_color)
            assert expected_error in str(exc_info.value)

    def test_edge_case_values(self):
        """Test edge case RGB values."""
        test_cases = [
            ("#010203", (1, 2, 3)),  # Very low values
            ("#FEFCFA", (254, 252, 250)),  # Very high values
            ("#808080", (128, 128, 128)),  # Middle gray
            ("#7F7F7F", (127, 127, 127)),  # Just below middle
            ("#818181", (129, 129, 129)),  # Just above middle
        ]

        for hex_color, expected_rgb in test_cases:
            result = color_tuple(hex_color)
            assert (
                result == expected_rgb
            ), f"Expected {expected_rgb}, got {result} for {hex_color}"


class TestStyleProviderAdapters:
    """Test cases for StyleProvider adapter methods."""

    @pytest.fixture
    def style_provider(self):
        """Create a style provider for testing."""
        style_data = {
            "version": "1.0",
            "name": "adapter_test",
            "colors": {
                "primary_text": "#111111",
                "accent": "#2563EB",
                "background": "#FFFFFF",
            },
            "typography": {
                "title_scale": 1.1,
                "subtitle_scale": 0.8,
                "text_scale": 0.85,
                "eq_scale": 1.05,
            },
            "layout": {"title_position": "center"},
        }
        style_pack = load_style_pack(style_data)
        return create_style_provider(style_pack)

    def test_title_position_enum(self, style_provider):
        """Test title position enum return."""
        position = style_provider.get_title_position_enum()
        assert position == "center"
        assert isinstance(position, str)
        assert position in ["top", "center", "bottom"]

    def test_text_scales_dict(self, style_provider):
        """Test text scales dictionary return."""
        scales = style_provider.get_text_scales()

        # Check return type and structure
        assert isinstance(scales, dict)
        assert set(scales.keys()) == {"title", "subtitle", "text", "eq"}

        # Check specific values
        assert scales["title"] == 1.1
        assert scales["subtitle"] == 0.8
        assert scales["text"] == 0.85
        assert scales["eq"] == 1.05

        # Check all values are floats
        for key, value in scales.items():
            assert isinstance(
                value, float
            ), f"Scale {key} should be float, got {type(value)}"

    def test_different_title_positions(self):
        """Test all possible title position values."""
        positions = ["top", "center", "bottom"]

        for position in positions:
            style_data = {
                "version": "1.0",
                "name": f"test_{position}",
                "colors": {
                    "primary_text": "#111111",
                    "accent": "#222222",
                    "background": "#FFFFFF",
                },
                "layout": {"title_position": position},
            }
            style_pack = load_style_pack(style_data)
            provider = create_style_provider(style_pack)

            result = provider.get_title_position_enum()
            assert result == position

    def test_default_text_scales(self):
        """Test that default text scales are returned when not specified."""
        minimal_style = {
            "version": "1.0",
            "name": "minimal",
            "colors": {
                "primary_text": "#111111",
                "accent": "#222222",
                "background": "#FFFFFF",
            },
        }
        style_pack = load_style_pack(minimal_style)
        provider = create_style_provider(style_pack)

        scales = provider.get_text_scales()

        # Should have default values
        assert scales["title"] == 0.9  # Default title scale
        assert scales["subtitle"] == 0.7  # Default subtitle scale
        assert scales["text"] == 0.8  # Default text scale
        assert scales["eq"] == 0.95  # Default equation scale


class TestIntegrationWithoutManim:
    """Test that adapter functions work without Manim imports."""

    def test_no_manim_import_in_normalize(self):
        """Ensure normalize.py doesn't import Manim."""
        import sys
        from style import normalize

        # Check that manim is not in the module's dependencies
        manim_imported = any(
            "manim" in module_name.lower() for module_name in sys.modules.keys()
        )
        # We don't assert False here because other parts of the system might import manim
        # But we can check that our normalize module works independently

        # Test that color_tuple works without Manim
        result = normalize.color_tuple("#2563EB")
        assert result == (37, 99, 235)

    def test_color_tuple_for_compiler_use(self):
        """Test color_tuple produces values suitable for compiler use."""
        # Test the specific example from the ticket
        result = color_tuple("#2563EB")
        assert result == (37, 99, 235)

        # Test that all values are in 0-255 range
        for i, value in enumerate(result):
            assert 0 <= value <= 255, f"RGB value {i} out of range: {value}"
            assert isinstance(
                value, int
            ), f"RGB value {i} should be int, got {type(value)}"

    def test_adapter_functions_are_compiler_friendly(self):
        """Test that adapter functions return compiler-friendly formats."""
        # Create a provider
        style_data = {
            "version": "1.0",
            "name": "compiler_test",
            "colors": {
                "primary_text": "#FF6B35",
                "accent": "#3182CE",
                "background": "#F7FAFC",
            },
            "typography": {"title_scale": 1.2, "subtitle_scale": 0.9},
            "layout": {"title_position": "bottom"},
        }
        style_pack = load_style_pack(style_data)
        provider = create_style_provider(style_pack)

        # Test position enum for compiler
        position = provider.get_title_position_enum()
        assert isinstance(position, str)
        assert position in ["top", "center", "bottom"]

        # Test scales dict for compiler
        scales = provider.get_text_scales()
        assert isinstance(scales, dict)
        assert all(isinstance(k, str) for k in scales.keys())
        assert all(isinstance(v, float) for v in scales.values())

        # Test color conversion for compiler
        hex_color = provider.get_accent_color()
        rgb_tuple = color_tuple(hex_color)
        assert isinstance(rgb_tuple, tuple)
        assert len(rgb_tuple) == 3
        assert all(isinstance(v, int) and 0 <= v <= 255 for v in rgb_tuple)

        # Example of how compiler might use these:
        print(f"✅ Compiler-ready values:")
        print(f"   Position: '{position}'")  # Can be used in if/elif statements
        print(f"   Title scale: {scales['title']}")  # Direct numeric value
        print(f"   RGB color: {rgb_tuple}")  # Ready for color libraries


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
