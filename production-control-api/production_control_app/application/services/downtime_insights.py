"""Insights gerenciais de paradas MES — funções puras sobre fatos (Etapa 6).

Mesma disciplina do downtime_analytics: sem I/O, sem relógio próprio —
recebe os fatos já filtrados pelo repositório (mesmo WHERE da listagem)
e a referência temporal resolvida no service. Nunca inventa limites:
regras de criticidade vêm parametrizadas do config do owner; regra sem
parâmetro configurado fica inativa e reportada como configured=false.

Semântica:
- reincidência (RQ-6.1): grupos (centro de trabalho, motivo confirmado)
  com 2+ ocorrências reais distintas — identidade = id do downtime_event;
- comparação (RQ-6.2): janela anterior equivalente = mesma duração
  imediatamente anterior ao from — critério explícito no contrato;
- criticidade (RQ-6.3): apenas regras parametrizadas pelo config do
  processo industrial — nunca valores inventados no código do consumidor;
- eficácia de ações (RQ-6.4): antes/depois de ocorrências do mesmo
  (CT, motivo) em janela simétrica ao redor da conclusão do tratamento —
  evidência observacional, nunca inferência de causalidade;
- telemetria (RQ-6.8): CTs com fatos mas sem observação Pulse íntegra no
  período aparecem em quality.telemetryGaps — lacuna descrita, fatos
  nunca suprimidos nem inventados.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

from production_control_app.application.services.downtime_analytics import (
    PENDING_GROUP_KEY,
    UNRECORDED_GROUP_KEY,
)
from production_control_app.application.services.public_mes_work_center_today_service import (
    FACTORY_TIMEZONE,
    _parse,
)


def _clipped_seconds(row, window_from: datetime, window_to: datetime) -> float:
    started = _parse(row.get("started_at") or row.get("startedAt"))
    if started is None:
        return 0.0
    ended = _parse(row.get("ended_at") or row.get("endedAt")) or window_to
    eff_start = max(started, window_from)
    eff_end = min(ended, window_to)
    return max(0.0, (eff_end - eff_start).total_seconds())


def _reason_key(row: dict[str, Any]) -> tuple[str | None, str]:
    """Identidade da causa: motivo confirmado quando existe; pendências e
    registros históricos sem motivo viram grupos nomeados, nunca motivos
    inventados."""
    reason = row.get("reason_code") or row.get("reasonCode")
    if row.get("confirmed") and reason:
        return reason, row.get("reason_label") or row.get("reasonLabel") or reason
    if reason:
        return PENDING_GROUP_KEY, "Pendente de classificação"
    return UNRECORDED_GROUP_KEY, "Motivo não informado"


def recurrence_groups(
    facts: Iterable[dict[str, Any]],
    *,
    window_from: datetime,
    window_to: datetime,
    min_occurrences: int = 2,
) -> list[dict[str, Any]]:
    """Reincidência por (CT, motivo) — só ocorrências reais, ids distintos."""
    groups: dict[tuple[str, str | None], dict[str, Any]] = {}
    seen: dict[tuple[str, str | None], set[str]] = {}
    for row in facts:
        work_center = row.get("work_center") or row.get("workCenter") or "?"
        reason_code, reason_label = _reason_key(row)
        key = (work_center, reason_code)
        group = groups.setdefault(
            key,
            {
                "workCenter": work_center,
                "reasonCode": reason_code,
                "reasonLabel": reason_label,
                "occurrencesCount": 0,
                "seconds": 0,
                "lastOccurrenceAt": None,
                "downtimeIds": [],
                "_last": None,
            },
        )
        dedup = seen.setdefault(key, set())
        occurrence_id = str(row.get("id") or "")
        if occurrence_id and occurrence_id in dedup:
            continue
        dedup.add(occurrence_id)
        group["occurrencesCount"] += 1
        group["seconds"] += _clipped_seconds(row, window_from, window_to)
        if occurrence_id:
            group["downtimeIds"].append(occurrence_id)
        started = _parse(row.get("started_at") or row.get("startedAt"))
        last = group["_last"]
        if started is not None and (last is None or started > last):
            group["_last"] = started
    for group in groups.values():
        last = group.pop("_last", None)
        group["lastOccurrenceAt"] = last.isoformat() if last else None
    items = [g for g in groups.values() if g["occurrencesCount"] >= min_occurrences]
    items.sort(
        key=lambda g: (-g["seconds"], -g["occurrencesCount"], g["workCenter"])
    )
    return items


def comparison_deltas(
    current: dict[str, Any], previous: dict[str, Any]
) -> dict[str, Any]:
    """Deltas explícitos entre janelas equivalentes (reproduzível)."""
    def delta(key: str) -> dict[str, Any]:
        cur = current.get(key) or 0
        prev = previous.get(key) or 0
        return {
            "current": cur,
            "previous": prev,
            "absolute": cur - prev,
            "percent": (
                round((cur - prev) / prev * 100, 1) if prev else None
            ),
        }

    return {
        "totalStoppedSeconds": delta("totalStoppedSeconds"),
        "occurrencesCount": delta("occurrencesCount"),
        "averageOccurrenceSeconds": delta("averageOccurrenceSeconds"),
        "pendingCount": delta("pendingCount"),
    }


def critical_items(
    facts: Iterable[dict[str, Any]],
    *,
    reference_at: datetime,
    critical_open_seconds: int | None,
    critical_recurrence_occurrences: int | None,
    window_from: datetime,
    window_to: datetime,
) -> dict[str, Any]:
    """Ocorrências críticas por regras parametrizadas (RQ-6.3).

    Regra sem parâmetro configurado fica inativa — configured=false é
    reportado explicitamente, sem limite inventado.
    """
    rules = {
        "openStopLongDuration": {
            "configured": critical_open_seconds is not None,
            "parameters": (
                {"elapsedSeconds": critical_open_seconds}
                if critical_open_seconds is not None
                else None
            ),
        },
        "recurrenceBurst": {
            "configured": critical_recurrence_occurrences is not None,
            "parameters": (
                {"minOccurrences": critical_recurrence_occurrences}
                if critical_recurrence_occurrences is not None
                else None
            ),
        },
    }
    items: list[dict[str, Any]] = []
    if critical_open_seconds is not None:
        for row in facts:
            started = _parse(row.get("started_at") or row.get("startedAt"))
            ended = _parse(row.get("ended_at") or row.get("endedAt"))
            if started is None or ended is not None:
                continue
            elapsed = (reference_at - started).total_seconds()
            if elapsed >= critical_open_seconds:
                items.append(
                    {
                        "rule": "openStopLongDuration",
                        "downtimeId": row.get("id"),
                        "workCenter": row.get("work_center") or row.get("workCenter"),
                        "reasonCode": row.get("reason_code") or row.get("reasonCode"),
                        "reasonLabel": row.get("reason_label") or row.get("reasonLabel"),
                        "startedAt": started.isoformat(),
                        "elapsedSeconds": int(elapsed),
                    }
                )
    if critical_recurrence_occurrences is not None:
        for group in recurrence_groups(
            facts,
            window_from=window_from,
            window_to=window_to,
            min_occurrences=critical_recurrence_occurrences,
        ):
            items.append(
                {
                    "rule": "recurrenceBurst",
                    "downtimeId": None,
                    "workCenter": group["workCenter"],
                    "reasonCode": group["reasonCode"],
                    "reasonLabel": group["reasonLabel"],
                    "occurrencesCount": group["occurrencesCount"],
                    "seconds": int(group["seconds"]),
                    "downtimeIds": group["downtimeIds"],
                }
            )
    return {"rules": rules, "items": items}


def effectiveness_records(
    concluded_treatments: Iterable[dict[str, Any]],
    *,
    count_occurrences: Callable[..., dict[str, int]],
    window_days: int,
    reference_at: datetime,
) -> list[dict[str, Any]]:
    """Evidência antes/depois por tratamento concluído (RQ-6.4).

    count_occurrences(work_center, reason_code, period_from, period_to)
    é injetado pelo service — o módulo não faz I/O. Resultado é
    observacional; causalidade nunca é inferida.
    """
    records: list[dict[str, Any]] = []
    for treatment in concluded_treatments:
        concluded_at = _parse(treatment.get("concluded_at"))
        reason_code = treatment.get("reason_code")
        work_center = treatment.get("work_center")
        if concluded_at is None or not reason_code or not work_center:
            continue
        before_from = concluded_at - timedelta(days=window_days)
        after_to = min(concluded_at + timedelta(days=window_days), reference_at)
        if after_to <= concluded_at:
            continue  # conclusão recente demais para evidência pós
        before = count_occurrences(
            work_center=work_center,
            reason_code=reason_code,
            period_from=before_from,
            period_to=concluded_at,
        )
        after = count_occurrences(
            work_center=work_center,
            reason_code=reason_code,
            period_from=concluded_at,
            period_to=after_to,
        )
        records.append(
            {
                "downtimeId": str(treatment.get("downtime_id")),
                "workCenter": work_center,
                "reasonCode": reason_code,
                "reasonLabel": treatment.get("reason_label"),
                "concludedAt": concluded_at.isoformat(),
                "requestId": (
                    str(treatment["request_id"])
                    if treatment.get("request_id")
                    else None
                ),
                "windowDays": window_days,
                "before": before,
                "after": after,
                "evidence": "pre_post_occurrence_comparison",
            }
        )
    return records


def telemetry_gaps(
    facts: Iterable[dict[str, Any]],
    *,
    observer_states: Iterable[dict[str, Any]],
    stale_minutes: int,
    reference_at: datetime,
) -> list[dict[str, Any]]:
    """CTs com fatos no período cuja observação Pulse está degradada ou
    sem sinal recente — descrito em quality, fatos nunca suprimidos."""
    observed = {
        (o.get("work_center") or ""): o for o in observer_states
    }
    centers_with_facts = {
        (row.get("work_center") or row.get("workCenter"))
        for row in facts
        if (row.get("work_center") or row.get("workCenter"))
    }
    gaps: list[dict[str, Any]] = []
    for work_center in sorted(centers_with_facts):
        observer = observed.get(work_center)
        if observer is None:
            gaps.append(
                {
                    "workCenter": work_center,
                    "state": "no_observation",
                    "detail": "Sem vínculo de monitoramento Pulse registrado.",
                }
            )
            continue
        if not observer.get("device_online"):
            gaps.append(
                {
                    "workCenter": work_center,
                    "state": "degraded",
                    "detail": observer.get("degraded_reason") or "dispositivo offline",
                }
            )
            continue
        last_seen = _parse(observer.get("last_seen_at"))
        if last_seen is None or (
            reference_at - last_seen
        ).total_seconds() > stale_minutes * 60:
            gaps.append(
                {
                    "workCenter": work_center,
                    "state": "stale",
                    "detail": "Sem sinal de telemetria recente na janela.",
                }
            )
    return gaps
