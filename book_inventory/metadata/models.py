from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class BookMetadata:
    title: str
    subtitle: Optional[str] = None
    authors: Optional[str] = None
    publishers: Optional[str] = None
    publish_date: Optional[str] = None
    page_count: Optional[int] = None
    languages: Optional[str] = None
    subjects: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    source_url: Optional[str] = None
    lookup_status: str = "found"
    lookup_error: Optional[str] = None

    def to_db_fields(self) -> dict[str, object]:
        data = asdict(self)
        data["open_library_url"] = data.pop("source_url")
        return data
