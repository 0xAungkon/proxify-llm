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
    log_retention_days: int = Field(default=10, alias="LOG_RETENTION_DAYS", ge=1)

settings = Settings()