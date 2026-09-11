"""Normalize physical hardware identity fields from firmware payloads."""

from __future__ import annotations

import re
from typing import Any

_MAC_HEX = re.compile(r"[^0-9A-Fa-f]")


def normalize_mac_address(value: str | None) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    hex_only = _MAC_HEX.sub("", raw)
    if len(hex_only) != 12:
        return None
    parts = [hex_only[i : i + 2].upper() for i in range(0, 12, 2)]
    return ":".join(parts)


def normalize_hardware_uid(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip().upper()
    if not cleaned:
        return None
    if len(cleaned) > 64:
        cleaned = cleaned[:64]
    return cleaned


def normalize_controller_code(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        return None
    if len(cleaned) > 64:
        cleaned = cleaned[:64]
    return cleaned


def extract_identity_fields(body: dict[str, Any] | None) -> dict[str, str | None]:
    """Pull identity keys from a firmware JSON body (contador or status)."""
    if not isinstance(body, dict):
        return {
            "hardware_uid": None,
            "controller_code": None,
            "mac_address": None,
        }
    uid = body.get("hardwareUid") or body.get("hardware_uid")
    code = body.get("controllerCode") or body.get("codigoControlador") or body.get("equipamento")
    mac = body.get("mac")
    return {
        "hardware_uid": normalize_hardware_uid(str(uid) if uid is not None else None),
        "controller_code": normalize_controller_code(str(code) if code is not None else None),
        "mac_address": normalize_mac_address(str(mac) if mac is not None else None),
    }


def classify_identity(
    *,
    hardware_uid: str | None,
    controller_code: str | None,
    mac_address: str | None,
) -> tuple[str, str, str | None]:
    """
    Returns (canonical_key_kind, identity_confidence, identity_source).

    canonical resolution key preference:
      hardware_uid > controller_code > mac > none
    """
    if hardware_uid:
        return "hardware_uid", "strong", "firmware_hardware_uid"
    if controller_code:
        return "controller_code", "controller_code", "controller_code"
    if mac_address:
        return "mac", "mac_fallback", "mac"
    return "none", "legacy_unknown", "legacy"
