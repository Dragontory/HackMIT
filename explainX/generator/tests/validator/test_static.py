"""
Tests for static validation (T5.1).
"""

import pytest

from generator.style.models import ColorPalette, StylePack
from generator.validator.errors import (
    ValidationError,
    ContentLengthError,
    StyleBoundsError,
    RangeError,
)
from generator.validator.scene_static import validate_scene_json, validate_style_pack


class TestSceneJsonValidation:
    """Test static validation of scene JSON."""

    def test_valid_scene_passes(self):
        """Valid scene should pass validation."""
        valid_scene = {
            "scene_id": "test_scene",
            "timeline": [
                {"op": "title", "text": "Test Title", "pos": "center"},
                {"op": "eq", "latex": "y = x^2", "pos": "center"},
                {"op": "pause", "seconds": 1.0},
            ],
        }

        # Should not raise any exceptions
        validate_scene_json(valid_scene)

    def test_overlong_text_rejected(self):
        """Scene with too-long text should be rejected with field path."""
        long_text = "A" * 200  # Exceeds schema maxLength of 160

        scene_with_long_text = {
            "scene_id": "long_text_test",
            "timeline": [{"op": "title", "text": long_text, "pos": "center"}],
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_scene_json(scene_with_long_text)

        assert exc_info.value.field == "timeline[0].text"
        assert "too long" in exc_info.value.message

    def test_overlong_latex_rejected(self):
        """Scene with too-long LaTeX should be rejected with field path."""
        long_latex = r"\frac{" + "x + " * 200 + "1}{2}"  # Over 1000 chars

        scene_with_long_latex = {
            "scene_id": "long_latex_test",
            "timeline": [{"op": "eq", "latex": long_latex, "pos": "center"}],
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_scene_json(scene_with_long_latex)

        assert exc_info.value.field == "timeline[0].latex"
        assert "too long" in exc_info.value.message

    def test_invalid_asset_ref_rejected(self):
        """Invalid asset reference should be rejected."""
        scene_with_bad_asset = {
            "scene_id": "bad_asset_test",
            "timeline": [{"op": "image", "ref": "not_a_valid_sha256", "width": 5.0}],
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_scene_json(scene_with_bad_asset)

        assert exc_info.value.field == "timeline[0].ref"
        assert "sha256:" in exc_info.value.message

    def test_valid_asset_ref_passes(self):
        """Valid sha256 asset reference should pass."""
        scene_with_good_asset = {
            "scene_id": "good_asset_test",
            "timeline": [
                {
                    "op": "image",
                    "ref": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                    "width": 5.0,
                }
            ],
        }

        # Should not raise
        validate_scene_json(scene_with_good_asset)

    def test_bad_range_rejected(self):
        """Range with min >= max should be rejected with field path."""
        scene_with_bad_range = {
            "scene_id": "bad_range_test",
            "timeline": [
                {
                    "op": "graph2d",
                    "fn": "x**2",
                    "x_min": 3,  # min > max - INVALID
                    "x_max": -3,
                    "y_min": -5,
                    "y_max": 5,
                }
            ],
        }

        with pytest.raises(RangeError) as exc_info:
            validate_scene_json(scene_with_bad_range)

        assert "x_min,x_max" in exc_info.value.field
        assert exc_info.value.min_val == 3
        assert exc_info.value.max_val == -3

    def test_invalid_function_expression_rejected(self):
        """Invalid function expression should be rejected by schema pattern."""
        scene_with_invalid_fn = {
            "scene_id": "invalid_fn_test",
            "timeline": [
                {
                    "op": "graph2d",
                    "fn": "import os; os.system('rm -rf /')",  # INVALID - dangerous pattern
                    "x_min": -5,
                    "x_max": 5,
                }
            ],
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_scene_json(scene_with_invalid_fn)

        # Should be caught by schema pattern validation
        assert "timeline[0]" in exc_info.value.field

    def test_surface3d_range_validation(self):
        """3D surface ranges should be validated."""
        scene_with_bad_3d_range = {
            "scene_id": "bad_3d_test",
            "timeline": [
                {
                    "op": "surface3d",
                    "fn": "sin(x)*cos(y)",
                    "x_min": 2,
                    "x_max": -2,  # min > max - INVALID
                    "y_min": -3,
                    "y_max": 3,
                }
            ],
        }

        with pytest.raises(RangeError) as exc_info:
            validate_scene_json(scene_with_bad_3d_range)

        assert "x_min,x_max" in exc_info.value.field


class TestStylePackValidation:
    """Test style pack validation."""

    def test_valid_style_pack_passes(self):
        """Valid style pack should pass validation."""
        colors = ColorPalette(
            primary_text="#000000", background="#FFFFFF", accent="#2563EB"
        )
        style_pack = StylePack(version="1.0", name="test_style", colors=colors)

        # Should not raise
        validate_style_pack(style_pack)

    def test_style_pack_validation_integration(self):
        """Test that style pack validation integrates properly with dataclass validation."""
        # The ColorPalette and StylePack dataclasses have their own validation
        # that prevents invalid objects from being created in the first place.
        # This is actually the desired behavior - validation happens early.

        # Test that invalid colors are caught at creation time
        with pytest.raises(ValueError):
            ColorPalette(
                primary_text="invalid_color", background="#FFFFFF", accent="#2563EB"
            )

        # Test that missing required colors are caught at creation time
        with pytest.raises(TypeError):
            ColorPalette(
                primary_text="#000000",
                background="#FFFFFF",
                # Missing accent - should fail at creation
            )

        # This demonstrates that the dataclass validation provides the first line of defense,
        # which is more robust than trying to validate after object creation.
