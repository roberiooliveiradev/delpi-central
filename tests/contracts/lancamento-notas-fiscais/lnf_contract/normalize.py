"""Normalização para golden. Valores voláteis viram marcadores estáveis."""

from __future__ import annotations

import re
from typing import Any

_ID_KEYS = re.compile(
    r"(^id$|_id$|Id$|request_id|user_id|document_id|existing_request_id|access_key|stored_name)$",
    re.IGNORECASE,
)
_TS_KEYS = re.compile(r"(at$|_at$|date$|_date$|timestamp|createdAt|updatedAt|executed_at|received_at)", re.IGNORECASE)
_USER_KEYS = re.compile(
    r"(user_id|user_name|assignee_name|actor_name|created_by(_name)?|cancelled_by(_name)?|email)$",
    re.IGNORECASE,
)
_DOC_KEYS = re.compile(r"(tax_id|cpf|cnpj|document_tax|federal_tax)$", re.IGNORECASE)
_VOLATILE_KEYS = re.compile(r"^(total|count|page|page_size|pages|elapsed|duration|cooldown)", re.IGNORECASE)
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
_DIGITS_DOC = re.compile(r"^\d{11}$|^\d{14}$")


def mask(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {k: mask(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [mask(item, key) for item in value]
    if key and _ID_KEYS.search(key):
        return "<id>"
    if key and _TS_KEYS.search(key):
        return "<ts>"
    if key and _USER_KEYS.search(key):
        return "<user>"
    if key and _DOC_KEYS.search(key):
        return "<tax_id>"
    if key and _VOLATILE_KEYS.search(key):
        return "<volatile>"
    if isinstance(value, str) and _UUID.match(value):
        return "<id>"
    if isinstance(value, str):
        digits = re.sub(r"\D", "", value)
        if len(digits) in {11, 14} and _DIGITS_DOC.match(digits):
            return "<tax_id>"
    return value


def type_tree(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: type_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        if not value:
            return []
        return [type_tree(value[0])]
    if value is None:
        return "null"
    return type(value).__name__


def envelope_snapshot(body: dict) -> dict:
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
    data = body.get("data")
    return {
        "status_class": "envelope",
        "keys": sorted(body.keys()),
        "success": body.get("success"),
        "error": mask(body.get("error")),
        "meta_keys": sorted(meta.keys()),
        "dataVersion": meta.get("dataVersion"),
        "operationId": meta.get("operationId"),
        "entity": meta.get("entity"),
        "shape": meta.get("shape"),
        "pagination": mask(meta.get("pagination")),
        "data_types": type_tree(mask(data)),
        "message": "<message>" if isinstance(body.get("message"), str) else None,
    }
