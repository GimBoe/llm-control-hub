from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HISTORY_PATH = Path(__file__).resolve().parent.parent / ".prompt_history.jsonl"


def _ensure_parent() -> None:
    _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)


def append_history_record(record: dict[str, Any]) -> None:
    _ensure_parent()
    with _HISTORY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), **record}) + "\n")


def read_history(limit: int = 20) -> list[dict[str, Any]]:
    if not _HISTORY_PATH.exists():
        return []

    items: list[dict[str, Any]] = []
    with _HISTORY_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            items.append(item)
            if len(items) >= limit:
                break
    return list(reversed(items))
