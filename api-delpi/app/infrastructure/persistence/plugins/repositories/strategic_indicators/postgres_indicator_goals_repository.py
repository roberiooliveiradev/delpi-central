from __future__ import annotations

from app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsIndicatorGoalsRepository(
    PluginBaseRepository,
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
):
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
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
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
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM strategic_indicators.module_settings ms,
                         jsonb_array_elements(ms.payload_json->'items') AS dep,
                         jsonb_array_elements(dep->'indicators') AS ind
                    WHERE ms.setting_key = 'indicators.catalog'
                      AND ms.is_active = TRUE
                      AND dep->>'department_id' = %s
                      AND ind->>'id' = ig.indicator_id
                )
            """
            params.append(department_id)

        query += """
            ORDER BY ig.indicator_id, ig.goal_year DESC, ig.version DESC
        """

        return self.fetch_all(query, tuple(params))

    def list_indicator_goal_history(
        self,
        *,
        indicator_id: str,
        goal_year: int | None = None,
    ) -> list[dict]:
        query = """
            SELECT
                id,
                indicator_id,
                goal_year,
                goal_label,
                goal_value,
                goal_periodicity,
                version,
                is_active,
                valid_from,
                valid_to,
                notes,
                created_by_user_id,
                created_by_email,
                updated_by_user_id,
                updated_by_email,
                created_at,
                updated_at
            FROM strategic_indicators.indicator_goals
            WHERE indicator_id = %s
        """
        params: list = [indicator_id]

        if goal_year is not None:
            query += " AND goal_year = %s"
            params.append(goal_year)

        query += " ORDER BY goal_year DESC, version DESC, created_at DESC"
        return self.fetch_all(query, tuple(params))

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
        return self.fetch_one(query, (indicator_id, year))

    def create_indicator_goal(
        self,
        *,
        indicator_id: str,
        goal_year: int,
        goal_label: str,
        goal_value: float,
        goal_periodicity: str,
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

        insert_query = """
            INSERT INTO strategic_indicators.indicator_goals (
                indicator_id,
                goal_year,
                goal_label,
                goal_value,
                goal_periodicity,
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
            VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        return self.execute_returning_one(
            insert_query,
            (
                indicator_id,
                goal_year,
                goal_label,
                goal_value,
                goal_periodicity,
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

    def update_indicator_goal(
        self,
        *,
        goal_id: str,
        goal_label: str,
        goal_value: float,
        goal_periodicity: str,
        valid_from: str | None,
        valid_to: str | None,
        notes: str | None,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        query = """
            UPDATE strategic_indicators.indicator_goals
            SET
                goal_label = %s,
                goal_value = %s,
                goal_periodicity = %s,
                valid_from = %s,
                valid_to = %s,
                notes = %s,
                updated_by_user_id = %s,
                updated_by_email = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """
        return self.execute_returning_one(
            query,
            (
                goal_label,
                goal_value,
                goal_periodicity,
                valid_from,
                valid_to,
                notes,
                actor_user_id,
                actor_email,
                goal_id,
            ),
        )

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
        return self.execute_returning_one(
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