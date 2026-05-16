from __future__ import annotations

from dataclasses import replace

from book_inventory.metadata import isbnsearch, open_library
from book_inventory.metadata.models import BookMetadata


class MetadataLookupError(RuntimeError):
    pass


def lookup_isbn(isbn: str) -> BookMetadata:
    errors: list[str] = []
    primary: BookMetadata | None = None
    try:
        primary = open_library.lookup(isbn)
    except RuntimeError as exc:
        errors.append(str(exc))

    try:
        secondary = isbnsearch.lookup(isbn)
    except RuntimeError as exc:
        errors.append(str(exc))
        secondary = None

    if primary and secondary:
        return _merge_metadata(primary, secondary)
    if primary:
        return primary
    if secondary:
        return secondary
    raise MetadataLookupError("; ".join(errors))


def _merge_metadata(primary: BookMetadata, secondary: BookMetadata) -> BookMetadata:
    return replace(
        primary,
        authors=secondary.authors or primary.authors,
        publishers=primary.publishers or secondary.publishers,
        publish_date=primary.publish_date or secondary.publish_date,
        page_count=primary.page_count or secondary.page_count,
        cover_url=primary.cover_url or secondary.cover_url,
    )
