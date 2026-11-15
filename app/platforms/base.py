"""Shared contract for platform adapters.

Adapters are plain objects assembled by the registry (composition over
inheritance): each one carries its own credential slice and implements the
``Platform`` protocol. A failed publish raises ``PlatformError`` (or any
exception) which the posting service converts into an isolated ``failed``
result without affecting the other platforms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import httpx


@dataclass(slots=True)
class PublishOutcome:
    """Successful publish details returned by an adapter."""

    posted_url: str | None
    public_access: bool


class PlatformError(Exception):
    """Raised by an adapter when publishing fails for a known reason."""


@runtime_checkable
class Platform(Protocol):
    name: str

    def configured(self) -> bool:
        """True when all required credentials for this platform are present."""
        ...

    async def publish(
        self, client: httpx.AsyncClient, message: str, link: str
    ) -> PublishOutcome:
        """Publish *message* (which contains *link*) and return the outcome."""
        ...
