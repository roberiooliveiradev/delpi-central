#!/usr/bin/env python3
"""WP6 — end-to-end A/B: production v23 vs experimental instruction B
on the `native_assessment` stage only, injected in memory at the
stage boundary (`orchestrator._instruction`), never persisted, never
touching the active v23 resource or any other instruction.

Arms: A = production instruction, B = experimental fixture.
Everything else in the governed chain stays natural — admission,
goal, group, capability, foreign selection, arguments, owner
invocation, relevance, synthesis. Interleaved rep -> arm -> scenario.

Fresh subject bearer per turn (JWT TTL 300s). Checkpointed per run.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.r4_authenticated_resume_eval import _compose  # noqa: E402
from scripts import semantic_fidelity_eval as base  # noqa: E402
from scripts.semantic_fidelity_eval import (  # noqa: E402
    _fetch_oracle_records,
    _find_orchestrator,
    _mint_bearer,
    _run_turn,
    _spy_propose,
    _StageLog,
    classify,
)
from scripts.downstream_causal_eval import _spy_invokes_all  # noqa: E402
from scripts.assessment_foreign_diag_eval import (  # noqa: E402
    CORPUS_IDS,
    RECORD_ORACLE,
    SUFFICIENT,
    _scenarios,
    _verdict,
)
from app.application.capability_provision.orchestration import (  # noqa: E402
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
)
from app.infrastructure.auth.subject_bearer import (  # noqa: E402
    bind_subject_bearer,
    unbind_subject_bearer,
)

REPS = 5
OUT_PATH = os.environ.get("EVAL_OUT", "/tmp/instruction_ab_runs.json")
CKPT_PATH = os.environ.get(
    "EVAL_CHECKPOINT", "/tmp/instruction_ab_ckpt.jsonl"
)
B_PATH = "/tmp/native-assessment-instruction-b.txt"
ARMS = ("A", "B")

# Pre-declared holdout (frozen before first B run): scenarios never
# consulted while drafting the fixture — different record families,
# doc asks, broad/ambiguous asks.
HOLDOUT = frozenset(
    {
        "h_rec_abracadeira",
        "h_rec_qual",
        "h_amb_broad",
        "h_doc_denominacao",
        "h_doc_sigla",
    }
)


def main() -> int:
    bearer = _mint_bearer()
    handler, guarded, mcp = _compose()
    orch = _find_orchestrator(handler)
    proposals = _spy_propose(orch)
    invokes = _spy_invokes_all(orch._providers)
    scenarios = _scenarios()

    bd = bind_subject_bearer(bearer)
    try:
        live_groups, surface_failures = orch._groups(  # noqa: SLF001
            "catalog_snapshot"
        )
    finally:
        unbind_subject_bearer(bd)
    catalog_snapshot = {
        k: sorted(c.capability_id for c in g.capabilities)
        for k, g in live_groups.items()
    }
    print(
        "CATALOG:",
        json.dumps({k: len(v) for k, v in catalog_snapshot.items()}),
        "FAILURES:", surface_failures,
        flush=True,
    )

    instr_a = orch._instruction(  # noqa: SLF001
        NATIVE_ASSESSMENT_INSTRUCTION_ID
    )
    instr_b = open(B_PATH).read()
    a_sha = hashlib.sha256(instr_a.encode()).hexdigest()[:16]
    b_sha = hashlib.sha256(instr_b.encode()).hexdigest()[:16]
    print("A_SHA", a_sha, "B_SHA", b_sha, flush=True)

    # ---- in-memory instruction injection at the assessment stage
    state = {"arm": "A", "sc": None, "groups": None, "natural": {}}
    real_instruction = orch._instruction  # noqa: SLF001
    real_sg = orch._select_group  # noqa: SLF001
    real_assess = orch._assess_native_path  # noqa: SLF001
    real_self = orch._select_foreign_capability  # noqa: SLF001

    def instruction(key):
        text = real_instruction(key)
        if (
            state["arm"] == "B"
            and key == NATIVE_ASSESSMENT_INSTRUCTION_ID
        ):
            return instr_b
        return text

    def sg(input_text, groups, *a, **kw):
        state["groups"] = groups
        return real_sg(input_text, groups, *a, **kw)

    def _group_key(group):
        groups = state.get("groups") or {}
        for key, g in groups.items():
            if g is group:
                return key
        ids = {c.capability_id for c in group.capabilities}
        for key, g in groups.items():
            if {c.capability_id for c in g.capabilities} == ids:
                return key
        return None

    def assess(input_text, group, descriptor, *a, **kw):
        decision = real_assess(input_text, group, descriptor, *a, **kw)
        key = _group_key(group)
        sc = state["sc"]
        state["natural"]["assessment"] = {
            "decision": decision,
            "target_group": key,
            "target_capability": getattr(
                descriptor, "capability_id", ""
            ),
            "oracle_verdict": (
                _verdict(sc.sid, key)
                if sc is not None
                else "inconclusive"
            ),
        }
        return decision

    def selforeign(
        input_text, groups, target_group_key, mode, *a, **kw
    ):
        natural = real_self(
            input_text, groups, target_group_key, mode, *a, **kw
        )
        state["natural"]["foreign_selection"] = {
            "mode": mode,
            "target_group": target_group_key,
            "selected": (
                {
                    "group": natural[0],
                    "capability_id": natural[1].capability_id,
                }
                if natural
                else None
            ),
        }
        return natural

    orch._instruction = instruction  # noqa: SLF001
    orch._select_group = sg  # noqa: SLF001
    orch._assess_native_path = assess  # noqa: SLF001
    orch._select_foreign_capability = selforeign  # noqa: SLF001

    # ---- record oracles (authorized READ once per scenario)
    oracle_cache = {}
    for sc in scenarios:
        q = RECORD_ORACLE.get(sc.sid)
        if q and sc.sid not in oracle_cache:
            oracle_cache[sc.sid] = _fetch_oracle_records(
                orch._providers, q, bearer
            )
    print(
        "ORACLES:",
        json.dumps(
            {
                k: {"codes": len(v["codes"]), "status": v["status"]}
                for k, v in oracle_cache.items()
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    done_keys = set()
    runs = []
    if os.path.exists(CKPT_PATH):
        for line in open(CKPT_PATH):
            try:
                d = json.loads(line)
                done_keys.add((d["scenario"], d["arm"], d["run"]))
                runs.append(d)
            except (ValueError, KeyError):
                continue
    print("RESUME: %d completed runs" % len(done_keys), flush=True)
    ckpt = open(CKPT_PATH, "a")

    for rep in range(REPS):
        for arm in ARMS:
            for sc in scenarios:
                if (sc.sid, arm, rep) in done_keys:
                    continue
                state["arm"] = arm
                state["sc"] = sc
                state["groups"] = None
                state["natural"] = {}
                bearer = _mint_bearer()
                proposals.clear()
                invokes.clear()
                stage_log = _StageLog()
                call_lo = len(guarded.calls)
                out = _run_turn(handler, sc, bearer, stage_log)
                turn_calls = guarded.calls[call_lo:]
                run = {
                    "scenario": sc.sid,
                    "holdout": sc.sid in HOLDOUT,
                    "arm": arm,
                    "run": rep,
                    "model_calls": len(turn_calls),
                    "tokens_in": sum(
                        c.get("in_units") or 0 for c in turn_calls
                    ),
                    "tokens_out": sum(
                        c.get("out_units") or 0 for c in turn_calls
                    ),
                    "latency_ms": sum(
                        c.get("ms") or 0 for c in turn_calls
                    ),
                    **out,
                    "stages": list(stage_log.records),
                    "proposals": list(proposals),
                    "invokes": list(invokes),
                    "natural": dict(state["natural"]),
                    "oracle_data": oracle_cache.get(sc.sid),
                }
                run["classification"] = classify(sc, run)
                runs.append(run)
                ckpt.write(
                    json.dumps(run, ensure_ascii=False) + "\n"
                )
                ckpt.flush()
                print(
                    "DONE %s%s %s r%d %s assess=%s foreign=%s "
                    "invokes=%s -> %s"
                    % (
                        sc.sid,
                        "[H]" if sc.sid in HOLDOUT else "",
                        arm,
                        rep,
                        run["classification"].get(
                            "first_divergent", "?"
                        ),
                        (state["natural"].get("assessment") or {})
                        .get("decision"),
                        (
                            (state["natural"].get(
                                "foreign_selection"
                            ) or {}).get("selected") or {}
                        ).get("capability_id"),
                        [i["capability_id"] for i in invokes][:5],
                        run["classification"].get("outcome", "?"),
                    ),
                    flush=True,
                )

    ckpt.close()
    with open(OUT_PATH, "w") as fh:
        json.dump(
            {
                "catalog_snapshot": catalog_snapshot,
                "instruction_a_sha": a_sha,
                "instruction_b_sha": b_sha,
                "holdout": sorted(HOLDOUT),
                "runs": runs,
                "model_calls": dict(guarded.counts),
                "model_call_detail": guarded.calls,
            },
            fh,
            ensure_ascii=False,
        )
    print("WROTE", OUT_PATH, "runs:", len(runs), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
