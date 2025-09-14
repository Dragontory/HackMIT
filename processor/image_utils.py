from typing import List, Dict
from .schemas import ImageInfo


def dedupe_images(images: List[ImageInfo]) -> List[ImageInfo]:
    """
    Remove duplicates:
    - Exact dedupe by sha256
    - Near-dups grouped by phash (keep first seen)
    """
    seen_sha: set[str] = set()
    by_key: Dict[str, ImageInfo] = {}
    for img in images:
        if img.sha256 in seen_sha:
            continue
        seen_sha.add(img.sha256)
        key = img.phash or img.sha256
        if key not in by_key:
            by_key[key] = img
    return list(by_key.values())
