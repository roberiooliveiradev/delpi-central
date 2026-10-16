"""Estados de execução do cockpit para a Carga Máquina — leitura MES local.

A fonte oficial de «o que está produzindo» passa a ser o PostgreSQL local
(``production_control.production_runs`` + ``work_center_state_events``), não
mais a HZA/TOTVS nem o Production Pulse: este serviço nunca recebe gateway de
rede. A consulta é uma só por filial (anti-N+1 via
``MesMonitoringReadRepositoryPort.list_live_work_centers``) e devolve o
snapshot completo dos runs abertos — runs sem estado operacional válido
aparecem como ``unknown`` com ``integrity_status`` sinalizado, nunca somem
silenciosamente.

Identidade pessoal não faz parte do contrato: operador é quem executa, não o
que o PCP consulta — ``operator_code``/``operator_name`` ficam no banco.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from production_control_app.core.security import PC_MACHINE_LOAD_VIEW, can
from production_control_app.domain.ports.mes_monitoring_read_repository import (
    MesMonitoringReadRepositoryPort,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService

_OPEN_RUN_STATUSES = frozenset({"running", "paused"})

_DISPLAY_PRODUCING = "producing"
_DISPLAY_STOPPED = "stopped"
_DISPLAY_PAUSED = "paused"
_DISPLAY_UNKNOWN = "unknown"

_INTEGRITY_COMPLETE = "complete"
_INTEGRITY_INCONSISTENT = "inconsistent"

_STATE_PRODUCING = "producing"
_STATE_STOPPED = "stopped"


def _classify(
    run_status: str, operational_state: str | None
) -> tuple[str, str]:
    """run_status + estado MES aberto → (display_status, integrity_status).

    ``running`` sozinho não prova produção: só o estado operacional aberto
    distingue produzindo de parado. Combinações fora da tabela não recebem
    classificação inventada — viram ``unknown`` com integridade sinalizada.
    """
    if run_status == "running":
        if operational_state == _STATE_PRODUCING:
            return _DISPLAY_PRODUCING, _INTEGRITY_COMPLETE
        if operational_state == _STATE_STOPPED:
            return _DISPLAY_STOPPED, _INTEGRITY_COMPLETE
        return _DISPLAY_UNKNOWN, _INTEGRITY_INCONSISTENT
    if run_status == "paused" and operational_state == _STATE_STOPPED:
        return _DISPLAY_PAUSED, _INTEGRITY_COMPLETE
    return _DISPLAY_UNKNOWN, _INTEGRITY_INCONSISTENT


def _item(row: dict[str, Any]) -> dict[str, Any] | None:
    run_status = str(row.get("run_status") or "").strip()
    if run_status not in _OPEN_RUN_STATUSES:
        # O repositório já filtra; o cinto de segurança cobre fakes/reads antigas.
        return None
    operational_state = row.get("operational_state")
    if isinstance(operational_state, str):
        operational_state = operational_state.strip() or None
    display_status, integrity_status = _classify(run_status, operational_state)
    started_at = row.get("run_started_at")
    return {
        "run_id": row.get("run_id"),
        "work_center": row.get("work_center"),
        "production_order": row.get("production_order"),
        "operation_code": row.get("operation_code"),
        "run_status": run_status,
        "operational_state": operational_state,
        "display_status": display_status,
        "integrity_status": integrity_status,
        "started_at": (
            started_at.isoformat() if hasattr(started_at, "isoformat") else started_at
        ),
    }


class MachineLoadCockpitStatusService:
    """Snapshot dos runs abertos do cockpit por filial — sem HZA, sem Pulse."""

    def __init__(
        self,
        *,
        repository: MesMonitoringReadRepositoryPort,
        branch_access: BranchAccessService,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._branch_access = branch_access
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def cockpit_status(self, user: object | None, *, branch: str) -> dict[str, Any]:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_MACHINE_LOAD_VIEW):
            raise PermissionError(
                "Você não tem permissão para ver a carga máquina."
            )
        code = self._branch_access.assert_valid_branch(branch)

        rows = self._repository.list_live_work_centers(branch=code)
        items: list[dict[str, Any]] = []
        seen_run_ids: set[str] = set()
        for row in rows:
            run_id = str(row.get("run_id") or "")
            if run_id and run_id in seen_run_ids:
                continue
            if run_id:
                seen_run_ids.add(run_id)
            item = _item(row)
            if item is not None:
                items.append(item)

        summary = {
            "active_runs": len(items),
            "producing": 0,
            "stopped": 0,
            "paused": 0,
            "unknown": 0,
        }
        for item in items:
            summary[item["display_status"]] += 1

        return {
            "branch": code,
            "source": "cockpit",
            "as_of": self._clock().isoformat(),
            "summary": summary,
            "items": items,
        }
