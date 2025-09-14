import re
from collections import Counter
from typing import List
from .settings import settings
import math


def _split_pages(text: str) -> List[str]:
    # Split raw text into pages by 2+ newlines
    return [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]


def _strip_common_headers_footers(pages: List[str]) -> List[str]:
    # Remove lines that repeat across many pages (likely headers/footers)
    lines_per_page = [set(ln.strip()
                          for ln in pg.splitlines() if ln.strip()) for pg in pages]
    all_lines = Counter(ln for s in lines_per_page for ln in s)
    threshold = max(1, int(len(pages) * settings.header_footer_hit_ratio))
    common = {ln for ln, c in all_lines.items() if c >=
              threshold and len(ln) <= 80}
    cleaned = []
    for pg in pages:
        kept = "\n".join(ln for ln in pg.splitlines()
                         if ln.strip() not in common)
        cleaned.append(kept)
    return cleaned


def _normalize_page(t: str) -> str:
    # Fix hyphenated line breaks, remove lone page numbers, normalize whitespace
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)
    # remove lines that are just numbers, even at end
    t = re.sub(r"\n\s*\d+\s*(?=\n|$)", "\n", t)

    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def clean_text(raw: str) -> str:
    pages = _split_pages(raw) or [raw]
    pages = _strip_common_headers_footers(pages)
    pages = [_normalize_page(p) for p in pages]

    # Cut references/bibliography if present
    pages = [re.split(r"(?:^|\n)(?:references|bibliography)\b[:\s]*",
                      p, flags=re.I)[0] for p in pages]

    result = "\n\n".join(p for p in pages if p)
    return result[: settings.max_json_chars].strip()  # cap size for safety


def auto_outline(summary: str) -> list[str]:
    # Break summary into 3–8 "beats" for scene cuts
    paras = [p.strip() for p in re.split(r"\n{2,}", summary) if p.strip()]
    if 0 < len(paras) <= 8:
        return paras
    sentences = re.split(r"(?<=[.!?])\s+", summary.strip())
    if not sentences:
        return []
    k = min(8, max(3, len(sentences)//3))
    size = max(1, len(sentences)//k)
    beats = [" ".join(sentences[i:i+size]).strip()
             for i in range(0, len(sentences), size)]
    return [b for b in beats if b][:8]


def _strip_common_headers_footers(pages: List[str]) -> List[str]:
    lines_per_page = [set(ln.strip()
                          for ln in pg.splitlines() if ln.strip()) for pg in pages]
    all_lines = Counter(ln for s in lines_per_page for ln in s)

    # BEFORE (too strict for odd page counts):
    # threshold = max(2, math.ceil(len(pages) * settings.header_footer_hit_ratio))

    # AFTER (matches expectation: 5 pages @ 0.5 => threshold = floor(2.5)=2)
    threshold = max(2, int(len(pages) * settings.header_footer_hit_ratio))

    common = {ln for ln, c in all_lines.items() if c >=
              threshold and len(ln) <= 80}
    cleaned = []
    for pg in pages:
        kept = "\n".join(ln for ln in pg.splitlines()
                         if ln.strip() not in common)
        cleaned.append(kept)
    return cleaned


def _normalize_page(t: str) -> str:
    # De-hyphenate words broken across lines
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)

    # Drop lines that are just page numbers, whether in the middle or at page ends
    lines = t.splitlines()
    lines = [ln for ln in lines if not re.fullmatch(r"\s*\d+\s*", ln)]
    t = "\n".join(lines)

    # Normalize whitespace and blank runs
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()
