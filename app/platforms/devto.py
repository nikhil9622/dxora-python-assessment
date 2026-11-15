"""DEV.to adapter (Forem API).

  POST https://dev.to/api/articles   (api-key header)
Publishes a short article; a title is derived from the message because the
Forem API requires one.
Docs: https://developers.forem.com/api/v1#tag/articles/operation/createArticle
"""

from __future__ import annotations

import httpx

from app.platforms.base import PlatformError, PublishOutcome
from app.validation import _URL_RE


def _derive_title(message: str) -> str:
    """Build a title from the message text (URL stripped, first ~12 words)."""
    text = _URL_RE.sub("", message).strip()
    words = text.split()
    title = " ".join(words[:12]).strip(" -–—:.,")
    return title or "New update"


class DevToPlatform:
    name = "devto"

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    def configured(self) -> bool:
        return bool(self._api_key)

    async def publish(
        self, client: httpx.AsyncClient, message: str, link: str
    ) -> PublishOutcome:
        resp = await client.post(
            "https://dev.to/api/articles",
            headers={"api-key": self._api_key, "Content-Type": "application/json"},
            json={
                "article": {
                    "title": _derive_title(message),
                    "body_markdown": message,
                    "published": True,
                }
            },
        )
        if resp.status_code >= 400:
            raise PlatformError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return PublishOutcome(posted_url=data.get("url"), public_access=True)
