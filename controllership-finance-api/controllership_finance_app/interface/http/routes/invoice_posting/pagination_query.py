from __future__ import annotations
from typing import Any
from fastapi import Query

_TIERS = {
    "page_20_100": (20, 1, 100),
    "page_25_100": (25, 1, 100),
    "limit_20_50": (20, 1, 50),
}

def PAGE_SIZE_QUERY(tier_id: str = "page_20_100", *, description: str | None = None) -> Any:
    default, ge, le = _TIERS.get(tier_id, (20, 1, 100))
    return Query(default, ge=ge, le=le, description=description)

def LIMIT_QUERY(tier_id: str = "limit_20_50", *, description: str | None = None) -> Any:
    default, ge, le = _TIERS.get(tier_id, (20, 1, 50))
    return Query(default, ge=ge, le=le, description=description)
