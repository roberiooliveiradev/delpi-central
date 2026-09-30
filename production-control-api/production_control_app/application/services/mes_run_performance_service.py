"""Performance MES do Production Run (Fase 2.4 — motor interno).

Deriva as métricas a partir exclusivamente de fatos já persistidos:
production_runs (snapshots + pieces_total canônico, líquido de
corrections) + work_center_state_events via MesTimelineBuilder.
Nenhuma consulta a TOTVS/api-delpi/Pulse, nenhuma escrita — leitura pura.

A exposição HTTP/S2S dessas métricas é decidida na Parte 2.5.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from production_control_app.application.services.mes_timeline_builder import (
    MesTimelineBuilder,
)
from production_control_app.domain.errors import ProductionRunNotFound
from production_control_app.domain.ports.mes_monitoring_read_repository import (
    MesMonitoringReadRepositoryPort,
)
from production_control_app.domain.services.mes_performance import (
    MesPerformanceCalculator,
)


class MesRunPerformanceService:
    """Orquestra run + timeline + calculator com um único reference_at."""

    def __init__(
        self,
        *,
        repository: MesMonitoringReadRepositoryPort,
        timeline_builder: MesTimelineBuilder | None = None,
        calculator: MesPerformanceCalculator | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._timeline_builder = timeline_builder or MesTimelineBuilder()
        self._calculator = calculator or MesPerformanceCalculator()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get_run_performance(self, run_id: str) -> dict[str, Any]:
        """Métricas derivadas do run. Somente leitura, sem efeito colateral."""
        run = self._repository.get_run(run_id)
        if run is None:
            raise ProductionRunNotFound("Produção não encontrada.")

        # Um único instante de referência para timeline + resultado; o builder
        # congela em run.ended_at quando o run já encerrou.
        reference_at = self._clock()
        events = self._repository.list_timeline_facts(run_id)
        timeline = self._timeline_builder.build(
            run=run, events=events, reference_at=reference_at
        )

        metrics = self._calculator.calculate(
            ideal_cycle_seconds=run.get("ideal_cycle_seconds_snapshot"),
            produced_pieces=run.get("pieces_total"),
            producing_seconds=timeline["summary"]["producingSeconds"],
            standard_time_data_quality=run.get(
                "standard_time_data_quality_snapshot"
            ),
        )
        return {
            "runId": run["id"],
            "branch": run.get("branch"),
            "workCenter": run.get("work_center"),
            "referenceAt": reference_at.isoformat(),
            "status": run.get("status"),
            "standardTimeSource": run.get("standard_time_source"),
            "standardTimeDataQuality": run.get(
                "standard_time_data_quality_snapshot"
            ),
            **metrics,
        }
