"""Bluesky adapter (AT Protocol).

Two calls:
  1. com.atproto.server.createSession  -> accessJwt + did
  2. com.atproto.repo.createRecord     -> create an app.bsky.feed.post
A richtext facet is attached so the CTA link is clickable.
Docs: https://docs.bsky.app/docs/api/com-atproto-repo-create-record
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.platforms.base import PlatformError, PublishOutcome


def _link_facet(text: str, link: str) -> dict | None:
    """Byte-indexed richtext facet marking *link* inside *text*."""
    idx = text.find(link)
    if idx < 0:
        return None
    byte_start = len(text[:idx].encode("utf-8"))
    byte_end = byte_start + len(link.encode("utf-8"))
    return {
        "index": {"byteStart": byte_start, "byteEnd": byte_end},
        "features": [{"$type": "app.bsky.richtext.facet#link", "uri": link}],
    }


class BlueskyPlatform:
    name = "bluesky"

    def __init__(
        self,
        identifier: str | None,
        app_password: str | None,
        service_url: str = "https://bsky.social",
    ) -> None:
        self._identifier = identifier
        self._password = app_password
        self._service = service_url.rstrip("/")

    def configured(self) -> bool:
        return bool(self._identifier and self._password)

    async def publish(
        self, client: httpx.AsyncClient, message: str, link: str
    ) -> PublishOutcome:
        session = await client.post(
            f"{self._service}/xrpc/com.atproto.server.createSession",
            json={"identifier": self._identifier, "password": self._password},
        )
        if session.status_code >= 400:
            raise PlatformError(
                f"auth failed HTTP {session.status_code}: {session.text[:200]}"
            )
        sess = session.json()
        jwt = sess["accessJwt"]
        did = sess["did"]
        handle = sess.get("handle", did)

        record: dict = {
            "$type": "app.bsky.feed.post",
            "text": message,
            "createdAt": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        }
        facet = _link_facet(message, link)
        if facet:
            record["facets"] = [facet]

        resp = await client.post(
            f"{self._service}/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {jwt}"},
            json={
                "repo": did,
                "collection": "app.bsky.feed.post",
                "record": record,
            },
        )
        if resp.status_code >= 400:
            raise PlatformError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        uri = data.get("uri", "")
        rkey = uri.rsplit("/", 1)[-1] if uri else ""
        posted_url = (
            f"https://bsky.app/profile/{handle}/post/{rkey}" if rkey else None
        )
        return PublishOutcome(posted_url=posted_url, public_access=True)
