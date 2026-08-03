"""Cálculo de próximo disparo de agenda — Delpi Reports."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "America/Sao_Paulo"
VALID_SCHEDULE_KINDS = frozenset({"daily", "weekly", "weekdays", "monthly"})
DEFAULT_DAY_OF_MONTH = 1


def build_cron_expression(
    *,
    schedule_kind: str,
    hour: int,
    minute: int,
    weekday: int | None = None,
    day_of_month: int | None = None,
) -> str:
    """Gera cron de 5 campos (minuto hora dom mês dow).

    ``weekday`` API: 0=segunda … 6=domingo.
    ``dow`` cron: 0=domingo, 1=segunda … 6=sábado.
    ``weekdays``: cron ``1-5`` (segunda a sexta).
    ``monthly``: dia do mês (default 1) → ``m h DOM * *``.
    """
    kind = str(schedule_kind or "").strip().lower()
    if kind not in VALID_SCHEDULE_KINDS:
        raise ValueError(
            "scheduleKind deve ser daily, weekly, weekdays ou monthly."
        )
    if not (0 <= int(hour) <= 23):
        raise ValueError("hour deve estar entre 0 e 23.")
    if not (0 <= int(minute) <= 59):
        raise ValueError("minute deve estar entre 0 e 59.")

    if kind == "daily":
        return f"{int(minute)} {int(hour)} * * *"

    if kind == "weekdays":
        return f"{int(minute)} {int(hour)} * * 1-5"

    if kind == "monthly":
        dom = int(day_of_month) if day_of_month is not None else DEFAULT_DAY_OF_MONTH
        if not (1 <= dom <= 28):
            raise ValueError("dayOfMonth deve estar entre 1 e 28.")
        return f"{int(minute)} {int(hour)} {dom} * *"

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
    """Extrai hour/minute/weekday/day_of_month do cron gerado por ``build_cron_expression``."""
    kind = str(schedule_kind or "").strip().lower()
    parts = str(cron_expression or "").strip().split()
    if len(parts) < 2:
        return {
            "hour": None,
            "minute": None,
            "weekday": None,
            "day_of_month": None,
        }
    try:
        minute = int(parts[0])
        hour = int(parts[1])
    except ValueError:
        return {
            "hour": None,
            "minute": None,
            "weekday": None,
            "day_of_month": None,
        }

    weekday: int | None = None
    day_of_month: int | None = None
    if kind == "weekly" and len(parts) >= 5 and parts[4] != "*":
        try:
            cron_dow = int(parts[4])
        except ValueError:
            cron_dow = -1
        if 0 <= cron_dow <= 6:
            weekday = 6 if cron_dow == 0 else cron_dow - 1
    if kind == "monthly" and len(parts) >= 3 and parts[2] != "*":
        try:
            day_of_month = int(parts[2])
        except ValueError:
            day_of_month = None
    return {
        "hour": hour,
        "minute": minute,
        "weekday": weekday,
        "day_of_month": day_of_month,
    }


def _advance_to_weekday(candidate: datetime) -> datetime:
    """Avança até segunda–sexta (Python weekday: 0=seg … 6=dom)."""
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def _add_months(base: datetime, months: int) -> datetime:
    year = base.year
    month = base.month + months
    while month > 12:
        month -= 12
        year += 1
    while month < 1:
        month += 12
        year -= 1
    day = min(base.day, _days_in_month(year, month))
    return base.replace(year=year, month=month, day=day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        nxt = datetime(year + 1, 1, 1)
    else:
        nxt = datetime(year, month + 1, 1)
    return (nxt - timedelta(days=1)).day


def compute_next_run_at(
    *,
    schedule_kind: str,
    hour: int,
    minute: int,
    weekday: int | None = None,
    day_of_month: int | None = None,
    timezone_name: str = DEFAULT_TIMEZONE,
    after: datetime | None = None,
) -> datetime:
    """Próximo instante >= after+ε no fuso informado."""
    kind = str(schedule_kind or "").strip().lower()
    if kind not in VALID_SCHEDULE_KINDS:
        raise ValueError(
            "scheduleKind deve ser daily, weekly, weekdays ou monthly."
        )
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

    if kind == "monthly":
        dom = int(day_of_month) if day_of_month is not None else DEFAULT_DAY_OF_MONTH
        if not (1 <= dom <= 28):
            raise ValueError("dayOfMonth deve estar entre 1 e 28.")
        candidate = now.replace(
            day=dom,
            hour=int(hour),
            minute=int(minute),
            second=0,
            microsecond=0,
        )
        # Se o mês atual não comporta o dia (não ocorre para 1–28) ou já passou:
        if candidate.day != dom or candidate <= now:
            candidate = _add_months(
                now.replace(day=1, hour=int(hour), minute=int(minute), second=0, microsecond=0),
                1,
            ).replace(day=dom)
            if candidate <= now:
                candidate = _add_months(candidate, 1)
        return candidate

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

    if kind == "weekdays":
        if candidate <= now:
            candidate += timedelta(days=1)
        return _advance_to_weekday(candidate)

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
        day_of_month=fields.get("day_of_month"),
        timezone_name=timezone_name,
        after=after,
    )
