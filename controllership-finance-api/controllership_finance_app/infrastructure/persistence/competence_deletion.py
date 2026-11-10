"""Exclusão administrativa de competência mensal (CF-UX-054).

Uma competência só é removida quando a transação comprova a ausência de
dependências operacionais. A auditoria de abertura não é apagada: a FK
histórica usa ON DELETE SET NULL (V021) e o evento COMPETENCE_DELETED
guarda período, identificador, motivo e chave de idempotência.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    CompetenceDeleteBlocked,
    CompetenceDeleteConflict,
    CompetenceDeleteInvalid,
    CompetenceDeleteUnavailable,
    CompetenceNotFound,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

PERIOD_RE = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")

# Única referência histórica que não bloqueia a exclusão.
HISTORICAL_TABLES = frozenset({"closing_audit_event"})

DEPENDENCY_LABELS = {
    "competence_checklist_item": "itens de checklist",
    "closing_document": "documentos",
    "document_file": "arquivos de evidência",
    "evidence_decision": "decisões de evidência",
    "item_correction": "correções de item",
    "closing_pendency": "pendências",
    "closing_cutoff": "registros de cutoff",
    "closing_reconciliation": "conciliações",
    "closing_revalidation": "revalidações",
    "closing_stock_state": "estado de estoque",
    "closing_package": "pacotes",
    "closing_review_assignment": "atribuições de revisão",
    "closing_terminal_rejection": "rejeição terminal",
    "closing_notification_event": "eventos de notificação",
    "document_message": "mensagens de documento",
    "document_adjustment_request": "solicitações de ajuste",
    "clara_proposal": "propostas CLARA pendentes",
    "clara_batch": "lotes CLARA pendentes",
}


def diagnose_competence_deletion(period: str) -> dict[str, Any]:
    """Diagnóstico somente leitura. Indisponibilidade não vira zero."""
    normalized = _period(period)
    with _connection() as conn, conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            row = _lock_competence(cur, normalized, share=True)
            if row is None:
                raise CompetenceNotFound(
                    "Competência não encontrada.",
                    details={"outcome": "not_found", "period": normalized},
                )
            reasons = _deletion_reasons(cur, row)
    return _eligibility(row, reasons)


def delete_competence(
    period: str,
    *,
    actor: str,
    expected_competence_id: str,
    reason: str,
    idempotency_key: str,
    channel: str = "portal",
) -> dict[str, Any]:
    """Remove a competência exata ou reproduz a exclusão já concluída."""
    normalized = _period(period)
    actor_id = _actor(actor)
    expected_id = _uuid(expected_competence_id, "expected_competence_id")
    clean_reason = _reason(reason)
    key = _idempotency_key(idempotency_key)
    try:
        with _connection() as conn, conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                return _delete_locked(
                    cur,
                    period=normalized,
                    actor=actor_id,
                    expected_id=expected_id,
                    reason=clean_reason,
                    idempotency_key=key,
                    channel=channel,
                )
    except (
        CompetenceNotFound,
        CompetenceDeleteBlocked,
        CompetenceDeleteConflict,
        CompetenceDeleteUnavailable,
        CompetenceDeleteInvalid,
    ):
        raise
    except psycopg.Error as exc:
        raise CompetenceDeleteUnavailable(
            "Não foi possível confirmar as dependências da competência.",
            details={"outcome": "unavailable", "period": normalized},
        ) from exc


def _delete_locked(
    cur,
    *,
    period: str,
    actor: str,
    expected_id: str,
    reason: str,
    idempotency_key: str,
    channel: str,
) -> dict[str, Any]:
    prior = _prior_deletion(cur, idempotency_key)
    if prior is not None and prior["competence_id"] != expected_id:
        raise CompetenceDeleteConflict(
            "Esta solicitação já excluiu outra competência.",
            details={
                "outcome": "conflict",
                "period": period,
                "idempotency_key": idempotency_key,
            },
        )
    row = _lock_competence(cur, period, share=False)
    if row is None:
        if prior is not None and prior["competence_id"] == expected_id:
            _assert_absent(cur, period)
            return _success(prior, replayed=True)
        raise CompetenceNotFound(
            "Competência não encontrada.",
            details={"outcome": "not_found", "period": period},
        )
    current_id = str(row["competence_id"])
    if current_id != expected_id:
        raise CompetenceDeleteConflict(
            "A competência deste período não é a informada.",
            details={
                "outcome": "conflict",
                "period": period,
                "competence_id": current_id,
            },
        )
    if prior is not None:
        raise CompetenceDeleteConflict(
            "A exclusão anterior desta solicitação não foi concluída.",
            details={"outcome": "conflict", "period": period},
        )
    if row["status"] != "OPEN":
        raise CompetenceDeleteBlocked(
            "A competência não está em estado elegível à exclusão.",
            details={
                "outcome": "blocked",
                "period": period,
                "reasons": [
                    {
                        "code": "status",
                        "count": 1,
                        "label": f"estado {row['status']}",
                    }
                ],
            },
        )
    reasons = _deletion_reasons(cur, row)
    if reasons:
        raise CompetenceDeleteBlocked(
            "A competência tem dependências e não pode ser excluída.",
            details={
                "outcome": "blocked",
                "period": period,
                "competence_id": current_id,
                "reasons": reasons,
            },
        )
    deleted_at = datetime.now(timezone.utc)
    detail = {
        "period": period,
        "competence_id": current_id,
        "reason": reason,
        "idempotency_key": idempotency_key,
        "template_version_id": (
            str(row["template_version_id"])
            if row["template_version_id"]
            else None
        ),
        "status": row["status"],
        "channel": channel,
        "deleted_at": deleted_at.isoformat(),
    }
    cur.execute(
        f"""
        INSERT INTO {SCHEMA_NAME}.closing_audit_event
            (entity_type, entity_id, competence_id, event_type,
             actor_subject, detail)
        VALUES ('monthly_competence', %s, %s, 'COMPETENCE_DELETED',
                %s, %s::jsonb)
        RETURNING event_id, created_at
        """,
        (current_id, current_id, actor, json.dumps(detail)),
    )
    audit = cur.fetchone()
    cur.execute(
        f"""
        DELETE FROM {SCHEMA_NAME}.monthly_competence
         WHERE competence_id = %s
           AND period = %s
        """,
        (current_id, period),
    )
    if cur.rowcount != 1:
        raise CompetenceDeleteUnavailable(
            "A exclusão não pôde ser confirmada.",
            details={"outcome": "unavailable", "period": period},
        )
    _assert_absent(cur, period)
    return {
        "competence_id": current_id,
        "period": period,
        "deleted": True,
        "deleted_at": audit["created_at"],
        "audit_reference": str(audit["event_id"]),
        "replayed": False,
    }


def _eligibility(row: dict[str, Any], reasons: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = bool(reasons) or row["status"] != "OPEN"
    if row["status"] != "OPEN":
        reasons = [
            {
                "code": "status",
                "count": 1,
                "label": f"estado {row['status']}",
            },
            *reasons,
        ]
    return {
        "outcome": "blocked" if blocked else "eligible",
        "competence_id": str(row["competence_id"]),
        "period": str(row["period"]).strip(),
        "status": row["status"],
        "reasons": reasons,
    }


def _deletion_reasons(cur, row: dict[str, Any]) -> list[dict[str, Any]]:
    references = _foreign_keys(cur)
    if not references or not any(
        item["table"] == "closing_audit_event" for item in references
    ):
        raise CompetenceDeleteUnavailable(
            "O catálogo de dependências da competência está indisponível.",
            details={"outcome": "unavailable"},
        )
    reasons: list[dict[str, Any]] = []
    competence_id = row["competence_id"]
    period = str(row["period"]).strip()
    for item in references:
        if item["table"] in HISTORICAL_TABLES:
            continue
        count = _count_rows(cur, item, competence_id)
        if count:
            reasons.append(
                {
                    "code": item["table"],
                    "count": count,
                    "label": DEPENDENCY_LABELS.get(
                        item["table"], f"registros em {item['table']}"
                    ),
                }
            )
    reasons.extend(_process_reasons(cur, period, str(competence_id)))
    return reasons


def _foreign_keys(cur) -> list[dict[str, str]]:
    cur.execute(
        """
        SELECT n.nspname AS schema_name,
               c.relname AS table_name,
               a.attname AS column_name
          FROM pg_constraint con
          JOIN pg_class c ON c.oid = con.conrelid
          JOIN pg_namespace n ON n.oid = c.relnamespace
          JOIN pg_attribute a
            ON a.attrelid = con.conrelid
           AND a.attnum = con.conkey[1]
           AND array_length(con.conkey, 1) = 1
         WHERE con.contype = 'f'
           AND con.confrelid = %s::regclass
         ORDER BY n.nspname, c.relname
        """,
        (f"{SCHEMA_NAME}.monthly_competence",),
    )
    found = []
    for item in cur.fetchall():
        if item["schema_name"] != SCHEMA_NAME:
            raise CompetenceDeleteUnavailable(
                "Há dependência fora do schema da Central de Fechamento.",
                details={"outcome": "unavailable"},
            )
        if not IDENT_RE.fullmatch(item["table_name"]) or not IDENT_RE.fullmatch(
            item["column_name"]
        ):
            raise CompetenceDeleteUnavailable(
                "O catálogo de dependências retornou um identificador inválido.",
                details={"outcome": "unavailable"},
            )
        found.append(
            {"table": item["table_name"], "column": item["column_name"]}
        )
    return found


def _count_rows(cur, item: dict[str, str], competence_id: Any) -> int:
    query = sql.SQL("SELECT count(*) AS n FROM {}.{} WHERE {} = %s").format(
        sql.Identifier(SCHEMA_NAME),
        sql.Identifier(item["table"]),
        sql.Identifier(item["column"]),
    )
    cur.execute(query, (competence_id,))
    return int(cur.fetchone()["n"])


def _process_reasons(
    cur, period: str, competence_id: str
) -> list[dict[str, Any]]:
    reasons = []
    cur.execute(
        f"""
        SELECT count(*) AS n
          FROM {SCHEMA_NAME}.clara_proposal
         WHERE consumed_at IS NULL
           AND execution_state IN ('PREPARED', 'CLAIMED')
           AND expires_at > now()
           AND NOT (
                capability = 'competence.delete'
            AND resource_key = %s
            AND payload->>'expected_competence_id' = %s
           )
           AND (
                resource_key = %s
             OR payload->>'period' = %s
             OR payload->>'competence_id' = %s
             OR payload->>'expected_competence_id' = %s
           )
        """,
        (period, competence_id, period, period, competence_id, competence_id),
    )
    proposals = int(cur.fetchone()["n"])
    if proposals:
        reasons.append(
            {
                "code": "clara_proposal",
                "count": proposals,
                "label": DEPENDENCY_LABELS["clara_proposal"],
            }
        )
    marker = f'"period": "{period}"'
    cur.execute(
        f"""
        SELECT count(*) AS n
          FROM {SCHEMA_NAME}.clara_batch
         WHERE status IN ('PREPARED', 'CONFIRMED', 'EXECUTING')
           AND expires_at > now()
           AND plan::text LIKE %s
        """,
        (f"%{marker}%",),
    )
    batches = int(cur.fetchone()["n"])
    if batches:
        reasons.append(
            {
                "code": "clara_batch",
                "count": batches,
                "label": DEPENDENCY_LABELS["clara_batch"],
            }
        )
    return reasons


def _lock_competence(cur, period: str, *, share: bool) -> dict[str, Any] | None:
    mode = "SHARE" if share else "UPDATE"
    cur.execute(
        f"""
        SELECT competence_id, period, status, template_version_id
          FROM {SCHEMA_NAME}.monthly_competence
         WHERE period = %s
           FOR {mode}
        """,
        (period,),
    )
    return cur.fetchone()


def _prior_deletion(cur, idempotency_key: str) -> dict[str, Any] | None:
    cur.execute(
        f"""
        SELECT event_id, created_at, detail
          FROM {SCHEMA_NAME}.closing_audit_event
         WHERE event_type = 'COMPETENCE_DELETED'
           AND detail->>'idempotency_key' = %s
         ORDER BY created_at DESC
         LIMIT 1
        """,
        (idempotency_key,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    detail = row["detail"] or {}
    competence_id = str(detail.get("competence_id") or "")
    period = str(detail.get("period") or "")
    if not competence_id or not period:
        raise CompetenceDeleteUnavailable(
            "A auditoria da exclusão anterior está incompleta.",
            details={"outcome": "unavailable"},
        )
    return {
        "event_id": str(row["event_id"]),
        "deleted_at": row["created_at"],
        "competence_id": competence_id,
        "period": period,
    }


def _success(prior: dict[str, Any], *, replayed: bool) -> dict[str, Any]:
    return {
        "competence_id": prior["competence_id"],
        "period": prior["period"],
        "deleted": True,
        "deleted_at": prior["deleted_at"],
        "audit_reference": prior["event_id"],
        "replayed": replayed,
    }


def _assert_absent(cur, period: str) -> None:
    cur.execute(
        f"""
        SELECT 1
          FROM {SCHEMA_NAME}.monthly_competence
         WHERE period = %s
        """,
        (period,),
    )
    if cur.fetchone() is not None:
        raise CompetenceDeleteUnavailable(
            "A competência ainda existe após a exclusão.",
            details={"outcome": "unavailable", "period": period},
        )


def _connection():
    if not plugins_db_configured():
        raise CompetenceDeleteUnavailable(
            "A persistência da Central de Fechamento não está configurada.",
            details={"outcome": "unavailable"},
        )
    try:
        return plugins_db_connect()
    except psycopg.Error as exc:
        raise CompetenceDeleteUnavailable(
            "A persistência da Central de Fechamento está indisponível.",
            details={"outcome": "unavailable"},
        ) from exc


def _period(value: str) -> str:
    text = str(value or "").strip()
    if not PERIOD_RE.fullmatch(text):
        raise CompetenceDeleteInvalid(
            "A competência deve estar no formato AAAA-MM.",
            details={"outcome": "invalid"},
        )
    return text


def _actor(value: str) -> str:
    return _uuid(value, "actor")


def _uuid(value: str, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError):
        raise CompetenceDeleteInvalid(
            "O identificador informado é inválido.",
            details={"outcome": "invalid", "field": field},
        ) from None


def _reason(value: str | None) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > 500:
        raise CompetenceDeleteInvalid(
            "O motivo da exclusão pode ter no máximo 500 caracteres.",
            details={"outcome": "invalid", "field": "reason"},
        )
    return text


def _idempotency_key(value: str) -> str:
    text = str(value or "").strip()
    if not KEY_RE.fullmatch(text):
        raise CompetenceDeleteInvalid(
            "A chave de idempotência é inválida.",
            details={"outcome": "invalid", "field": "idempotency_key"},
        )
    return text
