#!/usr/bin/env python3
"""Native assessment & foreign selection contract/prompt-surface
diagnostic — doc 159 harness.

Read-only causal diagnostic (TEST-HARNESS-ONLY overrides). Captures
the EXACT dispatched model surface for every stage — the literal
``input_text`` + ``instruction_content`` carried by
``ModelInvocationRequest`` — plus natural stage decisions, so the
SOURCE -> PROJECTED -> DISPATCHED -> DECISION -> VALIDATED chain can
be audited for the two target stages:

  native_assessment   — is the selected target owner sufficient?
  foreign_selection   — which auxiliary foreign capability supplies
                        the legitimately required evidence?

Arms (WP5; stage-local, oracle-gated):

  A natural      — full chain unmodified.
  B good_ctx     — NOT RUN: the assessment block already carries every
                   field its contract declares (full target group
                   surface, turn_goal incl. business_subject,
                   relevance_feedback). Injecting further context would
                   require changing the productive interface; context
                   hypotheses are tested in WP8 variant replay instead.
  C good_assess  — when the contract oracle proves the SELECTED target
                   group is sufficient, a contract-valid assessment
                   ("sufficient") is returned at the stage boundary.
                   Nothing else is touched; downstream stays natural.
  D good_foreign — when the oracle proves foreign evidence is REALLY
                   required for the selected target, a legitimate,
                   live, authorized foreign capability is returned at
                   the stage boundary (enrichment mode only; the
                   corroboration contract is never overridden).

Interleaving: rep -> arm -> scenario for temporal balance.
Fresh subject bearer per turn (JWT TTL 300s).
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
from scripts.downstream_causal_eval import (  # noqa: E402
    _spy_invokes_all,
)
from scripts import instruction_conflict_eval as conflict  # noqa: E402
from app.application.capability_provision.orchestration import (  # noqa: E402
    _PATH_FOREIGN_CLASSES,
)
from app.infrastructure.auth.subject_bearer import (  # noqa: E402
    bind_subject_bearer,
    unbind_subject_bearer,
)

REPS = 5
OUT_PATH = os.environ.get(
    "EVAL_OUT", "/tmp/assessment_foreign_runs.json"
)
CKPT_PATH = os.environ.get(
    "EVAL_CHECKPOINT", "/tmp/assessment_foreign_ckpt.jsonl"
)
ARMS = ("A", "C", "D")

# -------------------------------------------------------------------
# Corpus — records, doc asks, comparison, discovery, security, cont.
# -------------------------------------------------------------------
CORPUS_IDS = (
    # business records — descriptive subjects (8)
    "biz_bala3",
    "biz_o2_2",
    "biz_code",
    "nom_colloq",
    "nom_technical",
    "h_rec_abracadeira",
    "h_rec_qual",
    "h_amb_broad",
    # documentation asks — guidance family (4)
    "guide_term",
    "guide_proc",
    "h_doc_denominacao",
    "h_doc_sigla",
    # comparison + discovery + continuity (3)
    "cmp_legit",
    "disc_exec",
    "cont_prior",
    # security / conversational negatives (3)
    "neg_write",
    "neg_inject",
    "neg_nobiz",
)

# -------------------------------------------------------------------
# Contract oracle — assessment verdict as a function of the SELECTED
# target group. SUFFICIENT = group whose own surface satisfies the
# goal end-to-end. The oracle derives from the real catalog: DELPI
# record search resolves descriptive subjects (oracle queries return
# records); TEO/VISTA guidance surfaces answer documentation asks.
# "inconclusive" is never invented — when no legit foreign capability
# exists for a miss, the verdict is still REQUIRED (the target cannot
# satisfy the goal alone), we just cannot repair it.
# -------------------------------------------------------------------
DELPI_OK = frozenset({"openapi:delpi", "mcp:davi"})
GUIDE_OK = frozenset({"mcp:teo", "mcp:vista"})

SUFFICIENT = {
    "biz_bala3": DELPI_OK,
    "biz_o2_2": DELPI_OK,
    "biz_code": DELPI_OK,
    "nom_colloq": DELPI_OK,
    "nom_technical": DELPI_OK,
    "h_rec_abracadeira": DELPI_OK,
    "h_rec_qual": DELPI_OK,
    "h_amb_broad": DELPI_OK,
    "cont_prior": DELPI_OK,
    "guide_term": GUIDE_OK,
    "guide_proc": GUIDE_OK,
    "h_doc_denominacao": GUIDE_OK,
    "h_doc_sigla": GUIDE_OK,
    "cmp_legit": DELPI_OK,
    "disc_exec": DELPI_OK,
    # negatives — no owner surface is contractually sufficient
    "neg_write": None,
    "neg_inject": DELPI_OK,  # record ask w/ injection payload
    "neg_nobiz": None,       # conversational — owner not required
}

# Legitimate foreign capability when the selected target CANNOT
# satisfy the goal alone. (group_key, remote_name) — must exist in
# the live surface and be READ/DISCOVERY-class.
LEGIT_FOREIGN = {
    "biz_bala3": ("openapi:delpi", "delpi.search_products"),
    "biz_o2_2": ("openapi:delpi", "delpi.search_products"),
    "biz_code": ("openapi:delpi", "delpi.get_product_summary"),
    "nom_colloq": ("openapi:delpi", "delpi.search_products"),
    "nom_technical": ("openapi:delpi", "delpi.search_products"),
    "h_rec_abracadeira": ("openapi:delpi", "delpi.search_products"),
    "h_rec_qual": ("openapi:delpi", "delpi.search_products"),
    "h_amb_broad": ("openapi:delpi", "delpi.search_products"),
    "cont_prior": ("openapi:delpi", "delpi.search_products"),
    "guide_term": ("mcp:teo", "teo.get_product_guide"),
    "guide_proc": ("mcp:teo", "teo.get_methodology_guide"),
    "h_doc_denominacao": ("mcp:teo", "teo.get_product_guide"),
    "h_doc_sigla": ("mcp:teo", "teo.get_product_guide"),
    # corroboration contract is forced by goal.comparison_requested —
    # no "independent second source" exists for same-owner records,
    # so no legitimate repair: observe only.
    "cmp_legit": None,
    "disc_exec": ("mcp:davi", "davi.discover_delpi_information"),
    "neg_write": None,
    "neg_inject": ("openapi:delpi", "delpi.search_products"),
    "neg_nobiz": None,
}

# record-family oracle queries (for outcome + classification)
RECORD_ORACLE = {
    "biz_bala3": ("delpi.search_products", {"description": "terminal bala"}),
    "biz_o2_2": ("delpi.search_products", {"description": "terminal O2"}),
    "biz_code": ("delpi.get_product_summary", {"code": "10080092"}),
    "nom_colloq": ("delpi.search_products", {"description": "ilhós"}),
    "nom_technical": ("delpi.search_products", {"description": "TERM. BALA"}),
    "h_rec_abracadeira": ("delpi.search_products", {"description": "abraçadeira"}),
    "h_rec_qual": ("delpi.search_products", {"description": "terminal bala"}),
    "h_amb_broad": ("delpi.search_products", {"description": "terminal"}),
    "cont_prior": ("delpi.search_products", {"description": "terminal bala"}),
}


def _scenarios():
    by_id = {
        sc.sid: sc for sc in list(base.CORPUS) + list(conflict.HOLDOUT)
    }
    return [by_id[s] for s in CORPUS_IDS]


def _verdict(sid, target_group_key):
    """Contract oracle for native_assessment — conditional on the
    target the chain actually selected (never on what it 'should'
    have selected)."""
    suff = SUFFICIENT.get(sid)
    if suff is None:
        return "not_applicable"
    if target_group_key in suff:
        return "sufficient"
    return "required"


# -------------------------------------------------------------------
# Dispatch spy — captures the EXACT ModelInvocationRequest surface
# (the serialized block the model effectively receives, not the
# pre-serialization object) plus usage and the raw proposal.
# -------------------------------------------------------------------
def _spy_dispatch(orch):
    store: list[dict] = []
    real = orch._invoke_model.execute  # noqa: SLF001

    def wrapper(request):
        started = time.monotonic()
        entry = {
            "purpose": request.task_purpose_id,
            "instruction_sha": hashlib.sha256(
                (request.instruction_content or "").encode()
            ).hexdigest()[:12],
            "instruction_chars": len(request.instruction_content or ""),
            "dispatched_sha": hashlib.sha256(
                (request.input_text or "").encode()
            ).hexdigest()[:12],
            "dispatched_chars": len(request.input_text or ""),
            "dispatched": request.input_text,
            "expected_fields": list(request.expected_fields or ()),
            "prior_context_n": len(request.prior_context or ()),
        }
        try:
            result = real(request)
        except Exception as exc:
            entry["error"] = getattr(
                exc, "code", type(exc).__name__
            )
            entry["ms"] = int((time.monotonic() - started) * 1000)
            store.append(entry)
            raise
        usage = getattr(result, "usage", None)
        entry.update(
            {
                "proposal": result.structured_output,
                "finish": str(getattr(result, "finish_status", "")),
                "in_units": getattr(usage, "input_units", None),
                "out_units": getattr(usage, "output_units", None),
                "ms": int((time.monotonic() - started) * 1000),
            }
        )
        store.append(entry)
        return result

    orch._invoke_model.execute = wrapper  # noqa: SLF001
    return store


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def main() -> int:
    bearer = _mint_bearer()
    handler, guarded, mcp = _compose()
    orch = _find_orchestrator(handler)
    proposals = _spy_propose(orch)
    invokes = _spy_invokes_all(orch._providers)
    dispatch = _spy_dispatch(orch)
    scenarios = _scenarios()

    # ---- live surface fingerprint (WP1 catalog snapshot)
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
        "FAILURES:",
        surface_failures,
        flush=True,
    )

    # ---- per-run control state consulted by the wrappers.
    state = {
        "arm": "A",
        "sc": None,
        "groups": None,
        "engaged": set(),
        "eligible": set(),
        "natural": {},
    }

    real_sg = orch._select_group  # noqa: SLF001
    real_assess = orch._assess_native_path  # noqa: SLF001
    real_self = orch._select_foreign_capability  # noqa: SLF001

    def sg(input_text, groups, *a, **kw):
        # Stash the turn's live group map so the assessment wrapper can
        # resolve the selected target group object back to its key.
        state["groups"] = groups
        return real_sg(input_text, groups, *a, **kw)

    def _group_key(group):
        groups = state.get("groups") or {}
        for key, g in groups.items():
            if g is group:
                return key
        # fallback: match on capability-id set (fresh objects per turn)
        ids = {c.capability_id for c in group.capabilities}
        for key, g in groups.items():
            if {c.capability_id for c in g.capabilities} == ids:
                return key
        return None

    def assess(input_text, group, descriptor, *a, **kw):
        natural = real_assess(input_text, group, descriptor, *a, **kw)
        key = _group_key(group)
        state["natural"]["assessment"] = {
            "decision": natural,
            "target_group": key,
            "target_capability": getattr(
                descriptor, "capability_id", ""
            ),
        }
        sc = state["sc"]
        verdict = (
            _verdict(sc.sid, key) if sc is not None else "inconclusive"
        )
        state["natural"]["assessment"]["oracle_verdict"] = verdict
        if state["arm"] == "C" and verdict == "sufficient":
            state["eligible"].add("assessment")
            if natural != "sufficient":
                state["engaged"].add("assessment")
                return "sufficient"
        return natural

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
        sc = state["sc"]
        verdict = (
            _verdict(sc.sid, target_group_key)
            if sc is not None
            else "inconclusive"
        )
        state["natural"]["foreign_selection"]["oracle_verdict"] = verdict
        if (
            state["arm"] == "D"
            and mode == "enrichment"
            and verdict == "required"
        ):
            legit = LEGIT_FOREIGN.get(sc.sid) if sc else None
            if legit and legit[0] in groups and (
                legit[0] != target_group_key
            ):
                cap = next(
                    (
                        c
                        for c in groups[legit[0]].capabilities
                        if c.remote_name == legit[1]
                    ),
                    None,
                )
                if (
                    cap is not None
                    and cap.operation_class in _PATH_FOREIGN_CLASSES
                ):
                    state["eligible"].add("foreign_selection")
                    state["engaged"].add("foreign_selection")
                    return (legit[0], cap)
        return natural

    orch._select_group = sg  # noqa: SLF001
    orch._assess_native_path = assess  # noqa: SLF001
    orch._select_foreign_capability = selforeign  # noqa: SLF001

    # ---- oracle ground truth (authorized READ once per scenario)
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
                state["engaged"] = set()
                state["eligible"] = set()
                state["natural"] = {}
                # Fresh bearer per turn — subject JWT TTL is 300s.
                bearer = _mint_bearer()
                proposals.clear()
                invokes.clear()
                dispatch.clear()
                stage_log = _StageLog()
                out = _run_turn(handler, sc, bearer, stage_log)
                run = {
                    "scenario": sc.sid,
                    "arm": arm,
                    "run": rep,
                    **out,
                    "stages": list(stage_log.records),
                    "proposals": [
                        {k: v for k, v in p.items() if k != "raw"}
                        for p in proposals
                    ],
                    "invokes": list(invokes),
                    "dispatch": [
                        {
                            k: v
                            for k, v in d.items()
                            if k != "dispatched"  # hashed below
                        }
                        for d in dispatch
                    ],
                    "dispatch_blocks": {
                        d["purpose"]: {
                            "sha": d["dispatched_sha"],
                            "chars": d["dispatched_chars"],
                            "text": (
                                d["dispatched"]
                                if d["purpose"]
                                in (
                                    "delia.capability_orchestration."
                                    "native_assessment",
                                    "delia.capability_orchestration."
                                    "foreign_selection",
                                )
                                else None
                            ),
                        }
                        for d in dispatch
                    },
                    "natural": dict(state["natural"]),
                    "controls_eligible": sorted(state["eligible"]),
                    "controls_engaged": sorted(state["engaged"]),
                    "oracle_data": oracle_cache.get(sc.sid),
                }
                run["classification"] = classify(sc, run)
                runs.append(run)
                ckpt.write(json.dumps(run, ensure_ascii=False) + "\n")
                ckpt.flush()
                print(
                    "DONE %s %s r%d %s assess=%s foreign=%s engaged=%s "
                    "verdict=%s invokes=%s -> %s"
                    % (
                        sc.sid,
                        arm,
                        rep,
                        run["classification"].get(
                            "first_divergent", "?"
                        ),
                        (state["natural"].get("assessment") or {}).get(
                            "decision"
                        ),
                        (
                            (state["natural"].get("foreign_selection")
                             or {}).get("selected") or {}
                        ).get("capability_id"),
                        sorted(state["engaged"]),
                        (state["natural"].get("assessment") or {}).get(
                            "oracle_verdict"
                        ),
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
