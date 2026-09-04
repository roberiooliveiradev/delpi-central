"""Inbound pagination: no literal Query for sized list params."""

from __future__ import annotations

import json
import re
from pathlib import Path

_PARAM_QUERY = re.compile(
    r"(page_size|limit|top_limit|history_limit|details_limit)\s*:\s*[^=]+=\s*Query\s*\("
)

_API_ROOT = Path(__file__).resolve().parents[4]
_HTTP_ROOT = _API_ROOT / "app" / "interface" / "http"


def test_no_literal_pagination_query_in_http_routes() -> None:
    hits: list[str] = []
    for path in _HTTP_ROOT.rglob("*.py"):
        if path.name == "pagination_query.py":
            continue
        text = path.read_text(encoding="utf-8")
        for match in _PARAM_QUERY.finditer(text):
            line = text[: match.start()].count("\n") + 1
            hits.append(f"{path.relative_to(_API_ROOT)}:{line}")
    assert hits == [], f"literal Query pagination params remain: {hits}"


def test_inventory_factories_match_defaults() -> None:
    from app.interface.http.pagination_query import (
        HISTORY_LIMIT_QUERY,
        LIMIT_QUERY,
        PAGE_SIZE_QUERY,
        TOP_LIMIT_QUERY,
    )

    factories = {
        "page_size": PAGE_SIZE_QUERY,
        "limit": LIMIT_QUERY,
        "top_limit": TOP_LIMIT_QUERY,
        "history_limit": HISTORY_LIMIT_QUERY,
    }
    inv = json.loads(
        (_API_ROOT / "app" / "content" / "pagination_inbound_inventory.json").read_text(
            encoding="utf-8"
        )
    )
    assert inv["count"] == 117
    for entry in inv["entries"]:
        query = factories[entry["param"]](entry["tierId"])
        assert query.default == entry["defaultResolved"], entry
