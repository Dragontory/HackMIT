"""
Tests for Scene DSL to Manim compilation.

Tests the core compilation pipeline from Scene DSL JSON to Manim Python code.
"""

import sys
import json
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import pytest

from compiler import compile_scene, CompileOptions
from compiler.assets import StaticAssetResolver
from compiler.dsl_types import SceneDSL
from style.models import StylePack, ColorPalette
from style.provider import StylePackProvider


class TestSceneCompilation:
    """Test basic scene compilation functionality."""

    @pytest.fixture
    def sample_style_pack(self):
        """Create a sample style pack for testing."""
        colors = ColorPalette(
            primary_text="#000000", accent="#2563EB", background="#FFFFFF"
        )
        return StylePack(version="1.0", name="test_style", colors=colors)

    @pytest.fixture
    def style_provider(self, sample_style_pack):
        """Create style provider."""
        return StylePackProvider(sample_style_pack)

    @pytest.fixture
    def asset_resolver(self):
        """Create asset resolver."""
        resolver = StaticAssetResolver()
        resolver.add_asset("sha256:abc123def", "/path/to/test/image.png")
        return resolver

    @pytest.fixture
    def compile_options(self):
        """Create compile options."""
        return CompileOptions(
            scene_class_prefix="TestScene_", include_debug_comments=True
        )

    def test_simple_scene_compilation(
        self, style_provider, asset_resolver, compile_options
    ):
        """Test compilation of simple scene."""
        scene_json = {
            "scene_id": "test_simple",
            "timeline": [
                {"op": "title", "text": "Test Title", "pos": "center", "anim": "write"},
                {"op": "pause", "seconds": 1.0},
            ],
        }

        # Compile scene
        result = compile_scene(
            scene_json, style_provider, asset_resolver, compile_options
        )

        # Verify basic structure
        assert isinstance(result, str)
        assert "class TestScene_Test_Simple" in result
        assert "def construct(self):" in result
        assert "Text(" in result
        assert "self.play(Write(" in result
        assert "self.wait(1.0)" in result

    def test_equation_scene_compilation(
        self, style_provider, asset_resolver, compile_options
    ):
        """Test compilation of scene with equations."""
        scene_json = {
            "scene_id": "test_equation",
            "timeline": [
                {"op": "eq", "latex": "E = mc^2", "pos": "center", "anim": "write"}
            ],
        }

        result = compile_scene(
            scene_json, style_provider, asset_resolver, compile_options
        )

        assert "MathTex(" in result
        assert "E = mc^2" in result

    def test_graph_scene_compilation(
        self, style_provider, asset_resolver, compile_options
    ):
        """Test compilation of scene with 2D graph."""
        scene_json = {
            "scene_id": "test_graph",
            "timeline": [
                {
                    "op": "graph2d",
                    "fn": "x**2",
                    "x_min": -2,
                    "x_max": 2,
                    "y_min": -1,
                    "y_max": 4,
                    "anim": "draw",
                }
            ],
        }

        result = compile_scene(
            scene_json, style_provider, asset_resolver, compile_options
        )

        assert "import numpy as np" in result
        assert "Axes(" in result
        assert "plot(" in result
        assert "lambda x: x**2" in result

    def test_3d_scene_selection(self, style_provider, asset_resolver, compile_options):
        """Test that 3D operations select ThreeDScene base class."""
        scene_json = {
            "scene_id": "test_3d",
            "dimension": "3d",
            "timeline": [{"op": "title", "text": "3D Scene Test"}],
        }

        result = compile_scene(
            scene_json, style_provider, asset_resolver, compile_options
        )

        assert "ThreeDScene" in result
        assert "class TestScene_Test_3d(ThreeDScene)" in result

    def test_2d_scene_selection(self, style_provider, asset_resolver, compile_options):
        """Test that 2D operations select Scene base class."""
        scene_json = {
            "scene_id": "test_2d",
            "dimension": "2d",
            "timeline": [{"op": "title", "text": "2D Scene Test"}],
        }

        result = compile_scene(
            scene_json, style_provider, asset_resolver, compile_options
        )

        assert "class TestScene_Test_2d(Scene)" in result
        assert "ThreeDScene" not in result

    def test_asset_reference_compilation(
        self, style_provider, asset_resolver, compile_options
    ):
        """Test compilation of scene with asset references."""
        scene_json = {
            "scene_id": "test_assets",
            "timeline": [
                {
                    "op": "img",
                    "ref": "sha256:abc123def",
                    "pos": "center",
                    "width": 5.0,
                    "anim": "fade",
                }
            ],
        }

        result = compile_scene(
            scene_json, style_provider, asset_resolver, compile_options
        )

        assert "ImageMobject(" in result
        assert "/path/to/test/image.png" in result
        assert "scale_to_fit_width(5.0)" in result

    def test_unknown_operation_handling(
        self, style_provider, asset_resolver, compile_options
    ):
        """Test handling of unknown operations."""
        scene_json = {
            "scene_id": "test_unknown",
            "timeline": [{"op": "unknown_operation", "data": "test"}],
        }

        result = compile_scene(
            scene_json, style_provider, asset_resolver, compile_options
        )

        # Should generate comment about unknown operation
        assert "Unknown operation: unknown_operation" in result
        assert "pass" in result

    def test_empty_scene_handling(
        self, style_provider, asset_resolver, compile_options
    ):
        """Test handling of scene with no operations."""
        scene_json = {"scene_id": "test_empty", "timeline": []}

        # Should raise validation error for empty timeline
        with pytest.raises(Exception):
            SceneDSL.from_dict(scene_json)

    def test_style_integration(self, style_provider, asset_resolver, compile_options):
        """Test that style settings are applied to generated code."""
        scene_json = {
            "scene_id": "test_style",
            "timeline": [{"op": "title", "text": "Style Test", "pos": "center"}],
        }

        result = compile_scene(
            scene_json, style_provider, asset_resolver, compile_options
        )

        # Check that style integration works with enhanced compiler
        assert "font=BODY_FONT" in result  # Uses proper font styling
        assert "scale(0.9)" in result  # Title scale from style provider

        # Verify clean modern Manim patterns are used
        assert "Text(" in result
        assert "self.play(Write(" in result


class TestCompilationErrors:
    """Test error handling in compilation."""

    @pytest.fixture
    def basic_style_provider(self):
        """Create minimal style provider."""
        colors = ColorPalette(
            primary_text="#000000", accent="#0000FF", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="basic", colors=colors)
        return StylePackProvider(style_pack)

    @pytest.fixture
    def basic_asset_resolver(self):
        """Create basic asset resolver."""
        return StaticAssetResolver()

    def test_invalid_scene_structure(self, basic_style_provider, basic_asset_resolver):
        """Test handling of invalid scene structure."""
        invalid_scene = {
            # Missing scene_id
            "timeline": [{"op": "title", "text": "Test"}]
        }

        with pytest.raises(Exception):
            compile_scene(invalid_scene, basic_style_provider, basic_asset_resolver)

    def test_missing_asset_reference(self, basic_style_provider, basic_asset_resolver):
        """Test handling of missing asset references."""
        scene_json = {
            "scene_id": "test_missing_asset",
            "timeline": [{"op": "img", "ref": "sha256:nonexistent", "pos": "center"}],
        }

        # Should compile but include error comment
        result = compile_scene(scene_json, basic_style_provider, basic_asset_resolver)
        assert "Error resolving asset" in result


class TestLoadedSceneData:
    """Test compilation using loaded JSON data files."""

    @pytest.fixture
    def loaded_simple_scene(self):
        """Load simple 2D scene from test data."""
        data_path = Path(__file__).parent / "data" / "dsl_simple_2d.json"
        with open(data_path) as f:
            return json.load(f)

    @pytest.fixture
    def basic_style_provider(self):
        """Create minimal style provider."""
        colors = ColorPalette(
            primary_text="#111111", accent="#2563EB", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="loaded_test", colors=colors)
        return StylePackProvider(style_pack)

    def test_compile_loaded_simple_scene(
        self, loaded_simple_scene, basic_style_provider
    ):
        """Test compilation of loaded simple scene."""
        resolver = StaticAssetResolver()
        options = CompileOptions()

        result = compile_scene(
            loaded_simple_scene, basic_style_provider, resolver, options
        )

        # Verify expected elements from dsl_simple_2d.json
        assert "class Scene_Simple_Intro(Scene)" in result
        assert "Welcome to ExplainX" in result
        assert "E = mc^2" in result
        assert "self.wait(1.5)" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
