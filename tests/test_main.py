from fastapi.testclient import TestClient
from processor.main import app
from processor import main as main_mod


def test_process_endpoint_happy_path(monkeypatch):
    # stub CLIP
    def fake_score_pairs(self, pairs):
        return [0.9, 0.1][:len(pairs)]
    monkeypatch.setattr(main_mod.ClipScorer, "score_pairs",
                        fake_score_pairs, raising=False)

    # stub LLM
    async def fake_llm(self, cleaned_text, ranked_rows):
        top_id = ranked_rows[0].split("id:")[1].split()[0]
        return {"summary": "Short summary.", "relevant_images": [top_id]}
    monkeypatch.setattr(main_mod.LlmClient,
                        "summarize_and_select", fake_llm, raising=False)

    req = {
        "filename": "slides.pdf",
        "extracted_text": "Hello\n\nWorld",
        "images": [
            {"sha256": "a"*64, "page": 0, "context_snippet": "intro figure"},
            {"sha256": "b"*64, "page": 1, "context_snippet": "method fig"},
        ],
    }

    # Use context manager so lifespan startup sets app.state.llm/clip
    with TestClient(app) as client:
        res = client.post("/process", json=req)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["summary"] == "Short summary."
        assert data["relevant_images"] == ["a"*64]
        assert isinstance(data["estimated_duration_sec"], int)
        assert isinstance(data["outline"], list)
