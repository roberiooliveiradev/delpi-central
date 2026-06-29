from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.domain.services.quality_action_plans.five_whys_service import (
    five_whys_json,
    serialize_five_whys_row,
)
from app.domain.services.quality_action_plans.ishikawa_causes_service import (
    ishikawa_causes_json,
    serialize_ishikawa_row,
)
from app.domain.services.quality_action_plans.quality_action_plan_serialization import (
    PLAN_SELECT,
    serialize_plan_row,
    serialize_row,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

from app.domain.services.quality_action_plans.quality_action_plan_sla_service import (
    CRITICAL_STALL_DAYS,
    resolve_action_due_sla,
)


_TERMINAL_PLAN_STATUSES = frozenset({"completed", "cancelled"})
_STALL_DAYS_CRITICAL = CRITICAL_STALL_DAYS


def _optional_actor_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


class PostgresQualityActionPlanRepository(PluginBaseRepository):
    @staticmethod
    def _history_author(
        user_id: str,
        name: str | None = None,
        email: str | None = None,
    ) -> dict[str, str | None]:
        return {
            "created_by": user_id,
            "created_by_name": name,
            "created_by_email": email,
        }

    @staticmethod
    def _audit_author(
        user_id: str,
        name: str | None = None,
        email: str | None = None,
    ) -> dict[str, str | None]:
        return {
            "actor_user_id": user_id,
            "actor_name": name,
            "actor_email": email,
        }

    """Leitura e escrita PAC Qualidade (plugin + agente GPT via api-pac-quality)."""

    def list_plans(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        product_code: str | None = None,
        customer_name: str | None = None,
        owner_user_id: str | None = None,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        department: str | None = None,
        root_cause_category: str | None = None,
        overdue_only: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        filters = ["p.deleted_at IS NULL"]
        params: list[Any] = []

        if status:
            filters.append("p.status = %s")
            params.append(status)
        if severity:
            filters.append("p.severity = %s")
            params.append(severity)
        if product_code:
            filters.append("p.product_code = %s")
            params.append(product_code)
        if customer_name:
            filters.append("p.customer_name ILIKE %s")
            params.append(f"%{customer_name.strip()}%")
        if owner_user_id:
            filters.append("p.owner_user_id = %s")
            params.append(owner_user_id)
        if branch_code:
            filters.append("p.branch_code = %s")
            params.append(branch_code)
        if nonconformity_scope:
            filters.append("p.nonconformity_scope = %s")
            params.append(nonconformity_scope)
        if department:
            filters.append("p.department ILIKE %s")
            params.append(f"%{department.strip()}%")
        if root_cause_category:
            root_term = f"%{root_cause_category.strip()}%"
            filters.append(
                """(
                    p.root_cause_category ILIKE %s
                    OR EXISTS (
                        SELECT 1
                          FROM quality.quality_five_whys fw
                         WHERE fw.plan_id = p.id
                           AND fw.root_cause ILIKE %s
                    )
                )"""
            )
            params.extend([root_term, root_term])
        if overdue_only:
            filters.append("p.status NOT IN ('completed', 'cancelled')")
            filters.append(
                """EXISTS (
                    SELECT 1
                      FROM quality.quality_actions a
                     WHERE a.plan_id = p.id
                       AND a.status NOT IN ('completed', 'cancelled')
                       AND a.due_date < CURRENT_DATE
                )"""
            )

        where_clause = " AND ".join(filters)
        count_row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM quality.quality_action_plans p WHERE {where_clause}",
            tuple(params),
        )
        total = int(count_row["total"]) if count_row else 0
        offset = max(page - 1, 0) * page_size

        rows = self.fetch_all(
            f"""
            {PLAN_SELECT}
             WHERE {where_clause}
             ORDER BY p.created_at DESC
             LIMIT %s OFFSET %s
            """,
            tuple([*params, page_size, offset]),
        )

        return {
            "items": [serialize_plan_row(row) for row in rows],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1),
            },
        }

    def get_plan_detail(self, plan_id: str) -> dict[str, Any] | None:
        plan_row = self.fetch_one(
            f"""
            {PLAN_SELECT}
             WHERE p.id = %s AND p.deleted_at IS NULL
            """,
            (plan_id,),
        )
        if not plan_row:
            return None

        ishikawa = self.fetch_one(
            """
            SELECT id, plan_id, machine, method_process, material, manpower,
                   measurement, environment, notes, created_at, updated_at
              FROM quality.quality_ishikawa_analysis WHERE plan_id = %s
            """,
            (plan_id,),
        )
        five_whys = self.fetch_one(
            """
            SELECT id, plan_id, occurrence_whys, detection_whys,
                   root_cause, confidence_level, created_at, updated_at
              FROM quality.quality_five_whys WHERE plan_id = %s
            """,
            (plan_id,),
        )
        actions = self.fetch_all(
            """
            SELECT id, plan_id, action_type, description, responsible_user_id,
                   responsible_name, department, due_date, status,
                   evidence_required, cause_track, completed_at, created_at, updated_at
              FROM quality.quality_actions
             WHERE plan_id = %s
             ORDER BY due_date NULLS LAST, created_at ASC
            """,
            (plan_id,),
        )
        team_members = self.fetch_all(
            """
            SELECT id, plan_id, member_name, member_user_id, department, is_leader, sort_order, created_at
              FROM quality.quality_analysis_team_members
             WHERE plan_id = %s
             ORDER BY is_leader DESC, sort_order ASC, created_at ASC
            """,
            (plan_id,),
        )
        evidences = self.fetch_all(
            """
            SELECT id, plan_id, type, file_name, file_url, text_excerpt,
                   stored_name, mime_type, size_bytes, section, description,
                   knowledge_visible, uploaded_by, uploaded_by_name, uploaded_by_email,
                   action_id, created_at
              FROM quality.quality_problem_evidences
             WHERE plan_id = %s
             ORDER BY created_at DESC
            """,
            (plan_id,),
        )
        history = self.fetch_all(
            """
            SELECT id, plan_id, event_type, old_value, new_value, comment,
                   created_by, created_by_name, created_by_email, created_at
              FROM quality.quality_action_history
             WHERE plan_id = %s
             ORDER BY created_at DESC
             LIMIT 100
            """,
            (plan_id,),
        )

        return {
            "plan": serialize_plan_row(plan_row),
            "ishikawa": serialize_ishikawa_row(ishikawa),
            "five_whys": serialize_five_whys_row(five_whys),
            "team_members": [
                serialize_row(row, id_keys=("id", "plan_id")) for row in team_members if row
            ],
            "evidences": [
                serialize_row(row, id_keys=("id", "plan_id", "action_id")) for row in evidences if row
            ],
            "actions": [
                serialize_row(row, id_keys=("id", "plan_id")) for row in actions if row
            ],
            "history": [
                serialize_row(row, id_keys=("id", "plan_id")) for row in history if row
            ],
        }

    def get_dashboard_summary(
        self,
        *,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        months: int = 12,
    ) -> dict[str, Any]:
        branch_filter = ""
        scope_filter = ""
        params: list[Any] = []
        if branch_code:
            branch_filter = " AND branch_code = %s"
            params.append(branch_code)
        if nonconformity_scope:
            scope_filter = " AND nonconformity_scope = %s"
            params.append(nonconformity_scope)

        row = self.fetch_one(
            f"""
            SELECT
                COUNT(*) FILTER (
                    WHERE status NOT IN ('completed', 'cancelled')
                ) AS open_plans,
                COUNT(*) FILTER (
                    WHERE status NOT IN ('completed', 'cancelled')
                      AND severity = 'critical'
                ) AS critical_open,
                COUNT(*) FILTER (
                    WHERE status = 'waiting_validation'
                ) AS waiting_validation,
                COUNT(*) FILTER (
                    WHERE status = 'completed'
                      AND closed_at >= date_trunc('month', NOW())
                ) AS completed_this_month,
                COUNT(*) FILTER (
                    WHERE status NOT IN ('completed', 'cancelled')
                      AND nonconformity_scope = 'internal'
                ) AS open_internal,
                COUNT(*) FILTER (
                    WHERE status NOT IN ('completed', 'cancelled')
                      AND nonconformity_scope = 'external'
                ) AS open_external
              FROM quality.quality_action_plans
             WHERE deleted_at IS NULL
               {branch_filter}
               {scope_filter}
            """,
            tuple(params),
        )
        overdue_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS overdue_actions
              FROM quality.quality_actions a
              JOIN quality.quality_action_plans p ON p.id = a.plan_id
             WHERE p.deleted_at IS NULL
               AND a.status NOT IN ('completed', 'cancelled')
               AND a.due_date < CURRENT_DATE
               {branch_filter.replace("branch_code", "p.branch_code") if branch_filter else ""}
               {scope_filter.replace("nonconformity_scope", "p.nonconformity_scope") if scope_filter else ""}
            """,
            tuple(params),
        )
        overdue_plans_row = self.fetch_one(
            f"""
            SELECT COUNT(DISTINCT p.id) AS overdue_plans
              FROM quality.quality_action_plans p
              JOIN quality.quality_actions a ON a.plan_id = p.id
             WHERE p.deleted_at IS NULL
               AND p.status NOT IN ('completed', 'cancelled')
               AND a.status NOT IN ('completed', 'cancelled')
               AND a.due_date < CURRENT_DATE
               {branch_filter.replace("branch_code", "p.branch_code") if branch_filter else ""}
               {scope_filter.replace("nonconformity_scope", "p.nonconformity_scope") if scope_filter else ""}
            """,
            tuple(params),
        )
        result = {
            "open_plans": int((row or {}).get("open_plans") or 0),
            "critical_open": int((row or {}).get("critical_open") or 0),
            "waiting_validation": int((row or {}).get("waiting_validation") or 0),
            "completed_this_month": int((row or {}).get("completed_this_month") or 0),
            "overdue_actions": int((overdue_row or {}).get("overdue_actions") or 0),
            "overdue_plans": int((overdue_plans_row or {}).get("overdue_plans") or 0),
            "open_internal": int((row or {}).get("open_internal") or 0),
            "open_external": int((row or {}).get("open_external") or 0),
        }
        if branch_code:
            result["branch_code"] = branch_code
        if nonconformity_scope:
            result["nonconformity_scope"] = nonconformity_scope
        if branch_code or nonconformity_scope:
            result["timing"] = self._fetch_timing_kpis(
                branch_code=branch_code,
                nonconformity_scope=nonconformity_scope,
                months=months,
            )
            result["breakdowns"] = self._fetch_breakdowns(
                branch_code=branch_code,
                nonconformity_scope=nonconformity_scope,
                months=months,
            )
            result["rankings"] = self._fetch_rankings(
                branch_code=branch_code,
                nonconformity_scope=nonconformity_scope,
                months=months,
            )
            result["recurrence_alert"] = self._fetch_recurrence_alert(
                branch_code=branch_code,
                nonconformity_scope=nonconformity_scope,
                months=months,
            )
            result["effectiveness_by_action_type"] = self._fetch_effectiveness_by_action_type(
                branch_code=branch_code,
                nonconformity_scope=nonconformity_scope,
                months=months,
            )
            result["stalled_alert"] = self._fetch_stalled_alert(
                branch_code=branch_code,
                nonconformity_scope=nonconformity_scope,
            )
            result["effectiveness_pending_alert"] = self._fetch_effectiveness_pending_alert(
                branch_code=branch_code,
                nonconformity_scope=nonconformity_scope,
            )
            return result

        by_branch_rows = self.fetch_all(
            """
            SELECT branch_code,
                   COUNT(*) FILTER (
                       WHERE status NOT IN ('completed', 'cancelled')
                   ) AS open_plans,
                   COUNT(*) FILTER (
                       WHERE status NOT IN ('completed', 'cancelled')
                         AND severity = 'critical'
                   ) AS critical_open
              FROM quality.quality_action_plans
             WHERE deleted_at IS NULL
               AND branch_code IS NOT NULL
             GROUP BY branch_code
             ORDER BY branch_code
            """
        )
        result["by_branch"] = [
            {
                "branch_code": row["branch_code"],
                "open_plans": int(row.get("open_plans") or 0),
                "critical_open": int(row.get("critical_open") or 0),
            }
            for row in by_branch_rows
            if row.get("branch_code")
        ]
        by_scope_rows = self.fetch_all(
            """
            SELECT nonconformity_scope,
                   COUNT(*) FILTER (
                       WHERE status NOT IN ('completed', 'cancelled')
                   ) AS open_plans,
                   COUNT(*) FILTER (
                       WHERE status NOT IN ('completed', 'cancelled')
                         AND severity = 'critical'
                   ) AS critical_open
              FROM quality.quality_action_plans
             WHERE deleted_at IS NULL
             GROUP BY nonconformity_scope
             ORDER BY nonconformity_scope
            """
        )
        result["by_scope"] = [
            {
                "nonconformity_scope": row["nonconformity_scope"],
                "open_plans": int(row.get("open_plans") or 0),
                "critical_open": int(row.get("critical_open") or 0),
            }
            for row in by_scope_rows
            if row.get("nonconformity_scope")
        ]
        result["timing"] = self._fetch_timing_kpis(
            branch_code=branch_code,
            nonconformity_scope=nonconformity_scope,
            months=months,
        )
        result["breakdowns"] = self._fetch_breakdowns(
            branch_code=branch_code,
            nonconformity_scope=nonconformity_scope,
            months=months,
        )
        result["rankings"] = self._fetch_rankings(
            branch_code=branch_code,
            nonconformity_scope=nonconformity_scope,
            months=months,
        )
        result["recurrence_alert"] = self._fetch_recurrence_alert(
            branch_code=branch_code,
            nonconformity_scope=nonconformity_scope,
            months=months,
        )
        result["effectiveness_by_action_type"] = self._fetch_effectiveness_by_action_type(
            branch_code=branch_code,
            nonconformity_scope=nonconformity_scope,
            months=months,
        )
        result["stalled_alert"] = self._fetch_stalled_alert(
            branch_code=branch_code,
            nonconformity_scope=nonconformity_scope,
        )
        result["effectiveness_pending_alert"] = self._fetch_effectiveness_pending_alert(
            branch_code=branch_code,
            nonconformity_scope=nonconformity_scope,
        )
        return result

    def _fetch_timing_kpis(
        self,
        *,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        months: int = 12,
    ) -> dict[str, Any]:
        filters = ["deleted_at IS NULL"]
        params: list[Any] = [months, months, months, months]
        if branch_code:
            filters.append("branch_code = %s")
            params.append(branch_code)
        if nonconformity_scope:
            filters.append("nonconformity_scope = %s")
            params.append(nonconformity_scope)
        where_clause = " AND ".join(filters)

        row = self.fetch_one(
            f"""
            SELECT
                AVG(
                    EXTRACT(EPOCH FROM (closed_at - COALESCE(detected_at, created_at)))
                    / 86400.0
                ) FILTER (
                    WHERE status = 'completed'
                      AND closed_at IS NOT NULL
                      AND closed_at >= NOW() - make_interval(months => %s)
                ) AS avg_closure_days,
                COUNT(*) FILTER (
                    WHERE status = 'completed'
                      AND closed_at IS NOT NULL
                      AND closed_at >= NOW() - make_interval(months => %s)
                ) AS closure_sample_size,
                AVG(
                    EXTRACT(
                        EPOCH FROM (
                            effectiveness_verified_at - COALESCE(detected_at, created_at)
                        )
                    ) / 86400.0
                ) FILTER (
                    WHERE effectiveness_verified_at IS NOT NULL
                      AND effectiveness_verified_at >= NOW() - make_interval(months => %s)
                ) AS avg_time_to_effectiveness_days,
                COUNT(*) FILTER (
                    WHERE effectiveness_verified_at IS NOT NULL
                      AND effectiveness_verified_at >= NOW() - make_interval(months => %s)
                ) AS effectiveness_sample_size
              FROM quality.quality_action_plans
             WHERE {where_clause}
            """,
            tuple(params),
        )

        avg_closure = row.get("avg_closure_days") if row else None
        avg_effectiveness = row.get("avg_time_to_effectiveness_days") if row else None

        return {
            "window_months": months,
            "avg_closure_days": (
                round(float(avg_closure), 1) if avg_closure is not None else None
            ),
            "closure_sample_size": int((row or {}).get("closure_sample_size") or 0),
            "avg_time_to_effectiveness_days": (
                round(float(avg_effectiveness), 1)
                if avg_effectiveness is not None
                else None
            ),
            "effectiveness_sample_size": int(
                (row or {}).get("effectiveness_sample_size") or 0
            ),
        }

    def _fetch_breakdowns(
        self,
        *,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        months: int = 12,
        limit: int = 8,
    ) -> dict[str, Any]:
        plan_filters = ["p.deleted_at IS NULL", "p.created_at >= NOW() - make_interval(months => %s)"]
        plan_params: list[Any] = [months]
        if branch_code:
            plan_filters.append("p.branch_code = %s")
            plan_params.append(branch_code)
        if nonconformity_scope:
            plan_filters.append("p.nonconformity_scope = %s")
            plan_params.append(nonconformity_scope)
        plan_where = " AND ".join(plan_filters)

        root_cause_rows = self.fetch_all(
            f"""
            SELECT
                COALESCE(
                    NULLIF(trim(p.root_cause_category), ''),
                    NULLIF(trim(fw.root_cause), ''),
                    'Não informada'
                ) AS label,
                COUNT(*)::int AS total
              FROM quality.quality_action_plans p
              LEFT JOIN quality.quality_five_whys fw ON fw.plan_id = p.id
             WHERE {plan_where}
             GROUP BY 1
             ORDER BY total DESC, label ASC
             LIMIT %s
            """,
            tuple([*plan_params, limit]),
        )

        failure_mode_rows = self.fetch_all(
            f"""
            SELECT
                COALESCE(NULLIF(trim(p.failure_mode), ''), 'Não informado') AS label,
                COUNT(*)::int AS total
              FROM quality.quality_action_plans p
             WHERE {plan_where}
             GROUP BY 1
             ORDER BY total DESC, label ASC
             LIMIT %s
            """,
            tuple([*plan_params, limit]),
        )

        action_filters = [
            "p.deleted_at IS NULL",
            "a.created_at >= NOW() - make_interval(months => %s)",
        ]
        action_params: list[Any] = [months]
        if branch_code:
            action_filters.append("p.branch_code = %s")
            action_params.append(branch_code)
        if nonconformity_scope:
            action_filters.append("p.nonconformity_scope = %s")
            action_params.append(nonconformity_scope)
        action_where = " AND ".join(action_filters)

        action_type_rows = self.fetch_all(
            f"""
            SELECT a.action_type AS label, COUNT(*)::int AS total
              FROM quality.quality_actions a
              JOIN quality.quality_action_plans p ON p.id = a.plan_id
             WHERE {action_where}
             GROUP BY a.action_type
             ORDER BY total DESC, label ASC
             LIMIT %s
            """,
            tuple([*action_params, limit]),
        )

        return {
            "window_months": months,
            "by_root_cause": [
                {"label": row["label"], "total": int(row["total"])} for row in root_cause_rows
            ],
            "by_failure_mode": [
                {"label": row["label"], "total": int(row["total"])} for row in failure_mode_rows
            ],
            "by_action_type": [
                {"label": row["label"], "total": int(row["total"])} for row in action_type_rows
            ],
        }

    def _fetch_rankings(
        self,
        *,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        months: int = 12,
        limit: int = 8,
    ) -> dict[str, Any]:
        plan_filters = ["p.deleted_at IS NULL", "p.created_at >= NOW() - make_interval(months => %s)"]
        plan_params: list[Any] = [months]
        if branch_code:
            plan_filters.append("p.branch_code = %s")
            plan_params.append(branch_code)
        if nonconformity_scope:
            plan_filters.append("p.nonconformity_scope = %s")
            plan_params.append(nonconformity_scope)
        plan_where = " AND ".join(plan_filters)

        def _map_ranking_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            return [
                {
                    "label": row["label"],
                    "total": int(row["total"]),
                    "open_plans": int(row.get("open_plans") or 0),
                }
                for row in rows
            ]

        customer_rows = self.fetch_all(
            f"""
            SELECT
                COALESCE(NULLIF(trim(p.customer_name), ''), 'Sem cliente') AS label,
                COUNT(*)::int AS total,
                COUNT(*) FILTER (
                    WHERE p.status NOT IN ('completed', 'cancelled')
                )::int AS open_plans
              FROM quality.quality_action_plans p
             WHERE {plan_where}
             GROUP BY 1
             ORDER BY total DESC, open_plans DESC, label ASC
             LIMIT %s
            """,
            tuple([*plan_params, limit]),
        )

        product_rows = self.fetch_all(
            f"""
            SELECT
                COALESCE(NULLIF(trim(p.product_code), ''), 'Sem produto') AS label,
                COUNT(*)::int AS total,
                COUNT(*) FILTER (
                    WHERE p.status NOT IN ('completed', 'cancelled')
                )::int AS open_plans
              FROM quality.quality_action_plans p
             WHERE {plan_where}
             GROUP BY 1
             ORDER BY total DESC, open_plans DESC, label ASC
             LIMIT %s
            """,
            tuple([*plan_params, limit]),
        )

        owner_rows = self.fetch_all(
            f"""
            SELECT
                COALESCE(NULLIF(trim(p.owner_user_id), ''), 'Sem responsável') AS label,
                COUNT(*)::int AS total,
                COUNT(*) FILTER (
                    WHERE p.status NOT IN ('completed', 'cancelled')
                )::int AS open_plans
              FROM quality.quality_action_plans p
             WHERE {plan_where}
             GROUP BY 1
             ORDER BY total DESC, open_plans DESC, label ASC
             LIMIT %s
            """,
            tuple([*plan_params, limit]),
        )

        return {
            "window_months": months,
            "by_customer": _map_ranking_rows(customer_rows),
            "by_product": _map_ranking_rows(product_rows),
            "by_owner": _map_ranking_rows(owner_rows),
        }

    def _fetch_recurrence_alert(
        self,
        *,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        months: int = 12,
        limit: int = 5,
    ) -> dict[str, Any]:
        filters = ["p.deleted_at IS NULL", "p.recurrence_key IS NOT NULL"]
        filter_params: list[Any] = []
        if branch_code:
            filters.append("p.branch_code = %s")
            filter_params.append(branch_code)
        if nonconformity_scope:
            filters.append("p.nonconformity_scope = %s")
            filter_params.append(nonconformity_scope)
        where_clause = " AND ".join(filters)
        # Placeholders aparecem na ordem: janela no SELECT, filtros no WHERE, janela no HAVING.
        summary_params = [months, *filter_params, months]
        top_params = [months, *filter_params, months, limit]

        summary_row = self.fetch_one(
            f"""
            WITH grouped AS (
                SELECT p.recurrence_key,
                       COUNT(*) FILTER (
                           WHERE p.created_at >= NOW() - make_interval(months => %s)
                       )::int AS plans_in_window,
                       COUNT(*)::int AS total_plans,
                       COUNT(*) FILTER (
                           WHERE p.status NOT IN ('completed', 'cancelled')
                       )::int AS open_plans
                  FROM quality.quality_action_plans p
                 WHERE {where_clause}
                 GROUP BY p.recurrence_key
                HAVING COUNT(*) FILTER (
                           WHERE p.created_at >= NOW() - make_interval(months => %s)
                       ) >= 2
            )
            SELECT COUNT(*)::int AS groups_detected,
                   COALESCE(SUM(plans_in_window), 0)::int AS plans_in_window,
                   COALESCE(SUM(open_plans), 0)::int AS open_plans_in_recurrence
              FROM grouped
            """,
            tuple(summary_params),
        )

        top_rows = self.fetch_all(
            f"""
            SELECT p.recurrence_key,
                   COUNT(*) FILTER (
                       WHERE p.created_at >= NOW() - make_interval(months => %s)
                   )::int AS plans_in_window,
                   COUNT(*)::int AS total_plans,
                   COUNT(*) FILTER (
                       WHERE p.status NOT IN ('completed', 'cancelled')
                   )::int AS open_plans,
                   (array_agg(p.product_code ORDER BY p.created_at DESC))[1] AS product_code,
                   (array_agg(p.failure_mode ORDER BY p.created_at DESC))[1] AS failure_mode,
                   (array_agg(p.branch_code ORDER BY p.created_at DESC))[1] AS branch_code
              FROM quality.quality_action_plans p
             WHERE {where_clause}
             GROUP BY p.recurrence_key
            HAVING COUNT(*) FILTER (
                       WHERE p.created_at >= NOW() - make_interval(months => %s)
                   ) >= 2
             ORDER BY plans_in_window DESC, open_plans DESC, total_plans DESC
             LIMIT %s
            """,
            tuple(top_params),
        )

        return {
            "window_months": months,
            "groups_detected": int((summary_row or {}).get("groups_detected") or 0),
            "plans_in_window": int((summary_row or {}).get("plans_in_window") or 0),
            "open_plans_in_recurrence": int(
                (summary_row or {}).get("open_plans_in_recurrence") or 0
            ),
            "top_groups": [
                {
                    "recurrence_key": row["recurrence_key"],
                    "product_code": row.get("product_code"),
                    "failure_mode": row.get("failure_mode"),
                    "branch_code": row.get("branch_code"),
                    "plans_in_window": int(row.get("plans_in_window") or 0),
                    "total_plans": int(row.get("total_plans") or 0),
                    "open_plans": int(row.get("open_plans") or 0),
                }
                for row in top_rows
            ],
        }

    def _fetch_stalled_alert(
        self,
        *,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        stall_days: int = _STALL_DAYS_CRITICAL,
        limit: int = 8,
    ) -> dict[str, Any]:
        filters = [
            "p.deleted_at IS NULL",
            "p.status NOT IN ('completed', 'cancelled')",
            "p.severity = 'critical'",
            "p.updated_at < NOW() - make_interval(days => %s)",
        ]
        params: list[Any] = [stall_days]
        if branch_code:
            filters.append("p.branch_code = %s")
            params.append(branch_code)
        if nonconformity_scope:
            filters.append("p.nonconformity_scope = %s")
            params.append(nonconformity_scope)
        where_clause = " AND ".join(filters)

        summary_row = self.fetch_one(
            f"""
            SELECT COUNT(*)::int AS stalled_plans
              FROM quality.quality_action_plans p
             WHERE {where_clause}
            """,
            tuple(params),
        )

        top_rows = self.fetch_all(
            f"""
            SELECT p.id,
                   p.code,
                   p.title,
                   p.branch_code,
                   p.status,
                   p.updated_at,
                   EXTRACT(
                       DAY FROM (NOW() - p.updated_at)
                   )::int AS days_without_update
              FROM quality.quality_action_plans p
             WHERE {where_clause}
             ORDER BY p.updated_at ASC, p.code ASC
             LIMIT %s
            """,
            tuple([*params, limit]),
        )

        return {
            "stall_days": stall_days,
            "severity": "critical",
            "stalled_plans": int((summary_row or {}).get("stalled_plans") or 0),
            "top_plans": [
                {
                    "id": str(row["id"]),
                    "code": row.get("code"),
                    "title": row.get("title"),
                    "branch_code": row.get("branch_code"),
                    "status": row.get("status"),
                    "updated_at": (
                        row["updated_at"].isoformat()
                        if isinstance(row.get("updated_at"), datetime)
                        else row.get("updated_at")
                    ),
                    "days_without_update": int(row.get("days_without_update") or 0),
                }
                for row in top_rows
            ],
        }

    def _fetch_effectiveness_pending_alert(
        self,
        *,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        limit: int = 8,
    ) -> dict[str, Any]:
        filters = [
            "p.deleted_at IS NULL",
            "p.effectiveness_approval_status = 'pending_review'",
        ]
        params: list[Any] = []
        if branch_code:
            filters.append("p.branch_code = %s")
            params.append(branch_code)
        if nonconformity_scope:
            filters.append("p.nonconformity_scope = %s")
            params.append(nonconformity_scope)
        where_clause = " AND ".join(filters)

        summary_row = self.fetch_one(
            f"""
            SELECT COUNT(*)::int AS pending_plans
              FROM quality.quality_action_plans p
             WHERE {where_clause}
            """,
            tuple(params),
        )

        top_rows = self.fetch_all(
            f"""
            SELECT p.id,
                   p.code,
                   p.title,
                   p.branch_code,
                   p.severity,
                   p.effectiveness_proposed_status,
                   p.effectiveness_submitted_at,
                   p.effectiveness_submitted_by
              FROM quality.quality_action_plans p
             WHERE {where_clause}
             ORDER BY p.effectiveness_submitted_at ASC NULLS LAST, p.code ASC
             LIMIT %s
            """,
            tuple([*params, limit]),
        )

        return {
            "pending_plans": int((summary_row or {}).get("pending_plans") or 0),
            "top_plans": [
                {
                    "id": str(row["id"]),
                    "code": row.get("code"),
                    "title": row.get("title"),
                    "branch_code": row.get("branch_code"),
                    "severity": row.get("severity"),
                    "effectiveness_proposed_status": row.get("effectiveness_proposed_status"),
                    "effectiveness_submitted_at": (
                        row["effectiveness_submitted_at"].isoformat()
                        if isinstance(row.get("effectiveness_submitted_at"), datetime)
                        else row.get("effectiveness_submitted_at")
                    ),
                    "effectiveness_submitted_by": row.get("effectiveness_submitted_by"),
                }
                for row in top_rows
            ],
        }

    def _fetch_effectiveness_by_action_type(
        self,
        *,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        months: int = 12,
    ) -> dict[str, Any]:
        plan_filters = [
            "p.deleted_at IS NULL",
            "p.effectiveness_verified_at IS NOT NULL",
            "p.effectiveness_verified_at >= NOW() - make_interval(months => %s)",
            "p.effectiveness_status NOT IN ('pending', 'not_verified')",
        ]
        plan_params: list[Any] = [months]
        if branch_code:
            plan_filters.append("p.branch_code = %s")
            plan_params.append(branch_code)
        if nonconformity_scope:
            plan_filters.append("p.nonconformity_scope = %s")
            plan_params.append(nonconformity_scope)
        plan_where = " AND ".join(plan_filters)

        overall_row = self.fetch_one(
            f"""
            SELECT COUNT(*)::int AS reviewed_plans,
                   COUNT(*) FILTER (
                       WHERE p.effectiveness_status = 'effective'
                   )::int AS effective_plans,
                   COUNT(*) FILTER (
                       WHERE p.effectiveness_status = 'partially_effective'
                   )::int AS partially_effective_plans,
                   COUNT(*) FILTER (
                       WHERE p.effectiveness_status = 'ineffective'
                   )::int AS ineffective_plans
              FROM quality.quality_action_plans p
             WHERE {plan_where}
            """,
            tuple(plan_params),
        )

        action_rows = self.fetch_all(
            f"""
            SELECT a.action_type,
                   COUNT(DISTINCT p.id)::int AS reviewed_plans,
                   COUNT(DISTINCT p.id) FILTER (
                       WHERE p.effectiveness_status = 'effective'
                   )::int AS effective_plans,
                   COUNT(DISTINCT p.id) FILTER (
                       WHERE p.effectiveness_status = 'partially_effective'
                   )::int AS partially_effective_plans,
                   COUNT(DISTINCT p.id) FILTER (
                       WHERE p.effectiveness_status = 'ineffective'
                   )::int AS ineffective_plans
              FROM quality.quality_action_plans p
              JOIN quality.quality_actions a ON a.plan_id = p.id
             WHERE {plan_where}
             GROUP BY a.action_type
             ORDER BY reviewed_plans DESC, a.action_type ASC
            """,
            tuple(plan_params),
        )

        def _map_bucket(row: dict[str, Any] | None) -> dict[str, Any]:
            reviewed = int((row or {}).get("reviewed_plans") or 0)
            effective = int((row or {}).get("effective_plans") or 0)
            return {
                "reviewed_plans": reviewed,
                "effective_plans": effective,
                "partially_effective_plans": int(
                    (row or {}).get("partially_effective_plans") or 0
                ),
                "ineffective_plans": int((row or {}).get("ineffective_plans") or 0),
                "effectiveness_rate": (
                    round(100.0 * effective / reviewed, 1) if reviewed else None
                ),
            }

        return {
            "window_months": months,
            "overall": _map_bucket(overall_row),
            "by_action_type": [
                {
                    "action_type": row["action_type"],
                    **_map_bucket(row),
                }
                for row in action_rows
            ],
        }

    def list_overdue_plans(
        self,
        *,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        branch_filter = ""
        scope_filter = ""
        params: list[Any] = []
        if branch_code:
            branch_filter = " AND p.branch_code = %s"
            params.append(branch_code)
        if nonconformity_scope:
            scope_filter = " AND p.nonconformity_scope = %s"
            params.append(nonconformity_scope)

        count_row = self.fetch_one(
            f"""
            SELECT COUNT(DISTINCT p.id) AS total
              FROM quality.quality_action_plans p
              JOIN quality.quality_actions a ON a.plan_id = p.id
             WHERE p.deleted_at IS NULL
               AND p.status NOT IN ('completed', 'cancelled')
               AND a.status NOT IN ('completed', 'cancelled')
               AND a.due_date < CURRENT_DATE
               {branch_filter}
               {scope_filter}
            """,
            tuple(params),
        )
        total = int((count_row or {}).get("total") or 0)
        offset = max(page - 1, 0) * page_size
        rows = self.fetch_all(
            f"""
            SELECT DISTINCT ON (p.id)
                   p.id, p.code, p.title, p.customer_name, p.product_code,
                   p.branch_code, p.nonconformity_scope, p.severity, p.status,
                   p.owner_user_id, p.created_at, p.updated_at
              FROM quality.quality_action_plans p
              JOIN quality.quality_actions a ON a.plan_id = p.id
             WHERE p.deleted_at IS NULL
               AND p.status NOT IN ('completed', 'cancelled')
               AND a.status NOT IN ('completed', 'cancelled')
               AND a.due_date < CURRENT_DATE
               {branch_filter}
               {scope_filter}
             ORDER BY p.id, p.updated_at DESC
             LIMIT %s OFFSET %s
            """,
            tuple([*params, page_size, offset]),
        )
        items = []
        for row in rows:
            item = serialize_row(row, id_keys=("id",))
            if item:
                items.append(item)
        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1),
            },
        }

    def list_my_queue(
        self,
        *,
        user_id: str,
        branch_code: str | None = None,
        overdue_only: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        filters = [
            "p.deleted_at IS NULL",
            "p.status NOT IN ('completed', 'cancelled')",
            "a.status NOT IN ('completed', 'cancelled')",
            "a.responsible_user_id = %s",
        ]
        params: list[Any] = [user_id]
        if branch_code:
            filters.append("p.branch_code = %s")
            params.append(branch_code)
        if overdue_only:
            filters.append("a.due_date < CURRENT_DATE")
        where_clause = " AND ".join(filters)

        summary_row = self.fetch_one(
            f"""
            SELECT COUNT(*)::int AS open_actions,
                   COUNT(*) FILTER (
                       WHERE a.due_date IS NOT NULL AND a.due_date < CURRENT_DATE
                   )::int AS overdue_actions
              FROM quality.quality_actions a
              JOIN quality.quality_action_plans p ON p.id = a.plan_id
             WHERE {where_clause}
            """,
            tuple(params),
        )

        count_row = self.fetch_one(
            f"""
            SELECT COUNT(*)::int AS total
              FROM quality.quality_actions a
              JOIN quality.quality_action_plans p ON p.id = a.plan_id
             WHERE {where_clause}
            """,
            tuple(params),
        )
        total = int((count_row or {}).get("total") or 0)
        offset = max(page - 1, 0) * page_size

        rows = self.fetch_all(
            f"""
            SELECT a.id AS action_id,
                   a.plan_id,
                   a.action_type,
                   a.description,
                   a.responsible_user_id,
                   a.responsible_name,
                   a.department,
                   a.due_date,
                   a.status AS action_status,
                   (a.due_date IS NOT NULL AND a.due_date < CURRENT_DATE) AS is_overdue,
                   p.code AS plan_code,
                   p.title AS plan_title,
                   p.status AS plan_status,
                   p.severity AS plan_severity,
                   p.branch_code,
                   p.nonconformity_scope,
                   p.customer_name,
                   p.product_code
              FROM quality.quality_actions a
              JOIN quality.quality_action_plans p ON p.id = a.plan_id
             WHERE {where_clause}
             ORDER BY is_overdue DESC,
                      a.due_date NULLS LAST,
                      a.created_at ASC
             LIMIT %s OFFSET %s
            """,
            tuple([*params, page_size, offset]),
        )

        items: list[dict[str, Any]] = []
        for row in rows:
            due_date = row.get("due_date")
            due_date_value = (
                due_date.isoformat() if hasattr(due_date, "isoformat") else due_date
            )
            is_overdue = bool(row.get("is_overdue"))
            due_sla = resolve_action_due_sla(due_date=due_date, is_overdue=is_overdue)
            items.append(
                {
                    "action_id": str(row["action_id"]),
                    "plan_id": str(row["plan_id"]),
                    "action_type": row.get("action_type"),
                    "description": row.get("description"),
                    "responsible_user_id": row.get("responsible_user_id"),
                    "responsible_name": row.get("responsible_name"),
                    "department": row.get("department"),
                    "due_date": due_date_value,
                    "action_status": row.get("action_status"),
                    "is_overdue": is_overdue,
                    "is_due_soon": due_sla["due_sla_level"] == "due_soon",
                    "days_until_due": due_sla["days_until_due"],
                    "due_sla_level": due_sla["due_sla_level"],
                    "plan_code": row.get("plan_code"),
                    "plan_title": row.get("plan_title"),
                    "plan_status": row.get("plan_status"),
                    "plan_severity": row.get("plan_severity"),
                    "branch_code": row.get("branch_code"),
                    "nonconformity_scope": row.get("nonconformity_scope"),
                    "customer_name": row.get("customer_name"),
                    "product_code": row.get("product_code"),
                }
            )

        return {
            "user_id": user_id,
            "summary": {
                "open_actions": int((summary_row or {}).get("open_actions") or 0),
                "overdue_actions": int((summary_row or {}).get("overdue_actions") or 0),
            },
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1),
            },
        }

    def list_actions_due_within_days(self, *, days_ahead: int = 2) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT a.id AS action_id,
                   a.plan_id,
                   a.description,
                   a.due_date,
                   a.responsible_user_id,
                   p.code AS plan_code,
                   p.title AS plan_title
              FROM quality.quality_actions a
              JOIN quality.quality_action_plans p ON p.id = a.plan_id
             WHERE p.deleted_at IS NULL
               AND a.status NOT IN ('completed', 'cancelled')
               AND a.due_date IS NOT NULL
               AND a.due_date > CURRENT_DATE
               AND a.due_date <= CURRENT_DATE + make_interval(days => %s)
               AND a.responsible_user_id IS NOT NULL
               AND trim(a.responsible_user_id) <> ''
             ORDER BY a.due_date ASC, p.code ASC
            """,
            (days_ahead,),
        )
        result: list[dict[str, Any]] = []
        for row in rows:
            due_date = row.get("due_date")
            result.append(
                {
                    "action_id": str(row["action_id"]),
                    "plan_id": str(row["plan_id"]),
                    "description": row.get("description"),
                    "due_date": due_date,
                    "responsible_user_id": row.get("responsible_user_id"),
                    "plan_code": row.get("plan_code"),
                    "plan_title": row.get("plan_title"),
                }
            )
        return result

    def list_stalled_critical_plans(self, *, stall_days: int = 7) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT p.id,
                   p.code,
                   p.title,
                   p.owner_user_id,
                   p.status,
                   p.updated_at,
                   EXTRACT(DAY FROM (NOW() - p.updated_at))::int AS days_without_update
              FROM quality.quality_action_plans p
             WHERE p.deleted_at IS NULL
               AND p.status NOT IN ('completed', 'cancelled')
               AND p.severity = 'critical'
               AND p.updated_at < NOW() - make_interval(days => %s)
             ORDER BY p.updated_at ASC, p.code ASC
            """,
            (stall_days,),
        )
        return [
            {
                "id": str(row["id"]),
                "code": row.get("code"),
                "title": row.get("title"),
                "owner_user_id": row.get("owner_user_id"),
                "status": row.get("status"),
                "updated_at": row.get("updated_at"),
                "days_without_update": int(row.get("days_without_update") or 0),
            }
            for row in rows
        ]

    def notification_already_sent(self, notification_key: str) -> bool:
        row = self.fetch_one(
            """
            SELECT 1 AS found
              FROM quality.quality_notification_dispatches
             WHERE notification_key = %s
            """,
            (notification_key,),
        )
        return row is not None

    def record_notification_dispatch(
        self,
        *,
        notification_key: str,
        event_type: str,
        recipient_user_id: str | None,
        entity_type: str | None,
        entity_id: str | None,
    ) -> None:
        self.execute(
            """
            INSERT INTO quality.quality_notification_dispatches (
                notification_key, event_type, recipient_user_id, entity_type, entity_id
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (notification_key) DO NOTHING
            """,
            (
                notification_key,
                event_type,
                recipient_user_id,
                entity_type,
                entity_id,
            ),
        )

    def list_recurrence_groups(
        self,
        *,
        branch_code: str | None = None,
        nonconformity_scope: str | None = None,
        min_plans: int = 2,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        filters = ["p.deleted_at IS NULL", "p.recurrence_key IS NOT NULL"]
        params: list[Any] = []
        if branch_code:
            filters.append("p.branch_code = %s")
            params.append(branch_code)
        if nonconformity_scope:
            filters.append("p.nonconformity_scope = %s")
            params.append(nonconformity_scope)
        where_clause = " AND ".join(filters)

        count_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS total
              FROM (
                    SELECT p.recurrence_key
                      FROM quality.quality_action_plans p
                     WHERE {where_clause}
                     GROUP BY p.recurrence_key
                    HAVING COUNT(*) >= %s
                   ) grouped
            """,
            tuple([*params, min_plans]),
        )
        total = int((count_row or {}).get("total") or 0)
        offset = max(page - 1, 0) * page_size

        rows = self.fetch_all(
            f"""
            SELECT p.recurrence_key,
                   COUNT(*)::int AS total_plans,
                   COUNT(*) FILTER (
                       WHERE p.status NOT IN ('completed', 'cancelled')
                   )::int AS open_plans,
                   COUNT(*) FILTER (
                       WHERE p.status NOT IN ('completed', 'cancelled')
                         AND p.severity = 'critical'
                   )::int AS critical_open,
                   MAX(p.created_at) AS last_opened_at,
                   (array_agg(p.code ORDER BY p.created_at DESC))[1] AS last_plan_code,
                   (array_agg(p.id::text ORDER BY p.created_at DESC))[1] AS last_plan_id,
                   (array_agg(p.branch_code ORDER BY p.created_at DESC))[1] AS branch_code,
                   (array_agg(p.product_code ORDER BY p.created_at DESC))[1] AS product_code,
                   (array_agg(p.failure_mode ORDER BY p.created_at DESC))[1] AS failure_mode
              FROM quality.quality_action_plans p
             WHERE {where_clause}
             GROUP BY p.recurrence_key
            HAVING COUNT(*) >= %s
             ORDER BY open_plans DESC, total_plans DESC, last_opened_at DESC
             LIMIT %s OFFSET %s
            """,
            tuple([*params, min_plans, page_size, offset]),
        )

        items: list[dict[str, Any]] = []
        for row in rows:
            last_opened = row.get("last_opened_at")
            items.append(
                {
                    "recurrence_key": row["recurrence_key"],
                    "branch_code": row.get("branch_code"),
                    "product_code": row.get("product_code"),
                    "failure_mode": row.get("failure_mode"),
                    "total_plans": int(row.get("total_plans") or 0),
                    "open_plans": int(row.get("open_plans") or 0),
                    "critical_open": int(row.get("critical_open") or 0),
                    "last_plan_code": row.get("last_plan_code"),
                    "last_plan_id": row.get("last_plan_id"),
                    "last_opened_at": (
                        last_opened.isoformat()
                        if hasattr(last_opened, "isoformat")
                        else last_opened
                    ),
                }
            )

        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1) if total else 1,
            },
        }

    def next_plan_code(self) -> str:
        row = self.execute_returning_one(
            """
            UPDATE quality.document_sequences
               SET current_value = current_value + 1,
                   updated_at = NOW()
             WHERE sequence_key = 'quality_action_plan'
               AND active = TRUE
            RETURNING prefix, current_value, padding_length
            """,
            auto_commit=False,
        )
        if not row:
            raise PluginsRepositoryError(
                "Sequência quality_action_plan não encontrada. Execute as migrations do plugin quality-action-plans."
            )

        year = datetime.now(timezone.utc).year
        padded = str(int(row["current_value"])).zfill(int(row["padding_length"]))
        return f"{row['prefix']}-{year}-{padded}"

    def create_plan(self, fields: dict[str, Any]) -> dict[str, Any]:
        code = self.next_plan_code()
        row = self.execute_returning_one(
            """
            INSERT INTO quality.quality_action_plans (
                code, title, customer_name, customer_code, customer_store, customer_contact, nonconformity_scope,
                customer_template, client_nc_registry,
                source_type, source_reference,
                product_code, product_description, batch_number, reported_problem,
                detected_at, reported_at, severity, status, created_by_user_id, owner_user_id,
                branch_code, department, problem_category, symptom_tags, root_cause_category,
                failure_mode, recurrence_key
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id, code, status
            """,
            (
                code,
                fields["title"],
                fields.get("customer_name"),
                fields.get("customer_code"),
                fields.get("customer_store"),
                fields.get("customer_contact"),
                fields.get("nonconformity_scope", "external"),
                fields.get("customer_template", "generic"),
                fields.get("client_nc_registry"),
                fields.get("source_type"),
                fields.get("source_reference"),
                fields.get("product_code"),
                fields.get("product_description"),
                fields.get("batch_number"),
                fields.get("reported_problem"),
                fields.get("detected_at"),
                fields.get("reported_at"),
                fields.get("severity", "medium"),
                fields.get("status", "triage"),
                fields["created_by_user_id"],
                fields.get("owner_user_id"),
                fields.get("branch_code"),
                fields.get("department"),
                fields.get("problem_category"),
                fields.get("symptom_tags") or [],
                fields.get("root_cause_category"),
                fields.get("failure_mode"),
                fields.get("recurrence_key"),
            ),
            auto_commit=False,
        )
        if not row:
            self.rollback()
            raise PluginsRepositoryError("Falha ao criar plano de ação.")

        plan_id = str(row["id"])
        actor_name = _optional_actor_text(fields.get("created_by_name"))
        actor_email = _optional_actor_text(fields.get("created_by_email"))
        self.append_history(
            plan_id=plan_id,
            event_type="plan_created",
            created_by=fields["created_by_user_id"],
            created_by_name=actor_name,
            created_by_email=actor_email,
            new_value=code,
            comment="Plano de ação criado via api-delpi.",
            auto_commit=False,
        )
        self.append_audit_log(
            entity_type="quality_action_plan",
            entity_id=plan_id,
            event_type="plan_created",
            actor_user_id=fields["created_by_user_id"],
            actor_name=actor_name,
            actor_email=actor_email,
            payload={
                "code": code,
                "severity": fields.get("severity", "medium"),
                "status": fields.get("status", "triage"),
                "nonconformity_scope": fields.get("nonconformity_scope", "external"),
                "branch_code": fields.get("branch_code"),
            },
            auto_commit=False,
        )
        self.commit()
        plan = self.get_plan_by_id(plan_id)
        if not plan:
            raise PluginsRepositoryError("Plano criado mas não encontrado após persistência.")
        return plan

    def update_plan(self, plan_id: str, fields: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get_plan_by_id(plan_id)
        if not current:
            return None

        allowed = {
            "title",
            "customer_name",
            "customer_code",
            "customer_store",
            "customer_contact",
            "nonconformity_scope",
            "source_type",
            "source_reference",
            "product_code",
            "product_description",
            "batch_number",
            "reported_problem",
            "detected_at",
            "reported_at",
            "severity",
            "owner_user_id",
            "branch_code",
            "department",
            "problem_category",
            "symptom_tags",
            "root_cause_category",
            "failure_mode",
            "recurrence_key",
            "customer_template",
            "client_nc_registry",
        }
        updates = {
            key: value
            for key, value in fields.items()
            if key in allowed and value is not None
        }
        if not updates:
            return current

        set_parts = [f"{column} = %s" for column in updates]
        set_parts.append("updated_at = NOW()")
        params = list(updates.values()) + [plan_id]

        self.execute(
            f"""
            UPDATE quality.quality_action_plans
               SET {", ".join(set_parts)}
             WHERE id = %s
               AND deleted_at IS NULL
            """,
            tuple(params),
            auto_commit=False,
        )
        self.append_history(
            plan_id=plan_id,
            event_type="plan_updated",
            created_by=fields.get("updated_by_user_id", "system"),
            created_by_name=_optional_actor_text(fields.get("updated_by_name")),
            created_by_email=_optional_actor_text(fields.get("updated_by_email")),
            comment="Plano atualizado via api-delpi.",
            auto_commit=False,
        )
        actor = str(fields.get("updated_by_user_id") or "system")
        self.append_audit_log(
            entity_type="quality_action_plan",
            entity_id=plan_id,
            event_type="plan_updated",
            actor_user_id=actor,
            actor_name=_optional_actor_text(fields.get("updated_by_name")),
            actor_email=_optional_actor_text(fields.get("updated_by_email")),
            payload={"fields": sorted(updates.keys())},
            auto_commit=False,
        )
        self.commit()
        return self.get_plan_by_id(plan_id)

    def get_plan_by_id(self, plan_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            f"""
            {PLAN_SELECT}
             WHERE p.id = %s AND p.deleted_at IS NULL
            """,
            (plan_id,),
        )
        return serialize_plan_row(row) if row else None

    def update_plan_status(
        self,
        plan_id: str,
        *,
        status: str,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
        comment: str | None = None,
    ) -> dict[str, Any] | None:
        current = self.get_plan_by_id(plan_id)
        if not current:
            return None

        previous_status = current.get("status")
        closed_at_sql = ""
        if status in _TERMINAL_PLAN_STATUSES:
            closed_at_sql = ", closed_at = NOW()"

        self.execute(
            f"""
            UPDATE quality.quality_action_plans
               SET status = %s, updated_at = NOW(){closed_at_sql}
             WHERE id = %s AND deleted_at IS NULL
            """,
            (status, plan_id),
            auto_commit=False,
        )
        history_event = (
            "plan_closed" if status in _TERMINAL_PLAN_STATUSES else "status_changed"
        )
        self.append_history(
            plan_id=plan_id,
            event_type=history_event,
            created_by=updated_by,
            created_by_name=updated_by_name,
            created_by_email=updated_by_email,
            old_value=previous_status,
            new_value=status,
            comment=comment,
            auto_commit=False,
        )
        if status in _TERMINAL_PLAN_STATUSES:
            self.append_audit_log(
                entity_type="quality_action_plan",
                entity_id=plan_id,
                event_type="plan_closed",
                actor_user_id=updated_by,
                actor_name=updated_by_name,
                actor_email=updated_by_email,
                payload={
                    "previous_status": previous_status,
                    "status": status,
                    "comment": comment,
                },
                auto_commit=False,
            )
        self.commit()
        return self.get_plan_by_id(plan_id)

    def reopen_plan(
        self,
        plan_id: str,
        *,
        target_status: str,
        reason: str,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        current = self.get_plan_by_id(plan_id)
        if not current:
            return None

        previous_status = current.get("status")
        if previous_status not in _TERMINAL_PLAN_STATUSES:
            raise ValueError(
                "Somente planos concluídos ou cancelados podem ser reabertos."
            )
        if target_status in _TERMINAL_PLAN_STATUSES:
            raise ValueError("Status alvo inválido para reabertura.")

        self.execute(
            """
            UPDATE quality.quality_action_plans
               SET status = %s,
                   closed_at = NULL,
                   updated_at = NOW()
             WHERE id = %s AND deleted_at IS NULL
            """,
            (target_status, plan_id),
            auto_commit=False,
        )
        self.append_history(
            plan_id=plan_id,
            event_type="plan_reopened",
            created_by=updated_by,
            created_by_name=updated_by_name,
            created_by_email=updated_by_email,
            old_value=previous_status,
            new_value=target_status,
            comment=reason,
            auto_commit=False,
        )
        self.append_audit_log(
            entity_type="quality_action_plan",
            entity_id=plan_id,
            event_type="plan_reopened",
            actor_user_id=updated_by,
            actor_name=updated_by_name,
            actor_email=updated_by_email,
            payload={
                "previous_status": previous_status,
                "target_status": target_status,
                "reason": reason,
            },
            auto_commit=False,
        )
        self.commit()
        return self.get_plan_by_id(plan_id)

    def append_history(
        self,
        *,
        plan_id: str,
        event_type: str,
        created_by: str,
        created_by_name: str | None = None,
        created_by_email: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        comment: str | None = None,
        auto_commit: bool = True,
    ) -> None:
        self.execute(
            """
            INSERT INTO quality.quality_action_history (
                plan_id,
                event_type,
                old_value,
                new_value,
                comment,
                created_by,
                created_by_name,
                created_by_email
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                plan_id,
                event_type,
                old_value,
                new_value,
                comment,
                created_by,
                created_by_name,
                created_by_email,
            ),
            auto_commit=auto_commit,
        )

    def append_audit_log(
        self,
        *,
        entity_type: str,
        entity_id: str,
        event_type: str,
        actor_user_id: str,
        actor_name: str | None = None,
        actor_email: str | None = None,
        payload: dict[str, Any] | None = None,
        auto_commit: bool = True,
    ) -> None:
        self.execute(
            """
            INSERT INTO quality.quality_audit_log (
                entity_type, entity_id, event_type, payload, actor_user_id, actor_name, actor_email
            ) VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s)
            """,
            (
                entity_type,
                entity_id,
                event_type,
                json.dumps(payload or {}),
                actor_user_id,
                actor_name,
                actor_email,
            ),
            auto_commit=auto_commit,
        )

    def list_plan_audit_log(
        self,
        plan_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        if not self._plan_exists(plan_id):
            return {
                "items": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": 0,
                    "total_pages": 1,
                },
            }

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        count_row = self.fetch_one(
            """
            SELECT COUNT(*)::int AS total
              FROM quality.quality_audit_log
             WHERE entity_type = 'quality_action_plan'
               AND entity_id = %s
            """,
            (plan_id,),
        )
        total = int((count_row or {}).get("total") or 0)
        offset = (page - 1) * page_size
        rows = self.fetch_all(
            """
            SELECT id,
                   entity_type,
                   entity_id,
                   event_type,
                   payload,
                   actor_user_id,
                   actor_name,
                   actor_email,
                   created_at
              FROM quality.quality_audit_log
             WHERE entity_type = 'quality_action_plan'
               AND entity_id = %s
             ORDER BY created_at DESC
             LIMIT %s OFFSET %s
            """,
            (plan_id, page_size, offset),
        )
        items: list[dict[str, Any]] = []
        for row in rows:
            created_at = row.get("created_at")
            items.append(
                {
                    "id": str(row["id"]),
                    "event_type": row.get("event_type"),
                    "payload": row.get("payload") or {},
                    "actor_user_id": row.get("actor_user_id"),
                    "actor_name": row.get("actor_name"),
                    "actor_email": row.get("actor_email"),
                    "created_at": (
                        created_at.isoformat()
                        if isinstance(created_at, datetime)
                        else created_at
                    ),
                }
            )
        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1),
            },
        }

    def _plan_exists(self, plan_id: str) -> bool:
        row = self.fetch_one(
            "SELECT id FROM quality.quality_action_plans WHERE id = %s AND deleted_at IS NULL",
            (plan_id,),
        )
        return row is not None

    def action_belongs_to_plan(self, plan_id: str, action_id: str) -> bool:
        row = self.fetch_one(
            "SELECT id FROM quality.quality_actions WHERE id = %s AND plan_id = %s",
            (action_id, plan_id),
        )
        return row is not None

    def upsert_ishikawa(
        self,
        plan_id: str,
        fields: dict[str, Any],
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        if not self._plan_exists(plan_id):
            return None

        causes_json = ishikawa_causes_json(fields)
        row = self.execute_returning_one(
            """
            INSERT INTO quality.quality_ishikawa_analysis (
                plan_id, machine, method_process, material, manpower, measurement, environment, notes
            ) VALUES (%s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s)
            ON CONFLICT (plan_id) DO UPDATE SET
                machine = EXCLUDED.machine,
                method_process = EXCLUDED.method_process,
                material = EXCLUDED.material,
                manpower = EXCLUDED.manpower,
                measurement = EXCLUDED.measurement,
                environment = EXCLUDED.environment,
                notes = EXCLUDED.notes,
                updated_at = NOW()
            RETURNING id, plan_id, machine, method_process, material, manpower,
                      measurement, environment, notes, created_at, updated_at
            """,
            (
                plan_id,
                causes_json["machine"],
                causes_json["method_process"],
                causes_json["material"],
                causes_json["manpower"],
                causes_json["measurement"],
                causes_json["environment"],
                fields.get("notes"),
            ),
            auto_commit=False,
        )
        self.append_history(
            plan_id=plan_id,
            event_type="ishikawa_updated",
            **self._history_author(updated_by, updated_by_name, updated_by_email),
            auto_commit=False,
        )
        self.commit()
        return serialize_ishikawa_row(row)

    def upsert_five_whys(
        self,
        plan_id: str,
        fields: dict[str, Any],
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        if not self._plan_exists(plan_id):
            return None

        whys_json = five_whys_json(fields)
        row = self.execute_returning_one(
            """
            INSERT INTO quality.quality_five_whys (
                plan_id, occurrence_whys, detection_whys, root_cause, confidence_level
            ) VALUES (%s, %s::jsonb, %s::jsonb, %s, %s)
            ON CONFLICT (plan_id) DO UPDATE SET
                occurrence_whys = EXCLUDED.occurrence_whys,
                detection_whys = EXCLUDED.detection_whys,
                root_cause = EXCLUDED.root_cause,
                confidence_level = EXCLUDED.confidence_level,
                updated_at = NOW()
            RETURNING id, plan_id, occurrence_whys, detection_whys,
                      root_cause, confidence_level, created_at, updated_at
            """,
            (
                plan_id,
                whys_json["occurrence_whys"],
                whys_json["detection_whys"],
                fields.get("root_cause"),
                fields.get("confidence_level"),
            ),
            auto_commit=False,
        )
        if fields.get("root_cause"):
            self.execute(
                """
                UPDATE quality.quality_action_plans
                   SET root_cause_category = COALESCE(root_cause_category, 'processo'),
                       updated_at = NOW()
                 WHERE id = %s
                """,
                (plan_id,),
                auto_commit=False,
            )
        self.append_history(
            plan_id=plan_id,
            event_type="five_whys_updated",
            **self._history_author(updated_by, updated_by_name, updated_by_email),
            new_value=fields.get("root_cause"),
            auto_commit=False,
        )
        self.commit()
        return serialize_five_whys_row(row)

    def create_actions(
        self,
        plan_id: str,
        actions: list[dict[str, Any]],
        *,
        created_by: str,
        created_by_name: str | None = None,
        created_by_email: str | None = None,
    ) -> list[dict[str, Any]] | None:
        if not self._plan_exists(plan_id):
            return None
        if not actions:
            return []

        created: list[dict[str, Any]] = []
        for action in actions:
            row = self.execute_returning_one(
                """
                INSERT INTO quality.quality_actions (
                    plan_id, action_type, description, responsible_user_id,
                    responsible_name, department, due_date, status, evidence_required, cause_track
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, plan_id, action_type, description, responsible_user_id,
                          responsible_name, department, due_date, status,
                          evidence_required, cause_track, completed_at, created_at, updated_at
                """,
                (
                    plan_id,
                    action["action_type"],
                    action["description"],
                    action.get("responsible_user_id"),
                    action.get("responsible_name"),
                    action.get("department"),
                    action.get("due_date"),
                    action.get("status", "pending"),
                    action.get("evidence_required", False),
                    action.get("cause_track"),
                ),
                auto_commit=False,
            )
            if row:
                created.append(serialize_row(row, id_keys=("id", "plan_id")) or {})
                self.append_history(
                    plan_id=plan_id,
                    event_type="action_created",
                    **self._history_author(created_by, created_by_name, created_by_email),
                    new_value=action["description"][:200],
                    auto_commit=False,
                )
        self.commit()
        return created

    def update_action(
        self,
        plan_id: str,
        action_id: str,
        fields: dict[str, Any],
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        allowed = {
            "action_type",
            "description",
            "responsible_user_id",
            "responsible_name",
            "department",
            "due_date",
            "status",
            "evidence_required",
            "cause_track",
        }
        nullable_fields = {"responsible_user_id", "responsible_name", "department", "due_date", "cause_track"}
        updates = {
            key: value
            for key, value in fields.items()
            if key in allowed
            and (
                value is not None
                or key in nullable_fields
            )
        }
        if not updates:
            row = self.fetch_one(
                """
                SELECT id, plan_id, action_type, description, responsible_user_id,
                       responsible_name, department, due_date, status,
                       evidence_required, completed_at, created_at, updated_at
                  FROM quality.quality_actions
                 WHERE id = %s AND plan_id = %s
                """,
                (action_id, plan_id),
            )
            return serialize_row(row, id_keys=("id", "plan_id")) if row else None

        set_parts = [f"{column} = %s" for column in updates]
        params: list[Any] = list(updates.values())
        if updates.get("status") == "completed":
            set_parts.append("completed_at = NOW()")
        set_parts.append("updated_at = NOW()")
        params.extend([action_id, plan_id])

        row = self.execute_returning_one(
            f"""
            UPDATE quality.quality_actions
               SET {", ".join(set_parts)}
             WHERE id = %s AND plan_id = %s
            RETURNING id, plan_id, action_type, description, responsible_user_id,
                      responsible_name, department, due_date, status,
                      evidence_required, completed_at, created_at, updated_at
            """,
            tuple(params),
            auto_commit=False,
        )
        if not row:
            self.rollback()
            return None

        event = "action_completed" if fields.get("status") == "completed" else "action_updated"
        self.append_history(
            plan_id=plan_id,
            event_type=event,
            **self._history_author(updated_by, updated_by_name, updated_by_email),
            auto_commit=False,
        )
        self.commit()
        return serialize_row(row, id_keys=("id", "plan_id"))

    def delete_action(
        self,
        plan_id: str,
        action_id: str,
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        if not self.action_belongs_to_plan(plan_id, action_id):
            return None

        row = self.fetch_one(
            """
            SELECT id, description
              FROM quality.quality_actions
             WHERE id = %s AND plan_id = %s
            """,
            (action_id, plan_id),
        )
        if not row:
            return None

        self.execute(
            "DELETE FROM quality.quality_actions WHERE id = %s AND plan_id = %s",
            (action_id, plan_id),
            auto_commit=False,
        )
        self.append_history(
            plan_id=plan_id,
            event_type="action_deleted",
            **self._history_author(updated_by, updated_by_name, updated_by_email),
            old_value=(row.get("description") or "")[:200],
            auto_commit=False,
        )
        self.commit()
        return {"id": str(action_id), "deleted": True}

    def submit_effectiveness_review(
        self,
        plan_id: str,
        fields: dict[str, Any],
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        if not self._plan_exists(plan_id):
            return None

        current = self.get_plan_by_id(plan_id)
        if current is None:
            return None
        if current.get("effectiveness_approval_status") == "pending_review":
            raise ValueError("Já existe submissão de eficácia aguardando aprovação.")

        self.execute(
            """
            UPDATE quality.quality_action_plans
               SET effectiveness_proposed_status = %s,
                   effectiveness_approval_status = 'pending_review',
                   effectiveness_notes = %s,
                   effectiveness_submitted_at = NOW(),
                   effectiveness_submitted_by = %s,
                   effectiveness_reviewed_at = NULL,
                   effectiveness_reviewed_by = NULL,
                   effectiveness_rejection_reason = NULL,
                   updated_at = NOW()
             WHERE id = %s AND deleted_at IS NULL
            """,
            (
                fields["effectiveness_status"],
                fields.get("notes"),
                updated_by,
                plan_id,
            ),
            auto_commit=False,
        )
        self.append_history(
            plan_id=plan_id,
            event_type="effectiveness_submitted",
            **self._history_author(updated_by, updated_by_name, updated_by_email),
            new_value=fields["effectiveness_status"],
            comment=fields.get("notes"),
            auto_commit=False,
        )
        self.append_audit_log(
            entity_type="quality_action_plan",
            entity_id=plan_id,
            event_type="effectiveness_submitted",
            **self._audit_author(updated_by, updated_by_name, updated_by_email),
            payload={
                "proposed_status": fields["effectiveness_status"],
                "notes": fields.get("notes"),
            },
            auto_commit=False,
        )
        self.commit()
        return self.get_plan_by_id(plan_id)

    def approve_effectiveness_review(
        self,
        plan_id: str,
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        if not self._plan_exists(plan_id):
            return None

        current = self.get_plan_by_id(plan_id)
        if current is None:
            return None
        if current.get("effectiveness_approval_status") != "pending_review":
            raise ValueError("Não há submissão de eficácia pendente de aprovação.")
        proposed = current.get("effectiveness_proposed_status")
        if not proposed:
            raise ValueError("Submissão sem resultado proposto.")

        self.execute(
            """
            UPDATE quality.quality_action_plans
               SET effectiveness_status = %s,
                   effectiveness_verified_at = NOW(),
                   effectiveness_approval_status = 'approved',
                   effectiveness_reviewed_at = NOW(),
                   effectiveness_reviewed_by = %s,
                   effectiveness_rejection_reason = NULL,
                   updated_at = NOW()
             WHERE id = %s AND deleted_at IS NULL
            """,
            (proposed, updated_by, plan_id),
            auto_commit=False,
        )
        self.append_history(
            plan_id=plan_id,
            event_type="effectiveness_reviewed",
            **self._history_author(updated_by, updated_by_name, updated_by_email),
            new_value=proposed,
            comment=current.get("effectiveness_notes"),
            auto_commit=False,
        )
        self.append_audit_log(
            entity_type="quality_action_plan",
            entity_id=plan_id,
            event_type="effectiveness_approved",
            **self._audit_author(updated_by, updated_by_name, updated_by_email),
            payload={
                "effectiveness_status": proposed,
                "submitted_by": current.get("effectiveness_submitted_by"),
            },
            auto_commit=False,
        )
        self.commit()
        return self.get_plan_by_id(plan_id)

    def reject_effectiveness_review(
        self,
        plan_id: str,
        *,
        reason: str,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        if not self._plan_exists(plan_id):
            return None

        current = self.get_plan_by_id(plan_id)
        if current is None:
            return None
        if current.get("effectiveness_approval_status") != "pending_review":
            raise ValueError("Não há submissão de eficácia pendente de aprovação.")

        self.execute(
            """
            UPDATE quality.quality_action_plans
               SET effectiveness_approval_status = 'rejected',
                   effectiveness_reviewed_at = NOW(),
                   effectiveness_reviewed_by = %s,
                   effectiveness_rejection_reason = %s,
                   updated_at = NOW()
             WHERE id = %s AND deleted_at IS NULL
            """,
            (updated_by, reason, plan_id),
            auto_commit=False,
        )
        self.append_history(
            plan_id=plan_id,
            event_type="effectiveness_approval_rejected",
            **self._history_author(updated_by, updated_by_name, updated_by_email),
            new_value=current.get("effectiveness_proposed_status"),
            comment=reason,
            auto_commit=False,
        )
        self.append_audit_log(
            entity_type="quality_action_plan",
            entity_id=plan_id,
            event_type="effectiveness_approval_rejected",
            **self._audit_author(updated_by, updated_by_name, updated_by_email),
            payload={
                "proposed_status": current.get("effectiveness_proposed_status"),
                "reason": reason,
                "submitted_by": current.get("effectiveness_submitted_by"),
            },
            auto_commit=False,
        )
        self.commit()
        return self.get_plan_by_id(plan_id)

    def list_pending_effectiveness_reviews(
        self, *, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        count_row = self.fetch_one(
            """
            SELECT COUNT(*) AS total
              FROM quality.quality_action_plans p
             WHERE p.deleted_at IS NULL
               AND p.effectiveness_approval_status = 'pending_review'
            """,
            (),
        )
        total = int(count_row["total"]) if count_row else 0
        offset = (page - 1) * page_size
        rows = self.fetch_all(
            f"""
            {PLAN_SELECT}
             WHERE p.deleted_at IS NULL
               AND p.effectiveness_approval_status = 'pending_review'
             ORDER BY p.effectiveness_submitted_at ASC NULLS LAST, p.created_at ASC
             LIMIT %s OFFSET %s
            """,
            (page_size, offset),
        )
        return {
            "items": [serialize_plan_row(row) for row in rows],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1),
            },
        }

    def record_effectiveness_review(
        self,
        plan_id: str,
        fields: dict[str, Any],
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        if not self._plan_exists(plan_id):
            return None

        self.execute(
            """
            UPDATE quality.quality_action_plans
               SET effectiveness_status = %s,
                   effectiveness_verified_at = NOW(),
                   effectiveness_notes = %s,
                   effectiveness_approval_status = NULL,
                   effectiveness_proposed_status = NULL,
                   effectiveness_submitted_at = NULL,
                   effectiveness_submitted_by = NULL,
                   effectiveness_reviewed_at = NOW(),
                   effectiveness_reviewed_by = %s,
                   effectiveness_rejection_reason = NULL,
                   updated_at = NOW()
             WHERE id = %s AND deleted_at IS NULL
            """,
            (fields["effectiveness_status"], fields.get("notes"), updated_by, plan_id),
            auto_commit=False,
        )
        self.append_history(
            plan_id=plan_id,
            event_type="effectiveness_reviewed",
            **self._history_author(updated_by, updated_by_name, updated_by_email),
            new_value=fields["effectiveness_status"],
            comment=fields.get("notes"),
            auto_commit=False,
        )
        self.append_audit_log(
            entity_type="quality_action_plan",
            entity_id=plan_id,
            event_type="effectiveness_reviewed",
            **self._audit_author(updated_by, updated_by_name, updated_by_email),
            payload={
                "effectiveness_status": fields["effectiveness_status"],
                "notes": fields.get("notes"),
            },
            auto_commit=False,
        )
        self.commit()
        return self.get_plan_by_id(plan_id)

    def upsert_rnc_8d_report(
        self,
        plan_id: str,
        fields: dict[str, Any],
        *,
        updated_by: str,
        updated_by_name: str | None = None,
        updated_by_email: str | None = None,
    ) -> dict[str, Any] | None:
        if not self._plan_exists(plan_id):
            return None

        template_payload = fields.get("template_payload") or {}
        self.execute(
            """
            UPDATE quality.quality_action_plans
               SET customer_template = COALESCE(%s, customer_template),
                   client_nc_registry = COALESCE(%s, client_nc_registry),
                   customer_name = COALESCE(%s, customer_name),
                   customer_contact = COALESCE(%s, customer_contact),
                   product_code = COALESCE(%s, product_code),
                   product_description = COALESCE(%s, product_description),
                   batch_number = COALESCE(%s, batch_number),
                   reported_problem = COALESCE(%s, reported_problem),
                   template_payload = COALESCE(%s::jsonb, template_payload),
                   updated_at = NOW()
             WHERE id = %s AND deleted_at IS NULL
            """,
            (
                fields.get("customer_template", "rnc_8d"),
                fields.get("client_nc_registry"),
                fields.get("customer_name"),
                fields.get("customer_contact"),
                fields.get("product_code"),
                fields.get("product_description"),
                fields.get("batch_number"),
                fields.get("reported_problem"),
                json.dumps(template_payload) if template_payload else None,
                plan_id,
            ),
            auto_commit=False,
        )

        team_members = fields.get("team_members")
        if team_members is not None:
            self.execute(
                "DELETE FROM quality.quality_analysis_team_members WHERE plan_id = %s",
                (plan_id,),
                auto_commit=False,
            )
            for index, member in enumerate(team_members):
                self.execute(
                    """
                    INSERT INTO quality.quality_analysis_team_members (
                        plan_id, member_name, member_user_id, department, is_leader, sort_order
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        plan_id,
                        member.get("member_name") or member.get("name"),
                        member.get("member_user_id"),
                        member.get("department"),
                        bool(member.get("is_leader")),
                        member.get("sort_order", index),
                    ),
                    auto_commit=False,
                )

        self.append_history(
            plan_id=plan_id,
            event_type="plan_updated",
            **self._history_author(updated_by, updated_by_name, updated_by_email),
            comment="Relatório 8D (materiais adquiridos) atualizado.",
            auto_commit=False,
        )
        self.commit()
        return self.get_plan_detail(plan_id)

    def search_evidences(
        self,
        *,
        q: str,
        plan_id: str | None = None,
        branch_code: str | None = None,
        section: str | None = None,
        evidence_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        term = q.strip()
        if len(term) < 2:
            raise ValueError("Informe ao menos 2 caracteres para buscar evidências.")

        like = f"%{term}%"
        filters = [
            "p.deleted_at IS NULL",
            """(
                e.file_name ILIKE %s
                OR e.stored_name ILIKE %s
                OR COALESCE(e.description, '') ILIKE %s
                OR COALESCE(e.text_excerpt, '') ILIKE %s
            )""",
        ]
        params: list[Any] = [like, like, like, like]

        if plan_id:
            filters.append("e.plan_id = %s")
            params.append(plan_id)
        if branch_code:
            filters.append("p.branch_code = %s")
            params.append(branch_code)
        if section:
            filters.append("e.section = %s")
            params.append(section)
        if evidence_type:
            filters.append("e.type = %s")
            params.append(evidence_type)

        where_clause = " AND ".join(filters)

        count_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS total
              FROM quality.quality_problem_evidences e
              JOIN quality.quality_action_plans p ON p.id = e.plan_id
             WHERE {where_clause}
            """,
            tuple(params),
        )
        total = int((count_row or {}).get("total") or 0)
        offset = max(page - 1, 0) * page_size

        rows = self.fetch_all(
            f"""
            SELECT e.id,
                   e.plan_id,
                   e.type,
                   e.file_name,
                   e.stored_name,
                   e.description,
                   e.text_excerpt,
                   e.section,
                   e.action_id,
                   e.mime_type,
                   e.size_bytes,
                   e.created_at,
                   p.code AS plan_code,
                   p.title AS plan_title,
                   p.branch_code,
                   p.product_code
              FROM quality.quality_problem_evidences e
              JOIN quality.quality_action_plans p ON p.id = e.plan_id
             WHERE {where_clause}
             ORDER BY e.created_at DESC
             LIMIT %s OFFSET %s
            """,
            tuple([*params, page_size, offset]),
        )

        items: list[dict[str, Any]] = []
        for row in rows:
            item = serialize_row(
                row,
                id_keys=("id", "plan_id", "action_id"),
            ) or {}
            created_at = row.get("created_at")
            if hasattr(created_at, "isoformat"):
                item["created_at"] = created_at.isoformat()
            items.append(item)

        return {
            "items": items,
            "query": term,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1) if total else 1,
            },
        }

    def list_evidences(self, plan_id: str, *, q: str | None = None) -> list[dict[str, Any]]:
        if not self._plan_exists(plan_id):
            return []

        filters = ["plan_id = %s"]
        params: list[Any] = [plan_id]
        if q and q.strip():
            like = f"%{q.strip()}%"
            filters.append(
                """(
                    file_name ILIKE %s
                    OR stored_name ILIKE %s
                    OR COALESCE(description, '') ILIKE %s
                    OR COALESCE(text_excerpt, '') ILIKE %s
                )"""
            )
            params.extend([like, like, like, like])

        where_clause = " AND ".join(filters)
        rows = self.fetch_all(
            f"""
            SELECT id, plan_id, type, file_name, file_url, text_excerpt,
                   stored_name, mime_type, size_bytes, section, description,
                   knowledge_visible, uploaded_by, uploaded_by_name, uploaded_by_email,
                   action_id, created_at
              FROM quality.quality_problem_evidences
             WHERE {where_clause}
             ORDER BY created_at DESC
            """,
            tuple(params),
        )
        return [serialize_row(row, id_keys=("id", "plan_id", "action_id")) or {} for row in rows if row]

    def get_evidence(self, plan_id: str, evidence_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            """
            SELECT id, plan_id, type, file_name, file_url, text_excerpt,
                   stored_name, mime_type, size_bytes, section, description,
                   knowledge_visible, uploaded_by, uploaded_by_name, uploaded_by_email,
                   action_id, created_at
              FROM quality.quality_problem_evidences
             WHERE id = %s AND plan_id = %s
            """,
            (evidence_id, plan_id),
        )
        return serialize_row(row, id_keys=("id", "plan_id", "action_id")) if row else None

    def create_evidence(self, plan_id: str, fields: dict[str, Any]) -> dict[str, Any] | None:
        if not self._plan_exists(plan_id):
            return None
        action_id = fields.get("action_id")
        if action_id and not self.action_belongs_to_plan(plan_id, str(action_id)):
            return None
        row = self.execute_returning_one(
            """
            INSERT INTO quality.quality_problem_evidences (
                plan_id, type, file_name, file_url, text_excerpt,
                stored_name, mime_type, size_bytes, section, description,
                knowledge_visible, uploaded_by, uploaded_by_name, uploaded_by_email, action_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, plan_id, type, file_name, file_url, text_excerpt,
                      stored_name, mime_type, size_bytes, section, description,
                      knowledge_visible, uploaded_by, uploaded_by_name, uploaded_by_email,
                      action_id, created_at
            """,
            (
                plan_id,
                fields["type"],
                fields.get("file_name"),
                fields.get("file_url"),
                fields.get("text_excerpt"),
                fields.get("stored_name"),
                fields.get("mime_type"),
                fields.get("size_bytes"),
                fields.get("section", "general"),
                fields.get("description"),
                fields.get("knowledge_visible", True),
                fields["uploaded_by"],
                _optional_actor_text(fields.get("uploaded_by_name")),
                _optional_actor_text(fields.get("uploaded_by_email")),
                action_id,
            ),
            auto_commit=True,
        )
        return serialize_row(row, id_keys=("id", "plan_id", "action_id")) if row else None

    def delete_evidence(self, plan_id: str, evidence_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            """
            SELECT id, plan_id, stored_name
              FROM quality.quality_problem_evidences
             WHERE id = %s AND plan_id = %s
            """,
            (evidence_id, plan_id),
        )
        if not row:
            return None
        self.execute(
            "DELETE FROM quality.quality_problem_evidences WHERE id = %s AND plan_id = %s",
            (evidence_id, plan_id),
            auto_commit=True,
        )
        return serialize_row(row, id_keys=("id", "plan_id"))


PostgresQualityActionPlanReadRepository = PostgresQualityActionPlanRepository
