#!/usr/bin/env python3
"""Inventário, backup e verificação do escopo de saneamento de competências.

Gate B — fase prévia à exclusão governada de `2026-09` e `2026-10`.

Uso (dentro do container da API ou com PLUGINS_DB_* apontando ao banco):

    python scripts/competence_inventory_backup.py inventory \
        --periods 2026-09,2026-10 [--expect-id 2026-09=<uuid> ...]
    python scripts/competence_inventory_backup.py backup \
        --periods 2026-09,2026-10 --output backup.json [--expect-id ...]
    python scripts/competence_inventory_backup.py verify \
        --periods 2026-09,2026-10 --manifest manifest.json

Fail-closed: qualquer divergência entre o estado real e `--expect-id`/
`--manifest` aborta com código != 0 antes de qualquer escrita.
O comando `backup` faz apenas SELECTs (read-only) — a exclusão em si é
executada pelo endpoint DELETE governado.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any

from psycopg.rows import dict_row

from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_connect,
)

# Tabelas filtradas diretamente por competence_id — espelha a
# classificação de competence_deletion.py (EXCLUSIVE + BLOCKING +
# histórico). Tabelas sem competence_id são exportadas via join:
# document_version/document_file via closing_document,
# closing_package_version via closing_package.
DEPENDENT_TABLES = [
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
    "closing_package",
    "closing_review_assignment",
    "closing_terminal_rejection",
    "closing_audit_event",
]

VIA_DOCUMENT_TABLES = ["document_version", "document_file"]
VIA_PACKAGE_TABLES = ["closing_package_version"]

Q = "controllership_finance"


def _competences(cur, periods: list[str]) -> list[dict[str, Any]]:
    cur.execute(
        f"""
        SELECT competence_id, period, template_version_id, status,
               opened_by, opened_at
          FROM {Q}.monthly_competence
         WHERE period = ANY(%s)
         ORDER BY period
        """,
        (periods,),
    )
    return [dict(r) for r in cur.fetchall()]


ALL_TABLES = DEPENDENT_TABLES + VIA_DOCUMENT_TABLES + VIA_PACKAGE_TABLES


def _existing_tables(cur) -> set[str]:
    cur.execute(
        "SELECT table_name FROM information_schema.tables"
        " WHERE table_schema = %s AND table_name = ANY(%s)",
        (Q, ALL_TABLES),
    )
    return {r["table_name"] for r in cur.fetchall()}


def _rows_via_document(cur, table: str, competence_id: str):
    if table == "document_file":
        cur.execute(
            f"SELECT DISTINCT f.* FROM {Q}.document_file f"
            f" JOIN {Q}.document_version v ON v.file_id = f.file_id"
            f" JOIN {Q}.closing_document d"
            f"   ON d.document_id = v.document_id"
            " WHERE d.competence_id = %s",
            (competence_id,),
        )
    else:
        cur.execute(
            f"SELECT t.* FROM {Q}.{table} t"
            f" JOIN {Q}.closing_document d"
            f"   ON d.document_id = t.document_id"
            " WHERE d.competence_id = %s",
            (competence_id,),
        )
    return [dict(r) for r in cur.fetchall()]


def _rows_via_package(cur, table: str, competence_id: str):
    cur.execute(
        f"SELECT t.* FROM {Q}.{table} t"
        f" JOIN {Q}.closing_package p ON p.package_id = t.package_id"
        " WHERE p.competence_id = %s",
        (competence_id,),
    )
    return [dict(r) for r in cur.fetchall()]


def _clara_rows(cur, period: str, competence_id: str):
    """Linhas CLARA que referenciam a competência (sem competence_id
    próprio — ligação via resource_key/payload/plan)."""
    out = {}
    if "clara_proposal" in _existing_tables(cur):
        cur.execute(
            f"SELECT * FROM {Q}.clara_proposal"
            " WHERE resource_key = %s"
            "    OR payload->>'period' = %s"
            "    OR payload->>'competence_id' = %s"
            "    OR payload->>'expected_competence_id' = %s",
            (period, period, competence_id, competence_id),
        )
        out["clara_proposal"] = [dict(r) for r in cur.fetchall()]
    if "clara_batch" in _existing_tables(cur):
        cur.execute(
            f"SELECT * FROM {Q}.clara_batch"
            " WHERE plan::text LIKE %s",
            (f'%"period": "{period}"%',),
        )
        batches = [dict(r) for r in cur.fetchall()]
        out["clara_batch"] = batches
        if "clara_batch_operation" in _existing_tables(cur) and batches:
            cur.execute(
                f"SELECT * FROM {Q}.clara_batch_operation"
                " WHERE batch_id = ANY(%s)",
                ([b["batch_id"] for b in batches],),
            )
            out["clara_batch_operation"] = [
                dict(r) for r in cur.fetchall()
            ]
    return out


def _rows(cur, table: str, competence_id: str) -> list[dict[str, Any]]:
    cur.execute(
        f"SELECT * FROM {Q}.{table} WHERE competence_id = %s",
        (competence_id,),
    )
    return [dict(r) for r in cur.fetchall()]


def _shared_references(cur, competence_id: str) -> list[dict[str, Any]]:
    """Documentos da competência referenciados por outras competências."""
    cur.execute(
        f"""
        SELECT 'closing_reconciliation' AS source, r.competence_id::text AS
               referencing_competence, d.document_id::text AS document_id
          FROM {Q}.closing_reconciliation r
          JOIN {Q}.closing_document d ON d.document_id = r.official_document_id
         WHERE d.competence_id = %s AND r.competence_id <> %s
        UNION ALL
        SELECT 'evidence_decision', e.competence_id::text,
               d.document_id::text
          FROM {Q}.evidence_decision e
          JOIN {Q}.closing_document d ON d.document_id = e.document_id
         WHERE d.competence_id = %s AND e.competence_id <> %s
        """,
        (competence_id, competence_id, competence_id, competence_id),
    )
    return [dict(r) for r in cur.fetchall()]


def _document_files(cur, competence_id: str) -> list[dict[str, Any]]:
    cur.execute(
        f"""
        SELECT f.file_id, f.storage_key, f.original_name, f.size_bytes,
               f.checksum_sha256,
               EXISTS (
                   SELECT 1 FROM {Q}.document_version ov
                    JOIN {Q}.closing_document od
                      ON od.document_id = ov.document_id
                   WHERE ov.file_id = f.file_id
                     AND od.competence_id <> %s
               ) AS shared
          FROM {Q}.document_file f
          JOIN {Q}.document_version v ON v.file_id = f.file_id
          JOIN {Q}.closing_document d ON d.document_id = v.document_id
         WHERE d.competence_id = %s
         ORDER BY f.file_id
        """,
        (competence_id, competence_id),
    )
    return [dict(r) for r in cur.fetchall()]


def build_inventory(periods: list[str]) -> dict[str, Any]:
    with plugins_db_connect() as conn, conn.cursor(row_factory=dict_row) as cur:
        competences = _competences(cur, periods)
        found = {r["period"] for r in competences}
        missing = [p for p in periods if p not in found]
        present = _existing_tables(cur)
        absent_tables = [t for t in ALL_TABLES if t not in present]
        scope = []
        for comp in competences:
            cid = str(comp["competence_id"])
            counts = {
                t: len(_rows(cur, t, cid)) for t in DEPENDENT_TABLES
                if t in present
            }
            for t in VIA_DOCUMENT_TABLES:
                if t in present:
                    counts[t] = len(_rows_via_document(cur, t, cid))
            for t in VIA_PACKAGE_TABLES:
                if t in present:
                    counts[t] = len(_rows_via_package(cur, t, cid))
            clara = _clara_rows(cur, comp["period"], cid)
            counts.update({k: len(v) for k, v in clara.items()})
            scope.append(
                {
                    "competence": comp,
                    "counts": {k: v for k, v in counts.items() if v},
                    "files": _document_files(cur, cid),
                    "shared_references": _shared_references(cur, cid),
                }
            )
        return {"periods_requested": periods, "missing": missing,
                "absent_tables": absent_tables, "scope": scope}


def _fingerprint(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def cmd_inventory(args) -> int:
    inv = build_inventory(args.periods)
    expected = dict(e.split("=", 1) for e in args.expect_id or [])
    for entry in inv["scope"]:
        comp = entry["competence"]
        want = expected.get(comp["period"])
        if want and want != str(comp["competence_id"]):
            print(
                f"FAIL: {comp['period']} tem competence_id "
                f"{comp['competence_id']}, esperado {want}",
                file=sys.stderr,
            )
            return 2
        if want:
            expected.pop(comp["period"], None)
    if expected:
        print(f"FAIL: períodos esperados ausentes: {sorted(expected)}",
              file=sys.stderr)
        return 2
    inv["fingerprint"] = _fingerprint(inv["scope"])
    print(json.dumps(inv, indent=2, default=str))
    return 0


def cmd_backup(args) -> int:
    inv = build_inventory(args.periods)
    if inv["missing"]:
        print(f"FAIL: períodos ausentes: {inv['missing']}", file=sys.stderr)
        return 2
    backup = {"generated_by": "competence_inventory_backup.py",
              "absent_tables": inv["absent_tables"],
              "competences": []}
    present = set(ALL_TABLES) - set(inv["absent_tables"])
    with plugins_db_connect() as conn, conn.cursor(row_factory=dict_row) as cur:
        for entry in inv["scope"]:
            cid = str(entry["competence"]["competence_id"])
            period = entry["competence"]["period"]
            tables = {
                t: _rows(cur, t, cid) for t in DEPENDENT_TABLES
                if t in present
            }
            for t in VIA_DOCUMENT_TABLES:
                if t in present:
                    tables[t] = _rows_via_document(cur, t, cid)
            for t in VIA_PACKAGE_TABLES:
                if t in present:
                    tables[t] = _rows_via_package(cur, t, cid)
            tables.update(_clara_rows(cur, period, cid))
            backup["competences"].append(
                {
                    "competence": entry["competence"],
                    "tables": tables,
                    "document_files": entry["files"],
                }
            )
    backup["fingerprint"] = _fingerprint(backup["competences"])
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(backup, fh, indent=2, default=str)
    print(f"backup gravado em {args.output} "
          f"(fingerprint {backup['fingerprint'][:16]}…)")
    print("NOTA: objetos físicos em storage devem ser copiados à parte "
          "— ver `storage_key` em document_files.")
    return 0


def cmd_verify(args) -> int:
    current = build_inventory(args.periods)
    with open(args.manifest, encoding="utf-8") as fh:
        expected = json.load(fh)
    if _fingerprint(current["scope"]) != expected.get("fingerprint"):
        print("FAIL: inventário diverge do manifesto aprovado",
              file=sys.stderr)
        print(json.dumps({"current": current["scope"]}, indent=2,
                         default=str), file=sys.stderr)
        return 2
    print("OK: inventário idêntico ao manifesto aprovado")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inventory", "backup", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--periods", required=True,
                       type=lambda s: [x.strip() for x in s.split(",")])
        p.add_argument("--expect-id", action="append",
                       help="period=competence_uuid esperado (repetível)")
        p.add_argument("--output")
        p.add_argument("--manifest")
    args = parser.parse_args()
    if args.command == "backup" and not args.output:
        parser.error("backup requer --output")
    if args.command == "verify" and not args.manifest:
        parser.error("verify requer --manifest")
    return {"inventory": cmd_inventory, "backup": cmd_backup,
            "verify": cmd_verify}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
