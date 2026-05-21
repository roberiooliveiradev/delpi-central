from __future__ import annotations

import json

from si_app.application.services.strategic_indicators.period_scores_serialization import (
    deserialize_period_snapshot,
    serialize_period_snapshot,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.domain.ports.strategic_indicators.period_scores_repository_port import (
    StrategicIndicatorsPeriodScoresRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsPeriodScoresRepository(
    PluginBaseRepository,
    StrategicIndicatorsPeriodScoresRepositoryPort,
):
    def get_period_snapshot(
        self,
        *,
        competence: str,
        scope_branch: str,
        scope_department_id: str,
    ) -> StrategicIndicatorsPeriodSnapshot | None:
        row = self.fetch_one(
            """
            SELECT
                competence,
                start_date,
                end_date,
                igd,
                igd_exact,
                classification,
                calculated_departments,
                calculated_indicators,
                measurement_errors
            FROM strategic_indicators.period_scores
            WHERE competence = %s
              AND scope_branch = %s
              AND scope_department_id = %s
            """,
            (competence, scope_branch, scope_department_id),
        )
        if not row:
            return None
        return deserialize_period_snapshot(row)

    def list_period_snapshots(
        self,
        *,
        competences: list[str],
        scope_branch: str,
        scope_department_id: str,
    ) -> dict[str, StrategicIndicatorsPeriodSnapshot]:
        if not competences:
            return {}

        placeholders = ", ".join("%s" for _ in competences)
        rows = self.fetch_all(
            f"""
            SELECT
                competence,
                start_date,
                end_date,
                igd,
                igd_exact,
                classification,
                calculated_departments,
                calculated_indicators,
                measurement_errors
            FROM strategic_indicators.period_scores
            WHERE scope_branch = %s
              AND scope_department_id = %s
              AND competence IN ({placeholders})
            """,
            (scope_branch, scope_department_id, *competences),
        )

        result: dict[str, StrategicIndicatorsPeriodSnapshot] = {}
        for row in rows:
            competence = str(row.get("competence") or "").strip()
            if not competence:
                continue
            result[competence] = deserialize_period_snapshot(row)
        return result

    def upsert_period_snapshot(
        self,
        *,
        snapshot: StrategicIndicatorsPeriodSnapshot,
        scope_branch: str,
        scope_department_id: str,
    ) -> None:
        payload = serialize_period_snapshot(snapshot)

        query = """
            INSERT INTO strategic_indicators.period_scores (
                competence,
                start_date,
                end_date,
                scope_branch,
                scope_department_id,
                igd,
                igd_exact,
                classification,
                calculated_departments,
                calculated_indicators,
                measurement_errors,
                computed_at
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s::jsonb, %s::jsonb, %s::jsonb,
                NOW()
            )
            ON CONFLICT (competence, scope_branch, scope_department_id)
            DO UPDATE SET
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                igd = EXCLUDED.igd,
                igd_exact = EXCLUDED.igd_exact,
                classification = EXCLUDED.classification,
                calculated_departments = EXCLUDED.calculated_departments,
                calculated_indicators = EXCLUDED.calculated_indicators,
                measurement_errors = EXCLUDED.measurement_errors,
                computed_at = NOW()
        """

        self.execute(
            query,
            (
                snapshot.period.competence,
                snapshot.period.start_date,
                snapshot.period.end_date,
                scope_branch,
                scope_department_id,
                payload["igd"],
                payload["igd_exact"],
                payload["classification"],
                json.dumps(payload["calculated_departments"], ensure_ascii=False),
                json.dumps(payload["calculated_indicators"], ensure_ascii=False),
                json.dumps(payload["measurement_errors"], ensure_ascii=False),
            ),
        )

    def delete_all(self) -> None:
        self.execute("DELETE FROM strategic_indicators.period_scores")
