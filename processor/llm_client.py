# processor/llm_client.py
import os
import json
import httpx
import re
from backoff import expo, on_exception
from fastapi import HTTPException
from .settings import settings


class LlmClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.llm_timeout_s)

    async def aclose(self):
        await self.client.aclose()

    @on_exception(expo, (httpx.HTTPError,), max_tries=3)
    async def summarize_and_select(self, cleaned_text: str, ranked_image_rows: list[str]) -> dict:
        # Dev stub (no network)
        if os.getenv("DISABLE_LLM", "0") == "1":
            snippet = " ".join(cleaned_text.strip().split())[:600]
            ids = []
            for row in ranked_image_rows[: settings.max_relevant_images]:
                for part in row.split():
                    if part.startswith("id:"):
                        ids.append(part[3:])
                        break
            return {"summary": f"(stub) {snippet}", "relevant_images": ids, "slides": []}

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=503, detail="ANTHROPIC_API_KEY not set")

        model = os.getenv("ANTHROPIC_MODEL", settings.anthropic_model if hasattr(
            settings, "anthropic_model") else "claude-3-sonnet-20240229")
        base = (os.getenv("ANTHROPIC_BASE_URL") or getattr(
            settings, "anthropic_base_url", "https://api.anthropic.com")).rstrip("/")
        url = f"{base}/v1/messages"

        system = (
            "You transform a slide deck into a production-ready video plan.\n"
            "Return STRICT JSON with keys:\n"
            "  summary: string\n"
            "  slides: [ { page:int, title:string, summary:string, talking_points:[string], narration:string, image_refs:[string] } ]\n"
            f"  relevant_images: [string]  # <= {settings.max_relevant_images}\n"
            "- Use only provided content; don't invent facts.\n"
            "- Prefer diagrams/plots; deduplicate near-duplicates.\n"
            "- Output ONLY JSON.\n"
        )
        user = (
            "CLEANED_TEXT:\n"
            f"\"\"\"{cleaned_text}\"\"\"\n\n"
            "CANDIDATE_IMAGES (ranked lines 'id:<sha> page:<n> score:<X> context:...'):\n"
            f"{chr(10).join(ranked_image_rows) if ranked_image_rows else 'None'}"
        )

        headers = {
            "x-api-key": api_key,
            "anthropic-version": os.getenv("ANTHROPIC_VERSION", "2023-06-01"),
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", settings.llm_max_tokens if hasattr(settings, "llm_max_tokens") else 1200)),
            "temperature": float(os.getenv("LLM_TEMPERATURE", getattr(settings, "llm_temperature", 0.2))),
            "system": system,
            "messages": [{"role": "user", "content": [{"type": "text", "text": user}]}],
        }

        try:
            resp = await self.client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"Anthropic unreachable: {e}")

        data = resp.json()
        text = ""
        try:
            for part in data.get("content", []):
                if part.get("type") == "text":
                    text += part.get("text", "")
        except Exception:
            text = json.dumps(data)

        # Coerce to JSON no matter what
        text = (text or "").strip()
        try:
            obj = json.loads(text)
            if not isinstance(obj, dict):
                raise ValueError
            # sanitize
            obj.setdefault("summary", "")
            obj.setdefault("slides", [])
            obj.setdefault("relevant_images", [])
            obj["summary"] = str(obj["summary"])[: getattr(
                settings, "max_json_chars", 20000)]
            obj["relevant_images"] = [
                s for s in obj["relevant_images"] if isinstance(s, str)]
            obj["relevant_images"] = obj["relevant_images"][: getattr(
                settings, "max_relevant_images", 24)]
            return obj
        except Exception:
            return {"summary": text[: getattr(settings, "max_json_chars", 20000)],
                    "slides": [],
                    "relevant_images": []}
# processor/llm_client.py (inside class LlmClient)


async def summarize_and_select(self, cleaned_text: str, ranked_image_rows: list[str]) -> dict:
    # compatibility wrapper; returns the same dict your route expects
    return await self.plan_from_slides(cleaned_text, ranked_image_rows)
