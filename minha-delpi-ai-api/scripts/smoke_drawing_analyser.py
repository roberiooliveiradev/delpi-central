#!/usr/bin/env python3
"""Smoke — skill Análise de Desenhos DELPI (intent + relatório MVP, sem HTTP).

Uso:
  PYTHONPATH=. python scripts/smoke_drawing_analyser.py
"""

from __future__ import annotations

import sys

from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def main() -> int:
    failed = 0

    def check(name: str, ok: bool) -> None:
        nonlocal failed

        if ok:
            print(f"OK {name}")
        else:
            print(f"FAIL {name}", file=sys.stderr)
            failed += 1

    check(
        "intent desenho",
        ChatDrawingIntentService.is_drawing_analysis_request(
            "gerar relatorio tecnico do desenho 90260140"
        ),
    )
    check(
        "roteamento analyser",
        ChatProductQueryIntentService.detect("analise o desenho 90260140")
        == ChatProductQueryIntent.ANALYSER,
    )

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90260140",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=True,
        api_ok=True,
    )
    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)

    check("relatório markdown", "Relatório de Análise de Desenho DELPI" in report)
    check("metadata drawingAnalysis", bool(package.get("drawingAnalysis")))

    pdf_parsed = ChatDrawingPdfExtractionService.parse_from_text(
        "DESENHO 90260140 REV.01"
    )
    check("extração PDF código", pdf_parsed.get("productCode") == "90260140")

    if failed:
        print(f"\n{failed} verificação(ões) falharam", file=sys.stderr)
        return 1

    print("Smoke drawing analyser: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
