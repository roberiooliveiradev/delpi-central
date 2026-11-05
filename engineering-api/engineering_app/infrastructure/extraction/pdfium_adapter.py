"""pypdfium2 experimental adapter (R6B-06).

Optional dependency — absent → `provider_unavailable`, never fabricated.
Adds page rendering (PDFium) for OCR/visual pipelines. BSD-3 license.
"""

from __future__ import annotations

import hashlib
import io
import time
from typing import Any

from engineering_app.application.drawing.extraction_ports import (
    ProviderCapability,
    RenderedPage,
    RenderedRegion,
    max_render_pages,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    MAX_CHARS_PER_PAGE,
    MAX_PAGES,
    MAX_PDF_BYTES,
    PdfExtractionError,
    PdfPageText,
    PdfTextExtraction,
)

try:
    import pypdfium2 as pdfium  # type: ignore

    _PDFIUM_AVAILABLE = True
    _PDFIUM_VERSION = getattr(pdfium, "V_PDFIUM", None) or getattr(
        pdfium, "__version__", "unknown"
    )
except Exception:  # pragma: no cover
    pdfium = None  # type: ignore
    _PDFIUM_AVAILABLE = False
    _PDFIUM_VERSION = "not_installed"

_MAX_DPI = 300


class PdfiumExtractionAdapter:
    """PdfExtractionPort + PdfRenderingPort via pypdfium2."""

    def extract(
        self, pdf_bytes: bytes, *, filename: str | None = None
    ) -> PdfTextExtraction:
        if not _PDFIUM_AVAILABLE:
            raise PdfExtractionError(
                "provider_unavailable:pypdfium2_not_installed"
            )
        if not pdf_bytes:
            raise PdfExtractionError("empty_document")
        if len(pdf_bytes) > MAX_PDF_BYTES:
            raise PdfExtractionError(
                f"document_too_large:{len(pdf_bytes)}>{MAX_PDF_BYTES}"
            )
        if not pdf_bytes[:5] == b"%PDF-":
            raise PdfExtractionError("invalid_mime:missing_pdf_signature")

        result = PdfTextExtraction(
            document_hash=hashlib.sha256(pdf_bytes).hexdigest()
        )
        try:
            pdf = pdfium.PdfDocument(pdf_bytes)
            result.page_count = len(pdf)
            if result.page_count > MAX_PAGES:
                result.limitations.append(
                    f"page_limit:{result.page_count}>{MAX_PAGES}"
                )
            for index in range(min(result.page_count, MAX_PAGES)):
                textpage = pdf[index].get_textpage()
                raw = textpage.get_text_range() or ""
                truncated = len(raw) > MAX_CHARS_PER_PAGE
                text = raw[:MAX_CHARS_PER_PAGE]
                result.pages.append(
                    PdfPageText(page=index + 1, text=text,
                                truncated=truncated)
                )
                result.text_chars += len(text)
            pdf.close()
        except PdfExtractionError:
            raise
        except Exception as exc:
            raise PdfExtractionError(
                f"unreadable_pdf:{exc.__class__.__name__}"
            ) from exc
        result.pages_processed = len(result.pages)
        result.scanned_or_empty = result.text_chars < 40
        if result.scanned_or_empty:
            result.limitations.append("no_text_layer")
        result.metadata = {"provider": "pdfium"}
        return result

    def render_page(
        self, pdf_bytes: bytes, *, page: int, dpi: int = 150
    ) -> RenderedPage:
        """Render one page to PNG (bounded: ≤5 pages, ≤300 DPI).

        R7-04: preserves the PDF→pixel transform — scale = dpi/72,
        page rotation and point dimensions are recorded so pixel
        boxes can be mapped back to PDF space explicitly.
        """
        if not _PDFIUM_AVAILABLE:
            raise PdfExtractionError(
                "provider_unavailable:pypdfium2_not_installed"
            )
        if not pdf_bytes:
            raise PdfExtractionError("empty_document")
        if len(pdf_bytes) > MAX_PDF_BYTES:
            raise PdfExtractionError(
                f"document_too_large:{len(pdf_bytes)}>{MAX_PDF_BYTES}"
            )
        if not pdf_bytes[:5] == b"%PDF-":
            raise PdfExtractionError("invalid_mime:missing_pdf_signature")
        if dpi < 1 or dpi > _MAX_DPI:
            raise PdfExtractionError(f"dpi_limit:{dpi}>{_MAX_DPI}")
        pdf = pdfium.PdfDocument(pdf_bytes)
        try:
            cap = max_render_pages()
            if page < 1 or page > len(pdf):
                raise PdfExtractionError(f"page_out_of_bounds:{page}")
            if page > cap:
                raise PdfExtractionError(f"page_render_cap:{page}>{cap}")
            pdf_page = pdf[page - 1]
            try:
                rotation = int(pdf_page.get_rotation() or 0)
            except Exception:
                rotation = 0
            try:
                page_width_pt, page_height_pt = (
                    float(v) for v in pdf_page.get_size()
                )
            except Exception:
                page_width_pt = page_height_pt = None
            scale = dpi / 72
            # PDFium aplica a rotação da página no bitmap renderizado —
            # o pixel space retornado já é "visual" (top-left origin).
            bitmap = pdf_page.render(scale=scale)
            pil = bitmap.to_pil()
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            return RenderedPage(
                page=page, image_bytes=buf.getvalue(),
                width=pil.width, height=pil.height, dpi=dpi,
                provider_id="pdfium_experimental",
                scale=scale, rotation=rotation,
                page_width_pt=page_width_pt,
                page_height_pt=page_height_pt,
            )
        finally:
            pdf.close()

    def render_region(
        self,
        pdf_bytes: bytes,
        *,
        page: int,
        region_px: list[float],
        reference_dpi: int,
        dpi: int = 300,
        margin_px: int = 8,
    ) -> RenderedRegion:
        """Recorte direcionado via crop nativo do PDFium (R13) —
        re-renderiza a fonte vetorial, nunca amplia raster degradado."""
        if not _PDFIUM_AVAILABLE:
            raise PdfExtractionError(
                "provider_unavailable:pypdfium2_not_installed"
            )
        if not pdf_bytes:
            raise PdfExtractionError("empty_document")
        if dpi < 1 or dpi > _MAX_DPI:
            raise PdfExtractionError(f"dpi_limit:{dpi}>{_MAX_DPI}")
        if not region_px or len(region_px) < 4:
            raise PdfExtractionError("invalid_region")
        x1, y1 = float(region_px[0]), float(region_px[1])
        if len(region_px) >= 8:
            x2, y2 = float(region_px[4]), float(region_px[5])
        else:
            x2, y2 = float(region_px[2]), float(region_px[3])
        pdf = pdfium.PdfDocument(pdf_bytes)
        try:
            cap = max_render_pages()
            if page < 1 or page > len(pdf):
                raise PdfExtractionError(f"page_out_of_bounds:{page}")
            if page > cap:
                raise PdfExtractionError(f"page_render_cap:{page}>{cap}")
            pdf_page = pdf[page - 1]
            try:
                rotation = int(pdf_page.get_rotation() or 0)
            except Exception:
                rotation = 0
            try:
                page_w_pt, page_h_pt = (
                    float(v) for v in pdf_page.get_size()
                )
            except Exception as exc:
                raise PdfExtractionError(
                    f"page_size_unavailable:{type(exc).__name__}"
                ) from exc
            ref_scale = max(float(reference_dpi or dpi), 1.0) / 72.0
            margin_pt = float(margin_px) / ref_scale
            left = max(0.0, x1 / ref_scale - margin_pt)
            top = max(0.0, y1 / ref_scale - margin_pt)
            right = min(
                page_w_pt, max(left + 1.0, x2 / ref_scale + margin_pt)
            )
            bottom = min(
                page_h_pt, max(top + 1.0, y2 / ref_scale + margin_pt)
            )
            if left >= page_w_pt or top >= page_h_pt:
                raise PdfExtractionError("region_out_of_page")
            scale = dpi / 72
            # pdfium crop = quantidade cortada de CADA borda da página
            # (left, bottom, right, top) em pt — não o retângulo a
            # manter. Região top-left → cortes convertidos pelas bordas
            # opostas; região é clampada à página antes do render.
            bitmap = pdf_page.render(
                scale=scale,
                crop=(
                    left,
                    page_h_pt - bottom,
                    page_w_pt - right,
                    top,
                ),
            )
            pil = bitmap.to_pil()
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            return RenderedRegion(
                page=page,
                image_bytes=buf.getvalue(),
                width=pil.width,
                height=pil.height,
                dpi=dpi,
                provider_id="pdfium_experimental",
                region_px=[x1, y1, x2, y2],
                offset_px=(left * scale, top * scale),
                scale=scale,
                rotation=rotation,
            )
        finally:
            pdf.close()

    def page_count(self, pdf_bytes: bytes) -> int:
        """Número de páginas do PDF (sem render) — planejamento de
        cobertura multipágina (RQ-VAL-029)."""
        if not _PDFIUM_AVAILABLE:
            raise PdfExtractionError(
                "provider_unavailable:pypdfium2_not_installed"
            )
        if not pdf_bytes:
            raise PdfExtractionError("empty_document")
        pdf = pdfium.PdfDocument(pdf_bytes)
        try:
            return len(pdf)
        finally:
            pdf.close()

    def capability_descriptor(self) -> ProviderCapability:
        return ProviderCapability(
            provider_id="pdfium_experimental",
            version=str(_PDFIUM_VERSION),
            status=(
                "experimental" if _PDFIUM_AVAILABLE else "unavailable"
            ),
            capabilities={
                "text_layer": _PDFIUM_AVAILABLE,
                "pages": _PDFIUM_AVAILABLE,
                "document_hash": True,
                "coordinates": _PDFIUM_AVAILABLE,
                "render": _PDFIUM_AVAILABLE,
                "tables": False,
                "ocr": False,
                "scanned_pdf": False,
            },
            formats=["pdf"],
            runs_local=True,
            license="BSD-3-Clause",
            limits={
                "max_bytes": MAX_PDF_BYTES,
                "max_pages": MAX_PAGES,
                "max_render_pages": max_render_pages(),
                "max_dpi": _MAX_DPI,
            },
            license_notes="BSD-3 permissiva; binário PDFium bundled.",
        )
