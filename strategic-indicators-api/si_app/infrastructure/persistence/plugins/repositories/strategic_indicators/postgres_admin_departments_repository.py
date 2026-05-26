from __future__ import annotations

from si_app.domain.ports.strategic_indicators.admin_departments_repository_port import (
    StrategicIndicatorsAdminDepartmentsRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.catalog_admin_cascade import (
    delete_indicator_goals_cascade,
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
                None,
                actor_user_id,
                None,
            ),
        )

    def update_department(
        self,
        *,
        department_id: str,
        new_department_id: str | None,
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
    ) -> dict:
        current_id = department_id.strip()
        target_id = (new_department_id or current_id).strip()

        if not target_id:
            raise ValueError("department_id é obrigatório.")

        before = self.fetch_one(
            """
            SELECT *
            FROM strategic_indicators.departments
            WHERE department_id = %s
            """,
            (current_id,),
        )
        if not before:
            raise ValueError("Departamento não encontrado.")

        if target_id != current_id:
            conflict = self.fetch_one(
                """
                SELECT department_id
                FROM strategic_indicators.departments
                WHERE department_id = %s
                """,
                (target_id,),
            )
            if conflict:
                raise ValueError(
                    f"Já existe um departamento com o id '{target_id}'."
                )

            try:
                self.execute(
                    """
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        target_id,
                        department_name,
                        short_name,
                        strategic_summary,
                        headline_goal,
                        supporting_focus,
                        weight_pct,
                        aggregation_mode,
                        is_active,
                        display_order,
                        before.get("created_by_user_id"),
                        before.get("created_by_email"),
                        actor_user_id,
                        None,
                    ),
                )
                self.execute(
                    """
                    UPDATE strategic_indicators.department_indicators
                    SET department_id = %s, updated_at = NOW()
                    WHERE department_id = %s
                    """,
                    (target_id, current_id),
                )
                self.execute(
                    """
                    UPDATE strategic_indicators.period_scores
                    SET scope_department_id = %s
                    WHERE scope_department_id = %s
                    """,
                    (target_id, current_id),
                )
                self.execute(
                    """
                    DELETE FROM strategic_indicators.departments
                    WHERE department_id = %s
                    """,
                    (current_id,),
                )
                self.commit()
                current_id = target_id
            except Exception:
                self.rollback()
                raise

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
                None,
                current_id,
            ),
        )

    def activate_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
    ) -> dict:
        query = """
            UPDATE strategic_indicators.departments
            SET
                is_active = TRUE,
                updated_by_user_id = %s,
                updated_by_email = %s,
                updated_at = NOW()
            WHERE department_id = %s
            RETURNING *
        """
        row = self.execute_returning_one(
            query,
            (
                actor_user_id,
                None,
                department_id,
            ),
        )

        if not row:
            raise ValueError("Departamento não encontrado.")

        return row

    def deactivate_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
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
        row = self.execute_returning_one(
            query,
            (
                actor_user_id,
                None,
                department_id,
            ),
        )

        if not row:
            raise ValueError("Departamento não encontrado.")

        return row

    def delete_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
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

        indicator_rows = self.fetch_all(
            """
            SELECT indicator_id
            FROM strategic_indicators.department_indicators
            WHERE department_id = %s
            """,
            (department_id,),
        )

        try:
            for row in indicator_rows:
                delete_indicator_goals_cascade(
                    self,
                    indicator_id=row["indicator_id"],
                )
            self.execute(
                """
                DELETE FROM strategic_indicators.department_indicators
                WHERE department_id = %s
                """,
                (department_id,),
            )
            self.execute(
                """
                DELETE FROM strategic_indicators.departments
                WHERE department_id = %s
                """,
                (department_id,),
            )
            self.commit()
        except Exception:
            self.rollback()
            raise

        return {
            "message": "Departamento excluído com sucesso.",
            "department_id": department_id,
        }