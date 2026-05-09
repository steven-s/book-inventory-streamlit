import sqlite3

import pytest

from book_inventory.db import (
    get_book_by_isbn13,
    init_db,
    list_books,
    mark_lookup_error,
    update_book_fields,
    update_book_metadata,
    upsert_scan,
)
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


def test_upsert_scan_inserts_then_updates_scan_count_and_isbn10(conn):
    upsert_scan(conn, isbn_raw="9780306406157", isbn13="9780306406157", isbn10=None)
    upsert_scan(conn, isbn_raw="0-306-40615-2", isbn13="9780306406157", isbn10="0306406152")

    book = get_book_by_isbn13(conn, "9780306406157")

    assert book["isbn_raw"] == "0-306-40615-2"
    assert book["isbn10"] == "0306406152"
    assert book["scan_count"] == 2


def test_update_book_metadata_maps_metadata_to_columns(conn):
    upsert_scan(conn, isbn_raw="9780306406157", isbn13="9780306406157", isbn10=None)

    update_book_metadata(
        conn,
        isbn13="9780306406157",
        metadata=BookMetadata(
            title="The Example Book",
            authors="Ada Lovelace",
            publishers="Example Press",
            page_count=321,
            source_url="https://openlibrary.org/isbn/9780306406157",
        ),
    )

    book = get_book_by_isbn13(conn, "9780306406157")

    assert book["title"] == "The Example Book"
    assert book["authors"] == "Ada Lovelace"
    assert book["publishers"] == "Example Press"
    assert book["page_count"] == 321
    assert book["open_library_url"] == "https://openlibrary.org/isbn/9780306406157"
    assert book["lookup_status"] == "found"
    assert book["lookup_error"] is None


def test_mark_lookup_error_preserves_found_status_when_metadata_exists(conn):
    upsert_scan(conn, isbn_raw="9780306406157", isbn13="9780306406157", isbn10=None)
    update_book_metadata(conn, isbn13="9780306406157", metadata={"title": "Existing title"})

    mark_lookup_error(conn, isbn13="9780306406157", error="temporarily unavailable")

    book = get_book_by_isbn13(conn, "9780306406157")
    assert book["lookup_status"] == "found"
    assert book["lookup_error"] == "temporarily unavailable"


def test_mark_lookup_error_marks_unenriched_book_as_error(conn):
    upsert_scan(conn, isbn_raw="9780306406157", isbn13="9780306406157", isbn10=None)

    mark_lookup_error(conn, isbn13="9780306406157", error="no provider match")

    book = get_book_by_isbn13(conn, "9780306406157")
    assert book["lookup_status"] == "error"
    assert book["lookup_error"] == "no provider match"


def test_update_book_fields_ignores_unknown_columns(conn):
    row = upsert_scan(conn, isbn_raw="9780306406157", isbn13="9780306406157", isbn10=None)

    update_book_fields(
        conn,
        book_id=row["id"],
        fields={"title": "Updated title", "not_a_column": "ignored"},
    )

    book = get_book_by_isbn13(conn, "9780306406157")
    assert book["title"] == "Updated title"
    assert "not_a_column" not in book.keys()


def test_list_books_orders_most_recent_scan_first(conn):
    upsert_scan(conn, isbn_raw="9780306406157", isbn13="9780306406157", isbn10=None)
    upsert_scan(conn, isbn_raw="9780140328721", isbn13="9780140328721", isbn10=None)

    books = list_books(conn)

    assert [book["isbn13"] for book in books] == ["9780140328721", "9780306406157"]
