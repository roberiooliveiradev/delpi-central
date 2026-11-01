"""pdfplumber experimental adapter (R6A-07-B).

Optional dependency — when the package is absent the adapter reports
`unavailable` honestly via capability descriptor and raises
PdfExtractionError on use, never fabricating output. Positional words
are exposed in `PdfTextExtraction.metadata["positional_words"]` so
layout candidates remain comparable without breaking the contract.
"""

from __future__ import annotations

import hashlib
import io
import time
from typing import Any

from engineering_app.application.drawing.extraction_ports import (
    ProviderCapability,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    MAX_CHARS_PER_PAGE,
    MAX_PAGES,
    MAX_PDF_BYTES,
    PdfExtractionError,
    PdfPageText,
    PdfTextExtraction,
)

try:  # optional extra — not a prod requirement in R6-A
    import pdfplumber  # type: ignore

    _PDFPLUMBER_AVAILABLE = True
    _PDFPLUMBER_VERSION = getattr(pdfplumber, "__version__", "unknown")
except Exception:  # pragma: no cover - environment-dependent
    pdfplumber = None  # type: ignore
    _PDFPLUMBER_AVAILABLE = False
    _PDFPLUMBER_VERSION = "not_installed"


class PdfplumberExtractionAdapter:
    """Implements PdfExtractionPort using pdfplumber when present."""

    def extract(
        self, pdf_bytes: bytes, *, filename: str | None = None
    ) -> PdfTextExtraction:
        if not _PDFPLUMBER_AVAILABLE:
            raise PdfExtractionError(
                "provider_unavailable:pdfplumber_not_installed"
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
        positional: list[dict[str, Any]] = []
        t0 = time.monotonic()
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                result.page_count = len(pdf.pages)
                if result.page_count > MAX_PAGES:
                    result.limitations.append(
                        f"page_limit:{result.page_count}>{MAX_PAGES}"
                    )
                for index, page in enumerate(pdf.pages[:MAX_PAGES]):
                    raw = page.extract_text() or ""
                    truncated = len(raw) > MAX_CHARS_PER_PAGE
                    text = raw[:MAX_CHARS_PER_PAGE]
                    result.pages.append(
                        PdfPageText(page=index + 1, text=text,
                                    truncated=truncated)
                    )
                    result.text_chars += len(text)
                    if truncated:
                        result.limitations.append(
                            f"page_{index + 1}_truncated"
                        )
                    positional.append(
                        {
                            "page": index + 1,
                            "width": float(page.width or 0),
                            "height": float(page.height or 0),
                            "words": [
                                {
                                    "text": w.get("text"),
                                    "x0": w.get("x0"),
                                    "x1": w.get("x1"),
                                    "top": w.get("top"),
                                    "bottom": w.get("bottom"),
                                }
                                for w in page.extract_words()[:400]
                            ],
                        }
                    )
        except PdfExtractionError:
            raise
        except Exception as exc:
            raise PdfExtractionError(
                f"unreadable_pdf:{exc.__class__.__name__}"
            ) from exc
        result.pages_processed = len(result.pages)
        result.scanned_or_empty = result.text_chars < 40
        if result.scanned_or_empty:
            result.limitations.append(
                "no_text_layer:documento possivelmente escaneado"
            )
        result.metadata = {
            "provider": "pdfplumber",
            "coordinate_system": "pdfplumber_points_top_left",
            "positional_words": positional,
            "duration_ms": round((time.monotonic() - t0) * 1000),
        }
        return result

    def capability_descriptor(self) -> ProviderCapability:
        return ProviderCapability(
            provider_id="pdfplumber_experimental",
            version=_PDFPLUMBER_VERSION,
            status=(
                "experimental" if _PDFPLUMBER_AVAILABLE else "unavailable"
            ),
            capabilities={
                "text_layer": _PDFPLUMBER_AVAILABLE,
                "pages": _PDFPLUMBER_AVAILABLE,
                "document_hash": True,
                "coordinates": _PDFPLUMBER_AVAILABLE,
                "tables": _PDFPLUMBER_AVAILABLE,
                "ocr": False,
                "scanned_pdf": False,
            },
            formats=["pdf"],
            runs_local=True,
            requires_credentials=False,
            license="MIT",
            limits={
                "max_bytes": MAX_PDF_BYTES,
                "max_pages": MAX_PAGES,
                "max_chars_per_page": MAX_CHARS_PER_PAGE,
            },
            license_notes="MIT — permissiva; experimental, não default.",
        )
