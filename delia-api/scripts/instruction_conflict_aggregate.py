#!/usr/bin/env python3
"""A/B aggregation for the select_group instruction conflict eval.

Reads the run artifacts produced by ``instruction_conflict_eval.py``
and prints per-variant metrics with explicit numerators/denominators:

    python3 scripts/instruction_conflict_aggregate.py \
        /tmp/instr_eval_A_base.json /tmp/instr_eval_B_base.json ...

Group-selection accuracy is scored only over runs that actually
reached the group-selection stage (a select_group proposal exists),
never over turns that diverged earlier at admission — per WP4 §14.
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
# discovery owners are an authorized path for record asks
# (discover→execute resolves designations), so they count as
# acceptable for record-family group selection — same convention the
# base classifier applies via allowed_caps.
RECORD_OK = {"record", "discovery"}

SCENARIO_FAMILY = {
    "biz_bala3": "record", "biz_o2_2": "record", "biz_pino": "record",
    "biz_code": "record", "nom_colloq": "record",
    "nom_technical": "record", "nom_incomplete": "record",
    "nom_multi": "record", "cont_explicit": "record",
    "cont_prior": "record", "cont_obs": "record",
    "exhaust": "record", "cmp_legit": "record", "cmp_partial": "record",
    "disc_exec": "record",
    "guide_term": "doc", "guide_proc": "doc",
    "h_doc_denominacao": "doc", "h_doc_sigla": "doc",
    "disc_candidate": "discovery", "disc_none": "none",
    "cont_nonauth": "none", "neg_scope": "none", "neg_write": "none",
    "neg_inject": "record", "neg_nobiz": "none",
    "guide_caps": "none",
    "h_rec_abracadeira": "record", "h_rec_espaguete": "record",
    "h_rec_code2": "record", "h_rec_qual": "record",
    "h_amb_broad": "record", "h_nobiz_thanks": "none",
}


def _select_group_proposal(run: dict) -> dict | None:
    for p in run.get("proposals") or ():
        if p.get("purpose", "").endswith("select_group"):
            return p.get("proposal")
    return None


def aggregate(path: str) -> dict:
    data = json.load(open(path))
    runs = data["runs"]
    summary = data["summary"]

    by_scenario = defaultdict(list)
    for r in runs:
        by_scenario[r["scenario"]].append(r)

    eligible = correct = invalid_sel = not_applicable = 0
    wrong_dist = Counter()
    outcomes = Counter()
    divergent = Counter()
    lats = []
    per_scenario = {}

    for sid, group in by_scenario.items():
        want = SCENARIO_FAMILY.get(sid)
        sc_ok = sc_el = 0
        for r in group:
            cls = r["classification"]
            lats.append(r["elapsed_ms"])
            outcomes[cls["outcome"]] += 1
            if cls["first_divergent"]:
                divergent[cls["first_divergent"]] += 1
            sel = _select_group_proposal(r)
            if sel is None:
                continue  # stage never reached (admission stop)
            app = sel.get("applicable")
            if isinstance(app, str):
                app = app.strip().lower() == "true"
            grp = sel.get("capability_group_id")
            if app is not True:
                not_applicable += 1
                if want == "none":
                    correct += 1  # correct no-owner answer
                continue
            eligible += 1
            sc_el += 1
            fam = GROUP_FAMILY.get(grp)
            if not isinstance(grp, str) or fam is None:
                invalid_sel += 1
            elif want == "none":
                wrong_dist[grp] += 1  # owner claimed where none needed
            elif want == "doc" and fam == "doc":
                correct += 1
                sc_ok += 1
            elif want == "discovery" and fam == "discovery":
                correct += 1
                sc_ok += 1
            elif want == "record" and fam in RECORD_OK:
                correct += 1
                sc_ok += 1
            else:
                wrong_dist[grp] += 1
        per_scenario[sid] = {
            "runs": len(group),
            "eligible": sc_el,
            "correct": sc_ok,
            "outcomes": dict(
                Counter(
                    r["classification"]["outcome"] for r in group
                )
            ),
        }

    return {
        "file": path,
        "variant": summary.get("variant"),
        "fingerprint": summary.get("instruction_fingerprint"),
        "executions": len(runs),
        "model_calls": summary["model_calls"],
        "input_tokens": summary["input_tokens"],
        "output_tokens": summary["output_tokens"],
        "median_ms": int(statistics.median(lats)) if lats else 0,
        "p95_ms": sorted(lats)[int(0.95 * len(lats)) - 1]
        if lats
        else 0,
        "group_selection": {
            "eligible": eligible,
            "not_applicable": not_applicable,
            "correct": correct,
            "wrong": eligible - correct - invalid_sel,
            "invalid": invalid_sel,
            "wrong_distribution": dict(wrong_dist),
        },
        "outcomes": dict(outcomes),
        "first_divergent": dict(divergent),
        "per_scenario": per_scenario,
    }


def main() -> int:
    for path in sys.argv[1:]:
        print(json.dumps(aggregate(path), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
