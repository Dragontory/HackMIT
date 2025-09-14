# Extra unit tests to raise confidence on cleaner & dedupe.

from processor.text_cleaner import clean_text
from processor.image_utils import dedupe_images
from processor.schemas import ImageInfo


def test_dehyphenation_across_lines():
    raw = "Fourier trans-\nform is important.\n\nFourier transform anew."
    cleaned = clean_text(raw)
    assert "trans-\nform" not in cleaned
    assert "transform is" in cleaned


def test_repeated_header_footer_removed():
    raw = "Course X\n2025\n\nBody A\n\nCourse X\n2025\n\nBody B"
    cleaned = clean_text(raw)
    assert "Course X" not in cleaned and "2025" not in cleaned
    assert "Body A" in cleaned and "Body B" in cleaned


def test_references_trim_top_and_inline():
    raw = "Body\n\nReferences\n[1] a\n\nBody2\n\nSome text\n\nbibliography: stuff\nNext"
    cleaned = clean_text(raw)
    assert "References" not in cleaned
    assert "bibliography" not in cleaned
    assert "Body" in cleaned and "Body2" in cleaned


def test_lone_page_numbers_varied():
    raw = "A\n\n  12 \n\nB\n\nC\n 3\n"
    cleaned = clean_text(raw)
    # No lines that are just page numbers remain
    lines = [ln.strip() for ln in cleaned.splitlines()]
    assert "12" not in lines and "3" not in lines


def test_dedupe_prefers_first_rep():
    imgs = [
        ImageInfo(sha256="a"*64, page=0, context_snippet="A", phash="p"),
        ImageInfo(sha256="b"*64, page=5, context_snippet="B",
                  phash="p"),  # near-dup of first
        ImageInfo(sha256="c"*64, page=2, context_snippet="C"),
    ]
    deduped = dedupe_images(imgs)
    hashes = [i.sha256 for i in deduped]
    assert len(deduped) == 2
    assert "a"*64 in hashes and "c"*64 in hashes
    assert "b"*64 not in hashes
