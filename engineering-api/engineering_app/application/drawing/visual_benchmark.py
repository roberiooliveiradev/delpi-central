"""Visual-perception benchmark harness — experimental pipelines (R7).

Chains governed stages resolved through the infrastructure catalogs:
PDFium render → optional OpenCV preprocessing → PaddleOCR. Every run
record keeps document identity, page/region, coordinate transform,
provider + model provenance and honest limitations — OCR output is
coverage evidence, never official engineering fact.

Same rules as ``benchmark.py``: same bytes for every pipeline, JSONL
serialization strips ``_`` transient keys, quality stays
``metric_not_available`` without owner-approved ground truth.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from engineering_app.infrastructure.extraction.registry import (
    resolve_visual_provider,
)
from engineering_app.application.drawing.extraction_ports import (
    max_render_pages,
    token_sample_limit,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    PdfExtractionError,
)

_RETRY_DPI = 110  # retry único em falhas de recurso (dense pages)
_STRIP_BANDS = 3  # faixas horizontais no retry (preserva resolução)


def _ocr_in_strips(
    image_bytes: bytes, ocr: Any, bands: int = _STRIP_BANDS,
    overlap: float = 0.15,
) -> Any:
    """OCR por faixas horizontais sobrepostas — cada chamada usa ~1/bands
    da memória; tokens voltam com offsets de Y aplicados ao sistema da
    página. Retorna um OcrResult agregado."""
    import io

    import cv2
    import numpy as np

    from engineering_app.application.drawing.extraction_ports import (
        OcrResult,
        OcrToken,
    )

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    height, width = int(img.shape[0]), int(img.shape[1])
    step = height / bands
    pad = int(step * overlap)
    tokens: list[OcrToken] = []
    texts: list[str] = []
    duration = 0
    provider_id = ""
    limitations: list[str] = []
    metadata: dict[str, Any] = {}
    for b in range(bands):
        y0 = max(0, int(b * step) - pad)
        y1 = min(height, int((b + 1) * step) + pad)
        strip = img[y0:y1, :]
        ok, buf = cv2.imencode(".png", strip)
        if not ok:
            continue
        res = ocr.extract_text(buf.tobytes())
        if res is None:
            continue
        provider_id = res.provider_id or provider_id
        metadata = res.metadata or metadata
        duration += res.duration_ms or 0
        texts.append(res.text or "")
        for t in res.tokens or []:
            box = t.box
            if box and len(box) >= 4:
                box = [
                    box[0], box[1] + y0, box[2], box[3] + y0,
                ]
            tokens.append(
                OcrToken(text=t.text, confidence=t.confidence, box=box)
            )
        for lim in res.limitations or []:
            limitations.append(f"band{b}:{lim}")
    if not tokens:
        return None
    return OcrResult(
        provider_id=provider_id or "strip_retry",
        text="\n".join(texts),
        tokens=tokens,
        duration_ms=duration,
        limitations=limitations + [f"strips:{bands}x_overlap"],
        metadata=metadata,
    )


def _is_resource_error(exc: Exception) -> bool:
    """Falha de recurso (memória/limite de imagem) — elegível a retry
    com DPI reduzido; erros lógicos de extração não tentam de novo."""
    msg = f"{type(exc).__name__}:{exc}".lower()
    return any(
        key in msg
        for key in (
            "memoryerror",
            "out_of_memory",
            "oom",
            "image_too_large",
            "image_pixels_limit",
            "resource",
            # PaddleOCR encapsula OOM de predição em RuntimeError —
            # retry (faixas/menor dpi) é limitado e fail-closed.
            "runtimeerror",
        )
    )
_DEDUP_ENTRY_LIMIT = 500

# Backend-defined pipelines — the consumer never picks classes/modules.
VISUAL_PIPELINE_CATALOG: dict[str, dict[str, Any]] = {
    "pdfium_render_paddleocr": {
        "render": "pdfium_render_experimental",
        "preprocess": None,
        "ocr": "paddleocr_experimental",
    },
    "pdfium_render_opencv_paddleocr": {
        "render": "pdfium_render_experimental",
        "preprocess": "opencv_preprocess_experimental",
        "preprocess_mode": "adaptive_threshold",
        "ocr": "paddleocr_experimental",
    },
    "pdfium_render_grayscale_paddleocr": {
        "render": "pdfium_render_experimental",
        "preprocess": "opencv_preprocess_experimental",
        "preprocess_mode": "grayscale",
        "ocr": "paddleocr_experimental",
    },
}


def _resolve_isolation() -> str:
    import os

    mode = os.getenv("ENG_DRAWING_OCR_ISOLATION", "").strip().lower()
    return mode if mode in {"subprocess", "inprocess"} else "subprocess"


def _peak_rss_kb() -> int | None:
    """Best-effort peak RSS (Linux ru_maxrss) — observability, not SLA."""
    try:
        import resource

        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except Exception:
        return None


def _normalized(text: str) -> str:
    return "".join(str(text).split()).lower()


def _token_sample_entry(
    token: Any,
    *,
    page: int,
    scale: float | None,
    width: int,
    height: int,
    provider_id: str,
    provider_version: str | None,
    extraction_method: str,
) -> dict[str, Any]:
    box = token.box
    entry: dict[str, Any] = {
        "page": page,
        "raw_text": token.text,
        "normalized_text": _normalized(token.text),
        "confidence": token.confidence,
        "bounding_box_px": box,
        "coordinate_system": "pixels_top_left",
        "provider_id": provider_id,
        "provider_version": provider_version,
        "extraction_method": extraction_method,
    }
    if box and len(box) >= 4 and width and height:
        xs = box[0::2]
        ys = box[1::2]
        entry["bounding_box_normalized"] = [
            round(min(xs) / width, 4), round(min(ys) / height, 4),
            round(max(xs) / width, 4), round(max(ys) / height, 4),
        ]
        if scale:
            entry["bounding_box_pdf_points"] = [
                round(v / scale, 2) for v in box
            ]
            entry["pdf_transform"] = f"pdf_pt = px / {scale:.4f}"
    else:
        entry["bounding_box_normalized"] = None
        entry["bounding_box_pdf_points"] = None
    return entry


def _page_batch_size() -> int:
    """Páginas por subprocesso filho — DEC-VAL-036 lifecycle fix.

    Cada filho morre ao fim do lote, devolvendo memória nativa do
    Paddle/arrays ao OS. Default 4: bounded pelo observado (falha
    nativa após ~4 páginas densas no mesmo address-space) e pelo
    cap RLIMIT_AS — não pelo PDF de referência.
    """
    try:
        return max(1, min(25, int(os.environ.get(
            "ENG_DRAWING_OCR_PAGE_BATCH", "4"
        ))))
    except Exception:
        return 4


def _pdf_page_count(pdf_bytes: bytes) -> int | None:
    try:
        import pypdfium2 as pdfium  # type: ignore

        doc = pdfium.PdfDocument(pdf_bytes)
        try:
            return len(doc)
        finally:
            doc.close()
    except Exception:
        return None


def _merge_isolated_records(a: dict, b: dict) -> dict:
    """Merge sequential page-batch run records for one pipeline.

    Pages carry absolute page numbers — concatenation preserves
    order/provenance; summary fields recomputed from merged pages.
    """
    pages = (a.get("pages") or []) + (b.get("pages") or [])
    lim = list(
        dict.fromkeys(
            (a.get("limitations") or []) + (b.get("limitations") or [])
        )
    )
    merged = dict(a)
    merged["pages"] = pages
    merged["pages_rendered"] = len(pages)
    merged["text_chars"] = (a.get("text_chars") or 0) + (
        b.get("text_chars") or 0
    )
    merged["token_count"] = (a.get("token_count") or 0) + (
        b.get("token_count") or 0
    )
    merged["duration_ms"] = (a.get("duration_ms") or 0) + (
        b.get("duration_ms") or 0
    )
    merged["memory_peak_kb"] = max(
        a.get("memory_peak_kb") or 0, b.get("memory_peak_kb") or 0
    )
    merged["limitations"] = lim
    merged["_text_blob"] = " ".join(
        x for x in (a.get("_text_blob"), b.get("_text_blob")) if x
    )
    merged["_tokens_sample"] = (
        (a.get("_tokens_sample") or []) + (b.get("_tokens_sample") or [])
    )[: token_sample_limit()]
    gpa = dict(a.get("_graphic_primitives_by_page") or {})
    gpa.update(b.get("_graphic_primitives_by_page") or {})
    merged["_graphic_primitives_by_page"] = gpa
    merged["_graphic_primitives"] = (
        a.get("_graphic_primitives") or b.get("_graphic_primitives")
    )
    merged["document_page_count"] = (
        b.get("document_page_count") or a.get("document_page_count")
    )
    merged["worker_pids"] = [
        w for w in (
            (a.get("worker_pids") or [a.get("worker_pid")])
            + [b.get("worker_pid")]
        ) if w
    ]
    merged["batch_ranges"] = (a.get("batch_ranges") or []) + [
        b.get("page_range")
    ]
    ok = sum(
        1 for p in pages if (p.get("ocr") or {}).get("status") == "ok"
    )
    total = merged["document_page_count"] or len(pages)
    if ok and ok == total:
        merged["status"] = "ok"
    elif ok:
        merged["status"] = "partial"
    else:
        # Sem páginas OCR-ok: preserva o status de erro dos chunks
        # (provider_error/extraction_error) em vez de reescrever.
        merged["status"] = (
            a.get("status")
            if a.get("status") in {"provider_error", "extraction_error"}
            else "error"
        )
    merged["coverage_status"] = (
        "FULL" if (total and ok == total)
        else ("PARTIAL" if ok else "NONE")
    )
    return merged


def run_visual_benchmark(
    pdf_bytes: bytes,
    *,
    pipelines: list[str],
    corpus_id: str = "local",
    environment: str = "test",
    dpi: int = 200,
    isolation: str | None = None,
    page_start: int | None = None,
    page_end: int | None = None,
) -> list[dict[str, Any]]:
    """Execute visual pipelines over the same bytes → run records.

    ``isolation`` (R7.1): ``subprocess`` (default — real OS limits,
    killable) or ``inprocess`` (dev/test only). Resolved per call from
    ``ENG_DRAWING_OCR_ISOLATION``; never consumer-controlled via MCP.
    """
    doc_hash = hashlib.sha256(pdf_bytes).hexdigest()
    mode = isolation or _resolve_isolation()
    if mode == "subprocess":
        from engineering_app.infrastructure.extraction.subprocess_executor import (  # noqa: E501
            run_pipeline_isolated,
        )

        out: list[dict[str, Any]] = []
        # DEC-VAL-036 — batches de páginas em filhos separados: cada
        # filho morre devolvendo memória nativa (Paddle/arrays) ao OS.
        # Sem isso, RuntimeError → reset → model_load MemoryError
        # cascateia no mesmo address-space e derruba o restante do doc.
        batch = _page_batch_size()
        start = page_start or 1
        for pid in pipelines:
            merged = None
            p_start = start
            while True:
                p_end = (
                    min(page_end, p_start + batch - 1)
                    if page_end
                    else p_start + batch - 1
                )
                chunk = run_pipeline_isolated(
                    pdf_bytes,
                    pipeline_id=pid,
                    dpi=dpi,
                    page_start=p_start,
                    page_end=p_end,
                )
                chunk["page_range"] = [p_start, p_end]
                merged = (
                    chunk
                    if merged is None
                    else _merge_isolated_records(merged, chunk)
                )
                total = chunk.get("document_page_count")
                if (page_end and p_end >= page_end) or (
                    total and p_end >= total
                ):
                    break
                if p_end >= 500:  # guard duro — MAX_PAGES do worker
                    break
                p_start = p_end + 1
            rec = merged
            rec.setdefault("run_id", uuid.uuid4().hex[:12])
            rec["corpus_id"] = corpus_id
            rec["environment"] = environment
            rec.setdefault("document_hash", doc_hash)
            rec["precision"] = "metric_not_available"
            rec["recall"] = "metric_not_available"
            out.append(rec)
        return out
    records: list[dict[str, Any]] = []
    for pipeline_id in pipelines:
        rec: dict[str, Any] = {
            "run_id": uuid.uuid4().hex[:12],
            "corpus_id": corpus_id,
            "environment": environment,
            "provider_id": pipeline_id,
            "pipeline_kind": "visual_ocr",
            "document_hash": doc_hash,
            "input_bytes": len(pdf_bytes),
            "precision": "metric_not_available",
            "recall": "metric_not_available",
        }
        t0 = time.monotonic()
        spec = VISUAL_PIPELINE_CATALOG.get(pipeline_id)
        if spec is None:
            rec["status"] = "provider_error"
            rec["error"] = f"unknown_pipeline:{pipeline_id}"
            records.append(rec)
            continue
        try:
            renderer = resolve_visual_provider(
                "render", spec["render"], allow_experimental=True
            )
            preprocessor = (
                resolve_visual_provider(
                    "preprocess",
                    spec["preprocess"],
                    allow_experimental=True,
                )
                if spec.get("preprocess")
                else None
            )
            ocr = resolve_visual_provider(
                "ocr", spec["ocr"], allow_experimental=True
            )
        except Exception as exc:
            rec["status"] = "provider_error"
            rec["error"] = f"{type(exc).__name__}:{exc}"
            records.append(rec)
            continue

        desc = ocr.capability_descriptor()
        rec["provider_version"] = desc.version
        rec["provider_status"] = desc.status
        rec["preprocess_profile"] = spec.get("preprocess_mode")
        rec["render_provider"] = spec["render"]
        rec["ocr_provider"] = spec["ocr"]

        pages: list[dict[str, Any]] = []
        text_parts: list[str] = []
        tokens_sample: list[dict[str, Any]] = []
        page_errors = 0
        page_cap_hit = False
        limitations: list[str] = []
        try:
            _last = max_render_pages()
            if page_end:
                _last = min(_last, page_end)
            rec["document_page_count"] = _pdf_page_count(pdf_bytes)
            for page_no in range(page_start or 1, _last + 1):
                try:
                    rendered = renderer.render_page(
                        pdf_bytes, page=page_no, dpi=dpi
                    )
                except PdfExtractionError as exc:
                    if str(exc).startswith("page_out_of_bounds"):
                        break
                    if str(exc).startswith("page_render_cap"):
                        page_cap_hit = True
                        break
                    raise
                stage: dict[str, Any] = {
                    "page": page_no,
                    "render": {
                        "width": rendered.width,
                        "height": rendered.height,
                        "dpi": rendered.dpi,
                        "scale": rendered.scale,
                        "rotation": rendered.rotation,
                        "page_width_pt": rendered.page_width_pt,
                        "page_height_pt": rendered.page_height_pt,
                        "coordinate_system": rendered.coordinate_system,
                        "provider_id": rendered.provider_id,
                    },
                }
                image = rendered.image_bytes
                try:
                    from engineering_app.infrastructure.extraction.opencv_adapter import (  # noqa: E501
                        detect_graphic_primitives,
                    )
                    stage["graphic_primitives"] = (
                        detect_graphic_primitives(image)
                    )
                except Exception:
                    stage["graphic_primitives"] = None
                result = None
                last_exc: Exception | None = None
                # Páginas densas podem estourar recursos do OCR —
                # retentativa em faixas horizontais no mesmo DPI
                # (menos memória por chamada, resolução preservada) e,
                # por fim, página inteira com DPI reduzido.
                try:
                    img = rendered.image_bytes
                    if preprocessor is not None:
                        pre = preprocessor.preprocess(
                            img, mode=spec["preprocess_mode"]
                        )
                        stage["preprocess"] = {
                            "profile": pre.profile,
                            "ops_applied": pre.ops_applied,
                            "provider_id": pre.provider_id,
                        }
                        img = pre.image_bytes
                    result = ocr.extract_text(img)
                except Exception as exc:
                    last_exc = exc
                if result is None and _is_resource_error(last_exc):
                    try:
                        result = _ocr_in_strips(
                            rendered.image_bytes, ocr,
                            bands=_STRIP_BANDS,
                        )
                        if result is not None and result.tokens:
                            stage["retry"] = {
                                "mode": "horizontal_strips",
                                "bands": _STRIP_BANDS,
                                "reason": str(last_exc),
                            }
                    except Exception as exc:
                        last_exc = exc
                        result = None
                if result is None and _is_resource_error(last_exc):
                    try:
                        rendered = renderer.render_page(
                            pdf_bytes, page=page_no, dpi=_RETRY_DPI,
                        )
                        stage["render"].update(
                            {
                                "width": rendered.width,
                                "height": rendered.height,
                                "dpi": rendered.dpi,
                                "scale": rendered.scale,
                            }
                        )
                        img = rendered.image_bytes
                        if preprocessor is not None:
                            img = preprocessor.preprocess(
                                img, mode=spec["preprocess_mode"]
                            ).image_bytes
                        result = ocr.extract_text(img)
                        stage["retry"] = {
                            "dpi": _RETRY_DPI,
                            "reason": str(last_exc),
                        }
                    except Exception as exc:
                        last_exc = exc
                        result = None
                if result is None:
                    page_errors += 1
                    stage["status"] = "error"
                    stage["error"] = str(last_exc)
                    pages.append(stage)
                    continue
                confidences = [
                    t.confidence
                    for t in result.tokens
                    if t.confidence is not None
                ]
                meta = result.metadata or {}
                stage["status"] = "ok"
                stage["ocr"] = {
                    "text_chars": len(result.text),
                    "token_count": len(result.tokens),
                    "boxes_returned": sum(
                        1 for t in result.tokens if t.box
                    ),
                    "confidence_mean": (
                        round(sum(confidences) / len(confidences), 4)
                        if confidences
                        else None
                    ),
                    "duration_ms": result.duration_ms,
                    "limitations": result.limitations,
                    "model": {
                        "engine": meta.get("engine"),
                        "paddleocr_version": meta.get(
                            "paddleocr_version"
                        ),
                        "paddle_version": meta.get("paddle_version"),
                        "model_source": meta.get("model_source"),
                        "device": meta.get("device"),
                        "lang": meta.get("lang"),
                        "coordinate_system": meta.get(
                            "coordinate_system"
                        ),
                        "timeout_seconds": meta.get("timeout_seconds"),
                    },
                }
                text_parts.append(result.text)
                for token in result.tokens:
                    if len(tokens_sample) >= token_sample_limit():
                        break
                    tokens_sample.append(
                        _token_sample_entry(
                            token,
                            page=page_no,
                            scale=rendered.scale,
                            width=rendered.width,
                            height=rendered.height,
                            provider_id=result.provider_id,
                            provider_version=meta.get(
                                "paddleocr_version"
                            ),
                            extraction_method=(
                                "paddleocr_local"
                                if not preprocessor
                                else f"opencv_{spec['preprocess_mode']}"
                                "+paddleocr_local"
                            ),
                        )
                    )
                pages.append(stage)
        except PdfExtractionError as exc:
            rec["status"] = "extraction_error"
            rec["error"] = str(exc)
            records.append(rec)
            continue
        except Exception as exc:
            rec["status"] = "provider_error"
            rec["error"] = f"{type(exc).__name__}:{exc}"
            records.append(rec)
            continue

        if not pages:
            rec["status"] = "extraction_error"
            rec["error"] = "no_pages_rendered"
            records.append(rec)
            continue
        ocr_ok_pages = sum(1 for p in pages if "ocr" in p)
        if page_errors:
            limitations.append(
                f"page_errors:{page_errors}_of_{len(pages)}_pages"
            )
        if page_errors == 0:
            status = "ok"
        elif ocr_ok_pages > 0:
            status = "partial"
            limitations.append(
                f"partial_coverage:{ocr_ok_pages}_ok_pages"
            )
        else:
            status = "error"
        _gp = next(
            (
                p.get("graphic_primitives")
                for p in pages
                if p.get("graphic_primitives")
            ),
            None,
        )
        if page_cap_hit:
            limitations.append(
                f"page_render_cap:{max_render_pages()}_pages_rendered"
            )
        if len(tokens_sample) >= token_sample_limit():
            limitations.append(
                "token_sample_truncated:"
                f"{token_sample_limit()}_of_{rec.get('token_count', 0)}"
            )
        rec.update(
            {
                "status": status,
                "coverage_status": (
                    "FULL"
                    if (
                        page_errors == 0
                        and (
                            rec.get("document_page_count") is None
                            or rec["document_page_count"] == len(pages)
                        )
                    )
                    else ("PARTIAL" if ocr_ok_pages else "NONE")
                ),
                "duration_ms": round((time.monotonic() - t0) * 1000),
                "pages_rendered": len(pages),
                "pages": pages,
                "text_chars": sum(
                    p.get("ocr", {}).get("text_chars", 0) for p in pages
                ),
                "token_count": sum(
                    p.get("ocr", {}).get("token_count", 0)
                    for p in pages
                ),
                "limitations": limitations,
                "memory_peak_kb": _peak_rss_kb(),
                "has_positional_data": bool(tokens_sample),
                "_text_blob": " ".join(text_parts),
                "_tokens_sample": tokens_sample,
                "_graphic_primitives": _gp,
                "_graphic_primitives_by_page": {
                    p["page"]: p["graphic_primitives"]
                    for p in pages
                    if p.get("graphic_primitives") and p.get("page")
                },
                "pdf_page_count": (
                    renderer.page_count(pdf_bytes)
                    if getattr(renderer, "page_count", None)
                    else None
                ),
                "page_size_px": (
                    [
                        pages[0]["render"]["width"],
                        pages[0]["render"]["height"],
                    ]
                    if pages and pages[0].get("render")
                    else None
                ),
            }
        )
        records.append(rec)
    return records


def dedupe_visual_evidence(
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Conservative dedup across providers/pipelines (R7-15).

    Key = (page, normalized_text) — exact normalized match only. No
    geometric merge and no fuzzy value merge: distinct values and
    divergent regions are preserved, provenance per provider kept.
    """
    groups: dict[tuple[int, str], dict[str, Any]] = {}
    truncated = False
    for run in runs:
        pid = run.get("provider_id", "?")
        for tok in run.get("_tokens_sample") or []:
            key = (
                int(tok.get("page") or 0),
                str(tok.get("normalized_text") or ""),
            )
            if not key[1]:
                continue
            group = groups.get(key)
            if group is None:
                if len(groups) >= _DEDUP_ENTRY_LIMIT:
                    truncated = True
                    continue
                group = {
                    "page": key[0],
                    "normalized_text": key[1],
                    "occurrences": [],
                }
                groups[key] = group
            group["occurrences"].append(
                {
                    "provider_id": pid,
                    "confidence": tok.get("confidence"),
                    "bounding_box_px": tok.get("bounding_box_px"),
                }
            )
    entries = [
        {
            "page": g["page"],
            "normalized_text": g["normalized_text"],
            "copies": len(g["occurrences"]),
            "providers": sorted(
                {o["provider_id"] for o in g["occurrences"]}
            ),
            "occurrences": g["occurrences"],
        }
        for g in groups.values()
    ]
    return {
        "method": "page+normalized_text_exact (sem merge geométrico/"
        "fuzzy — divergências preservadas)",
        "unique_texts": len(entries),
        "duplicated_texts": sum(1 for e in entries if e["copies"] > 1),
        "truncated": truncated,
        "entries": entries,
    }


def visual_records_to_jsonl(records: list[dict[str, Any]]) -> str:
    clean = [
        {k: v for k, v in r.items() if not k.startswith("_")}
        for r in records
    ]
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in clean)
