"""Histórico diário MES do posto no cockpit público (Etapa 2).

Linha do tempo do dia civil (America/Sao_Paulo) com estados, paradas,
motivos e pendências — somente leitura, escopado por sessão de bancada do
mesmo (filial, CT). A fonte (mes/totvs/unavailable) vem do resolvedor da
Etapa 1, sem reimplementar a política.
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
from production_control_app.domain.errors import (
    BenchSessionRequired,
    DowntimeSourceUnavailable,
    PublicAccessDenied,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService

logger = logging.getLogger(__name__)

FACTORY_TIMEZONE = "America/Sao_Paulo"


def _parse(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _clip_seconds(
    started: datetime | None,
    ended: datetime | None,
    *,
    window_from: datetime,
    window_to: datetime,
) -> int:
    """Segundos do intervalo dentro da janela do dia (recorte, nunca negativo)."""
    if started is None:
        return 0
    eff_start = max(started, window_from)
    eff_end = min(ended or window_to, window_to)
    return max(0, int((eff_end - eff_start).total_seconds()))


def _merged_seconds(intervals: list[tuple[datetime, datetime]]) -> int:
    """Soma de intervalos sobrepostos contados uma única vez — durações de
    eventos anômalos sobrepostos não inflam o resumo."""
    spans = sorted(intervals)
    total = 0
    cur_start = cur_end = None
    for start, end in spans:
        if cur_start is None:
            cur_start, cur_end = start, end
            continue
        if start <= cur_end:
            cur_end = max(cur_end, end)
            continue
        total += int((cur_end - cur_start).total_seconds())
        cur_start, cur_end = start, end
    if cur_start is not None:
        total += int((cur_end - cur_start).total_seconds())
    return total


class PublicMesWorkCenterTodayService:
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

    def get_today(
        self,
        *,
        token: str,
        branch: str,
        work_center: str,
        session_token: str | None,
    ) -> dict[str, Any]:
        # 1. link público + 2. filial/CT publicado — mesmo escopo da Etapa 1.
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
        # 3-4. Sessão de bancada obrigatória e pertencente a ESTE posto —
        # o workCenter do navegador nunca é autoridade.
        session = self._run_service.resolve_bench_session(session_token)
        if (
            session.get("branch") != code
            or session.get("work_center") != center
        ):
            raise BenchSessionRequired(
                "Sessão não corresponde ao posto selecionado."
            )

        # 5. Fonte oficial (Etapa 1): TOTVS responde controlado sem consultar
        # histórico MES; unavailable é explícito, sem fallback.
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
            reference_at.date(), time.min, tzinfo=reference_at.tzinfo
        )
        window_to = reference_at

        timeline = self._integration_read.get_work_center_timeline(
            branch=code,
            work_center=center,
            period_from=window_from,
            period_to=window_to,
        )

        items: list[dict[str, Any]] = []
        producing_spans: list[tuple[datetime, datetime]] = []
        stopped_spans: list[tuple[datetime, datetime]] = []
        stop_ids: set[str] = set()
        pending_ids: set[str] = set()
        for row in timeline["items"]:
            started = _parse(row.get("startedAt"))
            ended = _parse(row.get("endedAt"))
            duration = _clip_seconds(
                started, ended, window_from=window_from, window_to=window_to
            )
            item = dict(row)
            item["effectiveDurationSeconds"] = duration
            dt = item.get("downtime")
            if isinstance(dt, dict):
                # Motivo pendente: downtime existente sem confirmação OU sem
                # código — setup confirmado pelo sistema não é pendência.
                pending = (not dt.get("confirmed")) or not dt.get("reasonCode")
                item["downtime"] = {**dt, "pendingReason": pending}
                if pending:
                    pending_ids.add(str(dt.get("id")))
            items.append(item)

            if started is not None:
                span = (
                    max(started, window_from),
                    min(ended or window_to, window_to),
                )
                state = item.get("state")
                if state == "producing":
                    producing_spans.append(span)
                elif state == "stopped":
                    stopped_spans.append(span)
                    stop_ids.add(str(item.get("stateEventId")))

        if len(items) > 1:
            for i in range(1, len(items)):
                prev_end = _parse(items[i - 1].get("endedAt")) or window_to
                cur_start = _parse(items[i].get("startedAt"))
                if cur_start is not None and cur_start < prev_end:
                    logger.warning(
                        "mes_today_overlap_detected branch=%s work_center=%s "
                        "prev_event=%s cur_event=%s",
                        code,
                        center,
                        items[i - 1].get("stateEventId"),
                        items[i].get("stateEventId"),
                    )

        return {
            "branch": code,
            "workCenter": center,
            "source": "mes",
            "reason": resolution["reason"],
            "date": window_from.date().isoformat(),
            "timezone": FACTORY_TIMEZONE,
            "from": window_from.isoformat(),
            "to": window_to.isoformat(),
            "referenceAt": reference_at.astimezone(ZoneInfo("UTC"))
            .isoformat()
            .replace("+00:00", "Z"),
            "summary": {
                "producingSeconds": _merged_seconds(producing_spans),
                "stoppedSeconds": _merged_seconds(stopped_spans),
                "stopCount": len(stop_ids),
                "pendingReasonCount": len(pending_ids),
            },
            "items": items,
        }
