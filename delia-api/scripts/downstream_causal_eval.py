#!/usr/bin/env python3
"""Downstream causal characterization — doc 158 harness.

Four cumulative diagnostic arms (TEST-HARNESS-ONLY overrides, real
published identifiers, real catalog objects, real AuthZ everywhere
downstream of the controlled boundary):

  A natural     — full chain unmodified
  B good_group  — _select_group returns the oracle group key
  C good_cap    — B + capability selectors return the oracle
                  ProviderCapability from the live group object
  D good_args   — C + _build_arguments returns contract-valid
                  oracle arguments for the oracle capability

Each arm isolates the first uncontrolled downstream stage. Nothing is
persisted to the live catalog; membership/schema/AuthZ checks run
unchanged on every arm.

Interleaving: rep -> arm -> scenario for temporal balance.
"""

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
    _spy_invokes,
    _spy_propose,
    _StageLog,
    classify,
)
from app.infrastructure.auth.subject_bearer import (  # noqa: E402
    bind_subject_bearer,
    unbind_subject_bearer,
)

REPS = 5
OUT_PATH = os.environ.get(
    "EVAL_OUT", "/tmp/downstream_causal_runs.json"
)
ARMS = ("A", "B", "C", "D")

# Per-scenario oracle triple — real published ids only.
# (group_key, cap_remote_name, contract-valid reference args)
ORACLE = {
    "biz_bala3": ("openapi:delpi", "delpi.search_products",
                  {"description": "terminal bala"}),
    "biz_o2_2": ("openapi:delpi", "delpi.search_products",
                 {"description": "terminal O2"}),
    "biz_pino": ("openapi:delpi", "delpi.search_products",
                 {"description": "terminal pino"}),
    "biz_code": ("openapi:delpi", "delpi.get_product_summary",
                 {"code": "10080092"}),
    "nom_colloq": ("openapi:delpi", "delpi.search_products",
                   {"description": "ilhós"}),
    "nom_technical": ("openapi:delpi", "delpi.search_products",
                      {"description": "TERM. BALA"}),
    "h_rec_abracadeira": ("openapi:delpi", "delpi.search_products",
                          {"description": "abraçadeira"}),
    "h_rec_espaguete": ("openapi:delpi", "delpi.search_products",
                        {"description": "espaguete"}),
    "h_rec_code2": ("openapi:delpi", "delpi.get_product_summary",
                    {"code": "10081004"}),
    "h_rec_qual": ("openapi:delpi", "delpi.search_products",
                   {"description": "terminal bala"}),
    "h_amb_broad": ("openapi:delpi", "delpi.search_products",
                    {"description": "terminal"}),
}

SCEN_IDS = list(ORACLE)


def _scenarios():
    by_id = {}
    for sc in list(base.CORPUS) + list(
        __import__(
            "scripts.instruction_conflict_eval",
            fromlist=["HOLDOUT"],
        ).HOLDOUT
    ):
        if sc.sid in ORACLE:
            by_id[sc.sid] = sc
    return [by_id[s] for s in SCEN_IDS if s in by_id]


# ---------------------------------------------------------------------
# Argument fidelity classifier (evaluation-only oracle rules — not
# production logic; records *why* an argument diverges semantically).
# ---------------------------------------------------------------------

def _classify_args(sc, args):
    """Return one eval category for the model-proposed arguments."""
    if args is None:
        return "ARGUMENT_REQUIRED_FIELD_MISSING"
    if not isinstance(args, dict) or not args:
        return "ARGUMENT_SCHEMA_INVALID"
    group, cap, ref = ORACLE.get(sc.sid, (None, None, {}))
    subject = (sc.expected_subject or "").strip().lower()
    if cap == "delpi.get_product_summary":
        code = str(args.get("code") or "").strip()
        if code == str(ref.get("code")):
            return "ARGUMENT_SEMANTICALLY_VALID"
        if code and code not in (sc.question or ""):
            return "ARGUMENT_FABRICATED_IDENTIFIER"
        return "ARGUMENT_SUBJECT_DISTORTION"
    # search_products family: subject must live in a searchable text
    # field, codes only when user supplied them.
    desc = str(args.get("description") or "").strip().lower()
    code = str(args.get("code") or "").strip()
    if code:
        if code in (sc.question or ""):
            return "ARGUMENT_WRONG_FIELD_BINDING"
        return "ARGUMENT_FABRICATED_IDENTIFIER"
    if subject and subject in desc:
        return "ARGUMENT_SEMANTICALLY_VALID"
    if desc:
        return "ARGUMENT_SUBJECT_DISTORTION"
    if not desc and not code:
        return "ARGUMENT_SCOPE_LOSS"
    return "ARGUMENT_SUBJECT_DISTORTION"


def _last_args_proposal(run):
    out = None
    for p in run.get("proposals") or ():
        if p.get("purpose", "").endswith(
            "capability_orchestration.arguments"
        ) and p.get("proposal") is not None:
            out = p["proposal"]
    return out


def _arm_stage_result(arm, sc, run, arg_eval):
    """First-divergent-stage under this arm, honouring CONTROLLED marks."""
    cls = run["classification"]
    proposals = {
        (p.get("purpose") or "").split(".")[-1]: p.get("proposal")
        for p in run.get("proposals") or ()
        if p.get("proposal") is not None
    }
    invoked_caps = {i["capability_id"] for i in run["invokes"]}
    grp_sel = proposals.get("select_group") or {}
    cap_sel = proposals.get("select_capability") or {}

    stage = {}
    if arm == "A":
        grp = grp_sel.get("capability_group_id")
        stage["group"] = (
            "CONTROLLED" if False else
            ("CORRECT" if grp == "openapi:delpi" else "WRONG")
        )
        cap = (
            cap_sel.get("remote_name")
            if cap_sel.get("applicable") is True
            else None
        )
        oracle_cap = ORACLE[sc.sid][1]
        stage["capability"] = (
            "CORRECT" if cap == oracle_cap else "WRONG"
        ) if (grp == "openapi:delpi" or cap) else "NOT_REACHED"
    else:
        stage["group"] = "CONTROLLED"
        if arm in ("C", "D"):
            stage["capability"] = "CONTROLLED"
        else:
            cap = (
                cap_sel.get("remote_name")
                if cap_sel.get("applicable") is True
                else None
            )
            oracle_cap = ORACLE[sc.sid][1]
            stage["capability"] = (
                "CORRECT"
                if cap == oracle_cap
                else ("WRONG" if cap else "NOT_REACHED")
            )
    stage["arguments"] = (
        "CONTROLLED" if arm == "D" else arg_eval
    )
    if invoked_caps:
        bad = [
            i for i in run["invokes"]
            if sc.allowed_caps
            and i["capability_id"] not in sc.allowed_caps
        ]
        stage["invoke"] = (
            "WRONG" if bad else
            ("OK" if all(
                i["status"] == "COMPLETED" for i in run["invokes"]
            ) else "FAILED")
        )
    else:
        stage["invoke"] = "NOT_REACHED"
    return stage, cls


def _spy_invokes_all(providers):
    """Wrap every provider.invoke — record success AND raised errors.

    The base spy only captures successful returns; provider errors
    (401/403 → AUTHZ_DENIED, transport failures) raised through the
    adapter are otherwise invisible to stage attribution.
    """
    captured: list[dict] = []
    for pid, provider in providers.items():
        real = provider.invoke

        def make(real_invoke, pid):
            def wrapper(capability, arguments, **kw):
                try:
                    outcome = real_invoke(capability, arguments, **kw)
                except Exception as exc:
                    captured.append(
                        {
                            "provider": pid,
                            "capability_id": getattr(
                                capability, "capability_id", ""
                            ),
                            "remote_name": getattr(
                                capability, "remote_name", ""
                            ),
                            "arg_keys": sorted(
                                (arguments or {}).keys()
                            ),
                            "status": "ERROR:"
                            + str(
                                getattr(exc, "code", None)
                                or type(exc).__name__
                            ),
                        }
                    )
                    raise
                captured.append(
                    {
                        "provider": pid,
                        "capability_id": getattr(
                            capability, "capability_id", ""
                        ),
                        "remote_name": getattr(
                            capability, "remote_name", ""
                        ),
                        "arg_keys": sorted(
                            (arguments or {}).keys()
                        ),
                        "status": getattr(
                            getattr(outcome, "status", None),
                            "value",
                            str(getattr(outcome, "status", "")),
                        ),
                    }
                )
                return outcome

            return wrapper

        provider.invoke = make(real, pid)
    return captured


def main() -> int:
    bearer = _mint_bearer()
    handler, guarded, mcp = _compose()
    orch = _find_orchestrator(handler)
    proposals = _spy_propose(orch)
    invokes = _spy_invokes_all(orch._providers)
    scenarios = _scenarios()
    if len(scenarios) != len(SCEN_IDS):
        missing = set(SCEN_IDS) - {s.sid for s in scenarios}
        print("MISSING SCENARIOS:", missing, flush=True)

    # ---- per-run control state consulted by the wrappers.
    # engaged[] records WHICH controls actually fired this run — a
    # CONTROLLED mark is only honest when the wrapper engaged (the
    # presented group set can legitimately exclude the oracle group
    # on non-operational admission paths).
    state = {"arm": "A", "oracle": None, "engaged": set()}

    real_sg = orch._select_group  # noqa: SLF001
    real_scap = orch._select_capability  # noqa: SLF001
    real_scap_g = orch._select_capability_with_goal  # noqa: SLF001
    real_bargs = orch._build_arguments  # noqa: SLF001

    def _oracle_cap(group, remote):
        return next(
            (
                c
                for c in group.capabilities
                if c.remote_name == remote
            ),
            None,
        )

    def sg(input_text, groups, *a, **kw):
        oracle = state["oracle"]
        if state["arm"] != "A" and oracle and oracle[0] in groups:
            state["engaged"].add("group")
            return ("selected", oracle[0])
        return real_sg(input_text, groups, *a, **kw)

    def scap(input_text, group, *a, **kw):
        oracle = state["oracle"]
        if state["arm"] in ("C", "D") and oracle:
            cap = _oracle_cap(group, oracle[1])
            if cap is not None:
                state["engaged"].add("capability")
                return ("selected", cap)
        return real_scap(input_text, group, *a, **kw)

    def scap_g(input_text, group, *a, **kw):
        oracle = state["oracle"]
        if state["arm"] in ("C", "D") and oracle:
            cap = _oracle_cap(group, oracle[1])
            if cap is not None:
                state["engaged"].add("capability")
                return ("selected", cap, None)
        return real_scap_g(input_text, group, *a, **kw)

    def bargs(input_text, descriptor, *a, **kw):
        oracle = state["oracle"]
        if state["arm"] == "D" and oracle and (
            getattr(descriptor, "remote_name", None) == oracle[1]
        ):
            state["engaged"].add("arguments")
            return dict(oracle[2]), ()
        return real_bargs(input_text, descriptor, *a, **kw)

    orch._select_group = sg  # noqa: SLF001
    orch._select_capability = scap  # noqa: SLF001
    orch._select_capability_with_goal = scap_g  # noqa: SLF001
    orch._build_arguments = bargs  # noqa: SLF001

    # ---- oracle ground truth (authorized READ once per scenario)
    oracle_cache = {}
    for sc in scenarios:
        if sc.oracle_query and sc.sid not in oracle_cache:
            oracle_cache[sc.sid] = _fetch_oracle_records(
                orch._providers, sc.oracle_query, bearer
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

    ckpt_path = os.environ.get(
        "EVAL_CHECKPOINT", "/tmp/downstream_causal_ckpt.jsonl"
    )
    done_keys = set()
    if os.path.exists(ckpt_path):
        for line in open(ckpt_path):
            try:
                d = json.loads(line)
                done_keys.add(
                    (d["scenario"], d["arm"], d["run"])
                )
            except (ValueError, KeyError):
                continue
    print(
        "RESUME: %d completed runs found" % len(done_keys),
        flush=True,
    )
    ckpt = open(ckpt_path, "a")

    runs = []
    for rep in range(REPS):
        for arm in ARMS:
            for sc in scenarios:
                if (sc.sid, arm, rep) in done_keys:
                    continue
                state["arm"] = arm
                state["oracle"] = ORACLE[sc.sid]
                state["engaged"] = set()
                # Fresh bearer per turn — subject JWT TTL is 300s and
                # raised provider 401s are invisible to the spy.
                bearer = _mint_bearer()
                proposals.clear()
                invokes.clear()
                stage_log = _StageLog()
                out = _run_turn(handler, sc, bearer, stage_log)
                run = {
                    "scenario": sc.sid,
                    "arm": arm,
                    "run": rep,
                    **out,
                    "stages": stage_log.records,
                    "proposals": list(proposals),
                    "invokes": list(invokes),
                    "controls_engaged": sorted(state["engaged"]),
                    "oracle_data": oracle_cache.get(sc.sid),
                }
                run["classification"] = classify(sc, run)
                ap = _last_args_proposal(run)
                arg_eval = (
                    "CONTROLLED"
                    if arm == "D"
                    else _classify_args(
                        sc, (ap or {}).get("arguments")
                    )
                )
                run["argument_eval"] = arg_eval
                stage, _ = _arm_stage_result(arm, sc, run, arg_eval)
                run["arm_stages"] = stage
                runs.append(run)
                ckpt.write(
                    json.dumps(
                        run, ensure_ascii=False
                    ) + "\n"
                )
                ckpt.flush()
                print(
                    json.dumps(
                        {
                            "s": sc.sid,
                            "arm": arm,
                            "r": rep,
                            "out": run["classification"]["outcome"],
                            "first": run["classification"][
                                "first_divergent"
                            ],
                            "arm_stages": stage,
                            "cap": run["classification"].get(
                                "chosen_cap"
                            ),
                            "inv": run["classification"].get(
                                "invoked_caps"
                            ),
                            "ms": out["elapsed_ms"],
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )

    ckpt.close()
    # authoritative run set = full checkpoint (covers resumed runs)
    all_runs = [
        json.loads(line)
        for line in open(ckpt_path)
        if line.strip()
    ]
    stats = {
        "model_calls": sum(guarded.counts.values()),
        "in_units": sum(
            c.get("in_units") or 0 for c in guarded.calls
        ),
        "out_units": sum(
            c.get("out_units") or 0 for c in guarded.calls
        ),
    }
    with open(OUT_PATH, "w") as fh:
        json.dump(
            {
                "arms": ARMS,
                "oracle": ORACLE,
                "scenarios": [s.sid for s in scenarios],
                "stats": stats,
                "runs": all_runs,
            },
            fh,
            ensure_ascii=False,
        )
    print(
        "TOTAL:", len(all_runs), "stats:", stats, flush=True
    )
    return 0


if __name__ == "__main__":
    rc = 1
    for attempt in range(12):
        try:
            rc = main()
            break
        except Exception as exc:  # resume-safe retry
            print(
                "RETRY %d after %r"
                % (attempt + 1, exc),
                flush=True,
            )
            time.sleep(10)
    sys.exit(rc)
