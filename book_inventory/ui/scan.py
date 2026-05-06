from __future__ import annotations

import sqlite3

import streamlit as st

from book_inventory.services import scan_book


def render_scan_form(conn: sqlite3.Connection) -> None:
    with st.form("scan_form", clear_on_submit=True):
        isbn_input = st.text_input(
            "Scan or enter ISBN",
            placeholder="Scan a barcode, then press Enter",
            help="USB and Bluetooth barcode scanners usually type the barcode and send Enter.",
        )
        submitted = st.form_submit_button("Add book", type="primary")

    if not submitted:
        return

    result = scan_book(conn, isbn_input)
    if not result.is_valid:
        st.error(result.error)
    elif result.is_enriched:
        st.success(f"Saved {result.metadata.title}")
    else:
        st.warning(f"Saved ISBN {result.isbn13}. Metadata lookup did not finish: {result.error}")
