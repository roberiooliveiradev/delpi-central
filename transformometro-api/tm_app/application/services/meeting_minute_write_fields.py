"""Normalize/validate meeting-minute write fields before SQL persistence.

Shared by UI CRUD and GPT Actions — one canonical gate (no GPT-only validator).
Aligns with V042 CHECKs: unit_code, meeting_type, DATE/TIME/UUID columns.
"""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from tm_app.core.catalogs import (
    MEETING_MINUTE_TYPES,
    MEETING_MINUTE_UNIT_CODES,
    assert_in,
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


def normalize_unit_code(value: Any) -> str:
    code = str(value or "").strip().zfill(2)
    if code not in MEETING_MINUTE_UNIT_CODES:
        raise ValueError(
            f"unit_code inválido: {value!r}. Use um código de filial válido "
            f"({', '.join(MEETING_MINUTE_UNIT_CODES)})."
        )
    return code


def normalize_optional_uuid(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return str(UUID(text))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(
            f"{field} inválido: informe um UUID ou omita/null (não envie string vazia)."
        ) from exc


def normalize_required_actor_uuid(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(
            "Usuário autenticado sem identificador (created_by_user_id). "
            "Não é possível gravar a ata."
        )
    try:
        return str(UUID(text))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("Identificador do usuário autenticado inválido.") from exc


def normalize_meeting_date(value: Any) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError("Informe a data da reunião (meeting_date) no formato YYYY-MM-DD.")
    text = str(value).strip()
    if "T" in text:
        text = text.split("T", 1)[0]
    if not _DATE_RE.match(text):
        raise ValueError(
            f"meeting_date inválido: {value!r}. Use o formato YYYY-MM-DD "
            "(exemplo: 2026-09-16). Não use DD/MM/AAAA."
        )
    year, month, day = (int(part) for part in text.split("-"))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        raise ValueError(f"meeting_date inválido: {value!r}.")
    return text


def normalize_optional_time(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if not _TIME_RE.match(text):
        raise ValueError(
            f"{field} inválido: {value!r}. Use HH:MM ou HH:MM:SS "
            "(exemplo: 14:30). Não use formatos como 14h30."
        )
    parts = [int(p) for p in text.split(":")]
    hour, minute = parts[0], parts[1]
    second = parts[2] if len(parts) > 2 else 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise ValueError(f"{field} inválido: {value!r}.")
    if len(parts) == 2:
        return f"{hour:02d}:{minute:02d}"
    return f"{hour:02d}:{minute:02d}:{second:02d}"


def normalize_meeting_type(value: Any) -> str:
    raw = str(value or "").strip().lower() or "ordinary"
    assert_in(raw, MEETING_MINUTE_TYPES, "meeting_type")
    return raw


def normalize_minute_create_fields(payload: dict[str, Any], *, actor_user_id: str) -> dict[str, Any]:
    """Return canonical header fields for create_minute (raises ValueError on bad input)."""
    title = str(payload.get("title") or "").strip()
    if not title:
        raise ValueError("Informe o título da ata.")
    return {
        "unit_code": normalize_unit_code(payload.get("unit_code")),
        "title": title,
        "meeting_type": normalize_meeting_type(payload.get("meeting_type")),
        "meeting_date": normalize_meeting_date(payload.get("meeting_date")),
        "start_time": normalize_optional_time(payload.get("start_time"), field="start_time"),
        "end_time": normalize_optional_time(payload.get("end_time"), field="end_time"),
        "location": _optional_text(payload.get("location")),
        "responsible_user_id": normalize_optional_uuid(
            payload.get("responsible_user_id"), field="responsible_user_id"
        ),
        "responsible_name": _optional_text(payload.get("responsible_name")),
        "chair_name": _optional_text(payload.get("chair_name")),
        "secretary_name": _optional_text(payload.get("secretary_name")),
        "created_by_user_id": normalize_required_actor_uuid(actor_user_id),
    }


def normalize_minute_update_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize only keys present in payload for draft update."""
    out: dict[str, Any] = {}
    if "title" in payload:
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("Informe o título da ata.")
        out["title"] = title
    if "meeting_type" in payload:
        out["meeting_type"] = normalize_meeting_type(payload.get("meeting_type"))
    if "meeting_date" in payload:
        out["meeting_date"] = normalize_meeting_date(payload.get("meeting_date"))
    if "start_time" in payload:
        out["start_time"] = normalize_optional_time(payload.get("start_time"), field="start_time")
    if "end_time" in payload:
        out["end_time"] = normalize_optional_time(payload.get("end_time"), field="end_time")
    if "location" in payload:
        out["location"] = _optional_text(payload.get("location"))
    if "responsible_user_id" in payload:
        out["responsible_user_id"] = normalize_optional_uuid(
            payload.get("responsible_user_id"), field="responsible_user_id"
        )
    if "responsible_name" in payload:
        out["responsible_name"] = _optional_text(payload.get("responsible_name"))
    if "chair_name" in payload:
        out["chair_name"] = _optional_text(payload.get("chair_name"))
    if "secretary_name" in payload:
        out["secretary_name"] = _optional_text(payload.get("secretary_name"))
    return out


def uuid_bind_or_none(value: Any) -> str | None:
    """Repository defense: blank string must not reach ``%s::uuid``."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
