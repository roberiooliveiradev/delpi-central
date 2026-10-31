"""Neutral PDF text-layer extraction adapter (E1).

Deterministic extraction of the embedded text layer of a technical
drawing PDF. Boundary-first: OCR/VLM perception remains behind
explicit adapters and is NOT performed here — scanned drawings yield
an honest INCONCLUSIVE state instead of fabricated text.

Security contract: byte cap, page cap, real signature check, no
embedded-action execution, extracted text is untrusted data.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass, field

MAX_PDF_BYTES = 15 * 1024 * 1024  # 15 MB
MAX_PAGES = 30
MAX_CHARS_PER_PAGE = 60_000


class PdfExtractionError(ValueError):
    """Input violates the extraction contract (not a parser failure)."""


@dataclass
class PdfPageText:
    page: int
    text: str
    truncated: bool = False


@dataclass
class PdfTextExtraction:
    document_hash: str
    pages: list[PdfPageText] = field(default_factory=list)
    page_count: int = 0
    pages_processed: int = 0
    text_chars: int = 0
    scanned_or_empty: bool = False
    limitations: list[str] = field(default_factory=list)


def extract_pdf_text(pdf_bytes: bytes) -> PdfTextExtraction:
    """Extract the text layer of a drawing PDF, page by page."""
    if not pdf_bytes:
        raise PdfExtractionError("empty_document")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise PdfExtractionError(
            f"document_too_large:{len(pdf_bytes)}>{MAX_PDF_BYTES}"
        )
    if not pdf_bytes[:5] == b"%PDF-":
        raise PdfExtractionError("invalid_mime:missing_pdf_signature")

    document_hash = hashlib.sha256(pdf_bytes).hexdigest()
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise PdfExtractionError("extractor_unavailable:pypdf") from exc

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes), strict=False)
    except Exception as exc:
        raise PdfExtractionError(
            f"unreadable_pdf:{exc.__class__.__name__}"
        ) from exc

    if getattr(reader, "is_encrypted", False):
        try:
            reader.decrypt("")
        except Exception:
            raise PdfExtractionError("encrypted_pdf")

    result = PdfTextExtraction(document_hash=document_hash)
    try:
        page_count = len(reader.pages)
    except Exception:
        page_count = 0
    result.page_count = page_count
    if page_count > MAX_PAGES:
        result.limitations.append(
            f"page_limit:{page_count}>{MAX_PAGES} — primeiras "
            f"{MAX_PAGES} páginas analisadas"
        )
    for index in range(min(page_count, MAX_PAGES)):
        try:
            raw = reader.pages[index].extract_text() or ""
        except Exception as exc:
            raw = ""
            result.limitations.append(
                f"page_{index + 1}_extract_error:{exc.__class__.__name__}"
            )
        truncated = len(raw) > MAX_CHARS_PER_PAGE
        text = raw[:MAX_CHARS_PER_PAGE]
        result.pages.append(
            PdfPageText(page=index + 1, text=text, truncated=truncated)
        )
        result.text_chars += len(text)
        if truncated:
            result.limitations.append(
                f"page_{index + 1}_truncated_at_{MAX_CHARS_PER_PAGE}_chars"
            )
    result.pages_processed = len(result.pages)
    result.scanned_or_empty = result.text_chars < 40
    if result.scanned_or_empty:
        result.limitations.append(
            "no_text_layer:documento possivelmente escaneado — OCR/VLM "
            "fora do escopo do adapter atual"
        )
    return result
