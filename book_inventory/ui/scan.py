from __future__ import annotations

import sqlite3

import streamlit as st

from book_inventory.services import save_invalid_printed_isbn, scan_book


def render_scan_form(conn: sqlite3.Connection) -> None:
    if "invalid_isbn_pending" not in st.session_state:
        st.session_state.invalid_isbn_pending = None
    if "scan_input_value" not in st.session_state:
        st.session_state.scan_input_value = ""
    if st.session_state.pop("clear_scan_input", False):
        st.session_state.scan_input_value = ""

    with st.form("scan_form"):
        isbn_input = st.text_input(
            "Scan or enter ISBN",
            placeholder="Scan a barcode, then press Enter",
            help="USB and Bluetooth barcode scanners usually type the barcode and send Enter.",
            key="scan_input_value",
        )
        submitted = st.form_submit_button("Add book", type="primary")

    if submitted:
        result = scan_book(conn, isbn_input)
        if not result.is_valid:
            st.session_state.invalid_isbn_pending = isbn_input
            st.error(result.error)
        elif result.is_enriched:
            st.session_state.invalid_isbn_pending = None
            st.success(f"Saved {result.metadata.title}")
            st.session_state.clear_scan_input = True
            st.rerun()
        else:
            st.session_state.invalid_isbn_pending = None
            st.warning(f"Saved ISBN {result.isbn13}. Metadata lookup did not finish: {result.error}")
            st.session_state.clear_scan_input = True
            st.rerun()

    if st.session_state.invalid_isbn_pending:
        st.caption(f"Pending invalid printed ISBN: {st.session_state.invalid_isbn_pending}")
        if st.button("Save invalid printed ISBN", type="primary"):
            save_invalid_printed_isbn(conn, st.session_state.invalid_isbn_pending)
            st.session_state.invalid_isbn_pending = None
            st.session_state.clear_scan_input = True
            st.success("Saved invalid printed ISBN for manual review.")
            st.rerun()
