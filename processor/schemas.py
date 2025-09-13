from typing import List, Optional
from pydantic import BaseModel, Field
from typing_extensions import Annotated

# Pydantic v2 style constraint
Sha256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class ImageInfo(BaseModel):
    sha256: Sha256 = Field(..., description="Exact SHA-256 of image bytes")
    phash: Optional[str] = Field(
        default=None, description="Optional perceptual hash for near-dup grouping")
    page: int = Field(..., ge=0, description="Zero-based page index")
    context_snippet: Annotated[str, Field(max_length=1200)] = ""
    image_path: Optional[str] = Field(
        None, description="Absolute or relative path to image file")


class ProcessingRequest(BaseModel):
    filename: Annotated[str, Field(min_length=1, max_length=256)]
    extracted_text: Annotated[str, Field(min_length=1)]
    images: List[ImageInfo] = Field(default_factory=list)


class ProcessingResponse(BaseModel):
    summary: str = ""
    relevant_images: Annotated[List[Sha256],
                               Field(min_length=0, max_length=24)]
    estimated_duration_sec: int = Field(..., ge=0)
    outline: List[str] = Field(default_factory=list)
