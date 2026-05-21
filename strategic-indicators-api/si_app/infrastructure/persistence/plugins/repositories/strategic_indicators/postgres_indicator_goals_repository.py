from __future__ import annotations

from datetime import date

from si_app.application.use_cases.strategic_indicators.period_resolution import (
    competence_reference_date,
)
from si_app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsIndicatorGoalsRepository(
    PluginBaseRepository,
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
):
    @staticmethod
    def _append_goal_validity_filter(
        query: str,
        *,
        reference_date: date,
        params: list,
    ) -> str:
        params.extend([reference_date, reference_date])
        return (
            query
            + """
              AND (ig.valid_from IS NULL OR ig.valid_from <= %s::date)
              AND (ig.valid_to IS NULL OR ig.valid_to >= %s::date)
            """
        )

    def list_indicator_goals(
        self,
        *,
        indicator_id: str | None = None,
        goal_year: int | None = None,
        department_id: str | None = None,
        active_only: bool = False,
    ) -> list[dict]:
        query = """
            SELECT
                ig.id,
                ig.indicator_id,
                di.indicator_name,
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
                ig.goal_mode,
                ig.version,
                ig.is_active,
                ig.valid_from,
                ig.valid_to,
                ig.notes,
                ig.created_by_user_id,
                ig.created_by_email,
                ig.updated_by_user_id,
                ig.updated_by_email,
                ig.created_at,
                ig.updated_at
            FROM strategic_indicators.indicator_goals ig
            INNER JOIN strategic_indicators.department_indicators di
                ON di.indicator_id = ig.indicator_id
            INNER JOIN strategic_indicators.departments d
                ON d.department_id = di.department_id
            WHERE 1 = 1
        """
        params: list = []

        if indicator_id:
            query += " AND ig.indicator_id = %s"
            params.append(indicator_id)

        if goal_year is not None:
            query += " AND ig.goal_year = %s"
            params.append(goal_year)

        if active_only:
            query += " AND ig.is_active = TRUE"

        if department_id:
            query += " AND di.department_id = %s"
            params.append(department_id)

        query += """
            ORDER BY
                d.display_order ASC,
                di.display_order ASC,
                ig.goal_year DESC,
                ig.version DESC
        """

        rows = self.fetch_all(query, tuple(params))
        return self._attach_monthly_targets(rows)

    def list_indicator_goal_history(
        self,
        *,
        indicator_id: str,
        goal_year: int | None = None,
    ) -> list[dict]:
        query = """
            SELECT
                ig.id,
                ig.indicator_id,
                di.indicator_name,
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
                ig.goal_mode,
                ig.version,
                ig.is_active,
                ig.valid_from,
                ig.valid_to,
                ig.notes,
                ig.created_by_user_id,
                ig.created_by_email,
                ig.updated_by_user_id,
                ig.updated_by_email,
                ig.created_at,
                ig.updated_at
            FROM strategic_indicators.indicator_goals ig
            INNER JOIN strategic_indicators.department_indicators di
                ON di.indicator_id = ig.indicator_id
            WHERE ig.indicator_id = %s
        """
        params: list = [indicator_id]

        if goal_year is not None:
            query += " AND ig.goal_year = %s"
            params.append(goal_year)

        query += " ORDER BY ig.goal_year DESC, ig.version DESC, ig.created_at DESC"

        rows = self.fetch_all(query, tuple(params))
        return self._attach_monthly_targets(rows)

    def get_resolved_goal(
        self,
        *,
        indicator_id: str,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict | None:
        year = self._resolve_goal_year(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

        query = """
            SELECT
                id,
                indicator_id,
                goal_year,
                goal_label,
                goal_value,
                goal_periodicity,
                goal_mode,
                version,
                is_active,
                valid_from,
                valid_to,
                notes,
                created_at,
                updated_at
            FROM strategic_indicators.indicator_goals
            WHERE indicator_id = %s
              AND goal_year = %s
              AND is_active = TRUE
            ORDER BY version DESC, updated_at DESC
            LIMIT 1
        """
        row = self.fetch_one(query, (indicator_id, year))
        if not row:
            return None

        row["monthly_targets"] = self.list_monthly_targets(
            indicator_goal_id=row["id"]
        )
        return row

    def list_resolved_goals_map(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, dict]:
        year = self._resolve_goal_year(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

        query = """
            SELECT DISTINCT ON (ig.indicator_id)
                ig.id,
                ig.indicator_id,
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
                ig.goal_mode,
                ig.version,
                ig.is_active,
                ig.valid_from,
                ig.valid_to,
                ig.notes,
                ig.created_at,
                ig.updated_at
            FROM strategic_indicators.indicator_goals ig
            INNER JOIN strategic_indicators.department_indicators di
                ON di.indicator_id = ig.indicator_id
            INNER JOIN strategic_indicators.departments d
                ON d.department_id = di.department_id
            WHERE ig.goal_year = %s
              AND ig.is_active = TRUE
              AND di.is_active = TRUE
              AND d.is_active = TRUE
        """
        params: list = [year]

        if department_id:
            query += " AND di.department_id = %s"
            params.append(department_id)

        reference_date = competence_reference_date(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
        query = self._append_goal_validity_filter(
            query,
            reference_date=reference_date,
            params=params,
        )

        query += """
            ORDER BY
                ig.indicator_id,
                ig.version DESC,
                ig.updated_at DESC
        """

        rows = self.fetch_all(query, tuple(params))
        if not rows:
            return {}

        goal_ids = [row["id"] for row in rows]
        monthly_by_goal = self._list_monthly_targets_batch(goal_ids)

        result: dict[str, dict] = {}
        for row in rows:
            item = dict(row)
            item["monthly_targets"] = monthly_by_goal.get(row["id"], [])
            result[row["indicator_id"]] = item
        return result

    def list_latest_active_goals_map(
        self,
        *,
        indicator_ids: list[str],
        department_id: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, dict]:
        normalized_ids = [
            str(indicator_id).strip()
            for indicator_id in indicator_ids
            if indicator_id is not None and str(indicator_id).strip()
        ]
        if not normalized_ids:
            return {}

        placeholders = ", ".join("%s" for _ in normalized_ids)
        query = f"""
            SELECT DISTINCT ON (ig.indicator_id)
                ig.id,
                ig.indicator_id,
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
                ig.goal_mode,
                ig.version,
                ig.is_active,
                ig.valid_from,
                ig.valid_to,
                ig.notes,
                ig.created_at,
                ig.updated_at
            FROM strategic_indicators.indicator_goals ig
            INNER JOIN strategic_indicators.department_indicators di
                ON di.indicator_id = ig.indicator_id
            INNER JOIN strategic_indicators.departments d
                ON d.department_id = di.department_id
            WHERE ig.indicator_id IN ({placeholders})
              AND ig.is_active = TRUE
              AND di.is_active = TRUE
              AND d.is_active = TRUE
        """
        params: list = list(normalized_ids)

        if department_id:
            query += " AND di.department_id = %s"
            params.append(department_id)

        reference_date = competence_reference_date(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
        query = self._append_goal_validity_filter(
            query,
            reference_date=reference_date,
            params=params,
        )

        query += """
            ORDER BY
                ig.indicator_id,
                ig.goal_year DESC,
                ig.version DESC,
                ig.updated_at DESC
        """

        rows = self.fetch_all(query, tuple(params))
        if not rows:
            return {}

        goal_ids = [row["id"] for row in rows]
        monthly_by_goal = self._list_monthly_targets_batch(goal_ids)

        result: dict[str, dict] = {}
        for row in rows:
            item = dict(row)
            item["monthly_targets"] = monthly_by_goal.get(row["id"], [])
            result[row["indicator_id"]] = item
        return result

    def _attach_monthly_targets(self, rows: list[dict]) -> list[dict]:
        if not rows:
            return rows

        goal_ids = [row["id"] for row in rows]
        monthly_by_goal = self._list_monthly_targets_batch(goal_ids)

        for row in rows:
            row["monthly_targets"] = monthly_by_goal.get(row["id"], [])

        return rows

    def _list_monthly_targets_batch(
        self,
        indicator_goal_ids: list,
    ) -> dict[str, list[dict]]:
        if not indicator_goal_ids:
            return {}

        placeholders = ", ".join("%s" for _ in indicator_goal_ids)
        rows = self.fetch_all(
            f"""
            SELECT
                indicator_goal_id,
                month_number,
                target_value
            FROM strategic_indicators.indicator_goal_monthly_targets
            WHERE indicator_goal_id IN ({placeholders})
            ORDER BY indicator_goal_id ASC, month_number ASC
            """,
            tuple(indicator_goal_ids),
        )

        grouped: dict[str, list[dict]] = {}
        for row in rows:
            goal_id = row["indicator_goal_id"]
            grouped.setdefault(goal_id, []).append(
                {
                    "month_number": row["month_number"],
                    "target_value": row["target_value"],
                }
            )
        return grouped

    def list_monthly_targets(
        self,
        *,
        indicator_goal_id: str,
    ) -> list[dict]:
        return self.fetch_all(
            """
            SELECT
                month_number,
                target_value
            FROM strategic_indicators.indicator_goal_monthly_targets
            WHERE indicator_goal_id = %s
            ORDER BY month_number ASC
            """,
            (indicator_goal_id,),
        )

    def replace_monthly_targets(
        self,
        *,
        indicator_goal_id: str,
        monthly_targets: list[dict],
    ) -> None:
        self.execute(
            """
            DELETE FROM strategic_indicators.indicator_goal_monthly_targets
            WHERE indicator_goal_id = %s
            """,
            (indicator_goal_id,),
        )

        for item in monthly_targets:
            self.execute(
                """
                INSERT INTO strategic_indicators.indicator_goal_monthly_targets (
                    indicator_goal_id,
                    month_number,
                    target_value
                )
                VALUES (%s, %s, %s)
                """,
                (
                    indicator_goal_id,
                    int(item["month_number"]),
                    float(item["target_value"]),
                ),
            )

    def create_indicator_goal(
        self,
        *,
        indicator_id: str,
        goal_year: int,
        goal_label: str,
        goal_value: float,
        goal_periodicity: str,
        goal_mode: str,
        monthly_targets: list[dict],
        valid_from: str | None,
        valid_to: str | None,
        notes: str | None,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        version_query = """
            SELECT COALESCE(MAX(version), 0) AS max_version
            FROM strategic_indicators.indicator_goals
            WHERE indicator_id = %s
              AND goal_year = %s
        """
        row = self.fetch_one(version_query, (indicator_id, goal_year))
        next_version = int((row or {}).get("max_version") or 0) + 1

        try:
            created = self.execute_returning_one(
                """
                INSERT INTO strategic_indicators.indicator_goals (
                    indicator_id,
                    goal_year,
                    goal_label,
                    goal_value,
                    goal_periodicity,
                    goal_mode,
                    version,
                    is_active,
                    valid_from,
                    valid_to,
                    notes,
                    created_by_user_id,
                    created_by_email,
                    updated_by_user_id,
                    updated_by_email
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    indicator_id,
                    goal_year,
                    goal_label,
                    goal_value,
                    goal_periodicity,
                    goal_mode,
                    next_version,
                    valid_from,
                    valid_to,
                    notes,
                    actor_user_id,
                    actor_email,
                    actor_user_id,
                    actor_email,
                ),
            )

            if goal_mode == "monthly_curve":
                self.replace_monthly_targets(
                    indicator_goal_id=created["id"],
                    monthly_targets=monthly_targets,
                )

            self.commit()
            created["monthly_targets"] = self.list_monthly_targets(
                indicator_goal_id=created["id"]
            )
            return created
        except Exception:
            self.rollback()
            raise

    def update_indicator_goal(
        self,
        *,
        goal_id: str,
        goal_label: str,
        goal_value: float,
        goal_periodicity: str,
        goal_mode: str,
        monthly_targets: list[dict],
        valid_from: str | None,
        valid_to: str | None,
        notes: str | None,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        try:
            updated = self.execute_returning_one(
                """
                UPDATE strategic_indicators.indicator_goals
                SET
                    goal_label = %s,
                    goal_value = %s,
                    goal_periodicity = %s,
                    goal_mode = %s,
                    valid_from = %s,
                    valid_to = %s,
                    notes = %s,
                    updated_by_user_id = %s,
                    updated_by_email = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (
                    goal_label,
                    goal_value,
                    goal_periodicity,
                    goal_mode,
                    valid_from,
                    valid_to,
                    notes,
                    actor_user_id,
                    actor_email,
                    goal_id,
                ),
            )

            if goal_mode == "monthly_curve":
                self.replace_monthly_targets(
                    indicator_goal_id=goal_id,
                    monthly_targets=monthly_targets,
                )
            else:
                self.execute(
                    """
                    DELETE FROM strategic_indicators.indicator_goal_monthly_targets
                    WHERE indicator_goal_id = %s
                    """,
                    (goal_id,),
                )

            self.commit()
            updated["monthly_targets"] = self.list_monthly_targets(
                indicator_goal_id=goal_id
            )
            return updated
        except Exception:
            self.rollback()
            raise

    def activate_indicator_goal(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        target = self.fetch_one(
            """
            SELECT id, indicator_id, goal_year
            FROM strategic_indicators.indicator_goals
            WHERE id = %s
            """,
            (goal_id,),
        )
        if not target:
            raise ValueError("Meta não encontrada.")

        try:
            self.execute(
                """
                UPDATE strategic_indicators.indicator_goals
                SET
                    is_active = FALSE,
                    updated_by_user_id = %s,
                    updated_by_email = %s,
                    updated_at = NOW()
                WHERE indicator_id = %s
                  AND goal_year = %s
                """,
                (
                    actor_user_id,
                    actor_email,
                    target["indicator_id"],
                    target["goal_year"],
                ),
            )

            row = self.execute_returning_one(
                """
                UPDATE strategic_indicators.indicator_goals
                SET
                    is_active = TRUE,
                    updated_by_user_id = %s,
                    updated_by_email = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (
                    actor_user_id,
                    actor_email,
                    goal_id,
                ),
            )
            self.commit()
            row["monthly_targets"] = self.list_monthly_targets(
                indicator_goal_id=goal_id
            )
            return row
        except Exception:
            self.rollback()
            raise

    def deactivate_indicator_goal(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        row = self.execute_returning_one(
            """
            UPDATE strategic_indicators.indicator_goals
            SET
                is_active = FALSE,
                updated_by_user_id = %s,
                updated_by_email = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING *
            """,
            (
                actor_user_id,
                actor_email,
                goal_id,
            ),
        )
        row["monthly_targets"] = self.list_monthly_targets(
            indicator_goal_id=goal_id
        )
        return row

    def _resolve_goal_year(
        self,
        *,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> int:
        if competence and len(competence) >= 4:
            return int(competence[:4])

        for value in (end_date, start_date):
            if value and len(value) >= 10:
                parts = value.split("-")
                if len(parts) == 3:
                    return int(parts[2])

        raise ValueError("Não foi possível resolver o ano da meta.")

    def bulk_create_indicator_goals(
        self,
        *,
        goal_year: int,
        items: list[dict],
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        created_items: list[dict] = []

        for item in items:
            created_items.append(
                self.create_indicator_goal(
                    indicator_id=item["indicator_id"],
                    goal_year=goal_year,
                    goal_label=item["goal_label"],
                    goal_value=float(item["goal_value"]),
                    goal_periodicity=item["goal_periodicity"],
                    goal_mode=item.get("goal_mode", "standard"),
                    monthly_targets=item.get("monthly_targets") or [],
                    valid_from=item.get("valid_from"),
                    valid_to=item.get("valid_to"),
                    notes=item.get("notes"),
                    actor_user_id=actor_user_id,
                    actor_email=actor_email,
                )
            )

        return {
            "message": "Metas analíticas criadas em lote com sucesso.",
            "items": created_items,
        }

    def duplicate_goals_year(
        self,
        *,
        source_year: int,
        target_year: int,
        indicator_ids: list[str] | None,
        overwrite_existing: bool,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        source_query = """
            SELECT
                id,
                indicator_id,
                goal_label,
                goal_value,
                goal_periodicity,
                goal_mode,
                valid_from,
                valid_to,
                notes
            FROM strategic_indicators.indicator_goals
            WHERE goal_year = %s
              AND is_active = TRUE
        """
        params: list = [source_year]

        if indicator_ids:
            placeholders = ", ".join(["%s"] * len(indicator_ids))
            source_query += f" AND indicator_id IN ({placeholders})"
            params.extend(indicator_ids)

        source_query += " ORDER BY indicator_id ASC"

        source_rows = self.fetch_all(source_query, tuple(params))
        created_items: list[dict] = []

        for row in source_rows:
            existing = self.fetch_one(
                """
                SELECT id
                FROM strategic_indicators.indicator_goals
                WHERE indicator_id = %s
                  AND goal_year = %s
                  AND is_active = TRUE
                LIMIT 1
                """,
                (row["indicator_id"], target_year),
            )

            if existing and not overwrite_existing:
                continue

            if existing and overwrite_existing:
                self.execute(
                    """
                    UPDATE strategic_indicators.indicator_goals
                    SET
                        is_active = FALSE,
                        updated_by_user_id = %s,
                        updated_by_email = %s,
                        updated_at = NOW()
                    WHERE indicator_id = %s
                      AND goal_year = %s
                    """,
                    (
                        actor_user_id,
                        actor_email,
                        row["indicator_id"],
                        target_year,
                    ),
                )

            version_row = self.fetch_one(
                """
                SELECT COALESCE(MAX(version), 0) AS max_version
                FROM strategic_indicators.indicator_goals
                WHERE indicator_id = %s
                  AND goal_year = %s
                """,
                (row["indicator_id"], target_year),
            )
            next_version = int((version_row or {}).get("max_version") or 0) + 1

            created = self.execute_returning_one(
                """
                INSERT INTO strategic_indicators.indicator_goals (
                    indicator_id,
                    goal_year,
                    goal_label,
                    goal_value,
                    goal_periodicity,
                    goal_mode,
                    version,
                    is_active,
                    valid_from,
                    valid_to,
                    notes,
                    copied_from_goal_id,
                    copied_from_year,
                    created_by_user_id,
                    created_by_email,
                    updated_by_user_id,
                    updated_by_email
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    row["indicator_id"],
                    target_year,
                    row["goal_label"],
                    row["goal_value"],
                    row["goal_periodicity"],
                    row.get("goal_mode", "standard"),
                    next_version,
                    row.get("valid_from"),
                    row.get("valid_to"),
                    row.get("notes"),
                    row["id"],
                    source_year,
                    actor_user_id,
                    actor_email,
                    actor_user_id,
                    actor_email,
                ),
            )

            if row.get("goal_mode") == "monthly_curve":
                monthly_targets = self.list_monthly_targets(
                    indicator_goal_id=row["id"]
                )
                self.replace_monthly_targets(
                    indicator_goal_id=created["id"],
                    monthly_targets=monthly_targets,
                )

            created["monthly_targets"] = self.list_monthly_targets(
                indicator_goal_id=created["id"]
            )
            created_items.append(created)

        return {
            "message": "Duplicação de metas concluída com sucesso.",
            "items": created_items,
        }

    def fill_missing_goals(
        self,
        *,
        goal_year: int,
        indicator_ids: list[str],
        copy_from_year: int | None,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        created_items: list[dict] = []

        for indicator_id in indicator_ids:
            existing = self.fetch_one(
                """
                SELECT id
                FROM strategic_indicators.indicator_goals
                WHERE indicator_id = %s
                  AND goal_year = %s
                  AND is_active = TRUE
                LIMIT 1
                """,
                (indicator_id, goal_year),
            )
            if existing:
                continue

            if copy_from_year is not None:
                source = self.fetch_one(
                    """
                    SELECT
                        id,
                        goal_label,
                        goal_value,
                        goal_periodicity,
                        goal_mode,
                        valid_from,
                        valid_to,
                        notes
                    FROM strategic_indicators.indicator_goals
                    WHERE indicator_id = %s
                      AND goal_year = %s
                      AND is_active = TRUE
                    ORDER BY version DESC, updated_at DESC
                    LIMIT 1
                    """,
                    (indicator_id, copy_from_year),
                )
                if source:
                    version_row = self.fetch_one(
                        """
                        SELECT COALESCE(MAX(version), 0) AS max_version
                        FROM strategic_indicators.indicator_goals
                        WHERE indicator_id = %s
                          AND goal_year = %s
                        """,
                        (indicator_id, goal_year),
                    )
                    next_version = int((version_row or {}).get("max_version") or 0) + 1

                    created = self.execute_returning_one(
                        """
                        INSERT INTO strategic_indicators.indicator_goals (
                            indicator_id,
                            goal_year,
                            goal_label,
                            goal_value,
                            goal_periodicity,
                            goal_mode,
                            version,
                            is_active,
                            valid_from,
                            valid_to,
                            notes,
                            copied_from_goal_id,
                            copied_from_year,
                            created_by_user_id,
                            created_by_email,
                            updated_by_user_id,
                            updated_by_email
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING *
                        """,
                        (
                            indicator_id,
                            goal_year,
                            source["goal_label"],
                            source["goal_value"],
                            source["goal_periodicity"],
                            source.get("goal_mode", "standard"),
                            next_version,
                            source.get("valid_from"),
                            source.get("valid_to"),
                            source.get("notes"),
                            source["id"],
                            copy_from_year,
                            actor_user_id,
                            actor_email,
                            actor_user_id,
                            actor_email,
                        ),
                    )

                    if source.get("goal_mode") == "monthly_curve":
                        monthly_targets = self.list_monthly_targets(
                            indicator_goal_id=source["id"]
                        )
                        self.replace_monthly_targets(
                            indicator_goal_id=created["id"],
                            monthly_targets=monthly_targets,
                        )

                    created["monthly_targets"] = self.list_monthly_targets(
                        indicator_goal_id=created["id"]
                    )
                    created_items.append(created)
                    continue

        return {
            "message": "Preenchimento de metas faltantes concluído com sucesso.",
            "items": created_items,
        }

    def list_goal_years_overview(self) -> list[dict]:
        query = """
            SELECT
                ig.goal_year,
                COUNT(*) AS total_versions,
                COUNT(*) FILTER (WHERE ig.is_active = TRUE) AS total_active_versions,
                COUNT(DISTINCT ig.indicator_id) FILTER (WHERE ig.is_active = TRUE) AS total_active_indicators
            FROM strategic_indicators.indicator_goals ig
            GROUP BY ig.goal_year
            ORDER BY ig.goal_year DESC
        """
        return self.fetch_all(query)