from book_inventory.metadata.isbnsearch import (
    _extract_h1,
    _extract_isbnsearch_fields,
    _extract_preload_image,
    _is_verification_page,
)
from book_inventory.metadata.lookup import _merge_metadata
from book_inventory.metadata.models import BookMetadata
from book_inventory.metadata.open_library import _author_keys


def test_isbnsearch_html_helpers_extract_book_fields():
    page = """
    <link rel="preload" as="image" href="https://example.com/cover.jpg">
    <h1>Hieratikon, Vol. 2 Liturgy Book for Priest and Deacon</h1>
    <p><strong>Author:</strong> Orthodox Eastern Church</p>
    <p><strong>Publisher:</strong> St. Tikhon&#39;s Monastery Press</p>
    <p><strong>Published:</strong> 2017-10-30</p>
    """

    assert _extract_h1(page) == "Hieratikon, Vol. 2 Liturgy Book for Priest and Deacon"
    assert _extract_preload_image(page) == "https://example.com/cover.jpg"
    assert _extract_isbnsearch_fields(page) == {
        "Author": "Orthodox Eastern Church",
        "Publisher": "St. Tikhon's Monastery Press",
        "Published": "2017-10-30",
    }


def test_book_metadata_maps_source_url_to_existing_db_column():
    metadata = BookMetadata(title="Example", source_url="https://example.com")

    assert metadata.to_db_fields()["open_library_url"] == "https://example.com"


def test_isbnsearch_verification_pages_are_detected():
    page = """
    <h1>Please Verify to Continue</h1>
    <form id="recaptcha" action="" method="post"></form>
    """

    assert _is_verification_page(page)


def test_open_library_author_keys_support_edition_and_work_shapes():
    authors = [
        {"key": "/authors/OL33146A"},
        {"author": {"key": "/authors/OL24137A"}, "type": {"key": "/type/author_role"}},
    ]

    assert _author_keys(authors) == ["/authors/OL33146A", "/authors/OL24137A"]


def test_metadata_merge_prefers_isbnsearch_author_cross_check():
    open_library = BookMetadata(
        title="Ecce Homo How To Become What You Are",
        authors="Duncan Large",
        publishers="Oxford University Press",
    )
    isbnsearch = BookMetadata(
        title="Ecce Homo How To Become What You Are",
        authors="Friedrich Nietzsche",
        publish_date="2009-09-03",
    )

    merged = _merge_metadata(open_library, isbnsearch)

    assert merged.authors == "Friedrich Nietzsche"
    assert merged.publishers == "Oxford University Press"
    assert merged.publish_date == "2009-09-03"
