"""Data loading and destination lookup utilities."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@lru_cache(maxsize=None)
def load_json(filename: str) -> dict[str, Any]:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def resolve_destination(destination: str) -> tuple[str, dict[str, Any] | None]:
    """Return the canonical key and record for a destination or alias."""
    needle = normalize(destination)
    destinations = load_json("destinations.json")
    for key, record in destinations.items():
        candidates = {key, record.get("name", ""), *record.get("aliases", [])}
        if any(normalize(candidate) == needle for candidate in candidates):
            return key, record
    for key, record in destinations.items():
        candidates = {key, record.get("name", ""), *record.get("aliases", [])}
        if any(needle in normalize(candidate) or normalize(candidate) in needle for candidate in candidates):
            return key, record
    return needle.replace(" ", "-"), None


def month_name(month: str) -> str:
    """Normalize common month formats to a full English month name."""
    value = month.strip().lower()
    months = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
    ]
    if value.isdigit():
        index = int(value)
        if 1 <= index <= 12:
            return months[index - 1].title()
    for candidate in months:
        if value.startswith(candidate[:3]):
            return candidate.title()
    return month.strip().title()


def compact_error(message: str, *, tool: str) -> dict[str, Any]:
    return {
        "ok": False,
        "tool": tool,
        "error": message,
        "source": "local validation",
        "suggestion": "Continue with the other available planning data.",
    }


def compact_record(record: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: record[key] for key in keys if key in record}
