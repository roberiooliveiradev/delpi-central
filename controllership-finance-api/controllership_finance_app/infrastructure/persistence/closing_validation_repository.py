"""Adapter PostgreSQL — validação humana de evidências e itens (P2).

Mesma disciplina do checklist/document repository: transação única por
mutação, lock `FOR UPDATE` no agregado, decisões append-only em
`evidence_decision` (o estado corrente é sempre o último registro —
nenhuma linha de decisão é atualizada ou apagada) e auditoria em
`closing_audit_event` na mesma transação.

Estados do item (`competence_checklist_item.state`):
  EXPECTED → ACCEPTED | NOT_APPLICABLE | CANCELLED
Rejeição de evidência NÃO vira estado do item — `REPLACEMENT_REQUIRED`
é derivação de leitura (RQ-P2-04/05/08).
"""

from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    CompetenceNotOpened,
    CorrectionNotFound,
    CorrectionNotPending,
    DecisionNotFound,
    DocumentNotAttached,
    DocumentNotFound,
    Forbidden,
    InvalidStateTransition,
    InvalidUpload,
    ItemCancelled,
    ItemLocked,
    ItemNotFound,
    NoEvidence,
    PersistenceUnavailable,
    StaleRevision,
    ValidationScopeMismatch,
)
from controllership_finance_app.domain.closing_documents.resource_scope import (
    scope_in_context,
)
from controllership_finance_app.infrastructure.persistence.closing_package_repository import (
    lock_competence_row,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

_SCHEMA = SCHEMA_NAME

CORRECTABLE_ITEM_FIELDS = frozenset(
    {
        "requirement_notes",
        "validation_scope",
        "recipient_area",
        "applicability",
        "branch_scope",
    }
)


def _q(table: str) -> str:
    return f"{_SCHEMA}.{table}"


class ClosingValidationRepository:
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

    # -- leituras de contexto -------------------------------------------------

    def _competence_id(self, cur, period: str) -> Any:
        cur.execute(
            f"SELECT competence_id FROM {_q('monthly_competence')}"
            " WHERE period = %s",
            (period,),
        )
        row = cur.fetchone()
        if row is None:
            raise CompetenceNotOpened(
                "Competência ainda não foi aberta."
            )
        return row["competence_id"]

    def _lock_item(self, cur, competence_id: Any, item_key: str) -> dict:
        cur.execute(
            f"""
            SELECT snapshot_item_id, item_key, competence_id, sheet, name,
                   origin_kind, recipient_area, applicability, branch_scope,
                   state, validation_scope, exceptional, revision,
                   requirement_notes
              FROM {_q('competence_checklist_item')}
             WHERE competence_id = %s AND item_key = %s
             FOR UPDATE
            """,
            (competence_id, item_key),
        )
        row = cur.fetchone()
        if row is None:
            raise ItemNotFound("Item do checklist não encontrado.")
        return row

    @staticmethod
    def _require_active(item: dict) -> None:
        if item["state"] == "CANCELLED":
            raise ItemCancelled("Item do checklist está cancelado.")

    @staticmethod
    def _require_in_context(item: dict, request_scope: str) -> None:
        """Recurso fora do filial-contexto declarado = inexistente (404)."""
        if not scope_in_context(
            request_scope=request_scope,
            document_scope=item.get("branch_scope"),
        ):
            raise ItemNotFound("Item do checklist não encontrado.")

    def _item_documents(
        self, cur, snapshot_item_id: Any, *, for_update: bool = False
    ) -> list[dict]:
        cur.execute(
            f"""
            SELECT document_id, state, current_version_no
              FROM {_q('closing_document')}
             WHERE snapshot_item_id = %s
             ORDER BY created_at{'' if not for_update else ' FOR UPDATE'}
            """,
            (snapshot_item_id,),
        )
        return cur.fetchall()

    def _version_state(self, cur, document_version_id: Any) -> dict | None:
        """Último estado de decisão PER_ATTACHMENT sobre a versão."""
        cur.execute(
            f"""
            SELECT decision_id, decision, result_state, reason_code,
                   comment, decided_by, created_at
              FROM {_q('evidence_decision')}
             WHERE document_version_id = %s AND scope = 'PER_ATTACHMENT'
             ORDER BY created_at DESC LIMIT 1
            """,
            (document_version_id,),
        )
        return cur.fetchone()

    # -- decisões de evidência -------------------------------------------------

    def decide_version(
        self,
        period: str,
        document_id: str,
        actor: str,
        *,
        decision: str,
        reason_code: str | None = None,
        comment: str | None = None,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        """Decisão PER_ATTACHMENT sobre a versão corrente do documento.

        Lock no documento (agregado da versão). Somente a versão corrente
        pode ser decidida; versão SUPERSEDED é histórico preservado.
        Item é recalculado na mesma transação: ACCEPTED somente quando
        todas as versões correntes dos documentos ativos estão aceitas.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    lock_competence_row(cur, competence_id)
                    cur.execute(
                        f"""
                        SELECT d.document_id, d.snapshot_item_id, d.state,
                               d.current_version_no,
                               v.document_version_id
                          FROM {_q('closing_document')} d
                          JOIN {_q('document_version')} v
                            ON v.document_id = d.document_id
                           AND v.version_no = d.current_version_no
                         WHERE d.document_id = %s
                           AND d.competence_id = %s
                         FOR UPDATE OF d
                        """,
                        (document_id, competence_id),
                    )
                    doc = cur.fetchone()
                    if doc is None:
                        raise DocumentNotFound(
                            "Documento não encontrado na competência."
                        )
                    if doc["state"] != "ATTACHED":
                        raise DocumentNotAttached(
                            "Somente documento ATTACHED pode ser validado."
                        )
                    item = None
                    if doc["snapshot_item_id"] is not None:
                        item = self._lock_item(
                            cur,
                            competence_id,
                            self._item_key_of(
                                cur, doc["snapshot_item_id"]
                            ),
                        )
                        self._require_active(item)
                        self._require_in_context(item, request_scope)
                        self._assert_not_package_locked(
                            cur, competence_id,
                            item["item_key"],
                        )
                        if item["validation_scope"] != "PER_ATTACHMENT":
                            raise ValidationScopeMismatch(
                                "Este item exige validação do conjunto "
                                "inteiro."
                            )
                    version_row = self._version_state(
                        cur, doc["document_version_id"]
                    )
                    cur.execute(
                        f"""
                        INSERT INTO {_q('evidence_decision')}
                            (competence_id, snapshot_item_id, document_id,
                             document_version_id, scope, decision,
                             reason_code, comment, decided_by)
                        VALUES (%s,%s,%s,%s,'PER_ATTACHMENT',%s,%s,%s,%s)
                        RETURNING decision_id, decision, created_at
                        """,
                        (
                            competence_id,
                            item["snapshot_item_id"] if item else None,
                            document_id,
                            doc["document_version_id"],
                            decision,
                            reason_code,
                            comment,
                            actor,
                        ),
                    )
                    inserted = cur.fetchone()
                    new_item_state = item["state"] if item else None
                    if item is not None:
                        new_item_state = self._recompute_item_state(
                            cur, item, document_hint=doc
                        )
                        if new_item_state != item["state"]:
                            cur.execute(
                                f"""
                                UPDATE {_q('competence_checklist_item')}
                                   SET state = %s
                                 WHERE snapshot_item_id = %s
                                """,
                                (new_item_state, item["snapshot_item_id"]),
                            )
                    event = (
                        "EVIDENCE_ACCEPTED"
                        if decision == "ACCEPTED"
                        else "EVIDENCE_REJECTED"
                    )
                    self._audit(
                        cur,
                        entity_type="closing_document",
                        entity_id=document_id,
                        competence_id=competence_id,
                        event_type=event,
                        actor=actor,
                        detail={
                            "document_version_id": str(
                                doc["document_version_id"]
                            ),
                            "version_no": doc["current_version_no"],
                            "snapshot_item_id": (
                                str(item["snapshot_item_id"])
                                if item
                                else None
                            ),
                            "decision": decision,
                            "reason_code": reason_code,
                            "item_state": new_item_state,
                        },
                    )
        return {
            "decision_id": inserted["decision_id"],
            "document_id": document_id,
            "version_no": doc["current_version_no"],
            "decision": decision,
            "reason_code": reason_code,
            "comment": comment,
            "previous_decision": (
                version_row["decision"] if version_row else None
            ),
            "item_state": new_item_state,
            "decided_by": actor,
            "created_at": inserted["created_at"],
        }


    @staticmethod
    def _assert_not_package_locked(
        cur, competence_id, item_key: str
    ) -> None:
        """F4/doc 105 + R-105-04: item na composicao de PackageVersion
        vigente SUBMITTED tem evidencia/validacao congeladas. A checagem
        e a mutacao dividem a MESMA transacao e o lock da competencia —
        sem janela TOCTOU contra a submissao do pacote."""
        from controllership_finance_app.domain.closing_checklist.errors import (
            ItemLockedBySubmittedPackage,
        )
        from controllership_finance_app.infrastructure.persistence.closing_package_repository import (
            locked_item_keys_in,
        )

        lock_competence_row(cur, competence_id)
        if item_key in locked_item_keys_in(cur, competence_id):
            raise ItemLockedBySubmittedPackage(
                f"Item {item_key} integra pacote submetido — correcao "
                "exige nova versao do pacote (reabrir/complementar)."
            )

    def _item_key_of(self, cur, snapshot_item_id: Any) -> str:
        cur.execute(
            f"SELECT item_key FROM {_q('competence_checklist_item')}"
            " WHERE snapshot_item_id = %s",
            (snapshot_item_id,),
        )
        return cur.fetchone()["item_key"]

    def _recompute_item_state(
        self, cur, item: dict, document_hint: dict | None = None
    ) -> str:
        return recompute_item_state(
            cur,
            snapshot_item_id=item["snapshot_item_id"],
            validation_scope=item["validation_scope"],
            current_state=item["state"],
        )


    def decide_item_set(
        self,
        period: str,
        item_key: str,
        actor: str,
        *,
        decision: str,
        reason_code: str | None = None,
        comment: str | None = None,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        """Decisão WHOLE_SET — o conjunto inteiro é a unidade lógica.

        A composição avaliada (documento + versão corrente de cada anexo
        ativo) é gravada na decisão; qualquer substituição posterior
        muda a composição e derruba a aceitação (nova validação exigida,
        RQ-P2-05/06).
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    lock_competence_row(cur, competence_id)
                    item = self._lock_item(cur, competence_id, item_key)
                    self._assert_not_package_locked(
                        cur, competence_id,
                        item["item_key"],
                    )
                    self._require_active(item)
                    self._require_in_context(item, request_scope)
                    if item["validation_scope"] != "WHOLE_SET":
                        raise ValidationScopeMismatch(
                            "Este item exige validação por anexo."
                        )
                    docs = self._item_documents(
                        cur, item["snapshot_item_id"], for_update=True
                    )
                    active = [d for d in docs if d["state"] == "ATTACHED"]
                    if not active:
                        raise NoEvidence(
                            "Não há evidência anexada para validar."
                        )
                    composition = sorted(
                        [
                            {
                                "document_id": str(d["document_id"]),
                                "version_no": d["current_version_no"],
                            }
                            for d in active
                        ],
                        key=lambda c: c["document_id"],
                    )
                    cur.execute(
                        f"""
                        INSERT INTO {_q('evidence_decision')}
                            (competence_id, snapshot_item_id, scope,
                             composition, decision, reason_code, comment,
                             decided_by)
                        VALUES (%s,%s,'WHOLE_SET',%s::jsonb,%s,%s,%s,%s)
                        RETURNING decision_id, created_at
                        """,
                        (
                            competence_id,
                            item["snapshot_item_id"],
                            json.dumps(composition),
                            decision,
                            reason_code,
                            comment,
                            actor,
                        ),
                    )
                    inserted = cur.fetchone()
                    new_item_state = (
                        "ACCEPTED" if decision == "ACCEPTED" else "EXPECTED"
                    )
                    if new_item_state != item["state"]:
                        cur.execute(
                            f"""
                            UPDATE {_q('competence_checklist_item')}
                               SET state = %s
                             WHERE snapshot_item_id = %s
                            """,
                            (new_item_state, item["snapshot_item_id"]),
                        )
                    self._audit(
                        cur,
                        entity_type="competence_checklist_item",
                        entity_id=item["snapshot_item_id"],
                        competence_id=competence_id,
                        event_type=(
                            "EVIDENCE_ACCEPTED"
                            if decision == "ACCEPTED"
                            else "EVIDENCE_REJECTED"
                        ),
                        actor=actor,
                        detail={
                            "snapshot_item_id": str(item["snapshot_item_id"]),
                            "item_key": item["item_key"],
                            "scope": "WHOLE_SET",
                            "composition": composition,
                            "decision": decision,
                            "reason_code": reason_code,
                            "item_state": new_item_state,
                        },
                    )
        return {
            "decision_id": inserted["decision_id"],
            "snapshot_item_id": item["snapshot_item_id"],
            "item_key": item["item_key"],
            "scope": "WHOLE_SET",
            "composition": composition,
            "decision": decision,
            "reason_code": reason_code,
            "comment": comment,
            "item_state": new_item_state,
            "decided_by": actor,
            "created_at": inserted["created_at"],
        }

    def reverse_decision(
        self,
        period: str,
        decision_id: str,
        actor: str,
        *,
        result_state: str,
        justification: str,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        """Reversão de rejeição pelo MESMO validador (RQ-P2-10).

        Bloqueia quando existe versão/composição posterior à decidida —
        a rejeição de uma versão SUPERSEDED não pode ser revertida se o
        responsável já anexou substituição. A reversão é uma nova
        decisão append-only (REVERSED), nunca UPDATE na rejeitada.
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    lock_competence_row(cur, competence_id)
                    cur.execute(
                        f"""
                        SELECT decision_id, snapshot_item_id, document_id,
                               document_version_id, scope, decision,
                               decided_by, composition
                          FROM {_q('evidence_decision')}
                         WHERE decision_id = %s AND competence_id = %s
                         FOR UPDATE
                        """,
                        (decision_id, competence_id),
                    )
                    original = cur.fetchone()
                    if original is None:
                        raise DecisionNotFound(
                            "Decisão de validação não encontrada."
                        )
                    if original["decision"] != "REJECTED":
                        raise InvalidStateTransition(
                            "Somente uma rejeição pode ser revertida."
                        )
                    cur.execute(
                        f"""
                        SELECT branch_scope, item_key
                          FROM {_q('competence_checklist_item')}
                         WHERE snapshot_item_id = %s
                        """,
                        (original["snapshot_item_id"],),
                    )
                    scope_row = cur.fetchone() or {}
                    if scope_row.get("item_key"):
                        self._assert_not_package_locked(
                            cur, competence_id,
                            scope_row["item_key"],
                        )
                    if not scope_in_context(
                        request_scope=request_scope,
                        document_scope=scope_row.get("branch_scope"),
                    ):
                        raise DecisionNotFound(
                            "Decisão de validação não encontrada."
                        )
                    if str(original["decided_by"]) != actor:
                        raise Forbidden(
                            "Somente o validador que rejeitou pode reverter."
                        )
                    if original["scope"] == "PER_ATTACHMENT":
                        cur.execute(
                            f"""
                            SELECT d.current_version_no, d.state,
                                   v.version_no AS decided_version
                              FROM {_q('closing_document')} d
                              JOIN {_q('document_version')} v
                                ON v.document_version_id = %s
                             WHERE d.document_id = %s
                             FOR UPDATE OF d
                            """,
                            (
                                original["document_version_id"],
                                original["document_id"],
                            ),
                        )
                        doc = cur.fetchone()
                        if (
                            doc is None
                            or doc["state"] != "ATTACHED"
                            or doc["current_version_no"]
                            != doc["decided_version"]
                        ):
                            raise InvalidStateTransition(
                                "Nova versão já anexada — a reversão da "
                                "rejeição anterior está bloqueada."
                            )
                    else:
                        docs = self._item_documents(
                            cur, original["snapshot_item_id"],
                            for_update=True,
                        )
                        active = [d for d in docs if d["state"] == "ATTACHED"]
                        current = sorted(
                            f"{d['document_id']}:{d['current_version_no']}"
                            for d in active
                        )
                        decided = sorted(
                            f"{c.get('document_id')}:{c.get('version_no')}"
                            for c in original["composition"]
                        )
                        if current != decided:
                            raise InvalidStateTransition(
                                "A composição do conjunto mudou — a "
                                "reversão da rejeição anterior está "
                                "bloqueada."
                            )
                    cur.execute(
                        f"""
                        INSERT INTO {_q('evidence_decision')}
                            (competence_id, snapshot_item_id, document_id,
                             document_version_id, scope, composition,
                             decision, result_state, comment,
                             reverses_decision_id, decided_by)
                        VALUES (%s,%s,%s,%s,%s,%s::jsonb,'REVERSED',
                                %s,%s,%s,%s)
                        RETURNING decision_id, created_at
                        """,
                        (
                            competence_id,
                            original["snapshot_item_id"],
                            original["document_id"],
                            original["document_version_id"],
                            original["scope"],
                            json.dumps(original["composition"]),
                            result_state,
                            justification,
                            decision_id,
                            actor,
                        ),
                    )
                    inserted = cur.fetchone()
                    cur.execute(
                        f"""
                        SELECT snapshot_item_id, item_key, state,
                               validation_scope
                          FROM {_q('competence_checklist_item')}
                         WHERE snapshot_item_id = %s
                         FOR UPDATE
                        """,
                        (original["snapshot_item_id"],),
                    )
                    item = cur.fetchone()
                    if original["scope"] == "WHOLE_SET":
                        new_item_state = (
                            "ACCEPTED"
                            if result_state == "ACCEPTED"
                            else "EXPECTED"
                        )
                    else:
                        new_item_state = self._recompute_item_state(
                            cur, item
                        )
                    if new_item_state != item["state"]:
                        cur.execute(
                            f"""
                            UPDATE {_q('competence_checklist_item')}
                               SET state = %s
                             WHERE snapshot_item_id = %s
                            """,
                            (new_item_state, item["snapshot_item_id"]),
                        )
                    self._audit(
                        cur,
                        entity_type="evidence_decision",
                        entity_id=decision_id,
                        competence_id=competence_id,
                        event_type="REJECTION_REVERSED",
                        actor=actor,
                        detail={
                            "reversed_decision_id": str(decision_id),
                            "result_state": result_state,
                            "item_state": new_item_state,
                        },
                    )
        return {
            "decision_id": inserted["decision_id"],
            "reversed_decision_id": decision_id,
            "decision": "REVERSED",
            "result_state": result_state,
            "item_state": new_item_state,
            "decided_by": actor,
            "created_at": inserted["created_at"],
        }

    # -- transições do item ----------------------------------------------------

    def _transition_item(
        self,
        period: str,
        item_key: str,
        actor: str,
        *,
        allowed_from: tuple[str, ...],
        to_state: str,
        justification: str,
        event_type: str,
        allowed_applicability: tuple[str, ...] | None = None,
        require_no_material_events: bool = False,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    item = self._lock_item(cur, competence_id, item_key)
                    self._require_in_context(item, request_scope)
                    if item["state"] not in allowed_from:
                        raise InvalidStateTransition(
                            f"Item em estado {item['state']} — transição "
                            f"para {to_state} não permitida."
                        )
                    if (
                        allowed_applicability
                        and item["applicability"] not in allowed_applicability
                    ):
                        raise InvalidStateTransition(
                            f"Item {item['applicability']} não admite "
                            "marcação N/A — apenas CONDITIONAL."
                        )
                    if require_no_material_events:
                        cur.execute(
                            f"""
                            SELECT 1
                              FROM {_q('closing_document')} d
                             WHERE d.snapshot_item_id = %s
                               AND d.state = 'ATTACHED'
                             LIMIT 1
                            """,
                            (item["snapshot_item_id"],),
                        )
                        if cur.fetchone() is not None:
                            raise ItemLocked(
                                "Item já possui evidência — cancelamento "
                                "simples bloqueado; use correção "
                                "estrutural."
                            )
                    cur.execute(
                        f"""
                        UPDATE {_q('competence_checklist_item')}
                           SET state = %s, state_reason = %s
                         WHERE snapshot_item_id = %s
                        """,
                        (to_state, justification, item["snapshot_item_id"]),
                    )
                    self._audit(
                        cur,
                        entity_type="competence_checklist_item",
                        entity_id=item["snapshot_item_id"],
                        competence_id=competence_id,
                        event_type=event_type,
                        actor=actor,
                        detail={
                            "item_key": item_key,
                            "from_state": item["state"],
                            "to_state": to_state,
                            "justification": justification,
                        },
                    )
        item = dict(item)
        item["state"] = to_state
        item["state_reason"] = justification
        return item

    def mark_not_applicable(
        self,
        period: str,
        item_key: str,
        actor: str,
        justification: str,
        *,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        return self._transition_item(
            period,
            item_key,
            actor,
            allowed_from=("EXPECTED",),
            to_state="NOT_APPLICABLE",
            justification=justification,
            event_type="ITEM_NOT_APPLICABLE",
            allowed_applicability=("CONDITIONAL",),
            request_scope=request_scope,
        )

    def revert_not_applicable(
        self,
        period: str,
        item_key: str,
        actor: str,
        justification: str,
        *,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        return self._transition_item(
            period,
            item_key,
            actor,
            allowed_from=("NOT_APPLICABLE",),
            to_state="EXPECTED",
            justification=justification,
            event_type="ITEM_NA_REVERTED",
            request_scope=request_scope,
        )

    def cancel_item(
        self,
        period: str,
        item_key: str,
        actor: str,
        justification: str,
        *,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        return self._transition_item(
            period,
            item_key,
            actor,
            allowed_from=("EXPECTED",),
            to_state="CANCELLED",
            justification=justification,
            event_type="ITEM_CANCELLED",
            require_no_material_events=True,
            request_scope=request_scope,
        )

    # -- item excepcional --------------------------------------------------------

    def create_exceptional_item(
        self,
        period: str,
        actor: str,
        *,
        sheet: str,
        name: str,
        justification: str,
        purpose: str | None = None,
        origin_kind: str = "EXTERNAL",
        recipient_area: str | None = None,
        applicability: str = "REQUIRED",
        branch_scope: str = "BOTH",
        validation_scope: str = "PER_ATTACHMENT",
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        """Item excepcional — só existe na competência, nunca no template."""
        if not scope_in_context(
            request_scope=request_scope, document_scope=branch_scope
        ):
            raise InvalidUpload(
                "branch_scope do item fora do contexto declarado."
            )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    cur.execute(
                        f"""
                        SELECT COALESCE(MAX(sort_order), 0) AS max_sort
                          FROM {_q('competence_checklist_item')}
                         WHERE competence_id = %s
                        """,
                        (competence_id,),
                    )
                    sort_order = int(cur.fetchone()["max_sort"]) + 1
                    item_key = f"EXC-{sort_order:02d}"
                    cur.execute(
                        f"""
                        INSERT INTO {_q('competence_checklist_item')}
                            (competence_id, item_key, sort_order, sheet,
                             name, purpose, origin_kind, recipient_area,
                             applicability, branch_scope, state,
                             validation_scope, exceptional, state_reason)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'EXPECTED',
                                %s, TRUE, %s)
                        RETURNING snapshot_item_id, item_key, state
                        """,
                        (
                            competence_id,
                            item_key,
                            sort_order,
                            sheet,
                            name,
                            purpose,
                            origin_kind,
                            recipient_area,
                            applicability,
                            branch_scope,
                            validation_scope,
                            justification,
                        ),
                    )
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="competence_checklist_item",
                        entity_id=row["snapshot_item_id"],
                        competence_id=competence_id,
                        event_type="ITEM_CREATED",
                        actor=actor,
                        detail={
                            "item_key": item_key,
                            "exceptional": True,
                            "justification": justification,
                        },
                    )
        return {
            "snapshot_item_id": row["snapshot_item_id"],
            "item_key": row["item_key"],
            "sort_order": sort_order,
            "sheet": sheet,
            "name": name,
            "purpose": purpose,
            "origin_kind": origin_kind,
            "recipient_area": recipient_area,
            "applicability": applicability,
            "branch_scope": branch_scope,
            "validation_scope": validation_scope,
            "exceptional": True,
            "state": row["state"],
        }

    # -- correção estrutural -----------------------------------------------------

    def request_correction(
        self,
        period: str,
        item_key: str,
        actor: str,
        *,
        changes: dict[str, Any],
        justification: str,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        """ACCESS REQUEST — correção estrutural pós-execução (RQ-P2-09)."""
        unknown = set(changes) - CORRECTABLE_ITEM_FIELDS
        if unknown:
            raise InvalidUpload(
                "Campos não corrigíveis: " + ", ".join(sorted(unknown))
            )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    item = self._lock_item(cur, competence_id, item_key)
                    self._require_active(item)
                    self._require_in_context(item, request_scope)
                    cur.execute(
                        f"""
                        INSERT INTO {_q('item_correction')}
                            (competence_id, snapshot_item_id, item_revision,
                             changes, justification, requested_by)
                        VALUES (%s,%s,%s,%s::jsonb,%s,%s)
                        RETURNING correction_id, status, requested_at
                        """,
                        (
                            competence_id,
                            item["snapshot_item_id"],
                            item["revision"],
                            json.dumps(changes),
                            justification,
                            actor,
                        ),
                    )
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="competence_checklist_item",
                        entity_id=item["snapshot_item_id"],
                        competence_id=competence_id,
                        event_type="CORRECTION_REQUESTED",
                        actor=actor,
                        detail={
                            "correction_id": str(row["correction_id"]),
                            "item_key": item_key,
                            "item_revision": item["revision"],
                            "changes": changes,
                        },
                    )
        return {
            "correction_id": row["correction_id"],
            "snapshot_item_id": item["snapshot_item_id"],
            "item_key": item_key,
            "item_revision": item["revision"],
            "changes": changes,
            "status": row["status"],
            "requested_by": actor,
            "requested_at": row["requested_at"],
        }

    def review_correction(
        self,
        period: str,
        correction_id: str,
        actor: str,
        *,
        approve: bool,
        review_reason: str | None = None,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        """MANAGE REVIEW — aprovação cria nova `revision` do item.

        A revisão compara `item_revision` capturada no pedido com a
        revisão corrente: divergência = `stale_revision` (a correção
        deve ser refeita sobre o estado atual). Request e aprovação são
        eventos separados mesmo quando o mesmo ator MANAGE solicita e
        aprova (autoaprovação governada, RQ-P2-09).
        """
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    cur.execute(
                        f"""
                        SELECT c.correction_id, c.snapshot_item_id,
                               c.item_revision, c.changes, c.status,
                               c.requested_by, i.item_key, i.revision,
                               i.branch_scope
                          FROM {_q('item_correction')} c
                          JOIN {_q('competence_checklist_item')} i
                            ON i.snapshot_item_id = c.snapshot_item_id
                         WHERE c.correction_id = %s
                           AND c.competence_id = %s
                         FOR UPDATE OF c, i
                        """,
                        (correction_id, competence_id),
                    )
                    correction = cur.fetchone()
                    if correction is None:
                        raise CorrectionNotFound(
                            "Solicitação de correção não encontrada."
                        )
                    if not scope_in_context(
                        request_scope=request_scope,
                        document_scope=correction["branch_scope"],
                    ):
                        raise CorrectionNotFound(
                            "Solicitação de correção não encontrada."
                        )
                    if correction["status"] != "PENDING":
                        raise CorrectionNotPending(
                            "Correção já foi revisada."
                        )
                    if correction["item_revision"] != correction["revision"]:
                        raise StaleRevision(
                            "O item mudou desde a solicitação — refaça a "
                            "correção sobre o estado atual."
                        )
                    status = "APPROVED" if approve else "REJECTED"
                    cur.execute(
                        f"""
                        UPDATE {_q('item_correction')}
                           SET status = %s, reviewed_by = %s,
                               reviewed_at = now(), review_reason = %s
                         WHERE correction_id = %s
                        """,
                        (status, actor, review_reason, correction_id),
                    )
                    new_revision = correction["revision"]
                    if approve:
                        changes = correction["changes"]
                        allowed = {
                            k: v
                            for k, v in changes.items()
                            if k in CORRECTABLE_ITEM_FIELDS
                        }
                        if allowed:
                            assignments = ", ".join(
                                f"{k} = %s" for k in allowed
                            )
                            cur.execute(
                                f"""
                                UPDATE {_q('competence_checklist_item')}
                                   SET {assignments},
                                       revision = revision + 1
                                 WHERE snapshot_item_id = %s
                                """,
                                (
                                    *allowed.values(),
                                    correction["snapshot_item_id"],
                                ),
                            )
                        else:
                            cur.execute(
                                f"""
                                UPDATE {_q('competence_checklist_item')}
                                   SET revision = revision + 1
                                 WHERE snapshot_item_id = %s
                                """,
                                (correction["snapshot_item_id"],),
                            )
                        new_revision = correction["revision"] + 1
                    self._audit(
                        cur,
                        entity_type="competence_checklist_item",
                        entity_id=correction["snapshot_item_id"],
                        competence_id=competence_id,
                        event_type=(
                            "CORRECTION_APPROVED"
                            if approve
                            else "CORRECTION_REJECTED"
                        ),
                        actor=actor,
                        detail={
                            "correction_id": str(correction_id),
                            "item_key": correction["item_key"],
                            "requested_by": str(correction["requested_by"]),
                            "new_revision": new_revision,
                            "review_reason": review_reason,
                        },
                    )
        return {
            "correction_id": correction_id,
            "snapshot_item_id": correction["snapshot_item_id"],
            "item_key": correction["item_key"],
            "status": status,
            "new_revision": new_revision,
            "reviewed_by": actor,
        }

    def list_corrections(
        self,
        period: str,
        item_key: str | None = None,
        *,
        request_scope: str = "BOTH",
    ) -> list[dict[str, Any]]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            clauses = ["c.competence_id = %s"]
            params: list[Any] = [competence_id]
            if item_key:
                clauses.append("i.item_key = %s")
                params.append(item_key)
            cur.execute(
                f"""
                SELECT c.correction_id, c.snapshot_item_id, i.item_key,
                       i.branch_scope, c.item_revision, c.changes,
                       c.justification, c.status, c.requested_by,
                       c.requested_at, c.reviewed_by, c.reviewed_at,
                       c.review_reason
                  FROM {_q('item_correction')} c
                  JOIN {_q('competence_checklist_item')} i
                    ON i.snapshot_item_id = c.snapshot_item_id
                 WHERE {' AND '.join(clauses)}
                 ORDER BY c.requested_at DESC
                """,
                params,
            )
            return [
                row
                for row in cur.fetchall()
                if scope_in_context(
                    request_scope=request_scope,
                    document_scope=row.get("branch_scope"),
                )
            ]

    # -- histórico de decisões ---------------------------------------------------

    def list_item_decisions(
        self,
        period: str,
        item_key: str,
        *,
        request_scope: str = "BOTH",
    ) -> dict[str, Any]:
        """Estado de validação do item: decisões por documento/versão.

        Cada documento ativo expõe a decisão corrente sobre a sua
        versão corrente; decisões de versões SUPERSEDED permanecem no
        histórico imutável (acessíveis via eventos/audit trail).
        """
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            cur.execute(
                f"""
                SELECT snapshot_item_id, item_key, state, validation_scope,
                       applicability, branch_scope
                  FROM {_q('competence_checklist_item')}
                 WHERE competence_id = %s AND item_key = %s
                """,
                (competence_id, item_key),
            )
            item = cur.fetchone()
            if item is None:
                raise ItemNotFound("Item do checklist não encontrado.")
            self._require_in_context(item, request_scope)
            documents = self._item_documents(
                cur, item["snapshot_item_id"]
            )
            per_document = []
            for doc in documents:
                cur.execute(
                    f"""
                    SELECT v.document_version_id, v.version_no
                      FROM {_q('document_version')} v
                     WHERE v.document_id = %s
                     ORDER BY v.version_no
                    """,
                    (doc["document_id"],),
                )
                versions = cur.fetchall()
                current_ver = next(
                    (
                        v
                        for v in versions
                        if v["version_no"] == doc["current_version_no"]
                    ),
                    None,
                )
                current_decision = (
                    self._version_state(cur, current_ver["document_version_id"])
                    if current_ver
                    else None
                )
                per_document.append(
                    {
                        "document_id": doc["document_id"],
                        "state": doc["state"],
                        "current_version_no": doc["current_version_no"],
                        "current_version_decision": (
                            {
                                "decision_id": current_decision["decision_id"],
                                "decision": current_decision["decision"],
                                "result_state": current_decision[
                                    "result_state"
                                ],
                                "reason_code": current_decision[
                                    "reason_code"
                                ],
                                "comment": current_decision["comment"],
                                "decided_by": current_decision["decided_by"],
                                "created_at": current_decision["created_at"],
                            }
                            if current_decision
                            else None
                        ),
                    }
                )
            cur.execute(
                f"""
                SELECT decision_id, document_id, scope, composition,
                       decision,
                       reason_code, comment, result_state,
                       reverses_decision_id, decided_by, created_at
                  FROM {_q('evidence_decision')}
                 WHERE snapshot_item_id = %s
                 ORDER BY created_at
                """,
                (item["snapshot_item_id"],),
            )
            decisions = cur.fetchall()
        return {
            "snapshot_item_id": item["snapshot_item_id"],
            "item_key": item["item_key"],
            "state": item["state"],
            "validation_scope": item["validation_scope"],
            "applicability": item["applicability"],
            "documents": per_document,
            "decisions": decisions,
        }

    # -- internals ------------------------------------------------------------

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


def _item_documents_of(cur, snapshot_item_id) -> list[dict]:
    cur.execute(
        f"""
        SELECT document_id, state, current_version_no
          FROM {_q('closing_document')}
         WHERE snapshot_item_id = %s
         ORDER BY created_at
        """,
        (snapshot_item_id,),
    )
    return cur.fetchall()


def _last_version_decision(cur, document_version_id) -> dict | None:
    cur.execute(
        f"""
        SELECT decision_id, decision, result_state, reason_code,
               comment, decided_by, created_at
          FROM {_q('evidence_decision')}
         WHERE document_version_id = %s AND scope = 'PER_ATTACHMENT'
         ORDER BY created_at DESC LIMIT 1
        """,
        (document_version_id,),
    )
    return cur.fetchone()


def recompute_item_state(
    cur, *, snapshot_item_id, validation_scope: str, current_state: str
) -> str:
    """Deriva o estado do item a partir das decisões correntes (RQ-P2-05).

    ACCEPTED somente quando existe evidência e TODAS as versões
    correntes dos documentos ativos do item estão aceitas
    (PER_ATTACHMENT) ou quando a composição WHOLE_SET decidida é
    exatamente a corrente — qualquer substituição/cancelamento muda a
    composição e rebaixa para EXPECTED (nova validação exigida).
    """
    item = {
        "state": current_state,
        "snapshot_item_id": snapshot_item_id,
        "validation_scope": validation_scope,
    }
    if item["state"] in ("CANCELLED", "NOT_APPLICABLE"):
        return item["state"]
    docs = _item_documents_of(cur, item["snapshot_item_id"])
    active = [d for d in docs if d["state"] == "ATTACHED"]
    if not active:
        return "EXPECTED"
    if item["validation_scope"] == "WHOLE_SET":
        cur.execute(
            f"""
            SELECT d.composition, d.decision
              FROM {_q('evidence_decision')} d
             WHERE d.snapshot_item_id = %s
               AND d.scope = 'WHOLE_SET'
             ORDER BY d.created_at DESC LIMIT 1
            """,
            (item["snapshot_item_id"],),
        )
        latest = cur.fetchone()
        if latest is None or latest["decision"] != "ACCEPTED":
            return "EXPECTED"
        current = sorted(
            f"{d['document_id']}:{d['current_version_no']}"
            for d in active
        )
        decided = sorted(
            f"{c.get('document_id')}:{c.get('version_no')}"
            for c in latest["composition"]
        )
        return "ACCEPTED" if current == decided else "EXPECTED"
    all_accepted = True
    for d in active:
        cur.execute(
            f"""
            SELECT v.document_version_id
              FROM {_q('document_version')} v
             WHERE v.document_id = %s AND v.version_no = %s
            """,
            (d["document_id"], d["current_version_no"]),
        )
        ver = cur.fetchone()
        last = _last_version_decision(cur, ver["document_version_id"])
        effective = (
            last["result_state"]
            if last and last["decision"] == "REVERSED"
            else last["decision"] if last else None
        )
        if effective != "ACCEPTED":
            all_accepted = False
            break
    return "ACCEPTED" if all_accepted else "EXPECTED"

