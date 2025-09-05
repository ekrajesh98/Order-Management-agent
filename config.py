from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelSettings(BaseModel):
    NAME: str
    API_KEY: str


class MCPServerSettings(BaseModel):
    URL: str


class FileSessionSettings(BaseModel):
    STORAGE_DIR: str = "./sessions"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )
    MODEL: ModelSettings
    MCP_SERVER: MCPServerSettings
    FILE_SESSION: FileSessionSettings = FileSessionSettings()


settings = Settings()
