from typing import List
from .schemas import ImageInfo


def dedupe_images(images: List[ImageInfo]) -> List[ImageInfo]:
    seen, out = set(), []
    for img in images:
        if img.sha256 not in seen:
            out.append(img)
            seen.add(img.sha256)
    return out
