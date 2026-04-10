from __future__ import annotations

from app.domain.ports.strategic_indicators.admin_departments_repository_port import (
    StrategicIndicatorsAdminDepartmentsRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsAdminDepartmentsRepository(
    PluginBaseRepository,
    StrategicIndicatorsAdminDepartmentsRepositoryPort,
):
    def list_departments(self) -> list[dict]:
        query = """
            SELECT
                department_id,
                department_name,
                short_name,
                strategic_summary,
                headline_goal,
                supporting_focus,
                weight_pct,
                aggregation_mode,
                is_active,
                display_order,
                created_at,
                updated_at,
                created_by_email,
                updated_by_email
            FROM strategic_indicators.departments
            ORDER BY display_order ASC, department_name ASC
        """
        return self.fetch_all(query)

    def create_department(
        self,
        *,
        department_id: str,
        department_name: str,
        short_name: str,
        strategic_summary: str,
        headline_goal: str,
        supporting_focus: str,
        weight_pct: float,
        aggregation_mode: str,
        display_order: int,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        query = """
            INSERT INTO strategic_indicators.departments (
                department_id,
                department_name,
                short_name,
                strategic_summary,
                headline_goal,
                supporting_focus,
                weight_pct,
                aggregation_mode,
                is_active,
                display_order,
                created_by_user_id,
                created_by_email,
                updated_by_user_id,
                updated_by_email
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s)
            RETURNING *
        """
        return self.execute_returning_one(
            query,
            (
                department_id,
                department_name,
                short_name,
                strategic_summary,
                headline_goal,
                supporting_focus,
                weight_pct,
                aggregation_mode,
                display_order,
                actor_user_id,
                actor_email,
                actor_user_id,
                actor_email,
            ),
        )

    def update_department(
        self,
        *,
        department_id: str,
        department_name: str,
        short_name: str,
        strategic_summary: str,
        headline_goal: str,
        supporting_focus: str,
        weight_pct: float,
        aggregation_mode: str,
        is_active: bool,
        display_order: int,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        query = """
            UPDATE strategic_indicators.departments
            SET
                department_name = %s,
                short_name = %s,
                strategic_summary = %s,
                headline_goal = %s,
                supporting_focus = %s,
                weight_pct = %s,
                aggregation_mode = %s,
                is_active = %s,
                display_order = %s,
                updated_by_user_id = %s,
                updated_by_email = %s,
                updated_at = NOW()
            WHERE department_id = %s
            RETURNING *
        """
        return self.execute_returning_one(
            query,
            (
                department_name,
                short_name,
                strategic_summary,
                headline_goal,
                supporting_focus,
                weight_pct,
                aggregation_mode,
                is_active,
                display_order,
                actor_user_id,
                actor_email,
                department_id,
            ),
        )

    def deactivate_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        query = """
            UPDATE strategic_indicators.departments
            SET
                is_active = FALSE,
                updated_by_user_id = %s,
                updated_by_email = %s,
                updated_at = NOW()
            WHERE department_id = %s
            RETURNING *
        """
        return self.execute_returning_one(
            query,
            (
                actor_user_id,
                actor_email,
                department_id,
            ),
        )

    def delete_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        before = self.fetch_one(
            """
            SELECT *
            FROM strategic_indicators.departments
            WHERE department_id = %s
            """,
            (department_id,),
        )
        if not before:
            raise ValueError("Departamento não encontrado.")

        indicators_count = self.fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM strategic_indicators.department_indicators
            WHERE department_id = %s
            """,
            (department_id,),
        )
        if int((indicators_count or {}).get("total") or 0) > 0:
            raise ValueError(
                "Não é possível excluir o departamento porque ainda existem indicadores vinculados."
            )

        self.execute(
            """
            DELETE FROM strategic_indicators.departments
            WHERE department_id = %s
            """,
            (department_id,),
        )
        return {
            "message": "Departamento excluído com sucesso.",
            "department_id": department_id,
        }