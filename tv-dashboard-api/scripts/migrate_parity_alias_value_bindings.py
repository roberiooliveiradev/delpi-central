"""Wave 3 — migração governada de bindings persistidos parity-alias non-SI.

`field: "value"` em blocos ligados a operationIds de
`PARITY_ALIAS_FIELD_MAP` migra para o campo semântico canônico do producer.

Executar DENTRO do container tv-dashboard-api (env PLUGINS_DB_*):

    docker exec -i delpi-tv-dashboard-api python3 - < tv-dashboard-api/scripts/migrate_parity_alias_value_bindings.py

Flags (argv):
    --apply            aplica a escrita (default: dry-run, só reporta)
    --expect N         aborta se refs encontradas != N (default: 9)
    --backup-path P    grava snapshot JSON das linhas afetadas em P

Caminho canônico: `PlaylistRepository.update_slide` — captura histórico
(playlist_history), bump de updated_at e transação por slide.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

EXPECTED_REFS = 9
MIGRATION_ACTOR = "wave3-parity-alias-field-migration"
MIGRATION_REASON = "parity_alias_value_field_migration"


def _scan_slides() -> list[dict]:
    from tv_app.infrastructure.persistence.plugins_postgres_connection import (
        get_connection,
    )

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text, playlist_id::text, title, native_config, updated_at
            FROM tv_dashboard.slides
            WHERE native_config IS NOT NULL
            ORDER BY id
            """
        )
        return cur.fetchall()


def _count_active_value_refs() -> dict[str, int]:
    """Postcondition scan: conta refs 'value' por classe de operationId."""
    from tv_app.application.services.data.value_field_binding_migration import (
        FIELD_REF_KEYS,
        FIELD_REF_LIST_KEYS,
        PARITY_ALIAS_FIELD_MAP,
        _iter_block_lists,
        _resolve_operation_id,
        si_meta_canonical_field,
    )

    counts = {
        "parity_alias": 0,
        "si_meta": 0,
        "si_realized": 0,
        "other": 0,
        "unresolved": 0,
    }
    for row in _scan_slides():
        for blocks in _iter_block_lists(row["native_config"]):
            by_id = {
                str(b.get("id")): b
                for b in blocks
                if isinstance(b, dict) and b.get("id")
            }
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                hits = []

                def _walk(node):
                    if isinstance(node, dict):
                        for k, v in node.items():
                            if k in FIELD_REF_KEYS and v == "value":
                                hits.append(k)
                            elif k in FIELD_REF_LIST_KEYS and isinstance(v, list):
                                hits.extend(i for i in v if i == "value")
                            _walk(v)
                    elif isinstance(node, list):
                        for it in node:
                            _walk(it)

                _walk(block)
                if not hits:
                    continue
                op = _resolve_operation_id(block, by_id) or ""
                if op in PARITY_ALIAS_FIELD_MAP:
                    counts["parity_alias"] += len(hits)
                elif si_meta_canonical_field(op):
                    counts["si_meta"] += len(hits)
                elif op.endswith("_realized") and op.startswith("get_si_indicator_"):
                    counts["si_realized"] += len(hits)
                elif op:
                    counts["other"] += len(hits)
                else:
                    counts["unresolved"] += len(hits)
    return counts


def main() -> int:
    apply = "--apply" in sys.argv
    expect = EXPECTED_REFS
    backup_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--expect" and i + 1 < len(sys.argv):
            expect = int(sys.argv[i + 1])
        if arg == "--backup-path" and i + 1 < len(sys.argv):
            backup_path = sys.argv[i + 1]

    from tv_app.application.services.data.value_field_binding_migration import (
        collect_value_refs,
        migrate_native_config,
        parity_alias_canonical_field,
    )

    rows = _scan_slides()
    targets = []
    for row in rows:
        refs = collect_value_refs(row["native_config"], parity_alias_canonical_field)
        if refs:
            targets.append((row, refs))

    found = sum(len(refs) for _, refs in targets)
    print(f"[scan] slides={len(rows)} targets={len(targets)} refs={found}", flush=True)
    if found != expect:
        print(
            f"[abort] EXECUTION_DRIFT: expected {expect} refs, found {found}.",
            file=sys.stderr,
        )
        return 2

    if not apply:
        for row, refs in targets:
            ops = sorted({r["operationId"] for r in refs})
            print(
                f"[dry] slide={row['id']} playlist={row['playlist_id']} "
                f"refs={len(refs)} ops={ops}"
            )
        print("[dry] nada escrito (use --apply).")
        return 0

    if backup_path:
        backup = [
            {
                "id": row["id"],
                "playlist_id": row["playlist_id"],
                "title": row["title"],
                "native_config": row["native_config"],
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
            for row, _ in targets
        ]
        with open(backup_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "reason": MIGRATION_REASON,
                    "rows": backup,
                },
                fh,
                ensure_ascii=False,
                indent=1,
            )
        print(f"[backup] {len(backup)} linhas -> {backup_path}", flush=True)

    from tv_app.infrastructure.persistence.repositories.playlist_repository import (
        PlaylistRepository,
    )

    repo = PlaylistRepository()
    updated = 0
    for row, _ in targets:
        migrated, applied = migrate_native_config(
            row["native_config"], parity_alias_canonical_field
        )
        assert len(applied) > 0
        repo.update_slide(
            row["playlist_id"],
            row["id"],
            {"nativeConfig": migrated},
            actor_user_id=MIGRATION_ACTOR,
            reason=MIGRATION_REASON,
        )
        updated += len(applied)
        print(f"[apply] slide={row['id']} migrated={len(applied)}", flush=True)

    post = _count_active_value_refs()
    print(f"[post] {post}", flush=True)
    ok = post["parity_alias"] == 0
    print("[done] migrated=%d postcondition=%s" % (updated, "OK" if ok else "FAIL"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
