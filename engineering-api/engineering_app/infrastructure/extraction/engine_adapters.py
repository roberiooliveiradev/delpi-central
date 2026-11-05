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




def _to_native(obj):
    """Converte numpy scalars/arrays para tipos nativos Python —
    numpy.float32/int64/ndarray quebram o serializer MCP (pydantic)."""
    try:
        import numpy as np
    except ImportError:
        np = None
    if np is not None:
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return [_to_native(x) for x in obj.tolist()]
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(x) for x in obj]
    return obj


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


class DoclingEngine:
    """Motor C — Docling (layout+TableFormer) adaptado ao contrato v1."""

    provider_id = "docling"

    def capability(self) -> dict:
        return capability_descriptor(
            provider_id=self.provider_id,
            provider_version="docling_2.145",
            supports={
                "pdf_native": True, "ocr": True, "layout": True,
                "tables": True, "cells": True, "figures": True,
                "symbols": False, "coords": True, "multipage": True,
                "page_select": True, "local": True, "gpu_required": False,
                "graphic_primitives": False,
            },
            notes=["Docling 2.145 + TableFormer + torch CPU"],
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

            from docling.document_converter import DocumentConverter

            with tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False
            ) as f:
                f.write(pdf_bytes)
                tmp = f.name
            try:
                conv = DocumentConverter()
                res = conv.convert(tmp)
            finally:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
            doc = res.document
            regions: list[dict] = []
            tables: list[dict] = []
            cells: list[dict] = []
            tblocks: list[dict] = []
            for page_item in getattr(doc, "pages", {}) or {}:
                pass
            # itera elementos do documento exportável
            try:
                for item, _ in doc.iterate_items():
                    label = getattr(getattr(item, "label", None), "value", str(getattr(item, "label", "")))
                    prov = (item.prov or [None])[0] if getattr(item, "prov", None) else None
                    bbox = getattr(prov, "bbox", None) if prov else None
                    bb = [bbox.l, bbox.t, bbox.r, bbox.b] if bbox else None
                    if label in ("table", "section_header", "list_item"):
                        regions.append(
                            make_region(
                                region_id=f"doc_{len(regions)}",
                                region_type="unknown",
                                page=getattr(prov, "page_no", 1) if prov else 1,
                                bounding_box_px=bb,
                                evidence=[str(label)],
                            )
                        )
                    if label == "table" and hasattr(item, "data"):
                        grid = getattr(item.data, "grid", None) or []
                        tables.append({"row_count": len(grid), "headers": []})
                        for r_i, row in enumerate(grid):
                            for c_i, cell in enumerate(row or []):
                                cells.append(
                                    make_cell(
                                        row=r_i, col=c_i,
                                        text=getattr(cell, "text", ""),
                                        bounding_box_px=None,
                                    )
                                )
                    elif label in ("text", "paragraph"):
                        tblocks.append(
                            {
                                "text": getattr(item, "text", ""),
                                "bounding_box_px": bb,
                            }
                        )
            except Exception:
                pass
            n_pages = len(getattr(doc, "pages", {}) or {1: 1})
            return make_result(
                provider_id=self.provider_id,
                provider_version="docling_2.145",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                model_version="docling_layout+tableformer",
                execution_mode="local_isolated",
                regions=regions,
                tables=tables,
                cells=cells,
                text_blocks=tblocks[:40],
                provenance=(
                    "api-delpi pdf → Docling (layout+TableFormer) → v1 contract"
                ),
                limitations=["candidates only", "coordenadas em pdf points quando bbox disponível"],
                duration_ms=round((time.monotonic() - t0) * 1000, 1),
                quality_status="EVAL_PENDING",
            )
        except ImportError as exc:
            return make_result(
                provider_id=self.provider_id,
                provider_version="unknown",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                error_kind="MODEL_NOT_PROVISIONED",
                error_detail=f"docling import: {exc}",
                quality_status="FAILED",
                duration_ms=round((time.monotonic() - t0) * 1000, 1),
            )
        except Exception as exc:
            return make_result(
                provider_id=self.provider_id,
                provider_version="docling_2.145",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                error_kind="UNAVAILABLE",
                error_detail=f"{type(exc).__name__}:{exc}",
                quality_status="FAILED",
                duration_ms=round((time.monotonic() - t0) * 1000, 1),
            )


ENGINES["docling"] = DoclingEngine()


class TableStructureEngine:
    """Motor D — PaddleOCR TableStructureRecognition (SLANet) isolado.

    Recebe um recorte de região de tabela (crop) e devolve estrutura
    tabular real (linhas/colunas/células + bbox). CPU, ~0.8GB pico.
    """

    provider_id = "table_structure_slanet"

    def capability(self) -> dict:
        return capability_descriptor(
            provider_id=self.provider_id,
            provider_version="slanet_7.67MB",
            supports={
                "pdf_native": False, "ocr": False, "layout": False,
                "tables": True, "cells": True, "figures": False,
                "symbols": False, "coords": True, "multipage": False,
                "page_select": False, "local": True, "gpu_required": False,
                "graphic_primitives": False,
            },
            notes=["SLANet — estrutura de tabela sobre crop da regiao"],
        )

    def run(
        self,
        pdf_bytes: bytes,
        *,
        document_hash_sha256: str,
        product_code: str | None = None,
        pages: list[int] | None = None,
        crop_box: list | None = None,
    ) -> dict:
        t0 = time.monotonic()
        try:
            import os
            import tempfile

            import numpy as np
            import pypdfium2 as pdfium
            from paddleocr import TableStructureRecognition

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(pdf_bytes)
                tmp = f.name
            try:
                pdf = pdfium.PdfDocument(tmp)
                img = np.array(pdf[0].render(scale=2.7778).to_pil())
            finally:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
            cb = crop_box
            if cb is None:
                # Fail-closed: sem região de tabela detectada por
                # evidência, coordenadas fixas fabricariam estrutura em
                # área arbitrária da folha.
                return make_result(
                    provider_id=self.provider_id,
                    provider_version="slanet_7.67MB",
                    document_hash_sha256=document_hash_sha256,
                    product_code=product_code,
                    model_version="SLANet",
                    execution_mode="local_isolated",
                    error_kind="NO_TABLE_REGION",
                    error_detail=(
                        "Sem região de tabela detectada — recorte "
                        "arbitrário removido (região deve derivar de "
                        "evidência, não de coordenadas fixas)"
                    ),
                    quality_status="FAILED",
                    duration_ms=round((time.monotonic() - t0) * 1000, 1),
                )
            crop = img[cb[1] : cb[3], cb[0] : cb[2]]
            # RQ-01: tokens OCR reais via pipeline governado (não só amostra)
            from engineering_app.infrastructure.extraction.subprocess_executor import (  # noqa: E501
                run_pipeline_isolated,
            )
            from engineering_app.application.drawing.perception_contract import (
                associate_tokens_to_cells,
            )
            rec = run_pipeline_isolated(
                pdf_bytes, pipeline_id="pdfium_render_paddleocr", timeout_s=190
            )
            ocr_tokens = rec.get("_tokens_sample") or []
            eng = TableStructureRecognition()
            out = eng.predict(input=crop)
            tables = []
            cells = []
            cell_bboxes = []
            for res in out or []:
                r = res if isinstance(res, dict) else res.json
                st = r.get("structure") or []
                tables.append(
                    {
                        "row_count": st.count("<tr>"),
                        "headers": [],
                        "structure_score": _to_native(
                            r.get("structure_score")
                        ),
                    }
                )
                for bb in r.get("bbox") or []:
                    cell_bboxes.append(bb)
            # RQ-02: associação OCR↔célula determinística
            assoc = associate_tokens_to_cells(
                ocr_tokens, cell_bboxes, crop_offset=(cb[0], cb[1])
            )
            cmap = assoc["cell_token_map"]
            for i, bb in enumerate(cell_bboxes):
                tis = cmap.get(str(i)) or []
                text = " ".join(
                    (ocr_tokens[ti].get("raw_text") or ocr_tokens[ti].get("normalized_text") or "")
                    for ti in tis
                    if ti < len(ocr_tokens)
                ).strip()
                cells.append(
                    make_cell(
                        row=i // 8,
                        col=i % 8,
                        text=text,
                        bounding_box_px=list(bb) if bb else None,
                        ambiguous=bool(
                            any(c["token_index"] in tis for c in assoc["conflicts"])
                        ),
                    )
                )
            _res = make_result(
                provider_id=self.provider_id,
                provider_version="slanet_7.67MB",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                model_version="SLANet",
                execution_mode="local_isolated",
                tables=tables,
                cells=cells,
                provenance="api-delpi pdf → render → table crop → SLANet → OCR-cell assoc → v1",
                limitations=[
                    "candidates only",
                    "estrutura tabular sem texto — OCR associa depois",
                ],
                duration_ms=round((time.monotonic() - t0) * 1000, 1),
                quality_status="EVAL_PENDING",
            )
            # DEC-VAL-034/FF-01 — a associação OCR↔célula era calculada
            # e descartada; o relatório já lê association.unassigned /
            # .conflicts. Propagar o que o framework produziu.
            _res["association"] = {
                "unassigned": assoc.get("unassigned") or [],
                "conflicts": assoc.get("conflicts") or [],
            }
            return _res
        except ImportError as exc:
            return make_result(
                provider_id=self.provider_id,
                provider_version="unknown",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                error_kind="MODEL_NOT_PROVISIONED",
                error_detail=str(exc),
                quality_status="FAILED",
                duration_ms=round((time.monotonic() - t0) * 1000, 1),
            )
        except Exception as exc:
            return make_result(
                provider_id=self.provider_id,
                provider_version="slanet_7.67MB",
                document_hash_sha256=document_hash_sha256,
                product_code=product_code,
                error_kind="UNAVAILABLE",
                error_detail=f"{type(exc).__name__}:{exc}",
                quality_status="FAILED",
                duration_ms=round((time.monotonic() - t0) * 1000, 1),
            )


ENGINES["table_structure_slanet"] = TableStructureEngine()
