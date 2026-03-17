from urllib.parse import urlparse

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_host: str = Field(default="localhost", alias="OLLAMA_HOST")
    ollama_port: int = Field(default=11434, alias="OLLAMA_PORT", ge=1, le=65535)
    proxy_host: str = Field(default="0.0.0.0", alias="PROXY_HOST")
    proxy_port: int = Field(default=8000, alias="PROXY_PORT", ge=1, le=65535)
    log_folder: str = Field(default="logs/ollama", alias="LOG_FOLDER")

    secret_key: str = Field(
        default="",
        alias="SECRET_KEY",
        min_length=8,
        max_length=64,
    )

    log_retention_days: int = Field(
        default=7,
        validation_alias=AliasChoices("LOG_RETAIN_DAYS", "LOG_RETENTION_DAYS"),
        ge=1,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def normalize_ollama_host(self) -> "Settings":
        host_value = self.ollama_host.strip()
        if not host_value:
            return self

        if "://" in host_value:
            parsed = urlparse(host_value)
            if parsed.hostname:
                self.ollama_host = parsed.hostname
            if parsed.port and self.ollama_port == 11434:
                self.ollama_port = parsed.port
            return self

        if ":" in host_value:
            host, sep, port = host_value.rpartition(":")
            if sep and host and port.isdigit():
                self.ollama_host = host
                if self.ollama_port == 11434:
                    self.ollama_port = int(port)

        return self


settings = Settings()