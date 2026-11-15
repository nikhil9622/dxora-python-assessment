"""Telegram adapter (Bot API).

  POST https://api.telegram.org/bot{token}/sendMessage
A public t.me link is returned only when the target chat is a public channel
with a username; otherwise the post succeeds but is not publicly accessible.
Docs: https://core.telegram.org/bots/api#sendmessage
"""

from __future__ import annotations

import httpx

from app.platforms.base import PlatformError, PublishOutcome


class TelegramPlatform:
    name = "telegram"

    def __init__(self, bot_token: str | None, chat_id: str | None) -> None:
        self._token = bot_token
        self._chat_id = chat_id

    def configured(self) -> bool:
        return bool(self._token and self._chat_id)

    async def publish(
        self, client: httpx.AsyncClient, message: str, link: str
    ) -> PublishOutcome:
        resp = await client.post(
            f"https://api.telegram.org/bot{self._token}/sendMessage",
            json={"chat_id": self._chat_id, "text": message},
        )
        if resp.status_code >= 400:
            raise PlatformError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("ok"):
            raise PlatformError(f"API error: {str(data)[:200]}")
        result = data.get("result", {})
        chat = result.get("chat", {})
        message_id = result.get("message_id")
        username = chat.get("username")
        if username and message_id:
            return PublishOutcome(
                posted_url=f"https://t.me/{username}/{message_id}",
                public_access=True,
            )
        return PublishOutcome(posted_url=None, public_access=False)
