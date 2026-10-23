"""Fonte de paradas do cockpit público — resolução por (filial, CT).

Somente leitura: valida o token do cockpit, o escopo (filial + CT na fila
publicada) e devolve qual fonte o cockpit deve consumir — MES, TOTVS ou
indisponível — sem efeitos colaterais (nada de TOTVS, seed, run ou escrita).

A política de decisão é o resolver puro de domínio
(downtime_source_selection); este serviço só orquestra as consultas.
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
from production_control_app.domain.errors import PublicAccessDenied, PulseGatewayError
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.downtime_source_selection import (
    resolve_downtime_source,
)

logger = logging.getLogger(__name__)

FACTORY_TIMEZONE = "America/Sao_Paulo"


class PublicWorkCenterDowntimeSourceService:
    def __init__(
        self,
        *,
        access: PublicCockpitAccessService,
        machine_load: MachineLoadService,
        branch_access: BranchAccessService,
        pulse_gateway: Any,
        mes_monitoring: Any,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._access = access
        self._machine_load = machine_load
        self._branch_access = branch_access
        self._pulse = pulse_gateway
        self._mes_monitoring = mes_monitoring
        self._clock = clock or (
            lambda: datetime.now(ZoneInfo(FACTORY_TIMEZONE))
        )

    def list_sensorized(self, *, token: str, branch: str) -> dict[str, Any]:
        """CTs sensorizados (vínculo pulse_counter) da filial.

        RQ-11: a «Atividade do posto» precisa alcançar CTs sem OP
        publicada — a lista sensorizada é o contrato de descoberta
        legítimo do seletor do cockpit. Falha do Pulse propaga como
        indisponibilidade explícita, nunca lista vazia fingida.
        """
        if not self._access.is_valid_token(token):
            raise PublicAccessDenied(
                self._access.message(
                    "invalidToken", "Link do cockpit inválido ou desativado."
                )
            )
        code = self._branch_access.assert_valid_branch(branch)
        payload = self._pulse.fetch_branch_counter_snapshots(
            branch=code, role_key="pulse_counter"
        )
        centers = sorted(
            {
                str(item.get("workCenterCode")).strip()
                for item in payload.get("items") or []
                if isinstance(item, dict)
                and str(item.get("workCenterCode") or "").strip()
            }
        )
        return {"branch": code, "items": [{"workCenter": wc} for wc in centers]}

    def resolve(
        self,
        *,
        token: str,
        branch: str,
        work_center: str,
    ) -> dict[str, Any]:
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

        # Escopo: fila publicada OU CT sensorizado com vínculo Pulse ativo
        # (PC-MES-CT-AUTONOMOUS-DOWNTIME, RQ-11) — a autorização efetiva
        # continua sendo token + sessão de bancada do posto; a fila deixa
        # de ser pré-requisito porque um CT sem OP publicada precisa ser
        # monitorável. O erro «fora da fila» só aparece quando o CT não é
        # sensorizado (fonte TOTVS/indisponível) — não há telemetria para
        # expor fora do escopo.
        in_queue = (
            self._machine_load.public_snapshot_work_center_resources(
                branch=code, work_center=center
            )
            is not None
        )

        reference_at = self._clock()

        bound_counters: int | None = None
        try:
            snapshot = self._pulse.fetch_work_center_snapshot(
                branch=code,
                work_center=center,
                role_key="pulse_counter",
            )
            items = snapshot.get("items")
            if not isinstance(items, list):
                raise PulseGatewayError(
                    "Resposta do Pulso sem lista de dispositivos."
                )
            bound_counters = len(items)
        except PulseGatewayError as exc:
            # Falha do Pulse NUNCA é prova de ausência de sensores.
            logger.warning(
                "downtime_source_pulse_unavailable branch=%s work_center=%s err=%s",
                code,
                center,
                exc,
            )

        mes_activity_today = False
        if bound_counters == 0:
            # Só consulta fatos MES quando o vínculo está ausente — e só a
            # consulta de existência é necessária (sem timeline completa).
            day_start = datetime.combine(
                reference_at.date(), time.min, tzinfo=reference_at.tzinfo
            )
            day_end = day_start + timedelta(days=1)
            try:
                mes_activity_today = self._mes_monitoring.has_activity_in_period(
                    branch=code,
                    work_center=center,
                    period_from=day_start,
                    period_to=day_end,
                )
            except Exception:  # noqa: BLE001 — leitura falhou → inconclusivo
                logger.warning(
                    "downtime_source_mes_activity_failed branch=%s work_center=%s",
                    code,
                    center,
                    exc_info=True,
                )
                bound_counters = None

        source, reason = resolve_downtime_source(
            lookup_ok=bound_counters is not None,
            bound_counters=bound_counters or 0,
            mes_activity_today=mes_activity_today,
        )
        if not in_queue and source != "mes":
            raise ValueError(
                f"Centro de trabalho «{center}» não está na fila publicada desta filial."
            )
        if source == "unavailable" and reason == "multiple_bound_counters":
            logger.warning(
                "downtime_source_ambiguous branch=%s work_center=%s counters=%s",
                code,
                center,
                bound_counters,
            )
        return {
            "branch": code,
            "workCenter": center,
            "source": source,
            "reason": reason,
            "referenceAt": reference_at.astimezone(ZoneInfo("UTC"))
            .isoformat()
            .replace("+00:00", "Z"),
        }
