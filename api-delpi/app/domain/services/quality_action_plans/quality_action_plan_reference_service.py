from __future__ import annotations

import re
import uuid

_PLAN_CODE_PATTERN = re.compile(r"^PAC-\d{4}-\d{4}$", re.IGNORECASE)


def is_plan_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def is_plan_code(value: str) -> bool:
    return bool(_PLAN_CODE_PATTERN.match((value or "").strip()))


def classify_plan_reference(value: str) -> str:
    """Retorna uuid | code | invalid."""
    trimmed = (value or "").strip()
    if not trimmed:
        return "invalid"
    if is_plan_uuid(trimmed):
        return "uuid"
    if is_plan_code(trimmed):
        return "code"
    return "invalid"


def normalize_plan_code(value: str) -> str:
    return (value or "").strip().upper()
