from __future__ import annotations

from typing import Any, List, Optional

import requests

from book_inventory.metadata.http import SESSION, TIMEOUT_SECONDS
from book_inventory.metadata.models import BookMetadata

BASE_URL = "https://openlibrary.org"


class OpenLibraryProviderError(RuntimeError):
    pass


def lookup(isbn: str) -> BookMetadata:
    edition = _get_json(f"{BASE_URL}/isbn/{isbn}.json")
    authors = _resolve_authors(edition)
    work = _resolve_first_work(edition)

    subjects = edition.get("subjects") or []
    description = None
    if work:
        subjects = subjects or work.get("subjects") or []
        description = _description_text(work.get("description"))

    title = edition.get("title") or (work or {}).get("title")
    if not title:
        raise OpenLibraryProviderError("Open Library found the ISBN but did not return a title.")

    return BookMetadata(
        title=title,
        subtitle=edition.get("subtitle"),
        authors=", ".join(authors) if authors else None,
        publishers=_join(edition.get("publishers")),
        publish_date=edition.get("publish_date"),
        page_count=edition.get("number_of_pages"),
        languages=_join_language_keys(edition.get("languages")),
        subjects=_join(subjects[:12]),
        description=description,
        cover_url=f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false",
        source_url=f"{BASE_URL}/isbn/{isbn}",
    )


def _get_json(url: str) -> dict[str, Any]:
    try:
        response = SESSION.get(url, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise OpenLibraryProviderError(f"Could not reach Open Library: {exc}") from exc
    if response.status_code == 404:
        raise OpenLibraryProviderError("No Open Library record was found for this ISBN.")
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise OpenLibraryProviderError(f"Open Library returned HTTP {response.status_code}.") from exc
    return response.json()


def _resolve_authors(edition: dict[str, Any]) -> List[str]:
    names: List[str] = []
    for author in edition.get("authors", []):
        key = author.get("key")
        if not key:
            continue
        try:
            data = _get_json(f"{BASE_URL}{key}.json")
        except OpenLibraryProviderError:
            continue
        name = data.get("name")
        if name:
            names.append(name)
    return names


def _resolve_first_work(edition: dict[str, Any]) -> Optional[dict[str, Any]]:
    works = edition.get("works") or []
    if not works:
        return None
    key = works[0].get("key")
    if not key:
        return None
    try:
        return _get_json(f"{BASE_URL}{key}.json")
    except OpenLibraryProviderError:
        return None


def _join(values: Optional[List[Any]]) -> Optional[str]:
    if not values:
        return None
    return ", ".join(str(value) for value in values if value)


def _join_language_keys(values: Optional[List[dict[str, str]]]) -> Optional[str]:
    if not values:
        return None
    return ", ".join(value["key"].removeprefix("/languages/") for value in values if value.get("key"))


def _description_text(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("value")
    return None
