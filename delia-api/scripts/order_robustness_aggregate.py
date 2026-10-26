#!/usr/bin/env python3
"""Order-robustness aggregation — doc 157.

Consumes order_robustness_probe.py output ({corpus, canon_order,
results[]}). Produces per-permutation exclusive-category metrics
(strict/lenient), absolute-position effects, relative-order effects,
selection concentration, and run-vs-order variance decomposition.

Categories (exclusive, per run):
  GROUP_CORRECT / GROUP_WRONG / GROUP_INVALID_OUTPUT /
  GROUP_NOT_APPLICABLE_CORRECT / GROUP_NOT_APPLICABLE_WRONG /
  GROUP_NOT_REACHED_OTHER

Usage:
    python3 scripts/order_robustness_aggregate.py RUNS.json
"""

import json
import statistics
import sys
from collections import Counter, defaultdict

GROUP_FAMILY = {
    "openapi:delpi": "record",
    "mcp:teo": "doc",
    "mcp:vista": "doc",
    "mcp:davi": "discovery",
}
RECORD_LENIENT = {"record", "discovery"}


def _classify(r: dict, strict: bool) -> str:
    expected = r["expected_family"]
    key = r.get("group")
    fam = r.get("family")
    status = r["status"]
    if status == "invalid" or (key is not None and fam is None):
        return "GROUP_INVALID_OUTPUT"
    if status != "selected" or key is None:
        return (
            "GROUP_NOT_APPLICABLE_CORRECT"
            if expected == "none"
            else "GROUP_NOT_APPLICABLE_WRONG"
        )
    if expected == "none":
        return "GROUP_WRONG"
    if expected == "record":
        ok = fam in ({"record"} if strict else RECORD_LENIENT)
    else:
        ok = fam == expected
    return "GROUP_CORRECT" if ok else "GROUP_WRONG"


def _acc(cats):
    c = Counter(cats)
    reached = (
        c["GROUP_CORRECT"] + c["GROUP_WRONG"]
        + c["GROUP_INVALID_OUTPUT"]
        + c["GROUP_NOT_APPLICABLE_CORRECT"]
        + c["GROUP_NOT_APPLICABLE_WRONG"]
    )
    return {
        "matrix": dict(c),
        "n": len(cats),
        "correct": c["GROUP_CORRECT"],
        "reached": reached,
        "acc": round(c["GROUP_CORRECT"] / reached, 3) if reached else 0,
        "invalid": c["GROUP_INVALID_OUTPUT"],
    }


def main() -> int:
    d = json.load(open(sys.argv[1]))
    runs = d["results"]
    canon = d["canon_order"]

    by_perm = defaultdict(list)
    for r in runs:
        by_perm[r["perm_id"]].append(r)

    out = {"corpus": d["corpus"], "canon_order": canon, "perms": {}}
    for pi, rs in sorted(by_perm.items()):
        order = rs[0]["group_order"]
        strict = _acc([_classify(r, True) for r in rs])
        lenient = _acc([_classify(r, False) for r in rs])
        sel = Counter(r["group"] for r in rs if r["group"])
        top_share = (
            round(max(sel.values()) / len(rs), 3) if sel else 0
        )
        # run variance: per (prompt) entropy of picks across reps
        prompt_spread = []
        per_prompt = defaultdict(Counter)
        for r in rs:
            per_prompt[r["prompt"]][r["group"]] += 1
        for p, c in per_prompt.items():
            if len(c) > 1:
                prompt_spread.append(p)
        out["perms"][str(pi)] = {
            "order": order,
            "strict": strict,
            "lenient": lenient,
            "selection": dict(sel),
            "dominant_share": top_share,
            "inconsistent_prompts": len(prompt_spread),
        }

    # ---- absolute position effect: for each group, pick-rate and
    # strict-correct-rate when it sits at each position.
    pos = {g: {p: [0, 0, 0] for p in (1, 2, 3, 4)} for g in canon}
    for r in runs:
        order = r["group_order"]
        for p, g in enumerate(order, 1):
            cell = pos[g][p]
            cell[0] += 1  # exposures
            if r["group"] == g:
                cell[1] += 1  # picked
            if r["group"] == g and _classify(r, True) == (
                "GROUP_CORRECT"
            ):
                cell[2] += 1  # picked + strictly correct
    out["position_effect"] = {
        g: {
            str(p): {
                "exposures": c[0],
                "picked": c[1],
                "correct": c[2],
            }
            for p, c in cells.items()
        }
        for g, cells in pos.items()
    }

    # ---- relative order: for record prompts, strict accuracy when
    # delpi is before vs after each other group.
    rel = {}
    for g in ("mcp:davi", "mcp:teo", "mcp:vista"):
        before = _acc(
            [
                _classify(r, True)
                for r in runs
                if r["expected_family"] == "record"
                and r["group_order"].index("openapi:delpi")
                < r["group_order"].index(g)
            ]
        )
        after = _acc(
            [
                _classify(r, True)
                for r in runs
                if r["expected_family"] == "record"
                and r["group_order"].index("openapi:delpi")
                > r["group_order"].index(g)
            ]
        )
        rel[f"delpi_before_{g}"] = before
        rel[f"delpi_after_{g}"] = after
    out["relative_order"] = rel

    # ---- global stats
    all_strict = _acc([_classify(r, True) for r in runs])
    all_lenient = _acc([_classify(r, False) for r in runs])
    accs = [
        out["perms"][str(pi)]["strict"]["acc"]
        for pi in by_perm
    ]
    out["global"] = {
        "total": len(runs),
        "strict": all_strict,
        "lenient": all_lenient,
        "perm_acc_mean": round(statistics.mean(accs), 3),
        "perm_acc_stdev": round(
            statistics.stdev(accs), 3
        ) if len(accs) > 1 else 0,
        "perm_acc_min": min(accs),
        "perm_acc_max": max(accs),
        "perm_acc_range": round(max(accs) - min(accs), 3),
    }

    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    main()
