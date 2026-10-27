#!/usr/bin/env python3
"""WP4 — stage-local A/B: production vs experimental instruction on
the EXACT captured native_assessment dispatch surfaces.

Loads every unique dispatched <target_capability_group> surface
recorded by the doc-159 diagnostic checkpoint, then replays each
surface REPS times under instruction A (production v23, verbatim)
and instruction B (experimental fixture), interleaved A,B,A,B… per
surface for temporal balance. Same model, same payload bytes —
only instruction_content differs.

Instruction B is read from the evidence fixture
(native-assessment-instruction-b.txt) copied into the container at
/tmp/. Nothing is written to runtime config.
"""

import hashlib
import json
import os
import sys
import uuid

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from scripts.r4_authenticated_resume_eval import _compose  # noqa: E402
from scripts.semantic_fidelity_eval import (  # noqa: E402
    _find_orchestrator,
)
from scripts.assessment_foreign_diag_eval import _verdict  # noqa: E402
from app.application.capability_provision.orchestration import (  # noqa: E402
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    SELECTION_INSTRUCTION_VERSION,
    _lineage,
)
from app.application.model_invocation.contracts import (  # noqa: E402
    EpistemicClass,
    ModelInvocationId,
    ModelInvocationRequest,
)

REPS = 5
CKPT = "/tmp/assessment_foreign_ckpt.jsonl"
B_PATH = "/tmp/native-assessment-instruction-b.txt"
OUT_PATH = os.environ.get(
    "EVAL_OUT", "/tmp/assessment_ab_stagelocal.json"
)


def _unique_surfaces():
    out = {}
    for line in open(CKPT):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        blk = (d.get("dispatch_blocks") or {}).get(
            NATIVE_ASSESSMENT_INSTRUCTION_ID
        ) or {}
        text = blk.get("text")
        sha = blk.get("sha")
        if not text or sha in out:
            continue
        nat = (d.get("natural") or {}).get("assessment") or {}
        out[sha] = {
            "surface_sha": sha,
            "scenario": d["scenario"],
            "target_group": nat.get("target_group"),
            "oracle_verdict": nat.get("oracle_verdict"),
            "natural_decision": nat.get("decision"),
            "text": text,
        }
    return list(out.values())


def _call(orch, surface, instruction):
    req = ModelInvocationRequest(
        invocation_id=ModelInvocationId(str(uuid.uuid4())),
        model_ref=orch._model_ref,  # noqa: SLF001
        prior_context=(),
        input_text=surface,
        task_purpose_id=NATIVE_ASSESSMENT_INSTRUCTION_ID,
        output_schema_id=NATIVE_ASSESSMENT_INSTRUCTION_ID,
        output_schema_version=SELECTION_INSTRUCTION_VERSION,
        expected_fields=("status",),
        instruction_lineage=_lineage(
            NATIVE_ASSESSMENT_INSTRUCTION_ID,
            instruction,
            SELECTION_INSTRUCTION_VERSION,
        ),
        instruction_content=instruction,
        timeout_seconds=60,
        declared_epistemic_class=EpistemicClass.HYPOTHESIS,
        untrusted_external_metadata={
            "interaction_surface": "delia-mfe",
            "input_kind": "native_assessment",
        },
    )
    try:
        res = orch._invoke_model.execute(req)  # noqa: SLF001
        prop = res.structured_output or {}
        return prop.get("status") or "EMPTY"
    except Exception as exc:
        return "ERR:" + getattr(exc, "code", type(exc).__name__)


def main() -> int:
    surfaces = _unique_surfaces()
    print("UNIQUE_SURFACES:", len(surfaces), flush=True)

    instr_a = json.load(
        open("config/orchestration_instructions.delpi.json")
    )["instructions"][NATIVE_ASSESSMENT_INSTRUCTION_ID]
    instr_b = open(B_PATH).read()
    print(
        "A_SHA", hashlib.sha256(instr_a.encode()).hexdigest()[:16],
        "B_SHA", hashlib.sha256(instr_b.encode()).hexdigest()[:16],
        flush=True,
    )

    handler, guarded, mcp = _compose()
    orch = _find_orchestrator(handler)

    results = []
    for s in surfaces:
        rec = {
            "surface_sha": s["surface_sha"],
            "scenario": s["scenario"],
            "target_group": s["target_group"],
            "oracle_verdict": s["oracle_verdict"],
            "natural_decision": s["natural_decision"],
            "A": [],
            "B": [],
        }
        for rep in range(REPS):
            rec["A"].append(_call(orch, s["text"], instr_a))
            rec["B"].append(_call(orch, s["text"], instr_b))
        results.append(rec)
        print(
            "SURF", s["scenario"], s["oracle_verdict"],
            "nat:", s["natural_decision"],
            "A:", rec["A"], "B:", rec["B"],
            flush=True,
        )

    with open(OUT_PATH, "w") as fh:
        json.dump(
            {
                "instruction_a_sha": hashlib.sha256(
                    instr_a.encode()
                ).hexdigest()[:16],
                "instruction_b_sha": hashlib.sha256(
                    instr_b.encode()
                ).hexdigest()[:16],
                "results": results,
                "model_call_detail": guarded.calls,
            },
            fh,
            ensure_ascii=False,
        )
    print("WROTE", OUT_PATH, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
