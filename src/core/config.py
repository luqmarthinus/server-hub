from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development", pattern="^(development|testing|production)$")
    JWT_SECRET: str = Field(min_length=32)
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = Field(default="mysql+aiomysql://fastapi_user:changeme@localhost:3306/fastapi_app")

    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # CORS origins as comma-separated string from environment
    CORS_ORIGINS_STR: str = Field(default="http://localhost:8000,http://localhost:3000", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def CORS_ORIGINS(self) -> List[str]:
        if not self.CORS_ORIGINS_STR:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
