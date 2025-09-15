"""
Tests for Scene DSL to Manim module compilation.

Tests the module-level compilation that combines multiple scenes into a single Python file.
"""

import sys
import json
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import pytest

from compiler import compile_module, CompileOptions
from compiler.assets import StaticAssetResolver
from style.models import StylePack, ColorPalette
from style.provider import StylePackProvider


class TestModuleCompilation:
    """Test module-level compilation functionality."""

    @pytest.fixture
    def sample_style_pack(self):
        """Create a sample style pack for testing."""
        colors = ColorPalette(
            primary_text="#111111", accent="#2563EB", background="#FFFFFF"
        )
        return StylePack(version="1.0", name="module_test_style", colors=colors)

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
            scene_class_prefix="Scene_",
            include_debug_comments=True,
            module_header_comment=True,
        )

    @pytest.fixture
    def sample_scenes(self):
        """Create sample scenes for module compilation."""
        return [
            {
                "scene_id": "intro",
                "timeline": [
                    {"op": "title", "text": "Introduction", "pos": "center"},
                    {"op": "pause", "seconds": 1.0},
                ],
            },
            {
                "scene_id": "main_content",
                "dimension": "2d",
                "timeline": [
                    {"op": "title", "text": "Main Content"},
                    {
                        "op": "text",
                        "text": "This is the main content of our presentation.",
                    },
                    {"op": "eq", "latex": "f(x) = x^2 + 2x + 1"},
                ],
            },
            {
                "scene_id": "conclusion",
                "dimension": "3d",
                "timeline": [
                    {"op": "title", "text": "Conclusion"},
                    {"op": "text", "text": "Thank you for watching!"},
                ],
            },
        ]

    def test_basic_module_compilation(
        self, sample_scenes, style_provider, asset_resolver, compile_options
    ):
        """Test basic module compilation with multiple scenes."""
        result = compile_module(
            sample_scenes, style_provider, asset_resolver, compile_options
        )

        # Verify module structure
        assert isinstance(result, str)
        assert "from manim import *" in result
        assert "Generated Manim Scene Module" in result

        # Verify all scenes are included
        assert "class Scene_Intro(Scene)" in result
        assert "class Scene_Main_Content(Scene)" in result
        assert "class Scene_Conclusion(ThreeDScene)" in result  # 3D scene

        # Verify scene registry comment
        assert "# Scene Registry:" in result
        assert "intro (auto," in result or "intro (2d," in result
        assert "main_content (2d," in result
        assert "conclusion (3d," in result

    def test_module_with_mixed_dimensions(
        self, style_provider, asset_resolver, compile_options
    ):
        """Test module compilation with mixed 2D and 3D scenes."""
        scenes = [
            {
                "scene_id": "scene_2d",
                "dimension": "2d",
                "timeline": [{"op": "title", "text": "2D Scene"}],
            },
            {
                "scene_id": "scene_3d",
                "dimension": "3d",
                "timeline": [{"op": "title", "text": "3D Scene"}],
            },
        ]

        result = compile_module(scenes, style_provider, asset_resolver, compile_options)

        # Verify correct base classes
        assert "class Scene_Scene_2d(Scene)" in result
        assert "class Scene_Scene_3d(ThreeDScene)" in result

    def test_module_header_comment(self, sample_scenes, style_provider, asset_resolver):
        """Test module header comment generation."""
        options = CompileOptions(module_header_comment=True)

        result = compile_module(sample_scenes, style_provider, asset_resolver, options)

        # Verify header components
        assert '"""' in result
        assert "Generated Manim Scene Module" in result
        assert "Generated on:" in result
        assert "Scene count: 3" in result
        assert "ExplainX Compiler" in result
        assert "Do not edit manually" in result

    def test_module_without_header_comment(
        self, sample_scenes, style_provider, asset_resolver
    ):
        """Test module compilation without header comment."""
        options = CompileOptions(module_header_comment=False)

        result = compile_module(sample_scenes, style_provider, asset_resolver, options)

        # Should still have imports but no header
        assert "from manim import *" in result
        assert "Generated Manim Scene Module" not in result

    def test_module_with_imports(self, style_provider, asset_resolver, compile_options):
        """Test module compilation includes necessary imports."""
        scenes = [
            {
                "scene_id": "graph_scene",
                "timeline": [{"op": "graph2d", "fn": "x**2", "x_min": -2, "x_max": 2}],
            }
        ]

        result = compile_module(scenes, style_provider, asset_resolver, compile_options)

        # Verify imports
        assert "from manim import *" in result
        assert "import numpy as np" in result  # Should be included for graph2d

    def test_empty_scenes_list(self, style_provider, asset_resolver, compile_options):
        """Test handling of empty scenes list."""
        with pytest.raises(Exception, match="Cannot compile empty scene list"):
            compile_module([], style_provider, asset_resolver, compile_options)

    def test_module_with_single_scene(
        self, style_provider, asset_resolver, compile_options
    ):
        """Test module compilation with single scene."""
        scenes = [
            {
                "scene_id": "single_scene",
                "timeline": [{"op": "title", "text": "Only Scene"}],
            }
        ]

        result = compile_module(scenes, style_provider, asset_resolver, compile_options)

        assert "class Scene_Single_Scene(Scene)" in result
        assert "Scene count: 1" in result

    def test_module_scene_separation(
        self, sample_scenes, style_provider, asset_resolver, compile_options
    ):
        """Test that scenes are properly separated in the module."""
        result = compile_module(
            sample_scenes, style_provider, asset_resolver, compile_options
        )

        # Count class definitions
        class_count = result.count("class Scene_")
        assert class_count == 3

        # Verify proper spacing between classes
        lines = result.split("\n")
        class_line_indices = [
            i for i, line in enumerate(lines) if line.startswith("class Scene_")
        ]

        # There should be blank lines between classes
        for i in range(1, len(class_line_indices)):
            prev_class_line = class_line_indices[i - 1]
            curr_class_line = class_line_indices[i]
            # Should have some blank lines between classes
            assert curr_class_line - prev_class_line > 5  # At least some separation

    def test_module_with_asset_references(
        self, style_provider, asset_resolver, compile_options
    ):
        """Test module compilation with asset references."""
        scenes = [
            {
                "scene_id": "image_scene",
                "timeline": [{"op": "img", "ref": "sha256:abc123def", "width": 4.0}],
            }
        ]

        result = compile_module(scenes, style_provider, asset_resolver, compile_options)

        assert "ImageMobject" in result
        assert "/path/to/test/image.png" in result

    def test_module_error_handling(
        self, style_provider, asset_resolver, compile_options
    ):
        """Test module compilation error handling for invalid scenes."""
        invalid_scenes = [
            {"scene_id": "valid_scene", "timeline": [{"op": "title", "text": "Valid"}]},
            {
                # Missing scene_id
                "timeline": [{"op": "title", "text": "Invalid"}]
            },
        ]

        # Should raise error for invalid scene structure
        with pytest.raises(Exception):
            compile_module(
                invalid_scenes, style_provider, asset_resolver, compile_options
            )


class TestModuleWithLoadedData:
    """Test module compilation using loaded JSON data."""

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
            primary_text="#222222", accent="#FF5722", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="loaded_module_test", colors=colors)
        return StylePackProvider(style_pack)

    def test_compile_module_with_loaded_data(
        self, loaded_simple_scene, basic_style_provider
    ):
        """Test module compilation with loaded JSON data."""
        resolver = StaticAssetResolver()
        options = CompileOptions(include_debug_comments=True)

        # Create module with loaded scene
        scenes = [loaded_simple_scene]
        result = compile_module(scenes, basic_style_provider, resolver, options)

        # Verify module structure
        assert "from manim import *" in result
        assert "class Scene_Simple_Intro(Scene)" in result
        assert "Welcome to ExplainX" in result
        assert "E = mc^2" in result

        # Verify scene registry
        assert "simple_intro" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
