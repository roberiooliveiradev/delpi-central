from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from typing import Any, Optional


def parse_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    raw = str(value).strip().lower()
    return raw in {"1", "true", "sim", "yes", "y", "ativo"}


def parse_number(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip().replace(".", "").replace(",", ".")
    raw = re.sub(r"[^\d.\-]", "", raw)
    if not raw or raw in {"-", "."}:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def parse_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None or value == "":
        return default
    try:
        return int(parse_number(value, 0))
    except (TypeError, ValueError):
        return default


def parse_date(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    raw = str(value).strip()
    if not raw:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw[:10], fmt).date().isoformat()
        except ValueError:
            continue

    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]
    return None


def parse_uuid(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    raw = str(value).strip()
    try:
        return str(uuid.UUID(raw))
    except ValueError:
        return None


def ensure_uuid(value: Any) -> str:
    return parse_uuid(value) or str(uuid.uuid4())


def normalize_filial(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return raw
    if raw.isdigit():
        return raw.zfill(2)
    return raw
