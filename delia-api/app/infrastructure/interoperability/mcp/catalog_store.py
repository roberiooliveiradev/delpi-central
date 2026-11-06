"""Versioned MCP capability-catalog snapshot store (doc 216, E2).

Eval-scoped SQLite persistence for the isolated SNAPSHOT_EXPERIMENT
variant. Immutable per-owner versions, content hash (SHA-256 over
canonicalized JSON), atomic ACTIVE pointer flip, history and rollback.

The store holds owner-published `tools/list` payloads — never
credentials, tokens or business data. Snapshot data is untrusted input:
consumers must treat stored descriptions/schemas as metadata, never as
authorization, instruction or business fact.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from typing import Any, Mapping, Sequence

SNAPSHOT_SCHEMA_VERSION = 1

STATUSES = frozenset(
    {"DRAFT", "CAPTURED", "VALIDATED", "ACTIVE", "RETIRED", "INVALID"}
)

_DDL = """
CREATE TABLE IF NOT EXISTS mcp_catalog_snapshots (
    owner_id        TEXT    NOT NULL,
    scope           TEXT    NOT NULL,
    catalog_version INTEGER NOT NULL,
    schema_version  INTEGER NOT NULL,
    contract_hash   TEXT    NOT NULL,
    status          TEXT    NOT NULL,
    tool_count      INTEGER NOT NULL,
    tools_json      TEXT    NOT NULL,
    change_summary  TEXT    NOT NULL DEFAULT '{}',
    provenance      TEXT    NOT NULL DEFAULT '{}',
    captured_at     REAL    NOT NULL,
    validated_at    REAL,
    activated_at    REAL,
    actor           TEXT    NOT NULL DEFAULT '',
    PRIMARY KEY (owner_id, scope, catalog_version)
);
CREATE TABLE IF NOT EXISTS mcp_catalog_active (
    owner_id        TEXT    NOT NULL,
    scope           TEXT    NOT NULL,
    catalog_version INTEGER NOT NULL,
    activated_at    REAL    NOT NULL,
    PRIMARY KEY (owner_id, scope)
);
"""


def canonicalize(payload: Any) -> str:
    """Deterministic JSON — key order and whitespace never matter."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def contract_hash(tools: Sequence[Mapping[str, Any]]) -> str:
    normalized = [
        {
            "name": t.get("name"),
            "title": t.get("title"),
            "description": t.get("description"),
            "inputSchema": t.get("inputSchema"),
            "outputSchema": t.get("outputSchema"),
            "annotations": t.get("annotations"),
            "_meta": t.get("_meta"),
        }
        for t in tools
    ]
    return hashlib.sha256(canonicalize(normalized).encode()).hexdigest()


def diff_tools(
    old: Sequence[Mapping[str, Any]], new: Sequence[Mapping[str, Any]]
) -> dict[str, list[str]]:
    """Semantic diff by tool — count alone never proves equality."""
    old_map = {t.get("name"): t for t in old}
    new_map = {t.get("name"): t for t in new}
    added = sorted(k for k in new_map if k not in old_map)
    removed = sorted(k for k in old_map if k not in new_map)
    changed = []
    for name in sorted(old_map.keys() & new_map.keys()):
        if canonicalize(old_map[name]) != canonicalize(new_map[name]):
            changed.append(name)
    return {"added": added, "removed": removed, "changed": changed}


class McpCatalogStore:
    """SQLite snapshot repository — one ACTIVE per (owner, scope)."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        # Per-thread connections — gunicorn gthread workers call the
        # catalog from threads other than the composing thread; sqlite
        # objects are never shared across threads. Each thread gets its
        # own connection; sqlite handles the file-level concurrency.
        self._local = threading.local()
        self._conn

    @property
    def _conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(
                self._db_path, isolation_level=None
            )
            conn.row_factory = sqlite3.Row
            conn.executescript(_DDL)
            self._local.conn = conn
        return conn

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    # ---- queries -----------------------------------------------------

    def active(self, owner_id: str, scope: str = "global") -> dict | None:
        row = self._conn.execute(
            "SELECT catalog_version FROM mcp_catalog_active "
            "WHERE owner_id=? AND scope=?",
            (owner_id, scope),
        ).fetchone()
        if row is None:
            return None
        return self.get_version(owner_id, scope, row["catalog_version"])

    def get_version(
        self, owner_id: str, scope: str, version: int
    ) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM mcp_catalog_snapshots "
            "WHERE owner_id=? AND scope=? AND catalog_version=?",
            (owner_id, scope, version),
        ).fetchone()
        return self._to_dict(row) if row else None

    def history(self, owner_id: str, scope: str = "global") -> list[dict]:
        rows = self._conn.execute(
            "SELECT owner_id, scope, catalog_version, status, "
            "tool_count, contract_hash, captured_at, activated_at "
            "FROM mcp_catalog_snapshots "
            "WHERE owner_id=? AND scope=? ORDER BY catalog_version",
            (owner_id, scope),
        ).fetchall()
        return [dict(r) for r in rows]

    def versions(self, owner_id: str, scope: str = "global") -> list[int]:
        return [r["catalog_version"] for r in self.history(owner_id, scope)]

    # ---- mutations ---------------------------------------------------

    def next_version(self, owner_id: str, scope: str) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(MAX(catalog_version),0)+1 AS v "
            "FROM mcp_catalog_snapshots WHERE owner_id=? AND scope=?",
            (owner_id, scope),
        ).fetchone()
        return int(row["v"])

    def add_snapshot(
        self,
        owner_id: str,
        tools: Sequence[Mapping[str, Any]],
        *,
        scope: str = "global",
        actor: str = "",
        status: str = "CAPTURED",
        provenance: Mapping[str, Any] | None = None,
        change_summary: Mapping[str, Any] | None = None,
    ) -> dict:
        """Append an immutable version. Idempotent: identical hash on
        the latest version returns it without writing a new one."""
        if status not in STATUSES:
            raise ValueError(f"invalid status {status}")
        tools_list = [dict(t) for t in tools]
        digest = contract_hash(tools_list)
        latest_v = self.versions(owner_id, scope)
        if latest_v:
            latest = self.get_version(owner_id, scope, latest_v[-1])
            if latest and latest["contract_hash"] == digest:
                return latest
        version = self.next_version(owner_id, scope)
        now = time.time()
        self._conn.execute(
            "INSERT INTO mcp_catalog_snapshots (owner_id, scope, "
            "catalog_version, schema_version, contract_hash, status, "
            "tool_count, tools_json, change_summary, provenance, "
            "captured_at, validated_at, actor) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                owner_id,
                scope,
                version,
                SNAPSHOT_SCHEMA_VERSION,
                digest,
                status,
                len(tools_list),
                canonicalize(tools_list),
                canonicalize(change_summary or {}),
                canonicalize(provenance or {}),
                now,
                now if status in {"VALIDATED", "ACTIVE"} else None,
                actor,
            ),
        )
        return self.get_version(owner_id, scope, version)

    def activate(
        self, owner_id: str, scope: str, version: int, *, actor: str = ""
    ) -> dict:
        """Atomic pointer flip — previous ACTIVE becomes RETIRED; an
        INVALID version can never be activated."""
        target = self.get_version(owner_id, scope, version)
        if target is None:
            raise ValueError(f"version {version} not found")
        if target["status"] == "INVALID":
            raise ValueError("invalid snapshot cannot be activated")
        now = time.time()
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE mcp_catalog_snapshots SET status='RETIRED' "
                "WHERE owner_id=? AND scope=? AND status='ACTIVE'",
                (owner_id, scope),
            )
            self._conn.execute(
                "INSERT OR REPLACE INTO mcp_catalog_active "
                "(owner_id, scope, catalog_version, activated_at) "
                "VALUES (?,?,?,?)",
                (owner_id, scope, version, now),
            )
            self._conn.execute(
                "UPDATE mcp_catalog_snapshots SET status='ACTIVE', "
                "activated_at=? WHERE owner_id=? AND scope=? AND "
                "catalog_version=?",
                (now, owner_id, scope, version),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return self.get_version(owner_id, scope, version)

    # ---- helpers -----------------------------------------------------

    def _to_dict(self, row: sqlite3.Row) -> dict:
        d = dict(row)
        d["tools"] = json.loads(d["tools_json"])
        d["change_summary"] = json.loads(d["change_summary"])
        d["provenance"] = json.loads(d["provenance"])
        return d

    def verify(self, owner_id: str, scope: str = "global") -> bool:
        """Recompute the ACTIVE hash — a tampered blob fails closed."""
        snap = self.active(owner_id, scope)
        if snap is None:
            return False
        return contract_hash(snap["tools"]) == snap["contract_hash"]
