"""Timeline operacional do Production Run (Etapa 04).

Persiste-se somente fatos (`work_center_state_events`, `downtime_events`);
este serviço **deriva** durações e resumo a partir dos timestamps, usando
``referenceAt`` (relógio do backend) como instante de fechamento de eventos
abertos. Nenhum OEE é calculado aqui.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from production_control_app.application.services.mes_timeline_builder import MesTimelineBuilder
from production_control_app.domain.ports.downtime_event_repository import (
    DowntimeEventRepositoryPort,
)
from production_control_app.domain.ports.downtime_reason_repository import (
    DowntimeReasonRepositoryPort,
)
from production_control_app.domain.ports.work_center_state_repository import (
    WorkCenterStateRepositoryPort,
)


class MesRunTimelineService:
    def __init__(
        self,
        *,
        run_service: Any,
        states: WorkCenterStateRepositoryPort,
        downtimes: DowntimeEventRepositoryPort,
        reasons: DowntimeReasonRepositoryPort | None = None,
        timeline_builder: MesTimelineBuilder | None = None,
    ) -> None:
        self._run_service = run_service
        self._states = states
        self._downtimes = downtimes
        self._reasons = reasons
        self._timeline_builder = timeline_builder or MesTimelineBuilder()

    def get_timeline(self, run_id: str, *, session_token: str | None) -> dict[str, Any]:
        session = self._run_service.resolve_bench_session(session_token)
        run = self._run_service.require_active_run_for_session(run_id, session=session)
        downtimes_by_state = {
            downtime["state_event_id"]: downtime
            for downtime in self._downtimes.list_for_run(run["id"])
            if downtime.get("state_event_id")
        }
        events = []
        for event in self._states.list_for_run(run["id"]):
            downtime = downtimes_by_state.get(event["id"])
            events.append(
                {
                    **event,
                    "downtime": self._downtime_view(downtime) if downtime else None,
                }
            )
        return self._timeline_builder.build(
            run=run,
            events=events,
            reference_at=datetime.now(timezone.utc),
        )

    def _downtime_view(self, downtime: dict[str, Any]) -> dict[str, Any]:
        reason_label = None
        category = None
        if downtime.get("reason_code") and self._reasons is not None:
            reason = self._reasons.get(str(downtime["reason_code"]))
            if reason is not None:
                reason_label = reason.get("label")
                category = reason.get("category")
        return {
            "id": downtime["id"],
            "reasonCode": downtime.get("reason_code"),
            "reasonLabel": reason_label,
            "category": category,
            "note": downtime.get("note"),
            "confirmed": bool(downtime.get("confirmed")),
            "source": downtime.get("source"),
        }
