"""Processa agendas vencidas — Delpi Reports (claim atômico Fase 4)."""

from __future__ import annotations

import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class _ReportsRepo(Protocol):
    def claim_due_schedules(
        self, *, limit: int = 20, now: Any = None
    ) -> list[dict[str, Any]]: ...


class _RunUseCase(Protocol):
    def execute(
        self, *, definition_id: str, trigger: str = "manual"
    ) -> dict[str, Any]: ...


class ProcessDueReportSchedulesUseCase:
    def __init__(
        self,
        repository: _ReportsRepo,
        run_use_case: _RunUseCase,
    ) -> None:
        self._repository = repository
        self._run = run_use_case

    def execute(self, *, limit: int = 20) -> dict[str, Any]:
        claimed = self._repository.claim_due_schedules(limit=limit)
        logger.info(
            "report_schedule_claimed count=%s limit=%s",
            len(claimed),
            limit,
        )
        processed: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []

        for schedule in claimed:
            schedule_id = schedule["id"]
            definition_id = schedule["definitionId"]
            try:
                run = self._run.execute(
                    definition_id=definition_id,
                    trigger="schedule",
                )
                logger.info(
                    "reports_schedule_run_done scheduleId=%s definitionId=%s "
                    "runId=%s status=%s",
                    schedule_id,
                    definition_id,
                    run.get("id"),
                    run.get("status"),
                )
                processed.append(
                    {
                        "scheduleId": schedule_id,
                        "definitionId": definition_id,
                        "runId": run.get("id"),
                        "status": run.get("status"),
                        "nextRunAt": schedule.get("nextRunAt"),
                    }
                )
            except Exception as exc:
                logger.warning(
                    "reports_schedule_run_failed scheduleId=%s definitionId=%s "
                    "error=%s",
                    schedule_id,
                    definition_id,
                    str(exc)[:400],
                )
                errors.append(
                    {
                        "scheduleId": schedule_id,
                        "definitionId": definition_id,
                        "error": str(exc)[:400],
                    }
                )

        return {
            "dueCount": len(claimed),
            "processedCount": len(processed),
            "errorCount": len(errors),
            "processed": processed,
            "errors": errors,
        }
