"""Exclusão administrativa de competência mensal (CF-UX-054).

Dois modos, mesma governança:

- **restrito (default)**: a competência só é removida quando a
  transação comprova a ausência de dependências operacionais;
- **governada com dependentes** (`delete_dependents`): dados
  operacionais exclusivos da competência — documentos, arquivos,
  mensagens, snapshot de checklist e estado operacional — são removidos
  na mesma transação, por deletes ordenados pelo grafo real de
  dependências (nunca `CASCADE` genérico). A confirmação exige o
  manifesto `expected_dependents` recomputado sob lock: divergência é
  conflito, nunca exclusão parcial silenciosa.

Bloqueios absolutos em qualquer modo: competência fora de `OPEN`,
artefatos oficiais de homologação (`closing_package`,
`closing_review_assignment`, `closing_terminal_rejection`), qualquer
tabela dependente desconhecida (fail-closed), propostas/lotes CLARA em
aberto e referências compartilhadas vindas de outras competências.

A auditoria de abertura não é apagada: a FK histórica usa
`ON DELETE SET NULL` (V021) e o evento `COMPETENCE_DELETED` guarda
período, identificador, motivo, manifesto removido e chave de
idempotência — sem copiar conteúdo sensível das linhas removidas.
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
    "document_version": "versões de documento",
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
    "shared_reference": "referências compartilhadas",
    "clara_proposal": "propostas CLARA pendentes",
    "clara_batch": "lotes CLARA pendentes",
}

# Dependências diretas de monthly_competence, classificadas:
# - EXCLUSIVE: dados operacionais que só existem por causa da
#   competência — removidos na exclusão governada confirmada.
# - BLOCKING: artefatos oficiais de homologação/entrega — bloqueiam
#   qualquer exclusão, mesmo governada.
# Tabela dependente desconhecida => BLOCKING (fail-closed: evolução de
# schema nunca vira cascade silencioso).
EXCLUSIVE_DEPENDENCIES = frozenset(
    {
        "competence_checklist_item",
        "closing_document",
        "document_message",
        "document_adjustment_request",
        "evidence_decision",
        "item_correction",
        "closing_pendency",
        "closing_cutoff",
        "closing_reconciliation",
        "closing_revalidation",
        "closing_stock_state",
        "closing_notification_event",
    }
)
BLOCKING_DEPENDENCIES = frozenset(
    {
        "closing_package",
        "closing_review_assignment",
        "closing_terminal_rejection",
    }
)

# Ordem determinada pelo grafo real de dependências (FK RESTRICT),
# folhas primeiro — nunca CASCADE genérico. document_version não tem
# coluna competence_id e é removida via documento; document_file é
# removida depois, só quando nenhuma versão restante a referencia.
COMPETENCE_SCOPED_DELETE_ORDER = (
    "document_adjustment_request",
    "document_message",
    "evidence_decision",
    "item_correction",
    "closing_pendency",
    "closing_revalidation",
    "closing_reconciliation",
    "closing_cutoff",
    "closing_stock_state",
    "closing_notification_event",
)


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
            inventory = _dependency_inventory(cur, row)
    return _eligibility(row, inventory)


def delete_competence(
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
    """Remove a competência exata ou reproduz a exclusão já concluída.

    `delete_dependents` exige `expected_dependents` igual ao manifesto
    exclusivo recomputado sob lock (diagnóstico prévio) — OCC sobre o
    conjunto de dependências, não apenas sobre a linha da competência.
    """
    normalized = _period(period)
    actor_id = _actor(actor)
    expected_id = _uuid(expected_competence_id, "expected_competence_id")
    clean_reason = _reason(reason)
    key = _idempotency_key(idempotency_key)
    manifest = _expected_dependents(expected_dependents)
    try:
        with _connection() as conn, conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                result = _delete_locked(
                    cur,
                    period=normalized,
                    actor=actor_id,
                    expected_id=expected_id,
                    reason=clean_reason,
                    idempotency_key=key,
                    channel=channel,
                    delete_dependents=delete_dependents,
                    expected_dependents=manifest,
                )
    except (
        CompetenceNotFound,
        CompetenceDeleteBlocked,
        CompetenceDeleteConflict,
        CompetenceDeleteUnavailable,
        CompetenceDeleteInvalid,
    ):
        raise
    except psycopg.errors.ForeignKeyViolation as exc:
        raise CompetenceDeleteBlocked(
            "Uma referência compartilhada impediu a exclusão governada.",
            details={
                "outcome": "blocked",
                "period": normalized,
                "reasons": [
                    {
                        "code": "shared_reference",
                        "count": 1,
                        "label": DEPENDENCY_LABELS["shared_reference"],
                    }
                ],
            },
        ) from exc
    except psycopg.Error as exc:
        raise CompetenceDeleteUnavailable(
            "Não foi possível confirmar as dependências da competência.",
            details={"outcome": "unavailable", "period": normalized},
        ) from exc
    storage_keys = result.pop("_storage_keys", None)
    if storage_keys:
        _remove_storage_objects(result, storage_keys)
    return result


def _delete_locked(
    cur,
    *,
    period: str,
    actor: str,
    expected_id: str,
    reason: str,
    idempotency_key: str,
    channel: str,
    delete_dependents: bool,
    expected_dependents: dict[str, int] | None,
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
    inventory = _dependency_inventory(cur, row)
    blocking = inventory["blocking"]
    if row["status"] != "OPEN":
        blocking = [
            {
                "code": "status",
                "count": 1,
                "label": f"estado {row['status']}",
            },
            *blocking,
        ]
    if blocking:
        raise CompetenceDeleteBlocked(
            "A competência tem dependências que impedem a exclusão.",
            details={
                "outcome": "blocked",
                "period": period,
                "competence_id": current_id,
                "reasons": blocking,
                "dependents": _dependents_detail(inventory),
            },
        )
    exclusive = inventory["exclusive"]
    if exclusive and not delete_dependents:
        raise CompetenceDeleteBlocked(
            "A competência tem dados vinculados — a exclusão governada "
            "exige confirmação explícita com o manifesto de impacto.",
            details={
                "outcome": "blocked",
                "period": period,
                "competence_id": current_id,
                "reasons": _manifest_entries(exclusive),
                "dependents": _dependents_detail(inventory),
                "confirmation": "delete_dependents+expected_dependents",
            },
        )
    if exclusive:
        if expected_dependents is None:
            raise CompetenceDeleteInvalid(
                "A exclusão com dependentes exige o manifesto "
                "expected_dependents do diagnóstico.",
                details={"outcome": "invalid", "field": "expected_dependents"},
            )
    if expected_dependents is not None and expected_dependents != exclusive:
        raise CompetenceDeleteConflict(
            "O manifesto de dependências diverge do estado atual — "
            "refaça o diagnóstico antes de confirmar.",
            details={
                "outcome": "conflict",
                "period": period,
                "expected": expected_dependents,
                "actual": exclusive,
            },
        )
    storage_keys = []
    if exclusive:
        storage_keys = _delete_exclusive_dependents(
            cur, row["competence_id"], inventory
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
    if exclusive:
        detail["dependents"] = exclusive
        detail["dependents_confirmed"] = True
    if storage_keys:
        detail["storage_objects"] = len(storage_keys)
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
    if exclusive:
        _assert_no_dependent_rows(cur, row["competence_id"])
    return {
        "competence_id": current_id,
        "period": period,
        "deleted": True,
        "deleted_at": audit["created_at"],
        "audit_reference": str(audit["event_id"]),
        "replayed": False,
        "dependents": exclusive or None,
        "_storage_keys": storage_keys,
    }


def _eligibility(
    row: dict[str, Any], inventory: dict[str, Any]
) -> dict[str, Any]:
    blocking = inventory["blocking"]
    if row["status"] != "OPEN":
        blocking = [
            {
                "code": "status",
                "count": 1,
                "label": f"estado {row['status']}",
            },
            *blocking,
        ]
    if blocking:
        outcome = "blocked"
    elif inventory["exclusive"]:
        outcome = "eligible_with_dependents"
    else:
        outcome = "eligible"
    return {
        "outcome": outcome,
        "competence_id": str(row["competence_id"]),
        "period": str(row["period"]).strip(),
        "status": row["status"],
        "reasons": blocking,
        "dependents": _dependents_detail(inventory),
    }


def _dependents_detail(inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "exclusive": _manifest_entries(inventory["exclusive"]),
        "shared_files": inventory["shared_files"],
    }


_MANIFEST_ORDER = {
    code: index
    for index, code in enumerate(
        (
            "competence_checklist_item",
            "closing_document",
            "document_version",
            "document_file",
            "document_message",
            "document_adjustment_request",
            "evidence_decision",
            "item_correction",
            "closing_pendency",
            "closing_cutoff",
            "closing_reconciliation",
            "closing_revalidation",
            "closing_stock_state",
            "closing_notification_event",
        )
    )
}


def _manifest_entries(exclusive: dict[str, int]) -> list[dict[str, Any]]:
    ordered = sorted(
        exclusive,
        key=lambda code: (_MANIFEST_ORDER.get(code, 99), code),
    )
    return [
        {
            "code": code,
            "count": exclusive[code],
            "label": DEPENDENCY_LABELS.get(code, f"registros em {code}"),
        }
        for code in ordered
    ]


def _dependency_inventory(
    cur, row: dict[str, Any]
) -> dict[str, Any]:
    """Inventário classificado das dependências da competência.

    `exclusive`: contagens por tabela — manifesto completo da remoção
    governada (inclui subárvore documental). `blocking`: razões que
    impedem qualquer exclusão. `shared_files`: arquivos também
    referenciados por outros documentos — preservados, nunca removidos.
    """
    references = _foreign_keys(cur)
    if not references or not any(
        item["table"] == "closing_audit_event" for item in references
    ):
        raise CompetenceDeleteUnavailable(
            "O catálogo de dependências da competência está indisponível.",
            details={"outcome": "unavailable"},
        )
    competence_id = row["competence_id"]
    period = str(row["period"]).strip()
    exclusive: dict[str, int] = {}
    blocking: list[dict[str, Any]] = []
    for item in references:
        table = item["table"]
        if table in HISTORICAL_TABLES:
            continue
        count = _count_rows(cur, item, competence_id)
        if not count:
            continue
        if table in EXCLUSIVE_DEPENDENCIES:
            exclusive[table] = count
        else:
            blocking.append(
                {
                    "code": table,
                    "count": count,
                    "label": DEPENDENCY_LABELS.get(
                        table, f"registros em {table}"
                    ),
                }
            )
    documents = _competence_document_ids(cur, competence_id)
    if documents:
        versions = _count_in(
            cur, "document_version", "document_id", documents
        )
        if versions:
            exclusive["document_version"] = versions
        owned, shared = _document_file_split(cur, competence_id, documents)
        if owned:
            exclusive["document_file"] = owned
    else:
        shared = 0
    blocking.extend(
        _shared_reference_reasons(cur, competence_id, documents)
    )
    blocking.extend(_process_reasons(cur, period, str(competence_id)))
    return {
        "exclusive": exclusive,
        "blocking": blocking,
        "shared_files": shared,
        "documents": documents,
    }


def _competence_document_ids(cur, competence_id: Any) -> list[str]:
    cur.execute(
        f"""
        SELECT document_id
          FROM {SCHEMA_NAME}.closing_document
         WHERE competence_id = %s
         ORDER BY document_id
        """,
        (competence_id,),
    )
    return [str(row["document_id"]) for row in cur.fetchall()]


def _count_in(cur, table: str, column: str, ids: list[str]) -> int:
    if not ids:
        return 0
    query = sql.SQL("SELECT count(*) AS n FROM {}.{} WHERE {} = ANY(%s)").format(
        sql.Identifier(SCHEMA_NAME),
        sql.Identifier(table),
        sql.Identifier(column),
    )
    cur.execute(query, (ids,))
    return int(cur.fetchone()["n"])


def _document_file_split(
    cur, competence_id: Any, documents: list[str]
) -> tuple[int, int]:
    """Arquivos do documento: exclusivos da competência × compartilhados."""
    cur.execute(
        f"""
        SELECT count(*) AS n
          FROM {SCHEMA_NAME}.document_file f
         WHERE f.file_id IN (
                SELECT dv.file_id
                  FROM {SCHEMA_NAME}.document_version dv
                 WHERE dv.document_id = ANY(%s)
               )
           AND NOT EXISTS (
                SELECT 1
                  FROM {SCHEMA_NAME}.document_version other
                 WHERE other.file_id = f.file_id
                   AND other.document_id <> ALL(%s)
               )
        """,
        (documents, documents),
    )
    owned = int(cur.fetchone()["n"])
    cur.execute(
        f"""
        SELECT count(DISTINCT dv.file_id) AS n
          FROM {SCHEMA_NAME}.document_version dv
         WHERE dv.document_id = ANY(%s)
        """,
        (documents,),
    )
    total = int(cur.fetchone()["n"])
    return owned, total - owned


def _shared_reference_reasons(
    cur, competence_id: Any, documents: list[str]
) -> list[dict[str, Any]]:
    """Referências de OUTRAS competências a dados desta — bloqueio."""
    reasons: list[dict[str, Any]] = []
    checks = []
    if documents:
        checks.extend(
            [
                (
                    "closing_reconciliation",
                    "official_document_id",
                    "document_id",
                    documents,
                    "conciliações de outra competência usam estes documentos",
                ),
                (
                    "evidence_decision",
                    "document_id",
                    "document_id",
                    documents,
                    "decisões de outra competência usam estes documentos",
                ),
                (
                    "document_message",
                    "document_id",
                    "document_id",
                    documents,
                    "mensagens de outra competência usam estes documentos",
                ),
                (
                    "document_adjustment_request",
                    "document_id",
                    "document_id",
                    documents,
                    "solicitações de outra competência usam estes documentos",
                ),
            ]
        )
    checks.append(
        (
            "evidence_decision",
            "snapshot_item_id",
            "snapshot_item_id",
            None,
            "decisões de outra competência usam estes itens",
        )
    )
    checks.append(
        (
            "item_correction",
            "snapshot_item_id",
            "snapshot_item_id",
            None,
            "correções de outra competência usam estes itens",
        )
    )
    checks.append(
        (
            "closing_pendency",
            "snapshot_item_id",
            "snapshot_item_id",
            None,
            "pendências de outra competência usam estes itens",
        )
    )
    checks.append(
        (
            "evidence_decision",
            "reverses_decision_id",
            "decision_id",
            None,
            "decisões de outra competência revertem estas decisões",
        )
    )
    checks.append(
        (
            "evidence_decision",
            "document_version_id",
            "document_version_id",
            "versions",
            "decisões de outra competência usam estas versões",
        )
    )
    for table, column, parent_column, scope, label in checks:
        if scope is None:
            parent_table = (
                "evidence_decision"
                if parent_column == "decision_id"
                else "competence_checklist_item"
            )
            subquery = sql.SQL(
                "SELECT {} FROM {}.{} WHERE competence_id = %s"
            ).format(
                sql.Identifier(parent_column),
                sql.Identifier(SCHEMA_NAME),
                sql.Identifier(parent_table),
            )
            params: tuple[Any, ...] = (competence_id,)
        elif scope == "versions":
            subquery = sql.SQL(
                "SELECT dv.document_version_id"
                " FROM {}.document_version dv"
                " WHERE dv.document_id = ANY(%s)"
            ).format(sql.Identifier(SCHEMA_NAME))
            params = (documents,)
        else:
            subquery = sql.SQL(
                "SELECT {} FROM {}.closing_document WHERE competence_id = %s"
            ).format(
                sql.Identifier(parent_column),
                sql.Identifier(SCHEMA_NAME),
            )
            params = (competence_id,)
        query = sql.SQL(
            "SELECT count(*) AS n FROM {}.{}"
            " WHERE {} IN ({}) AND competence_id <> %s"
        ).format(
            sql.Identifier(SCHEMA_NAME),
            sql.Identifier(table),
            sql.Identifier(column),
            subquery,
        )
        cur.execute(query, (*params, competence_id))
        count = int(cur.fetchone()["n"])
        if count:
            reasons.append(
                {
                    "code": "shared_reference",
                    "count": count,
                    "label": label,
                }
            )
    return reasons


def _delete_exclusive_dependents(
    cur, competence_id: Any, inventory: dict[str, Any]
) -> list[str]:
    """Remove os dados exclusivos na ordem do grafo real de FKs.

    Retorna as `storage_key` dos arquivos físicos a remover após o
    commit — o par binário↔metadado é indissociável e a remoção do
    objeto não é transacional.
    """
    exclusive = inventory["exclusive"]
    for table in COMPETENCE_SCOPED_DELETE_ORDER:
        if not exclusive.get(table):
            continue
        cur.execute(
            f"DELETE FROM {SCHEMA_NAME}.{table} WHERE competence_id = %s",
            (competence_id,),
        )
        if cur.rowcount != exclusive[table]:
            raise CompetenceDeleteUnavailable(
                "A remoção governada divergiu do manifesto confirmado.",
                details={"outcome": "unavailable", "table": table},
            )
    documents = inventory["documents"]
    if documents:
        cur.execute(
            f"""
            SELECT DISTINCT dv.file_id
              FROM {SCHEMA_NAME}.document_version dv
             WHERE dv.document_id = ANY(%s)
             ORDER BY dv.file_id
            """,
            (documents,),
        )
        candidate_files = [str(row["file_id"]) for row in cur.fetchall()]
        if exclusive.get("document_version"):
            cur.execute(
                f"""
                DELETE FROM {SCHEMA_NAME}.document_version
                 WHERE document_id = ANY(%s)
                """,
                (documents,),
            )
            if cur.rowcount != exclusive["document_version"]:
                raise CompetenceDeleteUnavailable(
                    "A remoção governada divergiu do manifesto confirmado.",
                    details={
                        "outcome": "unavailable",
                        "table": "document_version",
                    },
                )
        storage_keys: list[str] = []
        if exclusive.get("document_file") and candidate_files:
            cur.execute(
                f"""
                DELETE FROM {SCHEMA_NAME}.document_file f
                 WHERE f.file_id = ANY(%s)
                   AND NOT EXISTS (
                        SELECT 1
                          FROM {SCHEMA_NAME}.document_version other
                         WHERE other.file_id = f.file_id
                       )
                RETURNING f.file_id, f.storage_key
                """,
                (candidate_files,),
            )
            file_rows = cur.fetchall()
            storage_keys = [row["storage_key"] for row in file_rows]
            if len(file_rows) != exclusive["document_file"]:
                raise CompetenceDeleteUnavailable(
                    "A remoção governada divergiu do manifesto confirmado.",
                    details={
                        "outcome": "unavailable",
                        "table": "document_file",
                    },
                )
        cur.execute(
            f"""
            DELETE FROM {SCHEMA_NAME}.closing_document
             WHERE competence_id = %s
            """,
            (competence_id,),
        )
        if cur.rowcount != exclusive["closing_document"]:
            raise CompetenceDeleteUnavailable(
                "A remoção governada divergiu do manifesto confirmado.",
                details={
                    "outcome": "unavailable",
                    "table": "closing_document",
                },
            )
    else:
        storage_keys = []
    if exclusive.get("competence_checklist_item"):
        cur.execute(
            f"""
            DELETE FROM {SCHEMA_NAME}.competence_checklist_item
             WHERE competence_id = %s
            """,
            (competence_id,),
        )
        if cur.rowcount != exclusive["competence_checklist_item"]:
            raise CompetenceDeleteUnavailable(
                "A remoção governada divergiu do manifesto confirmado.",
                details={
                    "outcome": "unavailable",
                    "table": "competence_checklist_item",
                },
            )
    return storage_keys


def _assert_no_dependent_rows(cur, competence_id: Any) -> None:
    tables = (
        *COMPETENCE_SCOPED_DELETE_ORDER,
        "closing_document",
        "competence_checklist_item",
    )
    for table in tables:
        cur.execute(
            f"SELECT 1 FROM {SCHEMA_NAME}.{table}"
            " WHERE competence_id = %s LIMIT 1",
            (competence_id,),
        )
        if cur.fetchone() is not None:
            raise CompetenceDeleteUnavailable(
                "Restaram dados vinculados após a exclusão governada.",
                details={"outcome": "unavailable", "table": table},
            )


def _remove_storage_objects(
    result: dict[str, Any], storage_keys: list[str]
) -> None:
    """Remove os binários após o commit — falha vira housekeeping
    identificável (metadado já removido), nunca sucesso falso."""
    removed = 0
    orphaned: list[str] = []
    try:
        from controllership_finance_app.infrastructure.storage.closing_document_storage import (
            ClosingDocumentStorage,
        )

        storage = ClosingDocumentStorage()
        for key in storage_keys:
            if storage.remove(key):
                removed += 1
            else:
                orphaned.append(key)
    except Exception:  # storage indisponível — metadados já consistentes
        orphaned = list(storage_keys)
    if orphaned:
        import logging

        logging.getLogger(__name__).warning(
            "competence_delete_storage_orphans count=%d", len(orphaned)
        )
    result["storage_objects_removed"] = removed
    result["storage_objects_orphaned"] = len(orphaned)


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
        "dependents": detail.get("dependents") or None,
    }


def _success(prior: dict[str, Any], *, replayed: bool) -> dict[str, Any]:
    return {
        "competence_id": prior["competence_id"],
        "period": prior["period"],
        "deleted": True,
        "deleted_at": prior["deleted_at"],
        "audit_reference": prior["event_id"],
        "replayed": replayed,
        "dependents": prior["dependents"],
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


def _expected_dependents(
    value: dict[str, int] | None,
) -> dict[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or not value:
        raise CompetenceDeleteInvalid(
            "O manifesto de dependentes deve ser um objeto não vazio.",
            details={"outcome": "invalid", "field": "expected_dependents"},
        )
    manifest: dict[str, int] = {}
    for code, count in value.items():
        if not IDENT_RE.fullmatch(str(code)) or not isinstance(
            count, int
        ) or isinstance(count, bool):
            raise CompetenceDeleteInvalid(
                "O manifesto de dependentes está fora do contrato.",
                details={
                    "outcome": "invalid",
                    "field": "expected_dependents",
                },
            )
        if count < 1:
            raise CompetenceDeleteInvalid(
                "O manifesto de dependentes só admite contagens positivas.",
                details={
                    "outcome": "invalid",
                    "field": "expected_dependents",
                },
            )
        manifest[str(code)] = count
    return manifest
