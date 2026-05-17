from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Mapping

from book_inventory.metadata.models import BookMetadata

DB_PATH = Path("data/book_inventory.sqlite3")


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn13 TEXT UNIQUE,
            isbn10 TEXT,
            isbn_raw TEXT NOT NULL,
            title TEXT,
            subtitle TEXT,
            authors TEXT,
            publishers TEXT,
            publish_date TEXT,
            page_count INTEGER,
            languages TEXT,
            subjects TEXT,
            cover_url TEXT,
            open_library_url TEXT,
            lookup_status TEXT NOT NULL DEFAULT 'pending',
            lookup_error TEXT,
            scan_count INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_scanned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TRIGGER IF NOT EXISTS books_updated_at
        AFTER UPDATE ON books
        FOR EACH ROW
        BEGIN
            UPDATE books SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END
        """
    )
    conn.commit()


def upsert_scan(
    conn: sqlite3.Connection,
    *,
    isbn_raw: str,
    isbn13: str,
    isbn10: str | None,
) -> sqlite3.Row:
    conn.execute(
        """
        INSERT INTO books (isbn13, isbn10, isbn_raw)
        VALUES (?, ?, ?)
        ON CONFLICT(isbn13) DO UPDATE SET
            isbn_raw = excluded.isbn_raw,
            isbn10 = COALESCE(books.isbn10, excluded.isbn10),
            scan_count = books.scan_count + 1,
            last_scanned_at = CURRENT_TIMESTAMP
        """,
        (isbn13, isbn10, isbn_raw),
    )
    conn.commit()
    return get_book_by_isbn13(conn, isbn13)


def insert_invalid_printed_isbn(
    conn: sqlite3.Connection,
    *,
    isbn_raw: str,
) -> sqlite3.Row:
    existing = conn.execute(
        """
        SELECT * FROM books
        WHERE isbn13 IS NULL AND isbn_raw = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (isbn_raw,),
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE books
            SET scan_count = scan_count + 1,
                last_scanned_at = CURRENT_TIMESTAMP,
                lookup_status = 'manual_review',
                lookup_error = 'Invalid printed ISBN saved manually.'
            WHERE id = ?
            """,
            (existing["id"],),
        )
        conn.commit()
        return get_book_by_id(conn, existing["id"])

    cursor = conn.execute(
        """
        INSERT INTO books (isbn_raw, lookup_status, lookup_error)
        VALUES (?, 'manual_review', 'Invalid printed ISBN saved manually.')
        """,
        (isbn_raw,),
    )
    conn.commit()
    return get_book_by_id(conn, cursor.lastrowid)


def update_book_metadata(
    conn: sqlite3.Connection,
    *,
    isbn13: str,
    metadata: BookMetadata | Mapping[str, Any],
) -> None:
    fields = metadata.to_db_fields() if isinstance(metadata, BookMetadata) else metadata
    conn.execute(
        """
        UPDATE books SET
            title = ?,
            subtitle = ?,
            authors = ?,
            publishers = ?,
            publish_date = ?,
            page_count = ?,
            languages = ?,
            subjects = ?,
            cover_url = ?,
            open_library_url = ?,
            lookup_status = ?,
            lookup_error = ?
        WHERE isbn13 = ?
        """,
        (
            fields.get("title"),
            fields.get("subtitle"),
            fields.get("authors"),
            fields.get("publishers"),
            fields.get("publish_date"),
            fields.get("page_count"),
            fields.get("languages"),
            fields.get("subjects"),
            fields.get("cover_url"),
            fields.get("open_library_url"),
            fields.get("lookup_status", "found"),
            fields.get("lookup_error"),
            isbn13,
        ),
    )
    conn.commit()


def mark_lookup_error(conn: sqlite3.Connection, *, isbn13: str, error: str) -> None:
    conn.execute(
        """
        UPDATE books
        SET
            lookup_status = CASE
                WHEN title IS NOT NULL AND title != '' THEN 'found'
                ELSE 'error'
            END,
            lookup_error = ?
        WHERE isbn13 = ?
        """,
        (error, isbn13),
    )
    conn.commit()


def update_book_fields(
    conn: sqlite3.Connection,
    *,
    book_id: int,
    fields: dict[str, Any],
) -> None:
    allowed_fields = {
        "isbn10",
        "title",
        "subtitle",
        "authors",
        "publishers",
        "publish_date",
        "page_count",
        "languages",
        "subjects",
        "cover_url",
        "open_library_url",
        "lookup_status",
        "lookup_error",
        "scan_count",
    }
    updates = {key: value for key, value in fields.items() if key in allowed_fields}
    if not updates:
        return

    assignments = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values()) + [book_id]
    conn.execute(f"UPDATE books SET {assignments} WHERE id = ?", values)
    conn.commit()


def get_book_by_isbn13(conn: sqlite3.Connection, isbn13: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM books WHERE isbn13 = ?", (isbn13,)).fetchone()
    if row is None:
        raise LookupError(f"No book with ISBN {isbn13}")
    return row


def get_book_by_id(conn: sqlite3.Connection, book_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if row is None:
        raise LookupError(f"No book with ID {book_id}")
    return row


def list_books(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            id, isbn13, isbn10, isbn_raw, title, subtitle, authors, publishers, publish_date,
            page_count, languages, subjects, cover_url, open_library_url,
            lookup_status, lookup_error, scan_count, created_at, updated_at,
            last_scanned_at
        FROM books
        ORDER BY last_scanned_at DESC, id DESC
        """
    ).fetchall()


def delete_book(conn: sqlite3.Connection, book_id: int) -> None:
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
