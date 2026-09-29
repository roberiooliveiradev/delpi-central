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

import logging
from datetime import datetime, timezone
from typing import Any, Callable

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


logger = logging.getLogger(__name__)


class MesRunLifecycleService:
    """Sequência MES de cada transição do run, dentro da transação do chamador."""

    def __init__(
        self,
        *,
        states: WorkCenterStateRepositoryPort,
        downtimes: DowntimeEventRepositoryPort,
        reasons: DowntimeReasonRepositoryPort | None = None,
        run_lookup: Callable[[str], dict[str, Any] | None] | None = None,
    ) -> None:
        self._states = states
        self._downtimes = downtimes
        self._reasons = reasons
        self._run_lookup = run_lookup

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
        open_dt = self._downtimes.get_open(branch=branch, work_center=wc, conn=conn)
        if (
            open_state is not None
            and open_state["state"] == WorkCenterOperationalState.STOPPED.value
            and open_state["run_id"] == run["id"]
            and open_dt is not None
            and open_dt["run_id"] == run["id"]
        ):
            # Parada automática já aberta: Pause manual só muda run.status —
            # stopped/downtime existentes são reutilizados, sem fatos duplicados.
            return open_dt
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

    def record_automatic_stopped(
        self, run: dict[str, Any], *, conn: Any, at: datetime
    ) -> dict[str, Any] | None:
        """Auto-stop por ausência de golpes: fecha ``producing``, abre
        ``stopped`` + downtime ``source='system'`` — tudo em ``at`` =
        ``last_count_activity_at``. Idempotente: retorna ``None`` quando a
        parada automática já existe (tick seguinte não duplica)."""
        branch, wc = run["branch"], run["work_center"]
        self._close_finished_owner_facts(branch=branch, work_center=wc, conn=conn)
        open_dt = self._downtimes.get_open(branch=branch, work_center=wc, conn=conn)
        if open_dt is not None:
            if open_dt["run_id"] != run["id"]:
                raise DowntimeConflict(
                    "Existe parada aberta de outro run neste posto."
                )
            return None
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
            source="system",
            run_id=run["id"],
            started_at=at,
            conn=conn,
        )
        dt = self._downtimes.create(
            branch=branch,
            work_center=wc,
            source="system",
            run_id=run["id"],
            state_event_id=stopped["id"],
            production_order=run.get("production_order"),
            operation_code=run.get("operation_code"),
            started_at=at,
            conn=conn,
        )
        if int(run.get("pieces_total") or 0) == 0:
            # Parada sem nenhuma peça contada desde o Play: motivo inicial
            # ``setup`` (editável pelo operador enquanto a parada está aberta).
            dt = self._apply_initial_setup_reason(dt, conn=conn)
        return dt

    def record_automatic_resumed(
        self, run: dict[str, Any], *, conn: Any, at: datetime
    ) -> dict[str, Any] | None:
        """Novo golpe em ``running`` + ``stopped`` automático: encerra parada e
        estado, reabre ``producing``. Retorna a parada encerrada (``None``
        quando nada a fechar). Não exige classificação — o motivo pode ser
        informado depois, com a máquina já produzindo."""
        branch, wc = run["branch"], run["work_center"]
        self._close_finished_owner_facts(branch=branch, work_center=wc, conn=conn)
        open_state = self._states.get_open(branch=branch, work_center=wc, conn=conn)
        open_dt = self._downtimes.get_open(branch=branch, work_center=wc, conn=conn)
        if open_state is None and open_dt is None:
            return None
        if (
            open_state is None
            or open_state["state"] != WorkCenterOperationalState.STOPPED.value
        ):
            return None
        self._expect_run_state(
            open_state, run, expected=WorkCenterOperationalState.STOPPED
        )
        if open_dt is not None:
            if open_dt["run_id"] != run["id"]:
                raise DowntimeConflict(
                    "Existe parada aberta de outro run neste posto."
                )
            self._downtimes.close_open(
                branch=branch, work_center=wc, ended_at=at, conn=conn
            )
        self._states.close_open(branch=branch, work_center=wc, ended_at=at, conn=conn)
        self._states.open_event(
            branch=branch,
            work_center=wc,
            state=WorkCenterOperationalState.PRODUCING.value,
            source="system",
            run_id=run["id"],
            started_at=at,
            conn=conn,
        )
        return open_dt

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

    def open_state_view(self, run: dict[str, Any]) -> str | None:
        """Estado operacional aberto do run (``producing``/``stopped``/…)."""
        open_state = self._states.get_open(
            branch=run["branch"], work_center=run["work_center"]
        )
        if open_state is None or open_state["run_id"] != run["id"]:
            return None
        return str(open_state["state"])

    def pending_classification_view(
        self, run: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, int]:
        """Parada não classificada mais antiga do run + total pendente."""
        rows = self._downtimes.list_pending_classification(run["id"], limit=5)
        if not rows:
            return None, 0
        return self._downtime_view(rows[0], run), len(rows)

    def _downtime_view(
        self, dt: dict[str, Any], run: dict[str, Any]
    ) -> dict[str, Any]:
        reason_label = None
        category = None
        if dt.get("reason_code") and self._reasons is not None:
            reason = self._reasons.get(str(dt["reason_code"]))
            if reason is not None:
                reason_label = reason.get("label")
                category = reason.get("category")
        started = dt.get("started_at")
        ended = dt.get("ended_at")
        return {
            "id": dt["id"],
            "runId": run["id"],
            "reasonCode": dt.get("reason_code"),
            "reasonLabel": reason_label,
            "category": category,
            "note": dt.get("note"),
            "confirmed": bool(dt.get("confirmed")),
            "source": dt.get("source"),
            "startedAt": started.isoformat() if hasattr(started, "isoformat") else started,
            "endedAt": ended.isoformat() if hasattr(ended, "isoformat") else None,
        }

    def open_downtime_view(self, run: dict[str, Any]) -> dict[str, Any] | None:
        """Resumo público da parada aberta do run (classificada ou pendente)."""
        open_dt = self._downtimes.get_open(
            branch=run["branch"], work_center=run["work_center"]
        )
        if open_dt is None or open_dt["run_id"] != run["id"]:
            return None
        return self._downtime_view(open_dt, run)

    def _apply_initial_setup_reason(
        self, dt: dict[str, Any], *, conn: Any
    ) -> dict[str, Any]:
        """Motivo inicial ``setup`` para parada automática sem peça contada.

        Confirmado pelo sistema — permanece editável pelo operador enquanto
        a parada está aberta, como qualquer parada classificada. Se o
        catálogo não oferecer o motivo, a parada segue pendente (nunca
        inventa código fora do catálogo).
        """
        if self._reasons is None:
            return dt
        reason = self._reasons.get("setup")
        if reason is None or not reason.get("active"):
            return dt
        return self._downtimes.classify(
            dt["id"],
            reason_code=reason["code"],
            planned=reason.get("default_planned"),
            counts_as_availability_loss=reason.get("default_counts_as_availability_loss"),
            confirmed_by_type="system",
            confirmed_by_ref="auto-downtime",
            conn=conn,
        )

    def _close_finished_owner_facts(
        self, *, branch: str, work_center: str, conn: Any
    ) -> None:
        """Encerra parada/estado abertos cujo run dono já terminou.

        Fato operacional não pode sobreviver ao próprio run — a fronteira
        real é o ``ended_at`` do run dono. Sem a cura, a parada órfã
        bloqueia toda detecção automática do posto (conflito a cada tick)
        sem aparecer em nenhuma pendência. Se o dono segue ``running``/
        ``paused`` o conflito é real e os callers abortam como antes.
        """
        if self._run_lookup is None:
            return
        for kind, repo in (("downtime", self._downtimes), ("state", self._states)):
            open_fact = repo.get_open(
                branch=branch, work_center=work_center, conn=conn
            )
            if open_fact is None or not open_fact.get("run_id"):
                continue
            owner = self._run_lookup(str(open_fact["run_id"]))
            if owner is None or str(owner.get("status")) in {"running", "paused"}:
                continue
            boundary = owner.get("ended_at") or datetime.now(timezone.utc)
            started = open_fact.get("started_at")
            if started is not None and boundary < started:
                boundary = started
            repo.close_open(
                branch=branch, work_center=work_center, ended_at=boundary, conn=conn
            )
            logger.warning(
                "mes_orphan_fact_closed kind=%s fact_id=%s owner_run=%s "
                "branch=%s work_center=%s",
                kind,
                open_fact.get("id"),
                open_fact.get("run_id"),
                branch,
                work_center,
            )

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
