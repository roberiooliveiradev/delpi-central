from __future__ import annotations

from datetime import datetime
from typing import Any

from app.domain.services.lmp_process_stage_labels import (
    label_for_process,
    label_for_stage,
)

AIJ_STATUS_LABELS: dict[str, str] = {
    "1": "Em andamento",
    "2": "Encerrado",
    "3": "Cancelado",
    "4": "Suspenso",
    "5": "Aguardando",
    "6": "Reprovado",
    "7": "Aprovado",
    "8": "Finalizado",
    "9": "Concluído",
}

CLOSED_STATUS_CODES = frozenset({"2", "3", "6", "8", "9"})
ENGINEERING_FLOW_STAGE_CODES = frozenset({"000003", "000008", "000012"})


def label_for_history_status(status_code: str | None) -> str | None:
    normalized = str(status_code or "").strip()
    if not normalized:
        return None
    return AIJ_STATUS_LABELS.get(normalized, f"Status {normalized}")


def resolve_process_label(event: dict[str, Any]) -> str | None:
    description = str(event.get("process_description") or "").strip()
    if description:
        return description
    return label_for_process(event.get("process_code"))


def resolve_stage_label(event: dict[str, Any]) -> str | None:
    description = str(event.get("stage_description") or "").strip()
    if description:
        return description
    return label_for_stage(event.get("stage_code"))


def resolve_history_status_label(
    event: dict[str, Any],
    *,
    is_open: bool,
) -> str | None:
    status_code = str(event.get("status") or "").strip()

    if not is_open:
        if status_code in CLOSED_STATUS_CODES:
            return label_for_history_status(status_code)
        return "Encerrado"

    return label_for_history_status(status_code) or "Em andamento"


def _parse_totvs_datetime(
    date_str: str | None,
    time_str: str | None,
) -> datetime | None:
    normalized_date = str(date_str or "").strip()
    if len(normalized_date) != 8 or not normalized_date.isdigit():
        return None

    normalized_time = str(time_str or "").strip() or "00:00"
    if len(normalized_time) == 4 and normalized_time.isdigit():
        normalized_time = f"{normalized_time[:2]}:{normalized_time[2:]}"

    try:
        return datetime.strptime(
            f"{normalized_date}{normalized_time}",
            "%Y%m%d%H:%M",
        )
    except ValueError:
        return None


def is_event_open(event: dict[str, Any]) -> bool:
    return not str(event.get("end_date") or "").strip()


def is_event_late(
    event: dict[str, Any],
    *,
    now: datetime | None = None,
) -> bool:
    reference = now or datetime.now()
    limit_dt = _parse_totvs_datetime(event.get("limit_date"), event.get("limit_time"))
    if limit_dt is None:
        return False

    if is_event_open(event):
        return reference > limit_dt

    end_dt = _parse_totvs_datetime(event.get("end_date"), event.get("end_time"))
    if end_dt is None:
        return reference > limit_dt

    return end_dt > limit_dt


def is_engineering_flow(event: dict[str, Any]) -> bool:
    if bool(event.get("is_engineering")):
        return True

    stage_code = str(event.get("stage_code") or "").strip()
    return stage_code in ENGINEERING_FLOW_STAGE_CODES


def format_duration_display(
    minutes: int | float | None,
    *,
    is_open: bool,
) -> str | None:
    if minutes is None:
        return None

    try:
        total_minutes = int(round(float(minutes)))
    except (TypeError, ValueError):
        return None

    if total_minutes < 0:
        return None

    if is_open:
        days = total_minutes // (24 * 60)
        hours = (total_minutes % (24 * 60)) // 60
        if days > 0:
            return f"Em andamento · {days} dia(s)"
        if hours > 0:
            return f"Em andamento · {hours} h"
        return f"Em andamento · {total_minutes} min"

    if total_minutes < 60:
        return f"{total_minutes} min"

    hours = total_minutes // 60
    if hours < 24:
        rem_minutes = total_minutes % 60
        if rem_minutes:
            return f"{hours} h · {rem_minutes} min"
        return f"{hours} h"

    days = total_minutes // (24 * 60)
    rem_hours = (total_minutes % (24 * 60)) // 60
    if rem_hours:
        return f"{days} dia(s) · {rem_hours} h"
    return f"{days} dia(s)"


def _resolve_current_event_index(events: list[dict[str, Any]]) -> int | None:
    if not events:
        return None

    open_indices = [index for index, event in enumerate(events) if is_event_open(event)]
    if open_indices:
        return open_indices[-1]

    return len(events) - 1


def enrich_history_event(
    event: dict[str, Any],
    *,
    is_current: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    is_open = is_event_open(event)
    enriched = {
        key: value
        for key, value in event.items()
        if key not in {"process_description", "stage_description"}
    }

    return {
        **enriched,
        "process_label": resolve_process_label(event),
        "stage_label": resolve_stage_label(event),
        "status_label": resolve_history_status_label(event, is_open=is_open),
        "is_open": is_open,
        "is_late": is_event_late(event, now=now),
        "is_engineering_flow": is_engineering_flow(event),
        "duration_display": format_duration_display(
            event.get("duration_minutes"),
            is_open=is_open,
        ),
        "is_current": is_current,
    }


def enrich_history_events(
    events: list[dict[str, Any]] | None,
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    normalized = list(events or [])
    current_index = _resolve_current_event_index(normalized)

    return [
        enrich_history_event(
            event,
            is_current=index == current_index,
            now=now,
        )
        for index, event in enumerate(normalized)
    ]
