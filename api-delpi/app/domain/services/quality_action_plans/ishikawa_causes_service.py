from __future__ import annotations

import json
from typing import Any

ISHIKAWA_CATEGORY_FIELDS = (
    "machine",
    "method_process",
    "material",
    "manpower",
    "measurement",
    "environment",
)


def normalize_category_causes(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            if item is None:
                continue
            cleaned = str(item).strip()
            if cleaned:
                items.append(cleaned)
        return items
    if isinstance(value, str):
        if not value.strip():
            return []
        if "\n" in value:
            return [
                line.strip().lstrip("-•").strip()
                for line in value.splitlines()
                if line.strip()
            ]
        return [value.strip()]
    raise ValueError("Causa Ishikawa inválida; informe lista de strings.")


def normalize_ishikawa_payload(fields: dict[str, Any]) -> dict[str, Any]:
    result = dict(fields)
    for key in ISHIKAWA_CATEGORY_FIELDS:
        if key in result:
            result[key] = normalize_category_causes(result.get(key))
    notes = result.get("notes")
    if notes is not None:
        result["notes"] = str(notes).strip() or None
    return result


def ishikawa_causes_json(fields: dict[str, Any]) -> dict[str, str]:
    normalized = normalize_ishikawa_payload(fields)
    return {
        key: json.dumps(normalized.get(key) or [], ensure_ascii=False)
        for key in ISHIKAWA_CATEGORY_FIELDS
    }


def serialize_ishikawa_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    if result.get("id") is not None:
        result["id"] = str(result["id"])
    if result.get("plan_id") is not None:
        result["plan_id"] = str(result["plan_id"])
    for key, value in list(result.items()):
        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
    for key in ISHIKAWA_CATEGORY_FIELDS:
        result[key] = normalize_category_causes(result.get(key))
    notes = result.get("notes")
    if notes is not None:
        result["notes"] = str(notes).strip() or None
    return result


def ishikawa_category_lines(value: Any) -> list[str]:
    return normalize_category_causes(value)
