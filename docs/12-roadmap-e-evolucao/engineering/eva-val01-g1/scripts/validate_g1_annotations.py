#!/usr/bin/env python3
"""Offline integrity checker for EVA VAL-01 G1 annotation JSON artifacts.

Abstraction Gate: G1 evaluation packaging only. No perception, no product
runtime dependency, no import of engineering_app. Validates DRAFT geometry
artifacts against schema invariants required by Doc 119 §60 / G1-R07.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SCHEMA = "eva_val01_g1_page_annotation.v1"
FORBIDDEN_EXPECTED_CODES = {"10080192 10090316", "4 5"}
COVERAGE_VALUES = {
    "FULL_TABLE",
    "COMPLETE_SELECTED_REGION",
    "SELECTED_ROWS_ONLY",
    "PARTIAL_AMBIGUOUS",
}


def _err(errors: list[str], msg: str) -> None:
    errors.append(msg)


def validate_page(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 — report as validation failure
        return [f"{path.name}: invalid JSON ({exc})"]

    if data.get("schema") != SCHEMA:
        _err(errors, f"{path.name}: unexpected schema {data.get('schema')!r}")
    if data.get("annotation_status") != "DRAFT":
        _err(errors, f"{path.name}: annotation_status must remain DRAFT until owner approval")
    if data.get("gt_approval_status") != "OWNER_BLOCKED":
        _err(errors, f"{path.name}: gt_approval_status must be OWNER_BLOCKED without owner signature")

    pdf_sha = data.get("pdf_sha256")
    if not isinstance(pdf_sha, str) or len(pdf_sha) != 64:
        _err(errors, f"{path.name}: missing/invalid pdf_sha256")

    render = data.get("render_ref") or {}
    size = render.get("size_px") or [None, None]
    img_w, img_h = size[0], size[1]
    dpi = render.get("dpi")
    if dpi != 200:
        _err(errors, f"{path.name}: render_ref.dpi expected 200, got {dpi!r}")

    tables = data.get("tables") or []
    if not tables:
        _err(errors, f"{path.name}: no tables[]")
        return errors

    cell_ids: set[str] = set()
    for table in tables:
        tid = table.get("table_id")
        rows = table.get("row_count")
        cols = table.get("column_count")
        rb = table.get("row_boundaries") or []
        cb = table.get("column_boundaries") or []
        cov = table.get("annotation_coverage")
        if cov not in COVERAGE_VALUES:
            _err(errors, f"{path.name}/{tid}: invalid annotation_coverage {cov!r}")
        for field in (
            "expected_row_count",
            "annotated_row_count",
            "unannotated_row_ranges",
            "coverage_limitations",
        ):
            if field not in table:
                _err(errors, f"{path.name}/{tid}: missing coverage field {field}")

        if not isinstance(rows, int) or not isinstance(cols, int):
            _err(errors, f"{path.name}/{tid}: row_count/column_count must be int")
            continue
        if len(rb) != rows + 1:
            _err(errors, f"{path.name}/{tid}: row_boundaries length {len(rb)} != row_count+1 ({rows + 1})")
        if len(cb) != cols + 1:
            _err(errors, f"{path.name}/{tid}: column_boundaries length {len(cb)} != column_count+1 ({cols + 1})")
        if any(rb[i] >= rb[i + 1] for i in range(len(rb) - 1)):
            _err(errors, f"{path.name}/{tid}: non-increasing row_boundaries")
        if any(cb[i] >= cb[i + 1] for i in range(len(cb) - 1)):
            _err(errors, f"{path.name}/{tid}: non-increasing column_boundaries")

        bbox = table.get("table_bounding_box_px") or [0, 0, 0, 0]
        if len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            _err(errors, f"{path.name}/{tid}: invalid table_bounding_box_px {bbox}")
        if img_w and img_h and (bbox[0] < 0 or bbox[1] < 0 or bbox[2] > img_w or bbox[3] > img_h):
            _err(errors, f"{path.name}/{tid}: table bbox outside image {size}")

        occupancy: dict[tuple[int, int], str] = {}
        cells = table.get("cells") or []
        for cell in cells:
            cid = cell.get("cell_id")
            if not cid:
                _err(errors, f"{path.name}/{tid}: cell without cell_id")
                continue
            if cid in cell_ids:
                _err(errors, f"{path.name}: duplicate cell_id {cid}")
            cell_ids.add(cid)

            r = cell.get("row_index")
            c = cell.get("col_index")
            rs = cell.get("rowspan") or 1
            cs = cell.get("colspan") or 1
            if not isinstance(r, int) or not isinstance(c, int):
                _err(errors, f"{path.name}/{cid}: invalid indices")
                continue
            if r < 0 or c < 0 or r + rs > rows or c + cs > cols:
                _err(errors, f"{path.name}/{cid}: span out of grid r={r} c={c} rs={rs} cs={cs}")
            for rr in range(r, r + rs):
                for cc in range(c, c + cs):
                    key = (rr, cc)
                    if key in occupancy:
                        _err(
                            errors,
                            f"{path.name}/{tid}: occupancy conflict {key} "
                            f"{occupancy[key]} vs {cid}",
                        )
                    occupancy[key] = cid

            bb = cell.get("bounding_box_px") or [0, 0, 0, 0]
            if len(bb) != 4 or bb[0] >= bb[2] or bb[1] >= bb[3]:
                _err(errors, f"{path.name}/{cid}: inverted/invalid bounding_box_px {bb}")
            if img_w and img_h and (bb[0] < 0 or bb[1] < 0 or bb[2] > img_w or bb[3] > img_h):
                _err(errors, f"{path.name}/{cid}: bbox outside image")

            lit = cell.get("text_literal")
            role = cell.get("role")
            if role == "component_code" and lit in FORBIDDEN_EXPECTED_CODES:
                _err(errors, f"{path.name}/{cid}: forbidden eva_defect_contrast value in expected ({lit})")
            if cell.get("review_status") not in (None, "DRAFT", "APPROVED", "REJECTED"):
                _err(errors, f"{path.name}/{cid}: unexpected review_status")

        # Coverage of selected region: every grid slot occupied exactly once
        expected_slots = rows * cols
        if len(occupancy) != expected_slots:
            _err(
                errors,
                f"{path.name}/{tid}: occupancy {len(occupancy)} != rows*cols {expected_slots}",
            )

    # Relations: parent groups / occurrences refer to existing ids when present
    group_ids = {g.get("group_id") for g in (data.get("parent_groups") or []) if g.get("group_id")}
    for occ in data.get("component_occurrences") or []:
        parent = occ.get("parent_group_id")
        if parent and group_ids and parent not in group_ids and parent != "UNKNOWN":
            _err(errors, f"{path.name}: occurrence parent_group_id missing {parent}")

    # Defect contrast must not leak into expected literals as component_code (already checked)
    for defect in data.get("eva_defect_contrast") or []:
        if defect.get("use_as_expected") is True:
            _err(errors, f"{path.name}: eva_defect_contrast marked use_as_expected=true")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--annotations-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "annotations",
    )
    args = parser.parse_args()
    files = sorted(args.annotations_dir.glob("90264135_p*.json"))
    if not files:
        print(f"FAIL: no annotation files in {args.annotations_dir}", file=sys.stderr)
        return 2
    all_errors: list[str] = []
    for path in files:
        errs = validate_page(path)
        status = "PASS" if not errs else "FAIL"
        print(f"{status} {path.name}")
        for e in errs:
            print(f"  - {e}")
            all_errors.append(e)
    if all_errors:
        print(f"SUMMARY FAIL errors={len(all_errors)}")
        return 1
    print(f"SUMMARY PASS files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
