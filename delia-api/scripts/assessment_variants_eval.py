#!/usr/bin/env python3
"""WP8 — controlled prompt-surface variants for native_assessment.

Replays the FALSE-POSITIVE population captured by the diagnostic
(oracle verdict == sufficient, natural decision ==
foreign_evidence_required) through in-memory model calls, one factor
at a time — SAME production instruction text, SAME model, only the
dispatched block presentation varies:

  V1 full_contract     — the block exactly as dispatched (replay
                         baseline; measures decision stability).
  V2 minimal_sufficient— only contract-permitted fields the decision
                         semantically needs: target_capability_id,
                         target_operation_class, capability ids +
                         operation_class + description, turn_goal.
                         Drops argument_keys/required/role noise.
  V3 goal_preserved    — identical content to V1, but turn_goal is
                         serialized FIRST (explicit goal preservation;
                         no new information, no authorization change).

Each captured surface is replayed REPLAY_REPS times per variant.
Nothing about this writes to runtime — requests are built by hand
and executed through the same governed adapter.
"""

import hashlib
import json
import os
import re
import sys
import uuid

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from scripts.r4_authenticated_resume_eval import _compose  # noqa: E402
from scripts.semantic_fidelity_eval import (  # noqa: E402
    _find_orchestrator,
)
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

REPLAY_REPS = 3
OUT_PATH = os.environ.get(
    "EVAL_OUT", "/tmp/assessment_variants.json"
)
CKPT = os.environ.get(
    "EVAL_CHECKPOINT", "/tmp/assessment_foreign_ckpt.jsonl"
)

_BLOCK_RE = re.compile(
    r"(<user_message>\n.*?\n</user_message>)"
    r"(.*?)"
    r"(<target_capability_group>\n)(.*?)(\n</target_capability_group>)",
    re.S,
)


def _variants(text: str) -> dict[str, str]:
    m = _BLOCK_RE.search(text)
    if not m:
        return {}
    user_msg, middle, open_tag, payload, close_tag = m.groups()
    try:
        block = json.loads(payload)
    except ValueError:
        return {}
    v1 = block
    # V2 — minimal sufficient: drop per-capability argument noise and
    # non-semantic keys; keep ids, class, description verbatim.
    v2 = {
        "target_capability_id": block.get("target_capability_id"),
        "target_operation_class": block.get("target_operation_class"),
        "capabilities": [
            {
                "remote_name": c.get("remote_name"),
                "operation_class": c.get("operation_class"),
                "description": c.get("description"),
            }
            for c in block.get("capabilities") or []
        ],
        "turn_goal": block.get("turn_goal"),
    }
    # V3 — identical content, goal serialized first.
    v3 = {
        "turn_goal": block.get("turn_goal"),
        "target_capability_id": block.get("target_capability_id"),
        "target_operation_class": block.get("target_operation_class"),
        "capabilities": block.get("capabilities"),
        "relevance_feedback": block.get("relevance_feedback"),
    }
    out = {}
    for name, blk in (
        ("v1_full", v1), ("v2_minimal", v2), ("v3_goal_first", v3)
    ):
        body = json.dumps(blk, ensure_ascii=False)
        out[name] = (
            user_msg + middle + open_tag + body + close_tag
        )
    return out


def main() -> int:
    # ---- collect the FP population from the diagnostic checkpoint
    cases = []
    seen = set()
    for line in open(CKPT):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        nat = (d.get("natural") or {}).get("assessment") or {}
        if (
            nat.get("oracle_verdict") == "sufficient"
            and nat.get("decision") == "foreign_evidence_required"
        ):
            blk = (d.get("dispatch_blocks") or {}).get(
                NATIVE_ASSESSMENT_INSTRUCTION_ID
            ) or {}
            text = blk.get("text")
            if not text or d["scenario"] in seen:
                continue
            seen.add(d["scenario"])
            cases.append(
                {
                    "scenario": d["scenario"],
                    "target_group": nat.get("target_group"),
                    "target_capability": nat.get("target_capability"),
                    "surface_sha": blk.get("sha"),
                    "text": text,
                }
            )
    print("FP_CASES:", len(cases), flush=True)

    handler, guarded, mcp = _compose()
    orch = _find_orchestrator(handler)
    instruction = orch._instruction(  # noqa: SLF001
        NATIVE_ASSESSMENT_INSTRUCTION_ID
    )
    results = []
    for case in cases:
        variants = _variants(case["text"])
        for vname, surface in sorted(variants.items()):
            decisions = []
            for rep in range(REPLAY_REPS):
                req = ModelInvocationRequest(
                    invocation_id=ModelInvocationId(str(uuid.uuid4())),
                    model_ref=orch._model_ref,  # noqa: SLF001
                    prior_context=(),
                    input_text=surface,
                    task_purpose_id=NATIVE_ASSESSMENT_INSTRUCTION_ID,
                    output_schema_id=NATIVE_ASSESSMENT_INSTRUCTION_ID,
                    output_schema_version=(
                        SELECTION_INSTRUCTION_VERSION
                    ),
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
                        "eval_variant": vname,
                    },
                )
                try:
                    res = orch._invoke_model.execute(req)  # noqa: SLF001
                    prop = res.structured_output or {}
                    decisions.append(prop.get("status"))
                except Exception as exc:
                    decisions.append(
                        "ERR:" + getattr(
                            exc, "code", type(exc).__name__
                        )
                    )
            results.append(
                {
                    "scenario": case["scenario"],
                    "target_group": case["target_group"],
                    "variant": vname,
                    "decisions": decisions,
                }
            )
            print(
                "VAR",
                case["scenario"],
                vname,
                decisions,
                flush=True,
            )

    with open(OUT_PATH, "w") as fh:
        json.dump(
            {
                "instruction_sha": hashlib.sha256(
                    instruction.encode()
                ).hexdigest()[:16],
                "cases": [
                    {k: v for k, v in c.items() if k != "text"}
                    for c in cases
                ],
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
