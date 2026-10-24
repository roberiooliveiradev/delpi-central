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
    assert inv["count"] == 122
    for entry in inv["entries"]:
        query = factories[entry["param"]](entry["tierId"])
        assert query.default == entry["defaultResolved"], entry


def test_new_pagination_tiers_preserve_contract_defaults_and_caps() -> None:
    """No implicit DAVI 50->100 widening or LNF 25->20 default regression."""
    from app.domain.services.pagination_tier_service import PaginationTierService
    from app.interface.http.pagination_query import PAGE_SIZE_QUERY

    expected = {
        "page_50_50": (50, 1, 50),
        "page_25_100": (25, 1, 100),
    }
    for tier_id, (default, lower, upper) in expected.items():
        tier = PaginationTierService.get(tier_id)
        assert tier.param == "page_size"
        assert (tier.default, tier.ge, tier.le) == (default, lower, upper)
        query = PAGE_SIZE_QUERY(tier_id)
        assert query.default == default


def test_new_pagination_tiers_are_in_authoritative_inventory() -> None:
    from app.domain.services.pagination_tier_service import PaginationTierService

    inv = json.loads(
        (_API_ROOT / "app" / "content" / "pagination_inbound_inventory.json").read_text(
            encoding="utf-8"
        )
    )
    expected = {
        "page_50_50": ("gpt_actions_routes.py", 50),
        "page_25_100": ("lancamento_notas_fiscais_router.py", 25),
    }
    for tier_id, (filename, default) in expected.items():
        entries = [row for row in inv["entries"] if row["tierId"] == tier_id]
        assert len(entries) == 1, tier_id
        assert entries[0]["file"].endswith(filename)
        assert entries[0]["defaultResolved"] == default
        assert PaginationTierService.get(tier_id).default == default
