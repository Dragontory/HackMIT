"""
Style provider interface for compiler consumption.

This module provides a clean, read-only interface that the compiler can use
to access style pack information without directly depending on the domain models.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from .models import StylePack, TitlePosition


class StyleProvider(ABC):
    """Abstract interface for accessing style pack information."""

    @abstractmethod
    def get_title_font_family(self) -> List[str]:
        """Get ordered list of title font families with fallbacks."""
        pass

    @abstractmethod
    def get_body_font_family(self) -> List[str]:
        """Get ordered list of body font families with fallbacks."""
        pass

    @abstractmethod
    def get_math_font_family(self) -> List[str]:
        """Get ordered list of math font families with fallbacks."""
        pass

    @abstractmethod
    def get_title_scale(self) -> float:
        """Get scale factor for title text."""
        pass

    @abstractmethod
    def get_subtitle_scale(self) -> float:
        """Get scale factor for subtitle text."""
        pass

    @abstractmethod
    def get_text_scale(self) -> float:
        """Get scale factor for regular text."""
        pass

    @abstractmethod
    def get_equation_scale(self) -> float:
        """Get scale factor for mathematical equations."""
        pass

    @abstractmethod
    def get_primary_text_color(self) -> str:
        """Get primary text color as hex string."""
        pass

    @abstractmethod
    def get_secondary_text_color(self) -> str:
        """Get secondary text color as hex string."""
        pass

    @abstractmethod
    def get_accent_color(self) -> str:
        """Get accent color as hex string."""
        pass

    @abstractmethod
    def get_background_color(self) -> str:
        """Get background color as hex string."""
        pass

    @abstractmethod
    def get_highlight_color(self) -> str:
        """Get highlight color as hex string."""
        pass

    @abstractmethod
    def get_warning_color(self) -> str:
        """Get warning color as hex string."""
        pass

    @abstractmethod
    def get_success_color(self) -> str:
        """Get success color as hex string."""
        pass

    @abstractmethod
    def get_grid_color(self) -> str:
        """Get grid color as hex string."""
        pass

    @abstractmethod
    def get_margins(self) -> Tuple[float, float, float, float]:
        """Get margins as (top, right, bottom, left) in scene units."""
        pass

    @abstractmethod
    def get_title_position(self) -> str:
        """Get default title position as string ('top', 'center', 'bottom')."""
        pass

    @abstractmethod
    def get_max_line_length(self) -> int:
        """Get maximum line length in characters for text wrapping."""
        pass

    @abstractmethod
    def get_bullet_leading(self) -> float:
        """Get line spacing factor for bullet lists."""
        pass

    @abstractmethod
    def get_axes_settings(self) -> Tuple[bool, float, str]:
        """Get axes settings as (include_numbers, stroke_width, color)."""
        pass

    @abstractmethod
    def get_x_range(self) -> Tuple[float, float, float]:
        """Get default x-axis range as (min, max, step)."""
        pass

    @abstractmethod
    def get_y_range(self) -> Tuple[float, float, float]:
        """Get default y-axis range as (min, max, step)."""
        pass

    @abstractmethod
    def get_camera_3d_settings(self) -> Tuple[float, float, float]:
        """Get 3D camera settings as (elevation, azimuth, distance)."""
        pass

    @abstractmethod
    def get_default_wait_time(self) -> float:
        """Get default wait time between operations in seconds."""
        pass

    @abstractmethod
    def get_write_speed(self) -> float:
        """Get write animation speed factor."""
        pass

    @abstractmethod
    def get_style_name(self) -> str:
        """Get style pack name."""
        pass

    @abstractmethod
    def get_style_version(self) -> str:
        """Get style pack version."""
        pass

    @abstractmethod
    def get_title_position_enum(self) -> str:
        """Get title position as string literal ('top', 'center', 'bottom')."""
        pass

    @abstractmethod
    def get_text_scales(self) -> dict[str, float]:
        """Get text scales as dictionary with keys: title, subtitle, text, eq."""
        pass


class StylePackProvider(StyleProvider):
    """Concrete implementation of StyleProvider backed by a StylePack."""

    def __init__(self, style_pack: StylePack):
        """
        Initialize provider with a style pack.

        Args:
            style_pack: StylePack instance to provide access to
        """
        self._style_pack = style_pack

    def get_title_font_family(self) -> List[str]:
        """Get ordered list of title font families with fallbacks."""
        return list(self._style_pack.typography.title_font)  # Return copy

    def get_body_font_family(self) -> List[str]:
        """Get ordered list of body font families with fallbacks."""
        return list(self._style_pack.typography.body_font)

    def get_math_font_family(self) -> List[str]:
        """Get ordered list of math font families with fallbacks."""
        return list(self._style_pack.typography.math_font)

    def get_title_scale(self) -> float:
        """Get scale factor for title text."""
        return self._style_pack.typography.title_scale

    def get_subtitle_scale(self) -> float:
        """Get scale factor for subtitle text."""
        return self._style_pack.typography.subtitle_scale

    def get_text_scale(self) -> float:
        """Get scale factor for regular text."""
        return self._style_pack.typography.text_scale

    def get_equation_scale(self) -> float:
        """Get scale factor for mathematical equations."""
        return self._style_pack.typography.eq_scale

    def get_primary_text_color(self) -> str:
        """Get primary text color as hex string."""
        return self._style_pack.colors.primary_text

    def get_secondary_text_color(self) -> str:
        """Get secondary text color as hex string."""
        return self._style_pack.colors.secondary_text

    def get_accent_color(self) -> str:
        """Get accent color as hex string."""
        return self._style_pack.colors.accent

    def get_background_color(self) -> str:
        """Get background color as hex string."""
        return self._style_pack.colors.background

    def get_highlight_color(self) -> str:
        """Get highlight color as hex string."""
        return self._style_pack.colors.highlight

    def get_warning_color(self) -> str:
        """Get warning color as hex string."""
        return self._style_pack.colors.warning

    def get_success_color(self) -> str:
        """Get success color as hex string."""
        return self._style_pack.colors.success

    def get_grid_color(self) -> str:
        """Get grid color as hex string."""
        return self._style_pack.colors.grid

    def get_margins(self) -> Tuple[float, float, float, float]:
        """Get margins as (top, right, bottom, left) in scene units."""
        margins = self._style_pack.layout.margins
        return (margins.top, margins.right, margins.bottom, margins.left)

    def get_title_position(self) -> str:
        """Get default title position as string."""
        return self._style_pack.layout.title_position.value

    def get_max_line_length(self) -> int:
        """Get maximum line length in characters for text wrapping."""
        return self._style_pack.layout.max_line_length_chars

    def get_bullet_leading(self) -> float:
        """Get line spacing factor for bullet lists."""
        return self._style_pack.layout.bullet_leading

    def get_axes_settings(self) -> Tuple[bool, float, str]:
        """Get axes settings as (include_numbers, stroke_width, color)."""
        axes = self._style_pack.graph_defaults.axes
        return (axes.include_numbers, axes.stroke_width, axes.color)

    def get_x_range(self) -> Tuple[float, float, float]:
        """Get default x-axis range as (min, max, step)."""
        x_range = self._style_pack.graph_defaults.x_range
        return (x_range[0], x_range[1], x_range[2])

    def get_y_range(self) -> Tuple[float, float, float]:
        """Get default y-axis range as (min, max, step)."""
        y_range = self._style_pack.graph_defaults.y_range
        return (y_range[0], y_range[1], y_range[2])

    def get_camera_3d_settings(self) -> Tuple[float, float, float]:
        """Get 3D camera settings as (elevation, azimuth, distance)."""
        camera = self._style_pack.camera3d
        return (camera.elevation, camera.azimuth, camera.distance)

    def get_default_wait_time(self) -> float:
        """Get default wait time between operations in seconds."""
        return self._style_pack.animations.default_wait_s

    def get_write_speed(self) -> float:
        """Get write animation speed factor."""
        return self._style_pack.animations.write_speed

    def get_style_name(self) -> str:
        """Get style pack name."""
        return self._style_pack.name

    def get_style_version(self) -> str:
        """Get style pack version."""
        return self._style_pack.version

    def get_description(self) -> Optional[str]:
        """Get style pack description."""
        return self._style_pack.description

    def get_title_position_enum(self) -> str:
        """Get title position as string literal ('top', 'center', 'bottom')."""
        return self._style_pack.layout.title_position.value

    def get_text_scales(self) -> dict[str, float]:
        """Get text scales as dictionary with keys: title, subtitle, text, eq."""
        return {
            "title": self._style_pack.typography.title_scale,
            "subtitle": self._style_pack.typography.subtitle_scale,
            "text": self._style_pack.typography.text_scale,
            "eq": self._style_pack.typography.eq_scale,
        }


def create_style_provider(style_pack: StylePack) -> StyleProvider:
    """
    Factory function to create a style provider from a style pack.

    Args:
        style_pack: StylePack to wrap

    Returns:
        StyleProvider interface
    """
    return StylePackProvider(style_pack)
