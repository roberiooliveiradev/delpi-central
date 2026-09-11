from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.quality_labels.quality_labels_service import (
    QualityLabelsService,
)


def _service(**overrides: object) -> QualityLabelsService:
    kwargs: dict = {
        "repository": MagicMock(),
        "qr_service": MagicMock(),
        "production_order_use_case": MagicMock(),
        "search_orders_use_case": MagicMock(),
        "order_customer_use_case": MagicMock(),
        "product_query_repository": MagicMock(),
        "audit_metadata_service": MagicMock(),
        "audit_repository": MagicMock(),
    }
    kwargs.update(overrides)
    return QualityLabelsService(**kwargs)


def test_lookup_op_includes_customer_reference_from_product_cadastre() -> None:
    production_uc = MagicMock()
    production_uc.execute.return_value = {
        "order": {
            "production_order": "24671401001",
            "branch": "01",
            "product_code": "90263540",
            "product_description": "CHICOTE P26",
            "order_unit": "MI",
        }
    }
    repo = MagicMock()
    repo.list_by_production_order.return_value = []
    product_query = MagicMock()
    product_query.fetch_product_by_code.return_value = {
        "customer_reference": "  2229-07/1  "
    }
    order_customer = MagicMock()
    order_customer.execute.return_value = None

    service = _service(
        production_order_use_case=production_uc,
        repository=repo,
        product_query_repository=product_query,
        order_customer_use_case=order_customer,
    )

    payload = service.lookup_op(production_order="24671401001", branch="01")

    assert payload["customerReference"] == "2229-07/1"
    product_query.fetch_product_by_code.assert_called_once_with("90263540")


def test_get_public_live_fetches_when_snapshot_lacks_customer_reference() -> None:
    repo = MagicMock()
    repo.get_by_token.return_value = {
        "id": "lbl-1",
        "is_active": True,
        "product_code": "90263540",
        "audit_metadata": {"product": {"code": "90263540"}},
    }
    repo.to_public_payload.return_value = {
        "productCode": "90263540",
        "customerReference": None,
    }
    repo.audit_captured_customer_reference.return_value = False
    product_query = MagicMock()
    product_query.fetch_product_by_code.return_value = {
        "customer_reference": "2229-07/1"
    }

    service = _service(repository=repo, product_query_repository=product_query)
    payload = service.get_public(token="tok")

    assert payload["customerReference"] == "2229-07/1"
    product_query.fetch_product_by_code.assert_called_once_with("90263540")


def test_get_public_does_not_live_fetch_when_snapshot_already_captured_empty() -> None:
    repo = MagicMock()
    repo.get_by_token.return_value = {
        "id": "lbl-1",
        "is_active": True,
        "product_code": "90263540",
        "audit_metadata": {
            "product": {"code": "90263540", "customerReference": None}
        },
    }
    repo.to_public_payload.return_value = {
        "productCode": "90263540",
        "customerReference": None,
    }
    repo.audit_captured_customer_reference.return_value = True
    product_query = MagicMock()

    service = _service(repository=repo, product_query_repository=product_query)
    payload = service.get_public(token="tok")

    assert payload["customerReference"] is None
    product_query.fetch_product_by_code.assert_not_called()
