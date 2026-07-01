from __future__ import annotations

from typing import Any

DELPI_CONTACT_AREAS = frozenset({"comercial", "qualidade", "pcp", "engenharia", "outro"})

DELPI_CONTACT_AREA_LABELS = {
    "comercial": "Comercial",
    "qualidade": "Qualidade",
    "pcp": "PCP",
    "engenharia": "Engenharia",
    "outro": "Outro",
}

PLAN_CONTACT_ROLE_FIELDS = (
    "customer_contact",
    "customer_contact_email",
    "customer_contact_phone",
    "delpi_contact_name",
    "delpi_contact_area",
    "delpi_sales_rep",
    "delpi_quality_contact",
)


def _text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _payload(plan: dict[str, Any]) -> dict[str, Any]:
    raw = plan.get("template_payload") or {}
    return raw if isinstance(raw, dict) else {}


def resolve_customer_contact_name(plan: dict[str, Any]) -> str | None:
    payload = _payload(plan)
    explicit = _text(plan.get("customer_contact"))
    attention = _text(payload.get("attention_to"))
    delpi_name = _text(plan.get("delpi_contact_name"))

    if explicit and delpi_name:
        return explicit
    if explicit and attention and explicit != attention and not delpi_name:
        return attention
    return explicit or attention


def resolve_customer_contact_email(plan: dict[str, Any]) -> str | None:
    payload = _payload(plan)
    return _text(plan.get("customer_contact_email")) or _text(payload.get("attention_email"))


def resolve_customer_contact_phone(plan: dict[str, Any]) -> str | None:
    payload = _payload(plan)
    return _text(plan.get("customer_contact_phone")) or _text(payload.get("customer_contact_phone"))


def resolve_delpi_primary_contact_name(plan: dict[str, Any]) -> str | None:
    payload = _payload(plan)
    explicit = (
        _text(plan.get("delpi_contact_name"))
        or _text(plan.get("delpi_sales_rep"))
        or _text(payload.get("delpi_contact_name"))
        or _text(payload.get("delpi_sales_rep"))
    )
    if explicit:
        return explicit

    legacy_customer = _text(plan.get("customer_contact"))
    legacy_attention = _text(payload.get("attention_to"))
    if legacy_customer and legacy_attention and legacy_customer != legacy_attention:
        return legacy_customer
    return None


def resolve_delpi_contact_phone(plan: dict[str, Any]) -> str | None:
    payload = _payload(plan)
    return _text(payload.get("contact_phone")) or _text(payload.get("delpi_contact_phone"))


def resolve_delpi_contact_area(plan: dict[str, Any]) -> str | None:
    return _text(plan.get("delpi_contact_area")) or _text(_payload(plan).get("delpi_contact_area"))


def resolve_delpi_quality_contact(plan: dict[str, Any]) -> str | None:
    return _text(plan.get("delpi_quality_contact")) or _text(_payload(plan).get("delpi_quality_contact"))


def format_delpi_contact_area_label(area: str | None) -> str | None:
    if not area:
        return None
    return DELPI_CONTACT_AREA_LABELS.get(area, area)


def build_contact_roles_view(plan: dict[str, Any]) -> dict[str, str | None]:
    return {
        "customer_contact": resolve_customer_contact_name(plan),
        "customer_contact_email": resolve_customer_contact_email(plan),
        "customer_contact_phone": resolve_customer_contact_phone(plan),
        "delpi_contact_name": resolve_delpi_primary_contact_name(plan),
        "delpi_contact_area": resolve_delpi_contact_area(plan),
        "delpi_contact_area_label": format_delpi_contact_area_label(resolve_delpi_contact_area(plan)),
        "delpi_sales_rep": _text(plan.get("delpi_sales_rep")) or _text(_payload(plan).get("delpi_sales_rep")),
        "delpi_quality_contact": resolve_delpi_quality_contact(plan),
        "delpi_contact_phone": resolve_delpi_contact_phone(plan),
    }


def pick_plan_contact_fields(data: dict[str, Any]) -> dict[str, Any]:
    return {key: data[key] for key in PLAN_CONTACT_ROLE_FIELDS if data.get(key) is not None}


def merge_attention_fields_into_template_payload(
    template_payload: dict[str, Any] | None,
    *,
    customer_contact: str | None = None,
    customer_contact_email: str | None = None,
    customer_contact_phone: str | None = None,
) -> dict[str, Any]:
    payload = dict(template_payload or {})
    if customer_contact is not None:
        payload["attention_to"] = customer_contact
    if customer_contact_email is not None:
        payload["attention_email"] = customer_contact_email
    if customer_contact_phone is not None:
        payload["customer_contact_phone"] = customer_contact_phone
    return payload
