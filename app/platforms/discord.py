"""Discord adapter (incoming webhook).

  POST {webhook_url}?wait=true   -> returns the created message object
Webhook messages live inside a server channel, so they are not publicly
accessible without membership; public_access is reported as False.
Docs: https://discord.com/developers/docs/resources/webhook#execute-webhook
"""

from __future__ import annotations

import httpx

from app.platforms.base import PlatformError, PublishOutcome


class DiscordPlatform:
    name = "discord"

    def __init__(self, webhook_url: str | None) -> None:
        self._webhook_url = webhook_url

    def configured(self) -> bool:
        return bool(self._webhook_url)

    async def publish(
        self, client: httpx.AsyncClient, message: str, link: str
    ) -> PublishOutcome:
        resp = await client.post(
            self._webhook_url,
            params={"wait": "true"},
            json={"content": message},
        )
        if resp.status_code >= 400:
            raise PlatformError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        # A webhook post is delivered to a private server channel; there is no
        # public permalink reachable without membership.
        return PublishOutcome(posted_url=None, public_access=False)
