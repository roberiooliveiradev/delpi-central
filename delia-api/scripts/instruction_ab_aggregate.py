#!/usr/bin/env python3
"""Aggregate instruction A/B results — stage-local replay and E2E.

Stage-local input: assessment_ab_stagelocal.json (unique surfaces,
A/B decision lists per surface).
E2E input: instruction_ab_runs.json (full turns, arm A/B).
"""

import json
from collections import Counter

DECISIONS = (
    "sufficient",
    "foreign_evidence_required",
    "corroboration_requested",
    "inconclusive",
)


def _confusion(records):
    """records: iterable of (decision, oracle_verdict).
    Binary matrix on 'did the model demand foreign evidence?' vs
    'oracle says foreign was required'."""
    tp = fp = tn = fn = 0
    for dec, verdict in records:
        if verdict == "inconclusive":
            continue
        said_foreign = dec == "foreign_evidence_required"
        if said_foreign and verdict == "required":
            tp += 1
        elif said_foreign:
            fp += 1
        elif verdict == "required":
            fn += 1
        else:
            tn += 1
    app = tp + fp + tn + fn
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "applicable": app,
        "fp_rate": fp / (fp + tn) if fp + tn else None,
        "fn_rate": fn / (fn + tp) if fn + tp else None,
        "accuracy": (tp + tn) / app if app else None,
    }


def stage_local(path):
    d = json.load(open(path))
    rows = {"A": [], "B": []}
    counts = {"A": Counter(), "B": Counter()}
    for r in d["results"]:
        v = r["oracle_verdict"]
        for arm in ("A", "B"):
            for dec in r[arm]:
                counts[arm][dec if dec in DECISIONS else "INVALID"] += 1
                rows[arm].append((dec, v))
    out = {"instructions": {
        "A": d["instruction_a_sha"], "B": d["instruction_b_sha"]}}
    for arm in ("A", "B"):
        out[arm] = {
            "attempts": sum(counts[arm].values()),
            "decisions": dict(counts[arm]),
            "confusion": _confusion(rows[arm]),
        }
    # paired deltas: surfaces where majority decision flips
    flips = Counter()
    for r in d["results"]:
        maj = {}
        for arm in ("A", "B"):
            maj[arm] = Counter(r[arm]).most_common(1)[0][0]
        flips[(maj["A"], maj["B"])] += 1
    out["paired_majority_flips"] = {
        "%s->%s" % k: v for k, v in flips.items()
    }
    # model-call cost
    calls = d.get("model_call_detail", [])
    out["calls"] = len(calls)
    out["latency_s_total"] = round(
        sum(c.get("ms") or 0 for c in calls) / 1000, 1
    )
    out["tokens"] = {
        "in": sum(c.get("in_units") or 0 for c in calls),
        "out": sum(c.get("out_units") or 0 for c in calls),
    }
    return out


def e2e(path):
    d = json.load(open(path))
    out = {
        "instructions": {
            "A": d["instruction_a_sha"],
            "B": d["instruction_b_sha"],
        },
        "holdout": d.get("holdout"),
    }
    for arm in ("A", "B"):
        runs = [r for r in d["runs"] if r["arm"] == arm]
        dec = Counter()
        verdict = Counter()
        outcomes = Counter()
        invokes = Counter()
        foreign_sel = Counter()
        for r in runs:
            nat = r.get("natural") or {}
            a = nat.get("assessment") or {}
            if a.get("decision"):
                dec[a["decision"]] += 1
                verdict[a.get("oracle_verdict") or "?"] += 1
            fs = nat.get("foreign_selection") or {}
            sel = (fs.get("selected") or {}).get("capability_id")
            if fs and fs.get("mode"):
                foreign_sel[sel or "ABSTAIN"] += 1
            outcomes[
                r.get("classification", {}).get("outcome", "?")
            ] += 1
            for i in r.get("invokes", []):
                invokes[i["capability_id"]] += 1
        rows = []
        for r in runs:
            a = (r.get("natural") or {}).get("assessment") or {}
            if a.get("decision"):
                rows.append((a["decision"], a.get("oracle_verdict")))
        out[arm] = {
            "runs": len(runs),
            "assessment_decisions": dict(dec),
            "assessment_oracle_verdicts": dict(verdict),
            "assessment_confusion": _confusion(rows),
            "foreign_selection": dict(foreign_sel),
            "invocations": dict(invokes),
            "outcomes": dict(outcomes),
            "model_calls": sum(r.get("model_calls") or 0 for r in runs),
            "tokens": {
                "in": sum(r.get("tokens_in") or 0 for r in runs),
                "out": sum(r.get("tokens_out") or 0 for r in runs),
            },
            "latency_s": round(
                sum(r.get("latency_ms") or 0 for r in runs) / 1000, 1
            ),
        }
        for label, sub in (
            ("dev", [r for r in runs if not r.get("holdout")]),
            ("holdout", [r for r in runs if r.get("holdout")]),
        ):
            out[arm]["%s_runs" % label] = len(sub)
            out[arm]["%s_outcomes" % label] = dict(
                Counter(
                    r.get("classification", {}).get("outcome", "?")
                    for r in sub
                )
            )
            out[arm]["%s_decisions" % label] = dict(
                Counter(
                    ((r.get("natural") or {}).get("assessment") or {})
                    .get("decision")
                    for r in sub
                )
            )
    out["total_calls"] = len(d.get("model_call_detail", []))
    return out


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "stage":
        print(
            json.dumps(
                stage_local(sys.argv[2]), indent=2, ensure_ascii=False
            )
        )
    else:
        print(
            json.dumps(
                e2e(sys.argv[2]), indent=2, ensure_ascii=False
            )
        )
