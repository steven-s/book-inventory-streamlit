from book_inventory.isbn import normalize_isbn, split_isbn


def test_normalize_isbn_keeps_valid_trailing_x():
    assert normalize_isbn("0-8044-2957-X") == "080442957X"


def test_split_valid_isbn13():
    assert split_isbn("9780306406157") == ("9780306406157", None)


def test_split_valid_isbn10_converts_to_isbn13():
    assert split_isbn("0306406152") == ("9780306406157", "0306406152")


def test_split_rejects_invalid_isbn():
    assert split_isbn("12345") == (None, None)
