from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from si_app.application.services.strategic_indicators.admin_write_conflict_error import (
    StrategicIndicatorsAdminConflictError,
)
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
from si_app.infrastructure.providers.database.plugins_postgres_connection import (
    plugins_connection,
)


class PostgresStrategicIndicatorsDepartmentIndicatorsRepository(
    PluginBaseRepository,
    StrategicIndicatorsDepartmentIndicatorsRepositoryPort,
):
    @contextmanager
    def _unit_of_work(self) -> Iterator[None]:
        """Bind nested execute/fetch calls to one pooled connection/transaction.

        Without an injected connection each ``execute``/``fetch_*`` acquires
        its own pool lease and auto-commits per statement, so multi-statement
        mutations (rename migrate-goals + delete) and audit inserts would not
        be atomic with the mutation. Injecting the leased connection disables
        per-statement auto-commit and this wrapper performs a single
        commit/rollback for the whole unit.
        """
        if self._injected_connection is not None:
            yield
            return
        with plugins_connection() as connection:
            self._injected_connection = connection
            try:
                yield
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                self._injected_connection = None

    def _insert_admin_audit_event(
        self,
        *,
        event_type: str,
        entity_key: str,
        payload_before: dict | None,
        payload_after_row: dict | None,
        actor_user_id: str | None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Persist the mutation into ``strategic_indicators.settings_audit``.

        Must be called inside ``_unit_of_work`` so the INSERT rides the same
        transaction as the mutation. Correlation metadata is embedded under
        ``_audit_meta`` inside ``payload_after`` because the audit schema
        carries no dedicated correlation column (same convention as goals).
        """
        from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_audit_repository import (
            PostgresStrategicIndicatorsSettingsAuditRepository,
        )

        payload_after = (
            {k: v for k, v in payload_after_row.items() if k != "row_xmin"}
            if payload_after_row is not None
            else None
        )
        meta: dict = {}
        if audit_origin:
            meta["write_origin"] = audit_origin
        if correlation_id:
            meta["correlation_id"] = correlation_id
        if meta and payload_after is not None:
            payload_after["_audit_meta"] = meta

        PostgresStrategicIndicatorsSettingsAuditRepository(
            self._connection
        ).insert_audit_event(
            entity_key=entity_key[:150],
            payload_before=payload_before,
            payload_after=payload_after,
            changed_by_user_id=actor_user_id,
            event_type=event_type,
        )

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
                branch_value_aggregation,
                is_active,
                display_order,
                created_at,
                updated_at,
                created_by_email,
                updated_by_email,
                xmin::text AS row_xmin
            FROM strategic_indicators.department_indicators
            WHERE department_id = %s
            ORDER BY display_order ASC, indicator_name ASC
        """
        return self.fetch_all(query, (department_id,))

    def list_active_indicators_by_source_keys(
        self,
        source_keys: list[str],
        *,
        department_id: str | None = None,
    ) -> list[dict]:
        normalized_keys = [
            str(key).strip()
            for key in source_keys
            if key is not None and str(key).strip()
        ]
        if not normalized_keys:
            return []

        placeholders = ", ".join(["%s"] * len(normalized_keys))
        params: list = list(normalized_keys)

        query = f"""
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
                branch_value_aggregation,
                is_active,
                display_order
            FROM strategic_indicators.department_indicators
            WHERE is_active = TRUE
              AND source_key IN ({placeholders})
        """

        if department_id:
            query += " AND department_id = %s"
            params.append(department_id)

        query += " ORDER BY display_order ASC, indicator_name ASC"
        return self.fetch_all(query, tuple(params))

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
        branch_value_aggregation: str = "auto",
        display_order: int,
        actor_user_id: str | None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        with self._unit_of_work():
            conflict = self.fetch_one(
                """
                SELECT indicator_id
                FROM strategic_indicators.department_indicators
                WHERE indicator_id = %s
                """,
                (indicator_id,),
            )
            if conflict:
                raise StrategicIndicatorsAdminConflictError(
                    f"Já existe um indicador com o id '{indicator_id}'."
                )
            row = self.execute_returning_one(
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
                    branch_value_aggregation,
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
                    %s, %s,
                    TRUE, %s, %s, %s, %s, %s
                )
                ON CONFLICT (indicator_id) DO NOTHING
                RETURNING *, xmin::text AS row_xmin
                """,
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
                    (branch_value_aggregation or "auto").strip().lower(),
                    supports_branch_goals_for_scope_type(scope_type),
                    display_order,
                    actor_user_id,
                    None,
                    actor_user_id,
                    None,
                ),
            )
            if not row:
                # Lost the check→insert race: a concurrent writer committed
                # the same id between the pre-check and this statement.
                raise StrategicIndicatorsAdminConflictError(
                    f"Já existe um indicador com o id '{indicator_id}'."
                )
            self._insert_admin_audit_event(
                event_type="department_indicator.created",
                entity_key=f"indicator:{indicator_id}",
                payload_before=None,
                payload_after_row=row,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
            )
            return row

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
        branch_value_aggregation: str = "auto",
        is_active: bool,
        display_order: int,
        actor_user_id: str | None,
        expected_row_xmin: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        current_id = indicator_id.strip()
        target_id = (new_indicator_id or current_id).strip()

        if not target_id:
            raise ValueError("indicator_id é obrigatório.")

        with self._unit_of_work():
            # Guarded read: FOR UPDATE serializes writers on this row, so the
            # xmin compare below is an atomic precondition covering the whole
            # mutation — including the multi-statement rename path.
            before = self.fetch_one(
                """
                SELECT *, xmin::text AS row_xmin
                FROM strategic_indicators.department_indicators
                WHERE indicator_id = %s
                FOR UPDATE
                """,
                (current_id,),
            )
            if not before:
                raise ValueError("Indicador estrutural não encontrado.")
            if (
                expected_row_xmin is not None
                and str(before.get("row_xmin")) != str(expected_row_xmin)
            ):
                raise StrategicIndicatorsAdminConflictError(
                    "O indicador foi alterado desde a leitura "
                    "(expected_row_xmin desatualizado)."
                )

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
                        branch_value_aggregation,
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
                        %s, %s,
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
                        (branch_value_aggregation or "auto").strip().lower(),
                        supports_branch_goals_for_scope_type(scope_type),
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
                current_id = target_id

            row = self.execute_returning_one(
                """
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
                    branch_value_aggregation = %s,
                    supports_branch_goals = %s,
                    is_active = %s,
                    display_order = %s,
                    updated_by_user_id = %s,
                    updated_by_email = %s,
                    updated_at = NOW()
                WHERE indicator_id = %s
                RETURNING *, xmin::text AS row_xmin
                """,
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
                    (branch_value_aggregation or "auto").strip().lower(),
                    supports_branch_goals_for_scope_type(scope_type),
                    is_active,
                    display_order,
                    actor_user_id,
                    None,
                    current_id,
                ),
            )
            self._insert_admin_audit_event(
                event_type="department_indicator.updated",
                entity_key=f"indicator:{current_id}",
                payload_before={
                    k: v for k, v in before.items() if k != "row_xmin"
                },
                payload_after_row=row,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
            )
            return row

    def activate_department_indicator(
        self,
        *,
        indicator_id: str,
        actor_user_id: str | None,
        expected_xmin: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        return self._set_indicator_active(
            indicator_id=indicator_id,
            is_active=True,
            actor_user_id=actor_user_id,
            expected_xmin=expected_xmin,
            audit_origin=audit_origin,
            correlation_id=correlation_id,
        )

    def deactivate_department_indicator(
        self,
        *,
        indicator_id: str,
        actor_user_id: str | None,
        expected_xmin: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        return self._set_indicator_active(
            indicator_id=indicator_id,
            is_active=False,
            actor_user_id=actor_user_id,
            expected_xmin=expected_xmin,
            audit_origin=audit_origin,
            correlation_id=correlation_id,
        )

    def _set_indicator_active(
        self,
        *,
        indicator_id: str,
        is_active: bool,
        actor_user_id: str | None,
        expected_xmin: str | None,
        audit_origin: str | None,
        correlation_id: str | None,
    ) -> dict:
        with self._unit_of_work():
            before = self.fetch_one(
                """
                SELECT *, xmin::text AS row_xmin
                FROM strategic_indicators.department_indicators
                WHERE indicator_id = %s
                """,
                (indicator_id,),
            )
            # Guarded state change: the expected_xmin precondition is
            # evaluated in the same atomic statement as the mutation.
            row = self.execute_returning_one(
                """
                UPDATE strategic_indicators.department_indicators
                SET
                    is_active = %s,
                    updated_by_user_id = %s,
                    updated_by_email = %s,
                    updated_at = NOW()
                WHERE indicator_id = %s
                  AND (%s::text IS NULL OR xmin::text = %s)
                RETURNING *, xmin::text AS row_xmin
                """,
                (
                    is_active,
                    actor_user_id,
                    None,
                    indicator_id,
                    expected_xmin,
                    expected_xmin,
                ),
            )
            if not row:
                if expected_xmin is not None:
                    raise StrategicIndicatorsAdminConflictError(
                        "O indicador foi alterado ou excluído desde a leitura "
                        "(expected_xmin desatualizado)."
                    )
                raise ValueError("Indicador estrutural não encontrado.")
            self._insert_admin_audit_event(
                event_type=(
                    "department_indicator.activated"
                    if is_active
                    else "department_indicator.deactivated"
                ),
                entity_key=f"indicator:{indicator_id}",
                payload_before=(
                    {k: v for k, v in before.items() if k != "row_xmin"}
                    if before
                    else None
                ),
                payload_after_row=row,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
            )
            return row

    def delete_department_indicator(
        self,
        *,
        indicator_id: str,
        actor_user_id: str | None,
    ) -> dict:
        with self._unit_of_work():
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

            delete_indicator_goals_cascade(self, indicator_id=indicator_id)
            self.execute(
                """
                DELETE FROM strategic_indicators.department_indicators
                WHERE indicator_id = %s
                """,
                (indicator_id,),
            )
            self._insert_admin_audit_event(
                event_type="department_indicator.deleted",
                entity_key=f"indicator:{indicator_id}",
                payload_before=before,
                payload_after_row=None,
                actor_user_id=actor_user_id,
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
