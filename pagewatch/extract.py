"""Turning HTML into stable, comparable text."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

NOISE_TAGS = ("script", "style", "noscript", "template", "svg")
_WHITESPACE = re.compile(r"\s+")


class SelectorNotFound(LookupError):
    pass


def extract_text(
    html: str,
    selector: str | None = None,
    ignore: list[re.Pattern[str]] | None = None,
) -> str:
    """Return normalized, line-based text for the page or the selected part of it.

    - drops scripts/styles and other non-visible noise
    - keeps only elements matching `selector` (CSS) when given
    - flattens each table row into one line: `cell | cell | cell`
    - collapses whitespace and removes blank lines
    - removes anything matching the `ignore` regexes (timestamps, counters, tokens...)
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(NOISE_TAGS):
        tag.decompose()

    if selector:
        roots = soup.select(selector)
        if not roots:
            raise SelectorNotFound(f"selector {selector!r} matched nothing")
    else:
        roots = [soup.body or soup]

    for root in roots:
        _flatten_table_rows(soup, root)

    lines: list[str] = []
    for root in roots:
        for raw in root.get_text("\n").splitlines():
            line = _WHITESPACE.sub(" ", raw).strip()
            for pattern in ignore or []:
                line = pattern.sub("", line).strip()
            if line:
                lines.append(line)
    return "\n".join(lines)


def _flatten_table_rows(soup: BeautifulSoup, root) -> None:
    """Replace every table row with a single text line so a row diffs as one unit."""
    rows = [root] if root.name == "tr" else root.find_all("tr")
    for row in rows:
        cells = [_WHITESPACE.sub(" ", c.get_text(" ")).strip() for c in row.find_all(["th", "td"])]
        row.replace_with(soup.new_string("\n" + " | ".join(cells) + "\n"))
