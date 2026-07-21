"""Cálculo de próximo disparo de agenda — Delpi Reports."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "America/Sao_Paulo"
VALID_SCHEDULE_KINDS = frozenset({"daily", "weekly"})


def build_cron_expression(
    *,
    schedule_kind: str,
    hour: int,
    minute: int,
    weekday: int | None = None,
) -> str:
    """Gera cron de 5 campos (minuto hora dom mês dow).

    ``weekday`` API: 0=segunda … 6=domingo.
    ``dow`` cron: 0=domingo, 1=segunda … 6=sábado.
    """
    kind = str(schedule_kind or "").strip().lower()
    if kind not in VALID_SCHEDULE_KINDS:
        raise ValueError("scheduleKind deve ser daily ou weekly.")
    if not (0 <= int(hour) <= 23):
        raise ValueError("hour deve estar entre 0 e 23.")
    if not (0 <= int(minute) <= 59):
        raise ValueError("minute deve estar entre 0 e 59.")

    if kind == "daily":
        return f"{int(minute)} {int(hour)} * * *"

    if weekday is None:
        raise ValueError("weekday é obrigatório para agenda weekly.")
    wd = int(weekday)
    if not (0 <= wd <= 6):
        raise ValueError("weekday deve estar entre 0 (segunda) e 6 (domingo).")
    cron_dow = (wd + 1) % 7  # Mon=1 … Sat=6, Sun=0
    return f"{int(minute)} {int(hour)} * * {cron_dow}"


def parse_schedule_fields(
    *,
    schedule_kind: str,
    cron_expression: str | None,
) -> dict[str, int | None]:
    """Extrai hour/minute/weekday do cron gerado por ``build_cron_expression``."""
    kind = str(schedule_kind or "").strip().lower()
    parts = str(cron_expression or "").strip().split()
    if len(parts) < 2:
        return {"hour": None, "minute": None, "weekday": None}
    try:
        minute = int(parts[0])
        hour = int(parts[1])
    except ValueError:
        return {"hour": None, "minute": None, "weekday": None}

    weekday: int | None = None
    if kind == "weekly" and len(parts) >= 5 and parts[4] != "*":
        try:
            cron_dow = int(parts[4])
        except ValueError:
            cron_dow = -1
        if 0 <= cron_dow <= 6:
            weekday = 6 if cron_dow == 0 else cron_dow - 1
    return {"hour": hour, "minute": minute, "weekday": weekday}


def compute_next_run_at(
    *,
    schedule_kind: str,
    hour: int,
    minute: int,
    weekday: int | None = None,
    timezone_name: str = DEFAULT_TIMEZONE,
    after: datetime | None = None,
) -> datetime:
    """Próximo instante >= after+ε no fuso informado."""
    kind = str(schedule_kind or "").strip().lower()
    if kind not in VALID_SCHEDULE_KINDS:
        raise ValueError("scheduleKind deve ser daily ou weekly.")
    if not (0 <= int(hour) <= 23):
        raise ValueError("hour deve estar entre 0 e 23.")
    if not (0 <= int(minute) <= 59):
        raise ValueError("minute deve estar entre 0 e 59.")

    tz = ZoneInfo(timezone_name or DEFAULT_TIMEZONE)
    now = after or datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)

    candidate = now.replace(
        hour=int(hour),
        minute=int(minute),
        second=0,
        microsecond=0,
    )

    if kind == "daily":
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    if weekday is None:
        raise ValueError("weekday é obrigatório para agenda weekly.")
    wd = int(weekday)
    if not (0 <= wd <= 6):
        raise ValueError("weekday deve estar entre 0 (segunda) e 6 (domingo).")

    days_ahead = (wd - candidate.weekday()) % 7
    candidate = candidate + timedelta(days=days_ahead)
    if candidate <= now:
        candidate += timedelta(days=7)
    return candidate


def compute_next_run_from_cron(
    *,
    schedule_kind: str,
    cron_expression: str | None,
    timezone_name: str = DEFAULT_TIMEZONE,
    after: datetime | None = None,
) -> datetime:
    fields = parse_schedule_fields(
        schedule_kind=schedule_kind,
        cron_expression=cron_expression,
    )
    hour = fields.get("hour")
    minute = fields.get("minute")
    if hour is None or minute is None:
        raise ValueError("cron_expression inválida para calcular next_run_at.")
    return compute_next_run_at(
        schedule_kind=schedule_kind,
        hour=int(hour),
        minute=int(minute),
        weekday=fields.get("weekday"),
        timezone_name=timezone_name,
        after=after,
    )
