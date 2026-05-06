from __future__ import annotations

import sqlite3

import pandas as pd
import streamlit as st

from book_inventory.db import delete_book, mark_lookup_error, update_book_fields, update_book_metadata
from book_inventory.metadata import MetadataLookupError, lookup_isbn


def render_current_book_details(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    with st.expander("Current Book Details"):
        if df.empty:
            st.caption("No books have been scanned yet.")
            return

        show_debug_json = st.checkbox("Show raw JSON", value=False)
        if st.session_state.active_book_id not in set(df["id"].tolist()):
            st.session_state.active_book_id = int(df["id"].iloc[0])
        selected = st.session_state.active_book_id
        selected_row = df.loc[df["id"] == selected].iloc[0]
        st.caption(text_value(selected_row, "title") or text_value(selected_row, "isbn13"))
        if show_debug_json:
            st.json(selected_row.dropna().to_dict(), expanded=False)

        render_cover(selected_row)
        render_details_form(conn, selected, selected_row)
        render_record_actions(conn, selected, selected_row)


def render_cover(selected_row: pd.Series) -> None:
    cover_url = text_value(selected_row, "cover_url")
    if not cover_url:
        return
    cover_col, meta_col = st.columns([1, 3])
    with cover_col:
        st.image(cover_url, caption="Cover", width=160)
    with meta_col:
        st.markdown(f"[Open cover image]({cover_url})")


def render_details_form(conn: sqlite3.Connection, selected: int, selected_row: pd.Series) -> None:
    with st.form("record_details_form"):
        st.subheader("Book details")
        st.text_input("ISBN-13", value=text_value(selected_row, "isbn13"), disabled=True)
        detail_title = st.text_input("Title", value=text_value(selected_row, "title"))
        detail_subtitle = st.text_input("Subtitle", value=text_value(selected_row, "subtitle"))
        detail_authors = st.text_input("Authors", value=text_value(selected_row, "authors"))
        detail_publishers = st.text_input("Publishers", value=text_value(selected_row, "publishers"))
        detail_publish_date = st.text_input("Publish date", value=text_value(selected_row, "publish_date"))
        detail_page_count = st.number_input(
            "Page count",
            min_value=0,
            step=1,
            value=int_value(selected_row, "page_count"),
        )
        detail_scan_count = st.number_input(
            "Scan count",
            min_value=0,
            step=1,
            value=int_value(selected_row, "scan_count"),
        )
        detail_lookup_status = st.text_input("Lookup status", value=text_value(selected_row, "lookup_status"))
        detail_lookup_error = st.text_area("Lookup error", value=text_value(selected_row, "lookup_error"))
        detail_languages = st.text_input("Languages", value=text_value(selected_row, "languages"))
        detail_subjects = st.text_area("Subjects", value=text_value(selected_row, "subjects"))
        detail_cover_url = st.text_input("Cover URL", value=text_value(selected_row, "cover_url"))
        detail_source_url = st.text_input(
            "Source URL",
            value=text_value(selected_row, "open_library_url"),
        )
        if st.form_submit_button("Save record details"):
            update_book_fields(
                conn,
                book_id=int(selected),
                fields={
                    "title": detail_title or None,
                    "subtitle": detail_subtitle or None,
                    "authors": detail_authors or None,
                    "publishers": detail_publishers or None,
                    "publish_date": detail_publish_date or None,
                    "page_count": detail_page_count or None,
                    "scan_count": detail_scan_count,
                    "lookup_status": detail_lookup_status or None,
                    "lookup_error": detail_lookup_error or None,
                    "languages": detail_languages or None,
                    "subjects": detail_subjects or None,
                    "cover_url": detail_cover_url or None,
                    "open_library_url": detail_source_url or None,
                },
            )
            st.success("Record details saved.")
            st.rerun()


def render_record_actions(conn: sqlite3.Connection, selected: int, selected_row: pd.Series) -> None:
    col_a, col_b = st.columns(2)
    if col_a.button("Retry metadata lookup", width="stretch"):
        try:
            metadata = lookup_isbn(selected_row["isbn13"])
            update_book_metadata(conn, isbn13=selected_row["isbn13"], metadata=metadata)
            st.success("Metadata updated.")
            st.rerun()
        except MetadataLookupError as exc:
            mark_lookup_error(conn, isbn13=selected_row["isbn13"], error=str(exc))
            st.warning(f"Metadata lookup did not finish: {exc}")
    if col_b.button("Delete record", width="stretch"):
        delete_book(conn, int(selected))
        st.success("Record deleted.")
        st.rerun()


def text_value(row: pd.Series, key: str) -> str:
    value = row.get(key)
    if pd.isna(value):
        return ""
    return str(value)


def int_value(row: pd.Series, key: str) -> int:
    value = row.get(key)
    if pd.isna(value):
        return 0
    return int(value)
