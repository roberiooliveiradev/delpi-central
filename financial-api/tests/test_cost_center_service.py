from __future__ import annotations

import pytest

from financial_app.application.services.cost_center_service import (
    CostCenterService,
    InvalidCostCenterQuery,
)
from financial_app.domain.errors import BranchAccessDenied, InvalidBranch
from tests.conftest import full_user, user
from tests.fakes import FakeFinancialGateway


def build() -> tuple[CostCenterService, FakeFinancialGateway]:
    gateway = FakeFinancialGateway()
    return CostCenterService(gateway), gateway


def test_filters_are_normalized() -> None:
    service, _ = build()
    result = service.filters(full_user(), branch="01", start_date=None, end_date=None)

    assert result["branch"] == "01"
    assert result["branches"][0] == {"code": "01", "label": "Matriz SC"}
    assert result["costCenters"][0] == {"code": "1101", "label": "MANUTENCAO"}
    assert result["suppliers"][0]["label"] == "FORNECEDOR X LTDA"


def test_summary_maps_business_fields() -> None:
    service, _ = build()
    result = service.summary(
        full_user(),
        branch="01",
        start_date="2026-08-01",
        end_date="2026-08-22",
        cost_center=None,
        supplier_code=None,
        supplier_store=None,
    )

    assert result["totalAmount"] == 450_000.0
    assert result["entryCount"] == 320
    assert result["averageTicket"] == 1_406.25


def test_series_and_rankings() -> None:
    service, _ = build()
    series = service.series(
        full_user(),
        branch=None,
        start_date=None,
        end_date=None,
        cost_center=None,
        supplier_code=None,
        supplier_store=None,
    )
    assert series["items"][0]["yearMonth"] == "2026-08"
    assert series["items"][0]["totalAmount"] == 450_000.0

    centers = service.ranking_cost_centers(
        full_user(),
        branch=None,
        start_date=None,
        end_date=None,
        supplier_code=None,
        supplier_store=None,
        limit=None,
    )
    assert centers["items"][0]["code"] == "1101"
    assert centers["limit"] == 10

    suppliers = service.ranking_suppliers(
        full_user(),
        branch=None,
        start_date=None,
        end_date=None,
        cost_center=None,
        limit=999,
    )
    assert suppliers["items"][0]["label"] == "FORNECEDOR X LTDA"
    assert suppliers["limit"] == 50


def test_entries_map_and_paginate() -> None:
    service, gateway = build()
    result = service.entries(
        full_user(),
        branch="01",
        start_date="2026-08-01",
        end_date="2026-08-22",
        cost_center="1101",
        supplier_code=None,
        supplier_store=None,
        search="rolamento",
        page=1,
        page_size=9999,
        sort_by="valor_total",
        sort_dir="asc",
    )

    assert result["pagination"]["pageSize"] == 50
    assert result["items"][0]["id"] == "998877"
    assert result["items"][0]["totalAmount"] == 1_000.0
    assert result["items"][0]["costCenterLabel"] == "MANUTENCAO"
    assert gateway.call_kwargs("fetch_cost_center_entries")["page_size"] == 200
    assert gateway.call_kwargs("fetch_cost_center_entries")["sort_by"] == "valor_total"


def test_branch_gate_blocks_other_branch() -> None:
    service, _ = build()
    only_first = user(
        "financial.access", "financial.cost-centers.view", "financial.view.filial-01"
    )
    with pytest.raises(BranchAccessDenied):
        service.summary(
            only_first,
            branch="02",
            start_date=None,
            end_date=None,
            cost_center=None,
            supplier_code=None,
            supplier_store=None,
        )

    with pytest.raises(BranchAccessDenied):
        service.summary(
            only_first,
            branch=None,
            start_date=None,
            end_date=None,
            cost_center=None,
            supplier_code=None,
            supplier_store=None,
        )


def test_invalid_branch_and_sort_are_rejected() -> None:
    service, _ = build()
    with pytest.raises(InvalidBranch):
        service.series(
            full_user(),
            branch="99",
            start_date=None,
            end_date=None,
            cost_center=None,
            supplier_code=None,
            supplier_store=None,
        )

    with pytest.raises(InvalidCostCenterQuery):
        service.entries(
            full_user(),
            branch="01",
            start_date=None,
            end_date=None,
            cost_center=None,
            supplier_code=None,
            supplier_store=None,
            search=None,
            page=1,
            page_size=50,
            sort_by="1; DELETE FROM SD1010",
            sort_dir="desc",
        )


def test_summary_forwards_exclude_mp_products() -> None:
    service, gateway = build()
    service.summary(
        full_user(),
        branch="01",
        start_date="2026-08-01",
        end_date="2026-08-31",
        cost_center=None,
        supplier_code=None,
        supplier_store=None,
        exclude_mp_products=True,
    )
    assert gateway.call_kwargs("fetch_cost_center_summary")["exclude_mp_products"] is True


def test_requires_cost_center_permission() -> None:
    service, _ = build()
    with pytest.raises(PermissionError):
        service.filters(
            user("financial.access"), branch="01", start_date=None, end_date=None
        )


def test_default_period_is_applied_when_omitted() -> None:
    service, gateway = build()
    service.summary(
        full_user(),
        branch="01",
        start_date=None,
        end_date=None,
        cost_center=None,
        supplier_code=None,
        supplier_store=None,
    )
    kwargs = gateway.call_kwargs("fetch_cost_center_summary")
    assert kwargs["start_date"] and kwargs["end_date"]
    assert kwargs["start_date"] < kwargs["end_date"]
