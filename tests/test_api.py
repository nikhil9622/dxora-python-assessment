"""API-level tests for POST /posting.

Covers:
- validation failures return 422,
- the out-of-the-box 'no credentials' path (all platforms fail honestly),
- a real success path for one platform with its HTTP call mocked (respx),
  proving per-platform fault isolation.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app, get_settings

VALID_MESSAGE = "Our new plans are live, see them here https://example.com/pricing"


def _client(settings: Settings) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# Validation                                                                  #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "message",
    [
        "",  # empty
        "no cta link present here",  # zero links
        "two https://a.com links https://b.com here",  # two links
        "x" * 190 + " https://example.com/very/long/extra/padding",  # > 200 chars
    ],
)
def test_invalid_messages_return_422(message):
    client = _client(Settings(_env_file=None))
    resp = client.post("/posting", json={"message": message})
    assert resp.status_code == 422


def test_missing_field_returns_422():
    client = _client(Settings(_env_file=None))
    assert client.post("/posting", json={}).status_code == 422


# --------------------------------------------------------------------------- #
# No credentials: every platform fails honestly, nothing is faked              #
# --------------------------------------------------------------------------- #
def test_no_credentials_all_failed_not_configured():
    client = _client(Settings(_env_file=None))
    resp = client.post("/posting", json={"message": VALID_MESSAGE})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert len(body["results"]) == 5
    for result in body["results"]:
        assert result["status"] == "failed"
        assert "not configured" in result["error"]
        assert result["posted_url"] is None
        assert result["date"] is None and result["time"] is None


# --------------------------------------------------------------------------- #
# Success path for one platform (Mastodon), others left unconfigured          #
# --------------------------------------------------------------------------- #
@respx.mock
def test_one_platform_succeeds_others_isolated():
    settings = Settings(
        _env_file=None,
        mastodon_instance_url="https://mastodon.social",
        mastodon_access_token="test-token",
    )
    route = respx.post("https://mastodon.social/api/v1/statuses").mock(
        return_value=httpx.Response(
            200,
            json={
                "url": "https://mastodon.social/@tester/42",
                "visibility": "public",
            },
        )
    )
    client = _client(settings)
    resp = client.post("/posting", json={"message": VALID_MESSAGE})
    assert resp.status_code == 200
    body = resp.json()
    assert route.called
    assert body["success"] is True

    results = {r["platform"]: r for r in body["results"]}
    mastodon = results["mastodon"]
    assert mastodon["status"] == "success"
    assert mastodon["posted_url"] == "https://mastodon.social/@tester/42"
    assert mastodon["public_access"] is True
    assert mastodon["date"] and mastodon["time"]

    # The other four remain unconfigured and fail independently.
    assert sum(r["status"] == "failed" for r in body["results"]) == 4
