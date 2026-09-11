from __future__ import annotations

from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_repository import (
    PostgresQualityLabelsRepository,
)


def _row(**overrides: object) -> dict:
    base: dict = {
        "id": "lbl-1",
        "public_token": "tok",
        "production_order": "24689101001",
        "branch": "01",
        "product_code": "90300005",
        "product_description": "CABO",
        "product_unit": "UN",
        "order_number": "246891",
        "inspected_at": None,
        "inspector_name": "Inspetor",
        "result": "approved",
        "notes": None,
        "inspected_quantity": 10,
        "view_count": 0,
        "is_active": True,
        "created_at": None,
    }
    base.update(overrides)
    return base


def test_admin_payload_includes_customer_item_from_certificate() -> None:
    payload = PostgresQualityLabelsRepository.to_admin_payload(
        _row(customer_item="2229-07/1", customer_item_rev="00")
    )
    assert payload["productCode"] == "90300005"
    assert payload["customerItem"] == "2229-07/1"
    assert payload["customerItemRev"] == "00"


def test_admin_payload_customer_item_blank_becomes_none() -> None:
    payload = PostgresQualityLabelsRepository.to_admin_payload(
        _row(customer_item="  ", customer_item_rev="")
    )
    assert payload["customerItem"] is None
    assert payload["customerItemRev"] is None


def test_admin_payload_without_certificate_join_has_null_customer_item() -> None:
    payload = PostgresQualityLabelsRepository.to_admin_payload(_row())
    assert payload["customerItem"] is None
    assert payload["customerItemRev"] is None
    assert payload["customerReference"] is None


def test_admin_payload_includes_customer_reference_from_audit_snapshot() -> None:
    payload = PostgresQualityLabelsRepository.to_admin_payload(
        _row(
            audit_metadata={
                "product": {"code": "90300005", "customerReference": "2229-07/1"}
            }
        )
    )
    assert payload["customerReference"] == "2229-07/1"
    assert payload["customerItem"] is None


def test_public_payload_does_not_expose_customer_item() -> None:
    payload = PostgresQualityLabelsRepository.to_public_payload(
        _row(customer_item="2229-07/1")
    )
    assert "customerItem" not in payload
    assert payload["productCode"] == "90300005"
    assert payload["customerReference"] == "2229-07/1"


def test_public_payload_uses_snapshot_when_certificate_item_is_blank() -> None:
    payload = PostgresQualityLabelsRepository.to_public_payload(
        _row(
            customer_item="  ",
            audit_metadata={
                "product": {"code": "90300005", "customerReference": "2229-07/1"}
            },
        )
    )
    assert payload["customerReference"] == "2229-07/1"


def test_public_payload_certificate_item_wins_over_snapshot() -> None:
    payload = PostgresQualityLabelsRepository.to_public_payload(
        _row(
            customer_item="MANUAL-99",
            audit_metadata={
                "product": {"code": "90300005", "customerReference": "2229-07/1"}
            },
        )
    )
    assert payload["customerReference"] == "MANUAL-99"


def test_public_payload_omits_customer_reference_when_absent() -> None:
    payload = PostgresQualityLabelsRepository.to_public_payload(_row())
    assert payload["customerReference"] is None
    assert "customerItem" not in payload
