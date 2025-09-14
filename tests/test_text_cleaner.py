from processor.text_cleaner import clean_text, auto_outline


def test_clean_text_strips_headers_and_numbers():
    raw = "Course\nLecture\n\nA set is...\n1\n\nCourse\nLecture\n\nMore...\n\nReferences\n[1] x"
    cleaned = clean_text(raw)
    assert "Course" not in cleaned and "Lecture" not in cleaned
    assert "References" not in cleaned
    assert "1" not in [ln.strip() for ln in cleaned.splitlines()]


def test_auto_outline_makes_beats():
    summary = "Para1.\n\nPara2.\n\nPara3.\n\nPara4."
    beats = auto_outline(summary)
    assert 3 <= len(beats) <= 8
