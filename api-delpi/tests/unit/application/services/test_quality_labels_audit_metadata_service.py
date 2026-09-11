from __future__ import annotations

from unittest.mock import MagicMock

from app.application.services.quality_labels.quality_labels_audit_metadata_service import (
    QualityLabelsAuditMetadataService,
)


def _service(
    *,
    product_query: MagicMock | None = None,
    order_customer: MagicMock | None = None,
    product_customers: MagicMock | None = None,
) -> tuple[QualityLabelsAuditMetadataService, dict[str, MagicMock]]:
    production_uc = MagicMock()
    production_uc.execute.return_value = {
        "order": {
            "production_order": "10278501001",
            "branch": "02",
            "product_code": "90263901",
        },
        "linked_orders": [{"production_order": "10278501002"}],
        "link_summary": {"total_pi_orders": 1},
    }
    structure_uc = MagicMock()
    structure_uc.execute.return_value = {"root": {"code": "90263901"}, "items": []}
    guide_uc = MagicMock()
    guide_uc.execute.return_value = {"items": [{"operation": "10"}]}
    inspection_uc = MagicMock()
    inspection_uc.execute.return_value = {"items": [{"has_inspection": True}]}
    query = product_query or MagicMock()
    order_uc = order_customer or MagicMock()
    if order_customer is None:
        order_uc.execute.return_value = None
    customers = product_customers or MagicMock()
    if product_customers is None:
        customers.fetch_latest_customer_by_product.return_value = None
    service = QualityLabelsAuditMetadataService(
        production_order_use_case=production_uc,
        structure_use_case=structure_uc,
        guide_use_case=guide_uc,
        inspection_use_case=inspection_uc,
        product_query_repository=query,
        order_customer_use_case=order_uc,
        product_customers_repository=customers,
        max_depth=6,
    )
    return service, {
        "product_query": query,
        "order_customer": order_uc,
        "product_customers": customers,
    }


def test_build_audit_metadata_includes_op_product_and_sources():
    product_query = MagicMock()
    product_query.fetch_product_by_code.return_value = {
        "product_code": "90263901",
        "customer_reference": "  2229-07/1  ",
        "drawing_code": "  10014878060  ",
    }
    service, deps = _service(product_query=product_query)

    payload = service.build(production_order="10278501001", branch="02")

    assert payload["snapshotVersion"] == 1
    assert payload["productionOrder"]["order"]["product_code"] == "90263901"
    assert payload["product"]["code"] == "90263901"
    assert payload["product"]["customerReference"] == "2229-07/1"
    assert payload["product"]["drawingCode"] == "10014878060"
    assert payload["customer"] is None
    assert payload["product"]["structure"]["root"]["code"] == "90263901"
    assert payload["product"]["routing"]["items"][0]["operation"] == "10"
    assert payload["product"]["inspection"]["items"][0]["has_inspection"] is True
    assert any(src["operationId"] == "get_product" and src["ok"] is True for src in payload["sources"])
    assert payload["errors"] == []
    deps["product_query"].fetch_product_by_code.assert_called_once_with("90263901")


def test_build_audit_metadata_keeps_empty_customer_reference():
    product_query = MagicMock()
    product_query.fetch_product_by_code.return_value = {
        "product_code": "90263901",
        "customer_reference": "   ",
    }
    service, _ = _service(product_query=product_query)

    payload = service.build(production_order="10278501001", branch="02")

    assert payload["product"]["customerReference"] is None
    assert payload["product"]["drawingCode"] is None
    assert "drawingCode" in payload["product"]
    assert any(src["operationId"] == "get_product" and src["ok"] is True for src in payload["sources"])
    assert payload["errors"] == []


def test_build_audit_metadata_records_product_header_failure():
    product_query = MagicMock()
    product_query.fetch_product_by_code.side_effect = RuntimeError("TOTVS timeout")
    service, _ = _service(product_query=product_query)

    payload = service.build(production_order="10278501001", branch="02")

    assert payload["product"]["customerReference"] is None
    assert payload["product"]["structure"]["root"]["code"] == "90263901"
    assert any(err["operationId"] == "get_product" for err in payload["errors"])
    assert any(
        src["operationId"] == "get_product" and src["ok"] is False
        for src in payload["sources"]
    )


def test_build_audit_metadata_prefers_sales_order_customer():
    order_customer = MagicMock()
    order_customer.execute.return_value = {
        "customer_code": "000206",
        "customer_store": "01",
        "customer_name": "THERMOSTAR",
        "customer_legal_name": "THERMO STAR EQUIPAMENTOS LTDA",
    }
    product_customers = MagicMock()
    service, deps = _service(
        order_customer=order_customer,
        product_customers=product_customers,
    )

    payload = service.build(production_order="10278501001", branch="02")

    assert payload["customer"]["name"] == "THERMOSTAR"
    assert payload["customer"]["source"] == "sales_order"
    deps["product_customers"].fetch_latest_customer_by_product.assert_not_called()


def test_build_audit_metadata_uses_last_sale_when_op_has_no_customer():
    product_customers = MagicMock()
    product_customers.fetch_latest_customer_by_product.return_value = {
        "customer_code": "000206",
        "customer_store": "01",
        "customer_name": "THERMOSTAR",
        "customer_legal_name": "THERMO STAR EQUIPAMENTOS LTDA",
    }
    service, _ = _service(product_customers=product_customers)

    payload = service.build(production_order="10278501001", branch="02")

    assert payload["customer"]["name"] == "THERMOSTAR"
    assert payload["customer"]["source"] == "last_sale"
    product_customers.fetch_latest_customer_by_product.assert_called_once_with("90263901")


def test_build_audit_metadata_keeps_customer_none_when_no_totvs_name():
    service, _ = _service()

    payload = service.build(production_order="10278501001", branch="02")

    assert payload["customer"] is None
