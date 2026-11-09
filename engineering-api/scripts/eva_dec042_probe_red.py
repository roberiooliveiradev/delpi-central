#!/usr/bin/env python3
"""DEC-042 offline RED probe on official PDF — not a production entrypoint."""
from __future__ import annotations

import hashlib
import json
import sys

from engineering_app.application.drawing.understanding import (
    apply_native_table_observations,
    build_document_understanding,
    rows_from_native_cells,
)
from engineering_app.application.drawing.visual_benchmark import (
    run_visual_benchmark,
)
from engineering_app.infrastructure.extraction.engine_adapters import (
    TableStructureEngine,
)

EXPECTED_SHA = (
    "4d0c2e2f173cb2a427bb8de9b890018f9ca496b09b803b92e52ac0bf075dfec4"
)


def main(path: str, code: str) -> None:
    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXPECTED_SHA and code == "90264026":
        raise SystemExit(f"sha mismatch: {sha}")
    runs = run_visual_benchmark(
        data,
        pipelines=["pdfium_render_paddleocr"],
        isolation="inprocess",
        page_start=1,
        page_end=1,
    )
    best = runs[0]
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
    fallback = (understanding.get("component_table") or {}).get("rows") or []
    region = next(
        (
            r
            for r in (understanding.get("regions") or [])
            if r.get("type") == "component_table" and r.get("box_px")
        ),
        None,
    )
    engine = TableStructureEngine()
    slanet = engine.run(
        data,
        document_hash_sha256=sha,
        product_code=code,
        pages=[1],
        crop_box=(region or {}).get("box_px"),
        ocr_tokens=tokens,
        expected_render_px=render.get(1),
    )
    tables = slanet.get("tables") or []
    cells = slanet.get("cells") or []
    native_rows, _ = rows_from_native_cells(cells, page=1)
    applied = apply_native_table_observations(
        understanding,
        [{"region_type": "component_table", "page": 1, "result": slanet}],
    )
    applied_rows = (
        (applied.get("component_table") or {}).get("rows") or []
    )
    out = {
        "sha": sha,
        "structure_consistent": (tables[0] if tables else {}).get(
            "structure_consistent"
        ),
        "structure_limitations": (tables[0] if tables else {}).get(
            "structure_limitations"
        ),
        "cell_count": len(cells),
        "fallback": [
            {
                "item": r.get("item"),
                "code": r.get("component_code"),
                "desc": r.get("description"),
            }
            for r in fallback
        ],
        "native": [
            {
                "item": r.get("item"),
                "code": r.get("component_code"),
                "desc": r.get("description"),
                "group": r.get("parent_group_candidate"),
                "status": r.get("association_status"),
            }
            for r in native_rows
        ],
        "applied": [
            {
                "item": r.get("item"),
                "code": r.get("component_code"),
                "desc": r.get("description"),
            }
            for r in applied_rows
        ],
        "limitations": applied.get("limitations"),
        "topology_source": (applied.get("component_table") or {}).get(
            "topology_source"
        ),
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
