from __future__ import annotations

import streamlit as st

from book_inventory.db import get_connection, init_db
from book_inventory.ui.book_details import render_current_book_details
from book_inventory.ui.data import load_books_dataframe
from book_inventory.ui.inventory_table import ensure_inventory_state, render_inventory_table
from book_inventory.ui.scan import render_scan_form
from book_inventory.ui.summary import render_filter_and_export, render_summary


st.set_page_config(page_title="Book Inventory", page_icon="book", layout="wide")


@st.cache_resource
def connection():
    conn = get_connection()
    init_db(conn)
    return conn


conn = connection()

st.title("Book Inventory")

render_scan_form(conn)

df = load_books_dataframe(conn)
render_summary(df)
filtered = render_filter_and_export(df)
ensure_inventory_state(df)
render_inventory_table(filtered)
render_current_book_details(conn, df)
