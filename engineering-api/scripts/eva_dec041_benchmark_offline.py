"""DEC-VAL-041 offline benchmark helpers — not a production entrypoint.

Read-only probes for PP-StructureV3 and selective VLM hypothesis checks.
Does not mutate production association logic.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import traceback


def run_ppstructure(path: str, product_code: str) -> dict:
    from engineering_app.infrastructure.extraction.engine_adapters import (
        PPStructureEngine,
    )

    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    eng = PPStructureEngine()
    t0 = time.monotonic()
    try:
        result = eng.run(
            data,
            document_hash_sha256=sha,
            product_code=product_code,
            pages=[1],
        )
    except Exception:
        return {
            "sha": sha,
            "error": traceback.format_exc()[-2000:],
            "duration_ms": round((time.monotonic() - t0) * 1000),
        }
    return {
        "sha": sha,
        "duration_ms": round((time.monotonic() - t0) * 1000),
        "error_kind": result.get("error_kind"),
        "error_detail": (result.get("error_detail") or "")[:500],
        "quality_status": result.get("quality_status"),
        "regions": len(result.get("regions") or []),
        "tables": result.get("tables") or [],
        "cells": len(result.get("cells") or []),
        "limitations": result.get("limitations"),
    }


def probe_structure_consistent(path: str, product_code: str) -> dict:
    """Explain why SLANet structure_consistent is false for page 1."""
    from engineering_app.application.drawing.visual_benchmark import (
        run_visual_benchmark,
    )
    from engineering_app.application.drawing.understanding import (
        build_document_understanding,
    )
    from engineering_app.infrastructure.extraction.engine_adapters import (
        TableStructureEngine,
    )
    from engineering_app.application.drawing.perception_contract import (
        cells_from_html_structure,
    )

    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
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
        product_code=product_code,
        render_size_by_page=render,
        graphic_primitives_by_page=best.get("_graphic_primitives_by_page")
        or {},
    )
    region = next(
        (
            r
            for r in (understanding.get("regions") or [])
            if r.get("type") == "component_table" and r.get("box_px")
        ),
        None,
    )
    engine = TableStructureEngine()
    sl = engine.run(
        data,
        document_hash_sha256=sha,
        product_code=product_code,
        pages=[1],
        crop_box=(region or {}).get("box_px"),
        ocr_tokens=tokens,
        expected_render_px=render.get(1),
    )
    tables = sl.get("tables") or []
    return {
        "sha": sha,
        "region": (region or {}).get("box_px"),
        "error_kind": sl.get("error_kind"),
        "cell_count": len(sl.get("cells") or []),
        "tables": tables,
        "limitations": sl.get("limitations") or [],
        "sample_cells": [
            {
                "row": c.get("row"),
                "col": c.get("col"),
                "text": (c.get("text") or "")[:80],
                "ambiguous": c.get("ambiguous"),
            }
            for c in (sl.get("cells") or [])[:12]
        ],
    }


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "ppstructure":
        print(json.dumps(run_ppstructure(sys.argv[2], sys.argv[3]), ensure_ascii=False))
    elif cmd == "slanet_gate":
        print(
            json.dumps(
                probe_structure_consistent(sys.argv[2], sys.argv[3]),
                ensure_ascii=False,
            )
        )
    else:
        raise SystemExit(f"unknown command {cmd}")
