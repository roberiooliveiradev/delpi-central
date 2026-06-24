from __future__ import annotations

from typing import Any

from app.domain.services.quality_action_plans.quality_action_plan_serialization import (
    PLAN_SELECT,
    serialize_plan_row,
    serialize_row,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository


class PostgresQualityActionPlanReadRepository(PluginBaseRepository):
    """Leitura consolidada PAC para plugin de liderança (api-delpi)."""

    def list_plans(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        product_code: str | None = None,
        customer_name: str | None = None,
        owner_user_id: str | None = None,
        branch_code: str | None = None,
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
            SELECT id, plan_id, why_1, why_2, why_3, why_4, why_5,
                   root_cause, confidence_level, created_at, updated_at
              FROM quality.quality_five_whys WHERE plan_id = %s
            """,
            (plan_id,),
        )
        actions = self.fetch_all(
            """
            SELECT id, plan_id, action_type, description, responsible_user_id,
                   responsible_name, department, due_date, status,
                   evidence_required, completed_at, created_at, updated_at
              FROM quality.quality_actions
             WHERE plan_id = %s
             ORDER BY due_date NULLS LAST, created_at ASC
            """,
            (plan_id,),
        )
        history = self.fetch_all(
            """
            SELECT id, plan_id, event_type, old_value, new_value, comment,
                   created_by, created_at
              FROM quality.quality_action_history
             WHERE plan_id = %s
             ORDER BY created_at DESC
             LIMIT 100
            """,
            (plan_id,),
        )

        return {
            "plan": serialize_plan_row(plan_row),
            "ishikawa": serialize_row(ishikawa, id_keys=("id", "plan_id")),
            "five_whys": serialize_row(five_whys, id_keys=("id", "plan_id")),
            "actions": [
                serialize_row(row, id_keys=("id", "plan_id")) for row in actions if row
            ],
            "history": [
                serialize_row(row, id_keys=("id", "plan_id")) for row in history if row
            ],
        }

    def get_dashboard_summary(self, *, branch_code: str | None = None) -> dict[str, Any]:
        branch_filter = ""
        params: list[Any] = []
        if branch_code:
            branch_filter = " AND branch_code = %s"
            params = [branch_code]

        row = self.fetch_one(
            f"""
            SELECT
                COUNT(*) FILTER (
                    WHERE deleted_at IS NULL
                      AND status NOT IN ('completed', 'cancelled')
                      {branch_filter}
                ) AS open_plans,
                COUNT(*) FILTER (
                    WHERE deleted_at IS NULL
                      AND status NOT IN ('completed', 'cancelled')
                      AND severity = 'critical'
                      {branch_filter}
                ) AS critical_open,
                COUNT(*) FILTER (
                    WHERE deleted_at IS NULL
                      AND status = 'waiting_validation'
                      {branch_filter}
                ) AS waiting_validation,
                COUNT(*) FILTER (
                    WHERE deleted_at IS NULL
                      AND status = 'completed'
                      AND closed_at >= date_trunc('month', NOW())
                      {branch_filter}
                ) AS completed_this_month
              FROM quality.quality_action_plans
              WHERE deleted_at IS NULL
              {branch_filter}
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
        }
        if branch_code:
            result["branch_code"] = branch_code
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
        return result

    def list_overdue_plans(
        self, *, branch_code: str | None = None, page: int = 1, page_size: int = 50
    ) -> dict[str, Any]:
        branch_filter = ""
        params: list[Any] = []
        if branch_code:
            branch_filter = " AND p.branch_code = %s"
            params.append(branch_code)

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
            """,
            tuple(params),
        )
        total = int((count_row or {}).get("total") or 0)
        offset = max(page - 1, 0) * page_size
        rows = self.fetch_all(
            f"""
            SELECT DISTINCT ON (p.id)
                   p.id, p.code, p.title, p.customer_name, p.product_code,
                   p.branch_code, p.severity, p.status, p.owner_user_id, p.created_at, p.updated_at
              FROM quality.quality_action_plans p
              JOIN quality.quality_actions a ON a.plan_id = p.id
             WHERE p.deleted_at IS NULL
               AND p.status NOT IN ('completed', 'cancelled')
               AND a.status NOT IN ('completed', 'cancelled')
               AND a.due_date < CURRENT_DATE
               {branch_filter}
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
