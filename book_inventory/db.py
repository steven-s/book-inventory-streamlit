from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, List, Optional

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
    isbn10: Optional[str],
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


def update_book_metadata(
    conn: sqlite3.Connection,
    *,
    isbn13: str,
    metadata: dict[str, Any],
) -> None:
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
            metadata.get("title"),
            metadata.get("subtitle"),
            metadata.get("authors"),
            metadata.get("publishers"),
            metadata.get("publish_date"),
            metadata.get("page_count"),
            metadata.get("languages"),
            metadata.get("subjects"),
            metadata.get("cover_url"),
            metadata.get("open_library_url"),
            metadata.get("lookup_status", "found"),
            metadata.get("lookup_error"),
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


def list_books(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            id, isbn13, isbn10, title, subtitle, authors, publishers, publish_date,
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
