"""Filtros SQL das movimentações internas SD3."""

from __future__ import annotations

import pytest

from app.application.dto.product.list_product_internal_movements_request import (
    ListProductInternalMovementsRequest,
)
from app.infrastructure.persistence.totvs.product_repositories.product_internal_movements_sql import (
    bind_internal_movement_filters,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def _where(*, kind: str | None = None, tm: str | None = None) -> tuple[str, tuple]:
    qb = QueryBuilder()
    bind_internal_movement_filters(
        qb,
        code="10090482",
        date_start=None,
        date_end=None,
        branch="01",
        location=None,
        tm=tm,
        op=None,
        kind=kind,
    )
    return qb.build()


def test_without_kind_keeps_full_sd3_universe() -> None:
    where, params = _where()
    assert "D_E_L_E_T_ = ''" in where
    assert "D3_ESTORNO" in where
    assert "D3_CF" not in where
    assert "RE0" not in params
    assert "DE0" not in params
    assert params[0] == "10090482"
    assert "01" in params


def test_warehouse_transfer_kind_filters_cf_re0_de0() -> None:
    where, params = _where(kind="warehouse_transfer")
    assert "RTRIM(LTRIM(SD3.D3_CF)) IN" in where
    assert "RE0" in params
    assert "DE0" in params
    assert "PR0" not in params
    assert "999" not in params
    assert "D3_TM" not in where


def test_warehouse_transfer_kind_does_not_add_tm_predicate() -> None:
    where, _params = _where(kind="warehouse_transfer")
    assert "D3_TM" not in where


def test_invalid_kind_is_rejected() -> None:
    with pytest.raises(ValueError):
        ListProductInternalMovementsRequest(code="10090482", kind="consumption")
