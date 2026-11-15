"""FastAPI application entry point.

Run:
    uvicorn app.main:app --host 0.0.0.0 --port 4000
Interactive docs: http://localhost:4000/docs
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

from app.config import Settings, get_settings
from app.platforms.registry import build_platforms
from app.schemas import PostRequest, PostResponse
from app.services.posting_service import publish_to_all
from app.validation import extract_cta_link

app = FastAPI(
    title="Automated Multi-Platform Posting System",
    version="1.0.0",
    description=(
        "Publishes a short message (<=200 chars, exactly one CTA link) to five "
        "third-party platforms concurrently, with isolated per-platform results."
    ),
)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/posting", response_model=PostResponse, tags=["posting"])
async def posting(
    payload: PostRequest,
    settings: Settings = Depends(get_settings),
) -> PostResponse:
    # Message is already validated by PostRequest; this re-extraction just hands
    # the concrete CTA link to the adapters (idempotent, cannot raise here).
    link = extract_cta_link(payload.message)
    platforms = build_platforms(settings)
    results = await publish_to_all(
        platforms, payload.message, link, settings.http_timeout_seconds
    )
    success = any(result.status == "success" for result in results)
    return PostResponse(success=success, results=results)
