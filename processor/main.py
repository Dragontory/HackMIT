# processor/main.py (only the route body changed; rest stays)
import os
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.routing import APIRouter

from .settings import settings
from .schemas import ProcessingRequest, ProductionV1, Scene, ImageInfo
from .text_cleaner import clean_text, split_into_sections, outline_from_titles
from .image_utils import dedupe_images, images_by_page
from .policy import estimate_duration_sec
from .llm_client import LlmClient

router = APIRouter()


@router.post("/process", response_model=ProductionV1)
async def process_content(req: ProcessingRequest, request: Request) -> ProductionV1:
    if not req.extracted_text or not req.extracted_text.strip():
        raise HTTPException(400, "Extracted text cannot be empty.")

    cleaned = clean_text(req.extracted_text)
    if not cleaned:
        raise HTTPException(400, "No usable text after cleaning.")

    images: List[ImageInfo] = dedupe_images(req.images)
    by_page = images_by_page(images)

    # Ranked rows shown to LLM (neutral scores; CLIP can be added later)
    ranked_rows = [
        f"- id:{img.sha256} page:{img.page} score:0.500 context:{(img.context_snippet or '')[:220]}"
        for img in images
    ][: settings.max_relevant_images * 2]

    llm: LlmClient = request.app.state.llm
    plan = await llm.plan_from_slides(cleaned, ranked_rows)

    summary = (plan.get("summary") or "").strip()
    slide_plan = plan.get("slides") or []            # from Claude
    rel_imgs_llm = [s for s in (
        plan.get("relevant_images") or []) if isinstance(s, str)]

    # Build script paragraphs in source order, align images by page
    script_paras: List[str] = []
    chosen_imgs: List[str] = []
    order_items = []

    if slide_plan:
        # sort by page so flow matches PDF
        for s in sorted(slide_plan, key=lambda x: int(x.get("page", 0)) if isinstance(x.get("page"), int) else 0):
            page = int(s.get("page", 0)) if isinstance(
                s.get("page"), int) else 0
            narration = (s.get("narration") or s.get("summary") or "").strip()
            if not narration:
                continue
            # choose an image: first a proposed that exists on the same page, else any on that page, else any unused
            proposed = [r for r in (
                s.get("image_refs") or []) if isinstance(r, str)]
            page_pool = by_page.get(page, [])
            chosen = None
            for r in proposed:
                if r in page_pool:
                    chosen = r
                    break
            if not chosen and page_pool:
                chosen = page_pool[0]
            if not chosen:
                for img in images:
                    if img.sha256 not in chosen_imgs:
                        chosen = img.sha256
                        break
            if chosen and chosen not in chosen_imgs:
                chosen_imgs.append(chosen)
            order_items.append((narration, chosen))
    else:
        # fallback: paragraph sections if Claude didn’t return slides
        for idx, chunk in enumerate(split_into_sections(cleaned)[:12]):
            img = (by_page.get(idx) or by_page.get(0) or [None])[0]
            order_items.append((chunk, img))

    # Build script text & compute duration proportional to paragraph length (not equal slices)
    script_paras = [n for n, _ in order_items]
    script = "\n\n".join(script_paras)
    words = len(script.split())

    relevant_images = (rel_imgs_llm or [c for _, c in order_items if c])[
        : settings.max_relevant_images]
    duration = estimate_duration_sec(
        words=words, num_images=len(relevant_images))

    # Proportional timing by paragraph word count
    lengths = [max(1, len(p.split())) for p in script_paras] or [1]
    total_len = sum(lengths)
    raw_times = [max(3, int(round(duration * L / total_len)))
                 for L in lengths]  # >=3s per scene
    # fix rounding drift
    drift = duration - sum(raw_times)
    if raw_times:
        raw_times[-1] += drift

    scenes: List[Scene] = []
    t = 0
    for i, (para, img_hint) in enumerate(order_items):
        start, end = t, t + raw_times[i]
        hint = relevant_images[i] if i < len(relevant_images) else (
            relevant_images[-1] if relevant_images else None)
        if img_hint and hint is None:
            hint = img_hint
        scenes.append(Scene(start_sec=start, end_sec=end,
                      narration=para, image_hint=hint))
        t = end

    outline = outline_from_titles(slide_plan, summary)

    return ProductionV1(
        source_filename=req.filename,
        word_count=words,
        estimated_duration_sec=duration,
        summary=summary,
        outline=outline,
        script=script,
        scenes=scenes,
        relevant_images=relevant_images,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.llm = LlmClient()
    try:
        yield
    finally:
        await app.state.llm.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(router)

    @app.get("/health")
    def health():
        return {
            "ok": True,
            "provider": "anthropic",
            "anthropic_model": os.getenv("ANTHROPIC_MODEL", settings.anthropic_model),
        }
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("processor.main:app", host=settings.host,
                port=settings.port, reload=True)
