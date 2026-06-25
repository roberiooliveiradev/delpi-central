from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository


class PostgresQualityIntelligenceRepository(PluginBaseRepository):
    def sync_case_similarity_index(self, plan_id: str) -> None:
        row = self.fetch_one(
            """
            SELECT p.id,
                   p.title,
                   p.reported_problem,
                   p.product_code,
                   p.customer_name,
                   p.problem_category,
                   p.failure_mode,
                   p.root_cause_category,
                   p.symptom_tags,
                   p.branch_code,
                   p.product_description,
                   fw.root_cause
              FROM quality.quality_action_plans p
              LEFT JOIN quality.quality_five_whys fw ON fw.plan_id = p.id
             WHERE p.id = %s
               AND p.deleted_at IS NULL
            """,
            (plan_id,),
        )
        if not row:
            return

        parts = [
            row.get("title"),
            row.get("reported_problem"),
            row.get("failure_mode"),
            row.get("problem_category"),
            row.get("product_description"),
            row.get("root_cause"),
        ]
        search_text = " ".join(part.strip() for part in parts if part and str(part).strip())

        self.execute(
            """
            INSERT INTO quality.quality_case_similarity_index (
                plan_id,
                search_text,
                product_code,
                customer_name,
                problem_category,
                failure_mode,
                root_cause_category,
                symptom_tags,
                branch_code
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (plan_id) DO UPDATE SET
                search_text = EXCLUDED.search_text,
                product_code = EXCLUDED.product_code,
                customer_name = EXCLUDED.customer_name,
                problem_category = EXCLUDED.problem_category,
                failure_mode = EXCLUDED.failure_mode,
                root_cause_category = EXCLUDED.root_cause_category,
                symptom_tags = EXCLUDED.symptom_tags,
                branch_code = EXCLUDED.branch_code,
                updated_at = NOW()
            """,
            (
                plan_id,
                search_text,
                row.get("product_code"),
                row.get("customer_name"),
                row.get("problem_category"),
                row.get("failure_mode"),
                row.get("root_cause_category") or row.get("root_cause"),
                row.get("symptom_tags") or [],
                row.get("branch_code"),
            ),
        )

    def has_similarity_index_entry(self, plan_id: str) -> bool:
        row = self.fetch_one(
            """
            SELECT 1
              FROM quality.quality_case_similarity_index
             WHERE plan_id = %s
            """,
            (plan_id,),
        )
        return row is not None
