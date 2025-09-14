from dataclasses import dataclass
from typing import Literal
from .settings import settings

PolicyMode = Literal["static", "adaptive", "learned"]


@dataclass
class Policy:
    wpm: int                 # narration speed (words per minute)
    max_images: int          # hard cap on selected images
    seconds_per_image: int   # hold per visual
    max_image_bonus: int     # cap on total visual time contribution
    mode: PolicyMode


def _static_policy() -> Policy:
    """Server-wide safe defaults from settings (reproducible)."""
    return Policy(
        wpm=settings.words_per_minute,
        max_images=settings.max_relevant_images,
        seconds_per_image=settings.seconds_per_image,
        max_image_bonus=settings.max_image_bonus,
        mode="static",
    )


def _bucket_policy(word_count: int) -> Policy:
    """
    Adaptive, explainable policy:
      - Short docs: a bit faster narration, fewer images.
      - Medium: moderate.
      - Long: slower narration, more images.
    """
    if word_count < 600:        # Short
        return Policy(wpm=140, max_images=8,  seconds_per_image=7, max_image_bonus=10, mode="adaptive")
    elif word_count <= 1500:    # Medium
        return Policy(wpm=130, max_images=12, seconds_per_image=7, max_image_bonus=12, mode="adaptive")
    else:                       # Long
        return Policy(wpm=120, max_images=18, seconds_per_image=7, max_image_bonus=12, mode="adaptive")


def _learned_policy(word_count: int, clip_scores: list[float], image_diversity: float) -> Policy:
    """
    Lightweight, deterministic head using signals you already compute.
    - avg CLIP score -> confidence in visuals
    - image_diversity -> don't flood with near-duplicates
    - word_count -> pacing by length
    Then clamp to safety bounds from settings.
    """
    base = _bucket_policy(word_count)

    # average CLIP confidence (assume in [-1,1] or [0,1]); map to [0,1]
    if clip_scores:
        avg = sum(clip_scores) / len(clip_scores)
        avg01 = (avg + 1) / 2 if - \
            1.0 <= avg <= 1.0 else max(0.0, min(1.0, avg))
    else:
        avg01 = 0.0

    # up to +4 images if high confidence & diverse figures
    bonus_imgs = int(
        round(4.0 * (0.6 * avg01 + 0.4 * max(0.0, min(1.0, image_diversity)))))
    max_images = base.max_images + bonus_imgs

    # WPM: nudge faster if very confident, slower if very long
    wpm = base.wpm + int(round(5 * (avg01 - 0.5)))
    if word_count > 2500:
        wpm -= 5

    # Slightly longer holds for confident visuals
    spi = base.seconds_per_image + (1 if avg01 >= 0.35 else 0)

    # Clamp to guardrails (predictable & safe)
    wpm = max(60, min(200, wpm))
    spi = max(3, min(20, spi))
    max_images = max(1, min(settings.max_relevant_images, max_images))
    max_image_bonus = max(
        0, min(settings.max_image_bonus, base.max_image_bonus))

    return Policy(
        wpm=wpm,
        max_images=max_images,
        seconds_per_image=spi,
        max_image_bonus=max_image_bonus,
        mode="learned",
    )


def pick_policy(mode: PolicyMode, word_count: int, clip_scores: list[float], image_diversity: float) -> Policy:
    """Pluggable selection: static | adaptive | learned."""
    if mode == "static":
        return _static_policy()
    if mode == "learned":
        return _learned_policy(word_count, clip_scores, image_diversity)
    return _bucket_policy(word_count)


def estimate_duration_sec(words: int, num_images: int, pol: Policy) -> int:
    """
    Final runtime = narration + visuals (bounded).
    Deterministic math so same input → same timing.
    """
    narration = (max(1, words) / pol.wpm) * 60.0
    visuals = min(pol.max_image_bonus, num_images) * pol.seconds_per_image
    return int(narration + visuals)
