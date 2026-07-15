"""Audiência TV declarativa — mergeado em x-delpi.tv no OpenAPI."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_route_audience.json"


@lru_cache(maxsize=1)
def _load_audience_routes() -> dict[str, dict[str, Any]]:
    if not _CONTENT_PATH.is_file():
        return {}
    payload = json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))
    raw = payload.get("routes") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        op = str(key or "").strip()
        if not op or not isinstance(value, dict):
            continue
        cleaned: dict[str, Any] = {}
        when_to_use = str(value.get("whenToUse") or "").strip()
        if when_to_use:
            cleaned["whenToUse"] = when_to_use
        description = str(value.get("description") or "").strip()
        if description:
            cleaned["description"] = description
        label = str(value.get("label") or "").strip()
        if label:
            cleaned["label"] = label
        if cleaned:
            indexed[op] = cleaned
    return indexed


def tv_audience_for_operation(operation_id: str) -> dict[str, Any] | None:
    op = str(operation_id or "").strip()
    if not op:
        return None
    entry = _load_audience_routes().get(op)
    return dict(entry) if entry else None


def reset_tv_route_audience_cache() -> None:
    _load_audience_routes.cache_clear()
