"""Request and response models for the posting API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.validation import MAX_MESSAGE_LENGTH, extract_cta_link


class PostRequest(BaseModel):
    """Incoming body for ``POST /posting``."""

    message: str = Field(
        ...,
        examples=[
            "Big news! Our new pricing plans are live — see them here https://example.com/pricing"
        ],
        description="Message to publish. Must be <=200 chars and contain exactly one CTA link.",
    )

    @field_validator("message")
    @classmethod
    def _validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be empty")
        if len(value) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"message must not exceed {MAX_MESSAGE_LENGTH} characters "
                f"(got {len(value)})"
            )
        # Enforces 'exactly one valid CTA link'; raises ValueError otherwise.
        extract_cta_link(value)
        return value


class PlatformResult(BaseModel):
    """Per-platform outcome included in the response."""

    platform: str
    status: Literal["success", "failed"]
    posted_url: str | None = None
    public_access: bool = False
    date: str | None = None  # YYYY-MM-DD (UTC), set only on success
    time: str | None = None  # HH:MM:SS (UTC), set only on success
    error: str | None = None


class PostResponse(BaseModel):
    """Top-level response: overall flag + one entry per platform."""

    success: bool  # True if at least one platform published successfully
    results: list[PlatformResult]
