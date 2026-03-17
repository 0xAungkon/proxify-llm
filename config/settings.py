from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
from pathlib import Path


class Settings(BaseSettings):
    ollama_host: str = Field(default="127.0.0.1", alias="OLLAMA_HOST")
    ollama_port: int = Field(default=11434, alias="OLLAMA_PORT", ge=1, le=65535)
    proxy_host: str = Field(default="0.0.0.0", alias="PROXY_HOST")
    proxy_port: int = Field(default=8000, alias="PROXY_PORT", ge=1, le=65535)
    log_folder: str = Field(default="logs/ollama", alias="LOG_FOLDER")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def llm_configs(self) -> dict:
        
        config_path = "config/llm_configs.json"
        if not config_path.exists():
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

settings = Settings()