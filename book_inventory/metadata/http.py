from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT_SECONDS = (5, 20)


def create_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "book-inventory-streamlit/0.1"})
    return session


SESSION = create_session()
