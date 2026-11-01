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

_MAX_RENDER_PAGES = 5
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
        """Render one page to PNG (bounded: ≤5 pages, ≤300 DPI)."""
        if not _PDFIUM_AVAILABLE:
            raise PdfExtractionError(
                "provider_unavailable:pypdfium2_not_installed"
            )
        if dpi > _MAX_DPI:
            raise PdfExtractionError(f"dpi_limit:{dpi}>{_MAX_DPI}")
        pdf = pdfium.PdfDocument(pdf_bytes)
        if page < 1 or page > len(pdf) or page > _MAX_RENDER_PAGES:
            pdf.close()
            raise PdfExtractionError(f"page_out_of_bounds:{page}")
        bitmap = pdf[page - 1].render(scale=dpi / 72)
        pil = bitmap.to_pil()
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        pdf.close()
        return RenderedPage(
            page=page, image_bytes=buf.getvalue(),
            width=pil.width, height=pil.height, dpi=dpi,
            provider_id="pdfium_experimental",
        )

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
                "max_render_pages": _MAX_RENDER_PAGES,
                "max_dpi": _MAX_DPI,
            },
            license_notes="BSD-3 permissiva; binário PDFium bundled.",
        )
