# Automated Multi-Platform Posting System

A FastAPI service that validates a short message with a single call-to-action
link and publishes it **concurrently to five third-party platforms**, returning
an isolated success/failure result for each one.

> Built for the Dxora Technologies Python practical test. Stack: Python 3.11+,
> FastAPI, Uvicorn, Pydantic, HTTPX.

---

## Contents
- [Features](#features)
- [How it works](#how-it-works)
- [Quick start](#quick-start)
- [Platform credentials](#platform-credentials)
- [API reference](#api-reference)
- [Validation rules](#validation-rules)
- [Sample requests & responses](#sample-requests--responses)
- [Design notes](#design-notes)
- [Testing](#testing)
- [Project structure](#project-structure)

---

## Features

- **Single endpoint:** `POST /posting` on port `4000`.
- **Strict validation:** message ≤ 200 characters, exactly one CTA link, valid
  http(s) URL — enforced with Pydantic, returning `422` with a clear message.
- **Five real integrations:** Mastodon, Bluesky, Telegram, Discord, DEV.to —
  each hitting the platform's official API over HTTPX.
- **Fault isolation:** every platform posts concurrently (`asyncio.gather`); one
  platform failing never stops the others.
- **No fabricated results:** a platform without credentials returns an honest
  `failed` / `not configured` result. Nothing is ever faked as a success.
- **Self-documenting:** OpenAPI docs at `/docs`.

## How it works

```
                         POST /posting  {message}
                                 │
                         ┌───────▼────────┐
                         │  Pydantic       │  ≤200 chars · exactly one
                         │  validation     │  valid CTA link  → 422 on failure
                         └───────┬────────┘
                                 │  message + extracted link
                         ┌───────▼────────┐
                         │ posting_service │  asyncio.gather — each task is
                         │  (fan-out)      │  independently try/except-wrapped
                         └─┬───┬───┬───┬──┬┘
          ┌───────────────┘   │   │   │  └───────────────┐
      ┌───▼───┐  ┌────────▼┐ ┌▼──────┐ ┌▼──────┐  ┌──────▼─┐
      │Mastodon│ │ Bluesky │ │Telegram│ │Discord│  │ DEV.to │
      └───┬───┘  └────┬────┘ └───┬───┘ └───┬───┘  └────┬───┘
          └───────────┴──────────┴─────────┴───────────┘
                                 │  list[PlatformResult]
                         ┌───────▼────────┐
                         │ {success,results}│
                         └─────────────────┘
```

Each platform is a small adapter implementing a common `Platform` protocol
(composition, not inheritance). Adding a platform = one new module + one line in
`app/platforms/registry.py`.

## Quick start

Requires Python 3.11+.

```bash
# 1. Install dependencies
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure credentials (optional to start — see below)
cp .env.example .env        # Windows: copy .env.example .env
# edit .env and fill in the platforms you want

# 3. Run
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Then open the interactive docs at **http://localhost:4000/docs**.

The app **starts and responds even with no credentials** — every platform simply
reports `not configured`. Fill in `.env` to see real posts.

> Using [uv](https://docs.astral.sh/uv/)? `uv run uvicorn app.main:app --port 4000` works too.

## Platform credentials

All five use free, self-serve developer credentials — no business approval or
paid tier. Put them in `.env` (see `.env.example`).

| Platform | Variables | Where to get it |
|----------|-----------|-----------------|
| **Mastodon** | `MASTODON_INSTANCE_URL`, `MASTODON_ACCESS_TOKEN` | On your instance: Preferences → Development → New application → copy the access token. |
| **Bluesky** | `BLUESKY_IDENTIFIER`, `BLUESKY_APP_PASSWORD` | Settings → App Passwords → add one. Use the **app password**, not your login password. Identifier is your handle (`you.bsky.social`). |
| **Telegram** | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Create a bot via [@BotFather](https://t.me/BotFather) → token. Add the bot as an admin to your channel; `TELEGRAM_CHAT_ID` is `@yourchannel` (public) or a numeric id. |
| **Discord** | `DISCORD_WEBHOOK_URL` | Channel → Edit → Integrations → Webhooks → New Webhook → Copy URL. |
| **DEV.to** | `DEVTO_API_KEY` | Settings → Extensions → DEV Community API Keys → Generate. |

> **Never commit `.env`.** It is git-ignored; only `.env.example` is tracked.

## API reference

### `POST /posting`

Request body:

```json
{ "message": "Big news! Our new pricing plans are live — see them here https://example.com/pricing" }
```

Response `200 OK`:

```json
{
  "success": true,
  "results": [
    {
      "platform": "mastodon",
      "status": "success",
      "posted_url": "https://mastodon.social/@yourname/111871234567890123",
      "public_access": true,
      "date": "2026-11-15",
      "time": "10:30:00",
      "error": null
    }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `success` | `true` if **at least one** platform published successfully. |
| `results[].platform` | Platform name. |
| `results[].status` | `success` or `failed`. |
| `results[].posted_url` | Public URL of the published post (may be `null` where the platform exposes no public permalink, e.g. a Discord webhook). |
| `results[].public_access` | Whether the post is publicly viewable. |
| `results[].date` / `time` | UTC date (`YYYY-MM-DD`) and time (`HH:MM:SS`), set only on success. |
| `results[].error` | Failure detail, else `null`. |

### `GET /health`
Liveness check → `{"status": "ok"}`.

### Other
- `GET /` → redirects to `/docs`.
- `GET /docs` → Swagger UI. `GET /openapi.json` → schema.

## Validation rules

Invalid input returns **`422 Unprocessable Entity`** with a descriptive message:

- Message must be non-empty and **≤ 200 characters**.
- Message must contain **exactly one** CTA link (zero or two+ are rejected).
- That link must be a valid `http`/`https` URL with a dotted host.

Example error:

```json
{ "detail": [ { "loc": ["body","message"],
  "msg": "Value error, message must contain exactly one CTA link; found 2",
  "type": "value_error" } ] }
```

## Sample requests & responses

Ready-made examples live in [`samples/`](samples/):
- `request.json` — a valid request body.
- `response_success.json` — a mixed real response (some succeed, one fails independently).
- `response_no_credentials.json` — the out-of-the-box response with no `.env`.

Try it with curl:

```bash
curl -s -X POST http://localhost:4000/posting \
  -H "Content-Type: application/json" \
  -d @samples/request.json | python -m json.tool
```

> **Screenshots / logs:** add your own run screenshots to `docs/` (e.g. the
> `/docs` page and a real multi-platform response). See `docs/README.md`.

## Design notes

- **Fault isolation:** `posting_service._publish_one` wraps every adapter call in
  `try/except` (platform error, network error, unexpected error) and always
  returns a `PlatformResult`, so `asyncio.gather` never short-circuits.
- **Honest failures over fakes:** unconfigured platforms fail with
  `not configured` rather than returning fabricated success — matching the spec's
  intent and keeping results trustworthy.
- **Composition:** adapters share a `Platform` protocol, not a base class; the
  registry assembles them, so the service and API never change when platforms do.
- **Credentials via env:** loaded through `pydantic-settings`; all optional.
- **Timestamps:** UTC, ISO-formatted, recorded at the moment each post succeeds.

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

Covers validation (length, link count, URL validity → 422), the no-credentials
path (all platforms fail honestly), and a mocked Mastodon success proving the
other platforms fail independently (`respx` stubs the HTTP call — no real
network, no real tokens).

## Project structure

```
app/
  main.py                 FastAPI app + POST /posting, /health
  config.py               Settings (env vars) via pydantic-settings
  schemas.py              PostRequest / PlatformResult / PostResponse
  validation.py           CTA-link extraction + URL validation
  platforms/
    base.py               Platform protocol, PublishOutcome, PlatformError
    mastodon.py           \
    bluesky.py             |
    telegram.py            > one adapter per platform
    discord.py             |
    devto.py              /
    registry.py           Assembles adapters from settings
  services/
    posting_service.py    Concurrent, fault-isolated fan-out
tests/
  test_validation.py
  test_api.py
samples/                  Example request & responses
.env.example              Credential template (copy to .env)
requirements.txt          Runtime deps
requirements-dev.txt      + test deps
```

## Mapping to the evaluation criteria

| Criterion | Where |
|-----------|-------|
| FastAPI implementation & API structure | `app/main.py`, layered `app/` package |
| Input validation | `app/validation.py`, `app/schemas.py` (→ 422) |
| Platform research & API integration | `app/platforms/*.py` (5 real APIs) |
| Automatic multi-platform posting | `app/services/posting_service.py` (`asyncio.gather`) |
| Error handling & response management | per-task try/except, `not configured`, `PostResponse` |
| Code quality & documentation | typed, composition-based, this README, tests |
