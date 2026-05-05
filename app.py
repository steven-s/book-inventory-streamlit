from __future__ import annotations

import pandas as pd
import streamlit as st

from book_inventory.db import (
    delete_book,
    get_connection,
    init_db,
    list_books,
    mark_lookup_error,
    update_book_fields,
    update_book_metadata,
    upsert_scan,
)
from book_inventory.isbn import normalize_isbn, split_isbn
from book_inventory.open_library import OpenLibraryError, lookup_isbn


st.set_page_config(page_title="Book Inventory", page_icon="book", layout="wide")


@st.cache_resource
def connection():
    conn = get_connection()
    init_db(conn)
    return conn


def rows_to_dataframe(rows) -> pd.DataFrame:
    df = pd.DataFrame([dict(row) for row in rows])
    if df.empty:
        return pd.DataFrame(
            columns=[
                "isbn13",
                "isbn10",
                "title",
                "authors",
                "publishers",
                "publish_date",
                "page_count",
                "subjects",
                "lookup_status",
                "scan_count",
                "last_scanned_at",
            ]
        )
    return df


conn = connection()

st.title("Book Inventory")

with st.form("scan_form", clear_on_submit=True):
    isbn_input = st.text_input(
        "Scan or enter ISBN",
        placeholder="Scan a barcode, then press Enter",
        help="USB and Bluetooth barcode scanners usually type the barcode and send Enter.",
    )
    submitted = st.form_submit_button("Add book", type="primary")

if submitted:
    normalized = normalize_isbn(isbn_input)
    isbn13, isbn10 = split_isbn(normalized)
    if not isbn13:
        st.error("That does not look like a valid ISBN-10 or ISBN-13.")
    else:
        upsert_scan(conn, isbn_raw=isbn_input, isbn13=isbn13, isbn10=isbn10)
        try:
            metadata = lookup_isbn(isbn13)
            update_book_metadata(conn, isbn13=isbn13, metadata=metadata)
            st.success(f"Saved {metadata['title']}")
        except OpenLibraryError as exc:
            mark_lookup_error(conn, isbn13=isbn13, error=str(exc))
            st.warning(f"Saved ISBN {isbn13}. Open Library lookup did not finish: {exc}")

rows = list_books(conn)
df = rows_to_dataframe(rows)

summary_cols = st.columns(4)
summary_cols[0].metric("Books", len(df))
summary_cols[1].metric("Scans", int(df["scan_count"].sum()) if not df.empty else 0)
summary_cols[2].metric("Enriched", int((df["lookup_status"] == "found").sum()) if not df.empty else 0)
summary_cols[3].metric("Needs review", int((df["lookup_status"] != "found").sum()) if not df.empty else 0)

toolbar_left, toolbar_right = st.columns([3, 1])
with toolbar_left:
    search = st.text_input("Filter inventory", placeholder="Title, author, publisher, or ISBN")
with toolbar_right:
    st.download_button(
        "Export CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="book_inventory.csv",
        mime="text/csv",
        width="stretch",
        disabled=df.empty,
    )

filtered = df
if search and not df.empty:
    haystack_cols = ["isbn13", "isbn10", "title", "authors", "publishers", "subjects"]
    mask = df[haystack_cols].fillna("").agg(" ".join, axis=1).str.contains(search, case=False, regex=False)
    filtered = df[mask]

if "inventory_page" not in st.session_state:
    st.session_state.inventory_page = 1
if "active_book_id" not in st.session_state:
    st.session_state.active_book_id = int(df["id"].iloc[0]) if not df.empty else None

table_cols = [
    "id",
    "isbn13",
    "title",
    "authors",
    "lookup_status",
    "scan_count",
]
if filtered.empty:
    st.dataframe(filtered, hide_index=True, width="stretch")
else:
    pager_left, pager_middle, pager_right = st.columns([1, 2, 1])
    with pager_left:
        page_size = st.selectbox("Rows per page", options=[10, 25, 50, 100], index=1)

    total_rows = len(filtered)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    st.session_state.inventory_page = min(st.session_state.inventory_page, total_pages)

    with pager_middle:
        st.caption(f"Page {st.session_state.inventory_page} of {total_pages} · {total_rows} records")

    with pager_right:
        prev_col, next_col = st.columns(2)
        if prev_col.button("Prev", disabled=st.session_state.inventory_page <= 1, width="stretch"):
            st.session_state.inventory_page -= 1
            st.rerun()
        if next_col.button(
            "Next",
            disabled=st.session_state.inventory_page >= total_pages,
            width="stretch",
        ):
            st.session_state.inventory_page += 1
            st.rerun()

    page_start = (st.session_state.inventory_page - 1) * page_size
    page_end = page_start + page_size
    paged = filtered.iloc[page_start:page_end]
    table_input = paged[table_cols].set_index("id")
    table_state = st.dataframe(
        table_input,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "scan_count": st.column_config.NumberColumn("scan_count", min_value=0, step=1),
        },
        key="inventory_table",
    )
    selected_rows = table_state.selection.rows
    if selected_rows:
        st.session_state.active_book_id = int(table_input.index[selected_rows[0]])

with st.expander("Current Book Details"):
    if df.empty:
        st.caption("No books have been scanned yet.")
    else:
        show_debug_json = st.checkbox("Show raw JSON", value=False)
        if st.session_state.active_book_id not in set(df["id"].tolist()):
            st.session_state.active_book_id = int(df["id"].iloc[0])
        selected = st.session_state.active_book_id
        selected_row = df.loc[df["id"] == selected].iloc[0]
        st.caption(selected_row.get("title") or selected_row.get("isbn13"))
        if show_debug_json:
            st.json(selected_row.dropna().to_dict(), expanded=False)

        cover_url = selected_row.get("cover_url")
        if cover_url:
            cover_col, meta_col = st.columns([1, 3])
            with cover_col:
                st.image(cover_url, caption="Cover", width=160)
            with meta_col:
                st.markdown(f"[Open cover image]({cover_url})")

        with st.form("record_details_form"):
            st.subheader("Book details")
            st.text_input("ISBN-13", value=selected_row.get("isbn13") or "", disabled=True)
            detail_title = st.text_input("Title", value=selected_row.get("title") or "")
            detail_subtitle = st.text_input("Subtitle", value=selected_row.get("subtitle") or "")
            detail_authors = st.text_input("Authors", value=selected_row.get("authors") or "")
            detail_publishers = st.text_input("Publishers", value=selected_row.get("publishers") or "")
            detail_publish_date = st.text_input("Publish date", value=selected_row.get("publish_date") or "")
            detail_page_count = st.number_input(
                "Page count",
                min_value=0,
                step=1,
                value=int(selected_row["page_count"]) if pd.notna(selected_row.get("page_count")) else 0,
            )
            detail_scan_count = st.number_input(
                "Scan count",
                min_value=0,
                step=1,
                value=int(selected_row["scan_count"]) if pd.notna(selected_row.get("scan_count")) else 0,
            )
            detail_lookup_status = st.text_input("Lookup status", value=selected_row.get("lookup_status") or "")
            detail_lookup_error = st.text_area("Lookup error", value=selected_row.get("lookup_error") or "")
            detail_languages = st.text_input("Languages", value=selected_row.get("languages") or "")
            detail_subjects = st.text_area("Subjects", value=selected_row.get("subjects") or "")
            detail_cover_url = st.text_input("Cover URL", value=selected_row.get("cover_url") or "")
            detail_open_library_url = st.text_input(
                "Open Library URL",
                value=selected_row.get("open_library_url") or "",
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
                        "open_library_url": detail_open_library_url or None,
                    },
                )
                st.success("Record details saved.")
                st.rerun()

        col_a, col_b = st.columns(2)
        if col_a.button("Retry metadata lookup", width="stretch"):
            try:
                metadata = lookup_isbn(selected_row["isbn13"])
                update_book_metadata(conn, isbn13=selected_row["isbn13"], metadata=metadata)
                st.success("Metadata updated.")
                st.rerun()
            except OpenLibraryError as exc:
                mark_lookup_error(conn, isbn13=selected_row["isbn13"], error=str(exc))
                st.warning(f"Open Library lookup did not finish: {exc}")
        if col_b.button("Delete record", width="stretch"):
            delete_book(conn, int(selected))
            st.success("Record deleted.")
            st.rerun()
