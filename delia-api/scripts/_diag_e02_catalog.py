"""E02 catalog diagnosis with optional subject bearer (no secrets printed)."""
from __future__ import annotations

import json
import os
import sys

from app.application.interaction.turn_budget import TurnDeadline
from app.composition.root_composer import create_application
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    current_subject_bearer,
)


def main() -> None:
    token = os.environ.get("DIAG_SUBJECT_BEARER") or ""
    app = create_application()
    handler = app.config.get("INTERACTION_TURN_HANDLER")
    if handler is None:
        print(json.dumps({"error": "no_turn_handler"}))
        sys.exit(2)
    # Reach orchestrator via handler internals when available.
    orch = getattr(handler, "_capability_orchestration", None)
    gates = getattr(orch, "_gates", None) if orch is not None else None
    if gates is None and hasattr(orch, "_project_semantic_tool_catalog"):
        gates = orch

    print(
        json.dumps(
            {
                "handler_type": type(handler).__name__,
                "orch_type": type(orch).__name__ if orch else None,
                "gates_type": type(gates).__name__ if gates else None,
                "bearer_bound_requested": bool(token),
            }
        )
    )
    if gates is None or not hasattr(gates, "_project_semantic_tool_catalog"):
        attrs = [a for a in dir(handler) if not a.startswith("__")]
        print(json.dumps({"handler_attrs": attrs[:80]}))
        sys.exit(3)

    from app.infrastructure.auth.subject_bearer import unbind_subject_bearer

    token_ctx = None
    if token:
        token_ctx = bind_subject_bearer(token)
    try:
        deadline = TurnDeadline.start(60.0)
        groups, failures = gates._groups("diag-e02", deadline)
        catalog = gates._project_semantic_tool_catalog(
            correlation="diag-e02",
            deadline=deadline,
            actor_user_id="diag",
        )
        by_owner: dict[str, int] = {}
        sample = []
        for entry in catalog:
            owner = str(entry.get("owner") or entry.get("provider_id") or "?")
            by_owner[owner] = by_owner.get(owner, 0) + 1
            if len(sample) < 25:
                sample.append(
                    {
                        "capability_id": entry.get("capability_id"),
                        "remote": entry.get("remote_name"),
                        "class": entry.get("operation_class"),
                        "owner": owner,
                        "desc": str(entry.get("description") or "")[:100],
                    }
                )
        print(
            json.dumps(
                {
                    "bearer_present": bool(current_subject_bearer()),
                    "group_count": len(groups),
                    "group_ids": list(groups.keys())[:40],
                    "failures": [str(f) for f in (failures or [])][:20],
                    "catalog_len": len(catalog),
                    "by_owner": by_owner,
                    "sample": sample,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        if token_ctx is not None:
            unbind_subject_bearer(token_ctx)


if __name__ == "__main__":
    main()
