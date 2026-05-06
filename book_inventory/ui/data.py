from __future__ import annotations

import sqlite3

import pandas as pd

from book_inventory.db import list_books

EMPTY_COLUMNS = [
    "id",
    "isbn13",
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
    "created_at",
    "updated_at",
    "last_scanned_at",
]


def load_books_dataframe(conn: sqlite3.Connection) -> pd.DataFrame:
    rows = list_books(conn)
    df = pd.DataFrame([dict(row) for row in rows])
    if df.empty:
        return pd.DataFrame(columns=EMPTY_COLUMNS)
    return df
