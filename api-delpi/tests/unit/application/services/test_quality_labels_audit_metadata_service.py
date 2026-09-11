from __future__ import annotations

from unittest.mock import MagicMock

from app.application.services.quality_labels.quality_labels_audit_metadata_service import (
    QualityLabelsAuditMetadataService,
)


def _service(
    *,
    product_query: MagicMock | None = None,
    structure_ok: bool = True,
) -> tuple[QualityLabelsAuditMetadataService, MagicMock]:
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
    if structure_ok:
        structure_uc.execute.return_value = {"root": {"code": "90263901"}, "items": []}
    guide_uc = MagicMock()
    guide_uc.execute.return_value = {"items": [{"operation": "10"}]}
    inspection_uc = MagicMock()
    inspection_uc.execute.return_value = {"items": [{"has_inspection": True}]}
    query = product_query or MagicMock()
    service = QualityLabelsAuditMetadataService(
        production_order_use_case=production_uc,
        structure_use_case=structure_uc,
        guide_use_case=guide_uc,
        inspection_use_case=inspection_uc,
        product_query_repository=query,
        max_depth=6,
    )
    return service, query


def test_build_audit_metadata_includes_op_product_and_sources():
    product_query = MagicMock()
    product_query.fetch_product_by_code.return_value = {
        "product_code": "90263901",
        "customer_reference": "  2229-07/1  ",
    }
    service, _ = _service(product_query=product_query)

    payload = service.build(production_order="10278501001", branch="02")

    assert payload["snapshotVersion"] == 1
    assert payload["productionOrder"]["order"]["product_code"] == "90263901"
    assert payload["product"]["code"] == "90263901"
    assert payload["product"]["customerReference"] == "2229-07/1"
    assert payload["product"]["structure"]["root"]["code"] == "90263901"
    assert payload["product"]["routing"]["items"][0]["operation"] == "10"
    assert payload["product"]["inspection"]["items"][0]["has_inspection"] is True
    assert len(payload["sources"]) == 5
    assert payload["sources"][0]["operationId"] == "get_production_order_by_op"
    assert payload["sources"][1]["operationId"] == "get_product"
    assert payload["sources"][1]["ok"] is True
    assert payload["errors"] == []
    product_query.fetch_product_by_code.assert_called_once_with("90263901")


def test_build_audit_metadata_keeps_empty_customer_reference():
    product_query = MagicMock()
    product_query.fetch_product_by_code.return_value = {
        "product_code": "90263901",
        "customer_reference": "   ",
    }
    service, _ = _service(product_query=product_query)

    payload = service.build(production_order="10278501001", branch="02")

    assert payload["product"]["customerReference"] is None
    assert payload["sources"][1]["operationId"] == "get_product"
    assert payload["sources"][1]["ok"] is True
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
