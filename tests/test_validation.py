"""Unit tests for message / CTA-link validation."""

from __future__ import annotations

import pytest

from app.validation import extract_cta_link, find_urls, is_valid_url


def test_single_valid_link_is_extracted():
    msg = "Check our launch here https://example.com/launch"
    assert extract_cta_link(msg) == "https://example.com/launch"


def test_trailing_punctuation_is_trimmed():
    assert find_urls("visit https://example.com.") == ["https://example.com"]


def test_no_link_raises():
    with pytest.raises(ValueError, match="found none"):
        extract_cta_link("no link here at all")


def test_two_links_raise():
    with pytest.raises(ValueError, match="found 2"):
        extract_cta_link("a https://a.com and b https://b.com")


def test_invalid_url_raises():
    # http://localhost has no dotted host -> not a valid public CTA link.
    with pytest.raises(ValueError, match="not a valid URL"):
        extract_cta_link("broken http://localhost")


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://example.com", True),
        ("http://a.b.co/path?x=1", True),
        ("ftp://example.com", False),
        ("https://nodot", False),
        ("not a url", False),
    ],
)
def test_is_valid_url(url, expected):
    assert is_valid_url(url) is expected
