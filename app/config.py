"""Application settings, loaded from environment variables / a local .env file.

Every credential is optional: when a platform's variables are absent the app
still starts and that platform reports an honest ``not configured`` failure
instead of being silently skipped or faked.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Mastodon -------------------------------------------------------
    mastodon_instance_url: str = "https://mastodon.social"
    mastodon_access_token: str | None = None

    # --- Bluesky (AT Protocol) -----------------------------------------
    bluesky_identifier: str | None = None  # handle, e.g. you.bsky.social
    bluesky_app_password: str | None = None  # app password, NOT your login password
    bluesky_service_url: str = "https://bsky.social"

    # --- Telegram ------------------------------------------------------
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None  # @channelusername or numeric id

    # --- Discord -------------------------------------------------------
    discord_webhook_url: str | None = None

    # --- DEV.to --------------------------------------------------------
    devto_api_key: str | None = None

    # --- Networking ----------------------------------------------------
    http_timeout_seconds: float = 15.0


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (overridable in tests via dependency_overrides)."""
    return Settings()
