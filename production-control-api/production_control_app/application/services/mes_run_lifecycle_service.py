"""Orquestra os fatos MES do ciclo de vida do Production Run.

Cada método presume que o chamador já abriu a transação compartilhada
(``PostgresProductionRunRepository.transaction()``) e locou o run com
``FOR UPDATE``: aqui só se decide *quais* fatos MES escrever naquele ``conn``.

Política para runs legados (criados antes da Etapa 02, sem nenhum evento de
estado observado):

- Pause/Stop **registram fatos reais a partir de agora** — a parada do Pause é
  um fato novo, não backfill; abrir ``stopped``/``downtime`` é legítimo.
- Resume de um run pausado antes da fundação não encontra parada/estado e
  segue sem escrita MES (não inventa histórico).

Já inconsistências *observadas* (evento aberto de outro run, estado aberto que
não é o esperado para a transição) abortam com erro de domínio: falhar de
forma controlada é preferível a gravar fato falso.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from production_control_app.domain.errors import (
    DowntimeClassificationRequired,
    DowntimeConflict,
    InvalidMesEvent,
    MesStateConflict,
)
from production_control_app.domain.ports.downtime_event_repository import (
    DowntimeEventRepositoryPort,
)
from production_control_app.domain.ports.downtime_reason_repository import (
    DowntimeReasonRepositoryPort,
)
from production_control_app.domain.ports.work_center_state_repository import (
    WorkCenterStateRepositoryPort,
)
from production_control_app.domain.services.mes_operational_state import (
    WorkCenterOperationalState,
)


class MesRunLifecycleService:
    """Sequência MES de cada transição do run, dentro da transação do chamador."""

    def __init__(
        self,
        *,
        states: WorkCenterStateRepositoryPort,
        downtimes: DowntimeEventRepositoryPort,
        reasons: DowntimeReasonRepositoryPort | None = None,
    ) -> None:
        self._states = states
        self._downtimes = downtimes
        self._reasons = reasons

    def record_run_started(
        self, run: dict[str, Any], *, conn: Any, at: datetime
    ) -> dict[str, Any]:
        """PLAY → abre ``producing`` vinculado ao run."""
        return self._states.open_event(
            branch=run["branch"],
            work_center=run["work_center"],
            state=WorkCenterOperationalState.PRODUCING.value,
            source="operator",
            run_id=run["id"],
            started_at=at,
            conn=conn,
        )

    def record_run_paused(
        self, run: dict[str, Any], *, conn: Any, at: datetime
    ) -> dict[str, Any]:
        """PAUSE → fecha ``producing``, abre ``stopped``, cria parada sem motivo."""
        branch, wc = run["branch"], run["work_center"]
        open_state = self._states.get_open(branch=branch, work_center=wc, conn=conn)
        if open_state is not None:
            self._expect_run_state(
                open_state, run, expected=WorkCenterOperationalState.PRODUCING
            )
            self._states.close_open(branch=branch, work_center=wc, ended_at=at, conn=conn)
        stopped = self._states.open_event(
            branch=branch,
            work_center=wc,
            state=WorkCenterOperationalState.STOPPED.value,
            source="operator",
            run_id=run["id"],
            started_at=at,
            conn=conn,
        )
        return self._downtimes.create(
            branch=branch,
            work_center=wc,
            source="operator_pause",
            run_id=run["id"],
            state_event_id=stopped["id"],
            production_order=run.get("production_order"),
            operation_code=run.get("operation_code"),
            started_at=at,
            conn=conn,
        )

    def record_run_resumed(
        self, run: dict[str, Any], *, conn: Any, at: datetime
    ) -> dict[str, Any] | None:
        """RESUME → encerra parada, fecha ``stopped``, abre ``producing``."""
        branch, wc = run["branch"], run["work_center"]
        open_downtime = self._downtimes.get_open(branch=branch, work_center=wc, conn=conn)
        open_state = self._states.get_open(branch=branch, work_center=wc, conn=conn)

        if open_downtime is None and open_state is None:
            # Run pausado antes da fundação MES: nada observado, nada a fechar.
            opened = self._states.open_event(
                branch=branch,
                work_center=wc,
                state=WorkCenterOperationalState.PRODUCING.value,
                source="operator",
                run_id=run["id"],
                started_at=at,
                conn=conn,
            )
            return opened
        if open_downtime is None or open_downtime["run_id"] != run["id"]:
            raise InvalidMesEvent(
                "Resume esperava a parada aberta deste run e não a encontrou."
            )
        self._require_classified(open_downtime)
        if open_state is None:
            raise InvalidMesEvent(
                "Resume esperava estado 'stopped' aberto e não encontrou nenhum."
            )
        self._expect_run_state(
            open_state, run, expected=WorkCenterOperationalState.STOPPED
        )
        self._downtimes.close_open(branch=branch, work_center=wc, ended_at=at, conn=conn)
        self._states.close_open(branch=branch, work_center=wc, ended_at=at, conn=conn)
        return self._states.open_event(
            branch=branch,
            work_center=wc,
            state=WorkCenterOperationalState.PRODUCING.value,
            source="operator",
            run_id=run["id"],
            started_at=at,
            conn=conn,
        )

    def record_run_finished(
        self, run: dict[str, Any], *, conn: Any, at: datetime
    ) -> None:
        """STOP → encerra parada/estado abertos do run. Não abre ``idle`` ainda."""
        branch, wc = run["branch"], run["work_center"]
        open_downtime = self._downtimes.get_open(branch=branch, work_center=wc, conn=conn)
        if open_downtime is not None:
            if open_downtime["run_id"] != run["id"]:
                raise DowntimeConflict(
                    "Existe parada aberta de outro run neste posto."
                )
            self._require_classified(open_downtime)
            self._downtimes.close_open(
                branch=branch, work_center=wc, ended_at=at, conn=conn
            )
        open_state = self._states.get_open(branch=branch, work_center=wc, conn=conn)
        if open_state is not None:
            if open_state["run_id"] != run["id"]:
                raise MesStateConflict(
                    "Existe estado operacional aberto de outro run neste posto."
                )
            self._states.close_open(
                branch=branch, work_center=wc, ended_at=at, conn=conn
            )

    def open_downtime_view(self, run: dict[str, Any]) -> dict[str, Any] | None:
        """Resumo público da parada aberta do run (classificada ou pendente)."""
        open_dt = self._downtimes.get_open(
            branch=run["branch"], work_center=run["work_center"]
        )
        if open_dt is None or open_dt["run_id"] != run["id"]:
            return None
        reason_label = None
        category = None
        if open_dt.get("reason_code") and self._reasons is not None:
            reason = self._reasons.get(str(open_dt["reason_code"]))
            if reason is not None:
                reason_label = reason.get("label")
                category = reason.get("category")
        return {
            "id": open_dt["id"],
            "runId": run["id"],
            "reasonCode": open_dt.get("reason_code"),
            "reasonLabel": reason_label,
            "category": category,
            "note": open_dt.get("note"),
            "confirmed": bool(open_dt.get("confirmed")),
            "startedAt": open_dt["started_at"].isoformat()
            if hasattr(open_dt.get("started_at"), "isoformat")
            else open_dt.get("started_at"),
            "endedAt": None,
        }

    @staticmethod
    def _require_classified(open_downtime: dict[str, Any]) -> None:
        if not open_downtime.get("reason_code") or not open_downtime.get("confirmed"):
            raise DowntimeClassificationRequired(
                "Informe o motivo da parada antes de continuar."
            )

    @staticmethod
    def _expect_run_state(
        open_state: dict[str, Any],
        run: dict[str, Any],
        *,
        expected: WorkCenterOperationalState,
    ) -> None:
        if open_state["run_id"] != run["id"]:
            raise MesStateConflict(
                "Existe estado operacional aberto de outro run neste posto."
            )
        if open_state["state"] != expected.value:
            raise InvalidMesEvent(
                f"Estado operacional aberto é '{open_state['state']}', "
                f"esperado '{expected.value}' para esta transição."
            )
