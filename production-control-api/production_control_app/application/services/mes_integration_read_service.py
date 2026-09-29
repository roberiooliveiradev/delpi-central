from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from production_control_app.application.services.mes_timeline_builder import MesTimelineBuilder
from production_control_app.domain.errors import ProductionRunNotFound
from production_control_app.domain.ports.mes_monitoring_read_repository import (
    MesMonitoringReadRepositoryPort,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


class MesIntegrationReadService:
    def __init__(
        self,
        *,
        repository: MesMonitoringReadRepositoryPort,
        branch_access: BranchAccessService,
        timeline_builder: MesTimelineBuilder | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._branch_access = branch_access
        self._timeline_builder = timeline_builder or MesTimelineBuilder()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get_live_work_centers(self, *, branch: str) -> dict[str, Any]:
        code = self._branch_access.assert_valid_branch(branch)
        reference_at = self._clock()
        items = [self._live_item(row) for row in self._repository.list_live_work_centers(branch=code)]
        return {
            "branch": code,
            "referenceAt": reference_at.isoformat(),
            "summary": {
                "activeRuns": len(items),
                "producing": sum(item["operationalState"] == "producing" for item in items),
                "stopped": sum(item["operationalState"] == "stopped" for item in items),
                "paused": sum(item["runStatus"] == "paused" for item in items),
                "unclassifiedDowntimes": sum(
                    item["downtime"] is not None
                    and (
                        not item["downtime"]["confirmed"]
                        or item["downtime"]["reasonCode"] is None
                    )
                    for item in items
                ),
            },
            "items": items,
        }

    def get_run_timeline(self, run_id: str) -> dict[str, Any]:
        run = self._repository.get_run(run_id)
        if run is None:
            raise ProductionRunNotFound("Produção não encontrada.")
        events = []
        for row in self._repository.list_timeline_facts(run_id):
            downtime = None
            if row.get("downtime_id"):
                downtime = {
                    "id": row["downtime_id"],
                    "reasonCode": row.get("reason_code"),
                    "reasonLabel": row.get("reason_label"),
                    "category": row.get("category"),
                    "note": row.get("note"),
                    "confirmed": bool(row.get("confirmed")),
                    "source": row.get("downtime_source"),
                }
            events.append({**row, "downtime": downtime})
        return self._timeline_builder.build(run=run, events=events, reference_at=self._clock())

    def list_downtimes(
        self,
        *,
        branch: str,
        work_center: str | None = None,
        period_from: datetime | None = None,
        period_to: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        code = self._branch_access.assert_valid_branch(branch)
        if period_from and period_to and period_from >= period_to:
            raise ValueError("O início do período deve ser anterior ao fim.")
        if page < 1:
            raise ValueError("page deve ser maior ou igual a 1.")
        if page_size < 1 or page_size > 100:
            raise ValueError("pageSize deve estar entre 1 e 100.")
        reference_at = self._clock()
        rows, total = self._repository.list_downtimes(
            branch=code,
            work_center=(work_center or "").strip() or None,
            period_from=period_from,
            period_to=period_to,
            page=page,
            page_size=page_size,
        )
        return {
            "branch": code,
            "referenceAt": reference_at.isoformat(),
            "page": page,
            "pageSize": page_size,
            "total": total,
            "items": [self._downtime_item(row) for row in rows],
        }

    @staticmethod
    def _live_item(row: dict[str, Any]) -> dict[str, Any]:
        downtime = None
        if row.get("downtime_id"):
            downtime = {
                "id": row["downtime_id"],
                "startedAt": _iso(row.get("downtime_started_at")),
                "source": row.get("downtime_source"),
                "reasonCode": row.get("reason_code"),
                "reasonLabel": row.get("reason_label"),
                "category": row.get("category"),
                "confirmed": bool(row.get("confirmed")),
                "note": row.get("note"),
            }
        return {
            "branch": row["branch"],
            "workCenter": row["work_center"],
            "runId": row["run_id"],
            "runStatus": row["run_status"],
            "operationalState": row.get("operational_state"),
            "stateStartedAt": _iso(row.get("state_started_at")),
            "stateSource": row.get("state_source"),
            "integrityStatus": "complete" if row.get("state_id") else "incomplete",
            "productionOrder": row.get("production_order"),
            "operationCode": row.get("operation_code"),
            "operatorCode": row.get("operator_code"),
            "operatorName": row.get("operator_name"),
            "piecesTotal": int(row.get("pieces_total") or 0),
            "targetPieces": row.get("target_pieces"),
            "lastCountActivityAt": _iso(row.get("last_count_activity_at")),
            "downtime": downtime,
        }

    @staticmethod
    def _downtime_item(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "runId": row.get("run_id"),
            "workCenter": row["work_center"],
            "productionOrder": row.get("production_order"),
            "operationCode": row.get("operation_code"),
            "startedAt": _iso(row.get("started_at")),
            "endedAt": _iso(row.get("ended_at")),
            "source": row.get("source"),
            "reasonCode": row.get("reason_code"),
            "reasonLabel": row.get("reason_label"),
            "category": row.get("category"),
            "confirmed": bool(row.get("confirmed")),
            "note": row.get("note"),
        }
