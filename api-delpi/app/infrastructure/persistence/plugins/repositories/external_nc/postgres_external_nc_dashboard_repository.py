# app/infrastructure/persistence/plugins/repositories/external_nc/postgres_external_nc_dashboard_repository.py
from __future__ import annotations

from app.domain.ports.external_nc.external_nc_dashboard_repository import (
    ExternalNcDashboardRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresExternalNcDashboardRepository(
    PluginBaseRepository,
    ExternalNcDashboardRepositoryPort,
):
    def get_summary(self) -> dict:
        row = self.fetch_one(
            """
            WITH nc AS (
                SELECT
                    id,
                    current_status,
                    supplier_status,
                    created_at,
                    due_date,
                    closed_at
                FROM quality.external_nonconformities
            ),
            effectiveness AS (
                SELECT
                    nonconformity_id,
                    result,
                    ROW_NUMBER() OVER (
                        PARTITION BY nonconformity_id
                        ORDER BY checked_at ASC, created_at ASC
                    ) AS rn
                FROM quality.external_nc_effectiveness_checks
            )
            SELECT
                COUNT(*) AS total_cases,
                COUNT(*) FILTER (
                    WHERE current_status NOT IN ('closed', 'cancelled')
                ) AS open_cases,
                COUNT(*) FILTER (
                    WHERE due_date IS NOT NULL
                      AND due_date < CURRENT_DATE
                      AND current_status NOT IN ('closed', 'cancelled')
                ) AS overdue_cases,
                ROUND(
                    AVG(
                        CASE
                            WHEN closed_at IS NOT NULL
                            THEN EXTRACT(EPOCH FROM (closed_at - created_at)) / 86400.0
                            ELSE NULL
                        END
                    )::numeric,
                    2
                ) AS avg_closure_days,
                ROUND(
                    AVG(
                        CASE
                            WHEN supplier_status IN ('supplier-responded', 'supplier-validated')
                                 AND created_at IS NOT NULL
                            THEN EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400.0
                            ELSE NULL
                        END
                    )::numeric,
                    2
                ) AS avg_supplier_response_days,
                COUNT(*) FILTER (
                    WHERE current_status = 'reopened'
                ) AS reopened_cases,
                COUNT(*) FILTER (
                    WHERE id IN (
                        SELECT nonconformity_id
                        FROM effectiveness
                        WHERE rn = 1
                          AND result = 'approved'
                    )
                ) AS first_pass_effectiveness
            FROM quality.external_nonconformities
            """
        )
        return row or {}

    def get_by_supplier(self) -> list[dict]:
        return self.fetch_all(
            """
            SELECT
                supplier_id,
                supplier_name_snapshot AS supplier_name,
                COUNT(*) AS total_cases,
                COUNT(*) FILTER (
                    WHERE current_status NOT IN ('closed', 'cancelled')
                ) AS open_cases,
                COUNT(*) FILTER (
                    WHERE due_date IS NOT NULL
                      AND due_date < CURRENT_DATE
                      AND current_status NOT IN ('closed', 'cancelled')
                ) AS overdue_cases,
                ROUND(
                    AVG(
                        CASE
                            WHEN closed_at IS NOT NULL
                            THEN EXTRACT(EPOCH FROM (closed_at - created_at)) / 86400.0
                            ELSE NULL
                        END
                    )::numeric,
                    2
                ) AS avg_closure_days
            FROM quality.external_nonconformities
            GROUP BY supplier_id, supplier_name_snapshot
            ORDER BY total_cases DESC, supplier_name_snapshot ASC
            """
        )

    def get_by_cause(self) -> list[dict]:
        return self.fetch_all(
            """
            SELECT
                COALESCE(category, 'sem-categoria') AS cause_category,
                COUNT(*) AS total_root_causes,
                COUNT(DISTINCT nonconformity_id) AS affected_cases
            FROM quality.external_nc_root_causes
            GROUP BY COALESCE(category, 'sem-categoria')
            ORDER BY affected_cases DESC, total_root_causes DESC, cause_category ASC
            """
        )

    def get_overdue_actions(self) -> list[dict]:
        return self.fetch_all(
            """
            SELECT
                a.id,
                a.nonconformity_id,
                n.code AS nonconformity_code,
                n.title AS nonconformity_title,
                n.supplier_name_snapshot AS supplier_name,
                a.action_type,
                a.title,
                a.description,
                a.responsible_user_id,
                a.responsible_external_name,
                a.due_date,
                a.status,
                (CURRENT_DATE - a.due_date) AS overdue_days
            FROM quality.external_nc_actions a
            INNER JOIN quality.external_nonconformities n
                ON n.id = a.nonconformity_id
            WHERE a.due_date < CURRENT_DATE
              AND a.status NOT IN ('completed', 'cancelled')
            ORDER BY a.due_date ASC, a.created_at ASC
            """
        )