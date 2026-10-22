"""Loading and validating watches.yml."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class ConfigError(ValueError):
    """Raised when watches.yml is invalid."""


@dataclass
class Watch:
    id: str
    url: str
    selector: str | None = None
    keywords: list[str] = field(default_factory=list)
    ignore: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def compiled_ignore(self) -> list[re.Pattern[str]]:
        return [re.compile(p) for p in self.ignore]


def _as_list(value, key: str, watch_id: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return value
    raise ConfigError(f"watch '{watch_id}': '{key}' must be a string or list of strings")


def parse_watches(data) -> list[Watch]:
    if not isinstance(data, dict) or not isinstance(data.get("watches"), list):
        raise ConfigError("config must contain a top-level 'watches' list")

    watches: list[Watch] = []
    seen: set[str] = set()
    for i, raw in enumerate(data["watches"]):
        if not isinstance(raw, dict):
            raise ConfigError(f"watch #{i + 1} must be a mapping")
        watch_id = raw.get("id")
        url = raw.get("url")
        if not isinstance(watch_id, str) or not ID_PATTERN.match(watch_id):
            raise ConfigError(
                f"watch #{i + 1}: 'id' is required and may only contain "
                "lowercase letters, digits, '-' and '_'"
            )
        if watch_id in seen:
            raise ConfigError(f"duplicate watch id '{watch_id}'")
        seen.add(watch_id)
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ConfigError(f"watch '{watch_id}': 'url' must start with http:// or https://")

        ignore = _as_list(raw.get("ignore"), "ignore", watch_id)
        for pattern in ignore:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ConfigError(f"watch '{watch_id}': bad ignore regex {pattern!r}: {exc}") from exc

        headers = raw.get("headers") or {}
        if not isinstance(headers, dict):
            raise ConfigError(f"watch '{watch_id}': 'headers' must be a mapping")

        watches.append(
            Watch(
                id=watch_id,
                url=url,
                selector=raw.get("selector"),
                keywords=_as_list(raw.get("keywords"), "keywords", watch_id),
                ignore=ignore,
                headers={str(k): str(v) for k, v in headers.items()},
                enabled=bool(raw.get("enabled", True)),
            )
        )
    return watches


def load_watches(path: str | Path) -> list[Watch]:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ConfigError(f"could not parse {path}: {exc}") from exc
    return parse_watches(data)
