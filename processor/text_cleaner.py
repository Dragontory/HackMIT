# processor/text_cleaner.py
import re


def clean_text(s: str) -> str:
    """Normalize whitespace and collapse long blank runs."""
    s = s.replace("\r", "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def split_into_sections(text: str) -> list[str]:
    """
    Heuristic split into slide/paragraph-like chunks.
    First split on blank lines; if that yields too few, also split on bullets/headers.
    """
    chunks = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(chunks) <= 2:
        pieces = re.split(r"\n\s*\n|[\n•\-]\s+", text)
        chunks = [p.strip() for p in pieces if p.strip()]
    return chunks


def outline_from_titles(slides: list[dict], fallback_summary: str) -> list[str]:
    """
    Build an outline from LLM slide titles; if missing, fall back to summary lines.
    """
    out = []
    for s in slides:
        if isinstance(s, dict):
            t = (s.get("title") or "").strip()
            if t:
                out.append(t[:100])
                if len(out) >= 10:
                    break
    if not out and fallback_summary:
        out = [ln.strip()[:100]
               for ln in fallback_summary.split("\n") if ln.strip()][:10]
    return out
