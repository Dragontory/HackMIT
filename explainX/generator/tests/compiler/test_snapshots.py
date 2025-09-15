"""
Golden Snapshot Tests for Deterministic Manim Code Generation (Ticket 4.12).

These tests ensure that the compiler generates consistent, deterministic output
by comparing generated code against golden snapshot files.
"""

import sys
import json
import hashlib
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import pytest

from compiler.enhanced_emitter import compile_scene_enhanced, compile_module_enhanced
from compiler.assets import StaticAssetResolver
from style.models import StylePack, ColorPalette
from style.provider import StylePackProvider


class SnapshotTester:
    """Helper class for managing golden snapshot tests."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.snapshots_dir = Path(__file__).parent / "__snapshots__"
        self.snapshots_dir.mkdir(exist_ok=True)

    def assert_matches_snapshot(self, generated_code: str, scene_id: str = None):
        """Assert that generated code matches stored snapshot."""
        # Create deterministic filename
        if scene_id:
            snapshot_name = f"{self.test_name}_{scene_id}.py"
        else:
            snapshot_name = f"{self.test_name}.py"

        snapshot_path = self.snapshots_dir / snapshot_name

        # Normalize whitespace for consistent comparison
        normalized_code = self._normalize_code(generated_code)

        if snapshot_path.exists():
            # Compare against existing snapshot
            with open(snapshot_path, "r") as f:
                snapshot_content = f.read()

            if normalized_code != snapshot_content:
                # Show diff for debugging
                print(f"\n❌ SNAPSHOT MISMATCH for {snapshot_name}")
                print(f"Expected (snapshot):")
                print("-" * 40)
                print(snapshot_content)
                print("-" * 40)
                print(f"Actual (generated):")
                print("-" * 40)
                print(normalized_code)
                print("-" * 40)

                # Fail the test
                pytest.fail(f"Generated code doesn't match snapshot {snapshot_name}")
        else:
            # Create new snapshot
            with open(snapshot_path, "w") as f:
                f.write(normalized_code)

            print(f"✨ Created new snapshot: {snapshot_name}")
            print(f"Generated code length: {len(normalized_code)} chars")

    def _normalize_code(self, code: str) -> str:
        """Normalize code for consistent snapshots."""
        lines = code.split("\n")

        # Remove dynamic content (timestamps, etc.)
        normalized_lines = []
        for line in lines:
            # Skip timestamp lines in module headers
            if "Generated on:" in line:
                normalized_lines.append("Generated on: [TIMESTAMP]")
            else:
                normalized_lines.append(line)

        return "\n".join(normalized_lines)


class TestSnapshotBasicScenes:
    """Snapshot tests for basic scene types (Case A, B, C from spec)."""

    @pytest.fixture
    def style_provider(self):
        """Create deterministic style provider for snapshots."""
        colors = ColorPalette(
            primary_text="#000000", accent="#2563EB", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="snapshot_test", colors=colors)
        return StylePackProvider(style_pack)

    @pytest.fixture
    def asset_resolver(self):
        """Create deterministic asset resolver."""
        resolver = StaticAssetResolver()
        resolver.add_asset("sha256:abc123def456789", "/assets/test/demo_image.png")
        return resolver

    def test_2d_basic_scene_snapshot(self, style_provider, asset_resolver):
        """Case A: 2D basic scene with title + equation + bullet + pause."""
        tester = SnapshotTester("2d_basic")

        # Load test data
        data_path = Path(__file__).parent / "data" / "dsl_simple_2d.json"
        with open(data_path) as f:
            scene_json = json.load(f)

        # Generate code
        result = compile_scene_enhanced(
            scene_json, style_provider, asset_resolver, None
        )

        # Assert matches snapshot
        tester.assert_matches_snapshot(result, scene_json["scene_id"])

        # Verify key elements are present
        assert "class Scene_Simple_Intro(Scene)" in result
        assert "Text(" in result
        assert "MathTex(" in result
        assert "self.wait(" in result

    def test_3d_surface_scene_snapshot(self, style_provider, asset_resolver):
        """Case B: 3D surface scene with surface3d + camera_move."""
        tester = SnapshotTester("3d_surface")

        # Load test data
        data_path = Path(__file__).parent / "data" / "dsl_surface_3d.json"
        with open(data_path) as f:
            scene_json = json.load(f)

        # Generate code
        result = compile_scene_enhanced(
            scene_json, style_provider, asset_resolver, None
        )

        # Assert matches snapshot
        tester.assert_matches_snapshot(result, scene_json["scene_id"])

        # Verify 3D elements are present
        assert "class Scene_Sec_Surf(ThreeDScene)" in result
        assert "ThreeDAxes()" in result
        assert "Surface(" in result
        assert "set_camera_orientation" in result

    def test_image_asset_scene_snapshot(self, style_provider, asset_resolver):
        """Case C: Scene with image asset reference."""
        tester = SnapshotTester("image_asset")

        # Load test data
        data_path = Path(__file__).parent / "data" / "dsl_with_image.json"
        with open(data_path) as f:
            scene_json = json.load(f)

        # Generate code
        result = compile_scene_enhanced(
            scene_json, style_provider, asset_resolver, None
        )

        # Assert matches snapshot
        tester.assert_matches_snapshot(result, scene_json["scene_id"])

        # Verify asset elements are present
        assert "class Scene_Img_Demo(Scene)" in result
        assert "ImageMobject(" in result
        assert "/assets/test/demo_image.png" in result
        assert "scale_to_fit_width(6.0)" in result


class TestSnapshotModuleGeneration:
    """Snapshot tests for module generation."""

    @pytest.fixture
    def style_provider(self):
        """Create style provider."""
        colors = ColorPalette(
            primary_text="#111111", accent="#FF5722", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="module_test", colors=colors)
        return StylePackProvider(style_pack)

    @pytest.fixture
    def asset_resolver(self):
        """Create asset resolver."""
        resolver = StaticAssetResolver()
        resolver.add_asset("sha256:abc123def456789", "/assets/test/sample.png")
        return resolver

    def test_multi_scene_module_snapshot(self, style_provider, asset_resolver):
        """Test module with multiple scenes produces deterministic output."""
        tester = SnapshotTester("multi_scene_module")

        # Load multiple scene data files
        scenes_data = []
        data_dir = Path(__file__).parent / "data"

        for json_file in ["dsl_simple_2d.json", "dsl_surface_3d.json"]:
            with open(data_dir / json_file) as f:
                scenes_data.append(json.load(f))

        # Generate module
        result = compile_module_enhanced(
            scenes_data, style_provider, asset_resolver, None
        )

        # Assert matches snapshot
        tester.assert_matches_snapshot(result)

        # Verify module structure with enhanced templates
        assert "from manim import *" in result
        assert "import numpy as np" in result  # Should be included for 3D surface
        assert (
            "# Generated by codegen compiler — DO NOT EDIT." in result
        )  # New template header
        assert "class Scene_Simple_Intro(Scene)" in result
        assert "class Scene_Sec_Surf(ThreeDScene)" in result


class TestSnapshotDeterminism:
    """Test deterministic code generation."""

    def test_deterministic_output(self):
        """Test that multiple runs produce identical output."""
        # Create test dependencies
        colors = ColorPalette(
            primary_text="#333333", accent="#0066CC", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="determinism_test", colors=colors)
        style = StylePackProvider(style_pack)
        resolver = StaticAssetResolver()

        scene_json = {
            "scene_id": "determinism_test",
            "timeline": [
                {"op": "title", "text": "Deterministic Test"},
                {"op": "eq", "latex": "a^2 + b^2 = c^2"},
                {"op": "pause", "seconds": 1.0},
            ],
        }

        # Generate code multiple times
        results = []
        for i in range(3):
            result = compile_scene_enhanced(scene_json, style, resolver, None)
            results.append(result)

        # All results should be identical
        assert (
            results[0] == results[1] == results[2]
        ), "Code generation is not deterministic"

        # Should contain expected deterministic elements
        result = results[0]
        assert "class Scene_Determinism_Test(Scene)" in result
        assert "title = Text(" in result
        assert "eq = MathTex(" in result


class TestSnapshotEdgeCases:
    """Snapshot tests for edge cases and error handling."""

    def test_unknown_operation_snapshot(self):
        """Test handling of unknown operations."""
        tester = SnapshotTester("unknown_op")

        colors = ColorPalette(
            primary_text="#000000", accent="#0066CC", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="test", colors=colors)
        style = StylePackProvider(style_pack)
        resolver = StaticAssetResolver()

        scene_json = {
            "scene_id": "unknown_test",
            "timeline": [
                {"op": "title", "text": "Before Unknown"},
                {"op": "unknown_operation", "data": "test"},
                {"op": "text", "text": "After Unknown"},
            ],
        }

        result = compile_scene_enhanced(scene_json, style, resolver, None)
        tester.assert_matches_snapshot(result, "unknown_test")

        # Should handle unknown operations gracefully
        assert "Unknown operation: unknown_operation" in result
        assert "pass" in result

    def test_empty_timeline_snapshot(self):
        """Test handling of scenes with minimal content."""
        tester = SnapshotTester("minimal")

        colors = ColorPalette(
            primary_text="#000000", accent="#0066CC", background="#FFFFFF"
        )
        style_pack = StylePack(version="1.0", name="test", colors=colors)
        style = StylePackProvider(style_pack)
        resolver = StaticAssetResolver()

        scene_json = {
            "scene_id": "minimal_test",
            "timeline": [{"op": "pause", "seconds": 1.0}],
        }

        result = compile_scene_enhanced(scene_json, style, resolver, None)
        tester.assert_matches_snapshot(result, "minimal_test")

        # Should generate valid minimal scene
        assert "class Scene_Minimal_Test(Scene)" in result
        assert "self.wait(1.0)" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
