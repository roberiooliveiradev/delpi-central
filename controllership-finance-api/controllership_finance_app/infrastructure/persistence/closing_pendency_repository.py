"""P4 — pendências e classificações (doc 11/23/104).

Estado canônico fechado: OPEN → IN_ANALYSIS → WAITING_EXTERNAL →
RESOLVED | DISMISSED (terminais). Toda mutação: `FOR UPDATE` + OCC
`revision` + evento append-only em `closing_audit_event` — nunca UPDATE
em evento anterior. Sugestão (`suggested_*`) nunca promove decisão;
`confirm_classification` exige ator humano e registra
`CLASSIFICATION_CONFIRMED`. `DISMISSED` exige justificativa e não
substitui N/A (RQ-P4-05). Sem SLA: `pending_since` é fato, não overdue.

Escopo: `branch_scope` da pendência (ou herdado do item) × contexto
declarado — fora do contexto = 404 sem vazamento.
"""

from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
    ClassificationAlreadyConfirmed,
    CompetenceNotOpened,
    Forbidden,
    InvalidPendencyKind,
    InvalidPendencyState,
    InvalidPendencyTransition,
    MissingDismissJustification,
    PendencyNotFound,
    PendencyTerminal,
    PersistenceUnavailable,
    StaleRevision,
)
from controllership_finance_app.domain.closing_documents.resource_scope import (
    normalize_request_scope,
    scope_in_context,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

_SCHEMA = SCHEMA_NAME

PENDENCY_KINDS = frozenset(
    {
        "MISSING_EVIDENCE",
        "VALIDATION_REJECTED",
        "RECONCILIATION_DIVERGENCE",
        "STRUCTURAL_CORRECTION",
        "EXTERNAL_DEPENDENCY",
        "OTHER",
    }
)

PENDENCY_STATES = frozenset(
    {"OPEN", "IN_ANALYSIS", "WAITING_EXTERNAL", "RESOLVED", "DISMISSED"}
)

TERMINAL_STATES = frozenset({"RESOLVED", "DISMISSED"})

# Grafo fechado (RQ-P4-03): origem → destinos permitidos.
_TRANSITIONS: dict[str, frozenset[str]] = {
    "OPEN": frozenset({"IN_ANALYSIS", "WAITING_EXTERNAL", "DISMISSED"}),
    "IN_ANALYSIS": frozenset(
        {"WAITING_EXTERNAL", "RESOLVED", "DISMISSED"}
    ),
    "WAITING_EXTERNAL": frozenset(
        {"IN_ANALYSIS", "RESOLVED", "DISMISSED"}
    ),
}

_TRANSITION_EVENTS = {
    "IN_ANALYSIS": "PENDENCY_ANALYSIS_STARTED",
    "WAITING_EXTERNAL": "PENDENCY_WAITING_EXTERNAL",
    "RESOLVED": "PENDENCY_RESOLVED",
    "DISMISSED": "PENDENCY_DISMISSED",
}

SUGGESTION_SOURCES = frozenset({"DETERMINISTIC", "AI", "MANUAL"})


def _q(table: str) -> str:
    return f"{_SCHEMA}.{table}"


def _validate_kind(kind: str) -> None:
    if kind not in PENDENCY_KINDS:
        raise InvalidPendencyKind(
            f"kind deve ser um de {sorted(PENDENCY_KINDS)}."
        )


class ClosingPendencyRepository:
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

    def _competence_id(self, cur, period: str) -> str:
        cur.execute(
            f"SELECT competence_id FROM {_q('monthly_competence')}"
            " WHERE period = %s",
            (period,),
        )
        row = cur.fetchone()
        if row is None:
            raise CompetenceNotOpened(
                f"Competência {period} não está aberta."
            )
        return row["competence_id"]

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
    ) -> None:
        cur.execute(
            f"""
            INSERT INTO {_q('closing_audit_event')}
                (entity_type, entity_id, competence_id, event_type,
                 actor_subject, detail)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
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

    # -- leitura ------------------------------------------------------------

    def list_pendencies(
        self,
        period: str,
        *,
        state: str | None = None,
        kind: str | None = None,
        responsible: str | None = None,
        request_scope: str = "BOTH",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        ctx = normalize_request_scope(request_scope)
        if state is not None and state not in PENDENCY_STATES:
            raise InvalidPendencyState(
                f"state deve ser um de {sorted(PENDENCY_STATES)}."
            )
        if kind is not None:
            _validate_kind(kind)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            clauses = ["competence_id = %s"]
            params: list[Any] = [competence_id]
            if state is not None:
                clauses.append("state = %s")
                params.append(state)
            if kind is not None:
                clauses.append("kind = %s")
                params.append(kind)
            if responsible is not None:
                clauses.append("responsible_subject = %s")
                params.append(responsible)
            where = " AND ".join(clauses)
            cur.execute(
                f"""
                SELECT pendency_id, competence_id, snapshot_item_id,
                       kind, title, description, state, queue,
                       responsible_subject, branch_scope,
                       suggested_classification, suggestion_rationale,
                       suggestion_source, confirmed_classification,
                       classification_reason, resolution_notes,
                       dismiss_justification, revision,
                       created_by, created_at, updated_at
                  FROM {_q('closing_pendency')}
                 WHERE {where}
                 ORDER BY created_at DESC, pendency_id
                 LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            rows = cur.fetchall()
            items = [
                r
                for r in rows
                if scope_in_context(
                    request_scope=ctx, document_scope=r["branch_scope"]
                )
            ]
            return {
                "items": items,
                "count": len(items),
                "limit": limit,
                "offset": offset,
            }

    def get_pendency(
        self,
        period: str,
        pendency_id: str,
        *,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        ctx = normalize_request_scope(request_scope)
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            row = self._fetch(cur, competence_id, pendency_id)
            if not scope_in_context(
                request_scope=ctx, document_scope=row["branch_scope"]
            ):
                raise PendencyNotFound(
                    "Pendência não encontrada."
                )
            return row

    def _fetch(self, cur, competence_id: str, pendency_id: str) -> dict:
        cur.execute(
            f"""
            SELECT pendency_id, competence_id, snapshot_item_id,
                   kind, title, description, state, queue,
                   responsible_subject, branch_scope,
                   suggested_classification, suggestion_rationale,
                   suggestion_source, confirmed_classification,
                   classification_reason, resolution_notes,
                   dismiss_justification, revision,
                   created_by, created_at, updated_at
              FROM {_q('closing_pendency')}
             WHERE pendency_id = %s AND competence_id = %s
            """,
            (pendency_id, competence_id),
        )
        row = cur.fetchone()
        if row is None:
            raise PendencyNotFound("Pendência não encontrada.")
        return row

    def list_pendency_history(
        self,
        period: str,
        pendency_id: str,
        *,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        pendency = self.get_pendency(
            period, pendency_id, request_scope=request_scope
        )
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT event_id, event_type, actor_subject, detail,
                       created_at
                  FROM {_q('closing_audit_event')}
                 WHERE entity_type = 'closing_pendency'
                   AND entity_id = %s
                 ORDER BY created_at, event_id
                """,
                (pendency_id,),
            )
            return {
                "pendency": pendency,
                "events": cur.fetchall(),
            }

    # -- criação --------------------------------------------------------------

    def create_pendency(
        self,
        period: str,
        *,
        actor: str,
        kind: str,
        title: str,
        description: str | None = None,
        snapshot_item_id: str | None = None,
        queue: str | None = None,
        responsible_subject: str | None = None,
        branch_scope: str | None = None,
        suggested_classification: str | None = None,
        suggestion_rationale: str | None = None,
        suggestion_source: str | None = None,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        _validate_kind(kind)
        ctx = normalize_request_scope(request_scope)
        if suggestion_source is not None and suggestion_source not in (
            SUGGESTION_SOURCES
        ):
            raise InvalidPendencyState(
                "suggestion_source deve ser DETERMINISTIC, AI ou MANUAL."
            )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    scope = (branch_scope or "BOTH").strip().upper()
                    if snapshot_item_id is not None:
                        cur.execute(
                            f"""
                            SELECT snapshot_item_id, branch_scope
                              FROM {_q('competence_checklist_item')}
                             WHERE snapshot_item_id = %s
                               AND competence_id = %s
                            """,
                            (snapshot_item_id, competence_id),
                        )
                        item = cur.fetchone()
                        if item is None:
                            from controllership_finance_app.domain.closing_checklist.errors import (
                                ItemNotFound,
                            )

                            raise ItemNotFound(
                                "Item do checklist não encontrado."
                            )
                        scope = item["branch_scope"] or scope
                    if not scope_in_context(
                        request_scope=ctx, document_scope=scope
                    ):
                        # fora do contexto declarado — não vazar existência
                        raise PendencyNotFound(
                            "Contexto de filial não alcança este recurso."
                        )
                    cur.execute(
                        f"""
                        INSERT INTO {_q('closing_pendency')}
                            (competence_id, snapshot_item_id, kind,
                             title, description, queue,
                             responsible_subject, branch_scope,
                             suggested_classification,
                             suggestion_rationale, suggestion_source,
                             created_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s)
                        RETURNING pendency_id, competence_id,
                                  snapshot_item_id, kind, title,
                                  description, state, queue,
                                  responsible_subject, branch_scope,
                                  suggested_classification,
                                  suggestion_rationale, suggestion_source,
                                  confirmed_classification,
                                  classification_reason, resolution_notes,
                                  dismiss_justification, revision,
                                  created_by, created_at, updated_at
                        """,
                        (
                            competence_id,
                            snapshot_item_id,
                            kind,
                            title,
                            description,
                            queue,
                            responsible_subject,
                            scope,
                            suggested_classification,
                            suggestion_rationale,
                            suggestion_source,
                            actor,
                        ),
                    )
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="closing_pendency",
                        entity_id=row["pendency_id"],
                        competence_id=competence_id,
                        event_type="PENDENCY_CREATED",
                        actor=actor,
                        detail={
                            "kind": kind,
                            "title": title,
                            "snapshot_item_id": (
                                str(snapshot_item_id)
                                if snapshot_item_id
                                else None
                            ),
                            "queue": queue,
                            "responsible_subject": responsible_subject,
                        },
                    )
                    if suggestion_source is not None:
                        self._audit(
                            cur,
                            entity_type="closing_pendency",
                            entity_id=row["pendency_id"],
                            competence_id=competence_id,
                            event_type="CLASSIFICATION_SUGGESTED",
                            actor=actor,
                            detail={
                                "suggested_classification":
                                    suggested_classification,
                                "suggestion_source": suggestion_source,
                            },
                        )
                    return row

    # -- mutações governadas ---------------------------------------------------

    def _lock_pendency(
        self, cur, competence_id: str, pendency_id: str
    ) -> dict:
        cur.execute(
            f"""
            SELECT * FROM {_q('closing_pendency')}
             WHERE pendency_id = %s AND competence_id = %s
             FOR UPDATE
            """,
            (pendency_id, competence_id),
        )
        row = cur.fetchone()
        if row is None:
            raise PendencyNotFound("Pendência não encontrada.")
        return row

    def _check_revision(self, row: dict, expected_revision: int) -> None:
        if row["revision"] != expected_revision:
            raise StaleRevision(
                "A pendência foi alterada por outra sessão."
            )

    def claim_pendency(
        self,
        period: str,
        pendency_id: str,
        actor: str,
        *,
        expected_revision: int,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        ctx = normalize_request_scope(request_scope)
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    row = self._lock_pendency(
                        cur, competence_id, pendency_id
                    )
                    if not scope_in_context(
                        request_scope=ctx,
                        document_scope=row["branch_scope"],
                    ):
                        raise PendencyNotFound(
                            "Pendência não encontrada."
                        )
                    if row["state"] in TERMINAL_STATES:
                        raise PendencyTerminal(
                            "Pendência terminal não admite claim."
                        )
                    self._check_revision(row, expected_revision)
                    previous = row["responsible_subject"]
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_pendency')}
                           SET responsible_subject = %s,
                               revision = revision + 1,
                               updated_at = now()
                         WHERE pendency_id = %s
                        """,
                        (actor, pendency_id),
                    )
                    self._audit(
                        cur,
                        entity_type="closing_pendency",
                        entity_id=pendency_id,
                        competence_id=competence_id,
                        event_type="PENDENCY_CLAIMED",
                        actor=actor,
                        detail={
                            "previous_responsible": previous,
                            "responsible_subject": actor,
                        },
                    )
                    return self._fetch(cur, competence_id, pendency_id)

    def reassign_pendency(
        self,
        period: str,
        pendency_id: str,
        actor: str,
        *,
        new_responsible: str,
        expected_revision: int,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        ctx = normalize_request_scope(request_scope)
        if not new_responsible or not new_responsible.strip():
            raise InvalidPendencyState(
                "new_responsible é obrigatório."
            )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    row = self._lock_pendency(
                        cur, competence_id, pendency_id
                    )
                    if not scope_in_context(
                        request_scope=ctx,
                        document_scope=row["branch_scope"],
                    ):
                        raise PendencyNotFound(
                            "Pendência não encontrada."
                        )
                    if row["state"] in TERMINAL_STATES:
                        raise PendencyTerminal(
                            "Pendência terminal não admite reassign."
                        )
                    self._check_revision(row, expected_revision)
                    # somente o responsável atual, fila ou MANAGE
                    # (enforce de papel é da rota — aqui registramos ator)
                    previous = row["responsible_subject"]
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_pendency')}
                           SET responsible_subject = %s,
                               revision = revision + 1,
                               updated_at = now()
                         WHERE pendency_id = %s
                        """,
                        (new_responsible, pendency_id),
                    )
                    self._audit(
                        cur,
                        entity_type="closing_pendency",
                        entity_id=pendency_id,
                        competence_id=competence_id,
                        event_type="PENDENCY_REASSIGNED",
                        actor=actor,
                        detail={
                            "previous_responsible": previous,
                            "responsible_subject": new_responsible,
                        },
                    )
                    return self._fetch(cur, competence_id, pendency_id)

    def transition_pendency(
        self,
        period: str,
        pendency_id: str,
        actor: str,
        *,
        to_state: str,
        expected_revision: int,
        justification: str | None = None,
        notes: str | None = None,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        ctx = normalize_request_scope(request_scope)
        if to_state not in PENDENCY_STATES:
            raise InvalidPendencyState(
                f"to_state deve ser um de {sorted(PENDENCY_STATES)}."
            )
        if to_state == "DISMISSED" and not (
            justification and justification.strip()
        ):
            raise MissingDismissJustification(
                "DISMISSED exige justificativa."
            )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    row = self._lock_pendency(
                        cur, competence_id, pendency_id
                    )
                    if not scope_in_context(
                        request_scope=ctx,
                        document_scope=row["branch_scope"],
                    ):
                        raise PendencyNotFound(
                            "Pendência não encontrada."
                        )
                    if row["state"] in TERMINAL_STATES:
                        raise PendencyTerminal(
                            "Pendência terminal não admite transição."
                        )
                    allowed = _TRANSITIONS.get(row["state"], frozenset())
                    if to_state not in allowed:
                        raise InvalidPendencyTransition(
                            f"Transição {row['state']} → {to_state} não "
                            "permitida."
                        )
                    self._check_revision(row, expected_revision)
                    updates = [
                        "state = %s",
                        "revision = revision + 1",
                        "updated_at = now()",
                    ]
                    params: list[Any] = [to_state]
                    if to_state == "DISMISSED":
                        updates.append("dismiss_justification = %s")
                        params.append(justification)
                    if to_state == "RESOLVED" and notes is not None:
                        updates.append("resolution_notes = %s")
                        params.append(notes)
                    params.append(pendency_id)
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_pendency')}
                           SET {', '.join(updates)}
                         WHERE pendency_id = %s
                        """,
                        params,
                    )
                    self._audit(
                        cur,
                        entity_type="closing_pendency",
                        entity_id=pendency_id,
                        competence_id=competence_id,
                        event_type=_TRANSITION_EVENTS[to_state],
                        actor=actor,
                        detail={
                            "from_state": row["state"],
                            "to_state": to_state,
                            "justification": justification,
                            "notes": notes,
                        },
                    )
                    return self._fetch(cur, competence_id, pendency_id)

    def confirm_classification(
        self,
        period: str,
        pendency_id: str,
        actor: str,
        *,
        classification: str,
        reason: str | None,
        expected_revision: int,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        ctx = normalize_request_scope(request_scope)
        if not classification or not classification.strip():
            raise InvalidPendencyState(
                "classification é obrigatória."
            )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    row = self._lock_pendency(
                        cur, competence_id, pendency_id
                    )
                    if not scope_in_context(
                        request_scope=ctx,
                        document_scope=row["branch_scope"],
                    ):
                        raise PendencyNotFound(
                            "Pendência não encontrada."
                        )
                    if row["state"] in TERMINAL_STATES:
                        raise PendencyTerminal(
                            "Pendência terminal não admite confirmação."
                        )
                    if row["confirmed_classification"] is not None:
                        raise ClassificationAlreadyConfirmed(
                            "Classificação já confirmada."
                        )
                    self._check_revision(row, expected_revision)
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_pendency')}
                           SET confirmed_classification = %s,
                               classification_reason = %s,
                               revision = revision + 1,
                               updated_at = now()
                         WHERE pendency_id = %s
                        """,
                        (classification, reason, pendency_id),
                    )
                    self._audit(
                        cur,
                        entity_type="closing_pendency",
                        entity_id=pendency_id,
                        competence_id=competence_id,
                        event_type="CLASSIFICATION_CONFIRMED",
                        actor=actor,
                        detail={
                            "confirmed_classification": classification,
                            "suggested_classification":
                                row["suggested_classification"],
                            "reason": reason,
                        },
                    )
                    return self._fetch(cur, competence_id, pendency_id)
