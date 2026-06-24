from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_CONTENT_PATH = (
    Path(__file__).resolve().parents[3] / "content" / "supplies_stock_hybrid.json"
)


@lru_cache(maxsize=1)
def _bundle() -> dict:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def process_warehouse_locations() -> tuple[str, ...]:
    raw = _bundle().get("processWarehouseLocations") or []
    return tuple(str(item).strip() for item in raw if str(item).strip())


def note(key: str, **kwargs: str) -> str:
    template = str((_bundle().get("notes") or {}).get(key) or "")
    if kwargs:
        return template.format(**kwargs)
    return template
