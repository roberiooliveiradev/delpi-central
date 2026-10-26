#!/usr/bin/env python3
"""Aggregate downstream causal eval runs (doc 158).

Reads the JSON produced by downstream_causal_eval.py and emits the
per-arm comparison matrix + first-divergent-stage distribution
required by WP11/WP12. Rows marked CONTROLLED reflect harness
injection (controls_engaged), never model success.
"""
import json
import statistics
import sys
from collections import Counter, defaultdict

PATH = sys.argv[1] if len(sys.argv) > 1 else "downstream_causal_runs.json"
data = json.load(open(PATH))
runs = data["runs"]
ORACLE = data["oracle"]
ARMS = ("A", "B", "C", "D")
by_arm = defaultdict(list)
for r in runs:
    by_arm[r["arm"]].append(r)


def stage_div(r, arm):
    """First divergent stage — honors controls_engaged marks."""
    ps = {
        p["purpose"].split(".")[-1]: (p.get("proposal") or {})
        for p in r["proposals"]
    }
    ic = ps.get("interaction_admission", {}).get("interaction_class")
    if ic == "surface_inquiry":
        return "ADMISSION:surface_inquiry"
    if (
        ic == "hypothetical"
        and not r["invokes"]
        and "select_capability" not in ps
        and "turn_goal" not in ps
    ):
        return "ADMISSION:hypothetical_fab"
    eng = set(r["controls_engaged"])
    if "select_group" in ps and "group" not in eng:
        g = ps["select_group"].get("capability_group_id")
        if g != "openapi:delpi":
            return "GROUP:wrong(%s)" % g
    inv = r["invokes"]
    if inv:
        di = [
            i
            for i in inv
            if i["capability_id"].startswith("delpi.")
        ]
        if di and any(i["status"] == "COMPLETED" for i in di):
            return (
                "EVIDENCE_RELEVANCE_REJECT"
                if r["classification"]["outcome"] != "PASS"
                else "SUCCESS"
            )
        return "INVOKE:%s:%s" % (
            inv[-1]["capability_id"],
            inv[-1]["status"],
        )
    na = [
        p
        for p in r["proposals"]
        if p["purpose"].endswith("native_assessment")
    ]
    if na and (na[-1].get("proposal") or {}).get(
        "status"
    ) == "foreign_evidence_required":
        fs = [
            p
            for p in r["proposals"]
            if p["purpose"].endswith("foreign_selection")
        ]
        fid = (
            (fs[-1].get("proposal") or {}).get(
                "foreign_capability_id", ""
            )
            if fs
            else ""
        )
        return "FOREIGN_DIVERT(%s)" % (fid or "none")
    sc = ps.get("select_capability", {})
    if sc and (
        sc.get("applicable") is not True
        or not sc.get("remote_name")
    ):
        return "CAPABILITY:abstain"
    if sc:
        rn = sc.get("remote_name")
        if rn != ORACLE[r["scenario"]][1]:
            return "CAPABILITY:wrong(%s)" % rn
    args = [
        p
        for p in r["proposals"]
        if p["purpose"].endswith(".arguments")
    ]
    if args:
        a = args[-1].get("proposal") or {}
        if a.get("arguments") is None:
            return "ARGS:null/missing"
        return "ARGS:built-no-invoke"
    if "index_probe" in ps:
        return "STOP:after_index_probe"
    return "OTHER"


print("=== PER-ARM MATRIX (n=%d per arm) ===" % len(by_arm["A"]))
for arm in ARMS:
    rs = by_arm[arm]
    eng = sum(1 for r in rs if r["controls_engaged"])
    oc = Counter(r["classification"]["outcome"] for r in rs)
    gr = sum(1 for r in rs if "GROUNDED" in r["grounding"])
    inv = sum(1 for r in rs if r["invokes"])
    dinv = sum(
        1
        for r in rs
        if any(
            i["capability_id"].startswith("delpi.")
            and i["status"] == "COMPLETED"
            for i in r["invokes"]
        )
    )
    ms = statistics.median(r["elapsed_ms"] for r in rs)
    print(
        "%s engaged=%d grounded=%d any_invoke=%d delpi_completed=%d "
        "PASS=%d PARTIAL=%d FAIL=%d ms_med=%d"
        % (arm, eng, gr, inv, dinv, oc["PASS"], oc["PARTIAL"],
           oc["FAIL"], int(ms))
    )

print()
print("=== FIRST DIVERGENT STAGE BY ARM ===")
for arm in ARMS:
    dist = Counter(
        stage_div(r, arm) for r in by_arm[arm]
    )
    print(arm, dict(dist.most_common()))

print()
print("=== ARGUMENT EVAL BY ARM ===")
for arm in ARMS:
    print(
        arm,
        dict(
            Counter(
                r["argument_eval"] for r in by_arm[arm]
            ).most_common()
        ),
    )

print()
print("=== TOKENS / CALLS ===")
print(json.dumps(data["stats"], ensure_ascii=False))
