#!/usr/bin/env python3
"""One-turn arm-D stage debug — emits orchestration stage= lines."""
import json
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s %(message)s",
    stream=sys.stderr,
)
for noisy in (
    "urllib3",
    "requests",
    "httpx",
    "httpcore",
    "asyncio",
    "charset_normalizer",
):
    logging.getLogger(noisy).setLevel(logging.WARNING)

sys.path.insert(0, "/app")

from scripts.r4_authenticated_resume_eval import _compose  # noqa: E402
from scripts import semantic_fidelity_eval as base  # noqa: E402
from scripts.semantic_fidelity_eval import (  # noqa: E402
    _find_orchestrator,
    _mint_bearer,
    _run_turn,
    _StageLog,
    _spy_propose,
    _spy_invokes,
)

ORACLE = (
    "openapi:delpi",
    "delpi.search_products",
    {"description": "terminal bala"},
)


def main() -> int:
    bearer = _mint_bearer()
    handler, guarded, mcp = _compose()
    orch = _find_orchestrator(handler)
    proposals = _spy_propose(orch)
    invokes = _spy_invokes(orch._providers)

    real_sg = orch._select_group
    real_scap = orch._select_capability
    real_scap_g = orch._select_capability_with_goal
    real_bargs = orch._build_arguments

    def sg(t, g, *a, **k):
        if ORACLE[0] in g:
            print("FORCED group ->", ORACLE[0], flush=True)
            return ("selected", ORACLE[0])
        return real_sg(t, g, *a, **k)

    def scap(t, g, *a, **k):
        cap = next(
            (c for c in g.capabilities if c.remote_name == ORACLE[1]),
            None,
        )
        if cap is not None:
            print("FORCED cap ->", ORACLE[1], flush=True)
            return ("selected", cap)
        return real_scap(t, g, *a, **k)

    def scap_g(t, g, *a, **k):
        cap = next(
            (c for c in g.capabilities if c.remote_name == ORACLE[1]),
            None,
        )
        if cap is not None:
            print("FORCED capG ->", ORACLE[1], flush=True)
            return ("selected", cap, None)
        return real_scap_g(t, g, *a, **k)

    def bargs(t, d, *a, **k):
        if getattr(d, "remote_name", None) == ORACLE[1]:
            print("FORCED args ->", ORACLE[2], flush=True)
            return dict(ORACLE[2]), ()
        return real_bargs(t, d, *a, **k)

    orch._select_group = sg
    orch._select_capability = scap
    orch._select_capability_with_goal = scap_g
    orch._build_arguments = bargs

    # Also force admission to operational so the owner-surface path
    # (delpi offered) is exercised deterministically — harness only.
    real_adm = getattr(
        orch, "_classify_interaction_admission", None
    ) or getattr(orch, "_admission", None)
    for name in dir(orch):
        if "admission" in name and name.startswith("_"):
            print("ADMISSION-METHOD-CANDIDATE:", name)
    if real_adm is not None:
        print("ADMISSION-WRAPPED:", real_adm)

    sc = next(s for s in base.CORPUS if s.sid == "biz_bala3")
    sl = _StageLog()
    out = _run_turn(handler, sc, bearer, sl)
    print("PROPOSALS:", [p["purpose"].split(".")[-1]
                          for p in proposals])
    print("INVOKES:", invokes)
    print(
        "OUT:",
        json.dumps(
            {k: out[k] for k in ("error", "grounding", "limitations")},
            ensure_ascii=False,
        ),
    )
    print("CONTENT:", out["content"][:300])
    return 0


if __name__ == "__main__":
    sys.exit(main())
