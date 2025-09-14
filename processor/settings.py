from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # allow ANTHROPIC_* env vars without crashing
    )

    app_name: str = "AI Content Processing API"
    app_version: str = "3.0.0"
    host: str = "0.0.0.0"
    port: int = 8011

    anthropic_api_key: str | None = None
    anthropic_base_url: str = Field(default="https://api.anthropic.com")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20240620")
    anthropic_version: str = Field(default="2023-06-01")

    llm_timeout_s: float = 60.0
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2000  # client can compute a lower dynamic budget per request

    max_json_chars: int = 20_000
    max_relevant_images: int = 24
    words_per_minute: int = 115
    seconds_per_image: int = 8
    max_image_bonus: int = 24
    min_floor_sec: int = 20

    image_folder: str = "temp_uploads"


settings = Settings()
