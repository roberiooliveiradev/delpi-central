#!/usr/bin/env python3
"""DELIA-C3-GROUP-SELECTION-INSTRUCTION-SEMANTIC-CONFLICT-EVAL-01.

Controlled A/B harness over the *content* of one instruction entry —
``delia.capability_orchestration.select_group`` — with production code
and the active instruction resource untouched.

Experiment seam (evaluation only, never production): after composing
the real handler, ``SELECT_GROUP_INSTRUCTION_FILE`` (env) replaces the
text of that single entry inside the in-process ``_instructions``
mapping of the already-composed orchestrator. The versioned resource
on disk, every other instruction, the catalog builder, AuthZ,
PREPARE/ACT and the model remain identical across variants.

Usage (inside the eval container)::

    SELECT_GROUP_INSTRUCTION_FILE=/tmp/instr_B.txt \
    EVAL_CORPUS=base EVAL_TAG=B_base \
    python3 scripts/instruction_conflict_eval.py 5

Env:
    SELECT_GROUP_INSTRUCTION_FILE  optional path with the variant text
                                   (absent = canonical v23, variant A)
    EVAL_CORPUS                    ``base`` (doc-154 12-scenario subset)
                                   or ``holdout`` (unseen variants)
    EVAL_TAG                       output suffix /tmp/instr_eval_<tag>.json
    argv[1]                        repetitions per scenario (default 5)
    argv[2]                        optional comma scenario filter
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/app")

from scripts import semantic_fidelity_eval as base  # noqa: E402
from scripts.semantic_fidelity_eval import (  # noqa: E402
    DISCOVERY_CAPS,
    GUIDE_CAPS,
    PRODUCT_CAPS,
    STOCK_CAPS,
    Scenario,
    _a,
    _product,
    _u,
)

REPETITIONS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
SCENARIO_FILTER = (
    set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
)
CORPUS_MODE = os.environ.get("EVAL_CORPUS", "base")
EVAL_TAG = os.environ.get("EVAL_TAG", f"{CORPUS_MODE}_run")
INSTRUCTION_FILE = os.environ.get("SELECT_GROUP_INSTRUCTION_FILE")

SELECT_GROUP_ID = "delia.capability_orchestration.select_group"

BASE_SUBSET = {
    "biz_bala3", "biz_code", "biz_o2_2", "biz_pino", "cmp_legit",
    "disc_candidate", "disc_exec", "guide_term", "neg_inject",
    "neg_nobiz", "nom_colloq", "nom_technical",
}

# Holdout — never used to write variant B; covers records with other
# colloquial/technical subjects, explicit codes, qualifiers, doc asks,
# broad/ambiguous asks and conversational negatives.
HOLDOUT = [
    _product(
        "h_rec_abracadeira",
        "traga dois exemplos de abraçadeira cadastrados",
        "abraçadeira",
        0,
    ),
    _product(
        "h_rec_espaguete",
        "me mostre exemplos de espaguete para fiação",
        "espaguete",
        0,
    ),
    Scenario(
        sid="h_rec_code2",
        question="consulte o produto de código 10081004",
        family="records",
        needs_owner=True,
        oracle_kind="records",
        expected_subject="10081004",
        allowed_caps=frozenset(
            PRODUCT_CAPS | {"delpi.get_product_summary"}
        ),
        min_records=1,
        oracle_query=(
            "delpi.get_product_summary", {"code": "10081004"}
        ),
    ),
    _product(
        "h_rec_qual",
        "busque terminais bala para cabo de 4mm com estoque",
        "terminal bala",
        0,
    ),
    Scenario(
        sid="h_doc_denominacao",
        question="como a DELPI denomina terminais de compressão?",
        family="guidance",
        needs_owner=False,
        oracle_kind="guidance",
        allowed_caps=frozenset(GUIDE_CAPS | DISCOVERY_CAPS),
    ),
    Scenario(
        sid="h_doc_sigla",
        question="o que significa a sigla O2 na nomenclatura de "
        "terminais?",
        family="guidance",
        needs_owner=False,
        oracle_kind="guidance",
        allowed_caps=frozenset(GUIDE_CAPS | DISCOVERY_CAPS),
    ),
    _product(
        "h_amb_broad",
        "mostre terminais",
        "terminal",
        0,
    ),
    Scenario(
        sid="h_nobiz_thanks",
        question="obrigado, era só isso",
        family="negative",
        needs_owner=False,
        oracle_kind="conversational",
        allowed_caps=frozenset(),
        must_not_invoke=True,
    ),
]


def _corpus() -> list[Scenario]:
    if CORPUS_MODE == "holdout":
        return HOLDOUT
    return [s for s in base.CORPUS if s.sid in BASE_SUBSET]


def main() -> int:
    bearer = base._mint_bearer()
    handler, guarded, mcp = base._compose()
    orch = base._find_orchestrator(handler)

    # Experiment seam — single-instruction in-process override.
    fingerprint = None
    if INSTRUCTION_FILE:
        text = Path(INSTRUCTION_FILE).read_text(encoding="utf-8")
        orch._instructions[SELECT_GROUP_ID] = text  # noqa: SLF001
        import hashlib

        fingerprint = hashlib.sha256(text.encode()).hexdigest()[:16]
    print(
        f"VARIANT tag={EVAL_TAG} corpus={CORPUS_MODE} "
        f"instruction_override={INSTRUCTION_FILE or 'NONE(v23)'} "
        f"fp={fingerprint}",
        flush=True,
    )

    proposals = base._spy_propose(orch)
    invokes = base._spy_invokes(orch._providers)

    corpus = _corpus()
    oracle_cache: dict[str, dict] = {}
    for sc in corpus:
        if sc.oracle_query and sc.sid not in oracle_cache:
            oracle_cache[sc.sid] = base._fetch_oracle_records(
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

    runs = []
    model_calls_before = sum(guarded.counts.values())
    in_before = sum(c.get("in_units") or 0 for c in guarded.calls)
    out_before = sum(c.get("out_units") or 0 for c in guarded.calls)

    for sc in corpus:
        if SCENARIO_FILTER and sc.sid not in SCENARIO_FILTER:
            continue
        for rep in range(REPETITIONS):
            proposals.clear()
            invokes.clear()
            stage_log = base._StageLog()
            out = base._run_turn(handler, sc, bearer, stage_log)
            if any(
                "401" in str(i.get("status")) for i in invokes
            ) or (
                out.get("error") and "401" in str(out["error"])
            ):
                bearer = base._mint_bearer()
                proposals.clear()
                invokes.clear()
                stage_log = base._StageLog()
                out = base._run_turn(handler, sc, bearer, stage_log)
            run = {
                "scenario": sc.sid,
                "run": rep,
                "variant": EVAL_TAG,
                **out,
                "stages": stage_log.records,
                "proposals": list(proposals),
                "invokes": list(invokes),
                "oracle_data": oracle_cache.get(sc.sid),
            }
            cls = base.classify(sc, run)
            run["classification"] = cls
            runs.append(run)
            print(
                json.dumps(
                    {
                        "s": sc.sid,
                        "r": rep,
                        "out": cls["outcome"],
                        "first": cls["first_divergent"],
                        "g": out["grounding"].split(".")[-1],
                        "grp": cls["chosen_group"],
                        "cap": cls["chosen_cap"],
                        "caps": cls["invoked_caps"],
                        "hits": cls["oracle_hits"],
                        "ms": out["elapsed_ms"],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    summary = {
        "executions": len(runs),
        "model_calls": (
            sum(guarded.counts.values()) - model_calls_before
        ),
        "input_tokens": (
            sum(c.get("in_units") or 0 for c in guarded.calls)
            - in_before
        ),
        "output_tokens": (
            sum(c.get("out_units") or 0 for c in guarded.calls)
            - out_before
        ),
        "variant": EVAL_TAG,
        "instruction_fingerprint": fingerprint,
    }
    with open(f"/tmp/instr_eval_{EVAL_TAG}.json", "w") as fh:
        json.dump(
            {"summary": summary, "runs": runs},
            fh,
            ensure_ascii=False,
            indent=1,
        )
    print("SUMMARY:", json.dumps(summary), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
