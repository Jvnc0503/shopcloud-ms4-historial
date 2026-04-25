from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development", description="Entorno actual")
    DEBUG: bool = Field(default=False, description="Activa logs detallados")

    MS1_URL: str = Field(default="http://ms1-productos:8001", description="URL base de MS1")
    MS2_URL: str = Field(default="http://ms2-pedidos:8002", description="URL base de MS2")
    MS3_URL: str = Field(default="http://ms3-usuarios:8003", description="URL base de MS3")
    REQUEST_TIMEOUT_SECONDS: float = Field(default=10.0, ge=0.1, description="Timeout para llamadas HTTP")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
