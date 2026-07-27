"""Unit — ordenação da listagem de NCs LMP."""

from __future__ import annotations

from app.domain.services.lmp.lmp_nonconformity_list_sort import (
    resolve_lmp_nc_order_by,
)


def test_default_sort_is_occurrence_date_desc() -> None:
    key, direction, sql = resolve_lmp_nc_order_by(None, None)
    assert key == "occurrence_date"
    assert direction == "desc"
    assert "n.occurrence_date DESC" in sql


def test_unknown_sort_falls_back() -> None:
    key, direction, _sql = resolve_lmp_nc_order_by("hack);--", "up")
    assert key == "occurrence_date"
    assert direction == "desc"


def test_allowed_sort_asc() -> None:
    key, direction, sql = resolve_lmp_nc_order_by("customer_name", "asc")
    assert key == "customer_name"
    assert direction == "asc"
    assert "n.customer_name ASC" in sql
