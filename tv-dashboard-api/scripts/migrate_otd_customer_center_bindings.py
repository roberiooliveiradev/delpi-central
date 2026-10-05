"""Migração governada `cliente_loja_centro` → `customer_center` (OTD por cliente).

Executar DENTRO do container tv-dashboard-api (env PLUGINS_DB_*):

    docker exec -i delpi-tv-dashboard-api python3 - < tv-dashboard-api/scripts/migrate_otd_customer_center_bindings.py

Flags (argv):
    --apply            aplica a escrita (default: dry-run, só reporta)
    --expect N         aborta se refs encontradas != N (default: sem trava)
    --backup-path P    grava snapshot JSON das linhas afetadas em P

Caminho canônico: `PlaylistRepository.update_slide` — captura histórico
(playlist_history), bump de updated_at e transação por slide.

Pré-condição: api-delpi >= commit que resolve `customer_center` sem o filtro
`customer_centers` (SA7010.A7_XCENT via join agrupado).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

MIGRATION_ACTOR = "otd-customer-center-field-migration"
MIGRATION_REASON = "otd_customer_center_field_migration"


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


def _count_active_legacy_refs() -> int:
    """Postcondition scan: refs restantes de `cliente_loja_centro` nas rotas-alvo."""
    from tv_app.application.services.data.otd_customer_center_binding_migration import (
        collect_customer_center_refs,
    )

    return sum(
        len(collect_customer_center_refs(row["native_config"]))
        for row in _scan_slides()
    )


def main() -> int:
    apply = "--apply" in sys.argv
    expect = None
    backup_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--expect" and i + 1 < len(sys.argv):
            expect = int(sys.argv[i + 1])
        if arg == "--backup-path" and i + 1 < len(sys.argv):
            backup_path = sys.argv[i + 1]

    from tv_app.application.services.data.otd_customer_center_binding_migration import (
        collect_customer_center_refs,
        migrate_native_config,
    )

    rows = _scan_slides()
    targets = []
    for row in rows:
        refs = collect_customer_center_refs(row["native_config"])
        if refs:
            targets.append((row, refs))

    found = sum(len(refs) for _, refs in targets)
    print(f"[scan] slides={len(rows)} targets={len(targets)} refs={found}", flush=True)
    if expect is not None and found != expect:
        print(
            f"[abort] EXECUTION_DRIFT: expected {expect} refs, found {found}.",
            file=sys.stderr,
        )
        return 2

    if not apply:
        for row, refs in targets:
            kinds = sorted({ref["kind"] for ref in refs})
            paths = sorted(ref["field_path"] for ref in refs)
            print(
                f"[dry] slide={row['id']} title={row['title']!r} "
                f"playlist={row['playlist_id']} refs={len(refs)} kinds={kinds}",
                flush=True,
            )
            for path in paths:
                print(f"[dry]   {path}", flush=True)
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
        migrated, applied = migrate_native_config(row["native_config"])
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

    remaining = _count_active_legacy_refs()
    print(f"[post] remaining_legacy_refs={remaining}", flush=True)
    ok = remaining == 0
    print("[done] migrated=%d postcondition=%s" % (updated, "OK" if ok else "FAIL"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
