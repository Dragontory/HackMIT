from processor.schemas import ImageInfo
from processor.image_utils import dedupe_images


def test_dedupe_exact_and_near():
    imgs = [
        ImageInfo(sha256="a"*64, page=0, context_snippet="A", phash="p1"),
        ImageInfo(sha256="b"*64, page=1, context_snippet="B",
                  phash="p1"),  # near-dup of first
        ImageInfo(sha256="c"*64, page=2, context_snippet="C"),
        ImageInfo(sha256="a"*64, page=3,
                  context_snippet="A-dup-exact"),    # exact dup
    ]
    deduped = dedupe_images(imgs)
    kept_hashes = {d.sha256 for d in deduped}
    assert "a"*64 in kept_hashes and "c"*64 in kept_hashes
    assert "b"*64 not in kept_hashes
    assert len(deduped) == 2
