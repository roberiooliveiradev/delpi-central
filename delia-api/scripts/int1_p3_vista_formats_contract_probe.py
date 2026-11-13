#!/usr/bin/env python3
"""Eval-only P3 contract probe — VISTA visualization-formats surfaces.

Bounded, read-only, sanitized (no tokens/raw secrets printed). Reuses the
real governed path: subject session → bound bearer → composed MCP adapter
→ call_remote_tool. Answers, for subject ti_delpi:

  1. get_context action=catalog — authorized for this read subject or
     TV_WRITE-gated? Which format vocabularies does it publish?
  2. read playlist.list — playlists visible to the subject.
  3. read playlist.get — block ``type`` values actually in use.
  4. read data_route.search — per-route ``allowedDisplayModes``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import traceback
from pathlib import Path

_APP_ROOT = "/app"
sys.path.insert(0, _APP_ROOT)


def _load_script(module_name: str, filename: str):
    path = Path(_APP_ROOT) / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_native = _load_script(
    "native_mcptoolset_direct_eval", "native_mcptoolset_direct_eval.py"
)

from app.domain.specialist_interop.model import SpecialistRef  # noqa: E402
from app.infrastructure.auth.subject_bearer import (  # noqa: E402
    bind_subject_bearer,
    unbind_subject_bearer,
)

_compose = _native._compose
acquire_subject_access_session = _native.acquire_subject_access_session

VISTA = SpecialistRef(
    specialist_id="vista", display_name="VISTA", owner_ref="tv-dashboard-api"
)


def _structured(out) -> dict:
    s = getattr(out, "structured", None)
    return s if isinstance(s, dict) else {}


def _call(mcp, remote: str, args: dict, seq: int) -> dict:
    try:
        out = mcp.call_remote_tool(
            VISTA,
            remote,
            args,
            correlation_id=f"p3-probe-{seq}",
            timeout_seconds=30.0,
        )
        data = _structured(out)
        return {
            "call": f"{remote}",
            "args_keys": sorted(args),
            "is_error": bool(getattr(out, "is_error", False)),
            "status": data.get("status"),
            "code": data.get("code") or data.get("error_code"),
            "error_kind": data.get("error_kind"),
            "data": data.get("data") if isinstance(data.get("data"), dict) else data,
        }
    except Exception as exc:  # noqa: BLE001 — probe reports
        return {
            "call": f"{remote}",
            "args_keys": sorted(args),
            "exception": f"{type(exc).__name__}: {exc}"[:400],
        }


def main() -> int:
    session = acquire_subject_access_session()
    binding = bind_subject_bearer(session.access_token)
    report: dict = {"subject": "eval_portal_subject"}
    try:
        _handler, mcp = _compose()

        # 1. catalog (TV_WRITE-gated per owner code?)
        cat = _call(mcp, "get_context", {"action": "catalog"}, 1)
        d = cat.get("data") or {}
        cat["catalog_keys"] = sorted(d)[:40] if isinstance(d, dict) else None
        fmt = (d.get("displayFormatCatalog") or []) if isinstance(d, dict) else []
        cat["displayFormatCatalog_n"] = len(fmt)
        cat["displayFormatCatalog_sample"] = [
            e.get("formatId") for e in fmt[:8] if isinstance(e, dict)
        ]
        ops = (d.get("operations") or {}) if isinstance(d, dict) else {}
        vocab_keys = set()
        for row in ops.values() if isinstance(ops, dict) else []:
            if isinstance(row, dict):
                vocab_keys.update((row.get("fieldVocabulary") or {}).keys())
        cat["fieldVocabulary_keys"] = sorted(vocab_keys)[:20]
        block_vocab = None
        for row in ops.values() if isinstance(ops, dict) else []:
            if isinstance(row, dict):
                fv = row.get("fieldVocabulary") or {}
                for key in ("type", "block.type"):
                    if isinstance(fv.get(key), list):
                        block_vocab = fv[key]
                        break
            if block_vocab:
                break
        cat["block_type_vocabulary"] = block_vocab
        if isinstance(d, dict):
            cat["data"] = {k: "<truncated>" for k in list(d)[:10]}
        report["catalog"] = cat

        # 2. playlist.list
        pl = _call(mcp, "read", {"entity": "playlist", "action": "list"}, 2)
        d = pl.get("data") or {}
        items = (d.get("items") or []) if isinstance(d, dict) else []
        pl["playlist_count"] = len(items)
        pl["first_playlist_id"] = (
            str(items[0].get("playlistId") or items[0].get("id") or "")
            if items and isinstance(items[0], dict)
            else None
        )
        pl["data"] = "<truncated>"
        report["playlist_list"] = pl

        # 3. playlist.get on first playlist → block types in use
        if pl.get("first_playlist_id"):
            pg = _call(
                mcp,
                "read",
                {
                    "entity": "playlist",
                    "action": "get",
                    "ref": pl["first_playlist_id"],
                },
                3,
            )
            d = pg.get("data") or {}
            block_types = set()

            def _walk(node):
                if isinstance(node, dict):
                    bt = node.get("type")
                    if isinstance(bt, str) and bt:
                        block_types.add(bt)
                    for v in node.values():
                        _walk(v)
                elif isinstance(node, list):
                    for v in node:
                        _walk(v)

            _walk(d)
            pg["block_types_in_use"] = sorted(block_types)
            pg["data"] = "<truncated>"
            report["playlist_get"] = pg

        # 4. data_route.search → allowedDisplayModes per route
        dr = _call(
            mcp,
            "read",
            {
                "entity": "data_route",
                "action": "search",
                "filters": {"query": "indicadores de produção", "limit": 8},
            },
            4,
        )
        d = dr.get("data") or {}
        items = (d.get("items") or []) if isinstance(d, dict) else []
        dr["route_count"] = len(items)
        dr["routes_allowedDisplayModes"] = sorted(
            {
                m
                for it in items
                if isinstance(it, dict)
                for m in (it.get("allowedDisplayModes") or [])
            }
        )
        dr["data"] = "<truncated>"
        report["data_route_search"] = dr

    finally:
        unbind_subject_bearer(binding)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("PROBE_DONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        raise
