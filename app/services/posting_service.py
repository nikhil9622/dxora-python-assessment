"""Concurrent, fault-isolated multi-platform posting.

Each platform runs as its own task. A task never raises: every failure mode
(not configured, platform error, network error, or an unexpected bug) is
caught and turned into a ``failed`` result, so one platform going down can
never stop the others from being posted to.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx

from app.platforms.base import Platform, PlatformError
from app.schemas import PlatformResult


async def _publish_one(
    client: httpx.AsyncClient, platform: Platform, message: str, link: str
) -> PlatformResult:
    if not platform.configured():
        return PlatformResult(
            platform=platform.name,
            status="failed",
            error="not configured: required environment variables are not set",
        )

    try:
        outcome = await platform.publish(client, message, link)
    except PlatformError as exc:
        return PlatformResult(
            platform=platform.name, status="failed", error=str(exc)
        )
    except httpx.HTTPError as exc:
        return PlatformResult(
            platform=platform.name,
            status="failed",
            error=f"network error: {exc!s}",
        )
    except Exception as exc:  # defensive: never let one platform break the rest
        return PlatformResult(
            platform=platform.name,
            status="failed",
            error=f"unexpected error: {exc!s}",
        )

    now = datetime.now(timezone.utc)
    return PlatformResult(
        platform=platform.name,
        status="success",
        posted_url=outcome.posted_url,
        public_access=outcome.public_access,
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%H:%M:%S"),
    )


async def publish_to_all(
    platforms: list[Platform],
    message: str,
    link: str,
    timeout: float,
) -> list[PlatformResult]:
    """Publish *message* to every platform concurrently and collect results."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [_publish_one(client, p, message, link) for p in platforms]
        return await asyncio.gather(*tasks)
