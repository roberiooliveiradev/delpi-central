from __future__ import annotations

from si_app.domain.ports.strategic_indicators.department_indicators_repository_port import (
    StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from si_app.shared.goal_scope import supports_branch_goals_for_scope_type
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.catalog_admin_cascade import (
    delete_indicator_goals_cascade,
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
                performance_direction,
                strategic_description,
                source_key,
                value_unit,
                value_prefix,
                value_suffix,
                value_decimals,
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
        performance_direction: str,
        strategic_description: str,
        source_key: str | None,
        value_unit: str | None,
        value_prefix: str | None,
        value_suffix: str | None,
        value_decimals: int,
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
                performance_direction,
                strategic_description,
                source_key,
                value_unit,
                value_prefix,
                value_suffix,
                value_decimals,
                supports_branch_goals,
                is_active,
                display_order,
                created_by_user_id,
                created_by_email,
                updated_by_user_id,
                updated_by_email
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s,
                TRUE, %s, %s, %s, %s, %s
            )
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
                performance_direction,
                strategic_description,
                source_key,
                value_unit,
                value_prefix,
                value_suffix,
                value_decimals,
                supports_branch_goals_for_scope_type(scope_type),
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
        new_indicator_id: str | None,
        indicator_name: str,
        weight_pct: float,
        scope_type: str,
        performance_direction: str,
        strategic_description: str,
        source_key: str | None,
        value_unit: str | None,
        value_prefix: str | None,
        value_suffix: str | None,
        value_decimals: int,
        is_active: bool,
        display_order: int,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        current_id = indicator_id.strip()
        target_id = (new_indicator_id or current_id).strip()

        if not target_id:
            raise ValueError("indicator_id é obrigatório.")

        before = self.fetch_one(
            """
            SELECT *
            FROM strategic_indicators.department_indicators
            WHERE indicator_id = %s
            """,
            (current_id,),
        )
        if not before:
            raise ValueError("Indicador estrutural não encontrado.")

        if target_id != current_id:
            conflict = self.fetch_one(
                """
                SELECT indicator_id
                FROM strategic_indicators.department_indicators
                WHERE indicator_id = %s
                """,
                (target_id,),
            )
            if conflict:
                raise ValueError(
                    f"Já existe um indicador com o id '{target_id}'."
                )

            try:
                self.execute(
                    """
                    INSERT INTO strategic_indicators.department_indicators (
                        indicator_id,
                        department_id,
                        indicator_name,
                        weight_pct,
                        scope_type,
                        performance_direction,
                        strategic_description,
                        source_key,
                        value_unit,
                        value_prefix,
                        value_suffix,
                        value_decimals,
                        supports_branch_goals,
                        is_active,
                        display_order,
                        created_by_user_id,
                        created_by_email,
                        updated_by_user_id,
                        updated_by_email
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        target_id,
                        before["department_id"],
                        indicator_name,
                        weight_pct,
                        scope_type,
                        performance_direction,
                        strategic_description,
                        source_key,
                        value_unit,
                        value_prefix,
                        value_suffix,
                        value_decimals,
                        supports_branch_goals_for_scope_type(scope_type),
                        is_active,
                        display_order,
                        before.get("created_by_user_id"),
                        before.get("created_by_email"),
                        actor_user_id,
                        actor_email,
                    ),
                )
                self.execute(
                    """
                    UPDATE strategic_indicators.indicator_goals
                    SET indicator_id = %s, updated_at = NOW()
                    WHERE indicator_id = %s
                    """,
                    (target_id, current_id),
                )
                self.execute(
                    """
                    DELETE FROM strategic_indicators.department_indicators
                    WHERE indicator_id = %s
                    """,
                    (current_id,),
                )
                self.commit()
                current_id = target_id
            except Exception:
                self.rollback()
                raise

        query = """
            UPDATE strategic_indicators.department_indicators
            SET
                indicator_name = %s,
                weight_pct = %s,
                scope_type = %s,
                performance_direction = %s,
                strategic_description = %s,
                source_key = %s,
                value_unit = %s,
                value_prefix = %s,
                value_suffix = %s,
                value_decimals = %s,
                supports_branch_goals = %s,
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
                performance_direction,
                strategic_description,
                source_key,
                value_unit,
                value_prefix,
                value_suffix,
                value_decimals,
                supports_branch_goals_for_scope_type(scope_type),
                is_active,
                display_order,
                actor_user_id,
                actor_email,
                current_id,
            ),
        )

    def activate_department_indicator(
        self,
        *,
        indicator_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        query = """
            UPDATE strategic_indicators.department_indicators
            SET
                is_active = TRUE,
                updated_by_user_id = %s,
                updated_by_email = %s,
                updated_at = NOW()
            WHERE indicator_id = %s
            RETURNING *
        """
        row = self.execute_returning_one(
            query,
            (
                actor_user_id,
                actor_email,
                indicator_id,
            ),
        )

        if not row:
            raise ValueError("Indicador estrutural não encontrado.")

        return row

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
        row = self.execute_returning_one(
            query,
            (
                actor_user_id,
                actor_email,
                indicator_id,
            ),
        )

        if not row:
            raise ValueError("Indicador estrutural não encontrado.")

        return row

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

        try:
            delete_indicator_goals_cascade(self, indicator_id=indicator_id)
            self.execute(
                """
                DELETE FROM strategic_indicators.department_indicators
                WHERE indicator_id = %s
                """,
                (indicator_id,),
            )
            self.commit()
        except Exception:
            self.rollback()
            raise

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