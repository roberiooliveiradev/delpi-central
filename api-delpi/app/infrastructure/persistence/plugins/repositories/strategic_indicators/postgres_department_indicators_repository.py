from __future__ import annotations

from app.domain.ports.strategic_indicators.department_indicators_repository_port import (
    StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsDepartmentIndicatorsRepository(
    PluginBaseRepository,
    StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
):
    def list_department_indicators(
        self,
        *,
        department_id: str,
    ) -> list[dict]:
        query = """
            SELECT
                indicator_id,
                department_id,
                indicator_name,
                weight_pct,
                scope_type,
                strategic_description,
                source_key,
                is_active,
                display_order,
                created_at,
                updated_at,
                created_by_email,
                updated_by_email
            FROM strategic_indicators.department_indicators
            WHERE department_id = %s
            ORDER BY display_order ASC, indicator_name ASC
        """
        return self.fetch_all(query, (department_id,))

    def create_department_indicator(
        self,
        *,
        department_id: str,
        indicator_id: str,
        indicator_name: str,
        weight_pct: float,
        scope_type: str,
        strategic_description: str,
        source_key: str | None,
        display_order: int,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        query = """
            INSERT INTO strategic_indicators.department_indicators (
                indicator_id,
                department_id,
                indicator_name,
                weight_pct,
                scope_type,
                strategic_description,
                source_key,
                is_active,
                display_order,
                created_by_user_id,
                created_by_email,
                updated_by_user_id,
                updated_by_email
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s)
            RETURNING *
        """
        return self.execute_returning_one(
            query,
            (
                indicator_id,
                department_id,
                indicator_name,
                weight_pct,
                scope_type,
                strategic_description,
                source_key,
                display_order,
                actor_user_id,
                actor_email,
                actor_user_id,
                actor_email,
            ),
        )

    def update_department_indicator(
        self,
        *,
        indicator_id: str,
        indicator_name: str,
        weight_pct: float,
        scope_type: str,
        strategic_description: str,
        source_key: str | None,
        is_active: bool,
        display_order: int,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        query = """
            UPDATE strategic_indicators.department_indicators
            SET
                indicator_name = %s,
                weight_pct = %s,
                scope_type = %s,
                strategic_description = %s,
                source_key = %s,
                is_active = %s,
                display_order = %s,
                updated_by_user_id = %s,
                updated_by_email = %s,
                updated_at = NOW()
            WHERE indicator_id = %s
            RETURNING *
        """
        return self.execute_returning_one(
            query,
            (
                indicator_name,
                weight_pct,
                scope_type,
                strategic_description,
                source_key,
                is_active,
                display_order,
                actor_user_id,
                actor_email,
                indicator_id,
            ),
        )

    def deactivate_department_indicator(
        self,
        *,
        indicator_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        query = """
            UPDATE strategic_indicators.department_indicators
            SET
                is_active = FALSE,
                updated_by_user_id = %s,
                updated_by_email = %s,
                updated_at = NOW()
            WHERE indicator_id = %s
            RETURNING *
        """
        return self.execute_returning_one(
            query,
            (
                actor_user_id,
                actor_email,
                indicator_id,
            ),
        )

    def delete_department_indicator(
        self,
        *,
        indicator_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        before = self.fetch_one(
            """
            SELECT *
            FROM strategic_indicators.department_indicators
            WHERE indicator_id = %s
            """,
            (indicator_id,),
        )
        if not before:
            raise ValueError("Indicador estrutural não encontrado.")

        goals_count = self.fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM strategic_indicators.indicator_goals
            WHERE indicator_id = %s
            """,
            (indicator_id,),
        )
        if int((goals_count or {}).get("total") or 0) > 0:
            raise ValueError(
                "Não é possível excluir o indicador porque ainda existem metas vinculadas."
            )

        self.execute(
            """
            DELETE FROM strategic_indicators.department_indicators
            WHERE indicator_id = %s
            """,
            (indicator_id,),
        )
        return {
            "message": "Indicador estrutural excluído com sucesso.",
            "indicator_id": indicator_id,
        }

    def list_indicator_ids_by_departments(
        self,
        *,
        department_ids: list[str] | None = None,
    ) -> list[str]:
        query = """
            SELECT indicator_id
            FROM strategic_indicators.department_indicators
            WHERE is_active = TRUE
        """
        params: list = []

        if department_ids:
            placeholders = ", ".join(["%s"] * len(department_ids))
            query += f" AND department_id IN ({placeholders})"
            params.extend(department_ids)

        query += " ORDER BY department_id ASC, display_order ASC, indicator_name ASC"

        rows = self.fetch_all(query, tuple(params))
        return [row["indicator_id"] for row in rows]