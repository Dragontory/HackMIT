"""
Style pack loader with validation, normalization, and merging capabilities.

This module provides functionality to load style packs from various sources,
validate them against the schema, normalize values, and merge with base packs.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jsonschema
from jsonschema import Draft7Validator, ValidationError

from .models import (
    StylePack,
    ColorPalette,
    Typography,
    Layout,
    Margins,
    GraphDefaults,
    AxesSettings,
    Camera3DSettings,
    AnimationSettings,
    TitlePosition,
)
from .normalize import (
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


class StyleValidationError(Exception):
    """Exception raised when style pack validation fails."""

    def __init__(self, message: str, field_path: str = None, value: Any = None):
        self.field_path = field_path
        self.value = value
        super().__init__(message)


class StyleLoader:
    """Loads, validates, and normalizes style packs."""

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the style loader with schema.

        Args:
            schema_path: Path to style schema file. Uses default if None.
        """
        if schema_path is None:
            current_dir = Path(__file__).parent
            schema_path = current_dir / "schema" / "style_schema.json"

        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)

    def _load_schema(self) -> Dict[str, Any]:
        """Load and return the JSON schema."""
        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise StyleValidationError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise StyleValidationError(f"Invalid JSON in schema file: {e}")

    def validate_style_dict(self, style: Dict[str, Any]) -> None:
        """
        Validate a style dictionary against the JSON schema.

        Args:
            style: Style dictionary to validate

        Raises:
            StyleValidationError: If validation fails
        """
        try:
            self.validator.validate(style)
        except ValidationError as e:
            field_path = (
                ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            )
            raise StyleValidationError(
                f"Validation error at {field_path}: {e.message}", field_path, e.instance
            )

    def load_from_dict(
        self, style_data: Dict[str, Any], base_style: Optional[StylePack] = None
    ) -> StylePack:
        """
        Load a style pack from a dictionary.

        Args:
            style_data: Raw style data dictionary
            base_style: Optional base style to merge with

        Returns:
            Validated and normalized StylePack instance

        Raises:
            StyleValidationError: If validation or normalization fails
        """
        # Apply defaults and merge with base style if provided
        if base_style is not None:
            style_data = self._merge_with_base(style_data, base_style)
        else:
            style_data = self._apply_schema_defaults(style_data)

        # Validate against schema first
        self.validate_style_dict(style_data)

        # Normalize and create domain objects
        try:
            return self._create_style_pack(style_data)
        except (ValueError, StyleNormalizationError) as e:
            raise StyleValidationError(f"Normalization failed: {e}")

    def load_from_file(
        self, file_path: Union[str, Path], base_style: Optional[StylePack] = None
    ) -> StylePack:
        """
        Load a style pack from a JSON file.

        Args:
            file_path: Path to JSON file
            base_style: Optional base style to merge with

        Returns:
            Validated and normalized StylePack instance

        Raises:
            StyleValidationError: If loading, validation, or normalization fails
        """
        file_path = Path(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                style_data = json.load(f)
        except FileNotFoundError:
            raise StyleValidationError(f"Style pack file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise StyleValidationError(
                f"Invalid JSON in style pack file {file_path}: {e}"
            )

        return self.load_from_dict(style_data, base_style)

    def merge_styles(
        self, base_style: StylePack, override_style: Dict[str, Any]
    ) -> StylePack:
        """
        Merge an override style with a base style pack.

        Args:
            base_style: Base style pack to start with
            override_style: Override values to apply

        Returns:
            New StylePack with merged values
        """
        # Convert base style back to dict for merging
        base_dict = self._style_pack_to_dict(base_style)

        # Merge override values
        merged_dict = apply_defaults_to_dict(override_style, base_dict)

        # Create new style pack
        return self.load_from_dict(merged_dict)

    def _apply_schema_defaults(self, style_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values from the schema to the style data."""
        # This is a simplified approach - in a more robust implementation,
        # we would walk the schema and apply all defaults
        defaults = {
            "typography": {
                "title_font": ["Inter", "Noto Sans", "DejaVu Sans"],
                "body_font": ["Inter", "Noto Sans", "DejaVu Sans"],
                "math_font": ["Computer Modern", "Latin Modern Math"],
                "title_scale": 0.9,
                "subtitle_scale": 0.7,
                "text_scale": 0.8,
                "eq_scale": 0.95,
            },
            "colors": {
                "secondary_text": "#374151",
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
                "x_range": [-3.0, 3.0, 1.0],
                "y_range": [-1.0, 9.0, 1.0],
            },
            "camera3d": {"elevation": 45.0, "azimuth": 45.0, "distance": 6.0},
            "animations": {"default_wait_s": 0.2, "write_speed": 1.0},
        }

        return apply_defaults_to_dict(style_data, defaults)

    def _merge_with_base(
        self, override_data: Dict[str, Any], base_style: StylePack
    ) -> Dict[str, Any]:
        """Merge override data with base style pack."""
        base_dict = self._style_pack_to_dict(base_style)
        return apply_defaults_to_dict(override_data, base_dict)

    def _style_pack_to_dict(self, style_pack: StylePack) -> Dict[str, Any]:
        """Convert StylePack back to dictionary form for merging."""
        result = {
            "version": style_pack.version,
            "name": style_pack.name,
            "typography": {
                "title_font": style_pack.typography.title_font,
                "body_font": style_pack.typography.body_font,
                "math_font": style_pack.typography.math_font,
                "title_scale": style_pack.typography.title_scale,
                "subtitle_scale": style_pack.typography.subtitle_scale,
                "text_scale": style_pack.typography.text_scale,
                "eq_scale": style_pack.typography.eq_scale,
            },
            "colors": {
                "primary_text": style_pack.colors.primary_text,
                "secondary_text": style_pack.colors.secondary_text,
                "accent": style_pack.colors.accent,
                "background": style_pack.colors.background,
                "highlight": style_pack.colors.highlight,
                "warning": style_pack.colors.warning,
                "success": style_pack.colors.success,
                "grid": style_pack.colors.grid,
            },
            "layout": {
                "margins": {
                    "top": style_pack.layout.margins.top,
                    "right": style_pack.layout.margins.right,
                    "bottom": style_pack.layout.margins.bottom,
                    "left": style_pack.layout.margins.left,
                },
                "title_position": style_pack.layout.title_position.value,
                "max_line_length_chars": style_pack.layout.max_line_length_chars,
                "bullet_leading": style_pack.layout.bullet_leading,
            },
            "graph_defaults": {
                "axes": {
                    "include_numbers": style_pack.graph_defaults.axes.include_numbers,
                    "stroke_width": style_pack.graph_defaults.axes.stroke_width,
                    "color": style_pack.graph_defaults.axes.color,
                },
                "x_range": style_pack.graph_defaults.x_range,
                "y_range": style_pack.graph_defaults.y_range,
            },
            "camera3d": {
                "elevation": style_pack.camera3d.elevation,
                "azimuth": style_pack.camera3d.azimuth,
                "distance": style_pack.camera3d.distance,
            },
            "animations": {
                "default_wait_s": style_pack.animations.default_wait_s,
                "write_speed": style_pack.animations.write_speed,
            },
        }

        # Only include description if it's not None
        if style_pack.description is not None:
            result["description"] = style_pack.description

        return result

    def _create_style_pack(self, style_data: Dict[str, Any]) -> StylePack:
        """Create a StylePack from normalized data."""
        # Normalize and create color palette
        colors_data = style_data["colors"]
        colors = ColorPalette(
            primary_text=normalize_hex_color(
                colors_data["primary_text"], "colors.primary_text"
            ),
            secondary_text=normalize_hex_color(
                colors_data.get("secondary_text", "#374151"), "colors.secondary_text"
            ),
            accent=normalize_hex_color(colors_data["accent"], "colors.accent"),
            background=normalize_hex_color(
                colors_data["background"], "colors.background"
            ),
            highlight=normalize_hex_color(
                colors_data.get("highlight", "#F59E0B"), "colors.highlight"
            ),
            warning=normalize_hex_color(
                colors_data.get("warning", "#DC2626"), "colors.warning"
            ),
            success=normalize_hex_color(
                colors_data.get("success", "#16A34A"), "colors.success"
            ),
            grid=normalize_hex_color(colors_data.get("grid", "#9CA3AF"), "colors.grid"),
        )

        # Normalize and create typography
        typo_data = style_data.get("typography", {})
        typography = Typography(
            title_font=normalize_font_list(
                typo_data.get("title_font", ["Inter", "Noto Sans", "DejaVu Sans"]),
                "typography.title_font",
            ),
            body_font=normalize_font_list(
                typo_data.get("body_font", ["Inter", "Noto Sans", "DejaVu Sans"]),
                "typography.body_font",
            ),
            math_font=normalize_font_list(
                typo_data.get("math_font", ["Computer Modern", "Latin Modern Math"]),
                "typography.math_font",
            ),
            title_scale=normalize_scale_factor(
                typo_data.get("title_scale", 0.9), "typography.title_scale"
            ),
            subtitle_scale=normalize_scale_factor(
                typo_data.get("subtitle_scale", 0.7), "typography.subtitle_scale"
            ),
            text_scale=normalize_scale_factor(
                typo_data.get("text_scale", 0.8), "typography.text_scale"
            ),
            eq_scale=normalize_scale_factor(
                typo_data.get("eq_scale", 0.95), "typography.eq_scale"
            ),
        )

        # Normalize and create layout
        layout_data = style_data.get("layout", {})
        margins_data = layout_data.get("margins", {})
        margins = Margins(
            top=normalize_margin(margins_data.get("top", 0.6), "layout.margins.top"),
            right=normalize_margin(
                margins_data.get("right", 0.6), "layout.margins.right"
            ),
            bottom=normalize_margin(
                margins_data.get("bottom", 0.6), "layout.margins.bottom"
            ),
            left=normalize_margin(margins_data.get("left", 0.7), "layout.margins.left"),
        )

        title_pos_str = layout_data.get("title_position", "top")
        title_position = TitlePosition(title_pos_str)

        layout = Layout(
            margins=margins,
            title_position=title_position,
            max_line_length_chars=normalize_integer(
                layout_data.get("max_line_length_chars", 120),
                "layout.max_line_length_chars",
                50,
                200,
            ),
            bullet_leading=normalize_positive_number(
                layout_data.get("bullet_leading", 0.5),
                "layout.bullet_leading",
                0.1,
                2.0,
            ),
        )

        # Normalize and create graph defaults
        graph_data = style_data.get("graph_defaults", {})
        axes_data = graph_data.get("axes", {})
        axes = AxesSettings(
            include_numbers=bool(axes_data.get("include_numbers", False)),
            stroke_width=normalize_positive_number(
                axes_data.get("stroke_width", 2.0),
                "graph_defaults.axes.stroke_width",
                0.5,
                10.0,
            ),
            color=normalize_hex_color(
                axes_data.get("color", "#111111"), "graph_defaults.axes.color"
            ),
        )

        graph_defaults = GraphDefaults(
            axes=axes,
            x_range=normalize_range_array(
                graph_data.get("x_range", [-3.0, 3.0, 1.0]), "graph_defaults.x_range"
            ),
            y_range=normalize_range_array(
                graph_data.get("y_range", [-1.0, 9.0, 1.0]), "graph_defaults.y_range"
            ),
        )

        # Normalize and create camera 3D settings
        camera_data = style_data.get("camera3d", {})
        camera3d = Camera3DSettings(
            elevation=normalize_angle(
                camera_data.get("elevation", 45.0), "camera3d.elevation", -90, 90
            ),
            azimuth=normalize_angle(
                camera_data.get("azimuth", 45.0), "camera3d.azimuth", 0, 360
            ),
            distance=normalize_positive_number(
                camera_data.get("distance", 6.0), "camera3d.distance", 1.0, 20.0
            ),
        )

        # Normalize and create animation settings
        anim_data = style_data.get("animations", {})
        animations = AnimationSettings(
            default_wait_s=normalize_positive_number(
                anim_data.get("default_wait_s", 0.2),
                "animations.default_wait_s",
                0.0,
                5.0,
            ),
            write_speed=normalize_positive_number(
                anim_data.get("write_speed", 1.0), "animations.write_speed", 0.1, 3.0
            ),
        )

        # Create the complete style pack
        return StylePack(
            version=style_data["version"],
            name=style_data["name"],
            description=style_data.get("description"),
            colors=colors,
            typography=typography,
            layout=layout,
            graph_defaults=graph_defaults,
            camera3d=camera3d,
            animations=animations,
        )


# Convenience functions
def load_style_pack(
    source: Union[str, Path, Dict[str, Any]], base_style: Optional[StylePack] = None
) -> StylePack:
    """
    Convenience function to load a style pack from various sources.

    Args:
        source: File path, Path object, or dictionary
        base_style: Optional base style to merge with

    Returns:
        Validated and normalized StylePack
    """
    loader = StyleLoader()

    if isinstance(source, dict):
        return loader.load_from_dict(source, base_style)
    else:
        return loader.load_from_file(source, base_style)


def validate_style_dict(style: Dict[str, Any]) -> None:
    """
    Convenience function to validate a style dictionary.

    Args:
        style: Style dictionary to validate

    Raises:
        StyleValidationError: If validation fails
    """
    loader = StyleLoader()
    loader.validate_style_dict(style)
