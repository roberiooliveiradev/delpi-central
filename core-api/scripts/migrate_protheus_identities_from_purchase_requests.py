#!/usr/bin/env python3
"""Dry-run / apply transfer of Protheus mappings into Core.

Reads purchase_requests.user_protheus_mappings (plugins DB) and upserts into
core.user_protheus_identities. Does NOT delete the source table.

Usage (never run against production without backup + authorization):

  # Inventory / dry-run (default)
  python scripts/migrate_protheus_identities_from_purchase_requests.py \\
    --plugins-dsn "$PLUGINS_DATABASE_URL" \\
    --core-dsn "$CORE_DATABASE_URL"

  # Apply (idempotent upsert)
  python scripts/migrate_protheus_identities_from_purchase_requests.py \\
    --plugins-dsn "$PLUGINS_DATABASE_URL" \\
    --core-dsn "$CORE_DATABASE_URL" \\
    --apply

Exit codes:
  0 — success (or dry-run complete with no blocking conflicts)
  2 — blocking conflicts (apply refused)
  3 — usage / connection error
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

try:
    import psycopg2
    import psycopg2.extras
except ImportError as exc:  # pragma: no cover
    print("psycopg2 required:", exc, file=sys.stderr)
    sys.exit(3)


@dataclass
class Conflict:
    code: str
    user_id: str | None
    protheus_user_id: str | None
    detail: str


def _parse_uuid(raw: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(raw).strip())
    except (ValueError, AttributeError, TypeError):
        return None


def load_source(conn) -> list[dict[str, Any]]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT user_id, protheus_user_id, protheus_user_code, mapping_status,
                   mapping_source, verified, created_at, updated_at
            FROM purchase_requests.user_protheus_mappings
            ORDER BY user_id
            """
        )
        return [dict(row) for row in cur.fetchall()]


def load_core_user_ids(conn) -> set[uuid.UUID]:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users")
        return {row[0] for row in cur.fetchall()}


def inventory(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status = Counter((r.get("mapping_status") or "").strip() for r in rows)
    sources = Counter((r.get("mapping_source") or "null") for r in rows)
    verified = sum(1 for r in rows if r.get("verified"))
    leading_zeros = sum(
        1
        for r in rows
        if isinstance(r.get("protheus_user_id"), str)
        and r["protheus_user_id"].startswith("0")
        and r["protheus_user_id"].strip("0")
    )
    return {
        "total": len(rows),
        "by_status": dict(status),
        "by_source": dict(sources),
        "verified": verified,
        "protheus_ids_with_leading_zeros": leading_zeros,
    }


def detect_conflicts(
    rows: list[dict[str, Any]],
    core_users: set[uuid.UUID],
) -> list[Conflict]:
    conflicts: list[Conflict] = []
    seen_users: set[str] = set()
    protheus_owners: dict[str, str] = {}

    for row in rows:
        raw_uid = str(row.get("user_id") or "").strip()
        uid = _parse_uuid(raw_uid)
        if uid is None:
            conflicts.append(
                Conflict("invalid_user_id", raw_uid, None, "user_id não é UUID")
            )
            continue
        if raw_uid in seen_users:
            conflicts.append(
                Conflict("duplicate_user_id", raw_uid, None, "duplicata na origem")
            )
        seen_users.add(raw_uid)
        if uid not in core_users:
            conflicts.append(
                Conflict("orphan_user", raw_uid, None, "usuário inexistente no Core")
            )

        status = (row.get("mapping_status") or "").strip()
        pid = (row.get("protheus_user_id") or "").strip() or None
        if status == "mapped" and pid:
            prev = protheus_owners.get(pid)
            if prev and prev != raw_uid:
                conflicts.append(
                    Conflict(
                        "duplicate_protheus_user_id",
                        raw_uid,
                        pid,
                        f"já associado a {prev}",
                    )
                )
            else:
                protheus_owners[pid] = raw_uid

        if status and status not in {"mapped", "unmapped", "ambiguous"}:
            conflicts.append(
                Conflict("invalid_status", raw_uid, pid, f"status={status}")
            )
        source = row.get("mapping_source")
        if source is not None and source not in {
            "manual",
            "email_match",
            "login_match",
        }:
            conflicts.append(
                Conflict("invalid_source", raw_uid, pid, f"source={source}")
            )

    return conflicts


def upsert_core(conn, row: dict[str, Any], *, dry_run: bool) -> None:
    uid = _parse_uuid(str(row["user_id"]))
    assert uid is not None
    sql = """
    INSERT INTO user_protheus_identities (
        user_id, protheus_user_id, protheus_user_code, mapping_status,
        mapping_source, verified, created_at, updated_at
    ) VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
    ON CONFLICT (user_id) DO UPDATE SET
        protheus_user_id = EXCLUDED.protheus_user_id,
        protheus_user_code = EXCLUDED.protheus_user_code,
        mapping_status = EXCLUDED.mapping_status,
        mapping_source = EXCLUDED.mapping_source,
        verified = EXCLUDED.verified,
        updated_at = EXCLUDED.updated_at
    """
    params = (
        str(uid),
        row.get("protheus_user_id"),
        row.get("protheus_user_code"),
        row.get("mapping_status") or "unmapped",
        row.get("mapping_source"),
        bool(row.get("verified")),
        row.get("created_at"),
        row.get("updated_at"),
    )
    if dry_run:
        return
    with conn.cursor() as cur:
        cur.execute(sql, params)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugins-dsn", required=True)
    parser.add_argument("--core-dsn", required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist upserts (default is dry-run only)",
    )
    parser.add_argument(
        "--allow-conflicts",
        action="store_true",
        help="Apply even with conflicts (skips conflicting rows)",
    )
    args = parser.parse_args(argv)
    dry_run = not args.apply

    plugins = psycopg2.connect(args.plugins_dsn)
    core = psycopg2.connect(args.core_dsn)
    try:
        rows = load_source(plugins)
        core_users = load_core_user_ids(core)
        stats = inventory(rows)
        conflicts = detect_conflicts(rows, core_users)

        blocking = [
            c
            for c in conflicts
            if c.code
            in {
                "duplicate_protheus_user_id",
                "invalid_user_id",
                "invalid_status",
                "invalid_source",
            }
        ]

        transferred = 0
        skipped = 0
        conflict_user_ids = {c.user_id for c in blocking if c.user_id}

        for row in rows:
            uid = str(row.get("user_id") or "").strip()
            if uid in conflict_user_ids and not args.allow_conflicts:
                skipped += 1
                continue
            parsed = _parse_uuid(uid)
            if parsed is None or parsed not in core_users:
                skipped += 1
                continue
            upsert_core(core, row, dry_run=dry_run)
            transferred += 1

        if not dry_run:
            core.commit()

        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "dry-run" if dry_run else "apply",
            "inventory": stats,
            "conflicts": [asdict(c) for c in conflicts],
            "transferred": transferred,
            "skipped": skipped,
            "postcondition": {
                "source_table_untouched": True,
                "production_cutover": "PENDING — set PROTHEUS_IDENTITY_OWNER=core after reconciliation",
            },
        }
        # Sanitized: no emails/names — only ids already in mappings.
        print(json.dumps(manifest, indent=2, default=str))

        if blocking and not args.allow_conflicts and args.apply:
            return 2
        return 0
    finally:
        plugins.close()
        core.close()


if __name__ == "__main__":
    sys.exit(main())
