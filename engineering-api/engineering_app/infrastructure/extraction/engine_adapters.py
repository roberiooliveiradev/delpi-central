"""Perception engine adapters — R9 multi-engine laboratory.

Adapters independentes que executam motores e normalizam para
``drawing_perception_candidate.v1``. Infraestrutura — única camada
que pode importar cv2/paddleocr. Cada motor é fail-safe: falha
retorna erro tipado no contrato, nunca compromete os demais.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from engineering_app.application.drawing.perception_contract import (
    capability_descriptor,
    make_cell,
    make_region,
    make_result,
)


class EvaBaselineEngine:
    """Motor A — pipeline governado existente (PDFium+PaddleOCR+
    OpenCV+understanding.v1) adaptado ao contrato comum."""

    provider_id = "eva_baseline_r823"

    def capability(self) -> dict:
        return capability_descriptor(
            provider_id=self.provider_id,
            provider_version="r8.2.3",
            supports={
                "pdf_native": True, "ocr": True, "layout": True,
                "tables": True, "cells": True, "figures": False,
                "symbols": False, "coords": True, "multipage": False,
                "page_select": True, "local": True, "gpu_required": False,
                "graphic_primitives": True,
            },
            notes=["baseline R8.2.3 — heurísticas+OpenCV+labels"],
        )

    def run(
        self,
        pdf_bytes: bytes,
        *,
        document_hash_sha256: str,
        product_code: str | None = None,
        pages: list[int] | None = None,
    ) -> dict:
        t0 = time.monotonic()
        try:
            from engineering_app.infrastructure.extraction.subprocess_executor import (  # noqa: E501
                run_pipeline_isolated,
            )
            from engineering_app.application.drawing.understanding import (  # noqa: E501
                build_understanding,
            )

            rec = run_pipeline_isolated(
                pdf_bytes,
                pipeline_id="pdfium_render_paddleocr",
                timeout_s=180,
            )
            toks = rec.get("_tokens_sample") or []
            u = build_understanding(
                toks,
                document_hash=document_hash_sha256,
                product_code=product_code,
                render_size_px=(
                    tuple(rec.get("page_size_px"))
                    if rec.get("page_size_px")
                    else None
                ),
                graphic_primitives=rec.get("_graphic_primitives"),
            )
            regions = [
                make_region(
                    region_id=r["id"],
                    region_type=r["type"],
                    page=1,
                    bounding_box_px=r["box_px"],
                    evidence=r.get("evidence") or [],
                    token_count=r["token_count"],
                )
                for r in u["regions"]
            ]
            cells = [
                make_cell(
                    row=row_i,
                    col=c["col"],
                    text=c["text"],
                    bounding_box_px=c["bounding_box_px"],
                    col_type=c.get("col_type"),
                    ambiguous=c.get("ambiguous", False),
                )
                for row_i, row in enumerate(
                    u["component_table"]["rows"]
                )
                for c in row["cells"]
            ]
            dims = u["dimension_candidates"]
            revs = u["revision_candidates"]
            return make_result(
                provider_id=self.provider_id,
                provider_version="r8.2.3",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                model_version="paddleocr_3.3.0+r823_heuristics",
                execution_mode="local_isolated",
                page_width_px=(
                    rec.get("page_size_px") or [None, None]
                )[0],
                page_height_px=(
                    rec.get("page_size_px") or [None, None]
                )[1],
                regions=regions,
                tables=[
                    {
                        "row_count": u["component_table"]["row_count"],
                        "headers": u["component_table"]["headers"],
                        "col_types": u["component_table"]["col_types"],
                        "graphic_boundary": u["component_table"][
                            "graphic_boundary"
                        ],
                        "boundary_source": u["component_table"][
                            "boundary_source"
                        ],
                    }
                ],
                cells=cells,
                dimension_candidates=dims,
                text_blocks=[
                    {
                        "text": t.get("raw_text") or t.get("normalized_text"),
                        "bounding_box_px": t.get("bounding_box_px"),
                        "confidence": t.get("confidence"),
                    }
                    for t in toks[:30]
                ],
                provenance=(
                    "api-delpi pdf → PDFium render → PaddleOCR subprocess "
                    "→ OpenCV primitives → understanding.v1 → v1 contract"
                ),
                limitations=[
                    "candidates only — nunca fatos oficiais",
                    "confidence OCR não é aprovação técnica",
                    f"revisões: {len(revs)}",
                    u["component_table"].get(
                        "unreliable_boundary"
                    )
                    and "unreliable_boundary"
                    or None,
                ],
                duration_ms=round(
                    (time.monotonic() - t0) * 1000, 1
                ),
                memory_peak_kb=rec.get("memory_peak_kb"),
                error_kind=(
                    None
                    if rec.get("status") in {"ok", "partial"}
                    else "UNAVAILABLE"
                ),
                error_detail=rec.get("error"),
                quality_status="EVAL_PENDING",
            )
        except Exception as exc:
            return make_result(
                provider_id=self.provider_id,
                provider_version="r8.2.3",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                error_kind="UNAVAILABLE",
                error_detail=f"{type(exc).__name__}:{exc}",
                quality_status="FAILED",
                duration_ms=round((time.monotonic() - t0) * 1000, 1),
            )


class PPStructureEngine:
    """Motor B — PP-StructureV3 (PaddleOCR layout+table) adaptado.

    Local, isolado por processo quando possível; falha → erro tipado.
    """

    provider_id = "pp_structure_v3"

    def capability(self) -> dict:
        return capability_descriptor(
            provider_id=self.provider_id,
            provider_version="paddleocr_3.3.0",
            supports={
                "pdf_native": True, "ocr": True, "layout": True,
                "tables": True, "cells": True, "figures": True,
                "symbols": False, "coords": True, "multipage": True,
                "page_select": True, "local": True, "gpu_required": False,
                "graphic_primitives": False,
            },
            notes=["PP-StructureV3 — layout+table structure"],
        )

    def run(
        self,
        pdf_bytes: bytes,
        *,
        document_hash_sha256: str,
        product_code: str | None = None,
        pages: list[int] | None = None,
    ) -> dict:
        t0 = time.monotonic()
        try:
            import os
            import tempfile

            from paddleocr import PPStructureV3  # noqa: E501

            os.environ.setdefault(
                "DISABLE_MODEL_SOURCE_CHECK", "True"
            )
            engine = PPStructureV3()
            with tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False
            ) as f:
                f.write(pdf_bytes)
                tmp = f.name
            try:
                out = engine.predict(input=tmp)
            finally:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
            regions: list[dict] = []
            cells: list[dict] = []
            tables: list[dict] = []
            n_pages = 0
            for res in out or []:
                n_pages += 1
                try:
                    payload = res if isinstance(res, dict) else getattr(
                        res, "json", {}
                    )
                    if hasattr(payload, "get_res"):
                        payload = payload.get_res()
                    for blk in (payload.get("layout_det_res") or []):
                        box = blk.get("coordinate") or blk.get("bbox")
                        regions.append(
                            make_region(
                                region_id=f"pps_{blk.get('order',len(regions))}",
                                region_type="unknown",
                                page=n_pages,
                                bounding_box_px=list(box)
                                if box
                                else None,
                                evidence=[blk.get("label", "")],
                            )
                        )
                    for tbl in (payload.get("table_res_list") or []):
                        tcells = []
                        for cell in tbl.get("cell_box_list") or []:
                            tcells.append({"box": cell})
                        tables.append(
                            {
                                "row_count": len(tbl.get("pred_html") or [])
                                or len(tcells),
                                "headers": [],
                                "cells_raw": len(tcells),
                            }
                        )
                except Exception:
                    pass
            return make_result(
                provider_id=self.provider_id,
                provider_version="paddleocr_3.3.0",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                model_version="PP-StructureV3",
                execution_mode="local_isolated",
                regions=regions,
                tables=tables,
                cells=cells,
                provenance=(
                    "api-delpi pdf → PP-StructureV3 (layout+table) "
                    "→ v1 contract"
                ),
                limitations=[
                    "candidates only",
                    "regiões não tipadas semanticamente (layout genérico)",
                ],
                duration_ms=round((time.monotonic() - t0) * 1000, 1),
                quality_status="EVAL_PENDING",
            )
        except ImportError:
            return make_result(
                provider_id=self.provider_id,
                provider_version="unknown",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                error_kind="MODEL_NOT_PROVISIONED",
                error_detail="paddleocr PPStructureV3 não disponível",
                quality_status="FAILED",
                duration_ms=round((time.monotonic() - t0) * 1000, 1),
            )
        except Exception as exc:
            return make_result(
                provider_id=self.provider_id,
                provider_version="paddleocr_3.3.0",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                error_kind="UNAVAILABLE",
                error_detail=f"{type(exc).__name__}:{exc}",
                quality_status="FAILED",
                duration_ms=round((time.monotonic() - t0) * 1000, 1),
            )


ENGINES: dict[str, Any] = {
    "eva_baseline_r823": EvaBaselineEngine(),
    "pp_structure_v3": PPStructureEngine(),
}


def engine_capabilities() -> dict[str, dict]:
    return {k: v.capability() for k, v in ENGINES.items()}
