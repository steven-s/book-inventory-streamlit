# Book Inventory

A Streamlit application for scanning book barcodes, saving ISBNs in SQLite, enriching records with Open Library metadata, and exporting the inventory as CSV.

100% Vibe Coded in Codex

## Setup

```bash
mamba env create -f environment.yml
mamba activate book-inventory
```

If you prefer conda, use `conda env create -f environment.yml` instead of `mamba env create`.

## Run

```bash
streamlit run app.py
```

Most handheld barcode scanners act like a keyboard and send `Enter` after scanning. Put the cursor in the ISBN field and scan; the app will save and enrich the book.

The database is stored at `data/book_inventory.sqlite3`.
