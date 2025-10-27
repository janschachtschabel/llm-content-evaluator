"""Configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4.1-mini", env="OPENAI_MODEL")
    openai_base_url: str = Field("https://api.openai.com/v1", env="OPENAI_BASE_URL")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    schemes_dir: str = Field("schemes", env="SCHEMES_DIR")
    
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
