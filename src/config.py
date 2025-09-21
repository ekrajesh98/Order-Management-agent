from functools import cached_property
from typing import Annotated

from pydantic import AnyUrl, BaseModel, BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.sensitive_data_handler.adapters.presidio_analyzer import PresidioAnalyzer
from src.sensitive_data_handler.adapters.presidio_anonymizer import PresidioAnonymizer
from src.sensitive_data_handler.adapters.redis_cache import RedisSensitiveDataCache
from src.sensitive_data_handler.ports.data_analyzer_port import SensitiveDataAnalyzerABC
from src.sensitive_data_handler.ports.data_anonymizer_port import (
    SensitiveDataAnonymizerABC,
)
from src.sensitive_data_handler.ports.data_cache_port import SensitiveDataCacheABC


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


class RedisSettings(BaseModel):
    HOST: str
    PORT: int
    PASSWORD: str | None = None
    USE_TLS: bool = True

    @cached_property
    def URL(self) -> str:  # noqa: N802
        scheme = "rediss" if self.USE_TLS else "redis"
        auth_part = f":{self.PASSWORD}@" if self.PASSWORD else ""
        return f"{scheme}://{auth_part}{self.HOST}:{self.PORT}"


class SensitiveDataHandlerSettings(BaseModel):
    MASK_SENSITIVE_DATA: bool = True
    DATA_CACHE_EXPIRY_SECONDS: int = 28800  # 8 hours

    @cached_property
    def ANALYZER(self) -> SensitiveDataAnalyzerABC:
        return PresidioAnalyzer()

    @cached_property
    def ANONYMIZER(self) -> SensitiveDataAnonymizerABC:
        return PresidioAnonymizer()

    @cached_property
    def DATA_CACHE(self) -> SensitiveDataCacheABC:
        from src.config import settings

        return RedisSensitiveDataCache(
            settings.REDIS.URL, self.DATA_CACHE_EXPIRY_SECONDS
        )


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
    REDIS: RedisSettings

    SENSITIVE_DATA_HANDLER: SensitiveDataHandlerSettings = (
        SensitiveDataHandlerSettings()
    )


settings = Settings()
