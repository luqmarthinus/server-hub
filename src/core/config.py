from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development", pattern="^(development|testing|production)$")
    JWT_SECRET: str = Field(min_length=32)
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = Field(default="mysql+aiomysql://fastapi_user:changeme@localhost:3306/fastapi_app")
    MYSQL_ROOT_PASSWORD: Optional[str] = None
    MYSQL_DATABASE: Optional[str] = None
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306

    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    CORS_ORIGINS_STR: str = Field(default="http://localhost:8000,http://localhost:3000", alias="CORS_ORIGINS")

    # (Optional: you can keep rate limiting and upload settings if needed)
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_PERIOD: int = 60
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIRECTORY: str = "./uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_prefix="",
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