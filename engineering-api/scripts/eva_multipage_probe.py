#!/usr/bin/env python3
"""EVA VAL-01 F2 — probe multipágina escopado (páginas-alvo somente).

Pipeline real: PDF → PDFium render → PaddleOCR → SLANet →
Understanding → structure_occurrences, mas restrito às páginas
solicitadas (o orçamento do job MCP não cabe em 9-13 páginas no
hardware DEV). Saída: JSON com sha, páginas e ocorrências.
"""
from __future__ import annotations

import hashlib
import json
import sys

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


def main(path: str, code: str, pages: list[int]) -> None:
    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    engine = TableStructureEngine()
    observations = []
    understanding = None
    for page in pages:
        runs = run_visual_benchmark(
            data,
            pipelines=["pdfium_render_paddleocr"],
            isolation="inprocess",
            page_start=page,
            page_end=page,
        )
        best = runs[0]
        tokens = [
            {
                "normalized_text": t.get("normalized_text"),
                "raw_text": t.get("raw_text"),
                "bounding_box_px": t.get("bounding_box_px"),
                "confidence": t.get("confidence"),
                "page": t.get("page", page),
            }
            for t in best.get("_tokens_sample") or []
        ]
        render = {}
        for st in best.get("pages") or []:
            r = st.get("render") or {}
            p = st.get("page")
            if p and r.get("width"):
                render[int(p)] = (int(r["width"]), int(r["height"]))
        page_understanding = build_document_understanding(
            tokens,
            document_hash=sha,
            product_code=code,
            render_size_by_page=render,
            graphic_primitives_by_page=best.get(
                "_graphic_primitives_by_page"
            )
            or {},
        )
        if understanding is None:
            understanding = page_understanding
        else:
            rows = (understanding.get("component_table") or {}).get(
                "rows"
            ) or []
            rows.extend(
                (page_understanding.get("component_table") or {}).get(
                    "rows"
                )
                or []
            )
            understanding["component_table"]["rows"] = rows
        region = next(
            (
                r
                for r in (page_understanding.get("regions") or [])
                if r.get("type") == "component_table" and r.get("box_px")
            ),
            None,
        )
        slanet = engine.run(
            data,
            document_hash_sha256=sha,
            product_code=code,
            pages=[page],
            crop_box=(region or {}).get("box_px"),
            ocr_tokens=tokens,
            expected_render_px=render.get(page),
        )
        observations.append(
            {"region_type": "component_table", "page": page, "result": slanet}
        )
        print(f"page {page}: cells={len(slanet.get('cells') or [])} "
              f"unassigned={len((slanet.get('association') or {}).get('unassigned_tokens') or [])}",
              file=sys.stderr, flush=True)
    applied = apply_native_table_observations(understanding, observations)
    occs = (applied.get("component_table") or {}).get(
        "structure_occurrences"
    ) or []
    out = {
        "sha": sha,
        "product_code": code,
        "pages": pages,
        "occurrence_count": len(occs),
        "occurrences": occs,
        "limitations": applied.get("limitations"),
        "topology_source": (applied.get("component_table") or {}).get(
            "topology_source"
        ),
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], [int(p) for p in sys.argv[3].split(",")])
