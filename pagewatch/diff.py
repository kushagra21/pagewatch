"""Comparing two snapshots."""

from __future__ import annotations

import difflib
from dataclasses import dataclass


@dataclass
class Change:
    added: list[str]
    removed: list[str]

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed)

    def matching_keywords(self, keywords: list[str]) -> list[str]:
        """Keywords (case-insensitive) that appear in the added lines."""
        haystack = "\n".join(self.added).lower()
        return [k for k in keywords if k.lower() in haystack]


def compare(old: str, new: str) -> Change:
    added: list[str] = []
    removed: list[str] = []
    for line in difflib.ndiff(old.splitlines(), new.splitlines()):
        if line.startswith("+ "):
            added.append(line[2:])
        elif line.startswith("- "):
            removed.append(line[2:])
    return Change(added=added, removed=removed)
