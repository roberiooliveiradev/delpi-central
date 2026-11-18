#!/usr/bin/env python3
"""Migração explícita de status v1 → v2 (FA-4/FA-5/FA-6, T18).

O agrupamento por causa muda a identidade da ocorrência: a chave v1
``branch|key44|rule_id|field|item`` vira ``branch|key44|cause:<cause_id>``
(ou ``branch|doc:...|cause:<cause_id>`` para notas sem chave). Cada linha
v1 de `entry_audit_status` é anotada com a chave v2 derivada e um status
consolidado é criado por (nota, causa):

- **conservador** — a causa migrada só fica ``resolved`` se TODAS as
  linhas v1 mapeadas para ela estavam ``resolved`` (FA-6);
- **idempotente** — o mapeamento é determinístico; o INSERT do
  consolidado usa `ON CONFLICT DO NOTHING`, então status alterados
  depois da migração nunca são sobrescritos numa reexecução;
- **aditivo** — linhas e eventos v1 não são apagados nem reescritos;
  a trilha recebe um evento ``ENTRY_AUDIT_STATUS_MIGRATED_V2`` por
  causa consolidada ligando a chave antiga à nova;
- **histórico preservado** — quem resolveu e quando acompanha a linha
  consolidada (linha v1 resolvida mais recente do grupo).

Uso (executar DENTRO do container da API, após V037):

    python scripts/migrate_entry_audit_status_v2.py plan          # dry-run
    python scripts/migrate_entry_audit_status_v2.py apply          # grava

Antes do `apply` em PROD: backup da tabela `entry_audit_status` e
ensaio em HML com cópia dos status de PROD (track T18, regra 4).
"""

from __future__ import annotations

import json
import sys
from uuid import uuid4

from psycopg.types.json import Json

from controllership_finance_app.application.entry_audit.vocabulary import (
    stable_key_v2_from_v1,
)
from controllership_finance_app.domain.entry_audit.causes import cause_id_for
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_connect,
)

SCHEMA = "controllership_finance"
MIGRATION_EVENT = "ENTRY_AUDIT_STATUS_MIGRATED_V2"
_MIGRATION_ACTOR = "00000000-0000-4000-8000-0000000000ea"


def _v2_key(stable_key: str) -> str | None:
    return stable_key_v2_from_v1(stable_key, cause_id_for)


def _plan(conn) -> dict[str, dict]:
    rows = conn.execute(
        f"SELECT stable_key, kind, status, resolved_by_user_id, resolved_by_name, resolved_at"
        f"  FROM {SCHEMA}.entry_audit_status ORDER BY stable_key"
    ).fetchall()
    groups: dict[str, dict] = {}
    for row in rows:
        v2 = _v2_key(row["stable_key"])
        if v2 is None:
            continue
        group = groups.setdefault(
            v2,
            {
                "v2_key": v2,
                "kind": row["kind"],
                "from_keys": [],
                "all_resolved": True,
                "resolved_by_user_id": "",
                "resolved_by_name": "",
                "resolved_at": None,
            },
        )
        group["from_keys"].append(row["stable_key"])
        if row["status"] != "resolved":
            group["all_resolved"] = False
        elif group["resolved_at"] is None or (row["resolved_at"] and row["resolved_at"] > group["resolved_at"]):
            group["resolved_at"] = row["resolved_at"]
            group["resolved_by_user_id"] = row["resolved_by_user_id"]
            group["resolved_by_name"] = row["resolved_by_name"]
    return groups


def _apply(conn, groups: dict[str, dict]) -> tuple[int, int]:
    annotated = consolidated = 0
    for group in groups.values():
        for key in group["from_keys"]:
            cur = conn.execute(
                f"UPDATE {SCHEMA}.entry_audit_status SET stable_key_v2 = %s WHERE stable_key = %s",
                (group["v2_key"], key),
            )
            annotated += cur.rowcount
        status = "resolved" if group["all_resolved"] else "pending"
        cur = conn.execute(
            f"""
            INSERT INTO {SCHEMA}.entry_audit_status (
                stable_key, stable_key_v2, kind, status,
                resolved_by_user_id, resolved_by_name, resolved_at
            ) VALUES (%s, %s, 'occurrence', %s, %s, %s, %s)
            ON CONFLICT (stable_key) DO NOTHING
            """,
            (
                group["v2_key"],
                group["v2_key"],
                status,
                group["resolved_by_user_id"] if status == "resolved" else "",
                group["resolved_by_name"] if status == "resolved" else "",
                group["resolved_at"] if status == "resolved" else None,
            ),
        )
        consolidated += cur.rowcount
        if cur.rowcount:
            conn.execute(
                f"""
                INSERT INTO {SCHEMA}.closing_audit_event
                    (entity_type, entity_id, competence_id, event_type, actor_subject, detail)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    "entry_audit_status",
                    str(uuid4()),
                    None,
                    MIGRATION_EVENT,
                    _MIGRATION_ACTOR,
                    json.dumps(
                        {
                            "stable_key": group["v2_key"],
                            "from_keys": group["from_keys"],
                            "status": status,
                            "capability": "entry_audit_status_migrate_v2",
                            "channel": "migration",
                        }
                    ),
                ),
            )
    return annotated, consolidated


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if command not in {"plan", "apply"}:
        print(__doc__)
        return 2
    with plugins_db_connect() as conn:
        groups = _plan(conn)
        resolved = sum(1 for g in groups.values() if g["all_resolved"])
        print(
            json.dumps(
                {
                    "v2_groups": len(groups),
                    "v1_rows": sum(len(g["from_keys"]) for g in groups.values()),
                    "consolidated_resolved": resolved,
                    "consolidated_pending": len(groups) - resolved,
                },
                indent=2,
            )
        )
        if command == "plan":
            return 0
        annotated, consolidated = _apply(conn, groups)
        conn.commit()
        print(json.dumps({"annotated_v1": annotated, "inserted_v2": consolidated}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
