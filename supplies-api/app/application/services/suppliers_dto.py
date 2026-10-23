"""Supplier BFF contracts — input allowlists and LGPD-safe projection.

Policy: CPF (11 digits) is personal data and is never published in full by the
BFF; CNPJ (14 digits) is public corporate registry data and may be displayed.
Visual-only masking is not sufficient — projection happens here, backend-side.
"""

from __future__ import annotations

import re
import uuid
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
    # X4.FIELDS.E3 — 29 fields with POST persistence proven in the E2
    # DELPI_TST01 homologation assay; mirrors the api-delpi contract.
    "address_number",
    "po_box",
    "icms_contributor",
    "simples_nacional",
    "cnae_code",
    "legal_entity_type",
    "simp_regime_code",
    "pb_regime_code",
    "inss_withholding",
    "iss_withholding",
    "csll_withholding",
    "cofins_withholding",
    "pis_withholding",
    "irf_calculation",
    "inp_calculation",
    "tax_group_code",
    "commercial_contact_name",
    "fax",
    "website",
    "responsible_name",
    "risk_code",
    "swift_code",
    "purchase_price_table_code",
    "carrier_code",
    "segment_code",
    "administrator_code",
    "linked_customer_code",
    "linked_customer_store",
    "linked_employee_code",
}

# PO decision (F3.3) + E5 homologation: cadastral POST fields editable via
# PUT except the fiscal document and the identity fields (code/store), plus
# the 26 fields that proved PUT persistence in DELPI_TST01 (X4.FIELDS.E5).
# simp_regime_code / linked_customer_code / linked_customer_store stay OUT —
# upstream PUT did not prove a controlled change for them.
PUT_SUPPLIER_FIELDS = {
    "person_type",
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
    # X4.FIELDS.E5 — PUT_PERSISTENCE_PROVEN em DELPI_TST01
    "address_number",
    "po_box",
    "commercial_contact_name",
    "fax",
    "website",
    "responsible_name",
    "icms_contributor",
    "simples_nacional",
    "inss_withholding",
    "iss_withholding",
    "csll_withholding",
    "cofins_withholding",
    "pis_withholding",
    "irf_calculation",
    "inp_calculation",
    "tax_group_code",
    "legal_entity_type",
    "pb_regime_code",
    "cnae_code",
    "risk_code",
    "swift_code",
    "purchase_price_table_code",
    "carrier_code",
    "segment_code",
    "administrator_code",
    "linked_employee_code",
    # X4.FIELDS.E6 — retestes DELPI_TST01
    # simp_regime_code: PUT_PERSISTENCE_PROVEN.
    # linked_customer_store: PUT_PERSISTENCE_PROVEN no par composto.
    # linked_customer_code: entra como companion — upstream ignora mudança
    # de código via PUT; a api-delpi fixa o valor atual (rejeita divergente).
    "simp_regime_code",
    "linked_customer_code",
    "linked_customer_store",
}

# Identity/document fields — rejected explicitly, never silently dropped.
PUT_PROTECTED_FIELDS = {"tax_id", "supplier_code", "supplier_store"}

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
        "legal_entity_type",
    ),
    "address": (
        "address",
        "address_number",
        "district",
        "postal_code",
        "po_box",
        "city",
        "city_code",
        "state",
    ),
    "contact": (
        "contact_name",
        "commercial_contact_name",
        "responsible_name",
        "area_code",
        "phone",
        "fax",
        "email",
        "website",
    ),
    # Fiscal/tributário — campos E3 com persistência comprovada em homologação.
    "fiscal": (
        "state_registration",
        "municipal_registration",
        "rohs_indicator",
        "icms_contributor",
        "simples_nacional",
        "cnae_code",
        "simp_regime_code",
        "pb_regime_code",
        "tax_group_code",
        "inss_withholding",
        "iss_withholding",
        "csll_withholding",
        "cofins_withholding",
        "pis_withholding",
        "irf_calculation",
        "inp_calculation",
    ),
    # Compras e relacionamentos — referências e vínculos.
    "purchasing": (
        "payment_condition_code",
        "payment_method_code",
        "financial_nature_code",
        "accounting_account",
        "country_code",
        "bacen_country_code",
        "purchase_price_table_code",
        "risk_code",
        "swift_code",
        "carrier_code",
        "segment_code",
        "administrator_code",
        "linked_customer_code",
        "linked_customer_store",
        "linked_employee_code",
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


_OPERATION_OUTCOME = {
    "CREATED": "sent",
    "SENDING": "sent",
    "ACKNOWLEDGED": "acknowledged",
    "CONFIRMED": "confirmed",
    "UNKNOWN": "indeterminate",
    "REJECTED": "rejected",
    "FAILED_PRE_SEND": "rejected",
    "RECONCILIATION_REQUIRED": "reconciliation_required",
}


def normalize_operation_id(value: Any) -> str:
    try:
        return str(uuid.UUID(str(value).strip()))
    except (TypeError, ValueError) as exc:
        raise ValueError("operation_id must be a UUID") from exc


def project_operation(data: Any) -> dict[str, Any]:
    """Safe UX-facing projection of an api-delpi tracked write operation.

    Server-side sanitization already redacts payloads; the BFF further
    minimizes to status/outcome evidence — never raw payloads, hashes or
    caller internals.
    """
    if not isinstance(data, dict):
        data = {}
    status = str(data.get("status") or "").upper()
    error_details = data.get("error_details")
    evidence = data.get("confirmation_evidence")
    tracking_warning = None
    if isinstance(error_details, dict) and error_details.get("code"):
        tracking_warning = str(error_details["code"])
    elif isinstance(evidence, dict) and evidence.get("result") not in (None, "match"):
        tracking_warning = str(evidence["result"])
    return {
        "operation_id": data.get("operation_id"),
        "status": status or None,
        "outcome": _OPERATION_OUTCOME.get(status, "indeterminate"),
        "persistence_proven": status == "CONFIRMED",
        "tracking_warning": tracking_warning,
        "http_status": data.get("http_status"),
        "resource_key": data.get("resource_key"),
        "correlation_id": data.get("correlation_id"),
        "created_at": data.get("created_at"),
        "acknowledged_at": data.get("acknowledged_at"),
        "confirmed_at": data.get("confirmed_at"),
    }


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
    lowered = {str(k).strip().lower() for k in source}
    forbidden = IDENTITY_FORBIDDEN_FIELDS & lowered
    if forbidden:
        raise ValueError("protheus identity fields are not client-provided")
    protected = PUT_PROTECTED_FIELDS & lowered
    if protected:
        raise ValueError(
            "supplier identity/document fields are immutable: "
            + ", ".join(sorted(protected))
        )
    unknown = {k for k in source if str(k) not in PUT_SUPPLIER_FIELDS}
    if unknown:
        raise ValueError(
            "fields not editable via PUT: " + ", ".join(sorted(str(k) for k in unknown))
        )
    if not source:
        raise ValueError("no editable supplier field provided")
    return dict(source)
