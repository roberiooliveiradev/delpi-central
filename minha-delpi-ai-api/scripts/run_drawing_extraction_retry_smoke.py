#!/usr/bin/env python3
"""Smoke — extração com retry até confiança ≥95% (90264227-1.pdf).

Uso (container já em rede delpi):
  docker exec delpi-minha-delpi-ai-api python /app/scripts/run_drawing_extraction_retry_smoke.py

Uso isolado (sem entrypoint / banco):
  docker run --rm --entrypoint python \\
    -v \"$(pwd):/app\" -w /app \\
    infra-minha-delpi-ai-api:latest \\
    scripts/run_drawing_extraction_retry_smoke.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_API_ROOT = Path(__file__).resolve().parents[1]

if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
)
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)

configure_domain_infrastructure_ports()

PDF = Path(__file__).resolve().parents[1] / "desenhos" / "90264227-1.pdf"


def main() -> int:
    if not PDF.is_file():
        print(f"PDF ausente: {PDF}", file=sys.stderr)
        return 1

    start = time.time()
    parsed = ChatDrawingPdfExtractionService.extract_from_storage_path(
        str(PDF),
        filename=PDF.name,
    )
    elapsed = time.time() - start
    retry = parsed.get("extractionQualityRetry") or {}
    conf = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(pdf_extract=parsed)

    payload = {
        "elapsedSec": round(elapsed, 1),
        "productCode": parsed.get("productCode"),
        "revision": parsed.get("revision"),
        "componentCodes": parsed.get("componentCodes"),
        "intermediateCodes": parsed.get("intermediateCodes"),
        "charCount": parsed.get("charCount"),
        "dimensions": parsed.get("dimensions"),
        "extractionQualityRetry": retry,
        "confidence": conf.to_metadata(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if conf.meets_threshold else 2


if __name__ == "__main__":
    raise SystemExit(main())
