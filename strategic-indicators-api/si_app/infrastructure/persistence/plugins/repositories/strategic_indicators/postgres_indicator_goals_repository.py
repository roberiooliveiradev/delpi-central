from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from typing import Iterator

from si_app.application.services.strategic_indicators.indicator_goal_conflict_error import (
    StrategicIndicatorsGoalConflictError,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    competence_reference_date,
)
from si_app.domain.ports.strategic_indicators.indicator_goals_repository_port import (
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from si_app.infrastructure.providers.database.plugins_postgres_connection import (
    plugins_connection,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.catalog_admin_cascade import (
    delete_indicator_goal_hard,
)
from si_app.shared.goal_scope import (
    normalize_goal_scope_branch,
    uses_strict_branch_goal_resolution,
)


class PostgresStrategicIndicatorsIndicatorGoalsRepository(
    PluginBaseRepository,
    StrategicIndicatorsIndicatorGoalsRepositoryPort,
):
    @contextmanager
    def _unit_of_work(self) -> Iterator[None]:
        """Bind nested execute/fetch calls to one pooled connection/transaction.

        Without an injected connection each ``execute``/``fetch_*`` acquires
        its own pool lease and auto-commits per statement, so multi-statement
        mutations (deactivate + insert + targets) are not atomic. Injecting
        the leased connection disables per-statement auto-commit and this
        wrapper performs a single commit/rollback for the whole mutation.
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

    def _insert_goal_audit_event(
        self,
        *,
        event_type: str,
        goal_row: dict,
        payload_before: dict | None,
        actor_user_id: str | None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
        audit_meta: dict | None = None,
        deleted: bool = False,
    ) -> None:
        """Persist the goal mutation into ``strategic_indicators.settings_audit``.

        Must be called inside ``_unit_of_work`` so the INSERT rides the same
        transaction as the mutation — audit and write commit or roll back
        together. Correlation metadata (write origin, caller correlation id,
        consequential effects) is embedded under ``_audit_meta`` inside
        ``payload_after`` because the audit schema carries no dedicated
        correlation column. For deletes (``deleted=True``) there is no after
        row, so the metadata rides inside ``payload_before`` instead and
        ``payload_after`` stays ``None``.
        """
        from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_audit_repository import (
            PostgresStrategicIndicatorsSettingsAuditRepository,
        )

        entity_key = (
            f"indicator_goal:{goal_row.get('indicator_id')}"
            f":{goal_row.get('goal_year')}"
        )
        branch = (goal_row.get("goal_scope_branch") or "").strip()
        if branch:
            entity_key += f":{branch}"
        entity_key += f":v{goal_row.get('version')}"
        entity_key = entity_key[:150]

        meta = dict(audit_meta or {})
        if audit_origin:
            meta["write_origin"] = audit_origin
        if correlation_id:
            meta["correlation_id"] = correlation_id

        if deleted:
            payload_after = None
            if meta:
                payload_before = dict(payload_before or goal_row)
                payload_before["_audit_meta"] = meta
        else:
            payload_after = {k: v for k, v in goal_row.items() if k != "row_xmin"}
            if meta:
                payload_after["_audit_meta"] = meta

        PostgresStrategicIndicatorsSettingsAuditRepository(
            self._connection
        ).insert_audit_event(
            entity_key=entity_key,
            payload_before=payload_before,
            payload_after=payload_after,
            changed_by_user_id=actor_user_id,
            event_type=event_type,
        )

    @staticmethod
    def _scope_lock_key(
        *, indicator_id: str, goal_year: int, goal_scope_branch: str
    ) -> str:
        return f"si_goal_scope:{indicator_id}:{goal_year}:{goal_scope_branch}"

    def _lock_goal_scope(
        self,
        *,
        indicator_id: str,
        goal_year: int,
        goal_scope_branch: str,
    ) -> None:
        """Serialize concurrent writers of the same goal scope inside the
        current transaction (row locks alone do not cover INSERT gaps)."""
        self.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s)::bigint)",
            (
                self._scope_lock_key(
                    indicator_id=indicator_id,
                    goal_year=goal_year,
                    goal_scope_branch=goal_scope_branch,
                ),
            ),
        )

    @staticmethod
    def _resolved_goal_scope_filter(
        *,
        scope_branch: str | None,
        params: list,
    ) -> str:
        normalized = normalize_goal_scope_branch(scope_branch)
        if normalized:
            params.append(normalized)
            if uses_strict_branch_goal_resolution(scope_branch):
                return " AND ig.goal_scope_branch = %s"
            return " AND ig.goal_scope_branch IN (%s, '')"
        return " AND ig.goal_scope_branch = ''"

    @staticmethod
    def _resolved_goal_scope_order(
        *,
        scope_branch: str | None,
    ) -> tuple[str, list]:
        """
        Fragmento ORDER BY e parâmetros na ordem em que aparecem no SQL final.

        Os valores devem ser acrescentados a ``params`` depois do filtro de vigência
        (valid_from/valid_to), pois o CASE entra no ORDER BY após o WHERE.
        """
        normalized = normalize_goal_scope_branch(scope_branch)
        if normalized and not uses_strict_branch_goal_resolution(scope_branch):
            return (
                """
                CASE
                    WHEN ig.goal_scope_branch = %s THEN 0
                    WHEN ig.goal_scope_branch = '' THEN 1
                    ELSE 2
                END,
            """,
                [normalized],
            )
        return "", []

    def get_indicator_goal_policy(self, indicator_id: str) -> dict | None:
        return self.fetch_one(
            """
            SELECT
                indicator_id,
                scope_type,
                supports_branch_goals
            FROM strategic_indicators.department_indicators
            WHERE indicator_id = %s
            """,
            (indicator_id,),
        )

    def fetch_goal_identity(self, goal_id: str) -> dict | None:
        return self.fetch_one(
            """
            SELECT id, indicator_id, goal_year, goal_scope_branch
            FROM strategic_indicators.indicator_goals
            WHERE id = %s
            """,
            (goal_id,),
        )

    def _deactivate_active_goals_for_scope(
        self,
        *,
        indicator_id: str,
        goal_year: int,
        goal_scope_branch: str,
        actor_user_id: str | None,
    ) -> list[str]:
        return [
            str(row["id"])
            for row in self.fetch_all(
                """
                UPDATE strategic_indicators.indicator_goals
                SET
                    is_active = FALSE,
                    updated_by_user_id = %s,
                    updated_by_email = %s,
                    updated_at = NOW()
                WHERE indicator_id = %s
                  AND goal_year = %s
                  AND goal_scope_branch = %s
                  AND is_active = TRUE
                RETURNING id
                """,
                (
                    actor_user_id,
                    None,
                    indicator_id,
                    goal_year,
                    goal_scope_branch,
                ),
            )
        ]

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
                ig.goal_scope_branch,
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
                ig.updated_at,
                ig.xmin::text AS row_xmin
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
                ig.goal_scope_branch ASC,
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
                ig.goal_scope_branch,
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
                ig.updated_at,
                ig.xmin::text AS row_xmin
            FROM strategic_indicators.indicator_goals ig
            INNER JOIN strategic_indicators.department_indicators di
                ON di.indicator_id = ig.indicator_id
            WHERE ig.indicator_id = %s
        """
        params: list = [indicator_id]

        if goal_year is not None:
            query += " AND ig.goal_year = %s"
            params.append(goal_year)

        query += """
            ORDER BY
                ig.goal_year DESC,
                ig.goal_scope_branch ASC,
                ig.version DESC,
                ig.created_at DESC
        """

        rows = self.fetch_all(query, tuple(params))
        return self._attach_monthly_targets(rows)

    def get_resolved_goal(
        self,
        *,
        indicator_id: str,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        scope_branch: str | None = None,
    ) -> dict | None:
        year = self._resolve_goal_year(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

        params: list = [indicator_id, year]
        scope_filter = self._resolved_goal_scope_filter(
            scope_branch=scope_branch,
            params=params,
        )
        scope_order, scope_order_params = self._resolved_goal_scope_order(
            scope_branch=scope_branch,
        )
        params.extend(scope_order_params)

        query = f"""
            SELECT
                id,
                indicator_id,
                goal_year,
                goal_label,
                goal_value,
                goal_periodicity,
                goal_mode,
                goal_scope_branch,
                version,
                is_active,
                valid_from,
                valid_to,
                notes,
                created_at,
                updated_at
            FROM strategic_indicators.indicator_goals ig
            WHERE indicator_id = %s
              AND goal_year = %s
              AND is_active = TRUE
              {scope_filter}
            ORDER BY
                {scope_order}
                version DESC,
                updated_at DESC
            LIMIT 1
        """
        row = self.fetch_one(query, tuple(params))
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
        scope_branch: str | None = None,
    ) -> dict[str, dict]:
        year = self._resolve_goal_year(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

        params: list = [year]
        scope_filter = self._resolved_goal_scope_filter(
            scope_branch=scope_branch,
            params=params,
        )
        scope_order, scope_order_params = self._resolved_goal_scope_order(
            scope_branch=scope_branch,
        )

        query = f"""
            SELECT DISTINCT ON (ig.indicator_id)
                ig.id,
                ig.indicator_id,
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
                ig.goal_mode,
                ig.goal_scope_branch,
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
              {scope_filter}
        """

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
        params.extend(scope_order_params)

        query += f"""
            ORDER BY
                ig.indicator_id,
                {scope_order}
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

    def list_branch_scoped_goals_map(
        self,
        *,
        indicator_ids: list[str],
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, dict[str, dict]]:
        normalized_ids = [
            str(indicator_id).strip()
            for indicator_id in indicator_ids
            if indicator_id is not None and str(indicator_id).strip()
        ]
        if not normalized_ids:
            return {}

        year = self._resolve_goal_year(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
        placeholders = ", ".join("%s" for _ in normalized_ids)
        params: list = [year, *normalized_ids]

        query = f"""
            SELECT
                ig.id,
                ig.indicator_id,
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
                ig.goal_mode,
                ig.goal_scope_branch,
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
              AND ig.goal_scope_branch IN ('01', '02')
              AND ig.indicator_id IN ({placeholders})
        """

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
                ig.indicator_id ASC,
                ig.goal_scope_branch ASC,
                ig.version DESC,
                ig.updated_at DESC
        """

        rows = self.fetch_all(query, tuple(params))
        if not rows:
            return {}

        goal_ids = [row["id"] for row in rows]
        monthly_by_goal = self._list_monthly_targets_batch(goal_ids)

        result: dict[str, dict[str, dict]] = {}
        for row in rows:
            indicator_id = row["indicator_id"]
            scope_branch = normalize_goal_scope_branch(row.get("goal_scope_branch"))
            if scope_branch not in {"01", "02"}:
                continue
            if indicator_id not in result:
                result[indicator_id] = {}
            if scope_branch in result[indicator_id]:
                continue

            item = dict(row)
            item["monthly_targets"] = monthly_by_goal.get(row["id"], [])
            result[indicator_id][scope_branch] = item

        return result

    def list_latest_active_goals_map(
        self,
        *,
        indicator_ids: list[str],
        department_id: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        scope_branch: str | None = None,
    ) -> dict[str, dict]:
        normalized_ids = [
            str(indicator_id).strip()
            for indicator_id in indicator_ids
            if indicator_id is not None and str(indicator_id).strip()
        ]
        if not normalized_ids:
            return {}

        placeholders = ", ".join("%s" for _ in normalized_ids)
        params: list = list(normalized_ids)
        scope_filter = self._resolved_goal_scope_filter(
            scope_branch=scope_branch,
            params=params,
        )
        scope_order, scope_order_params = self._resolved_goal_scope_order(
            scope_branch=scope_branch,
        )

        query = f"""
            SELECT DISTINCT ON (ig.indicator_id)
                ig.id,
                ig.indicator_id,
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
                ig.goal_mode,
                ig.goal_scope_branch,
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
              {scope_filter}
        """

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
        params.extend(scope_order_params)

        query += f"""
            ORDER BY
                ig.indicator_id,
                ig.goal_year DESC,
                {scope_order}
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
        goal_scope_branch: str = "",
        monthly_targets: list[dict],
        valid_from: str | None,
        valid_to: str | None,
        notes: str | None,
        actor_user_id: str | None,
        expected_max_version: int | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        goal_scope_branch = normalize_goal_scope_branch(goal_scope_branch)

        with self._unit_of_work():
            # Serialize writers of this scope so the MAX(version) computation
            # and the active-goal swap cannot interleave with another create.
            self._lock_goal_scope(
                indicator_id=indicator_id,
                goal_year=goal_year,
                goal_scope_branch=goal_scope_branch,
            )

            superseded_ids = self._deactivate_active_goals_for_scope(
                indicator_id=indicator_id,
                goal_year=goal_year,
                goal_scope_branch=goal_scope_branch,
                actor_user_id=actor_user_id,
            )

            # Guarded insert: next version is computed inside the same
            # statement that inserts, and the optional optimistic precondition
            # (expected MAX(version) of the scope) is enforced atomically —
            # a stale expectation inserts zero rows instead of overwriting.
            created = self.execute_returning_one(
                """
                INSERT INTO strategic_indicators.indicator_goals (
                    indicator_id,
                    goal_year,
                    goal_label,
                    goal_value,
                    goal_periodicity,
                    goal_mode,
                    goal_scope_branch,
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
                SELECT
                    %s, %s, %s, %s, %s, %s, %s,
                    mv.max_version + 1,
                    TRUE, %s, %s, %s, %s, %s, %s, %s
                FROM (
                    SELECT COALESCE(MAX(version), 0) AS max_version
                    FROM strategic_indicators.indicator_goals
                    WHERE indicator_id = %s
                      AND goal_year = %s
                      AND goal_scope_branch = %s
                ) mv
                WHERE %s::int IS NULL OR mv.max_version = %s
                RETURNING *, xmin::text AS row_xmin
                """,
                (
                    indicator_id,
                    goal_year,
                    goal_label,
                    goal_value,
                    goal_periodicity,
                    goal_mode,
                    goal_scope_branch,
                    valid_from,
                    valid_to,
                    notes,
                    actor_user_id,
                    None,
                    actor_user_id,
                    None,
                    indicator_id,
                    goal_year,
                    goal_scope_branch,
                    expected_max_version,
                    expected_max_version,
                ),
            )
            if created is None:
                raise StrategicIndicatorsGoalConflictError(
                    "O escopo da meta foi alterado desde a leitura "
                    "(expected_max_version desatualizado)."
                )

            if goal_mode == "monthly_curve":
                self.replace_monthly_targets(
                    indicator_goal_id=created["id"],
                    monthly_targets=monthly_targets,
                )

            self._insert_goal_audit_event(
                event_type="indicator_goal.created",
                goal_row=created,
                payload_before=None,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
                audit_meta=(
                    {"superseded_goal_ids": superseded_ids}
                    if superseded_ids
                    else None
                ),
            )

        created["monthly_targets"] = self.list_monthly_targets(
            indicator_goal_id=created["id"]
        )
        return created

    def update_indicator_goal(
        self,
        *,
        goal_id: str,
        indicator_id: str | None,
        goal_year: int | None,
        goal_scope_branch: str | None,
        goal_label: str,
        goal_value: float,
        goal_periodicity: str,
        goal_mode: str,
        monthly_targets: list[dict],
        valid_from: str | None,
        valid_to: str | None,
        notes: str | None,
        actor_user_id: str | None,
        expected_row_xmin: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        with self._unit_of_work():
            before_row = self.fetch_one(
                """
                SELECT *
                FROM strategic_indicators.indicator_goals
                WHERE id = %s
                """,
                (goal_id,),
            )

            if indicator_id or goal_year is not None or goal_scope_branch is not None:
                current = self.fetch_goal_identity(goal_id)
                if not current:
                    raise ValueError("Meta não encontrada.")

                target_indicator = indicator_id or current["indicator_id"]
                target_year = goal_year if goal_year is not None else current["goal_year"]
                target_scope = (
                    goal_scope_branch
                    if goal_scope_branch is not None
                    else (current.get("goal_scope_branch") or "")
                )

                conflict = self.fetch_one(
                    """
                    SELECT id
                    FROM strategic_indicators.indicator_goals
                    WHERE indicator_id = %s
                      AND goal_year = %s
                      AND goal_scope_branch = %s
                      AND id <> %s
                    LIMIT 1
                    """,
                    (
                        target_indicator,
                        target_year,
                        target_scope,
                        goal_id,
                    ),
                )
                if conflict:
                    raise ValueError(
                        "Já existe meta para este indicador, ano e escopo."
                    )

            # Guarded update: the optional ``expected_row_xmin`` optimistic
            # precondition is evaluated in the same atomic statement as the
            # mutation, so a row changed since the caller's read is refused.
            updated = self.execute_returning_one(
                """
                UPDATE strategic_indicators.indicator_goals
                SET
                    indicator_id = COALESCE(%s, indicator_id),
                    goal_year = COALESCE(%s, goal_year),
                    goal_scope_branch = COALESCE(%s, goal_scope_branch),
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
                  AND (%s::text IS NULL OR xmin::text = %s)
                RETURNING *, xmin::text AS row_xmin
                """,
                (
                    indicator_id,
                    goal_year,
                    goal_scope_branch,
                    goal_label,
                    goal_value,
                    goal_periodicity,
                    goal_mode,
                    valid_from,
                    valid_to,
                    notes,
                    actor_user_id,
                    None,
                    goal_id,
                    expected_row_xmin,
                    expected_row_xmin,
                ),
            )
            if updated is None:
                if expected_row_xmin is not None:
                    raise StrategicIndicatorsGoalConflictError(
                        "A meta foi alterada ou excluída desde a leitura "
                        "(expected_row_xmin desatualizado)."
                    )
                raise ValueError("Meta não encontrada.")

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

            self._insert_goal_audit_event(
                event_type="indicator_goal.updated",
                goal_row=updated,
                payload_before=before_row,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
            )

        updated["monthly_targets"] = self.list_monthly_targets(
            indicator_goal_id=goal_id
        )
        return updated

    def activate_indicator_goal(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
        expected_xmin: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        with self._unit_of_work():
            target = self.fetch_one(
                """
                SELECT *
                FROM strategic_indicators.indicator_goals
                WHERE id = %s
                """,
                (goal_id,),
            )
            if not target:
                raise ValueError("Meta não encontrada.")

            # Serialize writers of this scope: the deactivate+activate pair
            # must not interleave with a concurrent activate or create.
            self._lock_goal_scope(
                indicator_id=target["indicator_id"],
                goal_year=target["goal_year"],
                goal_scope_branch=target.get("goal_scope_branch") or "",
            )

            superseded_ids = [
                str(r["id"])
                for r in self.fetch_all(
                    """
                    UPDATE strategic_indicators.indicator_goals
                    SET
                        is_active = FALSE,
                        updated_by_user_id = %s,
                        updated_by_email = %s,
                        updated_at = NOW()
                    WHERE indicator_id = %s
                      AND goal_year = %s
                      AND goal_scope_branch = %s
                      AND id <> %s
                      AND is_active = TRUE
                    RETURNING id
                    """,
                    (
                        actor_user_id,
                        None,
                        target["indicator_id"],
                        target["goal_year"],
                        target.get("goal_scope_branch") or "",
                        goal_id,
                    ),
                )
            ]

            # Guarded activate: a stale ``expected_xmin`` refuses the change
            # before any sibling is deactivated (single transaction).
            row = self.execute_returning_one(
                """
                UPDATE strategic_indicators.indicator_goals
                SET
                    is_active = TRUE,
                    updated_by_user_id = %s,
                    updated_by_email = %s,
                    updated_at = NOW()
                WHERE id = %s
                  AND (%s::text IS NULL OR xmin::text = %s)
                RETURNING *, xmin::text AS row_xmin
                """,
                (
                    actor_user_id,
                    None,
                    goal_id,
                    expected_xmin,
                    expected_xmin,
                ),
            )
            if row is None:
                raise StrategicIndicatorsGoalConflictError(
                    "A meta foi alterada ou excluída desde a leitura "
                    "(expected_xmin desatualizado)."
                )

            self._insert_goal_audit_event(
                event_type="indicator_goal.activated",
                goal_row=row,
                payload_before=target,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
                audit_meta=(
                    {"superseded_goal_ids": superseded_ids}
                    if superseded_ids
                    else None
                ),
            )

        row["monthly_targets"] = self.list_monthly_targets(
            indicator_goal_id=goal_id
        )
        return row

    def delete_indicator_goal(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
        expected_xmin: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        with self._unit_of_work():
            before_row = self.fetch_one(
                """
                SELECT *
                FROM strategic_indicators.indicator_goals
                WHERE id = %s
                """,
                (goal_id,),
            )
            if not before_row:
                raise ValueError("Meta não encontrada.")

            # Serialize against concurrent writers of the same goal scope so
            # a sibling mutation cannot interleave inside this transaction.
            self._lock_goal_scope(
                indicator_id=str(before_row["indicator_id"]),
                goal_year=int(before_row["goal_year"]),
                goal_scope_branch=str(before_row.get("goal_scope_branch") or ""),
            )

            monthly_targets = self.fetch_one(
                """
                SELECT COUNT(*) AS cnt
                FROM strategic_indicators.indicator_goal_monthly_targets
                WHERE indicator_goal_id = %s
                """,
                (goal_id,),
            )
            copied_refs = self.fetch_one(
                """
                SELECT COUNT(*) AS cnt
                FROM strategic_indicators.indicator_goals
                WHERE copied_from_goal_id = %s
                """,
                (goal_id,),
            )

            # Guarded delete: a stale ``expected_xmin`` refuses the change
            # atomically in the same statement as the mutation. FK rules
            # cascade monthly targets and SET NULL on copied_from refs in
            # the same transaction.
            deleted = self.execute_returning_one(
                """
                DELETE FROM strategic_indicators.indicator_goals
                WHERE id = %s
                  AND (%s::text IS NULL OR xmin::text = %s)
                RETURNING *
                """,
                (goal_id, expected_xmin, expected_xmin),
            )
            if deleted is None:
                if expected_xmin is not None:
                    raise StrategicIndicatorsGoalConflictError(
                        "Versão da meta divergente; recarregue antes de excluir."
                    )
                raise ValueError("Meta não encontrada.")

            self._insert_goal_audit_event(
                event_type="indicator_goal.deleted",
                goal_row=before_row,
                payload_before=before_row,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
                audit_meta={
                    "monthly_targets_deleted": int(
                        (monthly_targets or {}).get("cnt") or 0
                    ),
                    "copied_from_references_cleared": int(
                        (copied_refs or {}).get("cnt") or 0
                    ),
                },
                deleted=True,
            )
            return {
                "message": "Meta analítica excluída com sucesso.",
                "goal_id": goal_id,
            }

    def deactivate_indicator_goal(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
        expected_xmin: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        with self._unit_of_work():
            before_row = self.fetch_one(
                """
                SELECT *
                FROM strategic_indicators.indicator_goals
                WHERE id = %s
                """,
                (goal_id,),
            )

            # Guarded deactivate: a stale ``expected_xmin`` refuses the
            # change atomically in the same statement as the mutation.
            row = self.execute_returning_one(
                """
                UPDATE strategic_indicators.indicator_goals
                SET
                    is_active = FALSE,
                    updated_by_user_id = %s,
                    updated_by_email = %s,
                    updated_at = NOW()
                WHERE id = %s
                  AND (%s::text IS NULL OR xmin::text = %s)
                RETURNING *, xmin::text AS row_xmin
                """,
                (
                    actor_user_id,
                    None,
                    goal_id,
                    expected_xmin,
                    expected_xmin,
                ),
            )
            if row is None:
                if expected_xmin is not None:
                    raise StrategicIndicatorsGoalConflictError(
                        "A meta foi alterada ou excluída desde a leitura "
                        "(expected_xmin desatualizado)."
                    )
                raise ValueError("Meta não encontrada.")

            self._insert_goal_audit_event(
                event_type="indicator_goal.deactivated",
                goal_row=row,
                payload_before=before_row,
                actor_user_id=actor_user_id,
                audit_origin=audit_origin,
                correlation_id=correlation_id,
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

        from si_app.application.services.strategic_indicators.period_resolution import (
            _parse_dashboard_date_parts,
            normalize_dashboard_period_date,
        )

        for value in (end_date, start_date):
            normalized = normalize_dashboard_period_date(value)
            parts = _parse_dashboard_date_parts(normalized) if normalized else None
            if parts:
                _day, _month, year = parts
                return year

        raise ValueError("Não foi possível resolver o ano da meta.")

    def bulk_create_indicator_goals(
        self,
        *,
        goal_year: int,
        items: list[dict],
        actor_user_id: str | None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        created_items: list[dict] = []

        # One transaction for the whole batch — without the UoW each item
        # committed separately and a mid-batch failure left a partial set.
        with self._unit_of_work():
            for item in items:
                created_items.append(
                    self.create_indicator_goal(
                        indicator_id=item["indicator_id"],
                        goal_year=goal_year,
                        goal_label=item["goal_label"],
                        goal_value=float(item["goal_value"]),
                        goal_periodicity=item["goal_periodicity"],
                        goal_mode=item.get("goal_mode", "standard"),
                        goal_scope_branch=item.get("goal_scope_branch") or "",
                        monthly_targets=item.get("monthly_targets") or [],
                        valid_from=item.get("valid_from"),
                        valid_to=item.get("valid_to"),
                        notes=item.get("notes"),
                        actor_user_id=actor_user_id,
                        expected_max_version=item.get("expected_max_version"),
                        audit_origin=audit_origin,
                        correlation_id=correlation_id,
                    )
                )

        return {
            "message": "Metas analíticas criadas em lote com sucesso.",
            "items": created_items,
        }

    @staticmethod
    def _goals_rows_digest(rows: list[dict], fields: tuple[str, ...]) -> str:
        """Deterministic digest of a goal row set (PREPARE↔ACT binding).

        Shared contract with the DAVI BFF: sha256 over the sorted
        ``|``-joined field tuples — any drift in membership or copied
        content changes the digest and must surface a typed conflict.
        """
        import hashlib

        def _norm(field: str, value) -> str:
            if value is None:
                return ""
            # Numeric fields may surface as Decimal/float/int depending on
            # the driver path — coerce through float so the BFF-computed
            # digest over the JSON contract is byte-identical.
            if field == "goal_value":
                try:
                    return str(float(value))
                except (TypeError, ValueError):
                    return str(value)
            return str(value)

        tuples = sorted(
            "|".join(_norm(field, row.get(field)) for field in fields)
            for row in rows
        )
        return hashlib.sha256("\n".join(tuples).encode("utf-8")).hexdigest()

    _BULK_SOURCE_DIGEST_FIELDS = (
        "indicator_id",
        "goal_scope_branch",
        "goal_label",
        "goal_value",
        "goal_periodicity",
        "goal_mode",
    )
    _BULK_EXISTING_DIGEST_FIELDS = (
        "indicator_id",
        "goal_scope_branch",
        "goal_year",
    )

    def _require_bulk_digest(
        self,
        *,
        expected: str | None,
        actual_rows: list[dict],
        fields: tuple[str, ...],
        label: str,
    ) -> None:
        if expected is None:
            return
        actual = self._goals_rows_digest(actual_rows, fields)
        if actual != expected:
            from si_app.application.services.strategic_indicators.admin_write_conflict_error import (
                StrategicIndicatorsAdminConflictError,
            )

            raise StrategicIndicatorsAdminConflictError(
                f"Conjunto '{label}' diverge do preview aprovado — "
                "o estado mudou desde a leitura. Recarregue e tente novamente."
            )

    def duplicate_goals_year(
        self,
        *,
        source_year: int,
        target_year: int,
        indicator_ids: list[str] | None,
        overwrite_existing: bool,
        actor_user_id: str | None,
        expected_source_digest: str | None = None,
        expected_existing_digest: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        source_query = """
            SELECT
                id,
                indicator_id,
                goal_scope_branch,
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

        with self._unit_of_work():
            # First pass (pre-lock): discover the touched scopes so the
            # advisory locks can be taken in deterministic order.
            probe_rows = self.fetch_all(source_query, tuple(params))
            touched_scopes = sorted(
                {
                    (row["indicator_id"], row.get("goal_scope_branch") or "")
                    for row in probe_rows
                }
            )
            for indicator_id, goal_scope_branch in touched_scopes:
                self._lock_goal_scope(
                    indicator_id=indicator_id,
                    goal_year=target_year,
                    goal_scope_branch=goal_scope_branch,
                )

            # Second pass (post-lock): re-read both snapshots under the
            # held locks so the digests and existing-set reflect the state
            # that will actually be mutated — a concurrent writer cannot
            # slip a commit between read and lock.
            source_rows = self.fetch_all(source_query, tuple(params))
            # A source scope may have appeared between probe and re-read;
            # lock it too (advisory locks participate in PG deadlock
            # detection, so a conflicting order aborts safely).
            for indicator_id, goal_scope_branch in sorted(
                {
                    (row["indicator_id"], row.get("goal_scope_branch") or "")
                    for row in source_rows
                }
                - set(touched_scopes)
            ):
                self._lock_goal_scope(
                    indicator_id=indicator_id,
                    goal_year=target_year,
                    goal_scope_branch=goal_scope_branch,
                )
            existing_target_rows = self.fetch_all(
                """
                SELECT indicator_id, goal_scope_branch, goal_year
                FROM strategic_indicators.indicator_goals
                WHERE goal_year = %s
                  AND is_active = TRUE
                ORDER BY indicator_id ASC, goal_scope_branch ASC
                """,
                (target_year,),
            )
            existing_keys = {
                (row["indicator_id"], row.get("goal_scope_branch") or "")
                for row in existing_target_rows
            }

            # PREPARE↔ACT binding: the source set and the existing target
            # set must match the approved preview, otherwise a concurrent
            # change would be silently applied.
            self._require_bulk_digest(
                expected=expected_source_digest,
                actual_rows=source_rows,
                fields=self._BULK_SOURCE_DIGEST_FIELDS,
                label="source",
            )
            self._require_bulk_digest(
                expected=expected_existing_digest,
                actual_rows=existing_target_rows,
                fields=self._BULK_EXISTING_DIGEST_FIELDS,
                label="target_existing",
            )

            created_items: list[dict] = []

            for row in source_rows:
                goal_scope_branch = row.get("goal_scope_branch") or ""
                scope_key = (row["indicator_id"], goal_scope_branch)
                has_existing = scope_key in existing_keys

                if has_existing and not overwrite_existing:
                    continue

                if has_existing and overwrite_existing:
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
                          AND goal_scope_branch = %s
                          AND is_active = TRUE
                        """,
                        (
                            actor_user_id,
                            None,
                            row["indicator_id"],
                            target_year,
                            goal_scope_branch,
                        ),
                    )
                    self._insert_goal_audit_event(
                        event_type="indicator_goal.deactivated",
                        goal_row={
                            "indicator_id": row["indicator_id"],
                            "goal_year": target_year,
                            "goal_scope_branch": goal_scope_branch,
                            "version": "bulk-supersede",
                        },
                        payload_before={"is_active": True},
                        actor_user_id=actor_user_id,
                        audit_origin=audit_origin,
                        correlation_id=correlation_id,
                    )

                version_row = self.fetch_one(
                    """
                    SELECT COALESCE(MAX(version), 0) AS max_version
                    FROM strategic_indicators.indicator_goals
                    WHERE indicator_id = %s
                      AND goal_year = %s
                      AND goal_scope_branch = %s
                    """,
                    (row["indicator_id"], target_year, goal_scope_branch),
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
                        goal_scope_branch,
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        row["indicator_id"],
                        target_year,
                        row["goal_label"],
                        0.0
                        if row.get("goal_mode") == "monthly_curve"
                        else row["goal_value"],
                        row["goal_periodicity"],
                        row.get("goal_mode", "standard"),
                        goal_scope_branch,
                        next_version,
                        row.get("valid_from"),
                        row.get("valid_to"),
                        row.get("notes"),
                        row["id"],
                        source_year,
                        actor_user_id,
                        None,
                        actor_user_id,
                        None,
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
                self._insert_goal_audit_event(
                    event_type="indicator_goal.created",
                    goal_row=created,
                    payload_before=None,
                    actor_user_id=actor_user_id,
                    audit_origin=audit_origin,
                    correlation_id=correlation_id,
                    audit_meta={"operation": "duplicate_year"},
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
        expected_target_digest: str | None = None,
        expected_source_digest: str | None = None,
        audit_origin: str | None = None,
        correlation_id: str | None = None,
    ) -> dict:
        with self._unit_of_work():
            normalized_ids = [
                str(item).strip() for item in (indicator_ids or []) if str(item).strip()
            ]
            placeholders = ", ".join(["%s"] * len(normalized_ids)) or "NULL"

            # Serialize writers of every touched scope before reading the
            # snapshots the digests will be checked against (sorted → no
            # deadlock; a concurrent writer cannot slip a commit between
            # the lock and the read).
            for indicator_id in sorted(normalized_ids):
                self._lock_goal_scope(
                    indicator_id=indicator_id,
                    goal_year=goal_year,
                    goal_scope_branch="",
                )

            existing_rows = self.fetch_all(
                f"""
                SELECT indicator_id, goal_year, goal_scope_branch
                FROM strategic_indicators.indicator_goals
                WHERE goal_year = %s
                  AND is_active = TRUE
                  AND indicator_id IN ({placeholders})
                ORDER BY indicator_id ASC
                """,
                (goal_year, *normalized_ids),
            )
            existing_ids = {row["indicator_id"] for row in existing_rows}

            source_rows: list[dict] = []
            if copy_from_year is not None and normalized_ids:
                source_rows = self.fetch_all(
                    f"""
                    SELECT DISTINCT ON (indicator_id)
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
                      AND indicator_id IN ({placeholders})
                    ORDER BY indicator_id ASC, version DESC, updated_at DESC
                    """,
                    (copy_from_year, *normalized_ids),
                )
            source_by_indicator = {row["indicator_id"]: row for row in source_rows}

            self._require_bulk_digest(
                expected=expected_target_digest,
                actual_rows=existing_rows,
                fields=self._BULK_EXISTING_DIGEST_FIELDS,
                label="target_existing",
            )
            self._require_bulk_digest(
                expected=expected_source_digest,
                actual_rows=source_rows,
                fields=self._BULK_SOURCE_DIGEST_FIELDS,
                label="source",
            )

            created_items: list[dict] = []

            for indicator_id in normalized_ids:
                if indicator_id in existing_ids:
                    continue

                source = source_by_indicator.get(indicator_id)
                if source is None:
                    continue

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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        indicator_id,
                        goal_year,
                        source["goal_label"],
                        0.0
                        if source.get("goal_mode") == "monthly_curve"
                        else source["goal_value"],
                        source["goal_periodicity"],
                        source.get("goal_mode", "standard"),
                        next_version,
                        source.get("valid_from"),
                        source.get("valid_to"),
                        source.get("notes"),
                        source["id"],
                        copy_from_year,
                        actor_user_id,
                        None,
                        actor_user_id,
                        None,
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
                self._insert_goal_audit_event(
                    event_type="indicator_goal.created",
                    goal_row=created,
                    payload_before=None,
                    actor_user_id=actor_user_id,
                    audit_origin=audit_origin,
                    correlation_id=correlation_id,
                    audit_meta={"operation": "fill_missing"},
                )
                created_items.append(created)

            return {
                "message": "Preenchimento de metas faltantes concluído com sucesso.",
                "items": created_items,
            }

    def list_branch_scoped_goals_ignoring_validity(
        self,
        *,
        indicator_ids: list[str],
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, dict[str, dict]]:
        normalized_ids = [
            str(indicator_id).strip()
            for indicator_id in indicator_ids
            if indicator_id is not None and str(indicator_id).strip()
        ]
        if not normalized_ids:
            return {}

        year = self._resolve_goal_year(
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )
        placeholders = ", ".join("%s" for _ in normalized_ids)
        params: list = [year, *normalized_ids]

        query = f"""
            SELECT
                ig.id,
                ig.indicator_id,
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
                ig.goal_mode,
                ig.goal_scope_branch,
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
              AND ig.goal_scope_branch IN ('01', '02')
              AND ig.indicator_id IN ({placeholders})
        """

        if department_id:
            query += " AND di.department_id = %s"
            params.append(department_id)

        query += """
            ORDER BY
                ig.indicator_id ASC,
                ig.goal_scope_branch ASC,
                ig.version DESC,
                ig.updated_at DESC
        """

        rows = self.fetch_all(query, tuple(params))
        if not rows:
            return {}

        goal_ids = [row["id"] for row in rows]
        monthly_by_goal = self._list_monthly_targets_batch(goal_ids)

        result: dict[str, dict[str, dict]] = {}
        for row in rows:
            indicator_id = row["indicator_id"]
            scope_branch = normalize_goal_scope_branch(row.get("goal_scope_branch"))
            if scope_branch not in {"01", "02"}:
                continue
            if indicator_id not in result:
                result[indicator_id] = {}
            if scope_branch in result[indicator_id]:
                continue

            item = dict(row)
            item["monthly_targets"] = monthly_by_goal.get(row["id"], [])
            result[indicator_id][scope_branch] = item

        return result

    def list_latest_goals_ignoring_validity(
        self,
        *,
        indicator_ids: list[str],
        department_id: str | None = None,
        competence: str | None = None,
        scope_branch: str | None = None,
    ) -> dict[str, dict]:
        normalized_ids = [
            str(indicator_id).strip()
            for indicator_id in indicator_ids
            if indicator_id is not None and str(indicator_id).strip()
        ]
        if not normalized_ids:
            return {}

        year = self._resolve_goal_year(
            competence=competence,
            start_date=None,
            end_date=None,
        ) if competence else None

        placeholders = ", ".join("%s" for _ in normalized_ids)
        params: list = list(normalized_ids)
        scope_filter = self._resolved_goal_scope_filter(
            scope_branch=scope_branch,
            params=params,
        )
        scope_order, scope_order_params = self._resolved_goal_scope_order(
            scope_branch=scope_branch,
        )

        query = f"""
            SELECT DISTINCT ON (ig.indicator_id)
                ig.id,
                ig.indicator_id,
                ig.goal_year,
                ig.goal_label,
                ig.goal_value,
                ig.goal_periodicity,
                ig.goal_mode,
                ig.goal_scope_branch,
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
              {scope_filter}
        """

        if department_id:
            query += " AND di.department_id = %s"
            params.append(department_id)

        if year is not None:
            query += " AND ig.goal_year <= %s"
            params.append(year)

        params.extend(scope_order_params)

        query += f"""
            ORDER BY
                ig.indicator_id,
                ig.goal_year DESC,
                {scope_order}
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