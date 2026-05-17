from pathlib import Path

from book_inventory.db import get_connection, init_db, list_books
from book_inventory.services import save_invalid_printed_isbn


def test_save_invalid_printed_isbn_creates_manual_review_record():
    db = Path("/private/tmp/book_inventory_invalid_printed_test.sqlite3")
    if db.exists():
        db.unlink()
    conn = get_connection(db)
    init_db(conn)

    save_invalid_printed_isbn(conn, "0-938635-50-7")

    row = list_books(conn)[0]
    assert row["isbn_raw"] == "0-938635-50-7"
    assert row["isbn13"] is None
    assert row["lookup_status"] == "manual_review"


def test_save_invalid_printed_isbn_increments_existing_manual_record():
    db = Path("/private/tmp/book_inventory_invalid_printed_increment_test.sqlite3")
    if db.exists():
        db.unlink()
    conn = get_connection(db)
    init_db(conn)

    save_invalid_printed_isbn(conn, "0-938635-50-7")
    save_invalid_printed_isbn(conn, "0-938635-50-7")

    rows = list_books(conn)
    assert len(rows) == 1
    assert rows[0]["scan_count"] == 2
