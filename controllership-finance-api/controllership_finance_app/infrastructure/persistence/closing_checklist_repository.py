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
    DuplicateItemKey,
    EmptyResultingChecklist,
    IdempotencyConflict,
    InvalidRequirementWindow,
    ItemNotFound,
    OperationBusy,
    PersistenceUnavailable,
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
                SELECT v.version_id, v.template_id, v.version, v.status,
                       v.revision, v.effective_from_period, v.published_by,
                       v.published_at, v.inactivated_at, v.created_at,
                       (SELECT count(*) FROM {_q('checklist_template_item')} i
                         WHERE i.version_id = v.version_id) AS item_count
                  FROM {_q('checklist_template_version')} v
                 WHERE v.template_id = %s
                 ORDER BY v.version
                """,
                (template_id,),
            )
            return cur.fetchall()

    def get_version(self, template_id: str, version: int) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT version_id, template_id, version, status, revision,
                       effective_from_period, published_by, published_at,
                       inactivated_by, inactivated_at, created_at
                  FROM {_q('checklist_template_version')}
                 WHERE template_id = %s AND version = %s
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
                       validation_scope
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
        clauses = [
            "e.entity_type = 'checklist_template_version'",
            "v.template_id = %s",
        ]
        params: list[Any] = [template_id]
        if version is not None:
            clauses.append("v.version = %s")
            params.append(version)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT e.event_id, e.entity_id, e.competence_id,
                       e.event_type, e.actor_subject, e.detail,
                       e.created_at, v.version
                  FROM {_q('closing_audit_event')} e
                  JOIN {_q('checklist_template_version')} v
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
                        next_version = (latest["version"] + 1) if latest else 1
                        cur.execute(
                            f"""
                            INSERT INTO {_q('checklist_template_version')}
                                (template_id, version, status, created_by)
                            VALUES (%s, %s, 'DRAFT', %s)
                            RETURNING version_id, version, status, revision
                            """,
                            (template_id, next_version, actor),
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
                         WHERE template_id = %s AND version = %s
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
                         WHERE template_id = %s AND version = %s
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
                         WHERE template_id = %s AND version = %s
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
                         WHERE template_id = %s AND version = %s
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
                        UPDATE {_q('checklist_template_version')}
                           SET status = 'PUBLISHED',
                               effective_from_period = %s,
                               published_by = %s, published_at = now(),
                               updated_at = now()
                         WHERE template_id = %s AND version = %s
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
                         WHERE template_id = %s AND version = %s
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
                SELECT version_id, template_id, version,
                       effective_from_period
                  FROM {_q('checklist_template_version')}
                 WHERE status = 'PUBLISHED'
                   AND effective_from_period <= %s
                 ORDER BY effective_from_period DESC, version DESC
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
                        SELECT version_id, template_id, version,
                               effective_from_period
                          FROM {_q('checklist_template_version')}
                         WHERE status = 'PUBLISHED'
                           AND effective_from_period <= %s
                         ORDER BY effective_from_period DESC,
                                  version DESC
                         LIMIT 1
                        """,
                        (period,),
                    )
                    published = cur.fetchone()
                    cur.execute(
                        f"""
                        INSERT INTO {_q('monthly_competence')}
                            (period, template_version_id, opened_by)
                        VALUES (%s, %s, %s)
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
                       validation_scope, exceptional, revision, state_reason
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
                       exceptional, revision, state_reason
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
            SELECT version_id, status FROM {_q('checklist_template_version')}
             WHERE template_id = %s AND version = %s
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
                json.dumps(detail),
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

                        cur.execute(
                            f"""
                            SELECT max(version) AS max_version
                              FROM {_q('checklist_template_version')}
                             WHERE template_id = %s
                            """,
                            (template_id,),
                        )
                        next_version = (
                            cur.fetchone()["max_version"] or 0
                        ) + 1
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
        cur.execute(
            f"""
            INSERT INTO {_q('checklist_template_version')}
                (template_id, version, status, created_by)
            VALUES (%s, %s, 'DRAFT', %s)
            RETURNING version_id
            """,
            (template_id, version, actor),
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
