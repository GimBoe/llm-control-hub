from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

REPO_ROOT = Path(__file__).resolve().parents[2]
HISTORY_PATH = REPO_ROOT / ".prompt_history.jsonl"


def _fernet() -> Fernet | None:
    key = os.getenv("HISTORY_KEY")
    if not key:
        return None
    return Fernet(key.encode("utf-8") if not key.startswith("gAAAA") else key.encode("utf-8"))


def _serialize_record(record: dict[str, Any]) -> str:
    payload = json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), **record}, ensure_ascii=False)
    f = _fernet()
    if f is None:
        return payload
    return f.encrypt(payload.encode("utf-8")).decode("utf-8")


def _deserialize_record(line: str) -> dict[str, Any] | None:
    candidate = line.strip()
    if not candidate:
        return None
    f = _fernet()
    if f is not None:
        try:
            candidate = f.decrypt(candidate.encode("utf-8")).decode("utf-8")
        except Exception:
            return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def append_history_record(record: dict[str, Any]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(_serialize_record(record) + "\n")


def read_history(limit: int = 20) -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []

    items: list[dict[str, Any]] = []
    with HISTORY_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            item = _deserialize_record(line)
            if item is None:
                continue
            items.append(item)
            if len(items) >= limit:
                break
    return list(reversed(items))


def clear_history() -> None:
    if HISTORY_PATH.exists():
        HISTORY_PATH.unlink()


def prune_history(retention_days: int = 30) -> int:
    if not HISTORY_PATH.exists():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=max(retention_days, 1))
    remaining: list[str] = []
    removed = 0
    with HISTORY_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            parsed = _deserialize_record(line)
            if parsed is None:
                removed += 1
                continue
            try:
                ts = datetime.fromisoformat(parsed.get("timestamp", "1970-01-01T00:00:00+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    removed += 1
                    continue
            except ValueError:
                remaining.append(line)
                continue
            remaining.append(line)

    if removed:
        with HISTORY_PATH.open("w", encoding="utf-8") as handle:
            for line in remaining:
                handle.write(line)
    return removed
