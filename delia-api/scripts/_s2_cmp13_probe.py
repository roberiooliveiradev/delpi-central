#!/usr/bin/env python3
"""S2 residual probe: run the real cmp_13/cmp_19 turns and dump
per-invoke status — needed to classify the battery v2 failures
(owner invoked but no COMPLETED cap)."""
import json
import sys
import time

sys.path.insert(0, "/app/scripts")
sys.path.insert(0, "/app")

_WANTED = sys.argv[1:]
sys.argv[1:] = []  # eval modules parse argv at import time

from local_orchestration_reliability_eval import (
    _compose,
    _find_orchestrator,
    _mint_bearer,
    _run_turn,
    _context,
    DOC211_CORPUS,
)
import logging

from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    unbind_subject_bearer,
)


def main() -> None:
    wanted = _WANTED or ["cmp_13", "cmp_19"]
    handler, _guarded, _mcp = _compose()
    orch = _find_orchestrator(handler)
    bearer = _mint_bearer()

    providers = orch._providers
    if hasattr(providers, "values"):
        providers = dict(providers)
    invokes = []
    for pid, provider in providers.items():
        real = provider.invoke

        def make(real_invoke, pid):
            def wrapper(capability, arguments, **kw):
                cid = getattr(capability, "capability_id", "") or getattr(
                    capability, "remote_name", ""
                )
                try:
                    outcome = real_invoke(capability, arguments, **kw)
                except Exception as exc:  # noqa: BLE001
                    invokes.append(
                        {
                            "cap": cid,
                            "args": {
                                k: str(v)[:80]
                                for k, v in (arguments or {}).items()
                            },
                            "status": "EXC:" + type(exc).__name__,
                            "detail": str(exc)[:200],
                        }
                    )
                    raise
                structured = getattr(outcome, "structured", None) or {}
                invokes.append(
                    {
                        "cap": cid,
                        "args": {
                            k: str(v)[:80]
                            for k, v in (arguments or {}).items()
                        },
                        "status": getattr(
                            getattr(outcome, "status", None), "value",
                            getattr(outcome, "status", None),
                        ),
                        "is_error": bool(getattr(outcome, "is_error", False)),
                        "err_code": structured.get("error_code")
                        or structured.get("code"),
                        "recoverable": structured.get("recoverable"),
                        "msg": str(structured.get("message", ""))[:160],
                    }
                )
                return outcome

            return wrapper

        provider.invoke = make(real, pid)

    for sc in DOC211_CORPUS:
        if sc.sid not in wanted:
            continue
        stage_log = logging.Handler()
        stage_log.emit = lambda record: None
        activity = []
        out = _run_turn(handler, sc, bearer, stage_log, activity)
        print(
            json.dumps(
                {
                    "scenario": sc.sid,
                    "error": out["error"],
                    "grounding": out["grounding"],
                    "content_head": out["content"][:200],
                    "invokes": invokes[-6:],
                },
                ensure_ascii=False,
            )[:3000]
        )
        invokes.clear()


if __name__ == "__main__":
    main()
