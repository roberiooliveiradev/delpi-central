#!/usr/bin/env python3
"""Manual MCP catalog sync CLI (doc 216, E3) — eval/operator tool.

Captures live ``tools/list`` from an authorized MCP owner, normalizes,
hashes, diffs against the ACTIVE persisted snapshot and (on --apply)
stores and activates a new immutable version atomically.

  --owner mcp:caio --dry-run        diff only, no writes (default)
  --owner mcp:caio --apply          capture + activate atomically
  --owner mcp:caio --history        version list
  --owner mcp:caio --verify         ACTIVE hash integrity check
  --owner mcp:caio --activate-version N   controlled rollback/pin

Never persists tokens, credentials or business data.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.application.specialist_interop.errors import (
    SpecialistInteropError,
)
from app.domain.specialist_interop.rules import (
    specialist_ref_or_none,
)
from app.composition.root_composer import (
    _wire_delegated_credential_provider,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.interoperability.config import (
    specialist_connections_from_settings,
)
from app.infrastructure.interoperability.mcp.adapter import (
    McpSpecialistAdapter,
)
from app.infrastructure.interoperability.mcp.catalog_store import (
    McpCatalogStore,
    contract_hash,
    diff_tools,
)


def _tools_payload(descs) -> list[dict]:
    """RemoteToolDescriptor -> persisted tools/list-shaped entry."""
    out = []
    for d in descs:
        entry = {
            "name": d.remote_name,
            "title": d.title,
            "description": d.description,
            "inputSchema": dict(d.input_schema)
            if d.input_schema
            else None,
            "annotations": dict(d.annotations) if d.annotations else None,
        }
        if d.operation_class:
            entry["_meta"] = {"delpi/toolClass": d.operation_class}
        out.append(entry)
    return out


def _live_capture(owner: str, settings: Settings):
    ref = specialist_ref_or_none(owner.replace("mcp:", ""))
    if ref is None:
        raise SystemExit(f"unknown specialist {owner}")
    connections = specialist_connections_from_settings(settings)
    adapter = McpSpecialistAdapter(
        connections,
        credential_provider=_wire_delegated_credential_provider(
            settings, connections
        ),
    )
    timeout = float(os.getenv("DELIA_MCP_TIMEOUT_SECONDS") or 20)
    descs = adapter.list_remote_tools(ref, timeout_seconds=timeout)
    return _tools_payload(descs), ref


def _store(settings: Settings) -> McpCatalogStore:
    db = settings.mcp_catalog_db
    if not db:
        raise SystemExit(
            "DELIA_MCP_CATALOG_DB unset — point it at the snapshot store"
        )
    return McpCatalogStore(db)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--owner", required=True, help="e.g. mcp:caio")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--activate-version", type=int, default=None)
    ap.add_argument("--actor", default="operator:mcp_catalog_sync")
    args = ap.parse_args()

    owner_key = args.owner.replace("mcp:", "")
    owner_id = owner_key
    settings = Settings()
    store = _store(settings)

    if args.history:
        for r in store.history(owner_id):
            print(
                f"v{r['catalog_version']} {r['status']} "
                f"tools={r['tool_count']} hash={r['contract_hash'][:12]}"
            )
        return 0
    if args.verify:
        ok = store.verify(owner_id)
        print("VERIFY", "PASS" if ok else "FAIL")
        return 0 if ok else 1

    if args.activate_version is not None:
        snap = store.activate(
            owner_id, "global", args.activate_version, actor=args.actor
        )
        print(
            f"ACTIVATED v{snap['catalog_version']} "
            f"hash={snap['contract_hash'][:12]}"
        )
        return 0

    live_tools, ref = _live_capture(args.owner, settings)
    live_hash = contract_hash(live_tools)
    active = store.active(owner_id)

    diff = (
        diff_tools(active["tools"], live_tools)
        if active
        else {"added": [t["name"] for t in live_tools], "removed": [],
              "changed": []}
    )
    print(
        f"owner={owner_id} live_tools={len(live_tools)} "
        f"live_hash={live_hash[:12]}"
    )
    print(
        f"active={'v' + str(active['catalog_version']) if active else 'none'} "
        f"diff added={diff['added']} removed={diff['removed']} "
        f"changed={diff['changed']}"
    )

    if args.apply:
        if active and active["contract_hash"] == live_hash:
            print("IDEMPOTENT: no change — ACTIVE unchanged")
            return 0
        snap = store.add_snapshot(
            owner_id,
            live_tools,
            actor=args.actor,
            status="VALIDATED",
            provenance={"endpoint_owner": owner_id},
            change_summary=diff,
        )
        store.activate(
            owner_id, "global", snap["catalog_version"], actor=args.actor
        )
        print(f"APPLIED+ACTIVATED v{snap['catalog_version']}")
        return 0

    print("DRY-RUN: no persistent change (use --apply)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SpecialistInteropError as exc:
        print(f"SYNC_FAIL code={exc.code} {exc}", file=sys.stderr)
        sys.exit(2)
