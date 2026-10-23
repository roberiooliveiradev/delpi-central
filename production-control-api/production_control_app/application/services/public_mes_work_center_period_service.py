"""Resumo MES do posto por período de dias civis no cockpit público (Etapa 4).

Agregado somente-leitura, escopado por sessão de bancada do mesmo
(filial, CT), para alimentar o painel "Desempenho do posto" em centros
sensorizados — substituindo a leitura de apontamentos TOTVS naquela
superfície, sem alterar o contrato legado nem seus demais consumidores.

Regras herdadas da Etapa 2: mesma cadeia de autorização, mesma seleção
oficial de fonte, mesmo recorte de janela, mesma união de intervalos por
estado (sobreposição nunca infla os totais). O agrupamento por motivo é
atribuição por evento — se duas paradas anômalas se sobrepõem com motivos
distintos, `quality.stopOverlapSeconds` expõe a diferença em vez de
inventar uma distribuição.
"""

from __future__ import annotations

import logging
from datetime import datetime, time, timedelta
from typing import Any, Callable
from zoneinfo import ZoneInfo

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_mes_work_center_today_service import (
    FACTORY_TIMEZONE,
    _clip_seconds,
    _merged_seconds,
    _parse,
)
from production_control_app.domain.errors import (
    BenchSessionRequired,
    DowntimeSourceUnavailable,
    PublicAccessDenied,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService

logger = logging.getLogger(__name__)

MAX_PERIOD_DAYS = 31


class PublicMesWorkCenterPeriodService:
    def __init__(
        self,
        *,
        access: PublicCockpitAccessService,
        machine_load: MachineLoadService,
        branch_access: BranchAccessService,
        downtime_source: Any,
        integration_read: Any,
        run_service: Any,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._access = access
        self._machine_load = machine_load
        self._branch_access = branch_access
        self._downtime_source = downtime_source
        self._integration_read = integration_read
        self._run_service = run_service
        self._clock = clock or (lambda: datetime.now(ZoneInfo(FACTORY_TIMEZONE)))

    def get_period(
        self,
        *,
        token: str,
        branch: str,
        work_center: str,
        session_token: str | None,
        days: int,
    ) -> dict[str, Any]:
        # Mesma cadeia da Etapa 2: link público → filial/CT publicado →
        # sessão de bancada deste posto → fonte oficial.
        if not self._access.is_valid_token(token):
            raise PublicAccessDenied(
                self._access.message(
                    "invalidToken", "Link do cockpit inválido ou desativado."
                )
            )
        code = self._branch_access.assert_valid_branch(branch)
        center = str(work_center or "").strip()
        if not center:
            raise ValueError("Informe o centro de trabalho.")
        if days < 1 or days > MAX_PERIOD_DAYS:
            raise ValueError(
                f"O período deve estar entre 1 e {MAX_PERIOD_DAYS} dias."
            )
        session = self._run_service.resolve_bench_session(session_token)
        if (
            session.get("branch") != code
            or session.get("work_center") != center
        ):
            raise BenchSessionRequired(
                "Sessão não corresponde ao posto selecionado."
            )

        resolution = self._downtime_source.resolve(
            token=token, branch=code, work_center=center
        )
        if resolution["source"] == "totvs":
            return {
                "branch": code,
                "workCenter": center,
                "source": "totvs",
                "reason": resolution["reason"],
                "referenceAt": resolution["referenceAt"],
            }
        if resolution["source"] != "mes":
            raise DowntimeSourceUnavailable(
                "Fonte de paradas do posto indisponível no momento."
            )

        reference_at = self._clock()
        window_from = datetime.combine(
            reference_at.date() - timedelta(days=days - 1),
            time.min,
            tzinfo=reference_at.tzinfo,
        )
        window_to = reference_at

        timeline = self._integration_read.get_work_center_timeline(
            branch=code,
            work_center=center,
            period_from=window_from,
            period_to=window_to,
        )

        tz = ZoneInfo(FACTORY_TIMEZONE)
        day_from = window_from.date()
        day_to = window_to.date()
        civil_days = [
            day_from + timedelta(days=offset)
            for offset in range((day_to - day_from).days + 1)
        ]
        per_day: dict[Any, dict[str, Any]] = {
            day: {
                "date": day.isoformat(),
                "producingSpans": [],
                "stoppedSpans": [],
                "stopIds": set(),
                "pendingIds": set(),
            }
            for day in civil_days
        }

        total_producing_spans: list[tuple[datetime, datetime]] = []
        total_stopped_spans: list[tuple[datetime, datetime]] = []
        total_stop_ids: set[str] = set()
        total_pending_ids: set[str] = set()
        raw_stopped_seconds = 0
        reasons: dict[str, dict[str, Any]] = {}

        for row in timeline["items"]:
            started = _parse(row.get("startedAt"))
            ended = _parse(row.get("endedAt"))
            if started is None:
                continue
            clipped = (
                max(started, window_from),
                min(ended or window_to, window_to),
            )
            if clipped[1] <= clipped[0]:
                continue
            state = row.get("state")

            # Fatia por dia civil: evento atravessando a meia-noite
            # contribui com o trecho correto em cada dia.
            for day in civil_days:
                day_start = datetime.combine(day, time.min, tzinfo=tz)
                day_end = day_start + timedelta(days=1)
                slice_from = max(clipped[0], day_start)
                slice_to = min(clipped[1], day_end)
                if slice_to <= slice_from:
                    continue
                bucket = per_day[day]
                if state == "producing":
                    bucket["producingSpans"].append((slice_from, slice_to))
                elif state == "stopped":
                    bucket["stoppedSpans"].append((slice_from, slice_to))
                    bucket["stopIds"].add(str(row.get("stateEventId")))
                    downtime = row.get("downtime")
                    if isinstance(downtime, dict) and self._is_pending(downtime):
                        bucket["pendingIds"].add(str(downtime.get("id")))

            if state == "producing":
                total_producing_spans.append(clipped)
            elif state == "stopped":
                total_stopped_spans.append(clipped)
                total_stop_ids.add(str(row.get("stateEventId")))
                raw_stopped_seconds += int(
                    (clipped[1] - clipped[0]).total_seconds()
                )
                downtime = row.get("downtime")
                if isinstance(downtime, dict):
                    pending = self._is_pending(downtime)
                    if pending:
                        total_pending_ids.add(str(downtime.get("id")))
                    key = str(downtime.get("reasonCode") or "pending")
                    label = downtime.get("reasonLabel") or (
                        "Motivo pendente" if pending else "Motivo não informado"
                    )
                else:
                    # Parada sem downtime válido: fato existe, motivo nunca
                    # foi registrado — não entra na contagem de pendentes.
                    key = "unrecorded"
                    label = "Motivo não registrado"
                    pending = False
                entry = reasons.setdefault(
                    key,
                    {
                        "reasonCode": downtime.get("reasonCode")
                        if isinstance(downtime, dict)
                        else None,
                        "label": label,
                        "seconds": 0,
                        "count": 0,
                        "pendingCount": 0,
                        "_ids": set(),
                    },
                )
                entry["seconds"] += int(
                    (clipped[1] - clipped[0]).total_seconds()
                )
                event_id = str(row.get("stateEventId"))
                if event_id not in entry["_ids"]:
                    entry["_ids"].add(event_id)
                    entry["count"] += 1
                if pending:
                    entry["pendingCount"] += 1

        merged_stopped = _merged_seconds(total_stopped_spans)
        overlap_seconds = raw_stopped_seconds - merged_stopped
        if overlap_seconds > 0:
            logger.warning(
                "mes_period_overlap_detected branch=%s work_center=%s "
                "overlap_seconds=%s",
                code,
                center,
                overlap_seconds,
            )

        return {
            "branch": code,
            "workCenter": center,
            "source": "mes",
            "reason": resolution["reason"],
            "timezone": FACTORY_TIMEZONE,
            "periodDays": days,
            "from": window_from.isoformat(),
            "to": window_to.isoformat(),
            "referenceAt": reference_at.astimezone(ZoneInfo("UTC"))
            .isoformat()
            .replace("+00:00", "Z"),
            "totals": {
                "producingSeconds": _merged_seconds(total_producing_spans),
                "stoppedSeconds": merged_stopped,
                "stopCount": len(total_stop_ids),
                "pendingReasonCount": len(total_pending_ids),
            },
            "days": [
                {
                    "date": bucket["date"],
                    "producingSeconds": _merged_seconds(bucket["producingSpans"]),
                    "stoppedSeconds": _merged_seconds(bucket["stoppedSpans"]),
                    "stopCount": len(bucket["stopIds"]),
                    "pendingReasonCount": len(bucket["pendingIds"]),
                }
                for bucket in per_day.values()
            ],
            "reasons": [
                {
                    "reasonCode": entry["reasonCode"],
                    "label": entry["label"],
                    "seconds": entry["seconds"],
                    "count": entry["count"],
                    "pendingCount": entry["pendingCount"],
                }
                for entry in sorted(
                    reasons.values(),
                    key=lambda item: item["seconds"],
                    reverse=True,
                )
            ],
            "quality": {
                # >0 ⇒ duas paradas sobrepostas dividiram o mesmo tempo —
                # a soma por motivo excede o total real; exibido como nota.
                "stopOverlapSeconds": overlap_seconds,
            },
        }

    @staticmethod
    def _is_pending(downtime: dict[str, Any]) -> bool:
        return (not downtime.get("confirmed")) or not downtime.get("reasonCode")
