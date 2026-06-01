"""Shared configuration management using pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings


def find_env_file() -> Path | None:
    """Find .env file by walking up from CWD to project root."""
    current = Path.cwd()
    for _ in range(10):  # max 10 levels up
        env_path = current / ".env"
        if env_path.exists():
            return env_path
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/starter"

    model_config = {"env_file": str(find_env_file()) if find_env_file() else ".env"}


class SecuritySettings(BaseSettings):
    """Security configuration."""

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    model_config = {"env_file": str(find_env_file()) if find_env_file() else ".env"}


class AppSettings(BaseSettings):
    """Application settings aggregating all sub-settings."""

    db: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()

    # App ports
    web_backend_port: int = 8000
    admin_backend_port: int = 8001
    web_frontend_port: int = 5173
    admin_frontend_port: int = 5174

    model_config = {"env_file": str(find_env_file()) if find_env_file() else ".env"}


# Global settings instance
settings = AppSettings()
