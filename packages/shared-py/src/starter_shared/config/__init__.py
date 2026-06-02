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


_ENV_FILE = str(find_env_file()) if find_env_file() else ".env"


class DatabaseSettings(BaseSettings):
    """Database configuration with component-based connection.

    Set individual DB_* env vars, or use DATABASE_URL to override everything.
    Table prefix is automatically applied to all SQLAlchemy models via Base.
    """

    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "emptie"
    db_password: str = "123456"
    db_name: str = "starter"
    db_table_prefix: str = ""

    # Backward compatibility: if set, overrides the component-based URL
    database_url: str = ""

    model_config = {"env_file": _ENV_FILE, "extra": "ignore"}

    def get_database_url(self, db_name_override: str | None = None) -> str:
        """Construct asyncpg connection URL from components.

        Args:
            db_name_override: Use a different database name (e.g., "starter_test").
        """
        name = db_name_override or self.db_name
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{name}"
        )

    @property
    def effective_database_url(self) -> str:
        """Return DATABASE_URL if explicitly set, otherwise construct from components."""
        if self.database_url:
            return self.database_url
        return self.get_database_url()


class SecuritySettings(BaseSettings):
    """Security configuration."""

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    password_reset_expire_hours: int = 1
    algorithm: str = "HS256"

    model_config = {"env_file": _ENV_FILE, "extra": "ignore"}


class SmtpSettings(BaseSettings):
    """SMTP configuration for email sending.

    If smtp_host is empty, the email service falls back to console output
    (developer-friendly: prints the reset token / link to stdout).
    """

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"
    smtp_use_tls: bool = True

    model_config = {"env_file": _ENV_FILE, "extra": "ignore"}

    @property
    def is_configured(self) -> bool:
        """Return True when SMTP is fully configured for real email sending."""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)


class AppSettings(BaseSettings):
    """Application settings aggregating all sub-settings."""

    db: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()
    smtp: SmtpSettings = SmtpSettings()

    # App ports
    web_backend_port: int = 8000
    admin_backend_port: int = 8001
    web_frontend_port: int = 5173
    admin_frontend_port: int = 5174

    # Frontend base URL used for password reset links and similar
    frontend_base_url: str = "http://localhost:5173"

    model_config = {"env_file": _ENV_FILE, "extra": "ignore"}


# Global settings instance
settings = AppSettings()
