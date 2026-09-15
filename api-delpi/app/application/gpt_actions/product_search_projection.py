"""Fail-closed projection of product search items for Custom GPT V1."""

from __future__ import annotations

from typing import Any, Mapping

from app.application.gpt_actions.constants import GPT_SEARCH_FIELD_MAP


def project_product_search_item(item: Any) -> dict[str, Any]:
    """Map an internal product row to the approved GPT allowlist only."""
    if hasattr(item, "to_dict") and callable(item.to_dict):
        raw = item.to_dict()
    elif isinstance(item, Mapping):
        raw = dict(item)
    else:
        raw = vars(item)

    projected: dict[str, Any] = {}
    for gpt_field, source_field in GPT_SEARCH_FIELD_MAP.items():
        value = raw.get(source_field)
        projected[gpt_field] = value
    return projected


def project_product_search_page(page_payload: Mapping[str, Any]) -> dict[str, Any]:
    items = page_payload.get("items") or []
    return {
        "items": [project_product_search_item(item) for item in items],
        "page": page_payload.get("page"),
        "page_size": page_payload.get("page_size"),
        "total": page_payload.get("total"),
        "total_pages": page_payload.get("total_pages"),
    }
