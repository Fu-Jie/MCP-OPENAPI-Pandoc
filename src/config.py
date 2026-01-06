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

    # API Key settings
    # Format: "sk-xxx:2025-12-31,sk-yyy:2026-06-30" or "sk-xxx,sk-yyy" (no expiry)
    api_keys: str = ""

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

    def get_api_keys(self) -> dict[str, str | None]:
        """Get dict of API keys with their expiry dates.
        
        Returns:
            Dict mapping API key to expiry date string (YYYY-MM-DD) or None
        """
        if not self.api_keys:
            return {}
        
        result: dict[str, str | None] = {}
        for item in self.api_keys.split(","):
            item = item.strip()
            if not item:
                continue
            if ":" in item:
                key, expiry = item.split(":", 1)
                result[key.strip()] = expiry.strip()
            else:
                result[item] = None
        return result


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
