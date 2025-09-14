from .settings import settings
import math


def estimate_duration_sec(words: int, num_images: int) -> int:
    reading = math.ceil(max(1, words) / settings.words_per_minute * 60.0)
    image_bonus = min(num_images, settings.max_image_bonus) * \
        settings.seconds_per_image
    return max(settings.min_floor_sec, reading + image_bonus)
