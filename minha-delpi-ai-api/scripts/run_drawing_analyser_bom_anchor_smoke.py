#!/usr/bin/env python3
"""Smoke Onda B — extração + âncora BOM via /analyser após código resolvido.

Uso (container com stack no ar):
  docker exec delpi-minha-delpi-ai-api python /app/scripts/run_drawing_analyser_bom_anchor_smoke.py

Variáveis:
  DRAWING_SMOKE_PDF — caminho do PDF (default: desenhos/90262957.pdf)
  DRAWING_SMOKE_PRODUCT_CODE — código esperado (default: 90262957)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]

if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.application.services.chat_drawing_analyser_bom_confirmation_orchestration_service import (
    ChatDrawingAnalyserBomConfirmationOrchestrationService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
)
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)

configure_domain_infrastructure_ports()

PDF = Path(
    os.getenv(
        "DRAWING_SMOKE_PDF",
        str(_API_ROOT / "desenhos" / "90262957.pdf"),
    )
)
PRODUCT_CODE = os.getenv("DRAWING_SMOKE_PRODUCT_CODE", "90262957").strip()


def main() -> int:
    if not PDF.is_file():
        print(f"PDF ausente: {PDF}", file=sys.stderr)
        return 1

    start = time.time()
    parsed = ChatDrawingPdfExtractionService.extract_from_storage_path(
        str(PDF),
        filename=PDF.name,
    )
    extract_elapsed = time.time() - start

    before = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
        pdf_extract=parsed,
    )

    anchor_start = time.time()
    anchored = ChatDrawingAnalyserBomConfirmationOrchestrationService.try_anchor_after_code_resolution(
        pdf_extract=parsed,
        product_code=PRODUCT_CODE,
        access_token=None,
        storage_path=str(PDF),
        filename=PDF.name,
    )
    anchor_elapsed = time.time() - anchor_start

    after = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
        pdf_extract=anchored,
    )
    retry = anchored.get("extractionQualityRetry") or {}

    payload = {
        "pdf": str(PDF),
        "productCode": PRODUCT_CODE,
        "extractElapsedSec": round(extract_elapsed, 1),
        "anchorElapsedSec": round(anchor_elapsed, 1),
        "confidenceBefore": before.to_metadata(),
        "confidenceAfter": after.to_metadata(),
        "componentCodesBefore": parsed.get("componentCodes"),
        "componentCodesAfter": anchored.get("componentCodes"),
        "bomAnchorConfirmation": anchored.get("bomAnchorConfirmation"),
        "analyserBomAnchor": retry.get("analyserBomAnchor"),
        "confirmationAttempts": retry.get("confirmationAttempts"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    anchor_applied = bool(retry.get("analyserBomAnchor", {}).get("applied"))
    improved = after.score_percent >= before.score_percent

    if anchor_applied or improved:
        return 0

    if before.meets_threshold:
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
