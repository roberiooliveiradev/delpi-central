"""Generic DAVI broker pagination completeness — no operationId coupling."""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.application.external_capabilities.dynamic_information.projection import (
    bound_response_payload,
    derive_response_completeness,
    source_pagination_proves_partial,
)


def _items(n: int) -> list[dict[str, Any]]:
    return [{"code": f"X{i}", "value": i} for i in range(n)]


@pytest.mark.parametrize(
    ("payload", "expected_partial"),
    [
        (
            {
                "page": 1,
                "page_size": 50,
                "total": 123,
                "total_pages": 3,
                "items": _items(50),
            },
            True,
        ),
        (
            {
                "page": 2,
                "page_size": 50,
                "total": 123,
                "total_pages": 3,
                "items": _items(50),
            },
            True,
        ),
        (
            {
                "page": 3,
                "page_size": 50,
                "total": 123,
                "total_pages": 3,
                "items": _items(23),
            },
            True,
        ),
        (
            {
                "page": 1,
                "page_size": 50,
                "total": 3,
                "total_pages": 1,
                "items": _items(3),
            },
            False,
        ),
        (
            {
                "page": 1,
                "page_size": 50,
                "total": 0,
                "total_pages": 0,
                "items": [],
            },
            False,
        ),
        (
            {
                "page": 1,
                "page_size": 50,
                "total": 0,
                "total_pages": 1,
                "items": [],
            },
            False,
        ),
        ({"items": _items(3)}, None),
        ({"page": 0, "total": 10, "total_pages": 1, "items": _items(1)}, None),
        ({"total": -1, "total_pages": 1, "items": _items(1)}, None),
        ({"total": "123", "total_pages": 3, "items": _items(50)}, None),
    ],
)
def test_source_pagination_proves_partial_matrix(payload, expected_partial):
    assert source_pagination_proves_partial(payload) is expected_partial


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
    assert bounded["data"]["is_complete"] is True
    assert bounded["data"]["truncated"] is False


def test_empty_dataset_complete():
    payload = {
        "page": 1,
        "page_size": 50,
        "total": 0,
        "total_pages": 0,
        "items": [],
    }
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
    assert "is_complete" not in bounded["data"] or bounded["data"].get("is_complete") is True


def test_legacy_list_without_pagination_meta_complete_when_under_cap():
    payload = {"items": _items(3)}
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert bounded["is_complete"] is True
    assert bounded["truncated"] is False


def test_malformed_meta_does_not_force_complete_over_davi_truncation():
    payload = {
        "page": 0,
        "total": "bad",
        "total_pages": -1,
        "items": _items(60),
    }
    bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
    assert bounded["is_complete"] is False
    assert bounded["truncated"] is True


def test_metamorphic_endpoint_name_does_not_change_completeness():
    """Same pagination payload → same completeness regardless of imagined endpoint."""
    base = {
        "page": 1,
        "page_size": 10,
        "total": 123,
        "total_pages": 13,
        "items": _items(10),
    }
    outcomes = []
    for label in (
        "imaginary.parents",
        "imaginary.stock",
        "future.unknown.action",
        "/products/{code}/parents",
        "get_product_parents",
    ):
        payload = dict(base)
        payload["_imagined_endpoint"] = label  # ignored by generic bounding
        outcomes.append(
            derive_response_completeness(payload)
        )
        bounded = bound_response_payload(payload, max_bytes=65536, max_items=50)
        outcomes.append((bounded["is_complete"], bounded["truncated"]))
    assert len(set(outcomes)) == 1
    assert outcomes[0] == (False, True)


def test_derive_helper_has_no_operation_coupling():
    from pathlib import Path

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
