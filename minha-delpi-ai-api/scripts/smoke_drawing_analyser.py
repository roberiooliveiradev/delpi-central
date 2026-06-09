#!/usr/bin/env python3
"""Smoke — skill Análise de Desenhos DELPI (intent + relatório MVP, sem HTTP).

Uso:
  PYTHONPATH=. python scripts/smoke_drawing_analyser.py

Inclui regressão D1–D12 via pytest (`test_drawing_analysis_skill.py`).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.application.services.chat_drawing_follow_up_service import (
    ChatDrawingFollowUpService,
)
from app.application.services.chat_drawing_report_export_service import (
    ChatDrawingReportExportService,
)
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
        "intent desenho (relatorio tecnico)",
        ChatDrawingIntentService.is_drawing_analysis_request(
            "gerar relatorio tecnico do desenho 90260140"
        ),
    )
    check(
        "intent desenho (conformidade delpi)",
        ChatDrawingIntentService.is_drawing_analysis_request(
            "gerar relatorio de conformidade delpi 90260140"
        ),
    )
    check(
        "intent desenho (pdf anexado)",
        ChatDrawingIntentService.is_drawing_analysis_request(
            "validar carimbo do arquivo anexado do desenho",
            attachment_ids=["att-smoke"],
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

    package_full = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90260140",
        payload=_analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract={
            "productCode": "90260140",
            "legible": True,
            "componentCodes": ["50212194"],
            "intermediateCodes": ["50212194"],
            "dimensions": {"totalLengthMm": 2.0, "leftDecapeMm": 10, "rightDecapeMm": 12},
        },
    )
    check("validação BOM integrada", package_full["drawingAnalysis"]["criticalErrors"] == 0)

    meta: dict = {}
    ChatDrawingFollowUpService.attach_to_assistant_metadata(
        meta,
        intelligence={"drawingAnalysis": package_full["drawingAnalysis"]},
    )
    check("chips follow-up desenho", len(meta.get("drawingFollowUpSuggestions") or []) >= 3)

    package_nc = {
        "drawingAnalysis": {
            **package_full["drawingAnalysis"],
            "items": [
                *(package_full["drawingAnalysis"].get("items") or []),
                {
                    "section": "Smoke",
                    "item": "Item de teste",
                    "status": "error",
                    "recommendation": "Corrigir",
                },
            ],
        }
    }
    export_payload = ChatDrawingReportExportService.build_export_payload(
        package=package_nc,
        report_markdown=ChatDrawingValidationOrchestrationService.format_report_markdown(
            package_full
        ),
    )
    check("export CSV não conformidades", bool(export_payload.get("csv")))
    check("export linhas planilha", len(export_payload.get("spreadsheetRows") or []) >= 1)
    check("export PDF filename", str(export_payload.get("pdfFilename") or "").endswith(".pdf"))

    from app.application.services.chat_drawing_follow_up_turn_service import (
        ChatDrawingFollowUpTurnService,
    )

    follow_up = ChatDrawingFollowUpTurnService.resolve_direct_answer(
        "mostre apenas os erros críticos do relatório",
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {"drawingAnalysis": package_full["drawingAnalysis"]},
            }
        ],
    )
    check("follow-up erros críticos", bool(follow_up and "críticos" in follow_up.lower()))

    from app.domain.skills.chat_skill_registry import ChatSkillRegistry

    resolved = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata={},
        allowed_action_ids=["get_product_analyser"],
        has_agent=True,
    )
    check("skill default com analyser", resolved.get("drawingAnalysis") is True)

    resolved_externa = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata={},
        allowed_action_ids=["api_externa.products.get_product_analyser"],
        has_agent=True,
    )
    check(
        "skill com api-externa analyser",
        resolved_externa.get("drawingAnalysis") is True,
    )

    from app.application.services.external_actions.external_action_selection_service import (
        ExternalActionSelectionService,
    )
    from app.domain.services.chat_web_search_intent_service import (
        ChatWebSearchIntentService,
    )
    from app.infrastructure.config.settings import Settings

    class _SmokeActionRepo:
        def __init__(self, actions):
            self.actions = actions

        def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
            return self.actions

        def list_actions(self):
            return self.actions

    prev_prefer = Settings.CHAT_PREFER_API_EXTERNA_PROVIDER
    Settings.CHAT_PREFER_API_EXTERNA_PROVIDER = True
    prev_blocks = ChatWebSearchIntentService.blocks_external_action_selection
    ChatWebSearchIntentService.blocks_external_action_selection = staticmethod(
        lambda message: False
    )
    try:
        selection = ExternalActionSelectionService(
            _SmokeActionRepo(
                [
                    {
                        "actionId": "api_delpi.products.get_product_analyser",
                        "method": "GET",
                        "path": "/products/{code}/analyser",
                        "operationId": "get_product_analyser",
                        "parametersSchema": [
                            {"name": "code", "in": "path", "required": True},
                            {"name": "page_size", "in": "query"},
                            {"name": "max_depth", "in": "query"},
                        ],
                    },
                    {
                        "actionId": "api_externa.products.get_product_analyser",
                        "method": "GET",
                        "path": "/products/{code}/analyser",
                        "operationId": "get_product_analyser",
                        "parametersSchema": [
                            {"name": "code", "in": "path", "required": True},
                            {"name": "page_size", "in": "query"},
                            {"name": "max_depth", "in": "query"},
                        ],
                    },
                ]
            )
        ).select_action(
            "analise o desenho 90260140",
            allowed_action_ids=[
                "api_delpi.products.get_product_analyser",
                "api_externa.products.get_product_analyser",
            ],
        )
        check(
            "roteamento desenho → api-externa analyser",
            selection is not None
            and selection["arguments"]["actionId"]
            == "api_externa.products.get_product_analyser",
        )
    finally:
        Settings.CHAT_PREFER_API_EXTERNA_PROVIDER = prev_prefer
        ChatWebSearchIntentService.blocks_external_action_selection = prev_blocks

    from app.application.services.chat_drawing_admin_debug_service import (
        ChatDrawingAdminDebugService,
    )

    trace = ChatDrawingAdminDebugService.build_trace(
        tool_context={
            "drawingAnalysisMode": True,
            "drawingPdfExtractSummary": {"productCode": "90260140", "legible": True},
            "drawingAnalysis": package_full["drawingAnalysis"],
            "drawingAnalysisExport": export_payload,
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": "/products/90260140/analyser",
                        "statusCode": 200,
                    },
                    "arguments": {"code": "90260140"},
                }
            ],
        },
        intent_route={"intent": "drawing_analysis"},
        workspace_context={"skills": {"drawingAnalysis": True}},
    )
    check(
        "adminDebug drawing trace",
        bool(trace)
        and len(trace.get("phases") or []) >= 5
        and trace["phases"][0]["id"] == "intent",
    )

    from app.application.services.chat_drawing_metrics_service import (
        ChatDrawingMetricsService,
    )

    metrics = ChatDrawingMetricsService.build_snapshot(
        package_full["drawingAnalysis"],
        report_exported=True,
        analyser_ok=True,
    )
    check(
        "métricas drawingAnalysis",
        metrics.get("productCode") == "90260140"
        and metrics.get("checklistItems", 0) > 0
        and metrics.get("overallStatus") in {
            "approved",
            "approved_with_notes",
            "rejected",
            "incomplete",
        },
    )

    api_root = Path(__file__).resolve().parents[1]
    pytest_env = {**os.environ, "PYTHONPATH": os.environ.get("PYTHONPATH", str(api_root))}
    pytest_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit/domain/services/test_drawing_analysis_skill.py",
            "-q",
        ],
        cwd=str(api_root),
        env=pytest_env,
        capture_output=True,
        text=True,
    )

    if pytest_result.returncode == 0:
        check("regressão D1–D12 (pytest)", True)
    else:
        if pytest_result.stdout:
            print(pytest_result.stdout, file=sys.stderr)
        if pytest_result.stderr:
            print(pytest_result.stderr, file=sys.stderr)
        check("regressão D1–D12 (pytest)", False)

    if failed:
        print(f"\n{failed} verificação(ões) falharam", file=sys.stderr)
        return 1

    print("Smoke drawing analyser: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
