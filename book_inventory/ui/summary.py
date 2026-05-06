from __future__ import annotations

import pandas as pd
import streamlit as st


def render_summary(df: pd.DataFrame) -> None:
    summary_cols = st.columns(4)
    summary_cols[0].metric("Books", len(df))
    summary_cols[1].metric("Scans", int(df["scan_count"].sum()) if not df.empty else 0)
    summary_cols[2].metric("Enriched", int((df["lookup_status"] == "found").sum()) if not df.empty else 0)
    summary_cols[3].metric("Needs review", int((df["lookup_status"] != "found").sum()) if not df.empty else 0)


def render_filter_and_export(df: pd.DataFrame) -> pd.DataFrame:
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

    if not search or df.empty:
        return df

    haystack_cols = ["isbn13", "isbn10", "title", "authors", "publishers", "subjects"]
    mask = df[haystack_cols].fillna("").agg(" ".join, axis=1).str.contains(search, case=False, regex=False)
    return df[mask]
