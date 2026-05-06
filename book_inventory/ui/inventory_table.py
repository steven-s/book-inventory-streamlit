from __future__ import annotations

import pandas as pd
import streamlit as st

TABLE_COLUMNS = [
    "id",
    "isbn13",
    "title",
    "authors",
    "lookup_status",
    "scan_count",
]


def ensure_inventory_state(df: pd.DataFrame) -> None:
    if "inventory_page" not in st.session_state:
        st.session_state.inventory_page = 1
    if "active_book_id" not in st.session_state:
        st.session_state.active_book_id = int(df["id"].iloc[0]) if not df.empty else None


def render_inventory_table(filtered: pd.DataFrame) -> None:
    if filtered.empty:
        st.dataframe(filtered, hide_index=True, width="stretch")
        return

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
    table_input = filtered.iloc[page_start:page_end][TABLE_COLUMNS].set_index("id")
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
