"""In-memory store for recently classified flows.

Used by the dashboard to show a live feed. Capacity is fixed; oldest
entries are dropped when the buffer is full.

Note: this is process-local. Restarting the backend clears it. A
persistent store (PostgreSQL) arrives in Phase 8.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any

MAX_FLOWS = 200

_lock = Lock()
_flows: deque[dict[str, Any]] = deque(maxlen=MAX_FLOWS)


def add_flow(flow: dict[str, Any]) -> dict[str, Any]:
    """Append a flow record. Adds a server-side timestamp."""
    record = {
        **flow,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with _lock:
        _flows.append(record)
    return record


def recent(limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent flows, newest first."""
    with _lock:
        # deque of maxlen MAX_FLOWS; slice the tail.
        items = list(_flows)
    items.reverse()
    return items[:limit]


def count() -> int:
    with _lock:
        return len(_flows)


def clear() -> None:
    with _lock:
        _flows.clear()
