"""Typed evidence extraction from a drawing's text layer (E1.1).

Deterministic parsing only — every item carries page, method and
honest limitations. Region granularity beyond the page is not claimed
(text layer lacks reliable coordinates).
"""

from __future__ import annotations

import re
from typing import Any

from engineering_app.application.drawing.pdf_text_extractor import (
    PdfTextExtraction,
)
from engineering_app.domain.drawing import DrawingEvidence, EvidenceClass

_PRODUCT_CODE = re.compile(r"\b(\d{8})\b")
_REVISION = re.compile(
    r"\b(?:REVIS[ÃA]O|REV\.?)\s*[:.]?\s*([A-Z0-9]{1,6})\b", re.IGNORECASE
)
_DRAWING_CODE = re.compile(
    r"\b(?:DESENHO|DRAWING|C[ÓO]D(?:IGO)?\.?\s*DESENHO)\b[^0-9A-Z]{0,8}"
    r"([0-9A-Z\-]{3,})",
    re.IGNORECASE,
)
_QUANTITY_UNIT = re.compile(
    r"(\d{6,8})\s+(.{5,60}?)\s+(\d+[\d.,]*)\s+(PC|UN|KG|M|MM|PCT|PR|CX|RL|JGS)\b",
    re.IGNORECASE,
)
_BOM_ROW_HINT = re.compile(
    r"\b(\d{6,8})\b\s+([A-Z0-9][\w\s.,/\-°ºª×*]{4,70})", re.IGNORECASE
)
_UNIT_TOKEN = re.compile(
    r"\b(PC|UN|KG|G|M|MM|L|ML|PCT|JGS|PAR)\b", re.IGNORECASE
)
_NOTE_HINT = re.compile(
    r"\bNOTA[S]?\s*[:.]|\bOBS(?:ERVA[ÇC][ÃA]O|\.)\s*[:.]", re.IGNORECASE
)
_MATERIAL_HINT = re.compile(
    r"\b(MATERIAL|MAT[ÉE]RIA|PVC|EPR|SILICONE|TEFLON|COPPER|COBRE|"
    r"A[ÇC]O|LAT[ÃA]O|NYLON)\b",
    re.IGNORECASE,
)


def _evidence(
    *,
    ref: str,
    evidence_type: str,
    value: str | None,
    page: int,
    normalized: str | None = None,
    unit: str | None = None,
    confidence: str = "medium",
    classification: EvidenceClass = EvidenceClass.OBSERVED,
    revision: str | None = None,
    limitations: list[str] | None = None,
) -> DrawingEvidence:
    return DrawingEvidence(
        document_ref=ref,
        source="drawing_pdf_text_layer",
        source_revision=revision,
        page=page,
        region=None,
        evidence_type=evidence_type,
        observed_value=value,
        normalized_value=normalized or value,
        unit=unit,
        confidence=confidence,
        extraction_method="deterministic_regex_pdf_text",
        classification=classification,
        limitations=limitations or [
            "regiao_coordenada_unavailable:evidencia_localizada_por_pagina"
        ],
    )


def extract_evidence(
    extraction: PdfTextExtraction,
    *,
    document_ref: str,
    source_revision: str | None = None,
) -> list[DrawingEvidence]:
    """Parse the text layer into typed technical evidence."""
    items: list[DrawingEvidence] = []
    item_rows: list[dict[str, Any]] = []
    codes_seen: dict[str, int] = {}

    for page in extraction.pages:
        text = page.text
        # Product/drawing codes (8-digit TOTVS product codes)
        for match in _PRODUCT_CODE.finditer(text):
            code = match.group(1)
            codes_seen.setdefault(code, page.page)
        for match in _DRAWING_CODE.finditer(text):
            items.append(
                _evidence(
                    ref=document_ref,
                    evidence_type="drawing_code",
                    value=match.group(1).strip(),
                    page=page.page,
                    confidence="high",
                )
            )
        for match in _REVISION.finditer(text):
            items.append(
                _evidence(
                    ref=document_ref,
                    evidence_type="revision",
                    value=match.group(1).strip(),
                    page=page.page,
                    confidence="high",
                )
            )
        for match in _QUANTITY_UNIT.finditer(text):
            items.append(
                _evidence(
                    ref=document_ref,
                    evidence_type="quantity",
                    value=f"{match.group(1)} {match.group(3)} {match.group(4)}",
                    page=page.page,
                    normalized=match.group(3).replace(",", "."),
                    unit=match.group(4).upper(),
                    confidence="medium",
                )
            )
        for match in _BOM_ROW_HINT.finditer(text):
            code, desc = match.group(1), match.group(2).strip()
            item_rows.append(
                {"code": code, "description": desc[:80], "page": page.page}
            )
        for match in _UNIT_TOKEN.finditer(text):
            items.append(
                _evidence(
                    ref=document_ref,
                    evidence_type="unit",
                    value=match.group(1).upper(),
                    page=page.page,
                    confidence="high",
                )
            )
        if _NOTE_HINT.search(text):
            items.append(
                _evidence(
                    ref=document_ref,
                    evidence_type="technical_notes_present",
                    value="true",
                    page=page.page,
                    confidence="high",
                )
            )
        if _MATERIAL_HINT.search(text):
            found = _MATERIAL_HINT.findall(text)
            items.append(
                _evidence(
                    ref=document_ref,
                    evidence_type="material_hints",
                    value=", ".join(sorted({m.upper() for m in found})[:8]),
                    page=page.page,
                    confidence="medium",
                )
            )

    for code, page in sorted(codes_seen.items()):
        items.append(
            _evidence(
                ref=document_ref,
                evidence_type="product_code_candidate",
                value=code,
                page=page,
                confidence="medium",
            )
        )
    for row in item_rows[:80]:
        items.append(
            _evidence(
                ref=document_ref,
                evidence_type="item_row_candidate",
                value=f"{row['code']} — {row['description']}",
                page=row["page"],
                normalized=row["code"],
                confidence="low",
                classification=EvidenceClass.INFERRED,
            )
        )
    return items
