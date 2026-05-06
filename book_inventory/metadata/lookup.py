from __future__ import annotations

from book_inventory.metadata import isbnsearch, open_library
from book_inventory.metadata.models import BookMetadata


class MetadataLookupError(RuntimeError):
    pass


def lookup_isbn(isbn: str) -> BookMetadata:
    errors: list[str] = []
    for provider in (open_library, isbnsearch):
        try:
            return provider.lookup(isbn)
        except RuntimeError as exc:
            errors.append(str(exc))
    raise MetadataLookupError("; ".join(errors))
