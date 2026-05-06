from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

from book_inventory.db import mark_lookup_error, update_book_metadata, upsert_scan
from book_inventory.isbn import normalize_isbn, split_isbn
from book_inventory.metadata import MetadataLookupError, lookup_isbn
from book_inventory.metadata.models import BookMetadata


@dataclass
class ScanResult:
    isbn13: Optional[str]
    isbn10: Optional[str] = None
    metadata: Optional[BookMetadata] = None
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.isbn13 is not None

    @property
    def is_enriched(self) -> bool:
        return self.metadata is not None


def scan_book(conn: sqlite3.Connection, raw_isbn: str) -> ScanResult:
    normalized = normalize_isbn(raw_isbn)
    isbn13, isbn10 = split_isbn(normalized)
    if not isbn13:
        return ScanResult(isbn13=None, error="That does not look like a valid ISBN-10 or ISBN-13.")

    upsert_scan(conn, isbn_raw=raw_isbn, isbn13=isbn13, isbn10=isbn10)
    try:
        metadata = lookup_isbn(isbn13)
    except MetadataLookupError as exc:
        mark_lookup_error(conn, isbn13=isbn13, error=str(exc))
        return ScanResult(isbn13=isbn13, isbn10=isbn10, error=str(exc))

    update_book_metadata(conn, isbn13=isbn13, metadata=metadata)
    return ScanResult(isbn13=isbn13, isbn10=isbn10, metadata=metadata)
