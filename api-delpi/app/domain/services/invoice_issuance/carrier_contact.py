"""Formatação do contato da transportadora (SA4) para a ficha de emissão."""
from __future__ import annotations

import re
from typing import Any


def format_carrier_phone(*, ddd: str | None = None, phone: str | None = None) -> str | None:
    tel = str(phone or "").strip()
    if not tel:
        return None
    area = re.sub(r"\D", "", str(ddd or ""))
    if area and area not in re.sub(r"\D", "", tel):
        return f"({area}) {tel}"
    return tel


def format_carrier_address(
    *,
    street: str | None = None,
    district: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
) -> str | None:
    street_text = str(street or "").strip()
    district_text = str(district or "").strip()
    city_text = str(city or "").strip()
    state_text = str(state or "").strip()
    zip_digits = re.sub(r"\D", "", str(zip_code or ""))
    city_state = (
        f"{city_text}-{state_text}"
        if city_text and state_text
        else (city_text or state_text)
    )
    locality = ", ".join(part for part in (district_text, city_state) if part)
    zip_text = ""
    if zip_digits:
        zip_fmt = (
            f"{zip_digits[:5]}-{zip_digits[5:]}"
            if len(zip_digits) == 8
            else zip_digits
        )
        zip_text = f"CEP {zip_fmt}"
    chunks = [part for part in (street_text, locality, zip_text) if part]
    return ", ".join(chunks) or None


def carrier_snapshot_fields(carrier: dict[str, Any] | None) -> dict[str, Any]:
    if not carrier:
        return {
            "carrier_code": None,
            "carrier_name": None,
            "carrier_legal_name": None,
            "carrier_tax_id": None,
            "carrier_address": None,
            "carrier_phone": None,
        }
    return {
        "carrier_code": carrier.get("carrier_code") or None,
        "carrier_name": carrier.get("carrier_name") or None,
        "carrier_legal_name": carrier.get("legal_name") or None,
        "carrier_tax_id": carrier.get("tax_id") or None,
        "carrier_address": carrier.get("address") or None,
        "carrier_phone": carrier.get("phone") or None,
    }


def enrich_request_carrier(request: dict[str, Any], live: dict[str, Any] | None) -> dict[str, Any]:
    if not live:
        return request
    snapshot = carrier_snapshot_fields(live)
    out = dict(request)
    for key, value in snapshot.items():
        if value and not out.get(key):
            out[key] = value
    return out
