
"""
Domain models for ExplainX style pack system.

This module defines dataclasses and enums that represent the style pack
domain model used throughout the video generation system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TitlePosition(Enum):
    """Enumeration for title positioning options."""

    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


@dataclass(frozen=True)
class Typography:
    """Typography settings for text rendering."""

    title_font: List[str] = field(
        default_factory=lambda: ["Inter", "Noto Sans", "DejaVu Sans"]
    )
    body_font: List[str] = field(
        default_factory=lambda: ["Inter", "Noto Sans", "DejaVu Sans"]
    )
    math_font: List[str] = field(
        default_factory=lambda: ["Computer Modern", "Latin Modern Math"]
    )
    title_scale: float = 0.9
    subtitle_scale: float = 0.7
    text_scale: float = 0.8
    eq_scale: float = 0.95

    def __post_init__(self):
        """Validate typography settings after initialization."""
        self._validate_scale("title_scale", self.title_scale)
        self._validate_scale("subtitle_scale", self.subtitle_scale)
        self._validate_scale("text_scale", self.text_scale)
        self._validate_scale("eq_scale", self.eq_scale)
        self._validate_fonts("title_font", self.title_font)
        self._validate_fonts("body_font", self.body_font)
        self._validate_fonts("math_font", self.math_font)

    def _validate_scale(self, field_name: str, value: float) -> None:
        """Validate scale values are within acceptable range."""
        if not 0.4 <= value <= 2.0:
            raise ValueError(f"{field_name} must be between 0.4 and 2.0, got {value}")

    def _validate_fonts(self, field_name: str, fonts: List[str]) -> None:
        """Validate font list is not empty and contains valid font names."""
        if not fonts:
            raise ValueError(f"{field_name} cannot be empty")
        if len(fonts) > 5:
            raise ValueError(f"{field_name} cannot have more than 5 fallback fonts")
        for font in fonts:
            if not isinstance(font, str) or not font.strip():
                raise ValueError(f"All fonts in {field_name} must be non-empty strings")


@dataclass(frozen=True)
class ColorPalette:
    """Color palette for all visual elements."""

    primary_text: str
    background: str
    accent: str
    secondary_text: str = "#374151"
    highlight: str = "#F59E0B"
    warning: str = "#DC2626"
    success: str = "#16A34A"
    grid: str = "#9CA3AF"

    def __post_init__(self):
        """Validate all colors are proper hex format after initialization."""
        fields = [
            "primary_text",
            "secondary_text",
            "accent",
            "background",
            "highlight",
            "warning",
            "success",
            "grid",
        ]
        for field_name in fields:
            color = getattr(self, field_name)
            self._validate_hex_color(field_name, color)

    def _validate_hex_color(self, field_name: str, color: str) -> None:
        """Validate color is a proper hex color code."""
        import re

        if not isinstance(color, str) or not re.match(r"^#[0-9A-Fa-f]{6}$", color):
            raise ValueError(
                f"{field_name} must be a valid hex color (e.g., #FF0000), got {color}"
            )


@dataclass(frozen=True)
class Margins:
    """Margin settings for layout."""

    top: float = 0.6
    right: float = 0.6
    bottom: float = 0.6
    left: float = 0.7

    def __post_init__(self):
        """Validate margin values after initialization."""
        fields = ["top", "right", "bottom", "left"]
        for field_name in fields:
            value = getattr(self, field_name)
            if not 0 <= value <= 2.5:
                raise ValueError(
                    f"{field_name} margin must be between 0 and 2.5, got {value}"
                )


@dataclass(frozen=True)
class Layout:
    """Layout and positioning settings."""

    margins: Margins = field(default_factory=Margins)
    title_position: TitlePosition = TitlePosition.TOP
    max_line_length_chars: int = 120
    bullet_leading: float = 0.5

    def __post_init__(self):
        """Validate layout settings after initialization."""
        if not 50 <= self.max_line_length_chars <= 200:
            raise ValueError(
                f"max_line_length_chars must be between 50 and 200, got {self.max_line_length_chars}"
            )
        if not 0.1 <= self.bullet_leading <= 2.0:
            raise ValueError(
                f"bullet_leading must be between 0.1 and 2.0, got {self.bullet_leading}"
            )


@dataclass(frozen=True)
class AxesSettings:
    """Settings for graph axes."""

    include_numbers: bool = False
    stroke_width: float = 2.0
    color: str = "#111111"

    def __post_init__(self):
        """Validate axes settings after initialization."""
        if not 0.5 <= self.stroke_width <= 10.0:
            raise ValueError(
                f"stroke_width must be between 0.5 and 10.0, got {self.stroke_width}"
            )
        import re

        if not re.match(r"^#[0-9A-Fa-f]{6}$", self.color):
            raise ValueError(f"color must be a valid hex color, got {self.color}")


@dataclass(frozen=True)
class GraphDefaults:
    """Default settings for graphs and plots."""

    axes: AxesSettings = field(default_factory=AxesSettings)
    x_range: List[float] = field(default_factory=lambda: [-3.0, 3.0, 1.0])
    y_range: List[float] = field(default_factory=lambda: [-1.0, 9.0, 1.0])

    def __post_init__(self):
        """Validate graph defaults after initialization."""
        self._validate_range("x_range", self.x_range)
        self._validate_range("y_range", self.y_range)

    def _validate_range(self, field_name: str, range_values: List[float]) -> None:
        """Validate range has exactly 3 values: [min, max, step]."""
        if len(range_values) != 3:
            raise ValueError(
                f"{field_name} must have exactly 3 values [min, max, step], got {len(range_values)}"
            )
        min_val, max_val, step = range_values
        if min_val >= max_val:
            raise ValueError(
                f"{field_name} min ({min_val}) must be less than max ({max_val})"
            )
        if step <= 0:
            raise ValueError(f"{field_name} step must be positive, got {step}")


@dataclass(frozen=True)
class Camera3DSettings:
    """Default 3D camera settings."""

    elevation: float = 45.0
    azimuth: float = 45.0
    distance: float = 6.0

    def __post_init__(self):
        """Validate camera settings after initialization."""
        if not -90 <= self.elevation <= 90:
            raise ValueError(
                f"elevation must be between -90 and 90 degrees, got {self.elevation}"
            )
        if not 0 <= self.azimuth <= 360:
            raise ValueError(
                f"azimuth must be between 0 and 360 degrees, got {self.azimuth}"
            )
        if not 1.0 <= self.distance <= 20.0:
            raise ValueError(
                f"distance must be between 1.0 and 20.0, got {self.distance}"
            )


@dataclass(frozen=True)
class AnimationSettings:
    """Animation timing and speed settings."""

    default_wait_s: float = 0.2
    write_speed: float = 1.0

    def __post_init__(self):
        """Validate animation settings after initialization."""
        if not 0.0 <= self.default_wait_s <= 5.0:
            raise ValueError(
                f"default_wait_s must be between 0.0 and 5.0, got {self.default_wait_s}"
            )
        if not 0.1 <= self.write_speed <= 3.0:
            raise ValueError(
                f"write_speed must be between 0.1 and 3.0, got {self.write_speed}"
            )


@dataclass(frozen=True)
class StylePack:
    """Complete style pack containing all styling information."""

    version: str
    name: str
    colors: ColorPalette
    typography: Typography = field(default_factory=Typography)
    layout: Layout = field(default_factory=Layout)
    graph_defaults: GraphDefaults = field(default_factory=GraphDefaults)
    camera3d: Camera3DSettings = field(default_factory=Camera3DSettings)
    animations: AnimationSettings = field(default_factory=AnimationSettings)
    description: Optional[str] = None

    def __post_init__(self):
        """Validate style pack after initialization."""
        self._validate_version(self.version)
        self._validate_name(self.name)

    def _validate_version(self, version: str) -> None:
        """Validate version follows semantic versioning pattern."""
        import re

        if not re.match(r"^[0-9]+\.[0-9]+$", version):
            raise ValueError(
                f"version must follow pattern 'major.minor' (e.g., '1.0'), got {version}"
            )

    def _validate_name(self, name: str) -> None:
        """Validate name is a valid identifier."""
        import re

        if not re.match(r"^[a-zA-Z0-9_]+$", name):
            raise ValueError(
                f"name must contain only alphanumeric characters and underscores, got {name}"
            )
        if not 1 <= len(name) <= 50:
            raise ValueError(
                f"name must be between 1 and 50 characters, got {len(name)}"
            )
