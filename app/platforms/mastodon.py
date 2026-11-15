"""Mastodon adapter.

Posts a status via the Mastodon REST API:
  POST {instance}/api/v1/statuses   (Bearer token)
Docs: https://docs.joinmastodon.org/methods/statuses/#create
"""

from __future__ import annotations

import httpx

from app.platforms.base import PlatformError, PublishOutcome


class MastodonPlatform:
    name = "mastodon"

    def __init__(self, instance_url: str, access_token: str | None) -> None:
        self._instance = instance_url.rstrip("/")
        self._token = access_token

    def configured(self) -> bool:
        return bool(self._token)

    async def publish(
        self, client: httpx.AsyncClient, message: str, link: str
    ) -> PublishOutcome:
        resp = await client.post(
            f"{self._instance}/api/v1/statuses",
            headers={"Authorization": f"Bearer {self._token}"},
            data={"status": message},
        )
        if resp.status_code >= 400:
            raise PlatformError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return PublishOutcome(
            posted_url=data.get("url"),
            public_access=data.get("visibility") == "public",
        )
