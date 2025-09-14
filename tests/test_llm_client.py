# tests/test_llm_client.py
import asyncio
import httpx
import pytest
from processor.llm_client import LlmClient


class DummyResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {
            "choices": [{"message": {"content": "{\"summary\":\"ok\",\"relevant_images\":[\"" + "a"*64 + "\"]}"}}]
        }

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=None)

    def json(self):
        return self._payload


def test_llm_client_parses_json(monkeypatch):
    client = LlmClient()

    async def fake_post(url, json):
        return DummyResponse(payload={
            "choices": [{"message": {"content": "{\"summary\":\"S\",\"relevant_images\":[\"" + "a"*64 + "\"]}"}}]
        })
    monkeypatch.setattr(client.client, "post", fake_post)

    async def run():
        out = await client.summarize_and_select("text", ["- id:..."])
        assert out["summary"] == "S"
        assert out["relevant_images"] and len(out["relevant_images"][0]) == 64
        await client.aclose()

    asyncio.run(run())


def test_llm_client_raises_on_http_error(monkeypatch):
    client = LlmClient()

    async def fake_post(url, json):
        return DummyResponse(status_code=500)
    monkeypatch.setattr(client.client, "post", fake_post)

    async def run():
        with pytest.raises(httpx.HTTPError):
            await client.summarize_and_select("text", [])
        await client.aclose()

    asyncio.run(run())
