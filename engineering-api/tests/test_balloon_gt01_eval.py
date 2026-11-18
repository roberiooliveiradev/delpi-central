"""Focused tests for the GT-01 offline balloon evaluator.

Exercises the metric machinery on controlled GT/eval pairs — real-looking
consistent cases, ambiguous associations, abstentions and synthetic swapped
balloons — to prove denominators and verdict mapping behave correctly.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[2] /
          "docs/12-roadmap-e-evolucao/engineering/eva-val01-g1/scripts/eval_balloon_gt01.py")


def _gt_doc(code, occurrences, sha="a" * 64):
    return {
        "schema": "eva_val01_balloon_annotation.v1",
        "product_code": code,
        "document_id": f"gt01:{code}",
        "pdf_sha256": sha,
        "balloon_occurrences": occurrences,
    }


def _occ(i, label, bbox, rel, rows=None, target=None):
    return {
        "balloon_occurrence_id": f"{label}:{i}",
        "balloon_label": label,
        "balloon_bbox": bbox,
        "balloon_visual_presence": "PRESENT",
        "table_item_label": label.lower(),
        "table_item_reference": rows,
        "component_code": "X",
        "leader_presence": "PRESENT",
        "target_region": target,
        "balloon_relation_status": rel,
    }


def _eval_entry(label, bbox, cc="INCONCLUSIVE", assoc="MATCH_CANDIDATE",
                table_item=None, table_items=None, target_state="SINGLE_REGION",
                target_px=None):
    return {
        "balloon_label": label.lower(), "normalized_label": label,
        "bounding_box_px": bbox, "state": "BALLOON_LABEL_IDENTIFIED",
        "association": assoc,
        "table_item": table_item,
        "table_items": table_items or [],
        "leader_line": {"state": "CANDIDATE", "target_state": target_state,
                        "target_region_px": target_px},
        "component_consistency": {"state": cc},
    }


def _write_case(tmp_path, code, gt_occ, eval_entries, sha="a" * 64):
    (tmp_path / f"{code}.json").write_text(json.dumps(_gt_doc(code, gt_occ, sha)))
    (tmp_path / f"{code}.v2.json").write_text(json.dumps(
        {"document": code, "pdf_sha256": sha,
         "validation": {"balloons": eval_entries}}))


def _run(tmp_path):
    out = subprocess.run([sys.executable, str(SCRIPT), "--gt-dir", str(tmp_path),
                          "--eval-dir", str(tmp_path)],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_detection_recall_and_abstention(tmp_path):
    # One GT balloon detected (ambiguous target -> correct abstention),
    # one GT balloon missed entirely.
    _write_case(tmp_path, "DOC1", [
        _occ(0, "A", [0, 0, 50, 50], "INSUFFICIENT_EVIDENCE", "row_index:0"),
        _occ(1, "B", [900, 900, 950, 950], "ASSOCIATION_CONSISTENT", "row_index:1"),
    ], [
        _eval_entry("A", [0, 0, 50, 50], table_item={"row_index": 0, "item_label": "a"},
                    target_state="AMBIGUOUS_REGIONS"),
    ])
    r = _run(tmp_path)
    m = r["real"]["metrics"]
    assert m["DETECTION_RECALL"]["numerator"] == 1
    assert m["DETECTION_RECALL"]["denominator"] == 2
    assert m["DETECTION_PRECISION"]["denominator"] == 1
    assert m["CONFLICT_RECALL"]["status"] == "INCONCLUSIVE_NO_DENOMINATOR"


def test_ambiguous_table_rows_counted_as_hit(tmp_path):
    _write_case(tmp_path, "DOC2", [
        _occ(0, "A3", [0, 0, 50, 50], "INSUFFICIENT_EVIDENCE", "row_index:[2,4,7]"),
    ], [
        _eval_entry("A3", [0, 0, 50, 50], assoc="AMBIGUOUS", table_items=[
            {"row_index": r, "item_label": "a3"} for r in (2, 4, 7)]),
    ])
    r = _run(tmp_path)
    m = r["real"]["metrics"]
    assert m["TABLE_ASSOCIATION_ACCURACY"]["numerator"] == 1


def test_false_conflict_counted(tmp_path):
    # GT says consistent; EVA emits CONFLICT_CANDIDATE -> FALSE_CONFLICT.
    _write_case(tmp_path, "DOC3", [
        _occ(0, "A", [0, 0, 50, 50], "ASSOCIATION_CONSISTENT", "row_index:0",
             target=[10, 10, 60, 60]),
    ], [
        _eval_entry("A", [0, 0, 50, 50], cc="CONFLICT_CANDIDATE",
                    table_item={"row_index": 0, "item_label": "a"},
                    target_px=[10, 10, 60, 60]),
    ])
    r = _run(tmp_path)
    case = r["real"]["per_document"][0]["cases"][0]
    assert case["b3_consistency"] == "FALSE_CONFLICT"
    assert r["real"]["metrics"]["FALSE_ALERT_RATE"]["numerator"] == 1


def test_true_conflict_on_swapped_case(tmp_path):
    _write_case(tmp_path, "DOC4", [
        _occ(0, "A", [0, 0, 50, 50], "ASSOCIATION_SWAPPED", "row_index:0",
             target=[10, 10, 60, 60]),
    ], [
        _eval_entry("A", [0, 0, 50, 50], cc="CONFLICT_CANDIDATE",
                    table_item={"row_index": 0, "item_label": "a"},
                    target_px=[10, 10, 60, 60]),
    ])
    r = _run(tmp_path)
    m = r["real"]["metrics"]
    assert m["CONFLICT_PRECISION"]["numerator"] == 1
    assert m["CONFLICT_RECALL"]["numerator"] == 1


def test_extra_eval_balloon_counts_as_detection_fp(tmp_path):
    _write_case(tmp_path, "DOC5", [
        _occ(0, "A", [0, 0, 50, 50], "INSUFFICIENT_EVIDENCE", "row_index:0"),
    ], [
        _eval_entry("A", [0, 0, 50, 50], table_item={"row_index": 0, "item_label": "a"},
                    target_state="AMBIGUOUS_REGIONS"),
        _eval_entry("Z", [700, 700, 760, 760], table_item=None,
                    target_state="NOT_IDENTIFIED"),
    ])
    r = _run(tmp_path)
    m = r["real"]["metrics"]
    assert m["DETECTION_PRECISION"]["denominator"] == 2
    assert m["DETECTION_PRECISION"]["numerator"] == 1


def test_sha_mismatch_blocks_evaluation(tmp_path):
    _write_case(tmp_path, "DOC6", [
        _occ(0, "A", [0, 0, 50, 50], "INSUFFICIENT_EVIDENCE", "row_index:0"),
    ], [
        _eval_entry("A", [0, 0, 50, 50]),
    ], sha="b" * 64)
    (tmp_path / "DOC6.v2.json").write_text(json.dumps(
        {"document": "DOC6", "pdf_sha256": "c" * 64,
         "validation": {"balloons": [_eval_entry("A", [0, 0, 50, 50])]}}))
    r = _run(tmp_path)
    assert r["real"]["per_document"][0].get("sha_mismatch") is True
    assert r["real"]["metrics"]["TOTAL_GT_OCCURRENCES"] == 0
