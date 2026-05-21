from __future__ import annotations

import json

from si_app.shared.json_encoding import to_json_safe

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from si_app.application.services.strategic_indicators.calculation_snapshots_serialization import (
    CALCULATION_SNAPSHOT_SCHEMA_VERSION,
    serialize_calculation_inputs,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsCatalogSnapshot,
)
from si_app.application.use_cases.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.domain.ports.strategic_indicators.calculation_snapshots_repository_port import (
    StrategicIndicatorsCalculationSnapshotsRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsCalculationSnapshotsRepository(
    PluginBaseRepository,
    StrategicIndicatorsCalculationSnapshotsRepositoryPort,
):
    def upsert_calculation_snapshot(
        self,
        *,
        period: ResolvedPeriod,
        catalog: StrategicIndicatorsCatalogSnapshot,
        measurements: list[StrategicIndicatorMeasuredValue],
        measurement_errors: list[dict],
        scope_branch: str,
        scope_department_id: str,
        catalog_inputs_hash: str | None = None,
    ) -> None:
        payload = serialize_calculation_inputs(
            period=period,
            catalog=catalog,
            measurements=measurements,
            measurement_errors=measurement_errors,
        )

        query = """
            INSERT INTO strategic_indicators.calculation_snapshots (
                competence,
                start_date,
                end_date,
                scope_branch,
                scope_department_id,
                schema_version,
                departments_catalog,
                indicators_catalog,
                goals_by_department,
                measurements,
                measurement_errors,
                catalog_inputs_hash,
                computed_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb,
                %s,
                NOW()
            )
            ON CONFLICT (competence, scope_branch, scope_department_id)
            DO UPDATE SET
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                schema_version = EXCLUDED.schema_version,
                departments_catalog = EXCLUDED.departments_catalog,
                indicators_catalog = EXCLUDED.indicators_catalog,
                goals_by_department = EXCLUDED.goals_by_department,
                measurements = EXCLUDED.measurements,
                measurement_errors = EXCLUDED.measurement_errors,
                catalog_inputs_hash = EXCLUDED.catalog_inputs_hash,
                computed_at = NOW()
        """

        self.execute(
            query,
            (
                period.competence,
                period.start_date,
                period.end_date,
                scope_branch,
                scope_department_id,
                CALCULATION_SNAPSHOT_SCHEMA_VERSION,
                json.dumps(
                    to_json_safe(payload["departments_catalog"]),
                    ensure_ascii=False,
                ),
                json.dumps(
                    to_json_safe(payload["indicators_catalog"]),
                    ensure_ascii=False,
                ),
                json.dumps(
                    to_json_safe(payload["goals_by_department"]),
                    ensure_ascii=False,
                ),
                json.dumps(to_json_safe(payload["measurements"]), ensure_ascii=False),
                json.dumps(
                    to_json_safe(payload["measurement_errors"]),
                    ensure_ascii=False,
                ),
                catalog_inputs_hash,
            ),
        )

    def delete_all(self) -> None:
        self.execute("DELETE FROM strategic_indicators.calculation_snapshots")
