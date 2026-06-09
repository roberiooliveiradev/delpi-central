#!/usr/bin/env python3
"""Testa extração de desenhos PDF na pasta desenhos/ (gitignored).

Preferir ``scripts/run_onda14_desenhos_validation.sh`` (Onda 14 — baseline + casos H*).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_pdf_extraction_service import ChatDrawingPdfExtractionService
from app.infrastructure.config.settings import Settings

configure_domain_infrastructure_ports()

Settings.CHAT_DOCUMENT_VISION_ENABLED = True
Settings.CHAT_DOCUMENT_VISION_BACKEND = "auto"
Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING = True


def main() -> int:
    desenhos = Path(__file__).resolve().parent.parent / "desenhos"
    pdfs = sorted(desenhos.glob("*.pdf"))

    if not pdfs:
        print(f"Nenhum PDF em {desenhos}", file=sys.stderr)
        return 1

    print(f"Testando {len(pdfs)} PDFs em {desenhos}\n")
    header = (
        f"{'arquivo':<16} {'esperado':<10} {'native':<10} {'vision':<10} "
        f"{'rev':<6} {'leg':<5} {'engine':<12} {'chars':<6} {'dims':<8} {'bom':<4} {'title':<5}"
    )
    print(header)
    print("-" * len(header))

    summary = {
        "ok_code": 0,
        "fail_code": 0,
        "legible": 0,
        "not_legible": 0,
        "ocr_used": 0,
        "native_only": 0,
    }
    failures: list[dict] = []

    for pdf in pdfs:
        expected = re.sub(r"\.pdf$", "", pdf.name, flags=re.I)
        path = str(pdf)

        native_parse = ChatDrawingPdfExtractionService.extract_from_storage_path(
            path,
            filename=pdf.name,
        )
        vision = ChatDocumentVisionService.extract_from_storage_path(
            path,
            filename=pdf.name,
            content_type="application/pdf",
        )

        native_code = native_parse.get("productCode") or "-"
        vision_code = vision.get("productCode") or "-"
        revision = vision.get("revision") or "-"
        legible = bool(vision.get("legible"))
        engine = vision.get("engine") or "-"
        stages = vision.get("stages") or []
        chars = int(vision.get("charCount") or 0)
        dims = vision.get("dimensions") or {}
        dim_found = sum(1 for value in dims.values() if value is not None)
        bom = len(vision.get("bomRows") or [])
        title = "sim" if vision.get("titleBlock") else "nao"
        warnings = vision.get("warnings") or []

        code_ok = vision_code == expected
        summary["ok_code" if code_ok else "fail_code"] += 1
        summary["legible" if legible else "not_legible"] += 1

        if "tesseract" in stages or engine == "tesseract":
            summary["ocr_used"] += 1
        elif engine in {"pypdf", "native"}:
            summary["native_only"] += 1

        flag = "OK" if code_ok else "FAIL"
        print(
            f"{pdf.name:<16} {expected:<10} {str(native_code):<10} {str(vision_code):<10} "
            f"{str(revision):<6} {'sim' if legible else 'nao':<5} {engine:<12} {chars:<6} "
            f"{dim_found:<8} {bom:<4} {title:<5} [{flag}]"
        )

        if not code_ok or warnings or not legible:
            detail = {
                "file": pdf.name,
                "expected": expected,
                "native_code": native_code,
                "vision_code": vision_code,
                "revision": revision,
                "legible": legible,
                "engine": engine,
                "stages": stages,
                "warnings": warnings,
                "charCount": chars,
                "dimensions": dims,
                "bomRows": bom,
                "titleBlock": vision.get("titleBlock"),
                "componentCodes": (vision.get("componentCodes") or [])[:12],
                "textPreview": (vision.get("fullText") or "")[:300],
            }
            failures.append(detail)

    print("\n--- Resumo ---")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if failures:
        print("\n--- Detalhes (falhas / avisos / ilegível) ---")
        for item in failures:
            print(json.dumps(item, indent=2, ensure_ascii=False))

    return 0 if summary["fail_code"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
