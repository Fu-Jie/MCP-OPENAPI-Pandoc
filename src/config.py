"""Configuration management using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # JWT settings
    jwt_secret_key: str = "development-secret-key-change-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # Conversion settings
    max_file_size_mb: int = 50
    conversion_timeout: int = 60  # seconds

    # Service info
    service_name: str = "pandoc-bridge"
    service_version: str = "1.0.0"

    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
