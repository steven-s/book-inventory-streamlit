from __future__ import annotations

import html
import re

import requests

from book_inventory.metadata.http import SESSION, TIMEOUT_SECONDS
from book_inventory.metadata.models import BookMetadata

BASE_URL = "https://isbnsearch.org"


class ISBNsearchProviderError(RuntimeError):
    pass


def lookup(isbn: str) -> BookMetadata:
    url = f"{BASE_URL}/isbn/{isbn}"
    try:
        response = SESSION.get(url, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise ISBNsearchProviderError(f"Could not reach ISBNsearch: {exc}") from exc
    if response.status_code == 404:
        raise ISBNsearchProviderError("No ISBNsearch record was found for this ISBN.")
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise ISBNsearchProviderError(f"ISBNsearch returned HTTP {response.status_code}.") from exc

    page = response.text
    if _is_verification_page(page):
        raise ISBNsearchProviderError("ISBNsearch returned a human verification page.")

    title = _extract_h1(page)
    fields = _extract_isbnsearch_fields(page)
    if not title:
        raise ISBNsearchProviderError("ISBNsearch found the ISBN but did not return a title.")

    return BookMetadata(
        title=title,
        authors=fields.get("Author"),
        publishers=fields.get("Publisher"),
        publish_date=fields.get("Published"),
        subjects=fields.get("Binding"),
        cover_url=_extract_preload_image(page),
        source_url=url,
    )


def _extract_h1(page: str) -> str | None:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", page, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return _clean_html(match.group(1))


def _is_verification_page(page: str) -> bool:
    title = _extract_h1(page)
    if title == "Please Verify to Continue":
        return True
    return "g-recaptcha" in page or 'id="recaptcha"' in page


def _extract_isbnsearch_fields(page: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    pattern = re.compile(
        r"<p>\s*<strong>(?P<label>[^<:]+):</strong>\s*(?P<value>.*?)</p>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(page):
        label = _clean_html(match.group("label"))
        value = _clean_html(match.group("value"))
        if label and value:
            fields[label] = value
    return fields


def _extract_preload_image(page: str) -> str | None:
    match = re.search(r'<link[^>]+rel="preload"[^>]+as="image"[^>]+href="([^"]+)"', page, flags=re.IGNORECASE)
    if not match:
        return None
    return html.unescape(match.group(1))


def _clean_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", value)
    return " ".join(html.unescape(without_tags).split())
