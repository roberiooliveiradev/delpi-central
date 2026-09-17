"""Generic DAVI broker pagination completeness — no operationId coupling."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.application.external_capabilities.dynamic_information.projection import (
    bound_response_payload,
    classify_source_pagination,
    derive_response_completeness,
    source_pagination_proves_partial,
)


def _items(n: int) -> list[dict[str, Any]]:
    return [{"code": f"X{i}", "value": i} for i in range(n)]


@pytest.mark.parametrize(
    ("payload", "expected_state"),
    [
        (
            {
                "page": 1,
                "page_size": 50,
                "total": 123,
                "total_pages": 3,
                "items": _items(50),
            },
            "partial",
        ),
        (
            {
                "page": 3,
                "page_size": 50,
                "total": 123,
                "total_pages": 3,
                "items": _items(23),
            },
            "partial",
        ),
        (
            {
                "page": 1,
                "page_size": 50,
                "total": 3,
                "total_pages": 1,
                "items": _items(3),
            },
            "complete",
        ),
        (
            {
                "page": 1,
                "page_size": 50,
                "total": 0,
                "total_pages": 0,
                "items": [],
            },
            "complete",
        ),
        (
            {
                "page": 1,
                "page_size": 50,
                "total": 0,
                "total_pages": 1,
                "items": [],
            },
            "complete",
        ),
        ({"items": _items(3)}, "absent"),
        ({"page": 1, "page_size": 50, "items": _items(3)}, "unknown"),
        ({"page": 0, "total": 10, "total_pages": 1, "items": _items(1)}, "unknown"),
        ({"total": -1, "total_pages": 1, "items": _items(1)}, "unknown"),
        ({"total": "123", "total_pages": 3, "items": _items(50)}, "unknown"),
        ({"page": 2, "total_pages": 1, "items": _items(1)}, "unknown"),
        ({"page_size": 0, "items": _items(1)}, "unknown"),
        ({"total": 1, "items": _items(3)}, "unknown"),
        ({"total": 10, "total_pages": 0, "items": _items(1)}, "unknown"),
    ],
)
def test_classify_source_pagination_matrix(payload, expected_state):
    assert classify_source_pagination(payload) == expected_state


def test_source_pagination_proves_partial_compat_mapping():
    assert source_pagination_proves_partial(
        {
            "page": 1,
            "page_size": 50,
            "total": 123,
            "total_pages": 3,
            "items": _items(50),
        }
    ) is True
    assert source_pagination_proves_partial(
        {
            "page": 1,
            "page_size": 50,
            "total": 3,
            "total_pages": 1,
            "items": _items(3),
        }
    ) is False
    assert source_pagination_proves_partial({"items": _items(3)}) is None
    assert source_pagination_proves_partial(
        {"page": 0, "total": "bad", "items": _items(1)}
    ) is None


def test_multipage_first_page_incomplete():
    payload = {
        "page": 1,
        "page_size": 50,
        "total": 123,
        "total_pages": 3,
        "items": _items(50),
    }
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is True
    assert bounded["data"]["is_complete"] is False
    assert bounded["data"]["truncated"] is True
    assert len(bounded["data"]["items"]) == 50


def test_multipage_middle_and_last_page_incomplete():
    middle = {
        "page": 2,
        "page_size": 50,
        "total": 123,
        "total_pages": 3,
        "items": _items(50),
    }
    last = {
        "page": 3,
        "page_size": 50,
        "total": 123,
        "total_pages": 3,
        "items": _items(23),
    }
    for payload in (middle, last):
        bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
        assert bounded["is_complete"] is False
        assert bounded["truncated"] is True


def test_single_page_complete():
    payload = {
        "page": 1,
        "page_size": 50,
        "total": 3,
        "total_pages": 1,
        "items": _items(3),
    }
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert bounded["is_complete"] is True
    assert bounded["truncated"] is False


def test_empty_dataset_complete():
    for total_pages in (0, 1):
        payload = {
            "page": 1,
            "page_size": 50,
            "total": 0,
            "total_pages": total_pages,
            "items": [],
        }
        bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
        assert bounded["is_complete"] is True
        assert bounded["truncated"] is False


def test_malformed_under_cap_is_unknown_not_complete():
    """Architecture residual: present-but-invalid meta under cap → false/false."""
    payload = {
        "page": 0,
        "page_size": 50,
        "total": "bad",
        "total_pages": -1,
        "items": _items(3),
    }
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert len(bounded["data"]["items"]) == 3
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is False


def test_insufficient_pagination_meta_is_unknown():
    payload = {
        "page": 1,
        "page_size": 50,
        "items": _items(3),
    }
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {"page": 2, "total_pages": 1, "items": _items(1)},
        {"page_size": 0, "items": _items(1)},
        {"total": -1, "items": _items(1)},
        {"total": "10", "items": _items(1)},
        {"total": 1, "items": _items(3)},
        {"total": 10, "total_pages": 0, "items": _items(1)},
    ],
)
def test_contradictory_or_invalid_meta_is_unknown(payload):
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is False


def test_legacy_items_only_remains_complete():
    payload = {"items": _items(3)}
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert bounded["is_complete"] is True
    assert bounded["truncated"] is False


def test_source_false_and_truncated_are_sticky():
    sticky_false = {
        "page": 1,
        "page_size": 50,
        "total": 3,
        "total_pages": 1,
        "items": _items(3),
        "is_complete": False,
    }
    sticky_trunc = {
        "page": 1,
        "page_size": 50,
        "total": 3,
        "total_pages": 1,
        "items": _items(3),
        "truncated": True,
    }
    for payload in (sticky_false, sticky_trunc):
        bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
        assert bounded["is_complete"] is False
        assert bounded["truncated"] is True


def test_optimistic_source_true_overridden_by_pagination():
    payload = {
        "page": 1,
        "page_size": 50,
        "total": 123,
        "total_pages": 3,
        "items": _items(50),
        "is_complete": True,
        "truncated": False,
    }
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is True


def test_optimistic_source_true_overridden_by_unknown_meta():
    payload = {
        "page": 0,
        "page_size": 50,
        "total": "bad",
        "total_pages": -1,
        "items": _items(3),
        "is_complete": True,
        "truncated": False,
    }
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is False


def test_davi_item_slice_forces_incomplete():
    payload = {
        "page": 1,
        "page_size": 50,
        "total": 40,
        "total_pages": 1,
        "items": _items(40),
    }
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=20)
    assert len(bounded["data"]["items"]) == 20
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is True


def test_davi_byte_bound_forces_incomplete():
    payload = {
        "page": 1,
        "page_size": 50,
        "total": 3,
        "total_pages": 1,
        "items": [{"code": "A" * 200, "blob": "B" * 400} for _ in range(3)],
    }
    bounded = bound_response_payload(payload, max_bytes=120, max_items=50)
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is True
    assert bounded["data"] is None or bounded.get("error") or (
        isinstance(bounded["data"], dict) and bounded["data"]["truncated"] is True
    )


def test_malformed_plus_davi_slice_is_partial():
    payload = {
        "page": 0,
        "total": "bad",
        "total_pages": -1,
        "items": _items(60),
    }
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert len(bounded["data"]["items"]) == 50
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is True


def test_multipage_plus_davi_item_slice():
    payload = {
        "page": 1,
        "page_size": 50,
        "total": 123,
        "total_pages": 3,
        "items": _items(50),
    }
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=10)
    assert len(bounded["data"]["items"]) == 10
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is True


def test_non_paginated_scalar_preserved():
    payload = {"product": {"code": "X"}, "summary": {"ok": True}}
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert bounded["is_complete"] is True
    assert bounded["truncated"] is False


def test_metamorphic_partial_and_unknown_are_endpoint_agnostic():
    partial_base = {
        "page": 1,
        "page_size": 10,
        "total": 123,
        "total_pages": 13,
        "items": _items(10),
    }
    unknown_base = {
        "page": 0,
        "page_size": 50,
        "total": "bad",
        "total_pages": -1,
        "items": _items(3),
    }
    labels = (
        "imaginary.parents",
        "imaginary.stock",
        "future.unknown.action",
        "/products/{code}/parents",
        "get_product_parents",
    )
    for base, expected in ((partial_base, (False, True)), (unknown_base, (False, False))):
        outcomes = []
        for label in labels:
            payload = dict(base)
            payload["_imagined_endpoint"] = label
            outcomes.append(derive_response_completeness(payload))
            bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
            outcomes.append((bounded["is_complete"], bounded["truncated"]))
        assert len(set(outcomes)) == 1
        assert outcomes[0] == expected


def test_derive_helper_has_no_operation_coupling():
    source = (
        Path(__file__).resolve().parents[1]
        / "app/application/external_capabilities/dynamic_information/projection.py"
    ).read_text(encoding="utf-8")
    for banned in (
        "get_product_parents",
        "get_product_guide",
        "product_parents",
        "operation_id",
        "operationId",
        "/parents",
        "where_used",
        "where-used",
    ):
        assert banned not in source
