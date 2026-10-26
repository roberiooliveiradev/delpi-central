#!/usr/bin/env python3
"""Stage-1 order-robustness probe — doc 156 follow-up.

Permutes ONLY the already-projected ``capability_groups`` list inside
the serialized payload dispatched to the LLM. No re-compaction, no
field edits: canonical ids, capabilities, scope, omission markers and
descriptions are byte-identical across permutations (verified per run
by sha + field extraction).

Schedule is temporally interleaved (rep -> permutation -> prompt) so
each permutation's calls are spread across the whole run.

Usage:
    python3 scripts/order_robustness_probe.py
    EVAL_CORPUS=holdout python3 scripts/order_robustness_probe.py
    EVAL_PERMS=0,23,7,15 python3 scripts/order_robustness_probe.py
"""

import itertools
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.r4_authenticated_resume_eval import _compose  # noqa: E402
from scripts.semantic_fidelity_eval import (  # noqa: E402
    _find_orchestrator,
    _mint_bearer,
)
from app.application.capability_provision import (  # noqa: E402
    orchestration as _orch_mod,
)
from app.infrastructure.auth.subject_bearer import (  # noqa: E402
    bind_subject_bearer,
    unbind_subject_bearer,
)

REPS = 5
CORPUS_MODE = os.environ.get("EVAL_CORPUS", "base")
PERM_SUBSET = os.environ.get("EVAL_PERMS")  # "0,5,23" or None=all
OUT_PATH = os.environ.get(
    "EVAL_OUT", "/tmp/order_robustness_probe.json"
)

BASE_PROMPTS = [
    ("traga três exemplos de terminal bala", "record"),
    ("consulte o produto de código 10080092", "record"),
    ("me mostra ilhós pra cabo de 4 milímetros", "record"),
    ("busque TERM. BALA 0,50-2,27MM2", "record"),
    ("traga dois exemplos de abraçadeira cadastrados", "record"),
    ("o que é um terminal bala?", "doc"),
    ("como a DELPI denomina terminais de compressão?", "doc"),
    ("o que significa a sigla O2 na nomenclatura?", "doc"),
    (
        "use o mcp davi para descobrir como consultar produtos",
        "discovery",
    ),
    ("mostre terminais", "record"),
    ("bom dia! como vai você?", "none"),
    ("apague o produto de código 10080092", "none"),
]

# Holdout corpus — questions lifted verbatim from the doc-155/156
# governed holdout scenarios; never used to tune anything.
HOLDOUT_PROMPTS = [
    ("traga dois exemplos de abraçadeira cadastrados", "record"),
    ("me mostre exemplos de espaguete para fiação", "record"),
    ("consulte o produto de código 10081004", "record"),
    (
        "busque terminais bala para cabo de 4mm com estoque",
        "record",
    ),
    (
        "como a DELPI denomina terminais de compressão?",
        "doc",
    ),
    (
        "o que significa a sigla O2 na nomenclatura de terminais?",
        "doc",
    ),
    ("mostre terminais", "record"),
    ("obrigado, era só isso", "none"),
]

PROMPTS = HOLDOUT_PROMPTS if CORPUS_MODE == "holdout" else BASE_PROMPTS

GROUP_FAMILY = {
    "openapi:delpi": "record",
    "mcp:teo": "doc",
    "mcp:vista": "doc",
    "mcp:davi": "discovery",
}
RECORD_OK = {"record", "discovery"}


def main() -> int:
    bearer = _mint_bearer()
    handler, guarded, mcp = _compose()
    orch = _find_orchestrator(handler)

    captured: list[dict] = []
    real_propose = orch._propose  # noqa: SLF001

    def spy(*args, **kwargs):
        import hashlib

        instr = args[0] if args else kwargs.get("instruction")
        block = args[1] if len(args) > 1 else kwargs.get(
            "block_payload"
        )
        purpose = kwargs.get("instruction_id", "")
        proposal = real_propose(*args, **kwargs)
        if purpose.endswith("select_group") or (
            kwargs.get("block_tag") == "capability_groups"
        ):
            entry = {}
            if isinstance(block, str):
                entry["payload_sha"] = hashlib.sha256(
                    block.encode()
                ).hexdigest()[:16]
                entry["payload_chars"] = len(block)
                try:
                    parsed = json.loads(block)
                    glist = (
                        parsed.get("capability_groups")
                        if isinstance(parsed, dict)
                        else parsed
                    ) or []
                    entry["group_ids"] = [
                        g.get("capability_group_id")
                        for g in glist
                        if isinstance(g, dict)
                    ]
                    entry["scope_present"] = sum(
                        1 for g in glist if g.get("scope")
                    )
                    entry["omitted"] = sum(
                        g.get("capabilities_omitted", 0)
                        for g in glist
                        if isinstance(g, dict)
                    )
                    entry["cap_counts"] = [
                        len(g.get("capabilities") or [])
                        for g in glist
                        if isinstance(g, dict)
                    ]
                    entry["json_valid"] = True
                except Exception:
                    entry["json_valid"] = False
            captured.append(entry)
        return proposal

    orch._propose = spy  # noqa: SLF001

    real_summaries = _orch_mod._group_summaries
    binding = bind_subject_bearer(bearer)
    try:
        groups, failures = orch._groups("order-probe")  # noqa: SLF001
    finally:
        unbind_subject_bearer(binding)

    # Canonical serialized order (sorted keys in _group_summaries).
    canon_payload = json.loads(real_summaries(groups))
    canon_list = (
        canon_payload.get("capability_groups")
        if isinstance(canon_payload, dict)
        else canon_payload
    )
    canon_ids = [
        g["capability_group_id"] for g in canon_list
    ]
    print("CANON_ORDER:", canon_ids, "failures:", failures, flush=True)

    perms = list(itertools.permutations(canon_ids))
    perm_idx = (
        [int(x) for x in PERM_SUBSET.split(",")]
        if PERM_SUBSET
        else list(range(len(perms)))
    )
    print("PERMUTATIONS:", len(perm_idx), "PROMPTS:", len(PROMPTS))

    target_order: list[str] = list(canon_ids)

    def summaries_permuted(*args, **kwargs):
        payload = real_summaries(*args, **kwargs)
        parsed = json.loads(payload)
        is_dict = isinstance(parsed, dict)
        glist = parsed.get("capability_groups") if is_dict else parsed
        if not isinstance(glist, list):
            return payload
        by_id = {g["capability_group_id"]: g for g in glist}
        try:
            reordered = [by_id[i] for i in target_order]
        except KeyError:
            return payload  # group set changed — keep as-is
        if is_dict:
            parsed["capability_groups"] = reordered
        else:
            parsed = reordered
        return json.dumps(parsed, ensure_ascii=False)

    _orch_mod._group_summaries = summaries_permuted

    results = []
    for rep in range(REPS):
        for pi in perm_idx:
            order = list(perms[pi])
            target_order[:] = order
            for prompt, expected in PROMPTS:
                captured.clear()
                t0 = time.monotonic()
                status, key = orch._select_group(  # noqa: SLF001
                    prompt,
                    groups,
                    correlation=f"ord-p{pi}-r{rep}",
                )
                ms = int((time.monotonic() - t0) * 1000)
                fam = GROUP_FAMILY.get(key) if key else None
                strict_ok = (
                    (expected == "record" and fam == "record")
                    or (expected != "record" and fam == expected)
                    or (expected == "none" and key is None)
                )
                lenient_ok = (
                    (expected == "record" and fam in RECORD_OK)
                    or (expected != "record" and fam == expected)
                    or (expected == "none" and key is None)
                )
                payload = captured[-1] if captured else {}
                results.append(
                    {
                        "corpus": CORPUS_MODE,
                        "perm_id": pi,
                        "group_order": order,
                        "prompt": prompt,
                        "expected_family": expected,
                        "rep": rep,
                        "status": status,
                        "group": key,
                        "selected_position": (
                            order.index(key) + 1
                            if key in order
                            else None
                        ),
                        "expected_position": (
                            order.index("openapi:delpi") + 1
                            if expected == "record"
                            else (
                                min(
                                    order.index("mcp:teo"),
                                    order.index("mcp:vista"),
                                )
                                + 1
                                if expected == "doc"
                                else (
                                    order.index("mcp:davi") + 1
                                    if expected == "discovery"
                                    else None
                                )
                            )
                        ),
                        "family": fam,
                        "strict_ok": strict_ok,
                        "lenient_ok": lenient_ok,
                        "ms": ms,
                        "payload": payload,
                    }
                )
                print(
                    json.dumps(results[-1], ensure_ascii=False),
                    flush=True,
                )

    _orch_mod._group_summaries = real_summaries

    with open(OUT_PATH, "w") as fh:
        json.dump(
            {
                "corpus": CORPUS_MODE,
                "canon_order": canon_ids,
                "groups": {
                    k: len(g.capabilities)
                    for k, g in groups.items()
                },
                "results": results,
            },
            fh,
            ensure_ascii=False,
        )
    print("TOTAL:", len(results), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
