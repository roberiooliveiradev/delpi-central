"""Adapter PostgreSQL do workflow Central de Fechamento.

Schema próprio `controllership_finance` (CP-D01=A). Toda mutação executa
em transação única e registra evento append-only em `closing_audit_event`.
Idempotência e concorrência resolvem no banco (UNIQUE + índice parcial +
`revision` otimista + `ON CONFLICT`), nunca em lógica otimista do cliente.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist import (
    document_requirement as planner,
)
from controllership_finance_app.domain.closing_checklist.errors import (
    CatalogDraftConflict,
    ChecklistDomainError,
    CompetenceNotOpened,
    DraftAlreadyOpen,
    EmptyResultingChecklist,
    InvalidRequirementWindow,
    ItemNotFound,
    CatalogNotEmpty,
    CompletionReconciliationError,
    DuplicateItemKey,
    IdempotencyConflict,
    ItemRetired,
    OperationBusy,
    OperationNotRepeatable,
    PersistenceUnavailable,
    RevisionNotFound,
    SeriesConfirmationRequired,
    SeriesNotFound,
    SyncEventNotFound,
    SyncRetryNotAllowed,
    RetroactiveEffectivePeriod,
    StaleRevision,
    TemplateNotFound,
    VersionNotDraft,
    VersionNotFound,
    VersionNotInReview,
    VersionNotPublished,
    VersionReferenced,
    WindowCoversOpenCompetence,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

_SCHEMA = SCHEMA_NAME


def _q(table: str) -> str:
    return f"{_SCHEMA}.{table}"


class ClosingChecklistRepository:
    """Repository/port implementation — psycopg connection-per-call."""

    def _conn(self) -> psycopg.Connection:
        if not plugins_db_configured():
            raise PersistenceUnavailable(
                "Persistência do workflow não configurada."
            )
        try:
            return plugins_db_connect()
        except psycopg.Error as exc:
            raise PersistenceUnavailable(
                "Persistência do workflow indisponível."
            ) from exc

    # -- template / versions -------------------------------------------------

    def list_templates(self) -> list[dict[str, Any]]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT t.template_id, t.code, t.name, t.description,
                       t.created_at,
                       (SELECT max(v.version)
                          FROM {_q('checklist_template_version')} v
                         WHERE v.template_id = t.template_id
                           AND v.status = 'PUBLISHED') AS published_version,
                       (SELECT max(v.version)
                          FROM {_q('checklist_template_version')} v
                         WHERE v.template_id = t.template_id
                           AND v.status = 'DRAFT') AS draft_version
                  FROM {_q('checklist_template')} t
                 ORDER BY t.code
                """
            )
            return cur.fetchall()

    def get_template(self, template_id: str) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT template_id, code, name, description, created_at
                  FROM {_q('checklist_template')}
                 WHERE template_id = %s
                """,
                (template_id,),
            )
            row = cur.fetchone()
        if row is None:
            raise TemplateNotFound("Template de checklist não encontrado.")
        return row

    def list_versions(self, template_id: str) -> list[dict[str, Any]]:
        self.get_template(template_id)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT v.version_id, v.template_id, v.series_id,
                       s.series_no, v.version, v.status,
                       v.revision, v.effective_from_period, v.published_by,
                       v.published_at, v.inactivated_at, v.created_at,
                       (SELECT count(*) FROM {_q('checklist_template_item')} i
                         WHERE i.version_id = v.version_id) AS item_count
                  FROM {_q('checklist_template_version')} v
                  JOIN {_q('checklist_template_series')} s
                    ON s.series_id = v.series_id
                 WHERE v.template_id = %s
                 ORDER BY s.series_no, v.version
                """,
                (template_id,),
            )
            return cur.fetchall()

    def get_version(self, template_id: str, version: int) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT v.version_id, v.template_id, v.version, v.status,
                       v.revision, v.effective_from_period, v.published_by,
                       v.published_at, v.inactivated_by, v.inactivated_at,
                       v.created_at, v.series_id, s.series_no
                  FROM {_q('checklist_template_version')} v
                  JOIN {_q('checklist_template_series')} s
                    ON s.series_id = v.series_id
                 WHERE v.template_id = %s AND v.version = %s
                 ORDER BY s.series_no DESC LIMIT 1
                """,
                (template_id, version),
            )
            row = cur.fetchone()
        if row is None:
            raise VersionNotFound("Versão de checklist não encontrada.")
        return row

    def get_version_with_items(
        self, template_id: str, version: int
    ) -> dict[str, Any]:
        version_row = self.get_version(template_id, version)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT item_id, item_key, sort_order, sheet, name, purpose,
                       origin_kind, recipient_area, applicability,
                       branch_scope, totvs_report_ref, requirement_notes,
                       validation_scope, item_state, retired_revision_id,
                       retired_by, retired_at
                  FROM {_q('checklist_template_item')}
                 WHERE version_id = %s
                 ORDER BY sort_order
                """,
                (version_row["version_id"],),
            )
            version_row["items"] = cur.fetchall()
        return version_row

    def list_template_events(
        self, template_id: str, version: int | None = None
    ) -> list[dict[str, Any]]:
        """Eventos append-only das versões do template (P6 auditoria)."""
        self.get_template(template_id)
        version_expr = (
            "COALESCE(v.version, "
            "CASE WHEN e.detail ? 'version' AND "
            "e.detail->>'version' ~ '^[0-9]+$' "
            "THEN (e.detail->>'version')::int END)"
        )
        clauses = [
            "e.entity_type = 'checklist_template_version'",
            "(v.template_id = %s OR (v.version_id IS NULL AND "
            "e.detail->>'template_id' = %s))",
        ]
        params: list[Any] = [template_id, template_id]
        if version is not None:
            clauses.append(f"{version_expr} = %s")
            params.append(version)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT e.event_id, e.entity_id, e.competence_id,
                       e.event_type, e.actor_subject, e.detail,
                       e.created_at, {version_expr} AS version
                  FROM {_q('closing_audit_event')} e
                  LEFT JOIN {_q('checklist_template_version')} v
                    ON v.version_id = e.entity_id
                 WHERE {' AND '.join(clauses)}
                 ORDER BY e.created_at DESC
                 LIMIT 200
                """,
                params,
            )
            return cur.fetchall()

    def create_draft_version(
        self, template_id: str, actor: str
    ) -> dict[str, Any]:
        """Cria DRAFT clonando itens da versão mais recente.

        Índice parcial único garante um DRAFT por template — corrida vira
        `draft_already_open` (409), nunca dois rascunhos.
        """
        with self._conn() as conn:
            try:
                with conn.transaction():
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute(
                            f"""
                            SELECT template_id FROM {_q('checklist_template')}
                             WHERE template_id = %s FOR UPDATE
                            """,
                            (template_id,),
                        )
                        if cur.fetchone() is None:
                            raise TemplateNotFound(
                                "Template de checklist não encontrado."
                            )
                        cur.execute(
                            f"""
                            SELECT version_id, version
                              FROM {_q('checklist_template_version')}
                             WHERE template_id = %s
                             ORDER BY version DESC LIMIT 1
                            """,
                            (template_id,),
                        )
                        latest = cur.fetchone()
                        series_id = self._active_series_id_locked(
                            cur, template_id, actor
                        )
                        next_version = self._next_version_locked(
                            cur, template_id, series_id
                        )
                        cur.execute(
                            f"""
                            INSERT INTO {_q('checklist_template_version')}
                                (template_id, series_id, version, status,
                                 created_by)
                            VALUES (%s, %s, %s, 'DRAFT', %s)
                            RETURNING version_id, version, status, revision
                            """,
                            (template_id, series_id, next_version, actor),
                        )
                        draft = cur.fetchone()
                        if latest is not None:
                            cur.execute(
                                f"""
                                INSERT INTO {_q('checklist_template_item')}
                                    (version_id, item_key, sort_order, sheet,
                                     name, purpose, origin_kind,
                                     recipient_area, applicability,
                                     branch_scope, totvs_report_ref,
                                     requirement_notes, validation_scope)
                                SELECT %s, item_key, sort_order, sheet, name,
                                       purpose, origin_kind, recipient_area,
                                       applicability, branch_scope,
                                       totvs_report_ref, requirement_notes,
                                       validation_scope
                                  FROM {_q('checklist_template_item')}
                                 WHERE version_id = %s
                                 ORDER BY sort_order
                                """,
                                (draft["version_id"], latest["version_id"]),
                            )
                        self._audit(
                            cur,
                            entity_type="checklist_template_version",
                            entity_id=draft["version_id"],
                            event_type="DRAFT_CREATED",
                            actor=actor,
                            detail={
                                "template_id": template_id,
                                "version": next_version,
                                "cloned_from_version_id": (
                                    str(latest["version_id"])
                                    if latest
                                    else None
                                ),
                            },
                        )
            except psycopg.errors.UniqueViolation as exc:
                raise DraftAlreadyOpen(
                    "Já existe uma versão DRAFT aberta para este template."
                ) from exc
        return draft

    def update_draft_items(
        self,
        template_id: str,
        version: int,
        expected_revision: int,
        items: list[dict[str, Any]],
        actor: str,
    ) -> dict[str, Any]:
        """Substitui itens do DRAFT em transação única.

        `revision` otimista: 0 linhas => `stale_revision` ou estado inválido.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_template_version')}
                           SET revision = revision + 1, updated_at = now()
                         WHERE version_id = (
                            SELECT v2.version_id
                              FROM {_q('checklist_template_version')} v2
                              JOIN {_q('checklist_template_series')} s2
                                ON s2.series_id = v2.series_id
                             WHERE v2.template_id = %s AND v2.version = %s
                             ORDER BY s2.series_no DESC LIMIT 1
                        )
                           AND status = 'DRAFT' AND revision = %s
                        RETURNING version_id, revision
                        """,
                        (template_id, version, expected_revision),
                    )
                    updated = cur.fetchone()
                    if updated is None:
                        current = self._version_status(cur, template_id, version)
                        if current is None:
                            raise VersionNotFound(
                                "Versão de checklist não encontrada."
                            )
                        if current["status"] != "DRAFT":
                            raise VersionNotDraft(
                                "Somente versões DRAFT podem ser editadas."
                            )
                        raise StaleRevision(
                            "Revisão desatualizada — recarregue a versão."
                        )
                    cur.execute(
                        f"DELETE FROM {_q('checklist_template_item')}"
                        " WHERE version_id = %s",
                        (updated["version_id"],),
                    )
                    try:
                        for position, item in enumerate(items, start=1):
                            cur.execute(
                                f"""
                                INSERT INTO {_q('checklist_template_item')}
                                    (version_id, item_key, sort_order,
                                     sheet, name, purpose, origin_kind,
                                     recipient_area, applicability,
                                     branch_scope, totvs_report_ref,
                                     requirement_notes, validation_scope)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                """,
                                (
                                    updated["version_id"],
                                    item["item_key"],
                                    item.get("sort_order") or position,
                                    item["sheet"],
                                    item["name"],
                                    item.get("purpose"),
                                    item["origin_kind"],
                                    item.get("recipient_area"),
                                    item.get("applicability") or "REQUIRED",
                                    item.get("branch_scope") or "BOTH",
                                    item.get("totvs_report_ref"),
                                    item.get("requirement_notes"),
                                    item.get("validation_scope")
                                    or "PER_ATTACHMENT",
                                ),
                            )
                    except psycopg.errors.UniqueViolation as exc:
                        raise DuplicateItemKey(
                            "item_key duplicado no payload do rascunho."
                        ) from exc
                    self._audit(
                        cur,
                        entity_type="checklist_template_version",
                        entity_id=updated["version_id"],
                        event_type="DRAFT_UPDATED",
                        actor=actor,
                        detail={
                            "template_id": template_id,
                            "version": version,
                            "item_count": len(items),
                            "revision": updated["revision"],
                        },
                    )
        return updated

    def submit_version_for_review(
        self,
        template_id: str,
        version: int,
        actor: str,
    ) -> dict[str, Any]:
        """DRAFT → REVIEW: submete a versão à revisão administrativa."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_template_version')}
                           SET status = 'REVIEW', updated_at = now()
                         WHERE version_id = (
                            SELECT v2.version_id
                              FROM {_q('checklist_template_version')} v2
                              JOIN {_q('checklist_template_series')} s2
                                ON s2.series_id = v2.series_id
                             WHERE v2.template_id = %s AND v2.version = %s
                             ORDER BY s2.series_no DESC LIMIT 1
                        )
                           AND status = 'DRAFT'
                        RETURNING version_id, status
                        """,
                        (template_id, version),
                    )
                    row = cur.fetchone()
                    if row is None:
                        current = self._version_status(
                            cur, template_id, version
                        )
                        if current is None:
                            raise VersionNotFound(
                                "Versão de checklist não encontrada."
                            )
                        raise VersionNotDraft(
                            "Somente versões DRAFT podem ir a revisão."
                        )
                    self._audit(
                        cur,
                        entity_type="checklist_template_version",
                        entity_id=row["version_id"],
                        event_type="VERSION_SUBMITTED_FOR_REVIEW",
                        actor=actor,
                        detail={
                            "template_id": template_id,
                            "version": version,
                        },
                    )
        return row

    def return_version_to_draft(
        self,
        template_id: str,
        version: int,
        *,
        reason: str,
        actor: str,
    ) -> dict[str, Any]:
        """REVIEW → DRAFT: devolução motivada para ajuste."""
        if not (reason and reason.strip()):
            raise ChecklistDomainError(
                "Devolução a DRAFT exige motivo (reason)."
            )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_template_version')}
                           SET status = 'DRAFT', updated_at = now()
                         WHERE version_id = (
                            SELECT v2.version_id
                              FROM {_q('checklist_template_version')} v2
                              JOIN {_q('checklist_template_series')} s2
                                ON s2.series_id = v2.series_id
                             WHERE v2.template_id = %s AND v2.version = %s
                             ORDER BY s2.series_no DESC LIMIT 1
                        )
                           AND status = 'REVIEW'
                        RETURNING version_id, status
                        """,
                        (template_id, version),
                    )
                    row = cur.fetchone()
                    if row is None:
                        current = self._version_status(
                            cur, template_id, version
                        )
                        if current is None:
                            raise VersionNotFound(
                                "Versão de checklist não encontrada."
                            )
                        raise VersionNotInReview(
                            "Somente versões em REVIEW podem voltar a "
                            "DRAFT."
                        )
                    self._audit(
                        cur,
                        entity_type="checklist_template_version",
                        entity_id=row["version_id"],
                        event_type="VERSION_RETURNED_TO_DRAFT",
                        actor=actor,
                        detail={
                            "template_id": template_id,
                            "version": version,
                            "reason": reason.strip(),
                        },
                    )
        return row

    def discard_draft_version(
        self,
        template_id: str,
        version: int,
        *,
        expected_revision: int,
        actor: str,
    ) -> dict[str, Any]:
        """Descarte governado de DRAFT (GATE-017): remove a versão e seus
        itens dentro de uma transação, com lock no template, OCC
        `expected_revision` e evento `VERSION_DISCARDED`.

        Somente `DRAFT` é descartável — PUBLISHED/INACTIVE são histórico
        imutável; REVIEW deve voltar a DRAFT pela rota existente.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT 1 FROM {_q('checklist_template')}
                         WHERE template_id = %s FOR UPDATE
                        """,
                        (template_id,),
                    )
                    if cur.fetchone() is None:
                        raise TemplateNotFound(
                            "Template de checklist não encontrado."
                        )
                    current = self._version_status(cur, template_id, version)
                    if current is None:
                        raise VersionNotFound(
                            "Versão de checklist não encontrada."
                        )
                    if current["status"] != "DRAFT":
                        raise VersionNotDraft(
                            "Somente versões DRAFT podem ser descartadas."
                        )
                    version_id = current["version_id"]
                    cur.execute(
                        f"""
                        SELECT 1 FROM {_q('monthly_competence')}
                         WHERE template_version_id = %s LIMIT 1
                        """,
                        (version_id,),
                    )
                    if cur.fetchone() is not None:
                        raise VersionReferenced(
                            "Versão vinculada a competência não pode ser "
                            "descartada."
                        )
                    cur.execute(
                        f"DELETE FROM {_q('checklist_template_item')}"
                        " WHERE version_id = %s",
                        (version_id,),
                    )
                    cur.execute(
                        f"""
                        DELETE FROM {_q('checklist_template_version')}
                         WHERE version_id = (
                            SELECT v2.version_id
                              FROM {_q('checklist_template_version')} v2
                              JOIN {_q('checklist_template_series')} s2
                                ON s2.series_id = v2.series_id
                             WHERE v2.template_id = %s AND v2.version = %s
                             ORDER BY s2.series_no DESC LIMIT 1
                        )
                           AND status = 'DRAFT' AND revision = %s
                        """,
                        (template_id, version, expected_revision),
                    )
                    if cur.rowcount == 0:
                        current = self._version_status(
                            cur, template_id, version
                        )
                        if current is not None and current["status"] != "DRAFT":
                            raise VersionNotDraft(
                                "Somente versões DRAFT podem ser "
                                "descartadas."
                            )
                        raise StaleRevision(
                            "Revisão desatualizada — recarregue a versão."
                        )
                    self._audit(
                        cur,
                        entity_type="checklist_template_version",
                        entity_id=version_id,
                        event_type="VERSION_DISCARDED",
                        actor=actor,
                        detail={
                            "template_id": template_id,
                            "version": version,
                            "revision": expected_revision,
                        },
                    )
        return {
            "version_id": str(version_id),
            "version": version,
            "status": "DISCARDED",
        }

    def publish_version(
        self,
        template_id: str,
        version: int,
        effective_from_period: str,
        actor: str,
        *,
        allow_empty: bool = False,
    ) -> dict[str, Any]:
        """REVIEW → PUBLISHED atômico (lifecycle DRAFT→REVIEW→PUBLISH);
        recusa edição retroativa/corrida.

        DR-2: versão com zero itens só é aceita com `allow_empty`
        explícito — o guard padrão continua recusando esvaziamento
        acidental.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT template_id FROM {_q('checklist_template')}
                         WHERE template_id = %s FOR UPDATE
                        """,
                        (template_id,),
                    )
                    if cur.fetchone() is None:
                        raise TemplateNotFound(
                            "Template de checklist não encontrado."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_template_version')} v
                           SET status = 'SUPERSEDED', updated_at = now()
                          FROM {_q('checklist_template_series')} s
                         WHERE s.series_id = v.series_id
                           AND s.status = 'ACTIVE'
                           AND v.template_id = %s
                           AND v.status = 'PUBLISHED'
                           AND v.version <> %s
                        """,
                        (template_id, version),
                    )
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_template_version')}
                           SET status = 'PUBLISHED',
                               effective_from_period = %s,
                               published_by = %s, published_at = now(),
                               updated_at = now()
                         WHERE version_id = (
                            SELECT v2.version_id
                              FROM {_q('checklist_template_version')} v2
                              JOIN {_q('checklist_template_series')} s2
                                ON s2.series_id = v2.series_id
                             WHERE v2.template_id = %s AND v2.version = %s
                             ORDER BY s2.series_no DESC LIMIT 1
                        )
                           AND status = 'REVIEW'
                        RETURNING version_id, status, effective_from_period,
                                  published_at
                        """,
                        (effective_from_period, actor, template_id, version),
                    )
                    row = cur.fetchone()
                    if row is None:
                        current = self._version_status(cur, template_id, version)
                        if current is None:
                            raise VersionNotFound(
                                "Versão de checklist não encontrada."
                            )
                        raise VersionNotInReview(
                            "Publicação exige versão em REVIEW "
                            "(DRAFT→REVIEW→PUBLISH)."
                        )
                    cur.execute(
                        f"SELECT count(*) FROM {_q('checklist_template_item')}"
                        " WHERE version_id = %s",
                        (row["version_id"],),
                    )
                    item_count = cur.fetchone()["count"]
                    if item_count == 0 and not allow_empty:
                        raise EmptyResultingChecklist(
                            "Versão sem itens exige allow_empty "
                            "explícito para publicar."
                        )
                    # D3 (GATE-016 CP1.1): a versão vence em
                    # [effective_from, próximo boundary). Competência
                    # aberta nessa janela ficaria com snapshot congelado
                    # divergente do catálogo — mesma regra do comando
                    # documental transacional.
                    cur.execute(
                        f"""
                        SELECT min(effective_from_period) AS next_boundary
                          FROM {_q('checklist_template_version')}
                         WHERE template_id = %s AND status = 'PUBLISHED'
                           AND effective_from_period > %s
                        """,
                        (template_id, effective_from_period),
                    )
                    window_end = (
                        cur.fetchone()["next_boundary"] or "9999-12"
                    )
                    cur.execute(
                        f"""
                        SELECT period FROM {_q('monthly_competence')}
                         WHERE period >= %s AND period < %s
                         ORDER BY period
                        """,
                        (effective_from_period, window_end),
                    )
                    covered = [
                        row["period"] for row in cur.fetchall()
                    ]
                    if covered:
                        raise WindowCoversOpenCompetence(
                            "A vigência intersecta competências já "
                            f"abertas ({', '.join(covered)}) — "
                            "snapshots congelados não podem "
                            "divergir do catálogo."
                        )
                    self._audit(
                        cur,
                        entity_type="checklist_template_version",
                        entity_id=row["version_id"],
                        event_type="VERSION_PUBLISHED",
                        actor=actor,
                        detail={
                            "template_id": template_id,
                            "version": version,
                            "effective_from_period": effective_from_period,
                            "item_count": item_count,
                        },
                    )
        return row

    def inactivate_version(
        self, template_id: str, version: int, actor: str
    ) -> dict[str, Any]:
        """PUBLISHED → INACTIVE prospectivo; nunca toca snapshots."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT template_id FROM {_q('checklist_template')}
                         WHERE template_id = %s FOR UPDATE
                        """,
                        (template_id,),
                    )
                    if cur.fetchone() is None:
                        raise TemplateNotFound(
                            "Template de checklist não encontrado."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_template_version')}
                           SET status = 'INACTIVE',
                               inactivated_by = %s,
                               inactivated_at = now(),
                               updated_at = now()
                         WHERE version_id = (
                            SELECT v2.version_id
                              FROM {_q('checklist_template_version')} v2
                              JOIN {_q('checklist_template_series')} s2
                                ON s2.series_id = v2.series_id
                             WHERE v2.template_id = %s AND v2.version = %s
                             ORDER BY s2.series_no DESC LIMIT 1
                        )
                           AND status = 'PUBLISHED'
                        RETURNING version_id, status, inactivated_at,
                                  effective_from_period
                        """,
                        (actor, template_id, version),
                    )
                    row = cur.fetchone()
                    if row is None:
                        current = self._version_status(cur, template_id, version)
                        if current is None:
                            raise VersionNotFound(
                                "Versão de checklist não encontrada."
                            )
                        raise VersionNotPublished(
                            "Somente versões PUBLISHED podem ser inativadas."
                        )
                    # D3 (GATE-016 CP1.1): inativar a versão muda o
                    # vencedor de [effective_from, próximo boundary) —
                    # competência aberta na janela divergiria do
                    # snapshot congelado.
                    cur.execute(
                        f"""
                        SELECT min(effective_from_period) AS next_boundary
                          FROM {_q('checklist_template_version')}
                         WHERE template_id = %s AND status = 'PUBLISHED'
                           AND effective_from_period > %s
                        """,
                        (template_id, row["effective_from_period"]),
                    )
                    window_end = (
                        cur.fetchone()["next_boundary"] or "9999-12"
                    )
                    cur.execute(
                        f"""
                        SELECT period FROM {_q('monthly_competence')}
                         WHERE period >= %s AND period < %s
                         ORDER BY period
                        """,
                        (row["effective_from_period"], window_end),
                    )
                    covered = [
                        entry["period"] for entry in cur.fetchall()
                    ]
                    if covered:
                        raise WindowCoversOpenCompetence(
                            "A inativação intersecta competências já "
                            f"abertas ({', '.join(covered)}) — "
                            "snapshots congelados não podem "
                            "divergir do catálogo."
                        )
                    self._audit(
                        cur,
                        entity_type="checklist_template_version",
                        entity_id=row["version_id"],
                        event_type="VERSION_INACTIVATED",
                        actor=actor,
                        detail={
                            "template_id": template_id,
                            "version": version,
                        },
                    )
        return row

    # -- competências / snapshot ----------------------------------------------

    def resolve_published_version(
        self, period: str
    ) -> dict[str, Any] | None:
        """Versão PUBLISHED vigente para a competência (effective_from <=)."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT v.version_id, v.template_id, v.version,
                       v.effective_from_period
                  FROM {_q('checklist_template_version')} v
                  JOIN {_q('checklist_template_series')} s
                    ON s.series_id = v.series_id
                 WHERE v.status IN ('PUBLISHED', 'SUPERSEDED')
                   AND s.status = 'ACTIVE'
                   AND v.effective_from_period <= %s
                 ORDER BY v.effective_from_period DESC, v.version DESC
                 LIMIT 1
                """,
                (period,),
            )
            return cur.fetchone()

    def open_competence(
        self, period: str, actor: str
    ) -> tuple[dict[str, Any], bool]:
        """Abertura idempotente + snapshot atômico dos itens vigentes.

        Sem versão PUBLISHED vigente a competência é criada com
        `template_version_id` NULL e snapshot vazio — abertura legítima
        sem exigências (Plano 113 §10).

        `ON CONFLICT DO NOTHING` torna retry/replay seguro; quando a
        competência já existe retorna a existente (created=False) sem
        duplicar snapshot nem evento.

        Serialização (DR-1, doc 114 §8.1): a resolução da versão vigente
        acontece DENTRO da transação, após lock `FOR UPDATE` ordenado de
        todas as linhas de template — publicação documental concorrente
        espera ou precede a abertura, nunca produz snapshot de uma
        timeline intermediária (Teste D do gate).
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT template_id FROM {_q('checklist_template')}
                         ORDER BY template_id FOR UPDATE
                        """
                    )
                    cur.execute(
                        f"""
                        SELECT v.version_id, v.template_id, v.version,
                               v.effective_from_period
                          FROM {_q('checklist_template_version')} v
                          JOIN {_q('checklist_template_series')} s
                            ON s.series_id = v.series_id
                         WHERE v.status IN ('PUBLISHED', 'SUPERSEDED')
                           AND s.status = 'ACTIVE'
                           AND v.effective_from_period <= %s
                         ORDER BY v.effective_from_period DESC,
                                  v.version DESC
                         LIMIT 1
                        """,
                        (period,),
                    )
                    published = cur.fetchone()
                    cur.execute(
                        f"""
                        INSERT INTO {_q('monthly_competence')}
                            (period, template_version_id, opened_by,
                             completion_record)
                        VALUES (%s, %s, %s, 'NEVER')
                        ON CONFLICT (period) DO NOTHING
                        RETURNING competence_id, period, template_version_id,
                                  status, opened_by, opened_at
                        """,
                        (
                            period,
                            published["version_id"] if published else None,
                            actor,
                        ),
                    )
                    row = cur.fetchone()
                    created = row is not None
                    if not created:
                        row = self._competence_row(cur, period)
                        if row is None:
                            raise PersistenceUnavailable(
                                "Falha ao recuperar competência existente."
                            )
                    elif published is not None:
                        cur.execute(
                            f"""
                            INSERT INTO {_q('competence_checklist_item')}
                                (competence_id, item_key, sort_order,
                                 source_template_item_id, source_version_id,
                                 sheet, name, purpose, origin_kind,
                                 recipient_area, applicability, branch_scope,
                                 totvs_report_ref, requirement_notes,
                                 validation_scope)
                            SELECT %s, item_key, sort_order, item_id,
                                   version_id, sheet, name, purpose,
                                   origin_kind, recipient_area, applicability,
                                   branch_scope, totvs_report_ref,
                                   requirement_notes, validation_scope
                              FROM {_q('checklist_template_item')}
                             WHERE version_id = %s
                               AND item_state = 'ACTIVE'
                             ORDER BY sort_order
                            """,
                            (row["competence_id"], published["version_id"]),
                        )
                    if created:
                        self._audit(
                            cur,
                            entity_type="monthly_competence",
                            entity_id=row["competence_id"],
                            competence_id=row["competence_id"],
                            event_type="COMPETENCE_OPENED",
                            actor=actor,
                            detail={
                                "period": period,
                                "template_version_id": (
                                    str(published["version_id"])
                                    if published
                                    else None
                                ),
                                "template_version": (
                                    published["version"]
                                    if published
                                    else None
                                ),
                                "opened_without_template": published
                                is None,
                            },
                        )
        return row, created

    def list_competences(self) -> list[dict[str, Any]]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT c.competence_id, c.period, c.template_version_id,
                       c.status, c.opened_at,
                       v.version AS template_version,
                       (SELECT count(*)
                          FROM {_q('competence_checklist_item')} i
                         WHERE i.competence_id = c.competence_id
                       ) AS item_count
                  FROM {_q('monthly_competence')} c
                  LEFT JOIN {_q('checklist_template_version')} v
                    ON v.version_id = c.template_version_id
                 ORDER BY c.period DESC
                """
            )
            return cur.fetchall()

    def get_competence(self, period: str) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            row = self._competence_row(cur, period, with_version=True)
        if row is None:
            raise CompetenceNotOpened(
                "Competência ainda não foi aberta."
            )
        return row

    def diagnose_competence_deletion(self, period: str) -> dict[str, Any]:
        from controllership_finance_app.infrastructure.persistence.competence_deletion import (
            diagnose_competence_deletion,
        )

        return diagnose_competence_deletion(period)

    def delete_competence(
        self,
        period: str,
        *,
        actor: str,
        expected_competence_id: str,
        reason: str,
        idempotency_key: str,
        channel: str = "portal",
        delete_dependents: bool = False,
        expected_dependents: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        from controllership_finance_app.infrastructure.persistence.competence_deletion import (
            delete_competence,
        )

        return delete_competence(
            period,
            actor=actor,
            expected_competence_id=expected_competence_id,
            reason=reason,
            idempotency_key=idempotency_key,
            channel=channel,
            delete_dependents=delete_dependents,
            expected_dependents=expected_dependents,
        )

    def diagnose_template_version_deletion(
        self, template_id: str, version: int
    ) -> dict[str, Any]:
        from controllership_finance_app.infrastructure.persistence.checklist_version_deletion import (
            diagnose_template_version_deletion,
        )

        return diagnose_template_version_deletion(template_id, version)

    def delete_template_version(
        self,
        template_id: str,
        version: int,
        *,
        actor: str,
        expected_version_id: str,
        expected_revision: int,
        expected_item_count: int,
        reason: str,
        idempotency_key: str,
        channel: str = "portal",
    ) -> dict[str, Any]:
        from controllership_finance_app.infrastructure.persistence.checklist_version_deletion import (
            delete_template_version,
        )

        return delete_template_version(
            template_id,
            version,
            actor=actor,
            expected_version_id=expected_version_id,
            expected_revision=expected_revision,
            expected_item_count=expected_item_count,
            reason=reason,
            idempotency_key=idempotency_key,
            channel=channel,
        )

    def _next_version_locked(
        self, cur, template_id: str, series_id: Any
    ) -> int:
        """Próximo número de versão na série sem reutilização
        silenciosa.

        Alta-marca = maior versão existente na série ou já citada na
        trilha append-only (versão excluída definitivamente nunca
        volta). Entradas legadas sem `series_id` pertencem à série 1.
        """
        cur.execute(
            f"""
            SELECT series_no FROM {_q('checklist_template_series')}
             WHERE series_id = %s
            """,
            (series_id,),
        )
        is_legacy_series = cur.fetchone()["series_no"] == 1
        cur.execute(
            f"""
            SELECT GREATEST(
                COALESCE((
                    SELECT max(version)
                      FROM {_q('checklist_template_version')}
                     WHERE series_id = %s
                ), 0),
                COALESCE((
                    SELECT max((detail->>'version')::int)
                      FROM {_q('closing_audit_event')}
                     WHERE entity_type = 'checklist_template_version'
                       AND detail->>'template_id' = %s
                       AND detail->>'version' ~ '^[0-9]+$'
                       AND (detail->>'series_id' = %s
                            OR (%s AND detail->>'series_id' IS NULL))
                ), 0)
            ) AS high_water
            """,
            (
                series_id, template_id, str(series_id),
                is_legacy_series,
            ),
        )
        return int(cur.fetchone()["high_water"]) + 1

    def list_competence_items(
        self,
        period: str,
        *,
        sheet: str | None = None,
        origin_kind: str | None = None,
        recipient_area: str | None = None,
        branch_scope: str | None = None,
        state: str | None = None,
    ) -> list[dict[str, Any]]:
        competence = self.get_competence(period)
        clauses = ["competence_id = %s"]
        params: list[Any] = [competence["competence_id"]]
        for column, value in (
            ("sheet", sheet),
            ("origin_kind", origin_kind),
            ("recipient_area", recipient_area),
            ("branch_scope", branch_scope),
            ("state", state),
        ):
            if value:
                clauses.append(f"{column} = %s")
                params.append(value)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT snapshot_item_id, item_key, sort_order, sheet, name,
                       origin_kind, recipient_area, applicability,
                       branch_scope, totvs_report_ref, state,
                       validation_scope, exceptional, revision, state_reason,
                       cancel_origin, cancelled_revision_id
                  FROM {_q('competence_checklist_item')}
                 WHERE {' AND '.join(clauses)}
                 ORDER BY sort_order
                """,
                params,
            )
            return cur.fetchall()

    def get_competence_item(
        self, period: str, item_key: str
    ) -> dict[str, Any]:
        competence = self.get_competence(period)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT snapshot_item_id, item_key, sort_order,
                       source_template_item_id, source_version_id, sheet,
                       name, purpose, origin_kind, recipient_area,
                       applicability, branch_scope, totvs_report_ref,
                       requirement_notes, state, validation_scope,
                       exceptional, revision, state_reason,
                       cancel_origin, cancelled_revision_id
                  FROM {_q('competence_checklist_item')}
                 WHERE competence_id = %s AND item_key = %s
                """,
                (competence["competence_id"], item_key),
            )
            row = cur.fetchone()
        if row is None:
            raise ItemNotFound("Item do checklist não encontrado.")
        return row

    # -- internals ------------------------------------------------------------

    def _version_status(
        self, cur, template_id: str, version: int
    ) -> dict[str, Any] | None:
        cur.execute(
            f"""
            SELECT v.version_id, v.status
              FROM {_q('checklist_template_version')} v
              JOIN {_q('checklist_template_series')} s
                ON s.series_id = v.series_id
             WHERE v.template_id = %s AND v.version = %s
             ORDER BY s.series_no DESC LIMIT 1
            """,
            (template_id, version),
        )
        return cur.fetchone()

    def _competence_row(
        self, cur, period: str, with_version: bool = False
    ) -> dict[str, Any] | None:
        extra = ", v.version AS template_version" if with_version else ""
        join = (
            f" LEFT JOIN {_q('checklist_template_version')} v"
            " ON v.version_id = c.template_version_id"
            if with_version
            else ""
        )
        cur.execute(
            f"""
            SELECT c.competence_id, c.period, c.template_version_id,
                   c.status, c.opened_by, c.opened_at{extra}
              FROM {_q('monthly_competence')} c{join}
             WHERE c.period = %s
            """,
            (period,),
        )
        return cur.fetchone()

    def _audit(
        self,
        cur,
        *,
        entity_type: str,
        entity_id: Any,
        event_type: str,
        actor: str,
        detail: dict[str, Any],
        competence_id: Any = None,
    ) -> Any:
        cur.execute(
            f"""
            INSERT INTO {_q('closing_audit_event')}
                (entity_type, entity_id, competence_id, event_type,
                 actor_subject, detail)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            RETURNING event_id
            """,
            (
                entity_type,
                entity_id,
                competence_id,
                event_type,
                actor,
                json.dumps(detail, default=str),
            ),
        )
        return cur.fetchone()["event_id"]

    # -- DR-1: configuração documental transacional (doc 114 §8) ----------

    def _versions_with_items_locked(
        self, cur, template_id: str
    ) -> list[dict[str, Any]]:
        """Timeline completa do template com itens — chamada SOMENTE
        dentro da transação que já detém o lock do template."""
        cur.execute(
            f"""
            SELECT version_id, version, status, effective_from_period
              FROM {_q('checklist_template_version')}
             WHERE template_id = %s
             ORDER BY version
            """,
            (template_id,),
        )
        versions = cur.fetchall()
        for version in versions:
            cur.execute(
                f"""
                SELECT item_key, sort_order, sheet, name, purpose,
                       origin_kind, recipient_area, applicability,
                       branch_scope, totvs_report_ref, requirement_notes,
                       validation_scope
                  FROM {_q('checklist_template_item')}
                 WHERE version_id = %s
                 ORDER BY sort_order
                """,
                (version["version_id"],),
            )
            version["items"] = cur.fetchall()
        return versions

    @staticmethod
    def _requirement_request_hash(
        item_key: str,
        item: dict[str, Any] | None,
        effective_from: str,
        effective_until: str | None,
        allow_empty: bool,
    ) -> str:
        """SHA-256 do payload normalizado — `base_version` fica fora
        (é OCC, não identidade da operação; precedente V004)."""
        canonical = json.dumps(
            {
                "item_key": item_key,
                "item": item,
                "effective_from": effective_from,
                "effective_until": effective_until,
                "allow_empty": allow_empty,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def apply_document_requirement(
        self,
        template_id: str,
        item_key: str,
        item: dict[str, Any] | None,
        effective_from: str,
        effective_until: str | None,
        base_version: int,
        allow_empty: bool,
        idempotency_key: str,
        actor: str,
    ) -> dict[str, Any]:
        """Configura a exigência documental em UMA transação (DR-1).

        Ordem canônica (doc 114 §8.3): lock FOR UPDATE do template →
        replay idempotente (antes do OCC, retry legítimo nunca vira
        stale) → base_version → conflito de rascunho → regras de janela
        → competências abertas → plano de boundaries → versões com
        trilha DRAFT→REVIEW→PUBLISHED → evento resumo → registro da
        operação → commit único. Qualquer falha = rollback integral.
        """
        request_hash = self._requirement_request_hash(
            item_key, item, effective_from, effective_until, allow_empty
        )
        with self._conn() as conn:
            try:
                with conn.transaction():
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute("SET LOCAL lock_timeout = '5s'")
                        cur.execute(
                            f"""
                            SELECT template_id
                              FROM {_q('checklist_template')}
                             WHERE template_id = %s FOR UPDATE
                            """,
                            (template_id,),
                        )
                        if cur.fetchone() is None:
                            raise TemplateNotFound(
                                "Template de checklist não encontrado."
                            )

                        cur.execute(
                            f"""
                            SELECT request_hash, result
                              FROM {_q('document_requirement_operation')}
                             WHERE template_id = %s
                               AND idempotency_key = %s
                            """,
                            (template_id, idempotency_key),
                        )
                        replay = cur.fetchone()
                        if replay is not None:
                            if replay["request_hash"] != request_hash:
                                raise IdempotencyConflict(
                                    "Idempotency-Key reutilizada com "
                                    "payload diferente."
                                )
                            result = dict(replay["result"])
                            result["replayed"] = True
                            return result

                        cur.execute(
                            f"""
                            SELECT max(version) AS max_version
                              FROM {_q('checklist_template_version')}
                             WHERE template_id = %s
                            """,
                            (template_id,),
                        )
                        if (cur.fetchone()["max_version"] or 0) != (
                            base_version
                        ):
                            raise StaleRevision(
                                "A configuração do checklist mudou — "
                                "recarregue antes de salvar."
                            )

                        cur.execute(
                            f"""
                            SELECT version FROM {_q('checklist_template_version')}
                             WHERE template_id = %s
                               AND status IN ('DRAFT', 'REVIEW')
                            """,
                            (template_id,),
                        )
                        if cur.fetchone() is not None:
                            raise CatalogDraftConflict(
                                "Existe uma versão em rascunho ou "
                                "revisão — conclua-a ou descarte-a na "
                                "Administração do checklist."
                            )

                        cur.execute(
                            "SELECT to_char(now(), 'YYYY-MM') AS current"
                        )
                        if effective_from < cur.fetchone()["current"]:
                            raise RetroactiveEffectivePeriod(
                                "A vigência inicial não pode ser uma "
                                "competência passada."
                            )
                        if (
                            effective_until is not None
                            and effective_until < effective_from
                        ):
                            raise InvalidRequirementWindow(
                                "A competência final não pode ser "
                                "anterior à inicial."
                            )

                        # D3: a janela de efeito cobre [from, until] e a
                        # remoção publicada em until+1; sem item (fim de
                        # exigência) cobre [from, ∞).
                        if item is None or effective_until is None:
                            window_end = "9999-12"
                        else:
                            window_end = planner.next_period(
                                effective_until
                            )
                        cur.execute(
                            f"""
                            SELECT period FROM {_q('monthly_competence')}
                             WHERE period >= %s AND period <= %s
                             ORDER BY period
                            """,
                            (effective_from, window_end),
                        )
                        covered = [
                            row["period"] for row in cur.fetchall()
                        ]
                        if covered:
                            raise WindowCoversOpenCompetence(
                                "A janela intersecta competências já "
                                f"abertas ({', '.join(covered)}) — "
                                "snapshots congelados não podem "
                                "divergir do catálogo."
                            )

                        versions = self._versions_with_items_locked(
                            cur, template_id
                        )
                        if item is None:
                            steps = planner.plan_document_removal(
                                versions, item_key, effective_from
                            )
                        else:
                            steps = planner.plan_document_upsert(
                                versions,
                                item,
                                effective_from,
                                effective_until,
                            )
                        if not allow_empty and any(
                            not step["items"] for step in steps
                        ):
                            raise EmptyResultingChecklist(
                                "A operação deixaria o checklist sem "
                                "nenhuma exigência — confirme a "
                                "intenção de publicar checklist vazio."
                            )

                        series_id = self._active_series_id_locked(
                            cur, template_id, actor
                        )
                        next_version = self._next_version_locked(
                            cur, template_id, series_id
                        )
                        published_versions: list[dict[str, Any]] = []
                        audit_event_ids: list[str] = []
                        try:
                            for step in steps:
                                version_row = self._insert_governed_version(
                                    cur,
                                    template_id,
                                    next_version,
                                    step,
                                    actor,
                                    audit_event_ids,
                                )
                                published_versions.append(version_row)
                                self._record_unitary_revision(
                                    cur,
                                    version_row=version_row,
                                    item_key=item_key,
                                    item=item,
                                    idempotency_key=(
                                        f"{idempotency_key}"
                                        f":v{version_row['version']}"
                                    ),
                                    actor=actor,
                                )
                                next_version += 1
                        except psycopg.errors.UniqueViolation as exc:
                            raise CatalogDraftConflict(
                                "Uma versão em rascunho ou revisão foi "
                                "aberta em concorrência — repita a "
                                "operação."
                            ) from exc

                        operation_id = self._audit(
                            cur,
                            entity_type="checklist_template",
                            entity_id=template_id,
                            event_type="DOCUMENT_CONFIG_APPLIED",
                            actor=actor,
                            detail={
                                "template_id": template_id,
                                "item_key": item_key,
                                "operation": (
                                    "upsert" if item is not None
                                    else "removal"
                                ),
                                "effective_from": effective_from,
                                "effective_until": effective_until,
                                "allow_empty": allow_empty,
                                "idempotency_key": idempotency_key,
                                "published_versions": [
                                    {
                                        "version": v["version"],
                                        "effective_from_period": v[
                                            "effective_from_period"
                                        ],
                                        "item_count": v["item_count"],
                                    }
                                    for v in published_versions
                                ],
                            },
                        )
                        audit_event_ids.append(str(operation_id))

                        result = {
                            "item_key": item_key,
                            "published_versions": published_versions,
                            "no_changes": len(published_versions) == 0,
                            "replayed": False,
                            "audit_event_ids": audit_event_ids,
                        }
                        cur.execute(
                            f"""
                            INSERT INTO {_q('document_requirement_operation')}
                                (template_id, item_key, idempotency_key,
                                 request_hash, actor_subject, result)
                            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                            """,
                            (
                                template_id,
                                item_key,
                                idempotency_key,
                                request_hash,
                                actor,
                                json.dumps(result),
                            ),
                        )
                        return result
            except psycopg.errors.LockNotAvailable as exc:
                raise OperationBusy(
                    "Outra operação administrativa está em curso neste "
                    "checklist — tente novamente em instantes."
                ) from exc

    def _record_unitary_revision(
        self, cur, *, version_row: dict, item_key: str,
        item: dict[str, Any] | None, idempotency_key: str,
        actor: str,
    ) -> None:
        """Revisão interna R1 documentando a alteração unitária de
        exigência que gerou a versão (contrato Gate 2A §1 — a
        operação unitária registra `checklist_version_revision` com
        exatamente 1 change no histórico append-only)."""
        cur.execute(
            f"""
            INSERT INTO {_q('checklist_version_revision')}
                (version_id, revision_no, fingerprint,
                 reason, idempotency_key, reverts_revision_id,
                 created_by)
            VALUES (%s, 1, %s, %s, %s, NULL, %s)
            RETURNING revision_id
            """,
            (
                version_row["version_id"],
                self._catalog_fingerprint(
                    cur, version_row["version_id"]
                ),
                "Configuração unitária de exigência "
                f"{item_key} ({'upsert' if item else 'removal'})",
                idempotency_key[:80],
                actor,
            ),
        )
        revision_id = cur.fetchone()["revision_id"]
        cur.execute(
            f"""
            INSERT INTO {_q('checklist_version_revision_change')}
                (revision_id, seq, item_key, op,
                 before_state, after_state)
            VALUES (%s, 1, %s, %s, NULL, %s::jsonb)
            """,
            (
                revision_id,
                item_key,
                "UPDATE" if item is not None else "RETIRE",
                json.dumps(item, default=str)
                if item is not None else "null",
            ),
        )

    def _insert_governed_version(
        self,
        cur,
        template_id: str,
        version: int,
        step: dict[str, Any],
        actor: str,
        audit_event_ids: list[str],
    ) -> dict[str, Any]:
        """Insere uma versão já com a trilha governada auditada
        (D4): DRAFT_CREATED → VERSION_SUBMITTED_FOR_REVIEW →
        VERSION_PUBLISHED — equivalente ao ciclo manual, dentro da
        mesma transação."""
        series_id = self._active_series_id_locked(
            cur, template_id, actor
        )
        cur.execute(
            f"""
            INSERT INTO {_q('checklist_template_version')}
                (template_id, series_id, version, status, created_by)
            VALUES (%s, %s, %s, 'DRAFT', %s)
            RETURNING version_id
            """,
            (template_id, series_id, version, actor),
        )
        version_id = cur.fetchone()["version_id"]
        audit_event_ids.append(
            str(
                self._audit(
                    cur,
                    entity_type="checklist_template_version",
                    entity_id=version_id,
                    event_type="DRAFT_CREATED",
                    actor=actor,
                    detail={
                        "template_id": template_id,
                        "version": version,
                        "source": "document_requirement",
                    },
                )
            )
        )
        for position, item in enumerate(step["items"], start=1):
            cur.execute(
                f"""
                INSERT INTO {_q('checklist_template_item')}
                    (version_id, item_key, sort_order, sheet, name,
                     purpose, origin_kind, recipient_area, applicability,
                     branch_scope, totvs_report_ref, requirement_notes,
                     validation_scope)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    version_id,
                    item["item_key"],
                    item.get("sort_order") or position,
                    item["sheet"],
                    item["name"],
                    item.get("purpose"),
                    item["origin_kind"],
                    item.get("recipient_area"),
                    item.get("applicability") or "REQUIRED",
                    item.get("branch_scope") or "BOTH",
                    item.get("totvs_report_ref"),
                    item.get("requirement_notes"),
                    item.get("validation_scope") or "PER_ATTACHMENT",
                ),
            )
        audit_event_ids.append(
            str(
                self._audit(
                    cur,
                    entity_type="checklist_template_version",
                    entity_id=version_id,
                    event_type="DRAFT_UPDATED",
                    actor=actor,
                    detail={
                        "template_id": template_id,
                        "version": version,
                        "item_count": len(step["items"]),
                    },
                )
            )
        )
        cur.execute(
            f"""
            UPDATE {_q('checklist_template_version')}
               SET status = 'REVIEW', updated_at = now()
             WHERE version_id = %s
            """,
            (version_id,),
        )
        audit_event_ids.append(
            str(
                self._audit(
                    cur,
                    entity_type="checklist_template_version",
                    entity_id=version_id,
                    event_type="VERSION_SUBMITTED_FOR_REVIEW",
                    actor=actor,
                    detail={
                        "template_id": template_id,
                        "version": version,
                    },
                )
            )
        )
        cur.execute(
            f"""
            UPDATE {_q('checklist_template_version')} v
               SET status = 'SUPERSEDED', updated_at = now()
              FROM {_q('checklist_template_series')} s
             WHERE s.series_id = v.series_id
               AND s.status = 'ACTIVE'
               AND v.template_id = %s
               AND v.status = 'PUBLISHED'
               AND v.version_id <> %s
            """,
            (template_id, version_id),
        )
        cur.execute(
            f"""
            UPDATE {_q('checklist_template_version')}
               SET status = 'PUBLISHED',
                   effective_from_period = %s,
                   published_by = %s, published_at = now(),
                   updated_at = now()
             WHERE version_id = %s
            """,
            (step["effective_from"], actor, version_id),
        )
        audit_event_ids.append(
            str(
                self._audit(
                    cur,
                    entity_type="checklist_template_version",
                    entity_id=version_id,
                    event_type="VERSION_PUBLISHED",
                    actor=actor,
                    detail={
                        "template_id": template_id,
                        "version": version,
                        "effective_from_period": step["effective_from"],
                        "item_count": len(step["items"]),
                        "source": "document_requirement",
                    },
                )
            )
        )
        return {
            "version_id": str(version_id),
            "version": version,
            "effective_from_period": step["effective_from"],
            "item_count": len(step["items"]),
        }

    # ================= Checklist vivo (CF-CHECKLIST-LIVE-004) ==========
    # Séries, revisões internas da versão publicada, sincronização
    # automática por outbox durável e proteção histórica de conclusão.

    _REVISION_OPS = ("ADD", "UPDATE", "RETIRE", "REORDER", "REACTIVATE")
    _SYSTEM_ACTOR = "00000000-0000-4000-8000-000000000002"

    def _active_series_id_locked(
        self, cur, template_id: str, actor: str
    ) -> Any:
        """Série vigente para novas versões (V031): ACTIVE ou, em
        template legado sem série, série 1 criada na transação."""
        cur.execute(
            f"""
            SELECT series_id FROM {_q('checklist_template_series')}
             WHERE template_id = %s AND status = 'ACTIVE'
            """,
            (template_id,),
        )
        row = cur.fetchone()
        if row is not None:
            return row["series_id"]
        cur.execute(
            f"""
            SELECT series_id FROM {_q('checklist_template_series')}
             WHERE template_id = %s
             ORDER BY series_no DESC LIMIT 1
            """,
            (template_id,),
        )
        row = cur.fetchone()
        if row is not None:
            return row["series_id"]
        cur.execute(
            f"""
            INSERT INTO {_q('checklist_template_series')}
                (template_id, series_no, started_by)
            VALUES (%s, 1, %s)
            ON CONFLICT (template_id, series_no) DO NOTHING
            """,
            (template_id, actor),
        )
        cur.execute(
            f"""
            SELECT series_id FROM {_q('checklist_template_series')}
             WHERE template_id = %s AND series_no = 1
            """,
            (template_id,),
        )
        return cur.fetchone()["series_id"]

    _ITEM_COLS = (
        "item_key", "sort_order", "sheet", "name", "purpose",
        "origin_kind", "recipient_area", "applicability",
        "branch_scope", "totvs_report_ref", "requirement_notes",
        "validation_scope",
    )
    _PENDENCY_OPEN_STATES = ("OPEN", "IN_ANALYSIS", "WAITING_EXTERNAL")

    # -- séries ---------------------------------------------------------

    def list_series(self, template_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT 1 FROM {_q('checklist_template')}
                 WHERE template_id = %s
                """,
                (template_id,),
            )
            if cur.fetchone() is None:
                raise TemplateNotFound(
                    "Template de checklist não encontrado."
                )
            cur.execute(
                f"""
                SELECT s.series_id, s.template_id, s.series_no, s.status,
                       s.start_reason, s.started_by, s.started_at,
                       s.closed_by, s.closed_at,
                       (SELECT count(*) FROM {_q('checklist_template_version')} v
                         WHERE v.series_id = s.series_id) AS versions
                  FROM {_q('checklist_template_series')} s
                 WHERE s.template_id = %s
                 ORDER BY s.series_no
                """,
                (template_id,),
            )
            return cur.fetchall()

    def get_active_series(self, template_id: str) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT series_id, template_id, series_no, status,
                       start_reason, started_by, started_at
                  FROM {_q('checklist_template_series')}
                 WHERE template_id = %s AND status = 'ACTIVE'
                """,
                (template_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise SeriesNotFound(
                    "Nenhuma série ativa para o template."
                )
            return row

    def start_checklist_sequence(
        self,
        template_id: str,
        actor: str,
        reason: str,
        confirmation: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Inicia nova sequência (D4): fecha série ativa, cria série n+1
        e V1 DRAFT vazia — inicialização de itens é fluxo separado
        (`initialize_checklist_catalog`). Append-only: a série anterior
        nunca é apagada."""
        if confirmation != "START_NEW_SEQUENCE":
            raise SeriesConfirmationRequired(
                "Operação excepcional exige confirmação "
                "'START_NEW_SEQUENCE'."
            )
        if not (reason or "").strip():
            raise ChecklistDomainError("Motivo obrigatório.")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("SET LOCAL lock_timeout = '5s'")
                    cur.execute(
                        f"""
                        SELECT template_id FROM {_q('checklist_template')}
                         WHERE template_id = %s FOR UPDATE
                        """,
                        (template_id,),
                    )
                    if cur.fetchone() is None:
                        raise TemplateNotFound(
                            "Template de checklist não encontrado."
                        )
                    cur.execute(
                        f"""
                        SELECT series_id, series_no
                          FROM {_q('checklist_template_series')}
                         WHERE template_id = %s
                           AND idempotency_key = %s
                        """,
                        (template_id, idempotency_key),
                    )
                    replay = cur.fetchone()
                    if replay is not None:
                        return {
                            "series_id": str(replay["series_id"]),
                            "series_no": replay["series_no"],
                            "replayed": True,
                        }
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_template_series')}
                           SET status = 'CLOSED', closed_by = %s,
                               closed_at = now()
                         WHERE template_id = %s AND status = 'ACTIVE'
                        RETURNING series_id, series_no
                        """,
                        (actor, template_id),
                    )
                    previous = cur.fetchone()
                    next_no = (previous["series_no"] + 1) if previous else 1
                    cur.execute(
                        f"""
                        INSERT INTO {_q('checklist_template_series')}
                            (template_id, series_no, start_reason,
                             started_by, idempotency_key)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING series_id, series_no, status,
                                  started_at
                        """,
                        (template_id, next_no, reason, actor,
                         idempotency_key),
                    )
                    series = cur.fetchone()
                    cur.execute(
                        f"""
                        INSERT INTO {_q('checklist_template_version')}
                            (template_id, series_id, version, status,
                             created_by)
                        VALUES (%s, %s, 1, 'DRAFT', %s)
                        RETURNING version_id
                        """,
                        (template_id, series["series_id"], actor),
                    )
                    version_id = cur.fetchone()["version_id"]
                    self._audit(
                        cur,
                        entity_type="checklist_template_series",
                        entity_id=series["series_id"],
                        event_type="SERIES_STARTED",
                        actor=actor,
                        detail={
                            "template_id": template_id,
                            "series_no": next_no,
                            "previous_series_id": (
                                str(previous["series_id"])
                                if previous else None
                            ),
                            "reason": reason,
                            "version_id": str(version_id),
                        },
                    )
        return {
            "series_id": str(series["series_id"]),
            "series_no": next_no,
            "status": series["status"],
            "version_id": str(version_id),
            "replayed": False,
        }

    # -- inicialização excepcional (RQ-01) -------------------------------

    def initialize_checklist_catalog(
        self,
        version_id: str,
        actor: str,
        reason: str,
        items: list[dict[str, Any]],
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Carga inicial atômica da V1 DRAFT de série nova.

        Somente versão DRAFT; catálogo vazio ou replay idêntico.
        Reutiliza `document_requirement_operation` para idempotência
        (mesmo mecanismo canônico V017)."""
        if not (reason or "").strip():
            raise ChecklistDomainError("Motivo obrigatório.")
        request_hash = hashlib.sha256(
            json.dumps(items, sort_keys=True, default=str).encode()
        ).hexdigest()
        keys = [str(i.get("item_key") or "") for i in items]
        if len(set(keys)) != len(keys) or any(not k for k in keys):
            raise DuplicateItemKey(
                "item_key ausente ou duplicada no manifesto."
            )
        orders = [int(i.get("sort_order") or 0) for i in items]
        if len(set(orders)) != len(orders):
            raise ChecklistDomainError("sort_order duplicado no manifesto.")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("SET LOCAL lock_timeout = '5s'")
                    cur.execute(
                        f"""
                        SELECT v.version_id, v.template_id, v.status,
                               v.series_id, v.version
                          FROM {_q('checklist_template_version')} v
                         WHERE v.version_id = %s FOR UPDATE
                        """,
                        (version_id,),
                    )
                    version = cur.fetchone()
                    if version is None:
                        raise VersionNotFound("Versão não encontrada.")
                    cur.execute(
                        f"""
                        SELECT template_id FROM {_q('checklist_template')}
                         WHERE template_id = %s FOR UPDATE
                        """,
                        (version["template_id"],),
                    )
                    cur.execute(
                        f"""
                        SELECT request_hash, result
                          FROM {_q('document_requirement_operation')}
                         WHERE template_id = %s
                           AND idempotency_key = %s
                        """,
                        (version["template_id"], idempotency_key),
                    )
                    replay = cur.fetchone()
                    if replay is not None:
                        if replay["request_hash"] != request_hash:
                            raise IdempotencyConflict(
                                "Idempotency-Key reutilizada com "
                                "payload diferente."
                            )
                        result = dict(replay["result"])
                        result["replayed"] = True
                        return result
                    if version["status"] != "DRAFT":
                        raise VersionNotDraft(
                            "Carga inicial somente em versão DRAFT."
                        )
                    cur.execute(
                        f"""
                        SELECT count(*) AS n
                          FROM {_q('checklist_template_item')}
                         WHERE version_id = %s
                        """,
                        (version_id,),
                    )
                    if cur.fetchone()["n"]:
                        raise CatalogNotEmpty(
                            "Versão já possui itens — edição posterior "
                            "é por revisão, não por carga inicial."
                        )
                    for item in items:
                        cur.execute(
                            f"""
                            INSERT INTO {_q('checklist_template_item')}
                                (version_id, item_key, sort_order, sheet,
                                 name, purpose, origin_kind,
                                 recipient_area, applicability,
                                 branch_scope, totvs_report_ref,
                                 requirement_notes, validation_scope)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (
                                version_id, item["item_key"],
                                item["sort_order"], item["sheet"],
                                item["name"], item.get("purpose"),
                                item.get("origin_kind", "EXTERNAL"),
                                item.get("recipient_area"),
                                item.get("applicability", "REQUIRED"),
                                item.get("branch_scope", "BOTH"),
                                item.get("totvs_report_ref"),
                                item.get("requirement_notes"),
                                item.get("validation_scope",
                                         "PER_ATTACHMENT"),
                            ),
                        )
                    fingerprint = request_hash
                    result = {
                        "version_id": str(version_id),
                        "items_created": len(items),
                        "fingerprint": fingerprint,
                        "replayed": False,
                    }
                    cur.execute(
                        f"""
                        INSERT INTO {_q('document_requirement_operation')}
                            (template_id, item_key, idempotency_key,
                             request_hash, actor_subject, result)
                        VALUES (%s, '*', %s, %s, %s, %s::jsonb)
                        """,
                        (version["template_id"], idempotency_key,
                         request_hash, actor, json.dumps(result)),
                    )
                    self._audit(
                        cur,
                        entity_type="checklist_template_version",
                        entity_id=version_id,
                        event_type="CHECKLIST_CATALOG_INITIALIZED",
                        actor=actor,
                        detail={
                            "template_id": str(version["template_id"]),
                            "series_id": str(version["series_id"]),
                            "version": version["version"],
                            "items": len(items),
                            "fingerprint": fingerprint,
                            "reason": reason,
                        },
                    )
        return result

    # -- revisões (RQ-02/08/09) ------------------------------------------

    def _catalog_fingerprint(self, cur, version_id: str) -> str:
        cur.execute(
            f"""
            SELECT item_key, sort_order, sheet, name, applicability,
                   branch_scope, item_state
              FROM {_q('checklist_template_item')}
             WHERE version_id = %s
             ORDER BY item_key
            """,
            (version_id,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        return hashlib.sha256(
            json.dumps(rows, sort_keys=True, default=str).encode()
        ).hexdigest()

    def _item_row(self, cur, version_id: str, item_key: str):
        cur.execute(
            f"""
            SELECT * FROM {_q('checklist_template_item')}
             WHERE version_id = %s AND item_key = %s
            """,
            (version_id, item_key),
        )
        return cur.fetchone()

    def _apply_change(
        self, cur, *, version: dict, change: dict, seq: int,
        revision_id: str, actor: str,
    ) -> dict:
        """Aplica uma change do lote; devolve before/after para trilha."""
        op = change["op"]
        item_key = change["item_key"]
        row = self._item_row(cur, version["version_id"], item_key)
        before = dict(row) if row else None
        payload = change.get("payload") or {}

        if op == "ADD":
            if row is not None:
                raise DuplicateItemKey(f"item_key '{item_key}' já existe.")
            cur.execute(
                f"""
                INSERT INTO {_q('checklist_template_item')}
                    (version_id, item_key, sort_order, sheet, name,
                     purpose, origin_kind, recipient_area, applicability,
                     branch_scope, totvs_report_ref, requirement_notes,
                     validation_scope)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    version["version_id"], item_key,
                    payload.get("sort_order", 999),
                    payload["sheet"], payload["name"],
                    payload.get("purpose"),
                    payload.get("origin_kind", "EXTERNAL"),
                    payload.get("recipient_area"),
                    payload.get("applicability", "REQUIRED"),
                    payload.get("branch_scope", "BOTH"),
                    payload.get("totvs_report_ref"),
                    payload.get("requirement_notes"),
                    payload.get("validation_scope", "PER_ATTACHMENT"),
                ),
            )
            after = payload
        elif op == "UPDATE":
            if row is None:
                raise ItemNotFound(f"item '{item_key}' não existe.")
            if row["item_state"] != "ACTIVE":
                raise ItemRetired(f"item '{item_key}' está retirado.")
            fields, values = [], []
            for col in self._ITEM_COLS:
                if col in payload and col != "item_key":
                    fields.append(f"{col} = %s")
                    values.append(payload[col])
            if fields:
                values.append(row["item_id"])
                cur.execute(
                    f"""
                    UPDATE {_q('checklist_template_item')}
                       SET {', '.join(fields)}
                     WHERE item_id = %s
                    """,
                    values,
                )
            after = payload
        elif op == "RETIRE":
            if row is None:
                raise ItemNotFound(f"item '{item_key}' não existe.")
            if row["item_state"] != "ACTIVE":
                raise ItemRetired(f"item '{item_key}' já está retirado.")
            cur.execute(
                f"""
                UPDATE {_q('checklist_template_item')}
                   SET item_state = 'RETIRED',
                       retired_revision_id = %s,
                       retired_by = %s, retired_at = now()
                 WHERE item_id = %s
                """,
                (revision_id, actor, row["item_id"]),
            )
            after = {"item_state": "RETIRED",
                     "reason": payload.get("reason")}
        elif op == "REACTIVATE":
            if row is None:
                raise ItemNotFound(f"item '{item_key}' não existe.")
            if row["item_state"] != "RETIRED":
                raise ChecklistDomainError(
                    f"item '{item_key}' não está retirado."
                )
            cur.execute(
                f"""
                UPDATE {_q('checklist_template_item')}
                   SET item_state = 'ACTIVE', retired_revision_id = NULL,
                       retired_by = NULL, retired_at = NULL
                 WHERE item_id = %s
                """,
                (row["item_id"],),
            )
            after = {"item_state": "ACTIVE"}
        elif op == "REORDER":
            order = payload.get("order") or []
            for pos, key in enumerate(order, start=1):
                cur.execute(
                    f"""
                    UPDATE {_q('checklist_template_item')}
                       SET sort_order = %s
                     WHERE version_id = %s AND item_key = %s
                    """,
                    (pos, version["version_id"], key),
                )
            after = {"order": order}
        else:
            raise ChecklistDomainError(f"op desconhecida '{op}'.")
        return {
            "seq": seq, "item_key": item_key, "op": op,
            "before_state": before, "after_state": after,
        }

    def apply_revision(
        self,
        version_id: str,
        actor: str,
        reason: str,
        expected_revision: int,
        changes: list[dict[str, Any]],
        idempotency_key: str,
        reverts_revision_id: str | None = None,
    ) -> dict[str, Any]:
        """Aplica lote atômico de changes na versão PUBLISHED + emite
        evento de sincronização na mesma transação."""
        if not (reason or "").strip():
            raise ChecklistDomainError("Motivo obrigatório.")
        for ch in changes:
            if ch.get("op") not in self._REVISION_OPS:
                raise ChecklistDomainError(
                    f"op inválida '{ch.get('op')}'."
                )
            if not ch.get("item_key"):
                raise ChecklistDomainError("item_key obrigatório.")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute("SET LOCAL lock_timeout = '5s'")
                    cur.execute(
                        f"""
                        SELECT revision_id, revision_no
                          FROM {_q('checklist_version_revision')}
                         WHERE idempotency_key = %s
                        """,
                        (idempotency_key,),
                    )
                    replay = cur.fetchone()
                    if replay is not None:
                        return {
                            "revision_id": str(replay["revision_id"]),
                            "revision_no": replay["revision_no"],
                            "replayed": True,
                        }
                    cur.execute(
                        f"""
                        SELECT v.version_id, v.template_id, v.status,
                               v.revision, v.version, v.series_id
                          FROM {_q('checklist_template_version')} v
                         WHERE v.version_id = %s FOR UPDATE
                        """,
                        (version_id,),
                    )
                    version = cur.fetchone()
                    if version is None:
                        raise VersionNotFound("Versão não encontrada.")
                    cur.execute(
                        f"""
                        SELECT template_id FROM {_q('checklist_template')}
                         WHERE template_id = %s FOR UPDATE
                        """,
                        (version["template_id"],),
                    )
                    if version["status"] != "PUBLISHED":
                        raise VersionNotPublished(
                            "Revisões internas exigem versão PUBLISHED."
                        )
                    if int(version["revision"]) != int(expected_revision):
                        raise StaleRevision(
                            f"Revisão esperada {expected_revision}, "
                            f"atual {version['revision']}."
                        )
                    cur.execute(
                        f"""
                        SELECT COALESCE(max(revision_no),0)+1 AS next_no
                          FROM {_q('checklist_version_revision')}
                         WHERE version_id = %s
                        """,
                        (version_id,),
                    )
                    revision_no = cur.fetchone()["next_no"]
                    cur.execute(
                        f"""
                        INSERT INTO {_q('checklist_version_revision')}
                            (version_id, revision_no, fingerprint,
                             reason, idempotency_key,
                             reverts_revision_id, created_by)
                        VALUES (%s, %s, 'pending', %s, %s, %s, %s)
                        RETURNING revision_id
                        """,
                        (version_id, revision_no, reason,
                         idempotency_key, reverts_revision_id, actor),
                    )
                    revision_id = cur.fetchone()["revision_id"]
                    applied = []
                    for seq, change in enumerate(changes, start=1):
                        record = self._apply_change(
                            cur, version=version, change=change,
                            seq=seq, revision_id=revision_id,
                            actor=actor,
                        )
                        applied.append(record)
                        cur.execute(
                            f"""
                            INSERT INTO
                            {_q('checklist_version_revision_change')}
                                (revision_id, seq, item_key, op,
                                 before_state, after_state)
                            VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb)
                            """,
                            (
                                revision_id, seq, record["item_key"],
                                record["op"],
                                json.dumps(record["before_state"],
                                           default=str),
                                json.dumps(record["after_state"],
                                           default=str),
                            ),
                        )
                    fingerprint = self._catalog_fingerprint(cur, version_id)
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_version_revision')}
                           SET fingerprint = %s
                         WHERE revision_id = %s
                        """,
                        (fingerprint, revision_id),
                    )
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_template_version')}
                           SET revision = revision + 1, updated_at = now()
                         WHERE version_id = %s AND revision = %s
                        """,
                        (version_id, expected_revision),
                    )
                    cur.execute(
                        f"""
                        INSERT INTO {_q('checklist_sync_event')}
                            (revision_id) VALUES (%s)
                        RETURNING event_id
                        """,
                        (revision_id,),
                    )
                    event_id = cur.fetchone()["event_id"]
                    self._audit(
                        cur,
                        entity_type="checklist_version_revision",
                        entity_id=revision_id,
                        event_type="CHECKLIST_REVISION_APPLIED",
                        actor=actor,
                        detail={
                            "version_id": version_id,
                            "revision_no": revision_no,
                            "changes": len(applied),
                            "fingerprint": fingerprint,
                            "reverts_revision_id": reverts_revision_id,
                            "reason": reason,
                        },
                    )
        return {
            "revision_id": str(revision_id),
            "revision_no": revision_no,
            "fingerprint": fingerprint,
            "sync_event_id": str(event_id),
            "replayed": False,
        }

    def revert_revision(
        self,
        revision_id: str,
        actor: str,
        reason: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Reversão append-only: nova revisão compensatória que referencia
        o alvo — a revisão original nunca é atualizada (RQ-02)."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT r.revision_id, r.version_id, r.revision_no,
                       v.revision AS version_revision
                  FROM {_q('checklist_version_revision')} r
                  JOIN {_q('checklist_template_version')} v
                    ON v.version_id = r.version_id
                 WHERE r.revision_id = %s
                """,
                (revision_id,),
            )
            target = cur.fetchone()
            if target is None:
                raise RevisionNotFound("Revisão não encontrada.")
            cur.execute(
                f"""
                SELECT revision_id FROM {_q('checklist_version_revision')}
                 WHERE reverts_revision_id = %s
                """,
                (revision_id,),
            )
            if cur.fetchone() is not None:
                raise OperationNotRepeatable(
                    "Revisão já revertida — reverta a revisão "
                    "compensatória se necessário."
                )
            cur.execute(
                f"""
                SELECT seq, item_key, op, before_state, after_state
                  FROM {_q('checklist_version_revision_change')}
                 WHERE revision_id = %s ORDER BY seq DESC
                """,
                (revision_id,),
            )
            inverse = []
            for ch in cur.fetchall():
                op = ch["op"]
                if op == "ADD":
                    inverse.append({"op": "RETIRE", "item_key": ch["item_key"],
                                    "payload": {"reason": "revert"}})
                elif op == "RETIRE":
                    inverse.append({"op": "REACTIVATE",
                                    "item_key": ch["item_key"], "payload": {}})
                elif op == "REACTIVATE":
                    inverse.append({"op": "RETIRE", "item_key": ch["item_key"],
                                    "payload": {"reason": "revert"}})
                elif op == "UPDATE":
                    inverse.append({"op": "UPDATE",
                                    "item_key": ch["item_key"],
                                    "payload": ch["before_state"] or {}})
                elif op == "REORDER":
                    continue  # ordem não é revertida automaticamente
        return self.apply_revision(
            version_id=target["version_id"], actor=actor, reason=reason,
            expected_revision=expected_revision, changes=inverse or [
                {"op": "REORDER", "item_key": "__noop__", "payload": {"order": []}}
            ], idempotency_key=idempotency_key,
            reverts_revision_id=revision_id,
        )

    def list_revisions(self, version_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT r.revision_id, r.revision_no, r.fingerprint,
                       r.reason, r.created_by, r.created_at,
                       r.reverts_revision_id,
                       (SELECT count(*) FROM
                        {_q('checklist_version_revision_change')} c
                         WHERE c.revision_id = r.revision_id) AS changes
                  FROM {_q('checklist_version_revision')} r
                 WHERE r.version_id = %s ORDER BY r.revision_no DESC
                """,
                (version_id,),
            )
            return cur.fetchall()

    def get_revision(self, revision_id: str) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT revision_id, version_id, revision_no, fingerprint,
                       reason, created_by, created_at,
                       reverts_revision_id
                  FROM {_q('checklist_version_revision')}
                 WHERE revision_id = %s
                """,
                (revision_id,),
            )
            revision = cur.fetchone()
            if revision is None:
                raise RevisionNotFound("Revisão não encontrada.")
            cur.execute(
                f"""
                SELECT seq, item_key, op, before_state, after_state
                  FROM {_q('checklist_version_revision_change')}
                 WHERE revision_id = %s ORDER BY seq
                """,
                (revision_id,),
            )
            revision["changes"] = cur.fetchall()
            return revision

    def preview_revision(
        self, version_id: str, changes: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Impacto read-only: fingerprint resultante + competências
        elegíveis que receberiam sync."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT v.version_id, v.template_id, v.status, v.revision
                  FROM {_q('checklist_template_version')} v
                 WHERE v.version_id = %s
                """,
                (version_id,),
            )
            version = cur.fetchone()
            if version is None:
                raise VersionNotFound("Versão não encontrada.")
            cur.execute(
                f"""
                SELECT item_key, item_state
                  FROM {_q('checklist_template_item')}
                 WHERE version_id = %s
                """,
                (version_id,),
            )
            items = {r["item_key"]: r["item_state"] for r in cur.fetchall()}
            affected = []
            for ch in changes:
                state = items.get(ch["item_key"])
                affected.append({
                    "item_key": ch["item_key"], "op": ch["op"],
                    "current_state": state,
                    "valid": (
                        (ch["op"] == "ADD" and state is None) or
                        (ch["op"] in ("UPDATE", "RETIRE")
                         and state == "ACTIVE") or
                        (ch["op"] == "REACTIVATE"
                         and state == "RETIRED") or
                        (ch["op"] == "REORDER")
                    ),
                })
            cur.execute(
                f"""
                SELECT count(*) AS n FROM {_q('monthly_competence')}
                 WHERE status = 'OPEN' AND first_completed_at IS NULL
                   AND completion_record = 'NEVER'
                """
            )
            eligible = cur.fetchone()["n"]
            return {
                "version_id": version_id,
                "eligible_competences": eligible,
                "affected_items": affected,
            }

    # -- conclusão histórica (RQ-10) -------------------------------------

    def refresh_completion_marker(self, competence_id: str) -> bool:
        """Wrapper: abre transação própria e delega ao marcador
        locked (writers §6.2 chamam a variante in-tx)."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    return self.refresh_completion_marker_locked(
                        cur, competence_id
                    )

    def refresh_completion_marker_locked(
        self, cur, competence_id: str
    ) -> bool:
        """Marcador write-once NA transação do writer (RQ-10 §6.2).

        FOR UPDATE na competência → rederivação sobre o mesmo cursor
        (enxerga o efeito não commitado do writer) → UPDATE guardado
        por `first_completed_at IS NULL` + audit. Nunca regride
        COMPLETED."""
        cur.execute(
            f"""
            SELECT competence_id, period, first_completed_at
              FROM {_q('monthly_competence')}
             WHERE competence_id = %s FOR UPDATE
            """,
            (competence_id,),
        )
        row = cur.fetchone()
        if row is None or row["first_completed_at"] is not None:
            return False
        from controllership_finance_app.infrastructure.persistence\
            .closing_package_repository import ClosingPackageRepository
        derived = ClosingPackageRepository()._derive_closing_state(
            cur, row["period"]
        )
        if derived["state"] != "MONTHLY_CLOSING_COMPLETED":
            return False
        cur.execute(
            f"""
            UPDATE {_q('monthly_competence')}
               SET first_completed_at = now(),
                   completion_record = 'COMPLETED',
                   completion_basis = 'MARKER'
             WHERE competence_id = %s
               AND first_completed_at IS NULL
            RETURNING competence_id
            """,
            (competence_id,),
        )
        if cur.fetchone() is None:
            return False
        self._audit(
            cur,
            entity_type="monthly_competence",
            entity_id=str(competence_id),
            competence_id=str(competence_id),
            event_type="MONTHLY_CLOSING_COMPLETED",
            actor=self._SYSTEM_ACTOR,
            detail={"completion_record": "COMPLETED",
                    "completion_basis": "MARKER"},
        )
        return True


    def assess_completion(
        self, competence_id: str, actor: str, reason: str,
        completion_record: str, evidence_summary: str,
    ) -> dict[str, Any]:
        """Reconciliação governada de histórico UNEVALUATED (manage)."""
        if completion_record not in ("NEVER", "COMPLETED"):
            raise ChecklistDomainError(
                "completion_record deve ser NEVER ou COMPLETED."
            )
        if not (reason or "").strip() or not (evidence_summary or "").strip():
            raise ChecklistDomainError(
                "Motivo e resumo de evidência obrigatórios."
            )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT competence_id, period, completion_record,
                               first_completed_at
                          FROM {_q('monthly_competence')}
                         WHERE competence_id = %s FOR UPDATE
                        """,
                        (competence_id,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise CompetenceNotOpened(
                            "Competência não encontrada."
                        )
                    if row["completion_record"] != "UNEVALUATED":
                        raise CompletionReconciliationError(
                            "Reconciliação só se aplica a registros "
                            "UNEVALUATED."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('monthly_competence')}
                           SET completion_record = %s,
                               completion_basis = 'GOVERNED',
                               first_completed_at = CASE
                                   WHEN %s = 'COMPLETED'
                                        AND first_completed_at IS NULL
                                   THEN now()
                                   ELSE first_completed_at END
                         WHERE competence_id = %s
                        """,
                        (completion_record, completion_record,
                         competence_id),
                    )
                    self._audit(
                        cur,
                        entity_type="monthly_competence",
                        entity_id=competence_id,
                        competence_id=competence_id,
                        event_type="COMPLETION_ASSESSED",
                        actor=actor,
                        detail={
                            "period": row["period"],
                            "completion_record": completion_record,
                            "reason": reason,
                            "evidence_summary": evidence_summary,
                        },
                    )
        return {
            "competence_id": competence_id,
            "period": row["period"],
            "completion_record": completion_record,
            "completion_basis": "GOVERNED",
        }

    # -- sincronização (RQ-03/12) -----------------------------------------

    def dispatch_sync_events(self, batch_size: int = 20) -> dict[str, Any]:
        """Claim + processamento de eventos de sync (poller).

        Cada competência reconcilia em subtransação própria; o evento só
        conclui quando todo run está terminal E o read-back de
        convergência confirma (diff vazio)."""
        processed = {"claimed": 0, "events_completed": 0,
                     "runs": {"applied": 0, "skipped": 0, "failed": 0}}
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT event_id, revision_id FROM {_q('checklist_sync_event')}
                 WHERE converged_at IS NULL
                 ORDER BY emitted_at
                 FOR UPDATE SKIP LOCKED LIMIT %s
                """,
                (batch_size,),
            )
            events = cur.fetchall()
        for event in events:
            self._process_sync_event(event, processed)
        return processed

    def _process_sync_event(self, event: dict, processed: dict) -> None:
        processed["claimed"] += 1
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                UPDATE {_q('checklist_sync_event')}
                   SET state = 'DISPATCHED'
                 WHERE event_id = %s AND state = 'EMITTED'
                """,
                (event["event_id"],),
            )
            cur.execute(
                f"""
                SELECT c.competence_id
                  FROM {_q('monthly_competence')} c
                 WHERE c.status = 'OPEN'
                """
            )
            candidates = cur.fetchall()
        for cand in candidates:
            # Safety net RQ-10: conclusões derivadas desde o último
            # write ganham o marker antes da avaliação de elegibilidade.
            self.refresh_completion_marker(str(cand["competence_id"]))
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            for cand in candidates:
                cur.execute(
                    f"""
                    INSERT INTO {_q('checklist_sync_run')}
                        (event_id, competence_id, revision_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (revision_id, competence_id) DO NOTHING
                    """,
                    (event["event_id"], cand["competence_id"],
                     event["revision_id"]),
                )
            cur.execute(
                f"""
                SELECT run_id, competence_id, state
                  FROM {_q('checklist_sync_run')}
                 WHERE revision_id = %s
                """,
                (event["revision_id"],),
            )
            runs = cur.fetchall()
        for run in runs:
            if run["state"] in ("APPLIED", "APPLIED_WITH_EXCLUSIONS",
                                "SKIPPED"):
                continue
            outcome = self._reconcile_competence(
                event["revision_id"], run["competence_id"]
            )
            processed["runs"][outcome] += 1
        self._close_sync_event(event, runs, processed)

    def _close_sync_event(self, event, runs, processed) -> None:
        """Conclusão do evento: só quando todo run terminal + read-back."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT state FROM {_q('checklist_sync_run')}
                 WHERE revision_id = %s
                """,
                (event["revision_id"],),
            )
            states = [r["state"] for r in cur.fetchall()]
            if not states or any(
                st in ("PENDING", "APPLYING", "FAILED", "PARTIAL")
                for st in states
            ):
                return
            # Read-back obrigatório (RQ-03): convergência só com diff
            # residual vazio. Divergência reabre o run para retry —
            # evento permanece não-convergido.
            cur.execute(
                f"""
                SELECT r.run_id, c.competence_id, c.period
                  FROM {_q('checklist_sync_run')} r
                  JOIN {_q('monthly_competence')} c
                    ON c.competence_id = r.competence_id
                 WHERE r.revision_id = %s
                   AND r.state IN ('APPLIED', 'APPLIED_WITH_EXCLUSIONS')
                """,
                (event["revision_id"],),
            )
            divergent = False
            for r in cur.fetchall():
                if self._residual_sync_diff(
                    cur, r["competence_id"], r["period"]
                ):
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_sync_run')}
                           SET state = 'PENDING',
                               last_error = 'read_back_divergence'
                         WHERE run_id = %s
                        """,
                        (r["run_id"],),
                    )
                    divergent = True
            if divergent:
                return
            completion = (
                "CONVERGED_WITH_EXCLUSIONS"
                if "APPLIED_WITH_EXCLUSIONS" in states
                else "CONVERGED"
            )
            cur.execute(
                f"""
                UPDATE {_q('checklist_sync_event')}
                   SET completion_state = %s, converged_at = now()
                 WHERE event_id = %s
                """,
                (completion, event["event_id"]),
            )
            processed["events_completed"] += 1

    def _residual_sync_diff(
        self, cur, competence_id: str, period: str
    ) -> int:
        """Read-back do diff snapshot×winner (RQ-03).

        Conta divergências que a reconciliação teria aplicado —
        estados protegidos (exclusões documentadas) não são diff."""
        cur.execute(
            f"""
            SELECT v.version_id
              FROM {_q('checklist_template_version')} v
              JOIN {_q('checklist_template_series')} s
                ON s.series_id = v.series_id
             WHERE v.status IN ('PUBLISHED', 'SUPERSEDED')
               AND s.status = 'ACTIVE'
               AND v.effective_from_period <= %s
             ORDER BY v.effective_from_period DESC, v.version DESC
             LIMIT 1
            """,
            (period,),
        )
        winner = cur.fetchone()
        winner_items = {}
        if winner:
            cur.execute(
                f"""
                SELECT item_id, item_key, sort_order, sheet, name,
                       purpose, origin_kind, recipient_area,
                       applicability, branch_scope, totvs_report_ref,
                       requirement_notes, validation_scope
                  FROM {_q('checklist_template_item')}
                 WHERE version_id = %s AND item_state = 'ACTIVE'
                """,
                (winner["version_id"],),
            )
            winner_items = {r["item_key"]: r for r in cur.fetchall()}
        cur.execute(
            f"""
            SELECT * FROM {_q('competence_checklist_item')}
             WHERE competence_id = %s
            """,
            (competence_id,),
        )
        snapshot = {r["item_key"]: r for r in cur.fetchall()}
        fields = (
            "sort_order", "sheet", "name", "purpose", "origin_kind",
            "recipient_area", "applicability", "branch_scope",
            "totvs_report_ref", "requirement_notes", "validation_scope",
        )
        residual = 0
        for item_key, item in winner_items.items():
            existing = snapshot.get(item_key)
            if existing is None:
                residual += 1
            elif existing["state"] == "EXPECTED" and any(
                existing[f] != item[f] for f in fields
            ):
                residual += 1
            elif (
                existing["state"] == "CANCELLED"
                and existing["cancel_origin"] == "CATALOG_RETIRE"
            ):
                residual += 1
        residual += sum(
            1 for k, ex in snapshot.items()
            if k not in winner_items and ex["state"] == "EXPECTED"
        )
        return residual

    def _reconcile_competence(
        self, revision_id: str, competence_id: str
    ) -> str:
        """Reconciliação idempotente por competência (transação única).

        Retorna 'applied' | 'skipped' | 'failed'."""
        with self._conn() as conn:
            try:
                with conn.transaction():
                    with conn.cursor(row_factory=dict_row) as cur:
                        cur.execute(
                            f"""
                            SELECT c.competence_id, c.period, c.status,
                                   c.first_completed_at,
                                   c.completion_record
                              FROM {_q('monthly_competence')} c
                             WHERE c.competence_id = %s FOR UPDATE
                            """,
                            (competence_id,),
                        )
                        comp = cur.fetchone()
                        eligible, why = self._syncable(cur, comp)
                        if not eligible:
                            self._finish_run(
                                cur, revision_id, competence_id,
                                "SKIPPED", why,
                            )
                            return "skipped"
                        # §7.1 syncable: derivação deve ser PENDING —
                        # marker NULL não basta (fail-closed).
                        from controllership_finance_app.infrastructure\
                            .persistence.closing_package_repository \
                            import ClosingPackageRepository
                        derived = ClosingPackageRepository()\
                            ._derive_closing_state(cur, comp["period"])
                        if derived["state"] != "PENDING":
                            self._finish_run(
                                cur, revision_id, competence_id,
                                "SKIPPED", "competence_completed",
                            )
                            return "skipped"
                        cur.execute(
                            f"""
                            SELECT v.version_id
                              FROM {_q('checklist_template_version')} v
                              JOIN {_q('checklist_template_series')} s
                                ON s.series_id = v.series_id
                             WHERE v.status IN ('PUBLISHED',
                                                    'SUPERSEDED')
                               AND s.status = 'ACTIVE'
                               AND v.effective_from_period <= %s
                             ORDER BY v.effective_from_period DESC,
                                      v.version DESC LIMIT 1
                            """,
                            (comp["period"],),
                        )
                        winner = cur.fetchone()
                        winner_items = {}
                        if winner:
                            cur.execute(
                                f"""
                                SELECT item_id, item_key, sort_order,
                                       sheet, name, purpose, origin_kind,
                                       recipient_area, applicability,
                                       branch_scope, totvs_report_ref,
                                       requirement_notes,
                                       validation_scope
                                  FROM {_q('checklist_template_item')}
                                 WHERE version_id = %s
                                   AND item_state = 'ACTIVE'
                                """,
                                (winner["version_id"],),
                            )
                            winner_items = {
                                r["item_key"]: r for r in cur.fetchall()
                            }
                        cur.execute(
                            f"""
                            SELECT * FROM {_q('competence_checklist_item')}
                             WHERE competence_id = %s
                            """,
                            (competence_id,),
                        )
                        snapshot = {
                            r["item_key"]: r for r in cur.fetchall()
                        }
                        exclusions = []
                        mutations = 0
                        for item_key, item in winner_items.items():
                            existing = snapshot.get(item_key)
                            if existing is None:
                                cur.execute(
                                    f"""
                                    INSERT INTO
                                    {_q('competence_checklist_item')}
                                    (competence_id, item_key, sort_order,
                                     source_template_item_id,
                                     source_version_id, sheet, name,
                                     purpose, origin_kind,
                                     recipient_area, applicability,
                                     branch_scope, totvs_report_ref,
                                     requirement_notes, validation_scope)
                                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                            %s,%s,%s,%s,%s)
                                    """,
                                    (
                                        competence_id, item_key,
                                        item["sort_order"],
                                        item["item_id"],
                                        winner["version_id"],
                                        item["sheet"], item["name"],
                                        item["purpose"],
                                        item["origin_kind"],
                                        item["recipient_area"],
                                        item["applicability"],
                                        item["branch_scope"],
                                        item["totvs_report_ref"],
                                        item["requirement_notes"],
                                        item["validation_scope"],
                                    ),
                                )
                                mutations += 1
                            elif existing["state"] == "EXPECTED":
                                cur.execute(
                                    f"""
                                    UPDATE
                                    {_q('competence_checklist_item')}
                                       SET sort_order=%s, sheet=%s,
                                           name=%s, purpose=%s,
                                           origin_kind=%s,
                                           recipient_area=%s,
                                           applicability=%s,
                                           branch_scope=%s,
                                           totvs_report_ref=%s,
                                           requirement_notes=%s,
                                           validation_scope=%s
                                     WHERE snapshot_item_id=%s
                                    """,
                                    (
                                        item["sort_order"], item["sheet"],
                                        item["name"], item["purpose"],
                                        item["origin_kind"],
                                        item["recipient_area"],
                                        item["applicability"],
                                        item["branch_scope"],
                                        item["totvs_report_ref"],
                                        item["requirement_notes"],
                                        item["validation_scope"],
                                        existing["snapshot_item_id"],
                                    ),
                                )
                                mutations += 1
                            elif (
                                existing["state"] == "CANCELLED"
                                and existing["cancel_origin"]
                                == "CATALOG_RETIRE"
                            ):
                                # reativação por catálogo comprovada (RQ-05)
                                cur.execute(
                                    f"""
                                    UPDATE
                                    {_q('competence_checklist_item')}
                                       SET state='EXPECTED',
                                           state_reason=NULL,
                                           cancel_origin=NULL,
                                           cancelled_revision_id=NULL
                                     WHERE snapshot_item_id=%s
                                    """,
                                    (existing["snapshot_item_id"],),
                                )
                                mutations += 1
                            else:
                                exclusions.append({
                                    "item_key": item_key,
                                    "reason": "item_state_protected",
                                    "state": existing["state"],
                                })
                        retired_keys = set(snapshot) - set(winner_items)
                        for item_key in retired_keys:
                            existing = snapshot[item_key]
                            if existing["state"] != "EXPECTED":
                                if existing["state"] == "CANCELLED":
                                    continue
                                exclusions.append({
                                    "item_key": item_key,
                                    "reason": "item_locked_retire",
                                    "state": existing["state"],
                                })
                                continue
                            cur.execute(
                                f"""
                                UPDATE {_q('competence_checklist_item')}
                                   SET state='CANCELLED',
                                       state_reason='catalog_retire',
                                       cancel_origin='CATALOG_RETIRE',
                                       cancelled_revision_id=%s
                                 WHERE snapshot_item_id=%s
                                """,
                                (revision_id,
                                 existing["snapshot_item_id"]),
                            )
                            mutations += 1
                            self._close_item_records(
                                cur, existing["snapshot_item_id"],
                                revision_id,
                            )
                        state = (
                            "APPLIED_WITH_EXCLUSIONS" if exclusions
                            else "APPLIED"
                        )
                        self._finish_run(
                            cur, revision_id, competence_id,
                            state, None, exclusions,
                        )
                        self._audit(
                            cur,
                            entity_type="monthly_competence",
                            entity_id=competence_id,
                            competence_id=competence_id,
                            event_type="CHECKLIST_SYNC_APPLIED",
                            actor=self._SYSTEM_ACTOR,
                            detail={
                                "revision_id": revision_id,
                                "mutations": mutations,
                                "exclusions": exclusions,
                            },
                        )
                        return "applied"
            except Exception as exc:  # noqa: BLE001 — dead-letter seguro
                try:
                    with self._conn() as conn2:
                        with conn2.transaction():
                            with conn2.cursor(
                                row_factory=dict_row
                            ) as cur2:
                                cur2.execute(
                                    f"""
                                    UPDATE {_q('checklist_sync_run')}
                                       SET state='FAILED',
                                           attempts=attempts+1,
                                           last_error=%s,
                                           finished_at=now()
                                     WHERE revision_id=%s
                                       AND competence_id=%s
                                    """,
                                    (str(exc)[:500], revision_id,
                                     competence_id),
                                )
                except Exception:  # noqa: BLE001
                    pass
                return "failed"

    def _syncable(self, cur, comp) -> tuple[bool, str | None]:
        """Predicado fail-closed (doc 174 §2.3)."""
        if comp is None:
            return False, "competence_not_found"
        if comp["status"] != "OPEN":
            return False, "competence_not_open"
        if comp["first_completed_at"] is not None:
            return False, "competence_completed"
        if comp["completion_record"] != "NEVER":
            return False, (
                "competence_completed"
                if comp["completion_record"] == "COMPLETED"
                else "competence_unevaluated"
            )
        return True, None

    def _finish_run(
        self, cur, revision_id, competence_id, state,
        skip_reason, exclusions=None,
    ) -> None:
        cur.execute(
            f"""
            UPDATE {_q('checklist_sync_run')}
               SET state=%s, skip_reason=%s, exclusions=%s::jsonb,
                   finished_at=now()
             WHERE revision_id=%s AND competence_id=%s
            """,
            (state, skip_reason, json.dumps(exclusions or []),
             revision_id, competence_id),
        )

    def _close_item_records(self, cur, snapshot_item_id, revision_id) -> None:
        """Encerramento administrativo somente dos registros do item
        retirado (RQ-11): correções PENDING -> CLOSED_REQUIREMENT_RETIRED;
        pendências abertas -> DISMISSED/catalog_retire."""
        cur.execute(
            f"""
            SELECT r.created_by FROM {_q('checklist_version_revision')} r
             WHERE r.revision_id = %s
            """,
            (revision_id,),
        )
        actor = cur.fetchone()["created_by"]
        cur.execute(
            f"""
            UPDATE {_q('item_correction')}
               SET status='CLOSED_REQUIREMENT_RETIRED',
                   closure_reason='requirement_retired',
                   closed_by=%s, closed_at=now()
             WHERE snapshot_item_id=%s AND status='PENDING'
            """,
            (actor, snapshot_item_id),
        )
        cur.execute(
            f"""
            UPDATE {_q('closing_pendency')}
               SET state='DISMISSED',
                   dismiss_justification='catalog_retire',
                   resolution_notes=%s,
                   updated_at=now()
             WHERE snapshot_item_id=%s
               AND state IN ('OPEN','IN_ANALYSIS','WAITING_EXTERNAL')
            """,
            (f"catalog_retire:{revision_id}", snapshot_item_id),
        )

    def get_sync_status(self, period: str) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT competence_id FROM {_q('monthly_competence')}
                 WHERE period = %s
                """,
                (period,),
            )
            row = cur.fetchone()
            if row is None:
                raise CompetenceNotOpened("Competência não aberta.")
            cur.execute(
                f"""
                SELECT r.state, count(*) AS n,
                       COALESCE(jsonb_agg(r.exclusions)
                                FILTER (WHERE r.exclusions <> '[]'),
                                '[]') AS exclusions
                  FROM {_q('checklist_sync_run')} r
                 WHERE r.competence_id = %s
                 GROUP BY r.state
                """,
                (row["competence_id"],),
            )
            states = {r["state"]: r["n"] for r in cur.fetchall()}
            pending = states.get("PENDING", 0) + states.get("APPLYING", 0)
            failed = states.get("FAILED", 0) + states.get("PARTIAL", 0)
            if not states:
                agg = "SYNCED"
            elif failed:
                agg = "FAILED"
            elif pending:
                agg = "PENDING"
            elif states.get("APPLIED_WITH_EXCLUSIONS"):
                agg = "CONVERGED_WITH_EXCLUSIONS"
            else:
                agg = "CONVERGED"
            return {
                "period": period,
                "state": agg,
                "runs": {
                    "applied": states.get("APPLIED", 0),
                    "applied_with_exclusions":
                        states.get("APPLIED_WITH_EXCLUSIONS", 0),
                    "skipped": states.get("SKIPPED", 0),
                    "partial": states.get("PARTIAL", 0),
                    "failed": states.get("FAILED", 0),
                    "pending": pending,
                },
            }

    def list_sync_runs(
        self, template_id: str, revision_id: str | None = None
    ) -> list[dict[str, Any]]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            where, params = "v.template_id = %s", [template_id]
            if revision_id:
                where += " AND r.revision_id = %s"
                params.append(revision_id)
            cur.execute(
                f"""
                SELECT r.run_id, r.event_id, r.competence_id,
                       r.revision_id, r.state, r.attempts,
                       r.skip_reason, r.exclusions, r.last_error,
                       r.started_at, r.finished_at, c.period
                  FROM {_q('checklist_sync_run')} r
                  JOIN {_q('monthly_competence')} c
                    ON c.competence_id = r.competence_id
                  JOIN {_q('checklist_version_revision')} rev
                    ON rev.revision_id = r.revision_id
                  JOIN {_q('checklist_template_version')} v
                    ON v.version_id = rev.version_id
                 WHERE {where}
                 ORDER BY r.run_id
                """,
                params,
            )
            return cur.fetchall()

    def retry_sync_event(self, event_id: str, actor: str) -> dict[str, Any]:
        """Reprocessamento autorizado: FAILED/PARTIAL voltam a PENDING."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"""
                        SELECT event_id, revision_id, state
                          FROM {_q('checklist_sync_event')}
                         WHERE event_id = %s FOR UPDATE
                        """,
                        (event_id,),
                    )
                    event = cur.fetchone()
                    if event is None:
                        raise SyncEventNotFound(
                            "Evento de sincronização não encontrado."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_sync_run')}
                           SET state='PENDING', finished_at=NULL
                         WHERE revision_id=%s
                           AND state IN ('FAILED','PARTIAL')
                        """,
                        (event["revision_id"],),
                    )
                    reopened = cur.rowcount
                    if reopened == 0:
                        raise SyncRetryNotAllowed(
                            "Nenhum run FAILED/PARTIAL para reprocessar."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('checklist_sync_event')}
                           SET state='EMITTED', converged_at=NULL,
                               completion_state=NULL, attempts=attempts+1
                         WHERE event_id=%s
                        """,
                        (event_id,),
                    )
                    self._audit(
                        cur,
                        entity_type="checklist_sync_event",
                        entity_id=event_id,
                        event_type="CHECKLIST_SYNC_RETRIED",
                        actor=actor,
                        detail={"runs_reopened": reopened},
                    )
        return {"event_id": event_id, "runs_reopened": reopened}
