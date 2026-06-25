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

    def fetch_similar_case_candidates(
        self,
        *,
        problem_description: str,
        product_code: str | None,
        symptoms: list[str],
        branch_code: str | None = None,
        exclude_plan_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        tokens = [t.strip() for t in problem_description.split() if len(t.strip()) >= 3][:8]
        filters = ["p.deleted_at IS NULL", "p.status NOT IN ('draft', 'cancelled')"]
        params: list[Any] = []

        if exclude_plan_id:
            filters.append("p.id <> %s")
            params.append(exclude_plan_id)

        or_parts: list[str] = []
        if product_code:
            or_parts.append("idx.product_code = %s")
            params.append(product_code)

        if branch_code:
            filters.append("p.branch_code = %s")
            params.append(branch_code)

        if symptoms:
            or_parts.append("idx.symptom_tags && %s::text[]")
            params.append(symptoms)

        for token in tokens[:5]:
            or_parts.append("idx.search_text ILIKE %s")
            params.append(f"%{token}%")

        if or_parts:
            filters.append(f"({' OR '.join(or_parts)})")

        where_clause = " AND ".join(filters)
        rows = self.fetch_all(
            f"""
            SELECT idx.plan_id,
                   p.code AS plan_code,
                   idx.search_text,
                   idx.product_code,
                   idx.failure_mode,
                   idx.root_cause_category,
                   idx.symptom_tags,
                   p.branch_code,
                   COALESCE(p.reported_problem, p.title) AS problem_summary,
                   fw.root_cause,
                   p.effectiveness_status,
                   p.closed_at,
                   p.title
              FROM quality.quality_case_similarity_index idx
              JOIN quality.quality_action_plans p ON p.id = idx.plan_id
              LEFT JOIN quality.quality_five_whys fw ON fw.plan_id = p.id
             WHERE {where_clause}
             ORDER BY p.updated_at DESC
             LIMIT %s
            """,
            tuple([*params, limit]),
        )

        results: list[dict[str, Any]] = []
        for row in rows:
            candidate_plan_id = str(row["plan_id"])
            actions = self.fetch_all(
                """
                SELECT description
                  FROM quality.quality_actions
                 WHERE plan_id = %s
                   AND status = 'completed'
                 ORDER BY completed_at DESC NULLS LAST
                 LIMIT 5
                """,
                (candidate_plan_id,),
            )
            effective_actions = [a["description"] for a in actions if a.get("description")]
            closed_at = row.get("closed_at")
            results.append(
                {
                    "plan_id": candidate_plan_id,
                    "plan_code": row["plan_code"],
                    "search_text": row.get("search_text") or "",
                    "product_code": row.get("product_code"),
                    "failure_mode": row.get("failure_mode"),
                    "root_cause_category": row.get("root_cause_category"),
                    "symptom_tags": list(row.get("symptom_tags") or []),
                    "problem_summary": row.get("problem_summary") or row.get("title"),
                    "root_cause": row.get("root_cause"),
                    "effectiveness_status": row.get("effectiveness_status"),
                    "closed_at": closed_at.isoformat() if hasattr(closed_at, "isoformat") else closed_at,
                    "effective_actions": effective_actions,
                    "branch_code": row.get("branch_code"),
                }
            )
        return results
