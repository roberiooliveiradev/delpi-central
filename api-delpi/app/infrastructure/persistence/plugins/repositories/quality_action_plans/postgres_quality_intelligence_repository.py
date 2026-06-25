from __future__ import annotations

from typing import Any

from app.domain.services.quality_action_plans.case_similarity_embedding_service import (
    CaseSimilarityEmbeddingService,
)
from app.domain.services.quality_action_plans.quality_action_plan_serialization import serialize_row
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)


class PostgresQualityIntelligenceRepository(PluginBaseRepository):
    def sync_case_similarity_index(self, plan_id: str) -> str | None:
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
            return None

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
        return search_text

    def update_search_embedding(self, plan_id: str, embedding: list[float]) -> None:
        literal = CaseSimilarityEmbeddingService.format_pgvector_literal(embedding)
        self.execute(
            """
            UPDATE quality.quality_case_similarity_index
               SET search_embedding = %s::vector,
                   updated_at = NOW()
             WHERE plan_id = %s
            """,
            (literal, plan_id),
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
        query_embedding: list[float] | None = None,
    ) -> list[dict[str, Any]]:
        text_rows = self._fetch_text_similar_case_candidates(
            problem_description=problem_description,
            product_code=product_code,
            symptoms=symptoms,
            branch_code=branch_code,
            exclude_plan_id=exclude_plan_id,
            limit=limit,
        )

        if not query_embedding:
            return text_rows

        semantic_rows = self._fetch_semantic_similar_case_candidates(
            query_embedding=query_embedding,
            product_code=product_code,
            symptoms=symptoms,
            branch_code=branch_code,
            exclude_plan_id=exclude_plan_id,
            limit=limit,
        )
        return self._merge_similar_case_candidates(text_rows, semantic_rows)

    def _fetch_text_similar_case_candidates(
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
                    "semantic_similarity": None,
                }
            )
        return results

    def _fetch_semantic_similar_case_candidates(
        self,
        *,
        query_embedding: list[float],
        product_code: str | None,
        symptoms: list[str],
        branch_code: str | None = None,
        exclude_plan_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        literal = CaseSimilarityEmbeddingService.format_pgvector_literal(query_embedding)
        filters = [
            "p.deleted_at IS NULL",
            "p.status NOT IN ('draft', 'cancelled')",
            "idx.search_embedding IS NOT NULL",
        ]
        params: list[Any] = [literal, literal]

        if exclude_plan_id:
            filters.append("p.id <> %s")
            params.append(exclude_plan_id)

        if product_code:
            filters.append("idx.product_code = %s")
            params.append(product_code)

        if branch_code:
            filters.append("p.branch_code = %s")
            params.append(branch_code)

        if symptoms:
            filters.append("idx.symptom_tags && %s::text[]")
            params.append(symptoms)

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
                   p.title,
                   1 - (idx.search_embedding <=> %s::vector) AS semantic_similarity
              FROM quality.quality_case_similarity_index idx
              JOIN quality.quality_action_plans p ON p.id = idx.plan_id
              LEFT JOIN quality.quality_five_whys fw ON fw.plan_id = p.id
             WHERE {where_clause}
             ORDER BY idx.search_embedding <=> %s::vector
             LIMIT %s
            """,
            tuple([*params, limit]),
        )
        return self._hydrate_similar_case_rows(rows)

    def _hydrate_similar_case_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for row in rows:
            plan_id = str(row["plan_id"])
            actions = self.fetch_all(
                """
                SELECT description
                  FROM quality.quality_actions
                 WHERE plan_id = %s
                   AND status = 'completed'
                 ORDER BY completed_at DESC NULLS LAST
                 LIMIT 5
                """,
                (plan_id,),
            )
            effective_actions = [a["description"] for a in actions if a.get("description")]
            closed_at = row.get("closed_at")
            semantic_similarity = row.get("semantic_similarity")
            results.append(
                {
                    "plan_id": plan_id,
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
                    "semantic_similarity": float(semantic_similarity)
                    if semantic_similarity is not None
                    else None,
                }
            )
        return results

    @staticmethod
    def _merge_similar_case_candidates(
        text_rows: list[dict[str, Any]],
        semantic_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {
            str(row["plan_id"]): dict(row) for row in text_rows
        }

        for row in semantic_rows:
            plan_id = str(row["plan_id"])
            existing = merged.get(plan_id)
            if existing:
                existing["semantic_similarity"] = row.get("semantic_similarity")
                continue
            merged[plan_id] = dict(row)

        return list(merged.values())

    def list_solution_patterns(
        self,
        *,
        problem_category: str | None = None,
        failure_mode: str | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        filters: list[str] = []
        params: list[Any] = []

        if problem_category:
            filters.append("problem_category ILIKE %s")
            params.append(f"%{problem_category.strip()}%")
        if failure_mode:
            filters.append("failure_mode ILIKE %s")
            params.append(f"%{failure_mode.strip()}%")
        if q and q.strip():
            filters.append(
                "(title ILIKE %s OR failure_mode ILIKE %s OR problem_category ILIKE %s)"
            )
            token = f"%{q.strip()}%"
            params.extend([token, token, token])

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        count_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS total
              FROM quality.quality_solution_patterns
             {where_clause}
            """,
            tuple(params),
        )
        total = int((count_row or {}).get("total") or 0)
        offset = max(page - 1, 0) * page_size

        rows = self.fetch_all(
            f"""
            SELECT id, title, problem_category, failure_mode, root_cause_category,
                   symptom_tags, recommended_actions, actions_to_avoid,
                   evidence_summary, effectiveness_rate, usage_count, last_used_at,
                   created_from_plan_id
              FROM quality.quality_solution_patterns
             {where_clause}
             ORDER BY effectiveness_rate DESC NULLS LAST, usage_count DESC, updated_at DESC
             LIMIT %s OFFSET %s
            """,
            tuple([*params, page_size, offset]),
        )

        return {
            "items": [self._serialize_pattern(row) for row in rows],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max((total + page_size - 1) // page_size, 1) if total else 1,
            },
        }

    def upsert_solution_pattern_from_plan(self, plan_id: str) -> dict[str, Any] | None:
        plan = self.fetch_one(
            """
            SELECT p.id, p.code, p.title, p.problem_category, p.failure_mode,
                   p.root_cause_category, p.symptom_tags, p.effectiveness_status,
                   p.effectiveness_notes, fw.root_cause
              FROM quality.quality_action_plans p
              LEFT JOIN quality.quality_five_whys fw ON fw.plan_id = p.id
             WHERE p.id = %s
               AND p.deleted_at IS NULL
            """,
            (plan_id,),
        )
        if not plan:
            return None

        if plan.get("effectiveness_status") not in {"effective", "partially_effective"}:
            raise ValueError(
                "Promova apenas planos com eficácia effective ou partially_effective."
            )

        actions = self.fetch_all(
            """
            SELECT action_type, description
              FROM quality.quality_actions
             WHERE plan_id = %s
               AND status = 'completed'
             ORDER BY completed_at DESC NULLS LAST
            """,
            (plan_id,),
        )
        recommended = [a["description"] for a in actions if a.get("description")]
        if not recommended:
            raise ValueError("O plano precisa de ao menos uma ação concluída para virar padrão.")

        title = plan.get("title") or f"Padrão derivado de {plan.get('code')}"
        effectiveness_rate = 1.0 if plan.get("effectiveness_status") == "effective" else 0.6

        existing = self.fetch_one(
            """
            SELECT id, usage_count, effectiveness_rate
              FROM quality.quality_solution_patterns
             WHERE created_from_plan_id = %s
            """,
            (plan_id,),
        )
        if existing:
            row = self.execute_returning_one(
                """
                UPDATE quality.quality_solution_patterns
                   SET title = %s,
                       problem_category = %s,
                       failure_mode = %s,
                       root_cause_category = %s,
                       symptom_tags = %s,
                       recommended_actions = %s,
                       evidence_summary = %s,
                       effectiveness_rate = %s,
                       usage_count = usage_count + 1,
                       last_used_at = NOW(),
                       updated_at = NOW()
                 WHERE id = %s
                RETURNING id, title, problem_category, failure_mode, root_cause_category,
                          symptom_tags, recommended_actions, actions_to_avoid,
                          evidence_summary, effectiveness_rate, usage_count, last_used_at,
                          created_from_plan_id
                """,
                (
                    title,
                    plan.get("problem_category"),
                    plan.get("failure_mode"),
                    plan.get("root_cause_category") or plan.get("root_cause"),
                    plan.get("symptom_tags") or [],
                    recommended,
                    plan.get("effectiveness_notes"),
                    effectiveness_rate,
                    existing["id"],
                ),
            )
        else:
            row = self.execute_returning_one(
                """
                INSERT INTO quality.quality_solution_patterns (
                    title,
                    problem_category,
                    failure_mode,
                    root_cause_category,
                    symptom_tags,
                    recommended_actions,
                    evidence_summary,
                    effectiveness_rate,
                    usage_count,
                    last_used_at,
                    created_from_plan_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, NOW(), %s)
                RETURNING id, title, problem_category, failure_mode, root_cause_category,
                          symptom_tags, recommended_actions, actions_to_avoid,
                          evidence_summary, effectiveness_rate, usage_count, last_used_at,
                          created_from_plan_id
                """,
                (
                    title,
                    plan.get("problem_category"),
                    plan.get("failure_mode"),
                    plan.get("root_cause_category") or plan.get("root_cause"),
                    plan.get("symptom_tags") or [],
                    recommended,
                    plan.get("effectiveness_notes"),
                    effectiveness_rate,
                    plan_id,
                ),
            )

        if not row:
            raise PluginsRepositoryError("Falha ao registrar padrão de solução.")
        return self._serialize_pattern(row)

    def _serialize_pattern(self, row: dict[str, Any]) -> dict[str, Any]:
        result = serialize_row(row, id_keys=("id", "created_from_plan_id")) or {}
        for key in ("symptom_tags", "recommended_actions", "actions_to_avoid"):
            if result.get(key) is None:
                result[key] = []
        if result.get("effectiveness_rate") is not None:
            result["effectiveness_rate"] = float(result["effectiveness_rate"])
        if result.get("usage_count") is not None:
            result["usage_count"] = int(result["usage_count"])
        last_used = result.get("last_used_at")
        if hasattr(last_used, "isoformat"):
            result["last_used_at"] = last_used.isoformat()
        return result
