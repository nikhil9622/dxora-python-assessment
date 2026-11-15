"""Assembles the list of platform adapters from settings.

To add a platform, implement the ``Platform`` protocol in a new module and
append it here — no other code needs to change.
"""

from __future__ import annotations

from app.config import Settings
from app.platforms.base import Platform
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.devto import DevToPlatform
from app.platforms.discord import DiscordPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.telegram import TelegramPlatform


def build_platforms(settings: Settings) -> list[Platform]:
    return [
        MastodonPlatform(
            settings.mastodon_instance_url, settings.mastodon_access_token
        ),
        BlueskyPlatform(
            settings.bluesky_identifier,
            settings.bluesky_app_password,
            settings.bluesky_service_url,
        ),
        TelegramPlatform(settings.telegram_bot_token, settings.telegram_chat_id),
        DiscordPlatform(settings.discord_webhook_url),
        DevToPlatform(settings.devto_api_key),
    ]
