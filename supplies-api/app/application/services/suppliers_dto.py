"""Supplier BFF contracts — input allowlists and LGPD-safe projection.

Policy: CPF (11 digits) is personal data and is never published in full by the
BFF; CNPJ (14 digits) is public corporate registry data and may be displayed.
Visual-only masking is not sufficient — projection happens here, backend-side.
"""

from __future__ import annotations

import re
from typing import Any

POST_SUPPLIER_FIELDS = {
    "supplier_store",
    "person_type",
    "tax_id",
    "supplier_name",
    "supplier_short_name",
    "address",
    "district",
    "postal_code",
    "state",
    "city",
    "city_code",
    "area_code",
    "phone",
    "state_registration",
    "municipal_registration",
    "contact_name",
    "email",
    "payment_condition_code",
    "country_code",
    "bacen_country_code",
    "accounting_account",
    "financial_nature_code",
    "rohs_indicator",
    "payment_method_code",
}

PUT_SUPPLIER_FIELDS = {"supplier_name", "supplier_short_name"}

IDENTITY_FORBIDDEN_FIELDS = {"codusr", "user_id", "usr_id", "protheus_user_id"}

LIST_ITEM_FIELDS = (
    "supplier_id",
    "supplier_code",
    "supplier_store",
    "supplier_name",
    "supplier_short_name",
    "state",
    "blocked",
)

_DETAIL_SECTION_FIELDS = {
    "identification": (
        "supplier_code",
        "supplier_store",
        "supplier_name",
        "supplier_short_name",
        "person_type",
    ),
    "address": ("address", "district", "postal_code", "city", "city_code", "state"),
    "contact": ("contact_name", "area_code", "phone", "email"),
    "fiscal": ("state_registration", "municipal_registration", "rohs_indicator"),
    "purchasing": (
        "payment_condition_code",
        "payment_method_code",
        "financial_nature_code",
        "accounting_account",
        "country_code",
        "bacen_country_code",
    ),
}


def digits_only(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def mask_tax_id(tax_id: Any) -> dict[str, Any]:
    """Backend LGPD projection for tax documents.

    Returns ``{"tax_id": ..., "tax_id_masked": bool}``. CPF is fully masked;
    CNPJ (public registry) is published as digits.
    """
    digits = digits_only(tax_id)
    if not digits:
        return {"tax_id": None, "tax_id_masked": False}
    if len(digits) == 14:
        return {"tax_id": digits, "tax_id_masked": False}
    return {"tax_id": "*" * len(digits), "tax_id_masked": True}


def project_list_item(item: dict[str, Any]) -> dict[str, Any]:
    projected = {k: item.get(k) for k in LIST_ITEM_FIELDS}
    projected.update(mask_tax_id(item.get("tax_id")))
    return projected


def project_list_envelope(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"items": [], "total": 0}
    items = data.get("items")
    projected = dict(data)
    projected["items"] = [
        project_list_item(i) if isinstance(i, dict) else i for i in items or []
    ]
    return projected


def project_detail(data: Any) -> dict[str, Any]:
    """Curated Supplier 360 projection — publishes only known contract fields."""
    source = data
    if isinstance(data, dict) and isinstance(data.get("fornecedor"), dict):
        source = data["fornecedor"]
    if isinstance(data, dict) and isinstance(data.get("fornecedor"), list):
        first = data["fornecedor"][0] if data["fornecedor"] else {}
        source = first if isinstance(first, dict) else {}
    if not isinstance(source, dict):
        source = {}

    sections = {
        name: {f: source.get(f) for f in fields if source.get(f) is not None}
        for name, fields in _DETAIL_SECTION_FIELDS.items()
    }
    out: dict[str, Any] = {
        "supplier_id": source.get("supplier_id"),
        "supplier_code": source.get("supplier_code") or source.get("code"),
        "supplier_store": source.get("supplier_store") or source.get("store"),
        "blocked": bool(source.get("blocked", source.get("msblql") == "1")),
        "sections": sections,
    }
    out.update(mask_tax_id(source.get("tax_id")))
    return out


def normalize_supplier_id(code: Any, store: Any) -> str:
    code_digits = digits_only(code)
    store_digits = digits_only(store)
    if not code_digits or not store_digits:
        raise ValueError("supplier code and store are required")
    if len(code_digits) > 6 or len(store_digits) > 2:
        raise ValueError("supplier code max 6 digits, store max 2 digits")
    return code_digits.zfill(6) + store_digits.zfill(2)


def sanitize_post_body(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise ValueError("request body must be a JSON object")
    source = body.get("fornecedor", body)
    if not isinstance(source, dict):
        raise ValueError("fornecedor must be a JSON object")
    forbidden = IDENTITY_FORBIDDEN_FIELDS & source.keys()
    if forbidden:
        raise ValueError("protheus identity fields are not client-provided")
    return {k: v for k, v in source.items() if k in POST_SUPPLIER_FIELDS}


def sanitize_put_body(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise ValueError("request body must be a JSON object")
    source = body.get("fornecedor", body)
    if not isinstance(source, dict):
        raise ValueError("fornecedor must be a JSON object")
    forbidden = IDENTITY_FORBIDDEN_FIELDS & source.keys()
    if forbidden:
        raise ValueError("protheus identity fields are not client-provided")
    allowed = {k: v for k, v in source.items() if k in PUT_SUPPLIER_FIELDS}
    if not allowed:
        raise ValueError("no editable supplier field provided")
    return allowed
