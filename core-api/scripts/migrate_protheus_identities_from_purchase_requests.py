#!/usr/bin/env python3
"""Transfer Protheus mappings into Core — fail-closed, dry-run first.

Reads ``purchase_requests.user_protheus_mappings`` and plans upserts into
``user_protheus_identities``. Does NOT delete or mutate the source table.

Safety guarantees
-----------------
* Blocking conflicts / orphans abort **before** any write.
* ``--apply`` runs in a single transaction (rollback on any failure).
* Destination rows that already match are no-ops (true idempotency).
* Divergent Core rows are never overwritten silently.
* No ``--allow-conflicts`` bypass.

Usage (production requires backup + operational authorization):

  python scripts/migrate_protheus_identities_from_purchase_requests.py \\
    --plugins-dsn "$PLUGINS_DATABASE_URL" \\
    --core-dsn "$CORE_DATABASE_URL"

  python scripts/migrate_protheus_identities_from_purchase_requests.py \\
    --plugins-dsn "$PLUGINS_DATABASE_URL" \\
    --core-dsn "$CORE_DATABASE_URL" \\
    --apply

Exit codes:
  0 — dry-run ready / apply succeeded (zero blocking issues)
  2 — blocked (conflicts/orphans/divergences) — no writes persisted
  3 — usage / connection / unexpected runtime error
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

try:
    import psycopg2
    import psycopg2.extras
except ImportError as exc:  # pragma: no cover
    print("psycopg2 required:", exc, file=sys.stderr)
    sys.exit(3)


BLOCKING_CODES = frozenset(
    {
        "invalid_user_id",
        "duplicate_user_id",
        "orphan_user",
        "inactive_user",
        "duplicate_protheus_user_id",
        "invalid_status",
        "invalid_source",
        "destination_conflict",
        "destination_newer_divergence",
        "destination_protheus_owned_elsewhere",
    }
)

SEMANTIC_FIELDS = (
    "protheus_user_id",
    "protheus_user_code",
    "mapping_status",
    "mapping_source",
    "verified",
)


@dataclass
class Conflict:
    code: str
    user_id: str | None
    protheus_user_id: str | None
    detail: str


@dataclass
class TransferItem:
    action: str  # insert | update | identical | blocked
    user_id: str
    classification: str
    source: dict[str, Any] = field(default_factory=dict)


def parse_uuid(raw: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(raw).strip())
    except (ValueError, AttributeError, TypeError):
        return None


def _norm_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _norm_bool(value: Any) -> bool:
    return bool(value)


def semantic_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "protheus_user_id": _norm_text(row.get("protheus_user_id")),
        "protheus_user_code": _norm_text(row.get("protheus_user_code")),
        "mapping_status": _norm_text(row.get("mapping_status")) or "unmapped",
        "mapping_source": _norm_text(row.get("mapping_source")),
        "verified": _norm_bool(row.get("verified")),
    }


def semantics_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return semantic_snapshot(a) == semantic_snapshot(b)


def inventory(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status = Counter((_norm_text(r.get("mapping_status")) or "") for r in rows)
    sources = Counter((_norm_text(r.get("mapping_source")) or "null") for r in rows)
    verified = sum(1 for r in rows if r.get("verified"))
    leading_zeros = sum(
        1
        for r in rows
        if isinstance(r.get("protheus_user_id"), str)
        and str(r["protheus_user_id"]).startswith("0")
        and str(r["protheus_user_id"]).strip("0")
    )
    return {
        "total": len(rows),
        "by_status": dict(status),
        "by_source": dict(sources),
        "verified": verified,
        "protheus_ids_with_leading_zeros": leading_zeros,
    }


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


def load_core_users(conn) -> dict[uuid.UUID, bool]:
    """Map user_id → active flag."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, active FROM users")
        return {row[0]: bool(row[1]) for row in cur.fetchall()}


def load_destination(conn) -> dict[str, dict[str, Any]]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT user_id, protheus_user_id, protheus_user_code, mapping_status,
                   mapping_source, verified, created_at, updated_at
            FROM user_protheus_identities
            """
        )
        out: dict[str, dict[str, Any]] = {}
        for row in cur.fetchall():
            data = dict(row)
            out[str(data["user_id"])] = data
        return out


def detect_source_conflicts(
    rows: list[dict[str, Any]],
    core_users: dict[uuid.UUID, bool],
) -> list[Conflict]:
    conflicts: list[Conflict] = []
    seen_users: set[str] = set()
    protheus_owners: dict[str, str] = {}

    for row in rows:
        raw_uid = str(row.get("user_id") or "").strip()
        uid = parse_uuid(raw_uid)
        pid = _norm_text(row.get("protheus_user_id"))
        status = _norm_text(row.get("mapping_status")) or ""

        if uid is None:
            conflicts.append(
                Conflict("invalid_user_id", raw_uid or None, pid, "user_id não é UUID")
            )
            continue

        if raw_uid in seen_users:
            conflicts.append(
                Conflict("duplicate_user_id", raw_uid, pid, "duplicata na origem")
            )
        seen_users.add(raw_uid)

        if uid not in core_users:
            conflicts.append(
                Conflict("orphan_user", raw_uid, pid, "usuário inexistente no Core")
            )
        elif not core_users[uid] and status == "mapped":
            conflicts.append(
                Conflict(
                    "inactive_user",
                    raw_uid,
                    pid,
                    "usuário Core inativo com mapping mapped",
                )
            )

        if status == "mapped" and pid:
            prev = protheus_owners.get(pid)
            if prev and prev != raw_uid:
                conflicts.append(
                    Conflict(
                        "duplicate_protheus_user_id",
                        raw_uid,
                        pid,
                        f"já associado na origem a {prev}",
                    )
                )
            else:
                protheus_owners[pid] = raw_uid

        if status and status not in {"mapped", "unmapped", "ambiguous"}:
            conflicts.append(
                Conflict("invalid_status", raw_uid, pid, f"status={status}")
            )
        source = row.get("mapping_source")
        if source is not None and _norm_text(source) not in {
            "manual",
            "email_match",
            "login_match",
        }:
            conflicts.append(
                Conflict("invalid_source", raw_uid, pid, f"source={source}")
            )

    return conflicts


def classify_against_destination(
    source_row: dict[str, Any],
    destination: dict[str, dict[str, Any]],
    destination_protheus_owners: dict[str, str],
) -> tuple[str, Conflict | None]:
    """Return (classification, optional conflict)."""
    raw_uid = str(source_row.get("user_id") or "").strip()
    dest = destination.get(raw_uid)
    src_snap = semantic_snapshot(source_row)
    pid = src_snap["protheus_user_id"]

    if (
        src_snap["mapping_status"] == "mapped"
        and pid
        and destination_protheus_owners.get(pid)
        and destination_protheus_owners[pid] != raw_uid
    ):
        return (
            "destination_protheus_owned_elsewhere",
            Conflict(
                "destination_protheus_owned_elsewhere",
                raw_uid,
                pid,
                f"Core já mapeia USR_ID para {destination_protheus_owners[pid]}",
            ),
        )

    if dest is None:
        return "absent", None

    if semantics_equal(source_row, dest):
        return "identical", None

    src_updated = source_row.get("updated_at")
    dest_updated = dest.get("updated_at")
    if (
        isinstance(src_updated, datetime)
        and isinstance(dest_updated, datetime)
        and dest_updated > src_updated
    ):
        return (
            "destination_newer_divergence",
            Conflict(
                "destination_newer_divergence",
                raw_uid,
                pid,
                "Core diverge e é mais recente que a origem",
            ),
        )

    return (
        "destination_conflict",
        Conflict(
            "destination_conflict",
            raw_uid,
            pid,
            "origem e destino divergem semanticamente",
        ),
    )


def build_transfer_plan(
    rows: list[dict[str, Any]],
    core_users: dict[uuid.UUID, bool],
    destination: dict[str, dict[str, Any]],
) -> tuple[list[TransferItem], list[Conflict]]:
    conflicts = detect_source_conflicts(rows, core_users)

    destination_protheus_owners: dict[str, str] = {}
    for dest_uid, dest_row in destination.items():
        snap = semantic_snapshot(dest_row)
        if snap["mapping_status"] == "mapped" and snap["protheus_user_id"]:
            destination_protheus_owners[snap["protheus_user_id"]] = dest_uid

    blocked_users = {c.user_id for c in conflicts if c.user_id}
    plan: list[TransferItem] = []

    for row in rows:
        raw_uid = str(row.get("user_id") or "").strip()
        if raw_uid in blocked_users:
            plan.append(
                TransferItem(
                    action="blocked",
                    user_id=raw_uid,
                    classification="source_conflict",
                    source=semantic_snapshot(row),
                )
            )
            continue

        classification, dest_conflict = classify_against_destination(
            row, destination, destination_protheus_owners
        )
        if dest_conflict is not None:
            conflicts.append(dest_conflict)
            plan.append(
                TransferItem(
                    action="blocked",
                    user_id=raw_uid,
                    classification=classification,
                    source=semantic_snapshot(row),
                )
            )
            continue

        if classification == "identical":
            plan.append(
                TransferItem(
                    action="identical",
                    user_id=raw_uid,
                    classification=classification,
                    source=semantic_snapshot(row),
                )
            )
        elif classification == "absent":
            plan.append(
                TransferItem(
                    action="insert",
                    user_id=raw_uid,
                    classification=classification,
                    source=semantic_snapshot(row),
                )
            )
        else:
            # Should not reach — divergences become conflicts.
            conflicts.append(
                Conflict(
                    "destination_conflict",
                    raw_uid,
                    semantic_snapshot(row)["protheus_user_id"],
                    f"classificação inesperada: {classification}",
                )
            )
            plan.append(
                TransferItem(
                    action="blocked",
                    user_id=raw_uid,
                    classification=classification,
                    source=semantic_snapshot(row),
                )
            )

    return plan, conflicts


def blocking_conflicts(conflicts: list[Conflict]) -> list[Conflict]:
    return [c for c in conflicts if c.code in BLOCKING_CODES]


def apply_inserts(conn, items: list[TransferItem], source_by_user: dict[str, dict]) -> int:
    sql = """
    INSERT INTO user_protheus_identities (
        user_id, protheus_user_id, protheus_user_code, mapping_status,
        mapping_source, verified, created_at, updated_at
    ) VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
    """
    written = 0
    with conn.cursor() as cur:
        for item in items:
            if item.action != "insert":
                continue
            row = source_by_user[item.user_id]
            uid = parse_uuid(item.user_id)
            assert uid is not None
            snap = semantic_snapshot(row)
            cur.execute(
                sql,
                (
                    str(uid),
                    snap["protheus_user_id"],
                    snap["protheus_user_code"],
                    snap["mapping_status"],
                    snap["mapping_source"],
                    snap["verified"],
                    row.get("created_at"),
                    row.get("updated_at"),
                ),
            )
            written += 1
    return written


def build_manifest(
    *,
    mode: str,
    source_stats: dict[str, Any],
    destination_stats: dict[str, Any],
    plan: list[TransferItem],
    conflicts: list[Conflict],
    ready: bool,
    written: int = 0,
) -> dict[str, Any]:
    counts = Counter(item.action for item in plan)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "ready_to_apply": ready,
        "inventory": {
            "source": source_stats,
            "destination": destination_stats,
        },
        "plan": {
            "insert": counts.get("insert", 0),
            "identical": counts.get("identical", 0),
            "update": counts.get("update", 0),
            "blocked": counts.get("blocked", 0),
        },
        "written": written,
        "conflicts": [asdict(c) for c in conflicts],
        "blocking_conflict_count": len(blocking_conflicts(conflicts)),
        "postcondition": {
            "source_table_untouched": True,
            "no_partial_apply": True,
            "production_cutover": (
                "PENDING — set PROTHEUS_IDENTITY_OWNER=core only after reconciliation"
            ),
        },
    }


def run_migration(
    *,
    plugins_dsn: str,
    core_dsn: str,
    apply: bool,
) -> tuple[int, dict[str, Any]]:
    plugins = psycopg2.connect(plugins_dsn)
    core = psycopg2.connect(core_dsn)
    try:
        source_rows = load_source(plugins)
        core_users = load_core_users(core)
        destination = load_destination(core)

        source_stats = inventory(source_rows)
        destination_stats = inventory(list(destination.values()))

        plan, conflicts = build_transfer_plan(source_rows, core_users, destination)
        blocked = blocking_conflicts(conflicts)
        ready = len(blocked) == 0

        if not apply:
            manifest = build_manifest(
                mode="dry-run",
                source_stats=source_stats,
                destination_stats=destination_stats,
                plan=plan,
                conflicts=conflicts,
                ready=ready,
            )
            return (0 if ready else 2), manifest

        if not ready:
            # Fail closed: never write when blocked.
            manifest = build_manifest(
                mode="apply-refused",
                source_stats=source_stats,
                destination_stats=destination_stats,
                plan=plan,
                conflicts=conflicts,
                ready=False,
            )
            return 2, manifest

        source_by_user = {
            str(r.get("user_id") or "").strip(): r for r in source_rows
        }
        try:
            written = apply_inserts(core, plan, source_by_user)
            core.commit()
        except Exception:
            core.rollback()
            raise

        # Post-apply reconciliation snapshot
        destination_after = load_destination(core)
        after_stats = inventory(list(destination_after.values()))
        remaining_absent = 0
        for item in plan:
            if item.action != "insert":
                continue
            if item.user_id not in destination_after:
                remaining_absent += 1
            elif not semantics_equal(source_by_user[item.user_id], destination_after[item.user_id]):
                remaining_absent += 1
        if remaining_absent:
            manifest = build_manifest(
                mode="apply-failed-reconciliation",
                source_stats=source_stats,
                destination_stats=after_stats,
                plan=plan,
                conflicts=conflicts
                + [
                    Conflict(
                        "destination_conflict",
                        None,
                        None,
                        f"pós-apply: {remaining_absent} inserts não reconciliaram",
                    )
                ],
                ready=False,
                written=written,
            )
            return 2, manifest

        manifest = build_manifest(
            mode="apply",
            source_stats=source_stats,
            destination_stats=after_stats,
            plan=plan,
            conflicts=conflicts,
            ready=True,
            written=written,
        )
        return 0, manifest
    finally:
        plugins.close()
        core.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugins-dsn", required=True)
    parser.add_argument("--core-dsn", required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist inserts in one transaction (default: dry-run, no writes)",
    )
    args = parser.parse_args(argv)

    try:
        code, manifest = run_migration(
            plugins_dsn=args.plugins_dsn,
            core_dsn=args.core_dsn,
            apply=args.apply,
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "mode": "error",
                    "error": str(exc.__class__.__name__),
                    "detail": str(exc)[:300],
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 3

    print(json.dumps(manifest, indent=2, default=str))
    return code


if __name__ == "__main__":
    sys.exit(main())
