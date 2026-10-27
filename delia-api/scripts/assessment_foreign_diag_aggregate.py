#!/usr/bin/env python3
"""Aggregate the assessment/foreign-selection diagnostic (doc 159).

Stage-conditional denominators everywhere — a stage error is only
counted against the runs that actually reached it.
"""

import json
import re
import sys
from collections import Counter, defaultdict

ASSESS_ID = "delia.capability_orchestration.native_assessment"
FOREIGN_ID = "delia.capability_orchestration.foreign_selection"


def _load(path):
    runs = []
    for line in open(path):
        try:
            runs.append(json.loads(line))
        except ValueError:
            continue
    return runs


def _purpose(run, suffix):
    for p in run.get("proposals") or ():
        if (p.get("purpose") or "").endswith(suffix):
            return p.get("proposal") or {}
    return {}


def main(path):
    runs = _load(path)
    out = {"total_runs": len(runs)}

    arms = defaultdict(list)
    for r in runs:
        arms[r["arm"]].append(r)

    # ---------- dispatch-surface integrity (WP2/WP10) ----------
    block_stats = {}
    for stage_id in (ASSESS_ID, FOREIGN_ID):
        chars, json_ok, has_goal, has_subject, has_caps = (
            [], 0, 0, 0, 0
        )
        for r in runs:
            blk = (r.get("dispatch_blocks") or {}).get(stage_id)
            if not blk or not blk.get("text"):
                continue
            text = blk["text"]
            chars.append(blk["chars"])
            m = re.search(
                r"<(target_capability_group|foreign_capability_groups)>\n"
                r"(.*)\n</\1>",
                text,
                re.S,
            )
            if m:
                try:
                    payload = json.loads(m.group(2))
                    json_ok += 1
                    if not isinstance(payload, dict):
                        continue
                    if "turn_goal" in payload and payload["turn_goal"]:
                        has_goal += 1
                        if payload["turn_goal"].get("business_subject"):
                            has_subject += 1
                    if payload.get("business_subject"):
                        has_subject += 1
                    if (
                        "capabilities" in payload
                        or "capability_groups" in payload
                    ):
                        has_caps += 1
                except ValueError:
                    pass
        block_stats[stage_id.split(".")[-1]] = {
            "captured": len(chars),
            "median_chars": (
                sorted(chars)[len(chars) // 2] if chars else 0
            ),
            "json_valid": json_ok,
            "turn_goal_present": has_goal,
            "business_subject_present": has_subject,
            "capability_surface_present": has_caps,
        }
    out["dispatch_integrity"] = block_stats

    # ---------- per-arm analysis ----------
    per_arm = {}
    for arm, rs in sorted(arms.items()):
        a = {"runs": len(rs)}
        a["outcome"] = dict(
            Counter(r["classification"].get("outcome") for r in rs)
        )
        a["first_divergent"] = dict(
            Counter(
                str(r["classification"].get("first_divergent"))
                for r in rs
            )
        )
        # assessment reached + decision × oracle verdict matrix
        assessed = [
            r
            for r in rs
            if (r.get("natural") or {}).get("assessment")
        ]
        a["assessment_reached"] = len(assessed)
        matrix = Counter()
        for r in assessed:
            nat = r["natural"]["assessment"]
            matrix[
                f"verdict={nat.get('oracle_verdict')} "
                f"decision={nat.get('decision')}"
            ] += 1
        a["assessment_matrix"] = dict(matrix)
        # confusion for foreign_evidence_required on applicable runs
        appl = [
            r
            for r in assessed
            if r["natural"]["assessment"].get("oracle_verdict")
            in ("sufficient", "required")
        ]
        tp = sum(
            1
            for r in appl
            if r["natural"]["assessment"]["decision"]
            == "foreign_evidence_required"
            and r["natural"]["assessment"]["oracle_verdict"]
            == "required"
        )
        fp = sum(
            1
            for r in appl
            if r["natural"]["assessment"]["decision"]
            == "foreign_evidence_required"
            and r["natural"]["assessment"]["oracle_verdict"]
            == "sufficient"
        )
        tn = sum(
            1
            for r in appl
            if r["natural"]["assessment"]["decision"] != "foreign_evidence_required"
            and r["natural"]["assessment"]["oracle_verdict"]
            == "sufficient"
        )
        fn = sum(
            1
            for r in appl
            if r["natural"]["assessment"]["decision"] != "foreign_evidence_required"
            and r["natural"]["assessment"]["oracle_verdict"]
            == "required"
        )
        a["foreign_required_confusion"] = {
            "applicable": len(appl),
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
        }
        # foreign selection reached + pick distribution
        foreign_runs = [
            r
            for r in rs
            if (r.get("natural") or {}).get("foreign_selection")
        ]
        a["foreign_selection_reached"] = len(foreign_runs)
        a["foreign_picks"] = dict(
            Counter(
                str(
                    (
                        r["natural"]["foreign_selection"].get(
                            "selected"
                        )
                        or {}
                    ).get("capability_id")
                )
                for r in foreign_runs
            )
        )
        a["foreign_modes"] = dict(
            Counter(
                r["natural"]["foreign_selection"].get("mode")
                for r in foreign_runs
            )
        )
        # engagement + controlled-stage outcomes
        a["controls_eligible"] = dict(
            Counter(
                c for r in rs for c in r.get("controls_eligible", [])
            )
        )
        a["controls_engaged"] = dict(
            Counter(
                c for r in rs for c in r.get("controls_engaged", [])
            )
        )
        # invokes
        a["owner_invokes"] = dict(
            Counter(
                i["capability_id"]
                for r in rs
                for i in r.get("invokes", [])
            ).most_common(12)
        )
        a["delpi_invokes"] = sum(
            1
            for r in rs
            if any(
                i["capability_id"].startswith("delpi.")
                for i in r.get("invokes", [])
            )
        )
        per_arm[arm] = a
    out["arms"] = per_arm

    # ---------- assessment engagement detail (arm C effect) ----------
    c_engaged = [
        r
        for r in arms.get("C", [])
        if "assessment" in r.get("controls_engaged", [])
    ]
    out["arm_c_engaged_runs"] = {
        "count": len(c_engaged),
        "owner_invoked": sum(
            1
            for r in c_engaged
            if any(
                i["capability_id"].startswith("delpi.")
                for i in r.get("invokes", [])
            )
        ),
        "outcomes": dict(
            Counter(
                r["classification"].get("outcome") for r in c_engaged
            )
        ),
        "first_divergent": dict(
            Counter(
                str(r["classification"].get("first_divergent"))
                for r in c_engaged
            )
        ),
    }
    d_engaged = [
        r
        for r in arms.get("D", [])
        if "foreign_selection" in r.get("controls_engaged", [])
    ]
    out["arm_d_engaged_runs"] = {
        "count": len(d_engaged),
        "outcomes": dict(
            Counter(
                r["classification"].get("outcome") for r in d_engaged
            )
        ),
        "first_divergent": dict(
            Counter(
                str(r["classification"].get("first_divergent"))
                for r in d_engaged
            )
        ),
        "delpi_invoked": sum(
            1
            for r in d_engaged
            if any(
                i["capability_id"].startswith("delpi.")
                for i in r.get("invokes", [])
            )
        ),
    }

    # ---------- per-scenario assessment matrix (arm A) ----------
    scen = defaultdict(lambda: Counter())
    for r in arms.get("A", []):
        nat = (r.get("natural") or {}).get("assessment") or {}
        scen[r["scenario"]][
            f"{nat.get('decision','NOT_REACHED')}"
            f"|{nat.get('oracle_verdict','-')}"
            f"|{nat.get('target_group','-')}"
        ] += 1
    out["arm_a_assessment_by_scenario"] = {
        k: dict(v) for k, v in scen.items()
    }

    # ---------- model cost ----------
    out["model_calls"] = sum(
        len(r.get("dispatch") or []) for r in runs
    )
    out["input_units"] = sum(
        d.get("in_units") or 0
        for r in runs
        for d in r.get("dispatch") or []
    )
    out["output_units"] = sum(
        d.get("out_units") or 0
        for r in runs
        for d in r.get("dispatch") or []
    )
    lat = sorted(r["elapsed_ms"] for r in runs)
    out["latency_ms_median"] = lat[len(lat) // 2] if lat else 0

    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else
         "/tmp/assessment_foreign_ckpt.jsonl")
