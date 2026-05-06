from book_inventory.metadata.isbnsearch import _extract_h1, _extract_isbnsearch_fields, _extract_preload_image
from book_inventory.metadata.models import BookMetadata


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
