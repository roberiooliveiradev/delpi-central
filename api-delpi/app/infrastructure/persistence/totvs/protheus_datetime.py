from __future__ import annotations

from datetime import datetime


def parse_protheus_period_start(value: str) -> tuple[str, str]:
    return _parse_protheus_period_bound(value, default_time="00:00")


def parse_protheus_period_end(value: str) -> tuple[str, str]:
    return _parse_protheus_period_bound(value, default_time="23:59")


def _parse_protheus_period_bound(value: str, *, default_time: str) -> tuple[str, str]:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("Data do período é obrigatória.")

    date_part = raw
    time_part = default_time

    if "T" in raw:
        date_part, time_part = raw.split("T", 1)
        time_part = time_part.replace("Z", "")
        if "+" in time_part:
            time_part = time_part.split("+", 1)[0]
        elif time_part.count("-") > 1:
            # ISO com offset negativo: 2026-06-12T10:51:00-03:00
            time_part = time_part.rsplit("-", 1)[0]

    date_part = date_part[:10]
    parsed_date = datetime.strptime(date_part, "%Y-%m-%d")
    protheus_date = parsed_date.strftime("%Y%m%d")

    if len(time_part) >= 5:
        hour_minute = time_part[:5]
        datetime.strptime(hour_minute, "%H:%M")
    else:
        hour_minute = default_time

    return protheus_date, hour_minute
