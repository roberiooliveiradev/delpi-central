"""Agregações gerenciais de paradas MES — função pura sobre fatos lidos.

Sem I/O e sem semântica pública do cockpit: recebe as ocorrências já
filtradas pelo repositório (mesmo WHERE da listagem) e produz indicadores,
agrupamentos e sinais de qualidade. Reutiliza os helpers canônicos de
recorte/união temporal do today service — mesma fonte usada pelo
PublicMesWorkCenterPeriodService (sem duplicar a regra de intervalos).

Semântica temporal (RQ-E2 / contrato de analytics):
- cada ocorrência contribui pela interseção [max(início, from), min(fim,
  to efetivo)]; aberta usa o `to` efetivo (referenceAt resolvido no
  service) como fim;
- `totalStoppedSeconds` é a união deduplicada dos intervalos por filial+CT
  somada entre CTs — o mesmo segundo físico nunca conta duas vezes no
  mesmo equipamento;
- `attributedSeconds` é a soma bruta por ocorrência (pode superar o total
  deduplicado quando fatos históricos se sobrepõem — divergência exposta
  em `quality`, nunca escondida);
- `byDay`/`byWeekdayHour` distribuem cada intervalo pelos dias civis e
  horas de `FACTORY_TIMEZONE` (America/Sao_Paulo), com união por CT antes
  da soma — parada atravessando a meia-noite contribui em cada dia;
- contagem de ocorrências por dia/célula conta IDs distintos que
  intersectam o intervalo — a mesma parada pode contar em dois dias;
- motivo de ocorrência não confirmada nunca vira causa definitiva: grupa
  em "Pendente de classificação"; confirmada sem código legado cai em
  "Motivo não informado".
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from production_control_app.application.services.public_mes_work_center_today_service import (
    FACTORY_TIMEZONE,
    _clip_seconds,
    _merged_seconds,
    _parse,
)

PENDING_GROUP_KEY = "pending"
UNRECORDED_GROUP_KEY = "unrecorded"

_WEEKDAY_LABELS = ("seg", "ter", "qua", "qui", "sex", "sab", "dom")


def _clipped_span(row: dict[str, Any], window_from: datetime, window_to: datetime):
    started = _parse(row.get("started_at") or row.get("startedAt"))
    ended = _parse(row.get("ended_at") or row.get("endedAt"))
    if started is None:
        return None
    eff_start = max(started, window_from)
    eff_end = min(ended or window_to, window_to)
    if eff_end <= eff_start:
        return None
    return eff_start, eff_end


def _zone(dt: datetime, tz: ZoneInfo) -> datetime:
    # astimezone() é no-op quando o tzinfo já é o destino, o que preserva
    # wall-times inexistentes (ex.: 00:00 no dia de início do horário de
    # verão). O round-trip por UTC sempre produz a hora civil real.
    return dt.astimezone(timezone.utc).astimezone(tz)


def _day_range(date_key, tz: ZoneInfo):
    start = datetime(date_key.year, date_key.month, date_key.day, tzinfo=tz)
    return start, start + timedelta(days=1)


def aggregate_downtime_analytics(
    facts: Iterable[dict[str, Any]],
    *,
    window_from: datetime,
    window_to: datetime,
    timezone_name: str = FACTORY_TIMEZONE,
    facts_capped: bool = False,
) -> dict[str, Any]:
    tz = ZoneInfo(timezone_name)
    day_from = window_from.astimezone(tz).date()
    day_to = window_to.astimezone(tz).date()

    # spans já recortados na janela, por ocorrência e por CT
    per_ct_spans: dict[str, list[tuple[datetime, datetime]]] = {}
    attributed_seconds = 0
    occurrence_ids: set[str] = set()
    pending_ids: set[str] = set()
    open_ids: set[str] = set()

    reason_groups: dict[str, dict[str, Any]] = {}
    ct_counts: dict[str, set[str]] = {}
    ct_attributed: dict[str, int] = {}

    day_spans: dict[Any, dict[str, list]] = {}
    day_ids: dict[Any, set[str]] = {}
    hour_cell_spans: dict[tuple[int, int], dict[str, list]] = {}
    hour_cell_ids: dict[tuple[int, int], set[str]] = {}

    for row in facts:
        span = _clipped_span(row, window_from, window_to)
        if span is None:
            continue
        event_id = str(row.get("id"))
        work_center = str(row.get("work_center") or "").strip() or "—"
        confirmed = bool(row.get("confirmed"))
        ended_raw = row.get("ended_at") or row.get("endedAt")

        occurrence_ids.add(event_id)
        seconds = int((span[1] - span[0]).total_seconds())
        attributed_seconds += seconds
        per_ct_spans.setdefault(work_center, []).append(span)
        ct_counts.setdefault(work_center, set()).add(event_id)
        ct_attributed[work_center] = ct_attributed.get(work_center, 0) + seconds
        if not confirmed:
            pending_ids.add(event_id)
        if ended_raw is None:
            open_ids.add(event_id)

        # Motivo: pendente nunca vira causa definitiva (regra E2)
        if not confirmed:
            reason_key = PENDING_GROUP_KEY
            reason_label = "Pendente de classificação"
        elif row.get("reason_code") or row.get("reasonCode"):
            reason_key = str(row.get("reason_code") or row.get("reasonCode"))
            reason_label = (
                row.get("reason_label") or row.get("reasonLabel") or reason_key
            )
        else:
            reason_key = UNRECORDED_GROUP_KEY
            reason_label = "Motivo não informado"
        group = reason_groups.setdefault(
            reason_key,
            {
                "key": reason_key,
                "reasonCode": None
                if reason_key in (PENDING_GROUP_KEY, UNRECORDED_GROUP_KEY)
                else reason_key,
                "label": reason_label,
                "seconds": 0,
                "occurrencesCount": 0,
                "pendingCount": 0,
                "_ids": set(),
            },
        )
        group["seconds"] += seconds
        if event_id not in group["_ids"]:
            group["_ids"].add(event_id)
            group["occurrencesCount"] += 1
        if not confirmed:
            group["pendingCount"] += 1

        # Distribuição por dia civil (SP) e por célula dia-da-semana×hora.
        # O span já está recortado na janela; dias com interseção vazia
        # (parada terminando exatamente à meia-noite) não contam.
        day = span[0].astimezone(tz).date()
        last_day = span[1].astimezone(tz).date()
        while day <= last_day:
            day_start, day_end = _day_range(day, tz)
            slice_from = max(span[0], day_start)
            slice_to = min(span[1], day_end)
            if slice_to > slice_from:
                # Spans sempre em UTC: subtração de datetimes aware com o
                # MESMO tzinfo ignora o fuso (arithmética de wall-clock) e
                # inflaria horas em dias com transição de horário de verão.
                day_spans.setdefault(day, {}).setdefault(work_center, []).append(
                    (
                        slice_from.astimezone(timezone.utc),
                        slice_to.astimezone(timezone.utc),
                    )
                )
                day_ids.setdefault(day, set()).add(event_id)
                # fatia por hora dentro do dia — hora civil SP (o cursor do
                # recorte pode chegar em outro tzinfo, ex.: UTC, ou com
                # wall-time inexistente em transição de horário de verão)
                slice_from_tz = _zone(slice_from, tz)
                slice_to_tz = _zone(slice_to, tz)
                hour_cursor = slice_from_tz
                while hour_cursor < slice_to_tz:
                    hour_end = _zone(
                        hour_cursor.replace(minute=0, second=0, microsecond=0)
                        + timedelta(hours=1),
                        tz,
                    )
                    cell_to = min(slice_to_tz, hour_end)
                    cell = (hour_cursor.weekday(), hour_cursor.hour)
                    hour_cell_spans.setdefault(cell, {}).setdefault(
                        work_center, []
                    ).append(
                        (
                            hour_cursor.astimezone(timezone.utc),
                            cell_to.astimezone(timezone.utc),
                        )
                    )
                    hour_cell_ids.setdefault(cell, set()).add(event_id)
                    hour_cursor = cell_to
            day += timedelta(days=1)

    # Totais deduplicados por CT
    total_seconds = sum(
        _merged_seconds(spans) for spans in per_ct_spans.values()
    )
    overlap_seconds = attributed_seconds - total_seconds
    occurrences = len(occurrence_ids)

    by_reason = sorted(
        (
            {k: v for k, v in group.items() if k != "_ids"}
            for group in reason_groups.values()
        ),
        key=lambda g: (-g["seconds"], g["key"]),
    )
    cumulative = 0.0
    for group in by_reason:
        share = (group["seconds"] / attributed_seconds) if attributed_seconds else 0.0
        group["percentOfAttributed"] = round(share * 100, 2)
        cumulative += share * 100
        group["cumulativePercent"] = round(min(cumulative, 100.0), 2)

    by_work_center = sorted(
        (
            {
                "workCenter": center,
                "seconds": _merged_seconds(spans),
                "occurrencesCount": len(ct_counts[center]),
                "averageSeconds": (
                    round(ct_attributed[center] / len(ct_counts[center]))
                    if ct_counts[center]
                    else 0
                ),
                "percentOfTotal": (
                    round(
                        _merged_seconds(spans) / total_seconds * 100, 2
                    )
                    if total_seconds
                    else 0.0
                ),
            }
            for center, spans in per_ct_spans.items()
        ),
        key=lambda e: (-e["seconds"], e["workCenter"]),
    )

    days = []
    day = day_from
    while day <= day_to:
        per_ct = day_spans.get(day, {})
        days.append(
            {
                "date": day.isoformat(),
                "weekday": day.weekday(),
                "seconds": sum(
                    _merged_seconds(spans) for spans in per_ct.values()
                ),
                "occurrencesCount": len(day_ids.get(day, set())),
            }
        )
        day += timedelta(days=1)

    cells = []
    for (weekday, hour), per_ct in sorted(hour_cell_spans.items()):
        cells.append(
            {
                "weekday": weekday,
                "weekdayLabel": _WEEKDAY_LABELS[weekday],
                "hour": hour,
                "seconds": sum(
                    _merged_seconds(spans) for spans in per_ct.values()
                ),
                "occurrencesCount": len(hour_cell_ids.get((weekday, hour), set())),
            }
        )

    return {
        "summary": {
            "totalStoppedSeconds": total_seconds,
            "attributedSeconds": attributed_seconds,
            "occurrencesCount": occurrences,
            "averageOccurrenceSeconds": (
                round(attributed_seconds / occurrences) if occurrences else 0
            ),
            "pendingCount": len(pending_ids),
            "openCount": len(open_ids),
        },
        "byReason": by_reason,
        "byWorkCenter": by_work_center,
        "byDay": days,
        "byWeekdayHour": cells,
        "quality": {
            "overlapDetected": overlap_seconds > 0,
            "overlapSeconds": overlap_seconds,
            "partial": facts_capped,
            "factsCapped": facts_capped,
        },
    }
