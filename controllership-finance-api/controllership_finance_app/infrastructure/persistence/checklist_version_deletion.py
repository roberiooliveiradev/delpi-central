"""Exclusão definitiva de versão de checklist (CF-UX-054-R3).

Escopo deliberadamente diferente da exclusão de competência: remove a
configuração documental (versão + itens) e **nunca** dados operacionais
— competências, snapshots, documentos e pacotes são preservados e, por
isso, **bloqueiam** a operação enquanto referenciarem a versão.

Elegível em qualquer estado (`DRAFT`, `REVIEW`, `PUBLISHED`,
`INACTIVE`) quando nenhuma referência operacional existir:

- `monthly_competence.template_version_id` (FK RESTRICT) => BLOCKING;
- `competence_checklist_item.source_version_id` (proveniência congelada
  do snapshot, sem FK) => BLOCKING;
- `checklist_template_item` => dependência exclusiva, removida junto;
- qualquer outra tabela com FK para a versão => BLOCKING (fail-closed:
  evolução de schema nunca vira cascade silencioso).

A confirmação exige `expected_version_id` + `expected_revision` +
`expected_item_count` recomputados sob lock (OCC do conjunto) —
divergência é conflito, nunca exclusão parcial silenciosa. A auditoria
append-only permanece: o evento `VERSION_DELETED` guarda template,
versão, revisão, contagem de itens, motivo e chave de idempotência —
sem copiar conteúdo das linhas removidas.
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
    VersionDeleteBlocked,
    VersionDeleteConflict,
    VersionDeleteInvalid,
    VersionDeleteUnavailable,
    VersionNotFound,
    TemplateNotFound,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")

DEPENDENCY_LABELS = {
    "checklist_template_item": "itens do checklist",
    "monthly_competence": "competências vinculadas",
    "snapshot_reference": "snapshots de competências",
}

# FK para checklist_template_version: itens são conteúdo exclusivo;
# competência é vínculo operacional impeditivo; qualquer tabela
# dependente desconhecida => BLOCKING (fail-closed).
EXCLUSIVE_DEPENDENCIES = frozenset({"checklist_template_item"})


def diagnose_template_version_deletion(
    template_id: str, version: int
) -> dict[str, Any]:
    """Diagnóstico somente leitura. Indisponibilidade não vira zero."""
    tid = _uuid(template_id, "template_id")
    ver = _version(version)
    with _connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        row = _version_row(cur, tid, ver, mode="SHARE")
        if row is None:
            raise VersionNotFound("Versão de checklist não encontrada.")
        inventory = _dependency_inventory(cur, row)
    return _eligibility(row, inventory)


def delete_template_version(
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
    """Remove a versão e seus itens ou reproduz a exclusão concluída.

    `expected_*` formam o manifesto OCC recomputado sob lock —
    divergência de identidade, revisão ou contagem de itens é
    `version_delete_conflict`, nunca remoção parcial.
    """
    tid = _uuid(template_id, "template_id")
    ver = _version(version)
    actor_id = _uuid(actor, "actor")
    expected_id = _uuid(expected_version_id, "expected_version_id")
    revision = _positive_int(expected_revision, "expected_revision")
    item_count = _non_negative_int(
        expected_item_count, "expected_item_count"
    )
    clean_reason = _reason(reason)
    key = _idempotency_key(idempotency_key)
    try:
        with _connection() as conn, conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                return _delete_locked(
                    cur,
                    template_id=tid,
                    version=ver,
                    actor=actor_id,
                    expected_version_id=expected_id,
                    expected_revision=revision,
                    expected_item_count=item_count,
                    reason=clean_reason,
                    idempotency_key=key,
                    channel=channel,
                )
    except (
        TemplateNotFound,
        VersionNotFound,
        VersionDeleteBlocked,
        VersionDeleteConflict,
        VersionDeleteUnavailable,
        VersionDeleteInvalid,
    ):
        raise
    except psycopg.errors.ForeignKeyViolation as exc:
        raise VersionDeleteBlocked(
            "Uma referência operacional impediu a exclusão da versão.",
            details={
                "outcome": "blocked",
                "reasons": [
                    {
                        "code": "unknown_reference",
                        "count": 1,
                        "label": "referência operacional não mapeada",
                    }
                ],
            },
        ) from exc
    except psycopg.Error as exc:
        raise VersionDeleteUnavailable(
            "Não foi possível confirmar as dependências da versão.",
            details={"outcome": "unavailable"},
        ) from exc


def _delete_locked(
    cur,
    *,
    template_id: str,
    version: int,
    actor: str,
    expected_version_id: str,
    expected_revision: int,
    expected_item_count: int,
    reason: str,
    idempotency_key: str,
    channel: str,
) -> dict[str, Any]:
    cur.execute(
        f"""
        SELECT template_id FROM {SCHEMA_NAME}.checklist_template
         WHERE template_id = %s FOR UPDATE
        """,
        (template_id,),
    )
    if cur.fetchone() is None:
        raise TemplateNotFound("Template de checklist não encontrado.")
    prior = _prior_deletion(cur, template_id, idempotency_key)
    if prior is not None and prior["version_id"] != expected_version_id:
        raise VersionDeleteConflict(
            "A chave de idempotência já foi usada em outra exclusão.",
            details={"outcome": "conflict"},
        )
    row = _version_row(cur, template_id, version, mode="UPDATE")
    if row is None:
        if prior is not None:
            return _success(prior, replayed=True)
        raise VersionNotFound("Versão de checklist não encontrada.")
    current_id = str(row["version_id"])
    if prior is not None:
        return _success(prior, replayed=True)
    if current_id != expected_version_id:
        raise VersionDeleteConflict(
            "A versão informada diverge do recurso endereçado — refaça "
            "o diagnóstico antes de confirmar.",
            details={
                "outcome": "conflict",
                "expected": expected_version_id,
                "actual": current_id,
            },
        )
    inventory = _dependency_inventory(cur, row)
    if inventory["blocking"]:
        raise VersionDeleteBlocked(
            "A versão tem vínculos que impedem a exclusão definitiva.",
            details={
                "outcome": "blocked",
                "version_id": current_id,
                "version": version,
                "reasons": inventory["blocking"],
                "dependents": _dependents_detail(inventory),
            },
        )
    actual_count = inventory["exclusive"].get(
        "checklist_template_item", 0
    )
    if (
        row["revision"] != expected_revision
        or actual_count != expected_item_count
    ):
        raise VersionDeleteConflict(
            "O manifesto da versão diverge do estado atual — refaça o "
            "diagnóstico antes de confirmar.",
            details={
                "outcome": "conflict",
                "expected": {
                    "revision": expected_revision,
                    "checklist_template_item": expected_item_count,
                },
                "actual": {
                    "revision": row["revision"],
                    "checklist_template_item": actual_count,
                },
            },
        )
    if actual_count:
        cur.execute(
            f"DELETE FROM {SCHEMA_NAME}.checklist_template_item"
            " WHERE version_id = %s",
            (current_id,),
        )
        if cur.rowcount != actual_count:
            raise VersionDeleteUnavailable(
                "A remoção governada divergiu do manifesto confirmado.",
                details={
                    "outcome": "unavailable",
                    "table": "checklist_template_item",
                },
            )
    cur.execute(
        f"""
        DELETE FROM {SCHEMA_NAME}.checklist_template_version
         WHERE template_id = %s AND version = %s AND revision = %s
        """,
        (template_id, version, expected_revision),
    )
    if cur.rowcount == 0:
        raise VersionDeleteUnavailable(
            "A remoção governada divergiu do manifesto confirmado.",
            details={
                "outcome": "unavailable",
                "table": "checklist_template_version",
            },
        )
    deleted_at = datetime.now(timezone.utc)
    detail = {
        "template_id": template_id,
        "version": version,
        "version_id": current_id,
        "status": row["status"],
        "revision": expected_revision,
        "checklist_template_item": actual_count,
        "reason": reason or None,
        "idempotency_key": idempotency_key,
        "channel": channel,
        "deleted_at": deleted_at.isoformat(),
    }
    cur.execute(
        f"""
        INSERT INTO {SCHEMA_NAME}.closing_audit_event
            (entity_type, entity_id, competence_id, event_type,
             actor_subject, detail)
        VALUES ('checklist_template_version', %s, NULL,
                'VERSION_DELETED', %s, %s::jsonb)
        RETURNING event_id, created_at
        """,
        (current_id, actor, json.dumps(detail)),
    )
    audit = cur.fetchone()
    if audit is None:
        raise VersionDeleteUnavailable(
            "A auditoria da exclusão não pôde ser registrada.",
            details={"outcome": "unavailable"},
        )
    _assert_absent(cur, template_id, version)
    return {
        "version_id": current_id,
        "template_id": template_id,
        "version": version,
        "status": row["status"],
        "deleted": True,
        "deleted_at": audit["created_at"],
        "audit_reference": str(audit["event_id"]),
        "replayed": False,
        "dependents": (
            {"checklist_template_item": actual_count}
            if actual_count
            else None
        ),
    }


def _eligibility(
    row: dict[str, Any], inventory: dict[str, Any]
) -> dict[str, Any]:
    blocking = inventory["blocking"]
    exclusive = inventory["exclusive"]
    return {
        "outcome": "blocked" if blocking else "eligible",
        "template_id": str(row["template_id"]),
        "version_id": str(row["version_id"]),
        "version": row["version"],
        "status": row["status"],
        "revision": row["revision"],
        "item_count": exclusive.get("checklist_template_item", 0),
        "reasons": blocking,
        "dependents": _dependents_detail(inventory),
    }


def _dependents_detail(inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "exclusive": [
            {
                "code": code,
                "count": count,
                "label": DEPENDENCY_LABELS.get(
                    code, f"registros em {code}"
                ),
            }
            for code, count in sorted(inventory["exclusive"].items())
        ],
    }


def _dependency_inventory(
    cur, row: dict[str, Any]
) -> dict[str, Any]:
    """Inventário classificado das referências à versão.

    `exclusive`: filhos removidos junto (itens). `blocking`: vínculos
    operacionais impeditivos — competências (FK), snapshots
    (proveniência sem FK) e qualquer tabela dependente desconhecida.
    """
    references = _foreign_keys(cur)
    if not references or not any(
        item["table"] == "checklist_template_item" for item in references
    ):
        raise VersionDeleteUnavailable(
            "O catálogo de dependências da versão está indisponível.",
            details={"outcome": "unavailable"},
        )
    version_id = row["version_id"]
    exclusive: dict[str, int] = {}
    blocking: list[dict[str, Any]] = []
    for item in references:
        table = item["table"]
        count = _count_rows(cur, item, version_id)
        if not count:
            continue
        if table in EXCLUSIVE_DEPENDENCIES:
            exclusive[table] = count
        else:
            entry: dict[str, Any] = {
                "code": table,
                "count": count,
                "label": DEPENDENCY_LABELS.get(
                    table, f"registros em {table}"
                ),
            }
            if table == "monthly_competence":
                entry["periods"] = _referencing_periods(cur, version_id)
            blocking.append(entry)
    snapshot_refs = _snapshot_references(cur, version_id)
    if snapshot_refs["count"]:
        blocking.append(
            {
                "code": "snapshot_reference",
                "count": snapshot_refs["count"],
                "label": DEPENDENCY_LABELS["snapshot_reference"],
                "periods": snapshot_refs["periods"],
            }
        )
    return {"exclusive": exclusive, "blocking": blocking}


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
        (f"{SCHEMA_NAME}.checklist_template_version",),
    )
    found = []
    for item in cur.fetchall():
        if item["schema_name"] != SCHEMA_NAME:
            raise VersionDeleteUnavailable(
                "Há dependência fora do schema da Central de Fechamento.",
                details={"outcome": "unavailable"},
            )
        if not IDENT_RE.fullmatch(item["table_name"]) or not IDENT_RE.fullmatch(
            item["column_name"]
        ):
            raise VersionDeleteUnavailable(
                "O catálogo de dependências retornou um identificador inválido.",
                details={"outcome": "unavailable"},
            )
        found.append(
            {"table": item["table_name"], "column": item["column_name"]}
        )
    return found


def _count_rows(cur, reference: dict[str, str], version_id: Any) -> int:
    query = sql.SQL("SELECT count(*) AS n FROM {}.{} WHERE {} = %s").format(
        sql.Identifier(SCHEMA_NAME),
        sql.Identifier(reference["table"]),
        sql.Identifier(reference["column"]),
    )
    cur.execute(query, (version_id,))
    return int(cur.fetchone()["n"])


def _referencing_periods(cur, version_id: Any) -> list[str]:
    cur.execute(
        f"""
        SELECT period FROM {SCHEMA_NAME}.monthly_competence
         WHERE template_version_id = %s
         ORDER BY period
        """,
        (version_id,),
    )
    return [str(row["period"]).strip() for row in cur.fetchall()]


def _snapshot_references(cur, version_id: Any) -> dict[str, Any]:
    """Snapshots congelados que citam a versão como proveniência —
    referência real sem FK (V001 mantém `source_version_id` solto)."""
    cur.execute(
        f"""
        SELECT i.competence_id, count(*) AS n
          FROM {SCHEMA_NAME}.competence_checklist_item i
         WHERE i.source_version_id = %s
         GROUP BY i.competence_id
        """,
        (version_id,),
    )
    rows = cur.fetchall()
    if not rows:
        return {"count": 0, "periods": []}
    competence_ids = [str(row["competence_id"]) for row in rows]
    cur.execute(
        f"""
        SELECT period FROM {SCHEMA_NAME}.monthly_competence
         WHERE competence_id = ANY(%s)
         ORDER BY period
        """,
        (competence_ids,),
    )
    return {
        "count": int(sum(row["n"] for row in rows)),
        "periods": [str(row["period"]).strip() for row in cur.fetchall()],
    }


def _version_row(
    cur, template_id: str, version: int, *, mode: str
) -> dict[str, Any] | None:
    cur.execute(
        f"""
        SELECT version_id, template_id, version, status, revision,
               effective_from_period
          FROM {SCHEMA_NAME}.checklist_template_version
         WHERE template_id = %s AND version = %s
           FOR {mode}
        """,
        (template_id, version),
    )
    return cur.fetchone()


def _prior_deletion(
    cur, template_id: str, idempotency_key: str
) -> dict[str, Any] | None:
    cur.execute(
        f"""
        SELECT event_id, created_at, detail
          FROM {SCHEMA_NAME}.closing_audit_event
         WHERE event_type = 'VERSION_DELETED'
           AND detail->>'idempotency_key' = %s
           AND detail->>'template_id' = %s
         ORDER BY created_at DESC
         LIMIT 1
        """,
        (idempotency_key, template_id),
    )
    row = cur.fetchone()
    if row is None:
        return None
    detail = row["detail"] or {}
    version_id = str(detail.get("version_id") or "")
    if not version_id or detail.get("version") is None:
        raise VersionDeleteUnavailable(
            "A auditoria da exclusão anterior está incompleta.",
            details={"outcome": "unavailable"},
        )
    return {
        "event_id": str(row["event_id"]),
        "deleted_at": row["created_at"],
        "version_id": version_id,
        "version": int(detail["version"]),
        "status": detail.get("status"),
        "dependents": (
            {"checklist_template_item": detail["checklist_template_item"]}
            if detail.get("checklist_template_item")
            else None
        ),
    }


def _success(prior: dict[str, Any], *, replayed: bool) -> dict[str, Any]:
    return {
        "version_id": prior["version_id"],
        "version": prior["version"],
        "status": prior["status"],
        "deleted": True,
        "deleted_at": prior["deleted_at"],
        "audit_reference": prior["event_id"],
        "replayed": replayed,
        "dependents": prior["dependents"],
    }


def _assert_absent(cur, template_id: str, version: int) -> None:
    cur.execute(
        f"""
        SELECT 1
          FROM {SCHEMA_NAME}.checklist_template_version
         WHERE template_id = %s AND version = %s
        """,
        (template_id, version),
    )
    if cur.fetchone() is not None:
        raise VersionDeleteUnavailable(
            "A versão ainda existe após a exclusão.",
            details={"outcome": "unavailable"},
        )


def _connection():
    if not plugins_db_configured():
        raise VersionDeleteUnavailable(
            "A persistência da Central de Fechamento não está configurada.",
            details={"outcome": "unavailable"},
        )
    try:
        return plugins_db_connect()
    except psycopg.Error as exc:
        raise VersionDeleteUnavailable(
            "A persistência da Central de Fechamento está indisponível.",
            details={"outcome": "unavailable"},
        ) from exc


def _uuid(value: str, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError):
        raise VersionDeleteInvalid(
            "O identificador informado é inválido.",
            details={"outcome": "invalid", "field": field},
        ) from None


def _version(value: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise VersionDeleteInvalid(
            "O número da versão é inválido.",
            details={"outcome": "invalid", "field": "version"},
        ) from None
    if number < 1:
        raise VersionDeleteInvalid(
            "O número da versão é inválido.",
            details={"outcome": "invalid", "field": "version"},
        )
    return number


def _positive_int(value: int, field: str) -> int:
    return _bounded_int(value, field, minimum=1)


def _non_negative_int(value: int, field: str) -> int:
    return _bounded_int(value, field, minimum=0)


def _bounded_int(value: int, field: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        try:
            value = int(str(value))
        except (TypeError, ValueError):
            raise VersionDeleteInvalid(
                "O manifesto da versão está fora do contrato.",
                details={"outcome": "invalid", "field": field},
            ) from None
    if value < minimum:
        raise VersionDeleteInvalid(
            "O manifesto da versão está fora do contrato.",
            details={"outcome": "invalid", "field": field},
        )
    return value


def _reason(value: str | None) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > 500:
        raise VersionDeleteInvalid(
            "O motivo da exclusão pode ter no máximo 500 caracteres.",
            details={"outcome": "invalid", "field": "reason"},
        )
    return text


def _idempotency_key(value: str) -> str:
    text = str(value or "").strip()
    if not KEY_RE.fullmatch(text):
        raise VersionDeleteInvalid(
            "A chave de idempotência é inválida.",
            details={"outcome": "invalid", "field": "idempotency_key"},
        )
    return text
