"""Serialização segura de mudanças de auditoria (histórico LNF)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def history_changes_json_safe(value: Any) -> Any:
    """Converte date/datetime/Decimal/UUID para tipos JSON-nativos."""
    if isinstance(value, dict):
        return {str(k): history_changes_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [history_changes_json_safe(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    return value
