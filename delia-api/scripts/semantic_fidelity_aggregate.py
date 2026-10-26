"""Aggregate /tmp/semantic_eval_runs.json into the task metrics.

Read-only: computes per-scenario/family outcome rates, first-divergent
distribution, admission/goal/selection/argument rates, token and
latency aggregates, and prints a sanitized summary for the report.
"""

import json
import statistics
import sys
from collections import Counter, defaultdict

PATH = "/tmp/semantic_eval_runs.json"


def main() -> int:
    data = json.load(open(PATH))
    runs = data["runs"]
    summary = data["summary"]

    by_scenario = defaultdict(list)
    for r in runs:
        by_scenario[r["scenario"]].append(r)

    out = {
        "executions": len(runs),
        "model_calls": summary["model_calls"],
        "input_tokens": summary["input_tokens"],
        "output_tokens": summary["output_tokens"],
        "latencies_ms": sorted(r["elapsed_ms"] for r in runs),
    }
    lat = out["latencies_ms"]
    out["median_ms"] = int(statistics.median(lat)) if lat else 0
    out["p95_ms"] = (
        sorted(lat)[int(0.95 * len(lat)) - 1] if lat else 0
    )

    per_scenario = {}
    divergent = Counter()
    outcomes = Counter()
    admission_tp = admission_tn = admission_fp = admission_fn = 0
    subject_valid = subject_null = subject_total = 0
    invalid_structured = 0
    owners_invoked = []
    for sid, group in by_scenario.items():
        oc = Counter(
            r["classification"]["outcome"] for r in group
        )
        fd = Counter(
            r["classification"]["first_divergent"]
            for r in group
            if r["classification"]["first_divergent"]
        )
        subjects = [
            r["classification"].get("business_subject")
            for r in group
        ]
        per_scenario[sid] = {
            "runs": len(group),
            "outcomes": dict(oc),
            "first_divergent": dict(fd),
            "subjects": [s for s in subjects if s],
            "invoked": sorted(
                {
                    c
                    for r in group
                    for c in r["classification"]["invoked_caps"]
                }
            ),
            "grounded": sum(
                1 for r in group if "GROUNDED." in r["grounding"]
                or "GROUNDED" in r["grounding"]
                and "NON_GROUNDED" not in r["grounding"]
            ),
        }
        for r in group:
            cls = r["classification"]
            outcomes[cls["outcome"]] += 1
            if cls["first_divergent"]:
                divergent[cls["first_divergent"]] += 1
            if cls.get("invalid_structured"):
                invalid_structured += 1
            owners_invoked.append(len(r["invokes"]))
            adm = cls.get("admission")
            if adm is True:
                admission_tp += 1
            elif adm is False:
                admission_fn += 1
            bs = cls.get("business_subject")
            if bs is not None:
                subject_total += 1
                if bs:
                    subject_valid += 1
                else:
                    subject_null += 1
            else:
                subject_null += 1
                subject_total += 1

    out["per_scenario"] = per_scenario
    out["outcome_totals"] = dict(outcomes)
    out["divergent_totals"] = dict(divergent)
    out["admission"] = {
        "requires_owner_true": admission_tp,
        "requires_owner_false": admission_fn,
    }
    out["subject"] = {
        "proposed": subject_total,
        "non_null": subject_valid,
        "null": subject_null,
    }
    out["invalid_structured"] = invalid_structured
    out["mean_owner_calls"] = (
        round(statistics.mean(owners_invoked), 2)
        if owners_invoked
        else 0
    )
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
