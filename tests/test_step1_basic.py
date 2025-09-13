import pytest
from pydantic import ValidationError
from processor.settings import settings
from processor.schemas import ImageInfo, ProcessingRequest, ProcessingResponse


def test_settings_defaults():
    assert settings.app_name
    assert "http" in str(settings.llm_base_url)
    assert settings.max_relevant_images == 24


def test_imageinfo_valid():
    img = ImageInfo(sha256="a"*64, page=0, context_snippet="ok",
                    image_path="temp_uploads/a.png")
    assert img.sha256 == "a"*64
    assert img.page == 0


def test_imageinfo_bad_sha():
    with pytest.raises(ValidationError):
        ImageInfo(sha256="zzz", page=1)


def test_request_valid_and_list_default():
    req = ProcessingRequest(filename="slides.pdf", extracted_text="x")
    assert req.images == []  # default factory


def test_response_shape():
    r = ProcessingResponse(summary="", relevant_images=[],
                           estimated_duration_sec=0, outline=[])
    assert isinstance(r.estimated_duration_sec, int)
