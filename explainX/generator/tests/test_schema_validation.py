"""
Tests for Scene DSL schema validation.

This module contains comprehensive tests for validating Scene DSL documents
against the JSON schema, including positive and negative test cases.
"""

import json
import pytest
import sys
from pathlib import Path

# Add the parent directories to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from validator.schema_validate import (
    SceneValidator,
    validate_scene_dict,
    validate_plan_dict,
)


class TestSceneValidator:
    """Test cases for Scene DSL validation."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return SceneValidator()

    @pytest.fixture
    def valid_scene_basic(self):
        """Basic valid scene with minimal required fields."""
        return {
            "scene_id": "test_scene_01",
            "timeline": [{"op": "title", "text": "Test Title"}],
        }

    @pytest.fixture
    def valid_scene_complex(self):
        """Complex valid scene with multiple operations."""
        return {
            "scene_id": "gradient_descent_intro",
            "dimension": "auto",
            "heading": "What problem it solves",
            "narration": "We use gradient descent to minimize a loss function...",
            "timeline": [
                {"op": "title", "text": "Gradient Descent", "pos": "top"},
                {"op": "eq", "latex": "L(\\theta)", "anim": "write"},
                {
                    "op": "graph2d",
                    "fn": "x**2",
                    "x_min": -3,
                    "x_max": 3,
                    "anim": "draw",
                },
                {"op": "pause", "seconds": 0.4},
                {
                    "op": "transform_eq",
                    "from_latex": "L(\\theta)",
                    "to_latex": "\\nabla L(\\theta) = 0",
                },
                {"op": "callout", "text": "This is the minimum!", "pos": "bottom"},
                {
                    "op": "image",
                    "ref": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                },
                {
                    "op": "surface3d",
                    "fn": "x**2 + y**2",
                    "x_min": -2,
                    "x_max": 2,
                    "y_min": -2,
                    "y_max": 2,
                },
                {
                    "op": "camera_move",
                    "camera": {"phi": 1.2, "theta": 0.8, "distance": 10},
                },
                {
                    "op": "table",
                    "rows": [["x", "y"], ["1", "2"]],
                    "headers": ["X", "Y"],
                },
            ],
            "est_seconds": 25,
            "assets": [
                {
                    "ref": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
                }
            ],
            "complexity_score": 42,
        }

    @pytest.fixture
    def valid_full_plan(self, valid_scene_complex):
        """Valid complete plan with multiple scenes."""
        return {
            "video_id": "vid_123",
            "title": "Gradient Descent, Explained",
            "style_pack_id": "edu_default_v1",
            "scenes": [valid_scene_complex],
        }

    def test_valid_basic_scene(self, validator, valid_scene_basic):
        """Test that a basic valid scene passes validation."""
        is_valid, errors = validator.validate_scene(valid_scene_basic)
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_complex_scene(self, validator, valid_scene_complex):
        """Test that a complex valid scene with mixed operations passes validation."""
        is_valid, errors = validator.validate_scene(valid_scene_complex)
        assert is_valid is True
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_valid_full_plan(self, validator, valid_full_plan):
        """Test that a complete valid plan passes validation."""
        is_valid, errors = validator.validate_full_plan(valid_full_plan)
        assert is_valid is True
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_missing_required_scene_id(self, validator):
        """Test that missing scene_id is rejected."""
        scene = {"timeline": [{"op": "title", "text": "Test"}]}
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0
        assert any("scene_id" in error for error in errors)

    def test_missing_required_timeline(self, validator):
        """Test that missing timeline is rejected."""
        scene = {"scene_id": "test_scene"}
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0
        assert any("timeline" in error for error in errors)

    def test_unknown_operation(self, validator):
        """Test that unknown operation is rejected."""
        scene = {
            "scene_id": "test_scene",
            "timeline": [{"op": "unknown_operation", "text": "This should fail"}],
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0
        assert any(
            "unknown_operation" in error or "enum" in error.lower() for error in errors
        )

    def test_overlong_text(self, validator):
        """Test that text exceeding maxLength is rejected."""
        long_text = "x" * 161  # Exceeds 160 character limit
        scene = {
            "scene_id": "test_scene",
            "timeline": [{"op": "title", "text": long_text}],
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0
        assert any(
            "too long" in error.lower() or "maxlength" in error.lower()
            for error in errors
        )

    def test_overlong_latex(self, validator):
        """Test that LaTeX exceeding maxLength is rejected."""
        long_latex = "\\frac{" + "x" * 475 + "}{y}"  # Exceeds 480 character limit
        scene = {
            "scene_id": "test_scene",
            "timeline": [{"op": "eq", "latex": long_latex}],
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0
        assert any(
            "too long" in error.lower() or "maxlength" in error.lower()
            for error in errors
        )

    def test_invalid_scene_id_pattern(self, validator):
        """Test that invalid scene_id pattern is rejected."""
        scene = {
            "scene_id": "Invalid-Scene-ID!",  # Contains invalid characters
            "timeline": [{"op": "title", "text": "Test"}],
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0
        assert any(
            "invalid format" in error.lower() or "does not match" in error.lower()
            for error in errors
        )

    def test_invalid_asset_reference(self, validator):
        """Test that invalid asset reference format is rejected."""
        scene = {
            "scene_id": "test_scene",
            "timeline": [{"op": "image", "ref": "invalid-asset-reference"}],
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0
        assert any(
            "invalid format" in error.lower() or "does not match" in error.lower()
            for error in errors
        )

    def test_invalid_dimension_value(self, validator):
        """Test that invalid dimension value is rejected."""
        scene = {
            "scene_id": "test_scene",
            "dimension": "4d",  # Invalid dimension
            "timeline": [{"op": "title", "text": "Test"}],
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0
        assert any(
            "invalid value" in error.lower() or "not one of" in error.lower()
            for error in errors
        )

    def test_required_field_for_operation(self, validator):
        """Test that operations requiring specific fields are validated."""
        # Test equation without latex
        scene = {
            "scene_id": "test_scene",
            "timeline": [{"op": "eq", "text": "This should require latex, not text"}],
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0

    def test_pause_requires_seconds(self, validator):
        """Test that pause operation requires seconds field."""
        scene = {
            "scene_id": "test_scene",
            "timeline": [{"op": "pause"}],  # Missing required seconds field
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0

    def test_camera_move_requires_camera_params(self, validator):
        """Test that camera_move operation requires camera parameters."""
        scene = {
            "scene_id": "test_scene",
            "timeline": [{"op": "camera_move"}],  # Missing required camera field
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0

    def test_transform_eq_requires_both_latex_fields(self, validator):
        """Test that transform_eq requires both from_latex and to_latex."""
        scene = {
            "scene_id": "test_scene",
            "timeline": [
                {"op": "transform_eq", "from_latex": "x^2"}  # Missing to_latex
            ],
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0

    def test_negative_seconds_rejected(self, validator):
        """Test that negative seconds are rejected."""
        scene = {
            "scene_id": "test_scene",
            "timeline": [{"op": "pause", "seconds": -1}],  # Negative seconds
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0

    def test_invalid_width_range(self, validator):
        """Test that width outside valid range is rejected."""
        scene = {
            "scene_id": "test_scene",
            "timeline": [{"op": "box", "width": 15.0}],  # Exceeds maximum width of 12.0
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0

    def test_empty_timeline_rejected(self, validator):
        """Test that empty timeline is rejected."""
        scene = {"scene_id": "test_scene", "timeline": []}  # Empty timeline
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0

    def test_invalid_function_pattern(self, validator):
        """Test that dangerous function expressions are rejected."""
        scene = {
            "scene_id": "test_scene",
            "timeline": [
                {
                    "op": "graph2d",
                    "fn": "import os; os.system('rm -rf /')",
                }  # Dangerous function
            ],
        }
        is_valid, errors = validator.validate_scene(scene)
        assert is_valid is False
        assert len(errors) > 0

    def test_get_supported_operations(self, validator):
        """Test that validator returns correct list of supported operations."""
        ops = validator.get_supported_operations()
        expected_ops = [
            "title",
            "subtitle",
            "bullet",
            "eq",
            "image",
            "callout",
            "highlight",
            "pause",
            "transform_eq",
            "graph2d",
            "axes2d",
            "surface3d",
            "vector3d",
            "camera_move",
            "table",
            "box",
            "arrow",
        ]
        assert set(ops) == set(expected_ops)

    def test_convenience_function_validate_scene(self, valid_scene_basic):
        """Test convenience function for scene validation."""
        is_valid, errors = validate_scene_dict(valid_scene_basic)
        assert is_valid is True
        assert len(errors) == 0

    def test_convenience_function_validate_plan(self, valid_full_plan):
        """Test convenience function for plan validation."""
        is_valid, errors = validate_plan_dict(valid_full_plan)
        assert is_valid is True
        assert len(errors) == 0

    def test_multiple_scenes_validation(self, validator, valid_scene_complex):
        """Test validation of multiple scenes."""
        scene2 = {
            "scene_id": "scene_02",
            "timeline": [{"op": "subtitle", "text": "Second scene"}],
        }
        scenes = [valid_scene_complex, scene2]

        all_valid, scene_errors = validator.validate_scenes(scenes)
        assert all_valid is True
        assert len(scene_errors) == 0

    def test_multiple_scenes_with_errors(self, validator):
        """Test validation of multiple scenes where some have errors."""
        valid_scene = {
            "scene_id": "valid_scene",
            "timeline": [{"op": "title", "text": "Valid"}],
        }
        invalid_scene = {
            "scene_id": "invalid_scene",
            "timeline": [{"op": "unknown_op", "text": "Invalid"}],
        }
        scenes = [valid_scene, invalid_scene]

        all_valid, scene_errors = validator.validate_scenes(scenes)
        assert all_valid is False
        assert "invalid_scene" in scene_errors
        assert len(scene_errors["invalid_scene"]) > 0


# Integration tests
def test_real_world_gradient_descent_example():
    """Test with a realistic gradient descent example from the documentation."""
    plan = {
        "video_id": "vid_123",
        "title": "Gradient Descent, Explained",
        "style_pack_id": "edu_default_v1",
        "scenes": [
            {
                "scene_id": "sec_01",
                "dimension": "auto",
                "heading": "What problem it solves",
                "narration": "We use gradient descent to minimize a loss function...",
                "timeline": [
                    {"op": "title", "text": "Gradient Descent", "pos": "top"},
                    {"op": "eq", "latex": "L(\\theta)", "anim": "write"},
                    {
                        "op": "graph2d",
                        "fn": "x**2",
                        "x_min": -3,
                        "x_max": 3,
                        "anim": "draw",
                    },
                    {"op": "pause", "seconds": 0.4},
                ],
                "est_seconds": 25,
                "assets": [
                    {
                        "ref": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
                    }
                ],
                "complexity_score": 42,
            }
        ],
    }

    is_valid, errors = validate_plan_dict(plan)
    assert is_valid is True, f"Validation errors: {errors}"


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
