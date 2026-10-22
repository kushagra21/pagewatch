"""Fetching pages over HTTP."""

from __future__ import annotations

import httpx

from pagewatch import __version__

DEFAULT_HEADERS = {
    "User-Agent": f"pagewatch/{__version__} (+https://github.com/; personal page monitor)",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}


class FetchError(RuntimeError):
    pass


def fetch(url: str, headers: dict[str, str] | None = None, timeout: float = 30.0) -> str:
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    try:
        response = httpx.get(url, headers=merged, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FetchError(f"{url}: {exc}") from exc
    return response.text
