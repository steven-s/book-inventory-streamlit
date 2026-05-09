from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class BookMetadata:
    title: str
    subtitle: str | None = None
    authors: str | None = None
    publishers: str | None = None
    publish_date: str | None = None
    page_count: int | None = None
    languages: str | None = None
    subjects: str | None = None
    description: str | None = None
    cover_url: str | None = None
    source_url: str | None = None
    lookup_status: str = "found"
    lookup_error: str | None = None

    def to_db_fields(self) -> dict[str, object]:
        data = asdict(self)
        data["open_library_url"] = data.pop("source_url")
        return data
