"""Data fiscal no calendário de America/Sao_Paulo.

Data sem horário permanece nesse dia. Horário sem fuso é local de São Paulo.
Horário com fuso, inclusive UTC, converte para São Paulo antes de extrair o dia.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

FISCAL_ZONE = ZoneInfo("America/Sao_Paulo")
_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BR_DATE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def fiscal_calendar_date(value: str | None) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    if _DATE_ONLY.fullmatch(text):
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None
    brazilian = _BR_DATE.fullmatch(text)
    if brazilian:
        day, month, year = (int(part) for part in brazilian.groups())
        try:
            return date(year, month, day)
        except ValueError:
            return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=FISCAL_ZONE)
    return parsed.astimezone(FISCAL_ZONE).date()
