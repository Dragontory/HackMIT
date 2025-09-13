from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field


class Settings(BaseSettings):
    app_name: str = "AI Content Processing API"
    app_version: str = "1.4.0"

    host: str = "0.0.0.0"
    port: int = 8001

    # LLM
    llm_base_url: AnyHttpUrl = Field(default="http://127.0.0.1:8009/v1")
    llm_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    llm_temperature: float = 0.2
    llm_timeout_s: float = 90.0
    llm_max_tokens: int = 1024
    lora_name: str | None = None  # e.g., "mylora" when serving adapters

    clip_model_name: str = "ViT-B-32"
    clip_pretrained: str = "openai"
    clip_threshold: float = 0.20
    clip_topk: int = 24

    # Limits (able ro be overridden by policy.py)
    max_json_chars: int = 20000
    max_relevant_images: int = 24
    words_per_minute: int = 130
    seconds_per_image: int = 7
    max_image_bonus: int = 10

    # Cleaning heuristics
    header_footer_hit_ratio: float = 0.5

    # Default policy mode: "static" | "adaptive" | "learned"
    policy_mode: str = "adaptive"

    # Where parser saves images (used if resolving sha256 -> path)
    image_folder: str = "temp_uploads"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
