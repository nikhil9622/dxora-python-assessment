"""Message / CTA-link validation.

Rules enforced (from the assignment spec):
- Message must not exceed 200 characters.
- The message must contain exactly one CTA link.
- That link must be a syntactically valid http(s) URL.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

MAX_MESSAGE_LENGTH = 200

# Matches http:// or https:// URLs. Trailing sentence punctuation is trimmed
# separately so that "... visit https://example.com." yields a clean URL.
_URL_RE = re.compile(r"https?://[^\s<>\"'()]+", re.IGNORECASE)
_TRAILING_PUNCT = ".,;:!?”’"


def find_urls(text: str) -> list[str]:
    """Return every http(s) URL found in *text* (trailing punctuation trimmed)."""
    return [match.rstrip(_TRAILING_PUNCT) for match in _URL_RE.findall(text)]


def is_valid_url(url: str) -> bool:
    """A URL is valid when it has an http(s) scheme and a dotted host."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
        and "." in parsed.netloc
    )


def extract_cta_link(message: str) -> str:
    """Return the single CTA link in *message*.

    Raises ``ValueError`` if there is not exactly one link, or if that link is
    not a valid URL. The raised message is surfaced to the API caller as a 422.
    """
    urls = find_urls(message)
    if not urls:
        raise ValueError("message must contain exactly one CTA link; found none")
    if len(urls) > 1:
        raise ValueError(
            f"message must contain exactly one CTA link; found {len(urls)}"
        )
    url = urls[0]
    if not is_valid_url(url):
        raise ValueError(f"CTA link is not a valid URL: {url!r}")
    return url
