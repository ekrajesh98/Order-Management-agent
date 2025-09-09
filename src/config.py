from typing import Annotated

from pydantic import AnyUrl, BaseModel, BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: str | list[str]) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v

    raise ValueError(v)


class ModelSettings(BaseModel):
    NAME: str
    API_KEY: str


class MCPServerSettings(BaseModel):
    URL: str


class S3SessionSettings(BaseModel):
    BUCKET: str
    PREFIX: str = ""
    REGION_NAME: str | None = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        extra="ignore",
    )
    MODEL: ModelSettings
    MCP_SERVER: MCPServerSettings

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str,
        BeforeValidator(parse_cors),
    ]
    LOG_LEVEL: str = "INFO"
    S3_SESSION: S3SessionSettings


settings = Settings()
