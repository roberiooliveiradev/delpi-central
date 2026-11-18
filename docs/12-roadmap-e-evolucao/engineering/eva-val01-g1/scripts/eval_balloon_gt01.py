#!/usr/bin/env python3
"""GT-01 integrated B1+B2+B3 evaluator (offline, exploratory metrics).

Joins independent balloon GT annotations (schema eva_val01_balloon_annotation.v1)
with EVA evaluation dumps produced by the real pipeline probe, and computes
per-stage metrics only where denominators are valid. Real and synthetic
documents are evaluated separately and never mixed.

Usage:
    python eval_balloon_gt01.py --gt-dir ../annotations-balloon \
        --eval-dir /path/to/eval_dumps [--synthetic-dir ../synthetic-balloon] \
        --out report.json
"""
import argparse
import json
import os


def _iou(a, b):
    if not a or not b:
        return 0.0
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def _norm(label):
    return (label or "").strip().upper() or None


def _gt_row_set(ref):
    """Parse GT table_item_reference like 'row_index:[2,4,7]' or 'row_index:1'."""
    if not ref:
        return set()
    body = ref.split(":", 1)[-1].strip()
    if body.startswith("["):
        try:
            return {int(v) for v in json.loads(body.replace("'", '"'))}
        except Exception:
            return set()
    try:
        return {int(body)}
    except ValueError:
        return set()


def _ratio(num, den):
    if den <= 0:
        return {"value": None, "status": "INCONCLUSIVE_NO_DENOMINATOR", "numerator": num, "denominator": den}
    return {"value": round(num / den, 4), "status": "EXPLORATORY_ONLY", "numerator": num, "denominator": den}


def match_balloons(gt_occ, eval_entries):
    """Match GT occurrences to eval balloon entries by label + IoU>=0.5."""
    pairs, used = [], set()
    for g in gt_occ:
        best, best_iou = None, 0.5
        for i, e in enumerate(eval_entries):
            if i in used or _norm(e.get("normalized_label") or e.get("balloon_label")) != _norm(g.get("balloon_label")):
                continue
            ov = _iou(g.get("balloon_bbox"), e.get("bounding_box_px"))
            if ov > best_iou:
                best, best_iou = i, ov
        if best is not None:
            used.add(best)
            pairs.append((g, eval_entries[best]))
        else:
            pairs.append((g, None))
    extra = [e for i, e in enumerate(eval_entries) if i not in used]
    return pairs, extra


def evaluate_document(gt, dump):
    """Per-document stage results. Returns dict of case records + counters."""
    eval_entries = dump.get("validation", {}).get("balloons") or dump.get("balloons") or []
    gt_occ = [o for o in gt.get("balloon_occurrences", [])
              if o.get("balloon_visual_presence") == "PRESENT"]
    pairs, extra = match_balloons(gt_occ, eval_entries)

    rec = {"document_id": gt.get("document_id"), "cases": [], "unmatched_eval_balloons": len(extra)}

    for g, e in pairs:
        c = {"occurrence_id": g.get("balloon_occurrence_id"),
             "label": _norm(g.get("balloon_label")),
             "gt_relation": g.get("balloon_relation_status")}
        if e is None:
            c["b1_detection"] = "MISS"
            c["b1_table_association"] = c["b2_leader"] = c["b2_target"] = "NOT_EVALUABLE"
            c["b3_consistency"] = "NOT_EVALUABLE"
            rec["cases"].append(c)
            continue
        c["b1_detection"] = "HIT"

        # B1 table association: eval table_item (single) or table_items
        # (ambiguous candidates) vs GT row set.
        ti = e.get("table_item") or {}
        cands = e.get("table_items") or []
        gt_rows = _gt_row_set(g.get("table_item_reference"))
        if e.get("association") == "AMBIGUOUS" and cands:
            cand_rows = {c_.get("row_index") for c_ in cands}
            if gt_rows and cand_rows == gt_rows:
                c["b1_table_association"] = "HIT"
            elif gt_rows and cand_rows & gt_rows:
                c["b1_table_association"] = "PARTIAL_ROWS"
            else:
                c["b1_table_association"] = ("HIT" if _norm(g.get("table_item_label")) in
                                             {_norm(c_.get("item_label")) for c_ in cands}
                                             else "WRONG_LABEL")
        elif g.get("table_item_label") is None and not gt_rows:
            c["b1_table_association"] = ("CORRECT_NO_MATCH" if ti.get("row_index") is None
                                         else "UNEXPECTED_MATCH")
        elif ti.get("row_index") is None:
            c["b1_table_association"] = "MISS"
        elif gt_rows:
            c["b1_table_association"] = "HIT" if ti.get("row_index") in gt_rows else "WRONG_ROW"
        else:
            c["b1_table_association"] = ("HIT" if _norm(ti.get("item_label")) ==
                                         _norm(g.get("table_item_label")) else "WRONG_LABEL")

        # B2 leader + target
        ll = e.get("leader_line") or {}
        if g.get("leader_presence") != "PRESENT":
            c["b2_leader"] = "GT_NO_LEADER"
            c["b2_target"] = "GT_NO_LEADER"
        elif ll.get("state") != "CANDIDATE":
            c["b2_leader"] = "MISS"
            c["b2_target"] = "MISS"
        else:
            c["b2_leader"] = "CANDIDATE_FOUND"
            ts = ll.get("target_state")
            gt_has_target = g.get("target_region") is not None
            if ts == "SINGLE_REGION":
                c["b2_target"] = ("SINGLE_HIT" if gt_has_target and
                                  _iou(ll.get("target_region_px") or [], g["target_region"]) >= 0.5
                                  else "SINGLE_MISMATCH" if gt_has_target else "SINGLE_GT_INDETERMINATE")
            elif ts == "AMBIGUOUS_REGIONS":
                c["b2_target"] = "AMBIGUITY_PRESERVED" if not gt_has_target else "AMBIGUITY_GT_DISPUTED"
            else:
                c["b2_target"] = "NOT_IDENTIFIED"

        # B3 consistency vs GT relation status
        cc = (e.get("component_consistency") or {}).get("state")
        rel = g.get("balloon_relation_status")
        if rel == "ASSOCIATION_CONSISTENT":
            c["b3_consistency"] = {"COMPATIBLE_CANDIDATE": "CORRECT_CANDIDATE",
                                   "CONFLICT_CANDIDATE": "FALSE_CONFLICT"}.get(cc, "FALSE_NEGATIVE_OR_ABSTAIN")
        elif rel in ("INSUFFICIENT_EVIDENCE", "INDETERMINATE"):
            c["b3_consistency"] = ("CORRECT_ABSTENTION" if cc in ("INCONCLUSIVE", "NOT_COMPARABLE", "AMBIGUOUS", "NOT_CHECKED")
                                   else "UNSUPPORTED_VERDICT")
        elif rel == "ASSOCIATION_SWAPPED":
            c["b3_consistency"] = {"CONFLICT_CANDIDATE": "TRUE_CONFLICT",
                                   "COMPATIBLE_CANDIDATE": "FALSE_COMPATIBLE"}.get(cc, "MISSED_CONFLICT")
        else:
            c["b3_consistency"] = "GT_UNKNOWN"
        c["eva_cc_state"] = cc
        rec["cases"].append(c)
    return rec


def aggregate(records):
    def cnt(pred):
        return sum(1 for r in records for c in r["cases"] if pred(c))

    det_hit = cnt(lambda c: c.get("b1_detection") == "HIT")
    det_miss = cnt(lambda c: c.get("b1_detection") == "MISS")
    fp = sum(r["unmatched_eval_balloons"] for r in records)
    assoc_hit = cnt(lambda c: c.get("b1_table_association") == "HIT")
    assoc_den = cnt(lambda c: c.get("b1_table_association") in
                    ("HIT", "PARTIAL_ROWS", "WRONG_ROW", "WRONG_LABEL", "MISS"))
    lead_hit = cnt(lambda c: c.get("b2_leader") == "CANDIDATE_FOUND")
    lead_den = cnt(lambda c: c.get("b2_leader") in ("CANDIDATE_FOUND", "MISS"))
    tgt_single = cnt(lambda c: c.get("b2_target") == "SINGLE_HIT")
    tgt_den = cnt(lambda c: c.get("b2_target") in ("SINGLE_HIT", "SINGLE_MISMATCH", "NOT_IDENTIFIED"))
    tgt_amb_ok = cnt(lambda c: c.get("b2_target") == "AMBIGUITY_PRESERVED")
    tgt_amb_den = cnt(lambda c: c.get("b2_target") in ("AMBIGUITY_PRESERVED", "AMBIGUITY_GT_DISPUTED"))
    true_conf = cnt(lambda c: c.get("b3_consistency") == "TRUE_CONFLICT")
    false_conf = cnt(lambda c: c.get("b3_consistency") == "FALSE_CONFLICT")
    missed_conf = cnt(lambda c: c.get("b3_consistency") == "MISSED_CONFLICT")
    correct_cand = cnt(lambda c: c.get("b3_consistency") == "CORRECT_CANDIDATE")
    false_cand = cnt(lambda c: c.get("b3_consistency") == "UNSUPPORTED_VERDICT")
    abst = cnt(lambda c: c.get("b3_consistency") in ("CORRECT_ABSTENTION", "FALSE_NEGATIVE_OR_ABSTAIN"))
    total = sum(len(r["cases"]) for r in records)

    return {
        "DETECTION_PRECISION": _ratio(det_hit, det_hit + fp),
        "DETECTION_RECALL": _ratio(det_hit, det_hit + det_miss),
        "TABLE_ASSOCIATION_ACCURACY": _ratio(assoc_hit, assoc_den),
        "LEADER_DETECTION_RATE": _ratio(lead_hit, lead_den),
        "TARGET_ASSOCIATION_ACCURACY": _ratio(tgt_single, tgt_den),
        "AMBIGUITY_PRESERVATION_RATE": _ratio(tgt_amb_ok, tgt_amb_den),
        "CONFLICT_PRECISION": _ratio(true_conf, true_conf + false_conf),
        "CONFLICT_RECALL": _ratio(true_conf, true_conf + missed_conf),
        "FALSE_ALERT_RATE": _ratio(false_conf + false_cand, total),
        "FALSE_NEGATIVE_RATE": _ratio(missed_conf, true_conf + missed_conf),
        "ABSTENTION_RATE": _ratio(abst, total),
        "CORRECT_COMPATIBLE_CANDIDATES": {"value": correct_cand, "status": "COUNT"},
        "TOTAL_GT_OCCURRENCES": total,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt-dir", required=True)
    ap.add_argument("--eval-dir", required=True)
    ap.add_argument("--synthetic-dir", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    def load_dir(d):
        out = {}
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".json"):
                out[fn] = json.load(open(os.path.join(d, fn)))
        return out

    gts = load_dir(args.gt_dir)
    dumps = load_dir(args.eval_dir)

    def run_split(gt_files, dump_lookup):
        recs, missing = [], []
        for fn, gt in gt_files.items():
            doc = (gt.get("product_code") or "").strip()
            dump = (dump_lookup.get(f"{doc}.v2.json") or dump_lookup.get(f"{doc}.json")
                    or dump_lookup.get(f"{doc}.eval.json"))
            if dump is None:
                missing.append(doc)
                continue
            if gt.get("pdf_sha256") and dump.get("pdf_sha256") != gt["pdf_sha256"]:
                recs.append({"document_id": gt.get("document_id"), "cases": [],
                             "unmatched_eval_balloons": 0, "sha_mismatch": True})
                continue
            recs.append(evaluate_document(gt, dump))
        return recs, missing

    real_recs, missing = run_split(gts, dumps)
    report = {
        "schema": "eva_val01_balloon_gt01_report.v1",
        "metrics_status": "EXPLORATORY_ONLY",
        "gt_approval_status": "OWNER_BLOCKED",
        "real": {"documents": [r["document_id"] for r in real_recs],
                 "missing_eval_dumps": missing,
                 "per_document": real_recs,
                 "metrics": aggregate(real_recs)},
        "synthetic": None,
        "synthetic_swap_cases": 0,
        "real_swap_cases": sum(1 for fn, g in gts.items() for o in g.get("balloon_occurrences", [])
                               if o.get("balloon_relation_status") == "ASSOCIATION_SWAPPED"),
    }
    if args.synthetic_dir and os.path.isdir(args.synthetic_dir):
        syn_files = load_dir(args.synthetic_dir)
        syn_gt = {fn: g for fn, g in syn_files.items() if g.get("synthetic")}
        syn_dumps = dict(dumps)
        syn_dumps.update({fn: g for fn, g in syn_files.items() if fn.endswith(".eval.json")})
        syn_recs, syn_missing = run_split(syn_gt, syn_dumps)
        report["synthetic"] = {"documents": [r["document_id"] for r in syn_recs],
                               "missing_eval_dumps": syn_missing,
                               "per_document": syn_recs,
                               "metrics": aggregate(syn_recs)}
        report["synthetic_swap_cases"] = sum(
            1 for g in syn_gt.values() for o in g.get("balloon_occurrences", [])
            if o.get("balloon_relation_status") == "ASSOCIATION_SWAPPED")

    out = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
