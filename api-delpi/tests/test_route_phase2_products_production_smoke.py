"""Smoke Fase 2 — products playbooks + production operacional restantes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_PRODUCTS = "app.interface.http.routes.product_routes"
_OPERATIONAL = "app.interface.http.routes.production.production_operational_router"
_PRODUCTION = "app.interface.http.routes.production.production_router"


def _product_payload(**extra):
    base = {"product": {"code": "90269001", "description": "Item teste"}}
    base.update(extra)
    return base


@patch(f"{_PRODUCTS}.build_get_product_last_purchase_use_case")
def test_product_last_purchase_returns_meta(mock_build) -> None:
    from app.interface.http.routes.product_routes import get_last_purchase

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value=_product_payload(last_purchase={}))
    )
    response = get_last_purchase(code="90269001", branch=None)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_product_last_purchase",
        shape="playbook_report",
    )


@patch(f"{_PRODUCTS}.build_get_product_purchase_price_history_use_case")
def test_product_purchase_price_history_returns_meta(mock_build) -> None:
    from app.interface.http.routes.product_routes import get_purchase_price_history

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value=_product_payload(history=[]))
    )
    response = get_purchase_price_history(
        code="90269001",
        start_date=None,
        end_date=None,
        date_start=None,
        date_end=None,
        branch=None,
        history_limit=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_product_purchase_price_history",
        shape="playbook_report",
    )


@patch(f"{_PRODUCTS}.build_get_product_purchase_budget_history_use_case")
def test_product_purchase_budget_history_returns_meta(mock_build) -> None:
    from app.interface.http.routes.product_routes import get_purchase_budget_history

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value=_product_payload(history=[]))
    )
    response = get_purchase_budget_history(
        code="90269001",
        start_date=None,
        end_date=None,
        date_start=None,
        date_end=None,
        branch=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_product_purchase_budget_history",
        shape="playbook_report",
    )


@patch(f"{_PRODUCTS}.build_get_product_raw_material_price_intelligence_use_case")
def test_product_raw_material_price_intelligence_returns_meta(mock_build) -> None:
    from app.interface.http.routes.product_routes import (
        get_raw_material_price_intelligence,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value=_product_payload(intelligence={}))
    )
    response = get_raw_material_price_intelligence(
        code="90269001",
        start_date=None,
        end_date=None,
        date_start=None,
        date_end=None,
        branch=None,
        history_limit=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_product_raw_material_price_intelligence",
        shape="composite_analysis",
    )


@patch(f"{_PRODUCTS}.build_get_product_shipping_status_use_case")
def test_product_shipping_status_returns_meta(mock_build) -> None:
    from app.interface.http.routes.product_routes import get_shipping_status

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"code": "90269001", "status": "ok"})
    )
    response = get_shipping_status(
        code="90269001",
        reference_date=None,
        start_date=None,
        end_date=None,
        date_start=None,
        date_end=None,
        branch=None,
        legacy=False,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_product_shipping_status",
        shape="playbook_report",
    )


@patch(f"{_PRODUCTS}.build_list_product_purchases")
def test_product_purchases_returns_meta(mock_build) -> None:
    from app.interface.http.routes.product_routes import purchases

    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "items": [],
                "page": 1,
                "page_size": 50,
                "total": 0,
                "total_pages": 0,
            }
        )
    )
    response = purchases(code="90269001", page=1, page_size=50)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_product_purchases",
        shape="paged_list",
    )


@patch(f"{_PRODUCTS}.build_get_product_sales_summary")
def test_product_sales_summary_returns_meta(mock_build) -> None:
    from app.interface.http.routes.product_routes import product_sales_summary

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"total": 0})
    )
    response = product_sales_summary(code="90269001")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_product_sales_summary",
        shape="scalar",
    )


@patch(f"{_PRODUCTS}.build_get_product_sales_open_orders")
def test_product_sales_open_orders_returns_meta(mock_build) -> None:
    from app.interface.http.routes.product_routes import product_sales_open_orders

    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "items": [],
                "page": 1,
                "page_size": 50,
                "total": 0,
                "total_pages": 0,
            }
        )
    )
    response = product_sales_open_orders(code="90269001")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_product_sales_open_orders",
        shape="paged_list",
    )


@patch(f"{_OPERATIONAL}.build_get_production_order_by_op_use_case")
def test_production_order_by_op_returns_meta(mock_build) -> None:
    from app.interface.http.routes.production.production_operational_router import (
        get_production_order_by_op,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"production_order": "OP1", "items": []})
    )
    response = get_production_order_by_op(
        production_order="OP1",
        branch=None,
        product_type=None,
        linked_sort_by=None,
        linked_sort_dir="asc",
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_production_order_by_op",
        shape="playbook_report",
    )


@patch(f"{_OPERATIONAL}.build_get_production_losses_records_use_case")
def test_production_losses_records_returns_meta(mock_build) -> None:
    from app.interface.http.routes.production.production_operational_router import (
        get_losses_records,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"items": [], "summary": {}})
    )
    response = get_losses_records(
        start_date=None,
        end_date=None,
        date_start=None,
        date_end=None,
        branch=None,
        limit=None,
        loss_type="both",
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_production_losses_records",
        shape="playbook_report",
    )


@patch(f"{_OPERATIONAL}.build_get_production_work_center_order_summary_use_case")
def test_production_work_center_order_summary_returns_meta(mock_build) -> None:
    from app.interface.http.routes.production.production_operational_router import (
        get_work_center_order_summary,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"items": []})
    )
    response = get_work_center_order_summary(
        reference_date=None, branch=None, limit=None
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_production_work_center_order_summary",
        shape="playbook_report",
    )


@patch(f"{_OPERATIONAL}.build_get_production_consumption_top_items_by_work_center_use_case")
def test_production_consumption_top_items_by_work_center_returns_meta(mock_build) -> None:
    from app.interface.http.routes.production.production_operational_router import (
        get_consumption_top_items_by_work_center,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"items": []})
    )
    response = get_consumption_top_items_by_work_center(
        start_date=None,
        end_date=None,
        date_start=None,
        date_end=None,
        branch=None,
        work_center=None,
        limit=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_production_consumption_top_items_by_work_center",
        shape="playbook_report",
    )


@patch(f"{_PRODUCTION}.build_get_production_oee_appointment_by_id_use_case")
def test_production_oee_appointment_by_id_returns_meta(mock_build) -> None:
    from app.interface.http.routes.production.production_router import (
        get_production_oee_appointment_by_id,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"appointment_id": 1, "oee": 0.8})
    )
    response = get_production_oee_appointment_by_id(appointment_id=1, branch=None)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_production_oee_appointment_by_id",
        shape="composite_analysis",
    )


@patch(f"{_PRODUCTION}.build_get_eficiencia_fabril_appointments_use_case")
def test_eficiencia_fabril_appointments_returns_meta(mock_build) -> None:
    from app.interface.http.routes.production.production_router import (
        get_eficiencia_fabril_appointments,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"items": [], "page": 1, "total": 0})
    )
    response = get_eficiencia_fabril_appointments(
        start_date=None,
        end_date=None,
        date_start=None,
        date_end=None,
        branch=None,
        op=None,
        employee=None,
        work_center=None,
        status_ok_only=False,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="list_eficiencia_fabril_appointments",
        shape="paged_list",
    )


@patch(f"{_OPERATIONAL}.build_list_production_machine_program_top_intermediates_use_case")
def test_production_machine_program_top_intermediates_returns_meta(mock_build) -> None:
    from app.interface.http.routes.production.production_operational_router import (
        list_machine_program_top_intermediates,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "items": [],
                "page": 1,
                "page_size": 50,
                "total": 0,
                "total_pages": 0,
                "summary": {},
            }
        )
    )
    response = list_machine_program_top_intermediates(
        branch="01",
        start_date=None,
        end_date=None,
        date_start=None,
        date_end=None,
        page=1,
        page_size=50,
        search=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="list_production_machine_program_top_intermediates",
        shape="paged_list",
    )
