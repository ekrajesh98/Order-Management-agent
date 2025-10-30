from enum import StrEnum
from functools import cached_property
from typing import Annotated

import boto3
from pydantic import AnyUrl, BaseModel, BeforeValidator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from strands.models import Model
from strands.models.bedrock import BedrockModel
from strands.models.openai import OpenAIModel
from strands.session.file_session_manager import FileSessionManager
from strands.session.s3_session_manager import S3SessionManager

from src.agent.custom_repository.sqlalchemy_repository import (
    SqlAlchemySessionManager,
)
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


class ModelProvider(StrEnum):
    OPENAI = "OPENAI"
    AWS = "AWS"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_low = value.lower()
            for member in cls:
                if member.value.lower() == val_low:
                    return member
        return None


class ModelSettings(BaseModel):
    NAME: str
    API_KEY: str | None = None
    PROVIDER: ModelProvider = ModelProvider.AWS

    @model_validator(mode="after")
    def validate_api_key(self):
        if self.PROVIDER == ModelProvider.OPENAI and not self.API_KEY:
            raise ValueError("API_KEY must be provided when PROVIDER is OPENAI")
        return self

    @property
    def model(self) -> Model:
        match self.PROVIDER:
            case ModelProvider.OPENAI:
                return OpenAIModel(
                    client_args={"api_key": self.API_KEY},
                    model_id=self.NAME,
                )
            case _:
                session = boto3.Session(
                    region_name="eu-west-2",
                )
                return BedrockModel(model_id=self.NAME, boto_session=session)


class MCPServerSettings(BaseModel):
    URL: str


class S3RepoSettings(BaseModel):
    BUCKET: str
    PREFIX: str = ""
    REGION_NAME: str | None = None


class FileRepoSettings(BaseModel):
    STORAGE_DIR: str


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


class RepositoryType(StrEnum):
    S3 = "S3"
    FILE = "file"
    DATABASE = "database"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_low = value.lower()
            for member in cls:
                if member.value.lower() == val_low:
                    return member
        return None


class SessionManagementRepository(BaseModel):
    TYPE: RepositoryType

    def get_session_manager(self, session_id: str):
        from src.config import settings

        match self.TYPE:
            case RepositoryType.S3:
                return S3SessionManager(
                    session_id=session_id,
                    bucket=settings.S3_SESSION_REPO.BUCKET,
                    prefix=settings.S3_SESSION_REPO.PREFIX,
                    region_name=settings.S3_SESSION_REPO.REGION_NAME,
                )
            case RepositoryType.FILE:
                return FileSessionManager(
                    session_id=session_id,
                    storage_dir=settings.FILE_SESSION_REPO.STORAGE_DIR,
                )
            case RepositoryType.DATABASE:
                return SqlAlchemySessionManager(session_id)
            case _:
                raise ValueError(f"Unsupported repository type: {self.TYPE}")


class DBSettings(BaseModel):
    HOST: str
    NAME: str
    PASSWORD: str
    PORT: int
    USER: str
    SQLALCHEMY_ECHO: bool = False

    @cached_property
    def URL(self) -> str:  # noqa: N802
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    @cached_property
    def URL_SYNC(self) -> str:
        """
        Sync SQLAlchemy database URL using psycopg2 driver.
        """
        return (
            f"postgresql+psycopg2://{self.USER}:"
            f"{self.PASSWORD}@{self.HOST}:"
            f"{self.PORT}/{self.NAME}"
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        extra="ignore",
    )
    PATH_PREFIX: str = "/api"

    MODEL: ModelSettings
    MCP_SERVER: MCPServerSettings

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str,
        BeforeValidator(parse_cors),
    ]
    LOG_LEVEL: str = "INFO"
    S3_SESSION_REPO: S3RepoSettings | None = None
    FILE_SESSION_REPO: FileRepoSettings | None = None
    REDIS: RedisSettings

    SENSITIVE_DATA_HANDLER: SensitiveDataHandlerSettings = (
        SensitiveDataHandlerSettings()
    )

    SESSION_REPOSITORY: SessionManagementRepository

    DB: DBSettings

    @model_validator(mode="after")
    def validate_session_repo_settings(self):
        if (
            self.SESSION_REPOSITORY.TYPE.lower() == RepositoryType.S3
            and self.S3_SESSION_REPO is None
        ):
            raise ValueError("S3_SESSION must be provided when REPOSITORY_TYPE is 'S3'")
        elif (
            self.SESSION_REPOSITORY.TYPE.lower() == RepositoryType.FILE
            and self.FILE_SESSION_REPO is None
        ):
            raise ValueError(
                "FILE_SESSION must be provided when REPOSITORY_TYPE is 'file'"
            )

        return self


settings = Settings()
