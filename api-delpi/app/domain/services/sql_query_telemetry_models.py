from __future__ import annotations

from dataclasses import dataclass

_PREVIEW_LEN = 160


@dataclass(frozen=True)
class SqlQueryRecord:
    query_hash: str
    duration_ms: float
    operation_id: str | None
    caller_app: str | None
    repository: str
    recorded_at: str
    preview: str


def normalize_query(query: str) -> str:
    return " ".join(query.split())


def preview_query(query: str) -> str:
    compact = normalize_query(query)
    if len(compact) <= _PREVIEW_LEN:
        return compact
    return compact[: _PREVIEW_LEN - 1] + "…"
