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

    assert chip == {"label": "01", "kind": "warehouse", "value": "01"}


def test_chips_from_overlay():
    chips = ChatManualContextPinService.chips_from_overlay(
        {"lastEntities": {"branch": "02", "warehouse": "01", "productCode": "10080001"}}
    )

    assert {chip["kind"] for chip in chips} == {"branch", "warehouse", "product"}
