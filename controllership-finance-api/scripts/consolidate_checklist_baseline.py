#!/usr/bin/env python3
"""Consolidação controlada do baseline do checklist mensal (Gate B).

Objetivo: tornar o conteúdo da versão origem (ex.: V2 em REVIEW) o
conteúdo da versão oficial alvo (ex.: V1), publicada com vigência
`effective_from`, e inativar a origem — tudo em UMA transação, com
validações fail-closed e read-back.

    python scripts/consolidate_checklist_baseline.py apply \
        --template-code monthly-closing-checklist \
        --source-version 2 --target-version 1 \
        --effective-from 2026-01 --actor <uuid> \
        --expect-items 16 [--dry-run]

Por que não usar o endpoint de requisito documental: a publicação
retroativa passa por `window_covers_open_competence` /
`retroactive_effective_period`, guards intencionais para o fluxo
prospectivo normal. Esta consolidação é uma operação administrativa
única que preserva snapshots (competências abertas guardam cópia dos
itens — verificar com --acknowledge-periods se houver) e deixa trilha
de auditoria explícita (`CHECKLIST_BASELINE_CONSOLIDATED`).
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

Q = "controllership_finance"
ITEM_COLUMNS = (
    "item_key, sort_order, sheet, name, purpose, origin_kind,"
    " recipient_area, applicability, branch_scope, totvs_report_ref,"
    " requirement_notes, validation_scope"
)


def _items(cur, version_id: str) -> list[dict[str, Any]]:
    cur.execute(
        f"SELECT {ITEM_COLUMNS} FROM {Q}.checklist_template_item"
        " WHERE version_id = %s ORDER BY sort_order, item_key",
        (version_id,),
    )
    return [dict(r) for r in cur.fetchall()]


def _checksum(items: list[dict[str, Any]]) -> str:
    blob = json.dumps(items, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def _fail(message: str, detail: Any = None) -> "SystemExit":
    print(json.dumps({"error": "consolidation_refused",
                      "message": message, "detail": detail},
                     default=str), file=sys.stderr)
    return SystemExit(2)


def consolidate(args) -> dict[str, Any]:
    with plugins_db_connect() as conn:
        cur = conn.cursor(row_factory=dict_row)
        cur.execute(
            f"SELECT template_id FROM {Q}.checklist_template"
            " ORDER BY template_id FOR UPDATE"
        )
        cur.execute(
            f"SELECT template_id, code FROM {Q}.checklist_template"
            " WHERE code = %s",
            (args.template_code,),
        )
        row = cur.fetchone()
        if row is None:
            raise _fail("template não encontrado",
                        {"code": args.template_code})
        template_id = row["template_id"]
        cur.execute(
            f"SELECT version_id, version, status, revision,"
            "       effective_from_period"
            f"  FROM {Q}.checklist_template_version"
            " WHERE template_id = %s ORDER BY version",
            (template_id,),
        )
        versions = {r["version"]: r for r in cur.fetchall()}
        source = versions.get(args.source_version)
        target = versions.get(args.target_version)
        if source is None or target is None:
            raise _fail("versão origem/alvo ausente",
                        {"versions": {k: v["status"]
                                      for k, v in versions.items()}})
        source_items = _items(cur, str(source["version_id"]))
        target_items = _items(cur, str(target["version_id"]))
        src_sum, tgt_sum = _checksum(source_items), _checksum(target_items)
        if len(source_items) != args.expect_items:
            raise _fail("contagem de itens da origem diverge",
                        {"expected": args.expect_items,
                         "found": len(source_items)})
        already = (
            target["status"] == "PUBLISHED"
            and str(target["effective_from_period"]) == args.effective_from
            and source["status"] == "INACTIVE"
            and src_sum == tgt_sum
        )
        if already:
            return {"replayed": True, "template_id": str(template_id),
                    "target_version": args.target_version,
                    "items": len(target_items), "checksum": tgt_sum}
        # Competing published versions inside the same window.
        competitors = [
            v["version"] for v in versions.values()
            if v["version"] not in (args.source_version, args.target_version)
            and v["status"] == "PUBLISHED"
            and str(v["effective_from_period"] or "") >= args.effective_from
        ]
        if competitors:
            raise _fail("versão publicada concorrente na janela",
                        {"versions": competitors})
        # Open competences inside the retroactive window.
        cur.execute(
            f"SELECT competence_id, period, template_version_id"
            f"  FROM {Q}.monthly_competence WHERE period >= %s",
            (args.effective_from,),
        )
        open_rows = cur.fetchall()
        acknowledged = set(args.acknowledge_periods or [])
        blocking = [
            {"competence_id": str(r["competence_id"]),
             "period": r["period"],
             "template_version_id": (
                 str(r["template_version_id"])
                 if r["template_version_id"] else None)}
            for r in open_rows if r["period"] not in acknowledged
        ]
        if blocking:
            raise _fail(
                "competências na janela retroativa exigem "
                "--acknowledge-periods explícito",
                blocking)
        for r in open_rows:
            cur.execute(
                f"SELECT count(*) AS n FROM {Q}.competence_checklist_item"
                " WHERE competence_id = %s",
                (r["competence_id"],),
            )
            if cur.fetchone()["n"]:
                raise _fail(
                    "competência com snapshot congelado na janela — "
                    "saneamento prévio obrigatório",
                    {"competence_id": str(r["competence_id"]),
                     "period": r["period"]})
        # Rewrite target items as a copy of source.
        cur.execute(
            f"DELETE FROM {Q}.checklist_template_item WHERE version_id = %s",
            (target["version_id"],),
        )
        for item in source_items:
            cur.execute(
                f"INSERT INTO {Q}.checklist_template_item"
                f" (version_id, {ITEM_COLUMNS})"
                " VALUES (%(version_id)s, %(item_key)s, %(sort_order)s,"
                " %(sheet)s, %(name)s, %(purpose)s, %(origin_kind)s,"
                " %(recipient_area)s, %(applicability)s, %(branch_scope)s,"
                " %(totvs_report_ref)s, %(requirement_notes)s,"
                " %(validation_scope)s)",
                {"version_id": target["version_id"], **item},
            )
        cur.execute(
            f"UPDATE {Q}.checklist_template_version"
            "   SET status = 'PUBLISHED', effective_from_period = %s,"
            "       published_by = %s, published_at = now(),"
            "       revision = revision + 1, updated_at = now()"
            " WHERE version_id = %s",
            (args.effective_from, args.actor, target["version_id"]),
        )
        cur.execute(
            f"UPDATE {Q}.checklist_template_version"
            "   SET status = 'INACTIVE', inactivated_by = %s,"
            "       inactivated_at = now(), revision = revision + 1,"
            "       updated_at = now()"
            " WHERE version_id = %s",
            (args.actor, source["version_id"]),
        )
        # Read-back inside the transaction.
        new_items = _items(cur, str(target["version_id"]))
        if _checksum(new_items) != src_sum:
            raise _fail("read-back divergiu do snapshot da origem")
        cur.execute(
            f"SELECT version FROM {Q}.checklist_template_version v"
            " WHERE v.status = 'PUBLISHED'"
            "   AND v.effective_from_period <= %s"
            " ORDER BY v.effective_from_period DESC, v.version DESC"
            " LIMIT 1",
            (args.effective_from,),
        )
        selected = cur.fetchone()
        if selected is None or selected["version"] != args.target_version:
            raise _fail("seleção de versão vigente não retorna o alvo",
                        {"selected": selected})
        cur.execute(
            f"INSERT INTO {Q}.closing_audit_event"
            " (entity_type, entity_id, competence_id, event_type,"
            "  actor_subject, detail)"
            " VALUES ('checklist_template', %s, NULL,"
            " 'CHECKLIST_BASELINE_CONSOLIDATED', %s, %s)",
            (
                template_id,
                args.actor,
                json.dumps({
                    "template_code": args.template_code,
                    "source_version": args.source_version,
                    "target_version": args.target_version,
                    "source_status_before": source["status"],
                    "target_status_before": target["status"],
                    "effective_from_period": args.effective_from,
                    "items": len(source_items),
                    "checksum": src_sum,
                    "acknowledged_competences": sorted(acknowledged),
                    "dry_run": args.dry_run,
                }),
            ),
        )
        result = {
            "replayed": False,
            "template_id": str(template_id),
            "source_version": args.source_version,
            "source_status": "INACTIVE",
            "target_version": args.target_version,
            "target_status": "PUBLISHED",
            "effective_from_period": args.effective_from,
            "items": len(new_items),
            "checksum": src_sum,
            "dry_run": args.dry_run,
        }
        if args.dry_run:
            conn.rollback()
            result["rolled_back"] = True
            return result
        conn.commit()
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["apply"])
    parser.add_argument("--template-code", required=True)
    parser.add_argument("--source-version", type=int, required=True)
    parser.add_argument("--target-version", type=int, required=True)
    parser.add_argument("--effective-from", required=True)
    parser.add_argument("--actor", required=True,
                        help="subject UUID do operador com manage")
    parser.add_argument("--expect-items", type=int, required=True)
    parser.add_argument("--acknowledge-periods", type=lambda s: [
        x.strip() for x in s.split(",") if x.strip()])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(consolidate(args), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
