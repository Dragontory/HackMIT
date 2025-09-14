# processor/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional


class ImageInfo(BaseModel):
    sha256: str
    page: int = Field(..., ge=0)
    context_snippet: Optional[str] = ""
    image_path: Optional[str] = None
    phash: Optional[str] = None


class ProcessingRequest(BaseModel):
    filename: str
    extracted_text: str
    images: List[ImageInfo]


class Scene(BaseModel):
    start_sec: int
    end_sec: int
    narration: str
    image_hint: Optional[str] = None  # sha256


class ProductionV1(BaseModel):
    schema_version: str = "video.v1"
    source_filename: str
    word_count: int
    estimated_duration_sec: int
    summary: str
    outline: List[str]
    script: str
    scenes: List[Scene]
    relevant_images: List[str]
