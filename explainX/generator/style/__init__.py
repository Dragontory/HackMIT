"""
Style pack system for ExplainX video generation.

This package provides comprehensive style pack loading, validation, normalization,
and access functionality for consistent video styling.
"""

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
from .loader import (
    StyleLoader,
    StyleValidationError,
    load_style_pack,
    validate_style_dict,
)
from .provider import StyleProvider, StylePackProvider, create_style_provider
from .normalize import (
    StyleNormalizationError,
    normalize_hex_color,
    normalize_font_list,
    normalize_scale_factor,
    color_tuple,
)

__all__ = [
    # Models
    "StylePack",
    "ColorPalette",
    "Typography",
    "Layout",
    "Margins",
    "GraphDefaults",
    "AxesSettings",
    "Camera3DSettings",
    "AnimationSettings",
    "TitlePosition",
    # Loader
    "StyleLoader",
    "StyleValidationError",
    "load_style_pack",
    "validate_style_dict",
    # Provider
    "StyleProvider",
    "StylePackProvider",
    "create_style_provider",
    # Normalization
    "StyleNormalizationError",
    "normalize_hex_color",
    "normalize_font_list",
    "normalize_scale_factor",
    "color_tuple",
]
