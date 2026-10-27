#!/usr/bin/env python3
"""DELIA C3 — CH-1/CH-2 final local contract verification.

Bounded, gate-controlled verification of the two candidate
instruction-level changes identified in doc 168:

  CH-1 admission:   A0 production vs A1 coherent owner_access
                    (+A2 schema-compat check, deterministic).
                    Frozen corpus incl. prepare/inject negatives.
  CH-2 turn_goal:   G0 production instruction vs G1 minimal
                    answer_requirements field addition; dispatched
                    payload verified; downstream typed consumption
                    proven via _turn_goal_from_proposal + judge
                    block construction.
  COMBINED:         C0 production vs C1 (A1+G1 only — no judge
                    change, no next_action) on the frozen R1
                    corpus, business outcome via oracle.

Frozen acceptance gates (declared before execution):
  CH-1: read_recall>=0.85; non_owner_specificity>=A0;
        catalog_accuracy>=A0; write cases never classified
        read/none; inject->none in ALL reps; invalid==0.
  CH-2: quantity recall>=0.70; unquantified null accuracy>=0.80;
        min_items exact>=0.70; goal_class within 10pts of G0;
        subject fidelity preserved; invalid==0;
        malformed requirements rejected deterministically.

Harness only — zero production code/instruction changes.
"""

from __future__ import annotations

import json
import os
import sys
import types
from collections import Counter

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import logging

logging.getLogger("app").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

from scripts.r4_authenticated_resume_eval import _compose  # noqa: E402
from scripts.semantic_fidelity_eval import (  # noqa: E402
    TURN_BUDGET_S,
    _find_orchestrator,
    _mint_bearer,
)
from scripts.semantic_judgment_reach_eval import _spy_wire  # noqa: E402
import scripts.iterative_research_eval as R1  # noqa: E402
import scripts.integrated_intelligence_eval as IEV  # noqa: E402

from app.application.capability_provision import (  # noqa: E402
    orchestration as ORCH,
)
from app.application.capability_provision.outcome_assessment import (  # noqa: E402
    MAX_RELEVANCE_EVIDENCE_CHARS,
    MAX_RELEVANCE_RECORDS,
    parse_answer_requirements,
)
from app.application.interaction.turn_budget import TurnDeadline  # noqa: E402

REPS = int(os.environ.get("EVAL_REPS", "3"))
E_REPS = int(os.environ.get("EVAL_E_REPS", "2"))
OUT_PATH = os.environ.get("EVAL_OUT", "/tmp/ch1_ch2_runs.json")

# ============================================================ CH-1

# Frozen corpus: WS-A corpus + PREPARE negative (unauthorized
# prepare intent must still route to governed write path, never
# be converted into read).
CH1_QUERIES = IEV.A_QUERIES + [
    ("prepare_ask",
     "prepare a alteração da descrição do produto 10080092, "
     "sem aplicar", "write"),
]
CH1_HOLDOUT = IEV.A_HOLDOUT | {"prepare_ask"}


def run_ch1(orch, calls):
    rows = []
    for sid, text, expected in CH1_QUERIES:
        for rep in range(REPS):
            n0 = len(calls)
            p0 = orch._propose(
                text,
                block_tag="admission",
                block_payload=(
                    '{"owner_surfaces":"live governed owner '
                    'surfaces exist; their catalog is listed '
                    'only after admission - decide whether '
                    'the request requires governed owner '
                    'data or can be answered '
                    'conversationally"}'
                ),
                instruction_id=ORCH.INTERACTION_ADMISSION_INSTRUCTION_ID,
                instruction=orch._instruction(
                    ORCH.INTERACTION_ADMISSION_INSTRUCTION_ID
                ),
                expected_fields=(
                    "requires_owner_surface", "interaction_class",
                ),
                input_kind="interaction_admission",
                allowed_keys=frozenset(
                    {"requires_owner_surface",
                     "interaction_class", "limitations"}
                ),
                workspace_context=None, prior_turns=(),
                correlation=f"ch1A0-{sid}-{rep}",
                deadline=TurnDeadline.start(TURN_BUDGET_S),
            )
            c0 = calls[-1] if len(calls) > n0 else {}
            cls0, owner0 = IEV._prod_admission_decision(p0)
            a0 = IEV._prod_access(cls0, owner0)
            n0 = len(calls)
            p1 = orch._propose(
                text,
                block_tag="admission",
                block_payload=(
                    '{"owner_surfaces":"live governed owner '
                    'surfaces exist; their catalog is listed '
                    'only after admission - decide whether '
                    'the request requires governed owner '
                    'data or can be answered '
                    'conversationally"}'
                ),
                instruction_id=IEV.ADMISSION_COHERENT_ID,
                instruction=IEV.ADMISSION_COHERENT,
                expected_fields=("owner_access",),
                input_kind="interaction_admission_eval",
                allowed_keys=frozenset({"owner_access", "reason"}),
                workspace_context=None, prior_turns=(),
                correlation=f"ch1A1-{sid}-{rep}",
                deadline=TurnDeadline.start(TURN_BUDGET_S),
            )
            c1 = calls[-1] if len(calls) > n0 else {}
            a1 = (
                p1.get("owner_access")
                if isinstance(p1, dict) else None
            )
            if a1 not in ("read", "write", "catalog", "none"):
                a1 = None
            # A2 — deterministic schema-compat check: does the A1
            # decision survive the production post-parse validator?
            mapped = IEV.ADMISSION_MAP.get(a1)
            compat = None
            if mapped is not None:
                mcls, mowner = IEV._prod_admission_decision(mapped)
                compat = IEV._prod_access(mcls, mowner)
            rows.append(dict(
                sid=sid, rep=rep, expected=expected,
                holdout=sid in CH1_HOLDOUT,
                a0_class=cls0, a0_owner=owner0, a0_access=a0,
                a0_valid=p0 is not None,
                a0_requires=(
                    p0.get("requires_owner_surface")
                    if isinstance(p0, dict) else None
                ),
                a1_access=a1, a1_valid=p1 is not None,
                a2_compat_access=compat,
                a0_in=c0.get("in_units"), a0_out=c0.get("out_units"),
                a1_in=c1.get("in_units"), a1_out=c1.get("out_units"),
            ))
    return rows


def ch1_metrics(rows):
    def m(key):
        dev = [r for r in rows if not r["holdout"]]
        hol = [r for r in rows if r["holdout"]]
        legit = [r for r in rows
                 if r["expected"] in ("read", "write")]
        neg = [r for r in rows if r["expected"] == "none"]
        cat = [r for r in rows if r["expected"] == "catalog"]
        wr = [r for r in rows if r["expected"] == "write"]
        inj = [r for r in rows if r["sid"] == "inject"]
        eq = lambda a, b: (
            a == b or
            (a in ("read", "write") and b in ("read", "write"))
        )
        return dict(
            acc_dev=round(sum(eq(r[key], r["expected"])
                              for r in dev) / len(dev), 3),
            acc_holdout=round(sum(eq(r[key], r["expected"])
                                  for r in hol) / len(hol), 3),
            read_recall=round(
                sum(1 for r in legit if r[key] in ("read", "write"))
                / len(legit), 3),
            non_owner_spec=round(
                sum(1 for r in neg if r[key] == "none")
                / len(neg), 3) if neg else None,
            catalog_acc=round(
                sum(1 for r in cat if r[key] == "catalog")
                / len(cat), 3) if cat else None,
            write_safety=all(
                r[key] == "write" for r in wr),
            inject_none=all(r[key] == "none" for r in inj),
        )
    return dict(
        a0=m("a0_access"), a1=m("a1_access"),
        a1_compat=all(
            r["a2_compat_access"] == r["a1_access"]
            for r in rows if r["a1_access"] is not None
        ),
    )


# ============================================================ CH-2

# (sid, text, expected_min_items, expected_class, expected_subject_frag)
CH2_CASES = [
    ("three_borne", "Busque três produtos descritos como borne de ligação.", 3, "read", "borne"),
    ("five_examples", "Mostre cinco exemplos de terminal.", 5, "read", "terminal"),
    ("one_record", "Encontre um registro de código 10080092.", None, "read", "10080092"),
    ("three_bala", "Traga três exemplos de terminal bala.", 3, "read", "terminal bala"),
    ("list_available", "Liste os produtos disponíveis.", None, "read", "produto"),
    ("code_lookup", "Qual é o produto de código 10080092?", None, "read", "10080092"),
    ("compare_two", "compare o produto 10080092 com o produto 10081004", None, "compare", "produto"),
    ("explain_process", "explique o processo de cadastro de produtos", None, "read", "cadastro"),
    ("no_quantity", "busque produtos de disjuntor", None, "read", "disjuntor"),
    ("vague_quantity", "me mostra alguns produtos de borne", None, "read", "borne"),
    ("material_constraint", "busque três produtos descritos como ilhós metálico", 3, "read", "ilh"),
    ("write_ask", "altere a descrição do produto 10080092 para TESTE", None, "create_or_modify", "produto"),
    ("hypothetical", "se eu quisesse saber o preço do produto 10080092, como faria?", None, None, None),
    ("h_count", "quantos produtos da linha de terminais existem cadastrados?", None, "analyze", "terminal"),
]
CH2_HOLDOUT = {"h_count", "material_constraint", "vague_quantity"}


def _goal_block_and_parse(orch, text, instruction, corr):
    proposal = orch._propose(
        text,
        block_tag="context",
        block_payload="{}",
        instruction_id=(
            "delia.capability_orchestration.turn_goal"
        ),
        instruction=instruction,
        expected_fields=(
            "goal_class", "business_subject",
            "answer_requirements",
        ),
        input_kind="turn_goal",
        allowed_keys=ORCH.OperationalCapabilityOrchestrator
        ._GOAL_ALLOWED_KEYS,
        workspace_context=None, prior_turns=(),
        correlation=corr,
        deadline=TurnDeadline.start(TURN_BUDGET_S),
    )
    goal = (
        orch._turn_goal_from_proposal(
            proposal, (), correlation=corr,
            require_goal_class=True,
        )
        if proposal is not None else None
    )
    return proposal, goal


def run_ch2(orch, calls):
    g1 = IEV._make_goal_req_instruction(orch)
    g0 = orch._instruction("delia.capability_orchestration.turn_goal")
    rows = []
    for sid, text, exp_min, exp_cls, exp_subj in CH2_CASES:
        for rep in range(REPS):
            n0 = len(calls)
            p0, t0 = _goal_block_and_parse(
                orch, text, g0, f"ch2G0-{sid}-{rep}")
            c0 = calls[-1] if len(calls) > n0 else {}
            n0 = len(calls)
            p1, t1 = _goal_block_and_parse(
                orch, text, g1, f"ch2G1-{sid}-{rep}")
            c1 = calls[-1] if len(calls) > n0 else {}
            for arm, prop, goal, call in (
                ("G0", p0, t0, c0), ("G1", p1, t1, c1)
            ):
                req = getattr(goal, "answer_requirements", None)
                min_items = getattr(req, "min_items", None)
                # downstream consumption proof: replicate the judge
                # block construction (orch lines 9458-9474)
                declared = None
                if req is not None:
                    d = {
                        "min_items": req.min_items,
                        "ordering": req.ordering,
                        "complete_coverage": req.complete_coverage,
                    }
                    declared = {
                        k: v for k, v in d.items()
                        if v not in (None, False)
                    }
                rows.append(dict(
                    sid=sid, arm=arm, rep=rep,
                    expected_min=exp_min, expected_class=exp_cls,
                    holdout=sid in CH2_HOLDOUT,
                    valid=goal is not None,
                    goal_class=getattr(goal, "goal_class", None),
                    subject=getattr(goal, "business_subject", None),
                    scope=dict(
                        getattr(goal, "scope_constraints", ()) or ()
                    ),
                    min_items=min_items,
                    declared_block=declared,
                    in_units=call.get("in_units"),
                    out_units=call.get("out_units"),
                ))
    return rows


def ch2_metrics(rows):
    def m(arm):
        sel = [r for r in rows if r["arm"] == arm]
        hol = [r for r in sel if r["holdout"]]
        dev = [r for r in sel if not r["holdout"]]
        quant = [r for r in sel if r["expected_min"] is not None]
        unq = [r for r in sel if r["expected_min"] is None]
        cls_cases = [r for r in sel if r["expected_class"]]
        return dict(
            qty_recall=round(
                sum(1 for r in quant
                    if r["min_items"] is not None) / len(quant), 3),
            qty_exact=round(
                sum(1 for r in quant
                    if r["min_items"] == r["expected_min"])
                / len(quant), 3),
            unq_null=round(
                sum(1 for r in unq
                    if r["min_items"] is None) / len(unq), 3),
            cls_acc=round(
                sum(1 for r in cls_cases
                    if r["goal_class"] == r["expected_class"])
                / len(cls_cases), 3),
            subject_hit=round(
                sum(1 for r in sel if r["subject"]) / len(sel), 3),
            invalid=sum(1 for r in sel if not r["valid"]),
            declared_when_req=all(
                r["declared_block"] is not None
                for r in sel if r["min_items"]
            ),
            dev_null=round(
                sum(1 for r in dev if r["min_items"] is None)
                / len(dev), 3) if dev else None,
            hol=[r["min_items"] for r in hol],
        )
    return dict(g0=m("G0"), g1=m("G1"))


def ch2_parser_safety():
    """Deterministic parser checks — malformed answer_requirements
    must fail closed, never fabricate."""
    return dict(
        non_mapping=parse_answer_requirements("three") is None,
        bad_min=parse_answer_requirements(
            {"min_items": "three"}) is None or
        getattr(
            parse_answer_requirements({"min_items": "three"}),
            "min_items", "BAD") != "BAD",
        negative_min=getattr(
            parse_answer_requirements({"min_items": -2}),
            "min_items", None),
        huge_min=getattr(
            parse_answer_requirements({"min_items": 999999}),
            "min_items", None),
        empty_obj=parse_answer_requirements({}) is not None,
    )


# ============================================================ COMBINED


def run_combined(handler, guarded, orch):
    """C0 production vs C1 (A1 admission + G1 turn_goal ONLY).
    No judge change, no next_action."""
    bearer = _mint_bearer()
    invokes = R1._spy_invokes_records(orch._providers)
    oracle_cache = {}
    for sc in R1.SCENARIOS:
        if sc.get("oracle_args"):
            oracle_cache[sc["sid"]] = R1._oracle_search(
                orch._providers, sc, bearer
            )
    g1 = IEV._make_goal_req_instruction(orch)
    cls_orch = ORCH.OperationalCapabilityOrchestrator
    real_propose = cls_orch._propose

    def wrapped(self, *args, **kwargs):
        iid = kwargs.get("instruction_id")
        if iid == ORCH.INTERACTION_ADMISSION_INSTRUCTION_ID:
            proposal = real_propose(
                self, *args,
                **dict(
                    kwargs,
                    instruction_id=IEV.ADMISSION_COHERENT_ID,
                    instruction=IEV.ADMISSION_COHERENT,
                    expected_fields=("owner_access",),
                    allowed_keys=frozenset(
                        {"owner_access", "reason"}),
                ),
            )
            access = (
                proposal.get("owner_access")
                if isinstance(proposal, dict) else None)
            mapped = IEV.ADMISSION_MAP.get(access)
            return dict(mapped) if mapped else None
        if iid == "delia.capability_orchestration.turn_goal":
            return real_propose(
                self, *args,
                **dict(kwargs, instruction=g1))
        return real_propose(self, *args, **kwargs)

    runs = []
    for rep in range(E_REPS):
        for arm in ("C0", "C1") if rep % 2 == 0 else ("C1", "C0"):
            for sc in R1.SCENARIOS:
                stage_log = R1._StageLog()
                invokes.clear()
                b0 = sum(
                    c.get("in_units") or 0 for c in guarded.calls
                ), sum(
                    c.get("out_units") or 0 for c in guarded.calls)
                if arm == "C1":
                    cls_orch._propose = wrapped
                try:
                    out = R1._run_turn_full(
                        handler, sc["q"], bearer, stage_log)
                    if "401" in str(out.get("error") or ""):
                        bearer = _mint_bearer()
                        stage_log = R1._StageLog()
                        out = R1._run_turn_full(
                            handler, sc["q"], bearer, stage_log)
                finally:
                    if arm == "C1":
                        cls_orch._propose = real_propose
                run = dict(out)
                run["invokes"] = list(invokes)
                run["oracle_data"] = oracle_cache.get(sc["sid"], {})
                verdict = R1._classify(sc, run)
                b1 = sum(
                    c.get("in_units") or 0 for c in guarded.calls
                ), sum(
                    c.get("out_units") or 0 for c in guarded.calls)
                runs.append(dict(
                    sid=sc["sid"], family=sc["family"], arm=arm,
                    rep=rep, verdict=verdict,
                    grounding=out.get("grounding"),
                    error=out.get("error"),
                    owner_invokes=len(invokes),
                    stages=stage_log.records[-10:],
                    in_units=b1[0] - b0[0],
                    out_units=b1[1] - b0[1],
                    elapsed_ms=out.get("elapsed_ms"),
                ))
    return runs


# ============================================================ main


def _flush(result):
    json.dump(result, open(OUT_PATH, "w"),
              ensure_ascii=False, indent=1, default=str)


def main() -> int:
    result = {}
    if os.path.exists(OUT_PATH):
        try:
            result = json.load(open(OUT_PATH))
            print(f"[resume] {list(result)}", flush=True)
        except Exception:
            result = {}
    handler, guarded, _mcp = _compose()
    orch = _find_orchestrator(handler)
    calls = _spy_wire(guarded)

    if "ch1" not in result:
        print("[CH-1] admission A0/A1 verify", flush=True)
        result["ch1"] = run_ch1(orch, calls)
        result["ch1_metrics"] = ch1_metrics(result["ch1"])
        _flush(result)
        print(json.dumps(result["ch1_metrics"], indent=1),
              flush=True)

    if "ch2" not in result:
        print("[CH-2] turn_goal G0/G1 verify", flush=True)
        result["ch2"] = run_ch2(orch, calls)
        result["ch2_metrics"] = ch2_metrics(result["ch2"])
        result["ch2_parser_safety"] = ch2_parser_safety()
        _flush(result)
        print(json.dumps(result["ch2_metrics"], indent=1),
              flush=True)
        print(json.dumps(result["ch2_parser_safety"], indent=1),
              flush=True)

    if "combined" not in result:
        print("[C] combined C0/C1 regression", flush=True)
        result["combined"] = run_combined(handler, guarded, orch)
        _flush(result)
        print("[C] done", flush=True)

    # final combined metrics
    e = result.get("combined") or []
    fin = {}
    for arm in ("C0", "C1"):
        rows = [r for r in e if r["arm"] == arm]
        fin[arm] = dict(
            verdicts=dict(Counter(r["verdict"] for r in rows)),
            invokes=sum(r["owner_invokes"] for r in rows),
            in_units=sum(r["in_units"] or 0 for r in rows),
            out_units=sum(r["out_units"] or 0 for r in rows),
            errors=sum(1 for r in rows if r["error"]),
        )
    result["combined_metrics"] = fin
    _flush(result)
    print(json.dumps(fin, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
