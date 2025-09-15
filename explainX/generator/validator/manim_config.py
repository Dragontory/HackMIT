"""
Manim configuration templates for consistent preview settings.
"""

# Manim configuration for low quality previews
MANIM_CONFIG_LOW_QUALITY = """[CLI]
# Low quality preview settings for fast validation
quality = low_quality
resolution = 854,480
frame_rate = 15
pixel_height = 480
pixel_width = 854
verbosity = ERROR
disable_caching = True
dry_run = False
write_to_movie = True
save_last_frame = True
transparent = False
background_opacity = 1.0

[ffmpeg]
# Optimize for speed over quality
loglevel = error
"""

# Manim configuration for preview quality
MANIM_CONFIG_PREVIEW = """[CLI]
# Preview quality settings for validation
quality = medium_quality
resolution = 1280,720
frame_rate = 30
pixel_height = 720 
pixel_width = 1280
verbosity = ERROR
disable_caching = True
dry_run = False
write_to_movie = True
save_last_frame = True
transparent = False
background_opacity = 1.0

[ffmpeg]
# Balance speed and quality for preview
loglevel = error
"""


def get_manim_config(q_level: str = "preview") -> str:
    """
    Get appropriate manim configuration for quality level.

    Args:
        q_level: "low" or "preview"

    Returns:
        Manim config file content as string
    """
    if q_level == "low":
        return MANIM_CONFIG_LOW_QUALITY
    else:
        return MANIM_CONFIG_PREVIEW
