"""Timeline operacional do Production Run (Etapa 04).

Persiste-se somente fatos (`work_center_state_events`, `downtime_events`);
este serviço **deriva** durações e resumo a partir dos timestamps, usando
``referenceAt`` (relógio do backend) como instante de fechamento de eventos
abertos. Nenhum OEE é calculado aqui.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from production_control_app.domain.ports.downtime_event_repository import (
    DowntimeEventRepositoryPort,
)
from production_control_app.domain.ports.downtime_reason_repository import (
    DowntimeReasonRepositoryPort,
)
from production_control_app.domain.ports.work_center_state_repository import (
    WorkCenterStateRepositoryPort,
)


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _seconds(start: Any, end: Any) -> int:
    """Duração derivada; nunca negativa."""
    try:
        delta = (end - start).total_seconds()
    except Exception:  # noqa: BLE001 — defensivo para timestamps heterogêneos
        return 0
    return max(0, int(delta))


class MesRunTimelineService:
    def __init__(
        self,
        *,
        run_service: Any,
        states: WorkCenterStateRepositoryPort,
        downtimes: DowntimeEventRepositoryPort,
        reasons: DowntimeReasonRepositoryPort | None = None,
    ) -> None:
        self._run_service = run_service
        self._states = states
        self._downtimes = downtimes
        self._reasons = reasons

    def get_timeline(self, run_id: str, *, session_token: str | None) -> dict[str, Any]:
        session = self._run_service.resolve_bench_session(session_token)
        run = self._run_service.require_active_run_for_session(run_id, session=session)

        reference_at = datetime.now(timezone.utc)
        events = self._states.list_for_run(run["id"])
        dts_by_state = {
            d["state_event_id"]: d
            for d in self._downtimes.list_for_run(run["id"])
            if d.get("state_event_id")
        }

        items: list[dict[str, Any]] = []
        producing_seconds = 0
        stopped_seconds = 0
        stop_count = 0

        for event in sorted(events, key=lambda e: e["started_at"]):
            started = event["started_at"]
            ended = event.get("ended_at")
            duration = _seconds(started, ended or reference_at)

            downtime_view = None
            downtime = dts_by_state.get(event["id"])
            if downtime is not None:
                reason_label = None
                category = None
                if downtime.get("reason_code") and self._reasons is not None:
                    reason = self._reasons.get(str(downtime["reason_code"]))
                    if reason is not None:
                        reason_label = reason.get("label")
                        category = reason.get("category")
                downtime_view = {
                    "id": downtime["id"],
                    "reasonCode": downtime.get("reason_code"),
                    "reasonLabel": reason_label,
                    "category": category,
                    "note": downtime.get("note"),
                    "confirmed": bool(downtime.get("confirmed")),
                }

            if event["state"] == "producing":
                producing_seconds += duration
            elif event["state"] == "stopped":
                stopped_seconds += duration
                stop_count += 1

            items.append(
                {
                    "id": event["id"],
                    "state": event["state"],
                    "startedAt": _iso(started),
                    "endedAt": _iso(ended),
                    "durationSeconds": duration,
                    "source": event.get("source"),
                    "downtime": downtime_view,
                }
            )

        first_started = events[0]["started_at"] if events else run.get("started_at")
        run_ended = run.get("ended_at")
        elapsed_seconds = (
            _seconds(first_started, run_ended or reference_at)
            if first_started is not None
            else 0
        )

        return {
            "runId": run["id"],
            "branch": run["branch"],
            "workCenter": run["work_center"],
            "status": run.get("status"),
            "referenceAt": reference_at.isoformat(),
            "summary": {
                "elapsedSeconds": elapsed_seconds,
                "producingSeconds": producing_seconds,
                "stoppedSeconds": stopped_seconds,
                "stopCount": stop_count,
            },
            "items": items,
        }
