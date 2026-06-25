from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    agent_model: str = Field(default="", alias="AGENT_MODEL")
    tool_server_url: str = Field(
        default="http://localhost:8080",
        alias="TOOL_SERVER_URL",
    )
    tool_server_token: SecretStr = Field(
        default=SecretStr("local-dev-token"),
        alias="TOOL_SERVER_TOKEN",
    )
    agent_max_iterations: int = Field(
        default=5,
        ge=1,
        le=20,
        alias="AGENT_MAX_ITERATIONS",
    )
    tool_timeout_seconds: float = Field(
        default=5,
        gt=0,
        le=60,
        alias="TOOL_TIMEOUT_SECONDS",
    )
    request_timeout_seconds: float = Field(
        default=30,
        gt=0,
        le=300,
        alias="REQUEST_TIMEOUT_SECONDS",
    )
    max_tool_output_chars: int = Field(
        default=8000,
        ge=256,
        le=100_000,
        alias="MAX_TOOL_OUTPUT_CHARS",
    )
    trace_directory: Path = Field(
        default=Path("../var/traces"),
        alias="TRACE_DIRECTORY",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="CORS_ORIGINS",
    )
