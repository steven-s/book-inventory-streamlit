import sqlite3

import pytest

import book_inventory.services as services
from book_inventory.db import get_book_by_isbn13, init_db, list_books
from book_inventory.metadata import MetadataLookupError
from book_inventory.metadata.models import BookMetadata


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    init_db(connection)
    try:
        yield connection
    finally:
        connection.close()


def test_scan_book_rejects_invalid_isbn_without_writing(monkeypatch, conn):
    def fail_lookup(_isbn):
        raise AssertionError("lookup should not run for invalid ISBNs")

    monkeypatch.setattr(services, "lookup_isbn", fail_lookup)

    result = services.scan_book(conn, "not an isbn")

    assert result.is_valid is False
    assert result.is_enriched is False
    assert result.error == "That does not look like a valid ISBN-10 or ISBN-13."
    assert list_books(conn) == []


def test_scan_book_saves_scan_and_metadata_on_lookup_success(monkeypatch, conn):
    metadata = BookMetadata(
        title="The Example Book",
        authors="Ada Lovelace",
        source_url="https://example.com/book",
    )

    def lookup(isbn):
        assert isbn == "9780306406157"
        return metadata

    monkeypatch.setattr(services, "lookup_isbn", lookup)

    result = services.scan_book(conn, "0-306-40615-2")

    assert result.is_valid is True
    assert result.is_enriched is True
    assert result.isbn13 == "9780306406157"
    assert result.isbn10 == "0306406152"
    assert result.metadata == metadata
    assert result.error is None

    book = get_book_by_isbn13(conn, "9780306406157")
    assert book["isbn_raw"] == "0-306-40615-2"
    assert book["title"] == "The Example Book"
    assert book["authors"] == "Ada Lovelace"
    assert book["open_library_url"] == "https://example.com/book"
    assert book["lookup_status"] == "found"


def test_scan_book_records_lookup_error_on_provider_failure(monkeypatch, conn):
    def lookup(_isbn):
        raise MetadataLookupError("providers unavailable")

    monkeypatch.setattr(services, "lookup_isbn", lookup)

    result = services.scan_book(conn, "9780306406157")

    assert result.is_valid is True
    assert result.is_enriched is False
    assert result.isbn13 == "9780306406157"
    assert result.error == "providers unavailable"

    book = get_book_by_isbn13(conn, "9780306406157")
    assert book["lookup_status"] == "error"
    assert book["lookup_error"] == "providers unavailable"
