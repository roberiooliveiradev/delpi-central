#!/usr/bin/env python3
"""DEC-042 critical regression checks on official PDFs — offline."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time

from engineering_app.application.drawing.understanding import (
    apply_native_table_observations,
    build_document_understanding,
)
from engineering_app.application.drawing.visual_benchmark import (
    run_visual_benchmark,
)
from engineering_app.infrastructure.extraction.engine_adapters import (
    TableStructureEngine,
)

EXPECTED = {
    "90264026": (
        "4d0c2e2f173cb2a427bb8de9b890018f9ca496b09b803b92e52ac0bf075dfec4",
        1,
        1,
    ),
    "90264004": (
        "5b6717dfa7b8dcdc18f81b4657e1dcdf3410b9af42c8cf3109214df2f66719f4",
        1,
        1,
    ),
    "90264017": (
        "5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee",
        9,
        9,
    ),
    "90264135": (
        "af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3",
        10,
        13,
    ),
}
FUSED = re.compile(r"\b\d{6,11}(?:\s+\d{6,11})+\b")


def _run(path: str, code: str, start: int, end: int) -> dict:
    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    expected_sha, _, _ = EXPECTED[code]
    t0 = time.monotonic()
    runs = run_visual_benchmark(
        data,
        pipelines=["pdfium_render_paddleocr"],
        isolation="inprocess",
        page_start=start,
        page_end=end,
    )
    best = runs[0] if runs else {}
    tokens = []
    for t in best.get("_tokens_sample") or []:
        tokens.append(
            {
                "normalized_text": t.get("normalized_text"),
                "raw_text": t.get("raw_text"),
                "bounding_box_px": t.get("bounding_box_px"),
                "confidence": t.get("confidence"),
                "page": t.get("page", 1),
            }
        )
    render = {}
    for st in best.get("pages") or []:
        r = st.get("render") or {}
        p = st.get("page")
        if p and r.get("width"):
            render[int(p)] = (int(r["width"]), int(r["height"]))
    understanding = build_document_understanding(
        tokens,
        document_hash=sha,
        product_code=code,
        render_size_by_page=render,
        graphic_primitives_by_page=best.get("_graphic_primitives_by_page")
        or {},
    )
    engine = TableStructureEngine()
    observations = []
    regions = [
        region
        for region in (understanding.get("regions") or [])
        if region.get("type") == "component_table" and region.get("box_px")
    ]
    pages = sorted({int(r.get("page") or start) for r in regions}) or list(
        range(start, end + 1)
    )
    for page in pages:
        if page < start or page > end:
            continue
        region = next(
            (r for r in regions if int(r.get("page") or 0) == page),
            None,
        )
        sl = engine.run(
            data,
            document_hash_sha256=sha,
            product_code=code,
            pages=[page],
            crop_box=(region or {}).get("box_px"),
            ocr_tokens=[
                t for t in tokens if int(t.get("page") or 1) == page
            ],
            expected_render_px=render.get(page),
        )
        observations.append(
            {
                "region_type": "component_table",
                "page": page,
                "result": sl,
            }
        )
    understanding = apply_native_table_observations(
        understanding, observations
    )
    rows = (understanding.get("component_table") or {}).get("rows") or []
    brief = []
    for r in rows:
        brief.append(
            {
                "page": r.get("page"),
                "item": r.get("item"),
                "qty": r.get("quantity"),
                "code": r.get("component_code"),
                "desc": r.get("description"),
                "group": r.get("parent_group_candidate"),
                "status": r.get("association_status"),
                "conflict": bool(r.get("association_conflict")),
            }
        )
    return {
        "code": code,
        "sha256": sha,
        "sha_match": sha == expected_sha,
        "elapsed_s": round(time.monotonic() - t0, 1),
        "topology_source": (understanding.get("component_table") or {}).get(
            "topology_source"
        ),
        "limitations": understanding.get("limitations") or [],
        "rows": brief,
        "metrics": {
            "rows": len(brief),
            "with_item": sum(1 for r in brief if r.get("item")),
            "with_code": sum(1 for r in brief if r.get("code")),
            "with_desc": sum(1 for r in brief if r.get("desc")),
            "fused_codes": sum(
                1 for r in brief if FUSED.search(str(r.get("code") or ""))
            ),
            "conflicts": sum(1 for r in brief if r.get("conflict")),
            "false_g9": sum(
                1
                for r in brief
                if str(r.get("item") or "").upper() == "G"
                and str(r.get("qty") or "") == "9"
                and str(r.get("code") or "") == "10110676"
            ),
            "chicote_on_item": sum(
                1
                for r in brief
                if r.get("item") and "CHICOTE" in str(r.get("desc") or "").upper()
            ),
        },
    }


def _checks(report: dict) -> dict:
    code = report["code"]
    rows = report.get("rows") or []
    by_item = {}
    for r in rows:
        item = str(r.get("item") or "").upper()
        if item:
            by_item.setdefault(item, []).append(r)
    out = {"code": code, "sha_match": report.get("sha_match")}
    if code == "90264026":
        b = (by_item.get("B") or [{}])[0]
        out["B_code"] = b.get("code")
        out["B_desc_ok"] = "ISOLADOR" in str(b.get("desc") or "").upper()
        out["no_fused_b"] = "90264026" not in str(b.get("code") or "")
        out["pass"] = (
            b.get("code") == "10090010"
            and out["B_desc_ok"]
            and out["no_fused_b"]
        )
    elif code == "90264017":
        want = {
            "C": ("6", "10081389"),
            "D": ("3", "10081685"),
            "E": ("2", "10091368"),
            "F": ("9", "10110676"),
            "G": ("3", "10110679"),
            "K": ("2", "10130020"),
        }
        ok = True
        detail = {}
        for item, (qty, code_v) in want.items():
            hits = [
                r
                for r in by_item.get(item, [])
                if str(r.get("qty") or "") == qty
                and str(r.get("code") or "") == code_v
            ]
            detail[item] = bool(hits)
            ok = ok and bool(hits)
        out["tuples"] = detail
        out["false_g9"] = report["metrics"]["false_g9"]
        out["pass"] = ok and report["metrics"]["false_g9"] == 0
    elif code == "90264004":
        a9 = by_item.get("A9") or []
        aa = by_item.get("AA") or []
        out["a9_count"] = len(a9)
        out["aa_count"] = len(aa)
        out["false_g9"] = report["metrics"]["false_g9"]
        out["chicote_on_item"] = report["metrics"]["chicote_on_item"]
        out["pass"] = (
            len(a9) >= 2
            and len(aa) >= 2
            and report["metrics"]["false_g9"] == 0
            and report["metrics"]["chicote_on_item"] == 0
        )
    elif code == "90264135":
        out["metrics"] = report["metrics"]
        out["pass"] = report.get("sha_match") is True
        out["note"] = "diagnostic residual; gate not required to fix fused cells"
    return out


def main() -> None:
    code = sys.argv[1]
    path = sys.argv[2]
    _, start, end = EXPECTED[code]
    report = _run(path, code, start, end)
    print(
        json.dumps(
            {"report": report, "checks": _checks(report)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
