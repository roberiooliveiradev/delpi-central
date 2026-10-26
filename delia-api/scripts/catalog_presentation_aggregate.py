#!/usr/bin/env python3
"""Exclusive-category aggregation — catalog presentation eval.

Corrects the doc-155 aggregator flaw: every run lands in EXACTLY ONE
selection category; `correct` is never incremented for abstentions
in a metric whose denominator counts only applicable selections.

Categories (mutually exclusive, in precedence order):

  GROUP_INVALID_OUTPUT    select_group proposal exists but
                          unparseable/None, or applicable=true with a
                          group id absent from the live catalog
  ADMISSION_STOP          no select_group proposal; admission/other
                          stage declined before selection
  GROUP_NOT_REACHED_OTHER no select_group proposal for another reason
  GROUP_NOT_APPLICABLE_*  proposal applicable != true — CORRECT when
                          oracle wants no owner, WRONG when it does
  GROUP_CORRECT           applicable + live group + family accepted
  GROUP_WRONG             applicable + live group + family rejected

Owner oracle (WP0 §7 reconciled): for record-family asks,
`mcp:davi` (discover→execute) is a legitimate intermediate route —
scored under BOTH a lenient class (acceptable) and a strict class
(record owner only). Never scored by provider names; families come
from published operation classes.

Usage:
    python3 scripts/catalog_presentation_aggregate.py \
        --probe /tmp/catalog_presentation_probe.json \
        [--e2e /tmp/instr_eval_X.json ...]
"""

import argparse
import json
import statistics
from collections import Counter, defaultdict

GROUP_FAMILY = {
    "openapi:delpi": "record",
    "mcp:teo": "doc",
    "mcp:vista": "doc",
    "mcp:davi": "discovery",
}
RECORD_STRICT = {"record"}
RECORD_LENIENT = {"record", "discovery"}

SCENARIO_FAMILY = {
    "biz_bala3": "record", "biz_o2_2": "record", "biz_pino": "record",
    "biz_code": "record", "nom_colloq": "record",
    "nom_technical": "record", "nom_incomplete": "record",
    "nom_multi": "record", "cont_explicit": "record",
    "cont_prior": "record", "cont_obs": "record",
    "exhaust": "record", "cmp_legit": "record", "cmp_partial": "record",
    "disc_exec": "record", "neg_inject": "record",
    "h_rec_abracadeira": "record", "h_rec_espaguete": "record",
    "h_rec_code2": "record", "h_rec_qual": "record",
    "h_amb_broad": "record",
    "guide_term": "doc", "guide_proc": "doc",
    "h_doc_denominacao": "doc", "h_doc_sigla": "doc",
    "disc_candidate": "discovery",
    "disc_none": "none", "cont_nonauth": "none", "neg_scope": "none",
    "neg_write": "none", "neg_nobiz": "none", "guide_caps": "none",
    "h_nobiz_thanks": "none",
}


def _select_group_proposal(run: dict):
    for p in run.get("proposals") or ():
        if p.get("purpose", "").endswith("select_group"):
            return p.get("proposal"), p
    return None, None


def _accepts(expected: str, fam: str | None, strict: bool) -> bool:
    if fam is None:
        return False
    if expected == "record":
        return fam in (RECORD_STRICT if strict else RECORD_LENIENT)
    return fam == expected


def _classify_e2e(run: dict, strict: bool) -> str:
    sel, entry = _select_group_proposal(run)
    expected = SCENARIO_FAMILY.get(run["scenario"], "record")
    if entry is None:
        cls = run.get("classification") or {}
        if cls.get("first_divergent") == "ADMISSION_ERROR":
            return "ADMISSION_STOP"
        return "GROUP_NOT_REACHED_OTHER"
    if sel is None:
        return "GROUP_INVALID_OUTPUT"
    app = sel.get("applicable")
    if isinstance(app, str):
        app = app.strip().lower() == "true"
    grp = sel.get("capability_group_id")
    if app is True:
        fam = GROUP_FAMILY.get(grp)
        if fam is None:
            return "GROUP_INVALID_OUTPUT"
        if expected == "none":
            return "GROUP_WRONG"
        return (
            "GROUP_CORRECT"
            if _accepts(expected, fam, strict)
            else "GROUP_WRONG"
        )
    return (
        "GROUP_NOT_APPLICABLE_CORRECT"
        if expected == "none"
        else "GROUP_NOT_APPLICABLE_WRONG"
    )


def _classify_stage1(r: dict, strict: bool) -> str:
    expected = r["expected_family"]
    status = r["status"]
    grp = r["group"]
    fam = GROUP_FAMILY.get(grp) if grp else None
    if status == "invalid" or (grp is not None and fam is None):
        return "GROUP_INVALID_OUTPUT"
    if status != "selected" or grp is None:
        return (
            "GROUP_NOT_APPLICABLE_CORRECT"
            if expected == "none"
            else "GROUP_NOT_APPLICABLE_WRONG"
        )
    if expected == "none":
        return "GROUP_WRONG"
    return (
        "GROUP_CORRECT"
        if _accepts(expected, fam, strict)
        else "GROUP_WRONG"
    )


def _metrics(cats: list[str]) -> dict:
    c = Counter(cats)
    total = len(cats)
    reached = (
        c["GROUP_CORRECT"]
        + c["GROUP_WRONG"]
        + c["GROUP_NOT_APPLICABLE_CORRECT"]
        + c["GROUP_NOT_APPLICABLE_WRONG"]
        + c["GROUP_INVALID_OUTPUT"]
    )
    applicable = c["GROUP_CORRECT"] + c["GROUP_WRONG"]
    no_owner_runs = (
        c["GROUP_NOT_APPLICABLE_CORRECT"]
        + c["GROUP_NOT_APPLICABLE_WRONG"]
        # no-owner scenarios where a group was picked anyway
    )
    return {
        "total": total,
        "matrix": dict(c),
        "group_selection_accuracy": (
            f"{c['GROUP_CORRECT']}/{reached}",
            round(c["GROUP_CORRECT"] / reached, 3) if reached else 0,
        ),
        "owner_selection_precision": (
            f"{c['GROUP_CORRECT']}/{applicable}",
            round(c["GROUP_CORRECT"] / applicable, 3)
            if applicable
            else 0,
        ),
        "invalid_selection_rate": (
            f"{c['GROUP_INVALID_OUTPUT']}/{reached}",
            round(c["GROUP_INVALID_OUTPUT"] / reached, 3)
            if reached
            else 0,
        ),
        "admission_stop_rate": (
            f"{c['ADMISSION_STOP']}/{total}",
            round(c["ADMISSION_STOP"] / total, 3) if total else 0,
        ),
    }


def aggregate_probe(path: str) -> dict:
    d = json.load(open(path))
    results = d["results"]
    out = {}
    for strict in (False, True):
        label = "strict" if strict else "lenient"
        by_variant = defaultdict(list)
        for r in results:
            by_variant[r["variant"]].append(
                _classify_stage1(r, strict)
            )
        out[label] = {
            v: _metrics(cats) for v, cats in by_variant.items()
        }
    # per-variant, per-prompt accuracy (lenient)
    per = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in results:
        c = _classify_stage1(r, False)
        k = (r["prompt"], r["expected_family"])
        per[r["variant"]][k][0] += c in (
            "GROUP_CORRECT",
            "GROUP_NOT_APPLICABLE_CORRECT",
        )
        per[r["variant"]][k][1] += 1
    out["per_prompt"] = {
        v: {p[0]: c for p, c in items.items()}
        for v, items in per.items()
    }
    # payload stats per variant
    pay = defaultdict(list)
    for r in results:
        if r.get("payload"):
            pay[r["variant"]].append(r["payload"])
    out["payload"] = {
        v: {
            "chars": sorted({p["payload_chars"] for p in ps}),
            "json_valid_all": all(
                p.get("json_valid") for p in ps
            ),
            "scope_groups": sorted(
                {p.get("scope_present") for p in ps}
            ),
            "omitted": sorted({p.get("omitted") for p in ps}),
        }
        for v, ps in pay.items()
    }
    return out


def aggregate_e2e(path: str) -> dict:
    d = json.load(open(path))
    runs = d["runs"]
    out = {"file": path, "summary": d["summary"]}
    for strict in (False, True):
        label = "strict" if strict else "lenient"
        cats = [_classify_e2e(r, strict) for r in runs]
        out[label] = _metrics(cats)
        wrong = Counter()
        for r, c in zip(runs, cats):
            if c == "GROUP_WRONG":
                sel, _ = _select_group_proposal(r)
                wrong[(sel or {}).get("capability_group_id")] += 1
        out[label]["wrong_distribution"] = dict(wrong)
    out["outcomes"] = dict(
        Counter(r["classification"]["outcome"] for r in runs)
    )
    lats = sorted(r["elapsed_ms"] for r in runs)
    out["median_ms"] = (
        int(statistics.median(lats)) if lats else 0
    )
    out["p95_ms"] = lats[int(0.95 * len(lats)) - 1] if lats else 0
    per = defaultdict(list)
    for r in runs:
        per[r["scenario"]].append(_classify_e2e(r, False))
    out["per_scenario"] = {
        s: dict(Counter(cats)) for s, cats in per.items()
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe")
    ap.add_argument("--e2e", nargs="*", default=[])
    args = ap.parse_args()
    if args.probe:
        print(json.dumps(
            {"probe": aggregate_probe(args.probe)},
            ensure_ascii=False, indent=1,
        ))
    for path in args.e2e:
        print(json.dumps(
            aggregate_e2e(path), ensure_ascii=False, indent=1
        ))
    return 0


if __name__ == "__main__":
    main()
