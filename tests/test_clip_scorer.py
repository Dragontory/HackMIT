import os
from PIL import Image
from processor.clip_scorer import ClipScorer


def _make_img(path: str, color: tuple[int, int, int]):
    img = Image.new("RGB", (64, 64), color=color)
    img.save(path)


def test_clip_scores_and_missing_files(tmp_path):
    # Create two simple images
    p1 = tmp_path / "red.png"
    p2 = tmp_path / "green.png"
    _make_img(str(p1), (255, 0, 0))
    _make_img(str(p2), (0, 255, 0))

    scorer = ClipScorer()

    pairs = [
        (str(p1), "a red square"),
        (str(p2), "a green square"),
        ("does/not/exist.png", "anything"),
    ]
    scores = scorer.score_pairs(pairs)

    assert len(scores) == 3
    assert scores[2] == -1.0  # missing file handled
    # Each image should score reasonably against its own text
    assert scores[0] > -1.0 and scores[1] > -1.0
