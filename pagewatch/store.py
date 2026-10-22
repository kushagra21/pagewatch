"""Snapshot storage: one plain-text file per watch, versioned by git."""

from __future__ import annotations

from pathlib import Path


class SnapshotStore:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def path(self, watch_id: str) -> Path:
        return self.directory / f"{watch_id}.txt"

    def load(self, watch_id: str) -> str | None:
        path = self.path(watch_id)
        return path.read_text(encoding="utf-8") if path.exists() else None

    def save(self, watch_id: str, text: str) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path(watch_id).write_text(text + "\n", encoding="utf-8")
