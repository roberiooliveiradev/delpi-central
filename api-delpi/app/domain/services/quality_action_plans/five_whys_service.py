from __future__ import annotations

import json
from typing import Any

FIVE_WHYS_TRACK_FIELDS = ("occurrence_whys", "detection_whys")

LEGACY_OCCURRENCE_FIELDS = tuple(f"why_{index}" for index in range(1, 6))
LEGACY_DETECTION_FIELDS = tuple(f"detection_why_{index}" for index in range(1, 6))


def normalize_whys_list(value: Any) -> list[str]:
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
    raise ValueError("Porquê inválido; informe lista de strings.")


def _legacy_track_values(fields: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    items: list[str] = []
    for key in keys:
        raw = fields.get(key)
        if raw is None:
            continue
        cleaned = str(raw).strip()
        if cleaned:
            items.append(cleaned)
    return items


def normalize_five_whys_payload(fields: dict[str, Any]) -> dict[str, Any]:
    result = dict(fields)

    occurrence = result.get("occurrence_whys")
    if occurrence is None:
        occurrence = _legacy_track_values(result, LEGACY_OCCURRENCE_FIELDS)
    result["occurrence_whys"] = normalize_whys_list(occurrence)

    detection = result.get("detection_whys")
    if detection is None:
        detection = _legacy_track_values(result, LEGACY_DETECTION_FIELDS)
    result["detection_whys"] = normalize_whys_list(detection)

    root_cause = result.get("root_cause")
    if root_cause is not None:
        result["root_cause"] = str(root_cause).strip() or None

    for key in (*LEGACY_OCCURRENCE_FIELDS, *LEGACY_DETECTION_FIELDS):
        result.pop(key, None)

    return result


def five_whys_json(fields: dict[str, Any]) -> dict[str, str]:
    normalized = normalize_five_whys_payload(fields)
    return {
        "occurrence_whys": json.dumps(normalized.get("occurrence_whys") or [], ensure_ascii=False),
        "detection_whys": json.dumps(normalized.get("detection_whys") or [], ensure_ascii=False),
    }


def serialize_five_whys_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
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
    result["occurrence_whys"] = normalize_whys_list(result.get("occurrence_whys"))
    result["detection_whys"] = normalize_whys_list(result.get("detection_whys"))
    root_cause = result.get("root_cause")
    if root_cause is not None:
        result["root_cause"] = str(root_cause).strip() or None
    for key in (*LEGACY_OCCURRENCE_FIELDS, *LEGACY_DETECTION_FIELDS):
        result.pop(key, None)
    return result


def five_whys_track_lines(value: Any, *, track_label: str) -> list[str]:
    items = normalize_whys_list(value)
    return [f"{track_label} — Por quê {index}: {item}" for index, item in enumerate(items, start=1)]
