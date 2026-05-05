# Book Inventory

A Streamlit application for scanning book barcodes, saving ISBNs in SQLite, enriching records with Open Library metadata, and exporting the inventory as CSV.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Most handheld barcode scanners act like a keyboard and send `Enter` after scanning. Put the cursor in the ISBN field and scan; the app will save and enrich the book.

The database is stored at `data/book_inventory.sqlite3`.

