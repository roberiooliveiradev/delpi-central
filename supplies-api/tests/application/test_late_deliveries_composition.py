from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.services.late_deliveries_composition_service import (
    LateDeliveriesCompositionService,
)
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError


def _user(*, permissions: set[str] | None = None, is_superadmin: bool = False) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions or {"supplies.access"},
        is_superadmin=is_superadmin,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


def _panel(
    *,
    branch: str,
    items: list[dict],
    total: int | None = None,
    page: int = 1,
    page_size: int = 20,
    summary: dict | None = None,
) -> dict:
    total_value = total if total is not None else len(items)
    return {
        "branch": branch,
        "product_type": "MP",
        "summary": summary
        or {
            "total_lines": total_value,
            "on_time_lines": 0,
            "late_lines": total_value,
            "purchase_order_otd_pct": 0.0,
            "late_percentage": 100.0,
        },
        "lines": {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total_value,
            "total_pages": 1 if total_value else 0,
        },
    }


def test_single_branch_passthrough_does_not_recalculate_summary():
    reads = MagicMock()
    reads.get_purchase_order_otd_panel.return_value = _panel(
        branch="01",
        items=[{"branch": "01", "order_number": "1", "status": "late", "days_diff": -2}],
        summary={
            "total_lines": 10,
            "on_time_lines": 8,
            "late_lines": 2,
            "purchase_order_otd_pct": 80.0,
            "late_percentage": 20.0,
        },
    )
    service = LateDeliveriesCompositionService(
        delpi_reads=reads,
        today_provider=lambda: date(2026, 9, 15),
    )
    result = service.compose(
        _user(),
        branches=["01"],
        status="late",
        start_date="2026-09-01",
        end_date="2026-09-30",
        page=1,
        page_size=20,
        sort_by=None,
        sort_dir=None,
    )
    assert result["branch"] == "01"
    assert result["summary"]["total_lines"] == 10
    assert result["summary"]["late_lines"] == 2
    assert result["items"][0]["order_number"] == "1"
    assert result["applied_filters"]["branches"] == ["01"]
    assert result["applied_filters"]["status"] == "late"
    kwargs = reads.get_purchase_order_otd_panel.call_args.kwargs
    assert kwargs["branch"] == "01"
    assert kwargs["status"] == "late"


def test_defaults_use_current_month_and_late_and_both_units():
    reads = MagicMock()

    def _side_effect(**kwargs):
        branch = kwargs["branch"]
        return _panel(
            branch=branch,
            items=[
                {
                    "branch": branch,
                    "order_number": f"{branch}-1",
                    "order_item": "0001",
                    "status": "late",
                    "expected_delivery_date": "2026-09-10",
                    "days_diff": -1,
                }
            ],
            summary={
                "total_lines": 1,
                "on_time_lines": 0,
                "late_lines": 1,
                "purchase_order_otd_pct": 0.0,
                "late_percentage": 100.0,
            },
        )

    reads.get_purchase_order_otd_panel.side_effect = _side_effect
    service = LateDeliveriesCompositionService(
        delpi_reads=reads,
        today_provider=lambda: date(2026, 9, 15),
    )
    result = service.compose(
        _user(),
        branches=None,
        status=None,
        start_date=None,
        end_date=None,
        page=None,
        page_size=None,
        sort_by=None,
        sort_dir=None,
    )
    assert result["applied_filters"]["branches"] == ["01", "02"]
    assert result["applied_filters"]["status"] == "late"
    assert result["applied_filters"]["start_date"] == "2026-09-01"
    assert result["applied_filters"]["end_date"] == "2026-09-30"
    assert result["applied_filters"]["page"] == 1
    assert result["applied_filters"]["page_size"] == 20
    assert result["branch"] == "consolidated"
    branches_called = [
        call.kwargs["branch"] for call in reads.get_purchase_order_otd_panel.call_args_list
    ]
    assert branches_called == ["01", "02"]
    assert all(call.kwargs["branch"] for call in reads.get_purchase_order_otd_panel.call_args_list)


def test_consolidated_interleaved_global_page_two():
    """Page > 1 must reflect global order across 01+02, not concat of local pages."""
    reads = MagicMock()

    def _side_effect(**kwargs):
        branch = kwargs["branch"]
        if branch == "01":
            items = [
                {
                    "branch": "01",
                    "order_number": "A",
                    "order_item": "0001",
                    "status": "late",
                    "expected_delivery_date": "2026-09-20",
                    "days_diff": -1,
                },
                {
                    "branch": "01",
                    "order_number": "C",
                    "order_item": "0001",
                    "status": "late",
                    "expected_delivery_date": "2026-09-10",
                    "days_diff": -3,
                },
            ]
        else:
            items = [
                {
                    "branch": "02",
                    "order_number": "B",
                    "order_item": "0001",
                    "status": "late",
                    "expected_delivery_date": "2026-09-15",
                    "days_diff": -2,
                },
                {
                    "branch": "02",
                    "order_number": "D",
                    "order_item": "0001",
                    "status": "late",
                    "expected_delivery_date": "2026-09-05",
                    "days_diff": -4,
                },
            ]
        return _panel(branch=branch, items=items)

    reads.get_purchase_order_otd_panel.side_effect = _side_effect
    service = LateDeliveriesCompositionService(
        delpi_reads=reads,
        today_provider=lambda: date(2026, 9, 15),
    )
    # Default sort: status DESC, expected_delivery_date DESC → A(20), B(15), C(10), D(05)
    page1 = service.compose(
        _user(),
        branches=["01", "02"],
        status="late",
        start_date="2026-09-01",
        end_date="2026-09-30",
        page=1,
        page_size=2,
        sort_by=None,
        sort_dir=None,
    )
    page2 = service.compose(
        _user(),
        branches=["01", "02"],
        status="late",
        start_date="2026-09-01",
        end_date="2026-09-30",
        page=2,
        page_size=2,
        sort_by=None,
        sort_dir=None,
    )
    assert [row["order_number"] for row in page1["items"]] == ["A", "B"]
    assert [row["order_number"] for row in page2["items"]] == ["C", "D"]
    assert page2["total"] == 4
    assert page2["total_pages"] == 2
    assert page2["page"] == 2


def test_consolidated_never_calls_producer_without_branch():
    reads = MagicMock()
    reads.get_purchase_order_otd_panel.side_effect = lambda **kwargs: _panel(
        branch=kwargs["branch"],
        items=[],
        total=0,
        summary={
            "total_lines": 0,
            "on_time_lines": 0,
            "late_lines": 0,
            "purchase_order_otd_pct": None,
            "late_percentage": 0.0,
        },
    )
    service = LateDeliveriesCompositionService(
        delpi_reads=reads,
        today_provider=lambda: date(2026, 9, 15),
    )
    service.compose(
        _user(),
        branches=[],
        status="late",
        start_date="2026-09-01",
        end_date="2026-09-30",
        page=1,
        page_size=20,
        sort_by=None,
        sort_dir=None,
    )
    for call in reads.get_purchase_order_otd_panel.call_args_list:
        assert call.kwargs["branch"] in {"01", "02"}
        assert call.kwargs["branch"]


def test_unknown_branch_raises_value_error():
    service = LateDeliveriesCompositionService(
        delpi_reads=MagicMock(),
        today_provider=lambda: date(2026, 9, 15),
    )
    with pytest.raises(ValueError, match="Unknown branch"):
        service.compose(
            _user(),
            branches=["99"],
            status="late",
            start_date="2026-09-01",
            end_date="2026-09-30",
            page=1,
            page_size=20,
            sort_by=None,
            sort_dir=None,
        )


def test_invalid_status_raises_value_error():
    service = LateDeliveriesCompositionService(
        delpi_reads=MagicMock(),
        today_provider=lambda: date(2026, 9, 15),
    )
    with pytest.raises(ValueError, match="Invalid status"):
        service.compose(
            _user(),
            branches=["01"],
            status="tomorrow",
            start_date="2026-09-01",
            end_date="2026-09-30",
            page=1,
            page_size=20,
            sort_by=None,
            sort_dir=None,
        )


def test_forbidden_without_access():
    service = LateDeliveriesCompositionService(
        delpi_reads=MagicMock(),
        today_provider=lambda: date(2026, 9, 15),
    )
    with pytest.raises(AuthorizationError):
        service.compose(
            _user(permissions={"supplies.manage"}),
            branches=["01"],
            status="late",
            start_date="2026-09-01",
            end_date="2026-09-30",
            page=1,
            page_size=20,
            sort_by=None,
            sort_dir=None,
        )


def test_consolidated_one_leg_failure_propagates():
    reads = MagicMock()

    def _side_effect(**kwargs):
        if kwargs["branch"] == "02":
            raise DelpiApiGatewayError("api-delpi server error", status_code=503)
        return _panel(branch="01", items=[], total=0)

    reads.get_purchase_order_otd_panel.side_effect = _side_effect
    service = LateDeliveriesCompositionService(
        delpi_reads=reads,
        today_provider=lambda: date(2026, 9, 15),
    )
    with pytest.raises(DelpiApiGatewayError):
        service.compose(
            _user(),
            branches=["01", "02"],
            status="late",
            start_date="2026-09-01",
            end_date="2026-09-30",
            page=1,
            page_size=20,
            sort_by=None,
            sort_dir=None,
        )


def test_gateway_panel_requires_concrete_branch():
    from app.infrastructure.gateways.supplies_delpi_reads import SuppliesDelpiReads

    gateway = MagicMock()
    reads = SuppliesDelpiReads(gateway=gateway)
    with pytest.raises(ValueError, match="branch is required"):
        reads.get_purchase_order_otd_panel(
            access_token="tok",
            branch="",
            start_date="2026-09-01",
            end_date="2026-09-30",
            status="late",
            page=1,
            page_size=20,
        )
    gateway.get.assert_not_called()
