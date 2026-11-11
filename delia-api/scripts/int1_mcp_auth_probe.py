#!/usr/bin/env python3
"""Eval-only MCP auth probe for INT-1 harness (no LLM calls)."""

from __future__ import annotations

import sys
import traceback

import importlib.util
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
from app.infrastructure.config.settings import Settings  # noqa: E402

_compose = _native._compose
_subject_token = _native._subject_token

REFS = (
    SpecialistRef(
        specialist_id="davi", display_name="DAVI", owner_ref="api-delpi"
    ),
    SpecialistRef(
        specialist_id="teo",
        display_name="TEO",
        owner_ref="transformometro-api",
    ),
    SpecialistRef(
        specialist_id="vista",
        display_name="VISTA",
        owner_ref="tv-dashboard-api",
    ),
)


def main() -> int:
    settings = Settings()
    print(
        "enabled",
        {k: v for k, v in settings.mcp_specialist_enabled.items() if v},
    )
    print(
        "endpoints",
        {k: v for k, v in settings.mcp_specialist_endpoints.items() if v},
    )
    token = _subject_token()
    print("token_len", len(token or ""))
    binding = bind_subject_bearer(token)
    try:
        _handler, mcp = _compose()
        for ref in REFS:
            try:
                tools = mcp.list_remote_tools(ref, timeout_seconds=12.0)
                names = [getattr(t, "name", str(t)) for t in (tools or [])[:8]]
                print(
                    "LIST_OK",
                    ref.specialist_id,
                    "n",
                    len(tools or []),
                    "sample",
                    names,
                )
            except Exception as exc:  # noqa: BLE001 — probe reports
                print(
                    "LIST_FAIL",
                    ref.specialist_id,
                    type(exc).__name__,
                    exc,
                )
                traceback.print_exc()
    finally:
        unbind_subject_bearer(binding)
    print("PROBE_DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
