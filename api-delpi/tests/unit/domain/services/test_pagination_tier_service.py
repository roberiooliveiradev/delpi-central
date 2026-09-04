from __future__ import annotations

import pytest

from app.domain.services.pagination_tier_service import (
    PaginationTierService,
    PaginationTierServiceError,
)


def setup_function() -> None:
    PaginationTierService.clear_cache()


def test_pagination_tiers_catalog_has_expected_count() -> None:
    ids = PaginationTierService.tier_ids()
    assert len(ids) >= 29
    assert "page_50_500" in ids
    assert "page_optional_500" in ids
    assert "limit_rol_8000" in ids
    assert "infra_offset_50_1000" in ids


def test_get_page_50_500() -> None:
    tier = PaginationTierService.get("page_50_500")
    assert tier.param == "page_size"
    assert tier.default == 50
    assert tier.ge == 1
    assert tier.le == 500
    assert tier.optional is False


def test_clamp_respects_bounds() -> None:
    assert PaginationTierService.clamp("page_50_200", 1) == 1
    assert PaginationTierService.clamp("page_50_200", 50) == 50
    assert PaginationTierService.clamp("page_50_200", 999) == 200
    assert PaginationTierService.clamp("page_50_200", 0) == 1
    assert PaginationTierService.clamp("page_50_200", None) == 50


def test_optional_tier_preserves_none() -> None:
    assert PaginationTierService.clamp("page_optional_500", None) is None
    assert PaginationTierService.clamp("page_optional_500", 600) == 500
    assert PaginationTierService.clamp("page_optional_open", None) is None
    assert PaginationTierService.clamp("page_optional_open", 9999) == 9999


def test_require_int_and_unknown() -> None:
    assert PaginationTierService.require_int("limit_rol_8000", None) == 8000
    assert PaginationTierService.require_int("limit_freight_20000", 50000) == 20000
    with pytest.raises(PaginationTierServiceError):
        PaginationTierService.get("does_not_exist")


def test_inventory_tiers_resolve() -> None:
    import json
    from pathlib import Path

    inv = json.loads(
        (
            Path(__file__).resolve().parents[4]
            / "app"
            / "content"
            / "pagination_inbound_inventory.json"
        ).read_text()
    )
    for entry in inv["entries"]:
        tier = PaginationTierService.get(entry["tierId"])
        assert tier.param == entry["param"]
        assert tier.default == entry["defaultResolved"]
        assert tier.le == entry["leResolved"]
