"""Data de referência do negócio (vencimento de prazos) no fuso da DELPI."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

BUSINESS_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def business_today() -> date:
    return datetime.now(BUSINESS_TIMEZONE).date()
