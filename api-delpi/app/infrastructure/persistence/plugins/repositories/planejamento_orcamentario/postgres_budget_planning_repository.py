
from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

SCHEMA = "planejamento_orcamentario"


def _s(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {k: _s(v) for k, v in row.items()}


def _rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_row(r) or {} for r in rows]


def _append_unit_cost_center_pairs(
    clauses: list[str],
    params: list[Any],
    *,
    unit_col: str,
    cc_col: str,
    pairs: list[tuple[str, str]] | None,
) -> bool:
    """Filtra por pares (filial, código). Retorna False se pairs vazio ⇒ sem linhas."""
    if pairs is None:
        return True
    if not pairs:
        return False
    placeholders = ", ".join(["(%s, %s)"] * len(pairs))
    clauses.append(f"({unit_col}, {cc_col}) IN ({placeholders})")
    for unit_id, cost_center_id in pairs:
        params.extend([unit_id, cost_center_id])
    return True


def _plan_cost_center_owner_lateral_sql(*, module: str, plan_alias: str = "p") -> str:
    """Owner ativo do CC no exercício (nome para filas/aprovação)."""
    return f"""
                LEFT JOIN LATERAL (
                    SELECT
                        COALESCE(
                            NULLIF(BTRIM(r.user_name_snapshot), ''),
                            r.user_sub
                        ) AS cost_center_owner_name,
                        r.user_sub AS cost_center_owner_sub
                    FROM {SCHEMA}.budget_responsibilities r
                    WHERE r.exercise_id = {plan_alias}.exercise_id
                      AND r.unit_id = {plan_alias}.unit_id
                      AND r.cost_center_id = {plan_alias}.cost_center_id
                      AND r.module = '{module}'
                      AND r.responsibility_type = 'owner'
                      AND r.is_active = TRUE
                      AND (r.valid_from IS NULL OR r.valid_from <= CURRENT_DATE)
                      AND (r.valid_until IS NULL OR r.valid_until >= CURRENT_DATE)
                    ORDER BY r.created_at DESC
                    LIMIT 1
                ) owner ON TRUE
    """


def _plan_investment_count_lateral_sql(*, plan_alias: str = "p") -> str:
    """Contagem de investimentos ativos (status draft) do CC no exercício."""
    return f"""
                LEFT JOIN LATERAL (
                    SELECT COUNT(*)::int AS investment_count
                    FROM {SCHEMA}.capex_investments i
                    WHERE i.exercise_id = {plan_alias}.exercise_id
                      AND i.unit_id = {plan_alias}.unit_id
                      AND i.cost_center_id = {plan_alias}.cost_center_id
                      AND i.status = 'draft'
                ) inv ON TRUE
    """


class PostgresBudgetPlanningRepository(PluginBaseRepository):
    # ---- exercises ----
    def list_exercises(self) -> list[dict[str, Any]]:
        return _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.budget_exercises
                ORDER BY year DESC, created_at DESC
                """
            )
        )

    def get_exercise(self, exercise_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.budget_exercises WHERE id = %s",
                (exercise_id,),
            )
        )

    def get_exercise_by_year(self, year: int) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.budget_exercises WHERE year = %s",
                (year,),
            )
        )

    def get_active_exercise(self) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.budget_exercises WHERE is_active = TRUE LIMIT 1"
            )
        )

    def create_exercise(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.budget_exercises (
                year, name, description, status,
                preparation_starts_at, filling_starts_at, deadline_at, closed_at,
                is_active, created_by_user_id, created_by_name,
                updated_by_user_id, updated_by_name
            ) VALUES (
                %(year)s, %(name)s, %(description)s, %(status)s,
                %(preparation_starts_at)s, %(filling_starts_at)s, %(deadline_at)s, %(closed_at)s,
                %(is_active)s, %(created_by_user_id)s, %(created_by_name)s,
                %(updated_by_user_id)s, %(updated_by_name)s
            )
            RETURNING *
            """,
            payload,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao criar exercício.")
        self.commit()
        return _row(row) or {}

    def update_exercise(self, exercise_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "name", "description", "status", "preparation_starts_at", "filling_starts_at",
            "deadline_at", "closed_at", "is_active", "updated_by_user_id", "updated_by_name",
        }
        sets = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = %s")
            params.append(value)
        if not sets:
            exercise = self.get_exercise(exercise_id)
            if not exercise:
                raise PluginsRepositoryError("Exercício não encontrado.")
            return exercise
        sets.append("updated_at = NOW()")
        params.append(exercise_id)
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.budget_exercises
            SET {', '.join(sets)}
            WHERE id = %s
            RETURNING *
            """,
            tuple(params),
        )
        if not row:
            raise PluginsRepositoryError("Exercício não encontrado.")
        self.commit()
        return _row(row) or {}

    def clear_other_active(self, exercise_id: str) -> None:
        self.execute(
            f"""
            UPDATE {SCHEMA}.budget_exercises
            SET is_active = FALSE, updated_at = NOW()
            WHERE is_active = TRUE AND id <> %s
            """,
            (exercise_id,),
        )

    # ---- guidance ----
    def get_guidance_draft(self, exercise_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"""
                SELECT * FROM {SCHEMA}.guidance_versions
                WHERE exercise_id = %s AND status = 'draft'
                LIMIT 1
                """,
                (exercise_id,),
            )
        )

    def get_guidance(self, guidance_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.guidance_versions WHERE id = %s",
                (guidance_id,),
            )
        )

    def get_current_published_guidance(self, exercise_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"""
                SELECT * FROM {SCHEMA}.guidance_versions
                WHERE exercise_id = %s AND status = 'published'
                ORDER BY version_number DESC
                LIMIT 1
                """,
                (exercise_id,),
            )
        )

    def list_published_guidance(self, exercise_id: str) -> list[dict[str, Any]]:
        return _rows(
            self.fetch_all(
                f"""
                SELECT id, exercise_id, version_number, status, title, published_at,
                       published_by_user_id, published_by_name, created_at
                FROM {SCHEMA}.guidance_versions
                WHERE exercise_id = %s AND status = 'published'
                ORDER BY version_number DESC
                """,
                (exercise_id,),
            )
        )

    def create_guidance_draft(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.guidance_versions (
                exercise_id, status, title, board_message, sender_name, sender_role,
                objective, general_guidance, additional_notes,
                created_by_user_id, updated_by_user_id
            ) VALUES (
                %(exercise_id)s, 'draft', %(title)s, %(board_message)s, %(sender_name)s, %(sender_role)s,
                %(objective)s, %(general_guidance)s, %(additional_notes)s,
                %(created_by_user_id)s, %(updated_by_user_id)s
            )
            RETURNING *
            """,
            payload,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao criar orientações.")
        self.commit()
        return _row(row) or {}

    def update_guidance_draft(self, guidance_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "title", "board_message", "sender_name", "sender_role",
            "objective", "general_guidance", "additional_notes", "updated_by_user_id",
        }
        sets = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = %s")
            params.append(value)
        if not sets:
            g = self.get_guidance(guidance_id)
            if not g:
                raise PluginsRepositoryError("Orientações não encontradas.")
            return g
        sets.append("updated_at = NOW()")
        params.append(guidance_id)
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.guidance_versions
            SET {', '.join(sets)}
            WHERE id = %s AND status = 'draft'
            RETURNING *
            """,
            tuple(params),
        )
        if not row:
            raise PluginsRepositoryError("Rascunho de orientações não encontrado.")
        self.commit()
        return _row(row) or {}

    def publish_guidance(self, guidance_id: str, *, actor_id: str, actor_name: str | None) -> dict[str, Any]:
        current = self.get_guidance(guidance_id)
        if not current:
            raise PluginsRepositoryError("Orientações não encontradas.")
        if current["status"] != "draft":
            raise PluginsRepositoryError("Somente rascunho pode ser publicado.")
        max_row = self.fetch_one(
            f"""
            SELECT COALESCE(MAX(version_number), 0) AS max_version
            FROM {SCHEMA}.guidance_versions
            WHERE exercise_id = %s AND status = 'published'
            """,
            (current["exercise_id"],),
        )
        next_version = int((max_row or {}).get("max_version") or 0) + 1
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.guidance_versions
            SET status = 'published',
                version_number = %s,
                published_at = NOW(),
                published_by_user_id = %s,
                published_by_name = %s,
                updated_at = NOW()
            WHERE id = %s AND status = 'draft'
            RETURNING *
            """,
            (next_version, actor_id, actor_name, guidance_id),
        )
        if not row:
            raise PluginsRepositoryError("Falha ao publicar orientações.")
        self.commit()
        return _row(row) or {}

    def replace_premises(self, guidance_id: str, premises: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.execute(
            f"DELETE FROM {SCHEMA}.guidance_premises WHERE guidance_version_id = %s",
            (guidance_id,),
        )
        for idx, item in enumerate(premises):
            self.execute(
                f"""
                INSERT INTO {SCHEMA}.guidance_premises (
                    guidance_version_id, name, value_text, value_numeric, unit_label,
                    description, display_order, active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    guidance_id,
                    item["name"],
                    item.get("value_text"),
                    item.get("value_numeric"),
                    item.get("unit_label"),
                    item.get("description"),
                    item.get("display_order", idx),
                    bool(item.get("active", True)),
                ),
            )
        self.commit()
        return self.list_premises(guidance_id)

    def list_premises(self, guidance_id: str) -> list[dict[str, Any]]:
        return _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.guidance_premises
                WHERE guidance_version_id = %s
                ORDER BY display_order, created_at
                """,
                (guidance_id,),
            )
        )

    def replace_schedule(self, guidance_id: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.execute(
            f"DELETE FROM {SCHEMA}.guidance_schedule_items WHERE guidance_version_id = %s",
            (guidance_id,),
        )
        for idx, item in enumerate(items):
            self.execute(
                f"""
                INSERT INTO {SCHEMA}.guidance_schedule_items (
                    guidance_version_id, title, description, starts_on, ends_on,
                    display_order, highlighted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    guidance_id,
                    item["title"],
                    item.get("description"),
                    item["starts_on"],
                    item.get("ends_on"),
                    item.get("display_order", idx),
                    bool(item.get("highlighted", False)),
                ),
            )
        self.commit()
        return self.list_schedule(guidance_id)

    def list_schedule(self, guidance_id: str) -> list[dict[str, Any]]:
        return _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.guidance_schedule_items
                WHERE guidance_version_id = %s
                ORDER BY display_order, starts_on
                """,
                (guidance_id,),
            )
        )

    # ---- documents ----
    def create_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.support_documents (
                exercise_id, guidance_version_id, display_name, original_name, mime_type,
                size_bytes, document_kind, description, display_order, storage_key,
                external_url, uploaded_by_user_id, uploaded_by_name, status
            ) VALUES (
                %(exercise_id)s, %(guidance_version_id)s, %(display_name)s, %(original_name)s, %(mime_type)s,
                %(size_bytes)s, %(document_kind)s, %(description)s, %(display_order)s, %(storage_key)s,
                %(external_url)s, %(uploaded_by_user_id)s, %(uploaded_by_name)s, 'active'
            )
            RETURNING *
            """,
            payload,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao registrar documento.")
        self.commit()
        return _row(row) or {}

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.support_documents WHERE id = %s",
                (document_id,),
            )
        )

    def list_documents(
        self,
        *,
        exercise_id: str,
        guidance_version_id: str | None = None,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        clauses = ["exercise_id = %s"]
        params: list[Any] = [exercise_id]
        if guidance_version_id:
            clauses.append("(guidance_version_id = %s OR guidance_version_id IS NULL)")
            params.append(guidance_version_id)
        if active_only:
            clauses.append("status = 'active'")
        return _rows(
            self.fetch_all(
                f"""
                SELECT id, exercise_id, guidance_version_id, display_name, original_name,
                       mime_type, size_bytes, document_kind, description, display_order,
                       external_url, uploaded_by_user_id, uploaded_by_name, status,
                       created_at, updated_at, archived_at
                FROM {SCHEMA}.support_documents
                WHERE {' AND '.join(clauses)}
                ORDER BY display_order, created_at
                """,
                tuple(params),
            )
        )

    def update_document(self, document_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        allowed = {"display_name", "description", "display_order", "external_url"}
        sets = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = %s")
            params.append(value)
        sets.append("updated_at = NOW()")
        params.append(document_id)
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.support_documents
            SET {', '.join(sets)}
            WHERE id = %s
            RETURNING id, exercise_id, guidance_version_id, display_name, original_name,
                      mime_type, size_bytes, document_kind, description, display_order,
                      external_url, uploaded_by_user_id, uploaded_by_name, status,
                      created_at, updated_at, archived_at
            """,
            tuple(params),
        )
        if not row:
            raise PluginsRepositoryError("Documento não encontrado.")
        self.commit()
        return _row(row) or {}

    def archive_document(self, document_id: str, *, actor_id: str) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.support_documents
            SET status = 'archived',
                archived_at = NOW(),
                archived_by_user_id = %s,
                updated_at = NOW()
            WHERE id = %s AND status = 'active'
            RETURNING id, exercise_id, display_name, status, archived_at
            """,
            (actor_id, document_id),
        )
        if not row:
            raise PluginsRepositoryError("Documento ativo não encontrado.")
        self.commit()
        return _row(row) or {}

    # ---- acknowledgements ----
    def get_acknowledgement(self, *, user_sub: str, guidance_version_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"""
                SELECT * FROM {SCHEMA}.reading_acknowledgements
                WHERE user_sub = %s AND guidance_version_id = %s
                """,
                (user_sub, guidance_version_id),
            )
        )

    def create_acknowledgement(self, payload: dict[str, Any]) -> dict[str, Any]:
        # idempotent: ON CONFLICT DO NOTHING then select
        self.execute(
            f"""
            INSERT INTO {SCHEMA}.reading_acknowledgements (
                exercise_id, guidance_version_id, user_sub, user_name, request_id
            ) VALUES (
                %(exercise_id)s, %(guidance_version_id)s, %(user_sub)s, %(user_name)s, %(request_id)s
            )
            ON CONFLICT (user_sub, guidance_version_id) DO NOTHING
            """,
            payload,
        )
        self.commit()
        ack = self.get_acknowledgement(
            user_sub=payload["user_sub"],
            guidance_version_id=payload["guidance_version_id"],
        )
        if not ack:
            raise PluginsRepositoryError("Falha ao confirmar leitura.")
        return ack

    # ---- scopes & org catalog ----
    def list_org_units(self, *, active_only: bool = True) -> list[dict[str, Any]]:
        q = f"SELECT * FROM {SCHEMA}.org_units"
        if active_only:
            q += " WHERE active = TRUE"
        q += " ORDER BY code"
        return _rows(self.fetch_all(q))

    def list_org_areas(self, *, active_only: bool = True) -> list[dict[str, Any]]:
        q = f"SELECT * FROM {SCHEMA}.org_areas"
        if active_only:
            q += " WHERE active = TRUE"
        q += " ORDER BY code"
        return _rows(self.fetch_all(q))

    def list_org_cost_centers(
        self,
        *,
        active_only: bool = True,
        branch: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = ["TRUE"]
        params: list[Any] = []
        if active_only:
            clauses.append("active = TRUE")
        if branch:
            clauses.append("branch = %s")
            params.append(branch)
        where = " AND ".join(clauses)
        return _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.org_cost_centers
                WHERE {where}
                ORDER BY branch, code
                """,
                tuple(params),
            )
        )

    def upsert_org_cost_center(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.org_cost_centers (
                branch, code, name, unit_code, area_code, source, active, created_by_user_id
            ) VALUES (
                %(branch)s, %(code)s, %(name)s, %(unit_code)s, %(area_code)s,
                COALESCE(%(source)s, 'manual'), TRUE, %(created_by_user_id)s
            )
            ON CONFLICT (branch, code) DO UPDATE SET
                name = EXCLUDED.name,
                unit_code = EXCLUDED.unit_code,
                area_code = EXCLUDED.area_code,
                source = EXCLUDED.source,
                active = TRUE
            RETURNING *
            """,
            payload,
        )
        self.commit()
        return _row(row) or {}

    def update_org_cost_center_icon(
        self,
        *,
        branch: str,
        code: str,
        icon_key: str | None,
    ) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.org_cost_centers
            SET icon_key = %s
            WHERE branch = %s AND code = %s
            RETURNING *
            """,
            (icon_key, branch, code),
        )
        self.commit()
        return _row(row)

    def upsert_org_unit(self, code: str, name: str) -> None:
        self.execute(
            f"""
            INSERT INTO {SCHEMA}.org_units (code, name)
            VALUES (%s, %s)
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, active = TRUE
            """,
            (code, name),
        )
        self.commit()

    def upsert_org_area(self, code: str, name: str, unit_code: str | None) -> None:
        self.execute(
            f"""
            INSERT INTO {SCHEMA}.org_areas (code, name, unit_code)
            VALUES (%s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, unit_code = EXCLUDED.unit_code, active = TRUE
            """,
            (code, name, unit_code),
        )
        self.commit()

    def list_scopes(self, *, active_only: bool = False) -> list[dict[str, Any]]:
        q = f"SELECT * FROM {SCHEMA}.user_org_scopes"
        if active_only:
            q += " WHERE active = TRUE"
        q += " ORDER BY created_at DESC"
        return _rows(self.fetch_all(q))

    def list_scopes_for_user(self, user_sub: str) -> list[dict[str, Any]]:
        return _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.user_org_scopes
                WHERE user_sub = %s AND active = TRUE
                  AND (valid_from IS NULL OR valid_from <= CURRENT_DATE)
                  AND (valid_to IS NULL OR valid_to >= CURRENT_DATE)
                ORDER BY created_at DESC
                """,
                (user_sub,),
            )
        )

    def get_scope(self, scope_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.user_org_scopes WHERE id = %s",
                (scope_id,),
            )
        )

    def create_scope(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.user_org_scopes (
                user_sub, user_name, user_email, unit_code, area_code, cost_center_code,
                scope_level, role_in_scope, active, valid_from, valid_to,
                assigned_by_user_id, assigned_by_name
            ) VALUES (
                %(user_sub)s, %(user_name)s, %(user_email)s, %(unit_code)s, %(area_code)s, %(cost_center_code)s,
                %(scope_level)s, %(role_in_scope)s, TRUE, %(valid_from)s, %(valid_to)s,
                %(assigned_by_user_id)s, %(assigned_by_name)s
            )
            RETURNING *
            """,
            payload,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao criar escopo.")
        self.commit()
        return _row(row) or {}

    def update_scope(self, scope_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "user_name", "user_email", "unit_code", "area_code", "cost_center_code",
            "scope_level", "role_in_scope", "valid_from", "valid_to",
        }
        sets = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = %s")
            params.append(value)
        sets.append("updated_at = NOW()")
        params.append(scope_id)
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.user_org_scopes
            SET {', '.join(sets)}
            WHERE id = %s
            RETURNING *
            """,
            tuple(params),
        )
        if not row:
            raise PluginsRepositoryError("Escopo não encontrado.")
        self.commit()
        return _row(row) or {}

    def deactivate_scope(self, scope_id: str, *, actor_id: str) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.user_org_scopes
            SET active = FALSE,
                deactivated_at = NOW(),
                deactivated_by_user_id = %s,
                updated_at = NOW()
            WHERE id = %s AND active = TRUE
            RETURNING *
            """,
            (actor_id, scope_id),
        )
        if not row:
            raise PluginsRepositoryError("Escopo ativo não encontrado.")
        self.commit()
        return _row(row) or {}

    def find_conflicting_scope(
        self,
        *,
        user_sub: str,
        unit_code: str,
        area_code: str | None,
        cost_center_code: str | None,
        scope_level: str,
        exclude_id: str | None = None,
    ) -> dict[str, Any] | None:
        q = f"""
            SELECT * FROM {SCHEMA}.user_org_scopes
            WHERE active = TRUE
              AND user_sub = %s
              AND unit_code = %s
              AND scope_level = %s
              AND COALESCE(area_code, '') = COALESCE(%s, '')
              AND COALESCE(cost_center_code, '') = COALESCE(%s, '')
        """
        params: list[Any] = [user_sub, unit_code, scope_level, area_code, cost_center_code]
        if exclude_id:
            q += " AND id <> %s"
            params.append(exclude_id)
        q += " LIMIT 1"
        return _row(self.fetch_one(q, tuple(params)))

    def get_org_unit(self, code: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.org_units WHERE code = %s",
                (code,),
            )
        )

    def get_org_area(self, code: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.org_areas WHERE code = %s",
                (code,),
            )
        )

    def get_org_cost_center(
        self, code: str, *, branch: str | None = None
    ) -> dict[str, Any] | None:
        if branch:
            return _row(
                self.fetch_one(
                    f"""
                    SELECT * FROM {SCHEMA}.org_cost_centers
                    WHERE branch = %s AND code = %s
                    """,
                    (branch, code),
                )
            )
        rows = _rows(
            self.fetch_all(
                f"SELECT * FROM {SCHEMA}.org_cost_centers WHERE code = %s ORDER BY branch",
                (code,),
            )
        )
        if not rows:
            return None
        if len(rows) > 1:
            # Ambiguidade: caller deve passar branch
            return None
        return rows[0]

    def list_org_cost_centers_by_code(self, code: str) -> list[dict[str, Any]]:
        return _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.org_cost_centers
                WHERE code = %s
                ORDER BY branch
                """,
                (code,),
            )
        )

    def count_org_cost_centers_by_code(self, code: str) -> int:
        row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM {SCHEMA}.org_cost_centers WHERE code = %s",
            (code,),
        )
        return int((row or {}).get("total") or 0)

    # ---- budget responsibilities ----
    def get_budget_responsibility(self, responsibility_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.budget_responsibilities WHERE id = %s",
                (responsibility_id,),
            )
        )

    def find_active_budget_responsibility_conflict(
        self,
        *,
        exercise_id: str,
        module: str,
        user_sub: str,
        cost_center_id: str,
        unit_id: str | None = None,
        exclude_id: str | None = None,
    ) -> dict[str, Any] | None:
        q = f"""
            SELECT * FROM {SCHEMA}.budget_responsibilities
            WHERE is_active = TRUE
              AND exercise_id = %s
              AND module = %s
              AND user_sub = %s
              AND cost_center_id = %s
        """
        params: list[Any] = [exercise_id, module, user_sub, cost_center_id]
        if unit_id:
            q += " AND unit_id = %s"
            params.append(unit_id)
        if exclude_id:
            q += " AND id <> %s"
            params.append(exclude_id)
        q += " LIMIT 1"
        return _row(self.fetch_one(q, tuple(params)))

    def find_valid_responsibility(
        self,
        *,
        user_sub: str,
        exercise_id: str,
        module: str,
        cost_center_id: str,
        unit_id: str | None = None,
        on_date: date | None = None,
    ) -> dict[str, Any] | None:
        check = on_date or date.today()
        q = f"""
            SELECT * FROM {SCHEMA}.budget_responsibilities
            WHERE is_active = TRUE
              AND user_sub = %s
              AND exercise_id = %s
              AND module = %s
              AND cost_center_id = %s
              AND (valid_from IS NULL OR valid_from <= %s)
              AND (valid_until IS NULL OR valid_until >= %s)
        """
        params: list[Any] = [
            user_sub,
            exercise_id,
            module,
            cost_center_id,
            check,
            check,
        ]
        if unit_id:
            q += " AND unit_id = %s"
            params.append(unit_id)
        q += " LIMIT 1"
        return _row(self.fetch_one(q, tuple(params)))

    def list_budget_responsibilities(
        self,
        *,
        exercise_id: str | None = None,
        module: str | None = None,
        user_sub: str | None = None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        responsibility_type: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = ["TRUE"]
        params: list[Any] = []
        if exercise_id:
            clauses.append("exercise_id = %s")
            params.append(exercise_id)
        if module:
            clauses.append("module = %s")
            params.append(module)
        if user_sub:
            clauses.append("user_sub = %s")
            params.append(user_sub)
        if unit_id:
            clauses.append("unit_id = %s")
            params.append(unit_id)
        if area_id:
            clauses.append("area_id = %s")
            params.append(area_id)
        if cost_center_id:
            clauses.append("cost_center_id = %s")
            params.append(cost_center_id)
        if responsibility_type:
            clauses.append("responsibility_type = %s")
            params.append(responsibility_type)
        if is_active is not None:
            clauses.append("is_active = %s")
            params.append(is_active)
        where = " AND ".join(clauses)
        count_row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM {SCHEMA}.budget_responsibilities WHERE {where}",
            tuple(params),
        )
        total = int((count_row or {}).get("total") or 0)
        page_params = list(params) + [limit, offset]
        items = _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.budget_responsibilities
                WHERE {where}
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                tuple(page_params),
            )
        )
        return items, total

    def list_budget_responsibilities_for_user(
        self,
        *,
        user_sub: str,
        module: str | None = None,
        exercise_id: str | None = None,
        active_only: bool = True,
        on_date: date | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["r.user_sub = %s"]
        params: list[Any] = [user_sub]
        if module:
            clauses.append("r.module = %s")
            params.append(module)
        if exercise_id:
            clauses.append("r.exercise_id = %s")
            params.append(exercise_id)
        if active_only:
            clauses.append("r.is_active = TRUE")
            check = on_date or date.today()
            clauses.append("(r.valid_from IS NULL OR r.valid_from <= %s)")
            params.append(check)
            clauses.append("(r.valid_until IS NULL OR r.valid_until >= %s)")
            params.append(check)
        return _rows(
            self.fetch_all(
                f"""
                SELECT
                    r.*,
                    cc.name AS cost_center_name,
                    cc.icon_key AS cost_center_icon_key
                FROM {SCHEMA}.budget_responsibilities r
                LEFT JOIN {SCHEMA}.org_cost_centers cc
                    ON cc.code = r.cost_center_id
                   AND cc.branch = r.unit_id
                WHERE {' AND '.join(clauses)}
                ORDER BY r.cost_center_id, r.created_at DESC
                """,
                tuple(params),
            )
        )

    def create_budget_responsibility(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.budget_responsibilities (
                exercise_id, module, user_sub, user_name_snapshot, user_email_snapshot,
                unit_id, area_id, cost_center_id, responsibility_type,
                valid_from, valid_until, is_active, created_by, updated_by
            ) VALUES (
                %(exercise_id)s, %(module)s, %(user_sub)s, %(user_name_snapshot)s, %(user_email_snapshot)s,
                %(unit_id)s, %(area_id)s, %(cost_center_id)s, %(responsibility_type)s,
                %(valid_from)s, %(valid_until)s, TRUE, %(created_by)s, %(updated_by)s
            )
            RETURNING *
            """,
            payload,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao criar responsabilidade orçamentária.")
        self.commit()
        return _row(row) or {}

    def update_budget_responsibility(
        self, responsibility_id: str, fields: dict[str, Any]
    ) -> dict[str, Any]:
        allowed = {
            "responsibility_type",
            "valid_from",
            "valid_until",
            "user_name_snapshot",
            "user_email_snapshot",
            "updated_by",
        }
        sets: list[str] = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = %s")
            params.append(value)
        if not sets:
            current = self.get_budget_responsibility(responsibility_id)
            if not current:
                raise PluginsRepositoryError("Responsabilidade orçamentária não encontrada.")
            return current
        sets.append("updated_at = NOW()")
        params.append(responsibility_id)
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.budget_responsibilities
            SET {', '.join(sets)}
            WHERE id = %s
            RETURNING *
            """,
            tuple(params),
        )
        if not row:
            raise PluginsRepositoryError("Responsabilidade orçamentária não encontrada.")
        self.commit()
        return _row(row) or {}

    def deactivate_budget_responsibility(
        self,
        responsibility_id: str,
        *,
        actor_id: str,
        reason: str | None,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.budget_responsibilities
            SET is_active = FALSE,
                deactivated_by = %s,
                deactivated_at = NOW(),
                deactivation_reason = %s,
                updated_by = %s,
                updated_at = NOW()
            WHERE id = %s AND is_active = TRUE
            RETURNING *
            """,
            (actor_id, reason, actor_id, responsibility_id),
        )
        if not row:
            raise PluginsRepositoryError("Responsabilidade ativa não encontrada.")
        self.commit()
        return _row(row) or {}

    def reactivate_budget_responsibility(
        self, responsibility_id: str, *, actor_id: str
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.budget_responsibilities
            SET is_active = TRUE,
                deactivated_by = NULL,
                deactivated_at = NULL,
                deactivation_reason = NULL,
                updated_by = %s,
                updated_at = NOW()
            WHERE id = %s AND is_active = FALSE
            RETURNING *
            """,
            (actor_id, responsibility_id),
        )
        if not row:
            raise PluginsRepositoryError("Responsabilidade inativa não encontrada.")
        self.commit()
        return _row(row) or {}

    # ---- capex categories (Fase 2A.3) ----
    def get_capex_category(self, category_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.capex_categories WHERE id = %s",
                (category_id,),
            )
        )

    def get_capex_category_by_code(self, code: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.capex_categories WHERE code = %s",
                (code,),
            )
        )

    def list_capex_categories(
        self,
        *,
        is_active: bool | None = None,
        q: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = ["TRUE"]
        params: list[Any] = []
        if is_active is not None:
            clauses.append("is_active = %s")
            params.append(is_active)
        if q:
            clauses.append(
                "(code ILIKE %s OR name ILIKE %s OR COALESCE(description, '') ILIKE %s)"
            )
            like = f"%{q}%"
            params.extend([like, like, like])
        where = " AND ".join(clauses)
        return _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.capex_categories
                WHERE {where}
                ORDER BY display_order ASC, name ASC, code ASC
                """,
                tuple(params),
            )
        )

    def create_capex_category(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.capex_categories (
                code, name, description, display_order, icon_key, is_system_default,
                created_by, updated_by
            ) VALUES (
                %(code)s, %(name)s, %(description)s, %(display_order)s, %(icon_key)s,
                %(is_system_default)s, %(created_by)s, %(updated_by)s
            )
            RETURNING *
            """,
            {
                "code": payload["code"],
                "name": payload["name"],
                "description": payload.get("description"),
                "display_order": int(payload.get("display_order") or 0),
                "icon_key": payload.get("icon_key"),
                "is_system_default": bool(payload.get("is_system_default", False)),
                "created_by": payload["created_by"],
                "updated_by": payload.get("updated_by") or payload["created_by"],
            },
        )
        if not row:
            raise PluginsRepositoryError("Falha ao criar categoria CAPEX.")
        self.commit()
        return _row(row) or {}

    def update_capex_category(
        self, category_id: str, fields: dict[str, Any]
    ) -> dict[str, Any]:
        allowed = ("name", "description", "display_order", "icon_key", "icon_image_key", "icon_image_mime", "updated_by")
        sets: list[str] = []
        params: list[Any] = []
        for key in allowed:
            if key in fields:
                sets.append(f"{key} = %s")
                params.append(fields[key])
        if not sets:
            existing = self.get_capex_category(category_id)
            if not existing:
                raise PluginsRepositoryError("Categoria CAPEX não encontrada.")
            return existing
        sets.append("updated_at = NOW()")
        params.append(category_id)
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.capex_categories
            SET {", ".join(sets)}
            WHERE id = %s
            RETURNING *
            """,
            tuple(params),
        )
        if not row:
            raise PluginsRepositoryError("Categoria CAPEX não encontrada.")
        self.commit()
        return _row(row) or {}

    def deactivate_capex_category(
        self, category_id: str, *, actor_id: str, reason: str | None = None
    ) -> dict[str, Any]:
        del reason  # reservado — coluna de motivo não existe no catálogo
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.capex_categories
            SET is_active = FALSE,
                deactivated_by = %s,
                deactivated_at = NOW(),
                updated_by = %s,
                updated_at = NOW()
            WHERE id = %s AND is_active = TRUE
            RETURNING *
            """,
            (actor_id, actor_id, category_id),
        )
        if not row:
            raise PluginsRepositoryError("Categoria CAPEX ativa não encontrada.")
        self.commit()
        return _row(row) or {}

    def reactivate_capex_category(
        self, category_id: str, *, actor_id: str
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.capex_categories
            SET is_active = TRUE,
                deactivated_by = NULL,
                deactivated_at = NULL,
                updated_by = %s,
                updated_at = NOW()
            WHERE id = %s AND is_active = FALSE
            RETURNING *
            """,
            (actor_id, category_id),
        )
        if not row:
            raise PluginsRepositoryError("Categoria CAPEX inativa não encontrada.")
        self.commit()
        return _row(row) or {}

    # ---- capex investments (Fase 2B.1) ----
    def get_capex_investment(self, investment_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.capex_investments WHERE id = %s",
                (investment_id,),
            )
        )

    def list_capex_investments(
        self,
        *,
        exercise_id: str | None = None,
        unit_id: str | None = None,
        cost_center_id: str | None = None,
        category_id: str | None = None,
        priority: str | None = None,
        origin: str | None = None,
        status: str | None = None,
        q: str | None = None,
        cost_center_ids: list[str] | None = None,
        unit_cost_center_pairs: list[tuple[str, str]] | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = ["TRUE"]
        params: list[Any] = []
        if exercise_id:
            clauses.append("exercise_id = %s")
            params.append(exercise_id)
        if unit_id:
            clauses.append("unit_id = %s")
            params.append(unit_id)
        if cost_center_id:
            clauses.append("cost_center_id = %s")
            params.append(cost_center_id)
        if not _append_unit_cost_center_pairs(
            clauses,
            params,
            unit_col="unit_id",
            cc_col="cost_center_id",
            pairs=unit_cost_center_pairs,
        ):
            return [], 0
        if cost_center_ids is not None and unit_cost_center_pairs is None:
            if not cost_center_ids:
                return [], 0
            clauses.append("cost_center_id = ANY(%s)")
            params.append(list(cost_center_ids))
        if category_id:
            clauses.append("category_id = %s")
            params.append(category_id)
        if priority:
            clauses.append("priority = %s")
            params.append(priority)
        if origin:
            clauses.append("origin = %s")
            params.append(origin)
        if status:
            clauses.append("status = %s")
            params.append(status)
        if q:
            clauses.append(
                """(
                    COALESCE(description, '') ILIKE %s
                    OR COALESCE(justification, '') ILIKE %s
                    OR COALESCE(probable_supplier_name, '') ILIKE %s
                    OR COALESCE(observations, '') ILIKE %s
                    OR COALESCE(cost_center_id, '') ILIKE %s
                )"""
            )
            like = f"%{q}%"
            params.extend([like, like, like, like, like])
        where = " AND ".join(clauses)
        count_row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM {SCHEMA}.capex_investments WHERE {where}",
            tuple(params),
        )
        total = int((count_row or {}).get("total") or 0)
        page_params = list(params) + [limit, offset]
        items = _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.capex_investments
                WHERE {where}
                ORDER BY updated_at DESC, created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                tuple(page_params),
            )
        )
        return items, total

    def create_capex_investment(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.capex_investments (
                exercise_id, unit_id, area_id, cost_center_id, category_id,
                accounting_account_code, description, justification,
                probable_supplier_name, probable_supplier_code,
                estimated_amount, currency, required_date, priority, origin,
                classification, shift, application, observations, status,
                created_by, updated_by
            ) VALUES (
                %(exercise_id)s, %(unit_id)s, %(area_id)s, %(cost_center_id)s, %(category_id)s,
                %(accounting_account_code)s, %(description)s, %(justification)s,
                %(probable_supplier_name)s, %(probable_supplier_code)s,
                %(estimated_amount)s, %(currency)s, %(required_date)s, %(priority)s, %(origin)s,
                %(classification)s, %(shift)s, %(application)s, %(observations)s, %(status)s,
                %(created_by)s, %(updated_by)s
            )
            RETURNING *
            """,
            payload,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao criar investimento CAPEX.")
        self.commit()
        return _row(row) or {}

    def update_capex_investment(
        self,
        investment_id: str,
        fields: dict[str, Any],
        *,
        expected_version: int,
    ) -> dict[str, Any]:
        allowed = (
            "unit_id",
            "area_id",
            "cost_center_id",
            "category_id",
            "accounting_account_code",
            "description",
            "justification",
            "probable_supplier_name",
            "probable_supplier_code",
            "estimated_amount",
            "currency",
            "required_date",
            "priority",
            "origin",
            "classification",
            "shift",
            "application",
            "observations",
            "updated_by",
        )
        sets: list[str] = []
        params: list[Any] = []
        for key in allowed:
            if key in fields:
                sets.append(f"{key} = %s")
                params.append(fields[key])
        if not sets:
            existing = self.get_capex_investment(investment_id)
            if not existing:
                raise PluginsRepositoryError("Investimento CAPEX não encontrado.")
            if int(existing.get("version") or 0) != int(expected_version):
                raise PluginsRepositoryError("Conflito de versão do investimento.")
            return existing
        sets.append("version = version + 1")
        sets.append("updated_at = NOW()")
        params.extend([investment_id, int(expected_version)])
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.capex_investments
            SET {", ".join(sets)}
            WHERE id = %s AND version = %s AND status = 'draft'
            RETURNING *
            """,
            tuple(params),
        )
        if not row:
            current = self.get_capex_investment(investment_id)
            if not current:
                raise PluginsRepositoryError("Investimento CAPEX não encontrado.")
            if str(current.get("status")) != "draft":
                raise PluginsRepositoryError("Investimento arquivado não pode ser editado.")
            raise PluginsRepositoryError("Conflito de versão do investimento.")
        self.commit()
        return _row(row) or {}

    def archive_capex_investment(
        self, investment_id: str, *, actor_id: str, reason: str | None = None
    ) -> dict[str, Any]:
        del reason  # motivo opcional — não há coluna dedicada nesta fase
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.capex_investments
            SET status = 'archived',
                archived_by = %s,
                archived_at = NOW(),
                updated_by = %s,
                updated_at = NOW(),
                version = version + 1
            WHERE id = %s AND status = 'draft'
            RETURNING *
            """,
            (actor_id, actor_id, investment_id),
        )
        if not row:
            raise PluginsRepositoryError("Investimento CAPEX em rascunho não encontrado.")
        self.commit()
        return _row(row) or {}

    # ---- capex investment attachments (Fase 2B.3) ----
    def create_capex_investment_attachment(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.capex_investment_attachments (
                investment_id, attachment_type, display_name, description,
                original_filename, mime_type, file_size, storage_key,
                idempotency_key, created_by, is_active
            ) VALUES (
                %(investment_id)s, %(attachment_type)s, %(display_name)s, %(description)s,
                %(original_filename)s, %(mime_type)s, %(file_size)s, %(storage_key)s,
                %(idempotency_key)s, %(created_by)s, TRUE
            )
            RETURNING *
            """,
            payload,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao registrar anexo CAPEX.")
        self.commit()
        return _row(row) or {}

    def get_capex_investment_attachment(self, attachment_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.capex_investment_attachments WHERE id = %s",
                (attachment_id,),
            )
        )

    def get_capex_investment_attachment_by_idempotency(
        self, *, investment_id: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"""
                SELECT * FROM {SCHEMA}.capex_investment_attachments
                WHERE investment_id = %s AND idempotency_key = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (investment_id, idempotency_key),
            )
        )

    def list_capex_investment_attachments(
        self, *, investment_id: str, active_only: bool = True
    ) -> list[dict[str, Any]]:
        clauses = ["investment_id = %s"]
        params: list[Any] = [investment_id]
        if active_only:
            clauses.append("is_active = TRUE")
        return _rows(
            self.fetch_all(
                f"""
                SELECT id, investment_id, attachment_type, display_name, description,
                       original_filename, mime_type, file_size, created_by, created_at,
                       archived_by, archived_at, is_active
                FROM {SCHEMA}.capex_investment_attachments
                WHERE {' AND '.join(clauses)}
                ORDER BY created_at DESC
                """,
                tuple(params),
            )
        )

    def archive_capex_investment_attachment(
        self, attachment_id: str, *, actor_id: str
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.capex_investment_attachments
            SET is_active = FALSE,
                archived_by = %s,
                archived_at = NOW()
            WHERE id = %s AND is_active = TRUE
            RETURNING *
            """,
            (actor_id, attachment_id),
        )
        if not row:
            raise PluginsRepositoryError("Anexo CAPEX ativo não encontrado.")
        self.commit()
        return _row(row) or {}

    # ---- capex plans / workflow (Fase 2C.1) ----
    def get_capex_plan(self, plan_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"""
                SELECT
                    p.*,
                    cc.icon_key AS cost_center_icon_key,
                    cc.name AS cost_center_name,
                    owner.cost_center_owner_name,
                    owner.cost_center_owner_sub,
                    COALESCE(inv.investment_count, 0) AS investment_count
                FROM {SCHEMA}.capex_plans p
                LEFT JOIN {SCHEMA}.org_cost_centers cc
                    ON cc.code = p.cost_center_id
                   AND cc.branch = p.unit_id
                {_plan_cost_center_owner_lateral_sql(module="capex")}
                {_plan_investment_count_lateral_sql()}
                WHERE p.id = %s
                """,
                (plan_id,),
            )
        )

    def get_capex_plan_by_exercise_cc(
        self,
        *,
        exercise_id: str,
        cost_center_id: str,
        unit_id: str | None = None,
    ) -> dict[str, Any] | None:
        if unit_id:
            return _row(
                self.fetch_one(
                    f"""
                    SELECT * FROM {SCHEMA}.capex_plans
                    WHERE exercise_id = %s AND unit_id = %s AND cost_center_id = %s
                    """,
                    (exercise_id, unit_id, cost_center_id),
                )
            )
        return _row(
            self.fetch_one(
                f"""
                SELECT * FROM {SCHEMA}.capex_plans
                WHERE exercise_id = %s AND cost_center_id = %s
                """,
                (exercise_id, cost_center_id),
            )
        )

    def create_capex_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        # ON CONFLICT evita UniqueViolation (aborta a transação) em corrida de resolve.
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.capex_plans (
                exercise_id, unit_id, area_id, cost_center_id, status, version,
                created_by, updated_by
            ) VALUES (
                %(exercise_id)s, %(unit_id)s, %(area_id)s, %(cost_center_id)s, 'draft', 1,
                %(created_by)s, %(created_by)s
            )
            ON CONFLICT (exercise_id, unit_id, cost_center_id) DO NOTHING
            RETURNING *
            """,
            payload,
        )
        if row:
            return _row(row) or {}
        # Conflito sem abortar txn → use case recupera via get_*_by_exercise_cc.
        raise PluginsRepositoryError(
            "Planejamento CAPEX já existe para exercício/filial/centro de custo."
        )

    def list_capex_plans(
        self,
        *,
        exercise_id: str | None = None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        status: str | None = None,
        submitted_by: str | None = None,
        cost_center_ids: list[str] | None = None,
        unit_cost_center_pairs: list[tuple[str, str]] | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = ["TRUE"]
        params: list[Any] = []
        if exercise_id:
            clauses.append("exercise_id = %s")
            params.append(exercise_id)
        if unit_id:
            clauses.append("unit_id = %s")
            params.append(unit_id)
        if area_id:
            clauses.append("area_id = %s")
            params.append(area_id)
        if cost_center_id:
            clauses.append("cost_center_id = %s")
            params.append(cost_center_id)
        if not _append_unit_cost_center_pairs(
            clauses,
            params,
            unit_col="unit_id",
            cc_col="cost_center_id",
            pairs=unit_cost_center_pairs,
        ):
            return [], 0
        if cost_center_ids is not None and unit_cost_center_pairs is None:
            if not cost_center_ids:
                return [], 0
            clauses.append("cost_center_id = ANY(%s)")
            params.append(list(cost_center_ids))
        if status:
            clauses.append("status = %s")
            params.append(status)
        if submitted_by:
            clauses.append("submitted_by = %s")
            params.append(submitted_by)
        where = " AND ".join(clauses)
        count_row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM {SCHEMA}.capex_plans WHERE {where}",
            tuple(params),
        )
        total = int((count_row or {}).get("total") or 0)
        items = _rows(
            self.fetch_all(
                f"""
                SELECT
                    p.*,
                    cc.icon_key AS cost_center_icon_key,
                    cc.name AS cost_center_name,
                    owner.cost_center_owner_name,
                    owner.cost_center_owner_sub,
                    COALESCE(inv.investment_count, 0) AS investment_count
                FROM (
                    SELECT * FROM {SCHEMA}.capex_plans
                    WHERE {where}
                    ORDER BY updated_at DESC, created_at DESC, id DESC
                    LIMIT %s OFFSET %s
                ) p
                LEFT JOIN {SCHEMA}.org_cost_centers cc
                    ON cc.code = p.cost_center_id
                   AND cc.branch = p.unit_id
                {_plan_cost_center_owner_lateral_sql(module="capex")}
                {_plan_investment_count_lateral_sql()}
                """,
                tuple(list(params) + [limit, offset]),
            )
        )
        return items, total

    def transition_capex_plan(
        self,
        plan_id: str,
        *,
        expected_version: int,
        new_status: str,
        actor_id: str,
        submitted_by: str | None = None,
        submitted_by_name: str | None = None,
        clear_submission: bool = False,
        reviewed_by: str | None = None,
        decision_comment: str | None = None,
        clear_review: bool = False,
    ) -> dict[str, Any]:
        sets = [
            "status = %s",
            "version = version + 1",
            "updated_by = %s",
            "updated_at = NOW()",
        ]
        params: list[Any] = [new_status, actor_id]
        if submitted_by is not None:
            sets.append("submitted_by = %s")
            sets.append("submitted_at = NOW()")
            params.append(submitted_by)
            if submitted_by_name is not None:
                sets.append("submitted_by_name = %s")
                params.append(submitted_by_name)
        if clear_submission:
            sets.append("submitted_by = NULL")
            sets.append("submitted_by_name = NULL")
            sets.append("submitted_at = NULL")
        if reviewed_by is not None:
            sets.append("reviewed_by = %s")
            sets.append("reviewed_at = NOW()")
            params.append(reviewed_by)
        if clear_review:
            sets.append("reviewed_by = NULL")
            sets.append("reviewed_at = NULL")
        if decision_comment is not None:
            sets.append("decision_comment = %s")
            params.append(decision_comment)
        params.extend([plan_id, expected_version])
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.capex_plans
            SET {', '.join(sets)}
            WHERE id = %s AND version = %s
            RETURNING *
            """,
            tuple(params),
        )
        if not row:
            raise PluginsRepositoryError("Conflito de versão ou planejamento não encontrado.")
        self.commit()
        return _row(row) or {}

    def append_capex_plan_history(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = {
            "plan_id": payload.get("plan_id"),
            "action": payload.get("action"),
            "previous_status": payload.get("previous_status"),
            "new_status": payload.get("new_status"),
            "comment": payload.get("comment"),
            "actor_sub": payload.get("actor_sub"),
            "actor_name": payload.get("actor_name"),
            "investment_id": payload.get("investment_id"),
        }
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.capex_plan_history (
                plan_id, action, previous_status, new_status, comment,
                actor_sub, actor_name, investment_id
            ) VALUES (
                %(plan_id)s, %(action)s, %(previous_status)s, %(new_status)s, %(comment)s,
                %(actor_sub)s, %(actor_name)s, %(investment_id)s
            )
            RETURNING *
            """,
            data,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao registrar histórico do planejamento.")
        self.commit()
        return _row(row) or {}

    def set_capex_investment_review(
        self,
        investment_id: str,
        *,
        review_status: str,
        review_comment: str | None,
        reviewed_by: str,
        reviewed_by_name: str | None = None,
    ) -> dict[str, Any]:
        clear = review_status == "pending"
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.capex_investments
            SET review_status = %s,
                review_comment = %s,
                reviewed_by = %s,
                reviewed_by_name = %s,
                reviewed_at = CASE WHEN %s THEN NULL ELSE NOW() END
            WHERE id = %s AND status = 'draft'
            RETURNING *
            """,
            (
                review_status,
                None if clear else review_comment,
                None if clear else reviewed_by,
                None if clear else reviewed_by_name,
                clear,
                investment_id,
            ),
        )
        if not row:
            raise PluginsRepositoryError("Investimento CAPEX não encontrado ou arquivado.")
        self.commit()
        return _row(row) or {}

    def stamp_capex_investment_reviews(
        self,
        *,
        exercise_id: str,
        cost_center_id: str,
        unit_id: str | None,
        review_status: str,
        reviewed_by: str | None = None,
        reviewed_by_name: str | None = None,
        review_comment: str | None = None,
    ) -> None:
        unit = str(unit_id or "").strip()
        if not unit:
            raise PluginsRepositoryError(
                "Filial (unit_id) é obrigatória ao carimbar revisões de investimentos."
            )
        clauses = [
            "exercise_id = %s",
            "unit_id = %s",
            "cost_center_id = %s",
            "status = 'draft'",
        ]
        where_params: list[Any] = [exercise_id, unit, cost_center_id]
        clear = review_status == "pending"
        params: list[Any] = [
            review_status,
            None if clear else review_comment,
            None if clear else reviewed_by,
            None if clear else reviewed_by_name,
            clear,
            *where_params,
        ]
        self.execute(
            f"""
            UPDATE {SCHEMA}.capex_investments
            SET review_status = %s,
                review_comment = %s,
                reviewed_by = %s,
                reviewed_by_name = %s,
                reviewed_at = CASE WHEN %s THEN NULL ELSE NOW() END
            WHERE {" AND ".join(clauses)}
            """,
            tuple(params),
        )
        self.commit()

    def list_capex_plan_history(self, plan_id: str) -> list[dict[str, Any]]:
        return _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.capex_plan_history
                WHERE plan_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (plan_id,),
            )
        )

    # ---- CAPEX consolidation (Fase 2D.1) ----
    def list_capex_consolidation_rows(
        self,
        *,
        exercise_id: str,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        category_id: str | None = None,
        priority: str | None = None,
        origin: str | None = None,
        plan_status: str | None = None,
        required_date_from: str | None = None,
        required_date_to: str | None = None,
        cost_center_ids: list[str] | None = None,
        unit_cost_center_pairs: list[tuple[str, str]] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort_by: str = "updated_at",
        sort_dir: str = "desc",
    ) -> tuple[list[dict[str, Any]], int]:
        """Investimentos não arquivados + plano (LEFT JOIN) + rótulos org/categoria.

        Plano inexistente ⇒ status efetivo tratado como draft no serviço de domínio.
        """
        clauses: list[str] = [
            "i.exercise_id = %s",
            "i.status <> 'archived'",
        ]
        params: list[Any] = [exercise_id]

        if unit_id:
            clauses.append("i.unit_id = %s")
            params.append(unit_id)
        if area_id:
            clauses.append("i.area_id = %s")
            params.append(area_id)
        if cost_center_id:
            clauses.append("i.cost_center_id = %s")
            params.append(cost_center_id)
        if not _append_unit_cost_center_pairs(
            clauses,
            params,
            unit_col="i.unit_id",
            cc_col="i.cost_center_id",
            pairs=unit_cost_center_pairs,
        ):
            return [], 0
        if cost_center_ids is not None and unit_cost_center_pairs is None:
            if not cost_center_ids:
                return [], 0
            clauses.append("i.cost_center_id = ANY(%s)")
            params.append(list(cost_center_ids))
        if category_id:
            clauses.append("i.category_id = %s")
            params.append(category_id)
        if priority:
            clauses.append("i.priority = %s")
            params.append(priority)
        if origin:
            clauses.append("i.origin = %s")
            params.append(origin)
        if plan_status:
            if plan_status == "draft":
                clauses.append("(p.status IS NULL OR p.status = %s)")
            else:
                clauses.append("p.status = %s")
            params.append(plan_status)
        if required_date_from:
            clauses.append("i.required_date >= %s")
            params.append(required_date_from)
        if required_date_to:
            clauses.append("i.required_date <= %s")
            params.append(required_date_to)

        where = " AND ".join(clauses)
        from_sql = f"""
            FROM {SCHEMA}.capex_investments i
            LEFT JOIN {SCHEMA}.capex_plans p
              ON p.exercise_id = i.exercise_id
             AND p.unit_id = i.unit_id
             AND p.cost_center_id = i.cost_center_id
            LEFT JOIN {SCHEMA}.capex_categories c
              ON c.id = i.category_id
            LEFT JOIN {SCHEMA}.org_units u
              ON u.code = i.unit_id
            LEFT JOIN {SCHEMA}.org_areas a
              ON a.code = i.area_id
            LEFT JOIN {SCHEMA}.org_cost_centers cc
              ON cc.branch = i.unit_id
             AND cc.code = i.cost_center_id
        """

        count_row = self.fetch_one(
            f"SELECT COUNT(*) AS total {from_sql} WHERE {where}",
            tuple(params),
        )
        total = int((count_row or {}).get("total") or 0)

        sort_map = {
            "cost_center_id": "i.cost_center_id",
            "unit_id": "i.unit_id",
            "area_id": "i.area_id",
            "description": "i.description",
            "estimated_amount": "i.estimated_amount",
            "required_date": "i.required_date",
            "priority": "i.priority",
            "origin": "i.origin",
            "plan_status": "COALESCE(p.status, 'draft')",
            "updated_at": "i.updated_at",
            "created_at": "i.created_at",
        }
        order_col = sort_map.get(sort_by, "i.updated_at")
        direction = "ASC" if str(sort_dir).lower() == "asc" else "DESC"

        sql = f"""
            SELECT
                i.*,
                p.id AS plan_id,
                COALESCE(p.status, 'draft') AS plan_status,
                p.submitted_by AS plan_submitted_by,
                p.submitted_at AS plan_submitted_at,
                c.code AS category_code,
                c.name AS category_name,
                u.name AS unit_name,
                a.name AS area_name,
                cc.name AS cost_center_name
            {from_sql}
            WHERE {where}
            ORDER BY {order_col} {direction}, i.id DESC
        """
        page_params = list(params)
        if limit is not None:
            sql += " LIMIT %s OFFSET %s"
            page_params.extend([int(limit), int(offset or 0)])

        items = _rows(self.fetch_all(sql, tuple(page_params)))
        return items, total

    # ---- personnel plans / lines (Fase 3B.1 / 3B.1.1 — cargo livre) ----
    def get_personnel_plan(self, plan_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"""
                SELECT
                    p.*,
                    cc.icon_key AS cost_center_icon_key,
                    cc.name AS cost_center_name,
                    owner.cost_center_owner_name,
                    owner.cost_center_owner_sub
                FROM {SCHEMA}.personnel_plans p
                LEFT JOIN {SCHEMA}.org_cost_centers cc
                    ON cc.code = p.cost_center_id
                   AND cc.branch = p.unit_id
                {_plan_cost_center_owner_lateral_sql(module="personnel")}
                WHERE p.id = %s
                """,
                (plan_id,),
            )
        )

    def get_personnel_plan_by_exercise_cc(
        self,
        *,
        exercise_id: str,
        cost_center_id: str,
        unit_id: str,
    ) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"""
                SELECT * FROM {SCHEMA}.personnel_plans
                WHERE exercise_id = %s AND unit_id = %s AND cost_center_id = %s
                """,
                (exercise_id, unit_id, cost_center_id),
            )
        )

    def create_personnel_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        # ON CONFLICT evita UniqueViolation (aborta a transação) em corrida de resolve.
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.personnel_plans (
                exercise_id, unit_id, area_id, cost_center_id, status, version,
                created_by, updated_by
            ) VALUES (
                %(exercise_id)s, %(unit_id)s, %(area_id)s, %(cost_center_id)s, 'draft', 1,
                %(created_by)s, %(created_by)s
            )
            ON CONFLICT (exercise_id, unit_id, cost_center_id) DO NOTHING
            RETURNING *
            """,
            payload,
        )
        if row:
            return _row(row) or {}
        # Conflito sem abortar txn → use case recupera via get_*_by_exercise_cc.
        raise PluginsRepositoryError(
            "Planejamento de Pessoal já existe para exercício/filial/centro de custo."
        )

    def list_personnel_plans(
        self,
        *,
        exercise_id: str | None = None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        status: str | None = None,
        submitted_by: str | None = None,
        unit_cost_center_pairs: list[tuple[str, str]] | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = ["TRUE"]
        params: list[Any] = []
        if exercise_id:
            clauses.append("exercise_id = %s")
            params.append(exercise_id)
        if unit_id:
            clauses.append("unit_id = %s")
            params.append(unit_id)
        if area_id:
            clauses.append("area_id = %s")
            params.append(area_id)
        if cost_center_id:
            clauses.append("cost_center_id = %s")
            params.append(cost_center_id)
        if status:
            clauses.append("status = %s")
            params.append(status)
        if submitted_by:
            clauses.append("submitted_by = %s")
            params.append(submitted_by)
        if not _append_unit_cost_center_pairs(
            clauses,
            params,
            unit_col="unit_id",
            cc_col="cost_center_id",
            pairs=unit_cost_center_pairs,
        ):
            return [], 0
        where = " AND ".join(clauses)
        count_row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM {SCHEMA}.personnel_plans WHERE {where}",
            tuple(params),
        )
        total = int((count_row or {}).get("total") or 0)
        items = _rows(
            self.fetch_all(
                f"""
                SELECT
                    p.*,
                    cc.icon_key AS cost_center_icon_key,
                    cc.name AS cost_center_name,
                    owner.cost_center_owner_name,
                    owner.cost_center_owner_sub
                FROM (
                    SELECT * FROM {SCHEMA}.personnel_plans
                    WHERE {where}
                    ORDER BY updated_at DESC, created_at DESC, id DESC
                    LIMIT %s OFFSET %s
                ) p
                LEFT JOIN {SCHEMA}.org_cost_centers cc
                    ON cc.code = p.cost_center_id
                   AND cc.branch = p.unit_id
                {_plan_cost_center_owner_lateral_sql(module="personnel")}
                """,
                tuple(list(params) + [limit, offset]),
            )
        )
        return items, total

    def transition_personnel_plan(
        self,
        plan_id: str,
        *,
        expected_version: int,
        new_status: str,
        actor_id: str,
        submitted_by: str | None = None,
        submitted_by_name: str | None = None,
        reviewed_by: str | None = None,
        decision_comment: str | None = None,
        clear_review: bool = False,
        clear_submission: bool = False,
    ) -> dict[str, Any]:
        sets = [
            "status = %s",
            "version = version + 1",
            "updated_by = %s",
            "updated_at = NOW()",
        ]
        params: list[Any] = [new_status, actor_id]
        if submitted_by is not None:
            sets.append("submitted_by = %s")
            sets.append("submitted_at = NOW()")
            params.append(submitted_by)
            if submitted_by_name is not None:
                sets.append("submitted_by_name = %s")
                params.append(submitted_by_name)
        if clear_submission:
            sets.append("submitted_by = NULL")
            sets.append("submitted_by_name = NULL")
            sets.append("submitted_at = NULL")
        if reviewed_by is not None:
            sets.append("reviewed_by = %s")
            sets.append("reviewed_at = NOW()")
            params.append(reviewed_by)
        if clear_review:
            sets.append("reviewed_by = NULL")
            sets.append("reviewed_at = NULL")
        if decision_comment is not None:
            sets.append("decision_comment = %s")
            params.append(decision_comment)
        params.extend([plan_id, expected_version])
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.personnel_plans
            SET {', '.join(sets)}
            WHERE id = %s AND version = %s
            RETURNING *
            """,
            tuple(params),
        )
        if not row:
            raise PluginsRepositoryError(
                "Conflito de versão ou planejamento de Pessoal não encontrado."
            )
        self.commit()
        return _row(row) or {}

    def append_personnel_plan_history(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.personnel_plan_history (
                plan_id, action, previous_status, new_status, comment,
                actor_sub, actor_name
            ) VALUES (
                %(plan_id)s, %(action)s, %(previous_status)s, %(new_status)s, %(comment)s,
                %(actor_sub)s, %(actor_name)s
            )
            RETURNING *
            """,
            payload,
        )
        if not row:
            raise PluginsRepositoryError(
                "Falha ao registrar histórico do planejamento de Pessoal."
            )
        self.commit()
        return _row(row) or {}

    def list_personnel_plan_history(self, plan_id: str) -> list[dict[str, Any]]:
        return _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.personnel_plan_history
                WHERE plan_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (plan_id,),
            )
        )

    def get_personnel_plan_line(self, line_id: str) -> dict[str, Any] | None:
        return _row(
            self.fetch_one(
                f"SELECT * FROM {SCHEMA}.personnel_plan_lines WHERE id = %s",
                (line_id,),
            )
        )

    def get_personnel_plan_line_by_plan_position_name(
        self,
        *,
        plan_id: str,
        position_name: str,
        active_only: bool = True,
    ) -> dict[str, Any] | None:
        sql = f"""
            SELECT * FROM {SCHEMA}.personnel_plan_lines
            WHERE plan_id = %s
              AND lower(BTRIM(position_name)) = lower(BTRIM(%s))
        """
        params: list[Any] = [plan_id, position_name]
        if active_only:
            sql += " AND is_active = TRUE"
        return _row(self.fetch_one(sql, tuple(params)))

    def list_personnel_plan_lines(
        self, *, plan_id: str, active_only: bool = True
    ) -> list[dict[str, Any]]:
        clauses = ["plan_id = %s"]
        params: list[Any] = [plan_id]
        if active_only:
            clauses.append("is_active = TRUE")
        where = " AND ".join(clauses)
        return _rows(
            self.fetch_all(
                f"""
                SELECT * FROM {SCHEMA}.personnel_plan_lines
                WHERE {where}
                ORDER BY created_at ASC, id ASC
                """,
                tuple(params),
            )
        )

    def create_personnel_plan_line(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {SCHEMA}.personnel_plan_lines (
                plan_id, position_name,
                headcount_dec_2025, headcount_oct_2026,
                headcount_forecast, headcount_dec_2027,
                observations, version, is_active,
                created_by, updated_by
            ) VALUES (
                %(plan_id)s, %(position_name)s,
                %(headcount_dec_2025)s, %(headcount_oct_2026)s,
                %(headcount_forecast)s, %(headcount_dec_2027)s,
                %(observations)s, 1, TRUE,
                %(created_by)s, %(updated_by)s
            )
            RETURNING *
            """,
            payload,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao criar linha de Pessoal.")
        self.commit()
        return _row(row) or {}

    def update_personnel_plan_line(
        self,
        line_id: str,
        fields: dict[str, Any],
        *,
        expected_version: int,
    ) -> dict[str, Any]:
        allowed = (
            "position_name",
            "headcount_dec_2025",
            "headcount_oct_2026",
            "headcount_forecast",
            "headcount_dec_2027",
            "observations",
            "updated_by",
        )
        sets: list[str] = []
        params: list[Any] = []
        for key in allowed:
            if key in fields:
                sets.append(f"{key} = %s")
                params.append(fields[key])
        if not sets:
            existing = self.get_personnel_plan_line(line_id)
            if not existing:
                raise PluginsRepositoryError("Linha de Pessoal não encontrada.")
            if int(existing.get("version") or 0) != int(expected_version):
                raise PluginsRepositoryError("Conflito de versão da linha de Pessoal.")
            return existing
        sets.append("version = version + 1")
        sets.append("updated_at = NOW()")
        params.extend([line_id, int(expected_version)])
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.personnel_plan_lines
            SET {", ".join(sets)}
            WHERE id = %s AND version = %s AND is_active = TRUE
            RETURNING *
            """,
            tuple(params),
        )
        if not row:
            current = self.get_personnel_plan_line(line_id)
            if not current:
                raise PluginsRepositoryError("Linha de Pessoal não encontrada.")
            if not current.get("is_active"):
                raise PluginsRepositoryError("Linha arquivada não pode ser editada.")
            raise PluginsRepositoryError("Conflito de versão da linha de Pessoal.")
        self.commit()
        return _row(row) or {}

    def archive_personnel_plan_line(
        self, line_id: str, *, actor_id: str
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            UPDATE {SCHEMA}.personnel_plan_lines
            SET is_active = FALSE,
                updated_by = %s,
                updated_at = NOW(),
                version = version + 1
            WHERE id = %s AND is_active = TRUE
            RETURNING *
            """,
            (actor_id, line_id),
        )
        if not row:
            raise PluginsRepositoryError("Linha de Pessoal ativa não encontrada.")
        self.commit()
        return _row(row) or {}

    # ---- audit ----
    def append_audit(
        self,
        *,
        exercise_id: str | None,
        entity_type: str,
        entity_id: str | None,
        action: str,
        actor_user_id: str,
        actor_name: str | None,
        before_state: dict[str, Any] | None,
        after_state: dict[str, Any] | None,
        request_id: str | None = None,
    ) -> None:
        self.execute(
            f"""
            INSERT INTO {SCHEMA}.audit_events (
                exercise_id, entity_type, entity_id, action,
                actor_user_id, actor_name, before_state, after_state, request_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
            """,
            (
                exercise_id,
                entity_type,
                entity_id,
                action,
                actor_user_id,
                actor_name,
                json.dumps(before_state) if before_state is not None else None,
                json.dumps(after_state) if after_state is not None else None,
                request_id,
            ),
        )
        self.commit()
