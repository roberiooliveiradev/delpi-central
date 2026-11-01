"""pypdf baseline adapter (R6A-06) — preserves the production pipeline.

Delegates to the existing deterministic extractor; no behavioral
change to `product.drawing_analysis`.
"""

from __future__ import annotations

import pypdf  # noqa: F401  (adapter boundary — the only layer with SDK)

from engineering_app.application.drawing.extraction_ports import (
    ProviderCapability,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    PdfTextExtraction,
    extract_pdf_text,
)


class PypdfExtractionAdapter:
    """Implements PdfExtractionPort on top of the baseline extractor."""

    def extract(
        self, pdf_bytes: bytes, *, filename: str | None = None
    ) -> PdfTextExtraction:
        return extract_pdf_text(pdf_bytes)

    def capability_descriptor(self) -> ProviderCapability:
        return ProviderCapability(
            provider_id="pypdf_baseline",
            version=getattr(pypdf, "__version__", "unknown"),
            status="baseline",
            capabilities={
                "text_layer": True,
                "pages": True,
                "document_hash": True,
                "coordinates": False,
                "tables": False,
                "ocr": False,
                "scanned_pdf": False,
            },
            formats=["pdf"],
            runs_local=True,
            requires_credentials=False,
            license="BSD-3-Clause",
            limits={
                "max_bytes": 15 * 1024 * 1024,
                "max_pages": 30,
                "max_chars": 60000,
            },
            license_notes="Permissive BSD; safe for server use.",
        )
