from __future__ import annotations

import json

from si_app.application.services.strategic_indicators.period_scores_serialization import (
    deserialize_period_snapshot,
    serialize_period_snapshot,
)
from si_app.application.services.strategic_indicators.period_snapshot_versions import (
    prune_period_score_version_numbers,
    resolve_period_scores_serve,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    PeriodScoresCacheEntry,
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.domain.ports.strategic_indicators.period_scores_repository_port import (
    StrategicIndicatorsPeriodScoresRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_SELECT_COLUMNS = """
    competence,
    start_date,
    end_date,
    igd,
    igd_exact,
    classification,
    calculated_departments,
    calculated_indicators,
    measurement_errors,
    catalog_inputs_hash,
    version_number,
    is_clean
"""


class PostgresStrategicIndicatorsPeriodScoresRepository(
    PluginBaseRepository,
    StrategicIndicatorsPeriodScoresRepositoryPort,
):
    def _row_to_entry(self, row: dict) -> PeriodScoresCacheEntry:
        return PeriodScoresCacheEntry(
            snapshot=deserialize_period_snapshot(row),
            catalog_inputs_hash=row.get("catalog_inputs_hash"),
            version_number=int(row.get("version_number") or 1),
            is_clean=bool(row.get("is_clean", True)),
        )

    def list_period_snapshot_versions(
        self,
        *,
        competence: str,
        scope_branch: str,
        scope_department_id: str,
    ) -> list[PeriodScoresCacheEntry]:
        rows = self.fetch_all(
            f"""
            SELECT {_SELECT_COLUMNS}
            FROM strategic_indicators.period_scores
            WHERE competence = %s
              AND scope_branch = %s
              AND scope_department_id = %s
            ORDER BY version_number ASC
            """,
            (competence, scope_branch, scope_department_id),
        )
        return [self._row_to_entry(row) for row in rows]

    def get_period_snapshot(
        self,
        *,
        competence: str,
        scope_branch: str,
        scope_department_id: str,
    ) -> PeriodScoresCacheEntry | None:
        return resolve_period_scores_serve(
            self.list_period_snapshot_versions(
                competence=competence,
                scope_branch=scope_branch,
                scope_department_id=scope_department_id,
            )
        )

    def list_period_snapshots(
        self,
        *,
        competences: list[str],
        scope_branch: str,
        scope_department_id: str,
    ) -> dict[str, PeriodScoresCacheEntry]:
        if not competences:
            return {}

        placeholders = ", ".join("%s" for _ in competences)
        rows = self.fetch_all(
            f"""
            SELECT {_SELECT_COLUMNS}
            FROM strategic_indicators.period_scores
            WHERE scope_branch = %s
              AND scope_department_id = %s
              AND competence IN ({placeholders})
            ORDER BY competence ASC, version_number ASC
            """,
            (scope_branch, scope_department_id, *competences),
        )

        grouped: dict[str, list[PeriodScoresCacheEntry]] = {}
        for row in rows:
            competence = str(row.get("competence") or "").strip()
            if not competence:
                continue
            grouped.setdefault(competence, []).append(self._row_to_entry(row))

        result: dict[str, PeriodScoresCacheEntry] = {}
        for competence, entries in grouped.items():
            resolved = resolve_period_scores_serve(entries)
            if resolved is not None:
                result[competence] = resolved
        return result

    def upsert_period_snapshot(
        self,
        *,
        snapshot: StrategicIndicatorsPeriodSnapshot,
        scope_branch: str,
        scope_department_id: str,
        catalog_inputs_hash: str | None = None,
        is_clean: bool = True,
    ) -> None:
        payload = serialize_period_snapshot(snapshot)
        competence = snapshot.period.competence

        max_row = self.fetch_one(
            """
            SELECT COALESCE(MAX(version_number), 0) AS max_version
            FROM strategic_indicators.period_scores
            WHERE competence = %s
              AND scope_branch = %s
              AND scope_department_id = %s
            """,
            (competence, scope_branch, scope_department_id),
        )
        next_version = int((max_row or {}).get("max_version") or 0) + 1

        self.execute(
            """
            INSERT INTO strategic_indicators.period_scores (
                competence,
                start_date,
                end_date,
                scope_branch,
                scope_department_id,
                version_number,
                is_clean,
                igd,
                igd_exact,
                classification,
                calculated_departments,
                calculated_indicators,
                measurement_errors,
                catalog_inputs_hash,
                computed_at
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s::jsonb, %s::jsonb, %s::jsonb,
                %s,
                NOW()
            )
            """,
            (
                competence,
                snapshot.period.start_date,
                snapshot.period.end_date,
                scope_branch,
                scope_department_id,
                next_version,
                is_clean,
                payload["igd"],
                payload["igd_exact"],
                payload["classification"],
                json.dumps(payload["calculated_departments"], ensure_ascii=False),
                json.dumps(payload["calculated_indicators"], ensure_ascii=False),
                json.dumps(payload["measurement_errors"], ensure_ascii=False),
                catalog_inputs_hash,
            ),
        )

        self._prune_period_score_versions(
            competence=competence,
            scope_branch=scope_branch,
            scope_department_id=scope_department_id,
        )

    def _prune_period_score_versions(
        self,
        *,
        competence: str,
        scope_branch: str,
        scope_department_id: str,
    ) -> None:
        rows = self.fetch_all(
            """
            SELECT version_number
            FROM strategic_indicators.period_scores
            WHERE competence = %s
              AND scope_branch = %s
              AND scope_department_id = %s
            ORDER BY version_number ASC
            """,
            (competence, scope_branch, scope_department_id),
        )
        version_numbers = [int(row["version_number"]) for row in rows]
        keep = set(prune_period_score_version_numbers(version_numbers))
        if len(keep) >= len(version_numbers):
            return

        placeholders = ", ".join("%s" for _ in keep)
        self.execute(
            f"""
            DELETE FROM strategic_indicators.period_scores
            WHERE competence = %s
              AND scope_branch = %s
              AND scope_department_id = %s
              AND version_number NOT IN ({placeholders})
            """,
            (competence, scope_branch, scope_department_id, *sorted(keep)),
        )

    def delete_all(self) -> None:
        self.execute("DELETE FROM strategic_indicators.period_scores")
