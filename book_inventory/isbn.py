from __future__ import annotations

ISBN13_PREFIX = "978"


def normalize_isbn(value: str) -> str:
    """Return only ISBN characters, preserving a trailing ISBN-10 X."""
    cleaned = "".join(ch for ch in value.upper() if ch.isdigit() or ch == "X")
    if len(cleaned) == 10 and "X" in cleaned[:-1]:
        return cleaned.replace("X", "")
    return cleaned


def is_valid_isbn10(isbn: str) -> bool:
    if len(isbn) != 10:
        return False
    total = 0
    for index, char in enumerate(isbn):
        if char == "X" and index == 9:
            digit = 10
        elif char.isdigit():
            digit = int(char)
        else:
            return False
        total += (10 - index) * digit
    return total % 11 == 0


def is_valid_isbn13(isbn: str) -> bool:
    if len(isbn) != 13 or not isbn.isdigit():
        return False
    return _isbn13_check_digit(isbn[:12]) == int(isbn[-1])


def isbn10_to_isbn13(isbn10: str) -> str:
    if not is_valid_isbn10(isbn10):
        raise ValueError("Invalid ISBN-10")
    body = ISBN13_PREFIX + isbn10[:9]
    return f"{body}{_isbn13_check_digit(body)}"


def _isbn13_check_digit(body: str) -> int:
    total = 0
    for index, char in enumerate(body):
        total += int(char) * (1 if index % 2 == 0 else 3)
    return (10 - (total % 10)) % 10


def split_isbn(value: str) -> tuple[str | None, str | None]:
    isbn = normalize_isbn(value)
    if is_valid_isbn13(isbn):
        return (isbn, None)
    if is_valid_isbn10(isbn):
        return (isbn10_to_isbn13(isbn), isbn)
    return (None, None)
