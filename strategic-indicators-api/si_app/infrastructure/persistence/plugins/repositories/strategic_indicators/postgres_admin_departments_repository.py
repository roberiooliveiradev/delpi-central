from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from si_app.application.services.strategic_indicators.admin_write_conflict_error import (
    StrategicIndicatorsAdminConflictError,
)
from si_app.domain.ports.strategic_indicators.admin_departments_repository_port import (
    StrategicIndicatorsAdminDepartmentsRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.catalog_admin_cascade import (
    delete_indicator_goals_cascade,
)
from si_app.infrastructure.providers.database.plugins_postgres_connection import (
    plugins_connection,
)


class PostgresStrategicIndicatorsAdminDepartmentsRepository(
    PluginBaseRepository,
    StrategicIndicatorsAdminDepartmentsRepositoryPort,
):
    @contextmanager
    def _unit_of_work(self) -> Iterator[None]:
        """Bind nested execute/fetch calls to one pooled connection/transaction.

        Without an injected connection each ``execute``/``fetch_*`` acquires
        its own pool lease and auto-commits per statement, so multi-statement
        mutations (rename migrate-refs + delete) and audit inserts would not
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
        audit_meta: dict | None = None,
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
        meta: dict = dict(audit_meta or {})
        if audit_origin:
            meta["write_origin"] = audit_origin
        if correlation_id:
            meta["correlation_id"] = correlation_id
        if meta and payload_after is not None:
            payload_after["_audit_meta"] = meta
        elif meta and payload_after is None:
            # Deletes carry no after row; provenance rides inside
            # payload_before instead (same `_audit_meta` key).
            payload_before = dict(payload_before or {})
            payload_before["_audit_meta"] = meta

        PostgresStrategicIndicatorsSettingsAuditRepository(
            self._connection
        ).insert_audit_event(
            entity_key=entity_key[:150],
            payload_before=payload_before,
            payload_after=payload_after,
            changed_by_user_id=actor_user_id,
            event_type=event_type,
        )

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
                updated_by_email,
                xmin::text AS row_xmin
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
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        with self._unit_of_work():
            conflict = self.fetch_one(
                """
                SELECT department_id
                FROM strategic_indicators.departments
                WHERE department_id = %s
                """,
                (department_id,),
            )
            if conflict:
                raise StrategicIndicatorsAdminConflictError(
                    f"Já existe um departamento com o id '{department_id}'."
                )
            row = self.execute_returning_one(
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s)
                ON CONFLICT (department_id) DO NOTHING
                RETURNING *, xmin::text AS row_xmin
                """,
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
            if not row:
                # Lost the check→insert race: a concurrent writer committed
                # the same id between the pre-check and this statement.
                raise StrategicIndicatorsAdminConflictError(
                    f"Já existe um departamento com o id '{department_id}'."
                )
            self._insert_admin_audit_event(
                event_type="department.created",
                entity_key=f"department:{department_id}",
                payload_before=None,
                payload_after_row=row,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
            )
            return row

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
        expected_row_xmin: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        current_id = department_id.strip()
        target_id = (new_department_id or current_id).strip()

        if not target_id:
            raise ValueError("department_id é obrigatório.")

        with self._unit_of_work():
            # Guarded read: FOR UPDATE serializes writers on this row, so the
            # xmin compare below is an atomic precondition covering the whole
            # mutation — including the multi-statement rename path.
            before = self.fetch_one(
                """
                SELECT *, xmin::text AS row_xmin
                FROM strategic_indicators.departments
                WHERE department_id = %s
                FOR UPDATE
                """,
                (current_id,),
            )
            if not before:
                raise ValueError("Departamento não encontrado.")
            if (
                expected_row_xmin is not None
                and str(before.get("row_xmin")) != str(expected_row_xmin)
            ):
                raise StrategicIndicatorsAdminConflictError(
                    "O departamento foi alterado desde a leitura "
                    "(expected_row_xmin desatualizado)."
                )

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
                current_id = target_id

            row = self.execute_returning_one(
                """
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
                RETURNING *, xmin::text AS row_xmin
                """,
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
            self._insert_admin_audit_event(
                event_type="department.updated",
                entity_key=f"department:{current_id}",
                payload_before={
                    k: v for k, v in before.items() if k != "row_xmin"
                },
                payload_after_row=row,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
            )
            return row

    def activate_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
        expected_xmin: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        return self._set_department_active(
            department_id=department_id,
            is_active=True,
            actor_user_id=actor_user_id,
            expected_xmin=expected_xmin,
            audit_origin=audit_origin,
            correlation_id=correlation_id,
        )

    def deactivate_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
        expected_xmin: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        return self._set_department_active(
            department_id=department_id,
            is_active=False,
            actor_user_id=actor_user_id,
            expected_xmin=expected_xmin,
            audit_origin=audit_origin,
            correlation_id=correlation_id,
        )

    def _set_department_active(
        self,
        *,
        department_id: str,
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
                FROM strategic_indicators.departments
                WHERE department_id = %s
                """,
                (department_id,),
            )
            # Guarded state change: the expected_xmin precondition is
            # evaluated in the same atomic statement as the mutation.
            row = self.execute_returning_one(
                """
                UPDATE strategic_indicators.departments
                SET
                    is_active = %s,
                    updated_by_user_id = %s,
                    updated_by_email = %s,
                    updated_at = NOW()
                WHERE department_id = %s
                  AND (%s::text IS NULL OR xmin::text = %s)
                RETURNING *, xmin::text AS row_xmin
                """,
                (
                    is_active,
                    actor_user_id,
                    None,
                    department_id,
                    expected_xmin,
                    expected_xmin,
                ),
            )
            if not row:
                if expected_xmin is not None and before:
                    raise StrategicIndicatorsAdminConflictError(
                        "O departamento foi alterado desde a leitura "
                        "(expected_xmin desatualizado)."
                    )
                if expected_xmin is not None:
                    raise StrategicIndicatorsAdminConflictError(
                        "O departamento foi alterado ou excluído desde a "
                        "leitura (expected_xmin desatualizado)."
                    )
                raise ValueError("Departamento não encontrado.")
            self._insert_admin_audit_event(
                event_type=(
                    "department.activated" if is_active else "department.deactivated"
                ),
                entity_key=f"department:{department_id}",
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

    def delete_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
        expected_xmin: str | None = None,
        expected_indicator_count: int | None = None,
        expected_goal_count: int | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        with self._unit_of_work():
            # Row locks block sibling mutations/deletes on the department and
            # its indicators while the dependent set is validated in-tx.
            before = self.fetch_one(
                """
                SELECT *
                FROM strategic_indicators.departments
                WHERE department_id = %s
                FOR UPDATE
                """,
                (department_id,),
            )
            if not before:
                raise ValueError("Departamento não encontrado.")

            if expected_xmin is not None:
                current_xmin = self.fetch_one(
                    """
                    SELECT xmin::text AS row_xmin
                    FROM strategic_indicators.departments
                    WHERE department_id = %s
                    """,
                    (department_id,),
                )
                if not current_xmin or current_xmin["row_xmin"] != expected_xmin:
                    raise StrategicIndicatorsAdminConflictError(
                        "Versão do departamento divergente; recarregue antes de excluir."
                    )

            indicator_rows = self.fetch_all(
                """
                SELECT indicator_id
                FROM strategic_indicators.department_indicators
                WHERE department_id = %s
                FOR UPDATE
                """,
                (department_id,),
            )
            if expected_indicator_count is not None and len(indicator_rows) != int(
                expected_indicator_count
            ):
                raise StrategicIndicatorsAdminConflictError(
                    "Dependentes do departamento divergentes; recarregue antes de excluir."
                )

            goals_count = self.fetch_one(
                """
                SELECT COUNT(*) AS cnt
                FROM strategic_indicators.indicator_goals g
                INNER JOIN strategic_indicators.department_indicators di
                    ON di.indicator_id = g.indicator_id
                WHERE di.department_id = %s
                """,
                (department_id,),
            )
            goal_total = int((goals_count or {}).get("cnt") or 0)
            if expected_goal_count is not None and goal_total != int(
                expected_goal_count
            ):
                raise StrategicIndicatorsAdminConflictError(
                    "Dependentes do departamento divergentes; recarregue antes de excluir."
                )

            monthly_count = self.fetch_one(
                """
                SELECT COUNT(*) AS cnt
                FROM strategic_indicators.indicator_goal_monthly_targets t
                INNER JOIN strategic_indicators.indicator_goals g
                    ON g.id = t.indicator_goal_id
                INNER JOIN strategic_indicators.department_indicators di
                    ON di.indicator_id = g.indicator_id
                WHERE di.department_id = %s
                """,
                (department_id,),
            )

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
            deleted = self.execute_returning_one(
                """
                DELETE FROM strategic_indicators.departments
                WHERE department_id = %s
                RETURNING *
                """,
                (department_id,),
            )
            if deleted is None:
                raise ValueError("Departamento não encontrado.")

            self._insert_admin_audit_event(
                event_type="department.deleted",
                entity_key=f"department:{department_id}",
                payload_before=before,
                payload_after_row=None,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
                audit_meta={
                    "indicators_deleted": len(indicator_rows),
                    "indicator_goals_deleted": goal_total,
                    "monthly_targets_deleted": int(
                        (monthly_count or {}).get("cnt") or 0
                    ),
                },
            )
            return {
                "message": "Departamento excluído com sucesso.",
                "department_id": department_id,
            }
