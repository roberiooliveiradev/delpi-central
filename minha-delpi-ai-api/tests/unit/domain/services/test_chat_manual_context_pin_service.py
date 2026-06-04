import pytest

from app.domain.services.chat_manual_context_pin_service import ChatManualContextPinService


def test_normalize_branch_pin():
    result = ChatManualContextPinService.normalize_pin(kind="branch", value="02")

    assert result == ("branch", "02")


def test_normalize_warehouse_pin():
    result = ChatManualContextPinService.normalize_pin(kind="warehouse", value="01")

    assert result == ("warehouse", "01")


def test_normalize_product_pin():
    result = ChatManualContextPinService.normalize_pin(kind="product", value="10080001")

    assert result == ("product", "10080001")


def test_rejects_invalid_product():
    assert ChatManualContextPinService.normalize_pin(kind="product", value="abc") is None


def test_build_chip_labels():
    chip = ChatManualContextPinService.build_chip(kind="warehouse", value="01")

    assert chip == {"label": "01", "kind": "context", "value": "01"}


def test_chips_from_overlay():
    chips = ChatManualContextPinService.chips_from_overlay(
        {
            "userContextItems": [
                {
                    "id": "b1",
                    "kind": "context",
                    "label": "02",
                    "content": "filial 02",
                    "extractedEntities": {"branch": "02"},
                },
                {
                    "id": "p1",
                    "kind": "context",
                    "label": "10080001",
                    "content": "10080001",
                    "extractedEntities": {"productCode": "10080001"},
                },
            ],
        }
    )

    assert {chip["kind"] for chip in chips} == {"context"}
    assert {chip["value"] for chip in chips} == {"02", "10080001"}
