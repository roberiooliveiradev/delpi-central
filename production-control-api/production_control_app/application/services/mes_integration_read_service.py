from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from production_control_app.application.services.mes_timeline_builder import MesTimelineBuilder
from production_control_app.domain.errors import ProductionRunNotFound
from production_control_app.domain.ports.mes_monitoring_read_repository import (
    MesMonitoringReadRepositoryPort,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.mes_performance import (
    MesPerformanceCalculator,
)

# Bloco de Performance no monitoramento live — sem idealProductionSeconds
# (reservado ao detalhamento do run) para manter o payload enxuto.
_LIVE_PERFORMANCE_FIELDS = (
    "idealCycleSeconds", "producedPieces", "producingSeconds",
    "performancePercent", "actualAverageCycleSeconds",
    "actualThroughputPerHour", "expectedThroughputPerHour", "dataQuality",
)


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


class MesIntegrationReadService:
    def __init__(
        self,
        *,
        repository: MesMonitoringReadRepositoryPort,
        branch_access: BranchAccessService,
        timeline_builder: MesTimelineBuilder | None = None,
        calculator: MesPerformanceCalculator | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._branch_access = branch_access
        self._timeline_builder = timeline_builder or MesTimelineBuilder()
        self._calculator = calculator or MesPerformanceCalculator()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get_live_work_centers(self, *, branch: str) -> dict[str, Any]:
        code = self._branch_access.assert_valid_branch(branch)
        reference_at = self._clock()
        rows = self._repository.list_live_work_centers(branch=code)
        # Anti-N+1: uma query batch traz os state events de todos os runs;
        # o mesmo reference_at serve a timeline e Performance de todos.
        facts_by_run: dict[str, list[dict[str, Any]]] = {}
        run_ids = [row["run_id"] for row in rows]
        if run_ids:
            for fact in self._repository.list_timeline_facts_for_runs(run_ids):
                facts_by_run.setdefault(str(fact["run_id"]), []).append(fact)
        items = [
            self._live_item(row, self._live_performance(row, facts_by_run, reference_at))
            for row in rows
        ]
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
            events.append({**row, "downtime": self._downtime_view(row)})
        return self._timeline_builder.build(run=run, events=events, reference_at=self._clock())

    def get_work_center_timeline(
        self,
        *,
        branch: str,
        work_center: str,
        period_from: datetime,
        period_to: datetime | None = None,
    ) -> dict[str, Any]:
        code = self._branch_access.assert_valid_branch(branch)
        center = (work_center or "").strip()
        if not center or len(center) > 40:
            raise ValueError("Centro de trabalho inválido.")
        for name, value in (("from", period_from), ("to", period_to)):
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} deve incluir timezone.")
        reference_at = self._clock()
        effective_to = period_to or reference_at
        if period_from >= effective_to:
            raise ValueError("O início do período deve ser anterior ao fim.")
        rows = self._repository.list_work_center_timeline_facts(
            branch=code,
            work_center=center,
            period_from=period_from,
            period_to=effective_to,
        )
        return {
            "branch": code,
            "workCenter": center,
            "from": period_from.isoformat(),
            "to": effective_to.isoformat(),
            "referenceAt": reference_at.isoformat(),
            "items": [self._work_center_timeline_item(row) for row in rows],
        }

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

    def _live_performance(
        self,
        row: dict[str, Any],
        facts_by_run: dict[str, list[dict[str, Any]]],
        reference_at: datetime,
    ) -> dict[str, Any]:
        """Performance derivada do run — mesma semântica do motor da 2.4."""
        run = {
            "id": row["run_id"],
            "branch": row["branch"],
            "work_center": row["work_center"],
            "status": row.get("run_status"),
            "started_at": row.get("run_started_at"),
            "ended_at": row.get("run_ended_at"),
        }
        timeline = self._timeline_builder.build(
            run=run,
            events=facts_by_run.get(str(row["run_id"]), []),
            reference_at=reference_at,
        )
        metrics = self._calculator.calculate(
            ideal_cycle_seconds=row.get("ideal_cycle_seconds_snapshot"),
            produced_pieces=row.get("pieces_total"),
            producing_seconds=timeline["summary"]["producingSeconds"],
            standard_time_data_quality=row.get(
                "standard_time_data_quality_snapshot"
            ),
        )
        performance = {
            field: metrics.get(field) for field in _LIVE_PERFORMANCE_FIELDS
        }
        performance["standardTimeSource"] = row.get("standard_time_source")
        performance["standardTimeDataQuality"] = row.get(
            "standard_time_data_quality_snapshot"
        )
        return performance

    @staticmethod
    def _live_item(row: dict[str, Any], performance: dict[str, Any]) -> dict[str, Any]:
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
            "performance": performance,
        }

    @staticmethod
    def _downtime_view(row: dict[str, Any]) -> dict[str, Any] | None:
        if not row.get("downtime_id"):
            return None
        return {
            "id": row["downtime_id"],
            "reasonCode": row.get("reason_code"),
            "reasonLabel": row.get("reason_label"),
            "category": row.get("category"),
            "note": row.get("note"),
            "confirmed": bool(row.get("confirmed")),
            "source": row.get("downtime_source"),
        }

    @classmethod
    def _work_center_timeline_item(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "stateEventId": row["id"],
            "runId": row.get("run_id"),
            "productionOrder": row.get("production_order"),
            "operationCode": row.get("operation_code"),
            "state": row.get("state"),
            "startedAt": _iso(row.get("started_at")),
            "endedAt": _iso(row.get("ended_at")),
            "source": row.get("source"),
            "downtime": cls._downtime_view(row),
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
