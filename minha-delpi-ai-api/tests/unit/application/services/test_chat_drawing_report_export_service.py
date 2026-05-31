from app.application.services.chat_drawing_report_export_service import (
    ChatDrawingReportExportService,
)


def test_build_export_payload():
    payload = ChatDrawingReportExportService.build_export_payload(
        package={"drawingAnalysis": {"productCode": "90260140"}},
        report_markdown="# Relatório de teste",
    )

    assert payload["filename"].startswith("relatorio-desenho-90260140")
    assert payload["filename"].endswith(".md")
    assert payload["pdfFilename"].endswith(".pdf")
    assert "90260140" in payload["pdfFilename"]
    assert "Relatório" in payload["markdown"]


def test_build_export_includes_csv_for_nonconformities():
    payload = ChatDrawingReportExportService.build_export_payload(
        package={
            "drawingAnalysis": {
                "productCode": "90260140",
                "items": [
                    {"section": "BOM", "item": "Falta comp", "status": "critical_error"},
                    {"section": "Cotas", "item": "OK", "status": "ok"},
                ],
            }
        },
        report_markdown="# Relatório",
    )

    assert payload.get("csvFilename", "").endswith(".csv")
    assert "Erro crítico" in (payload.get("csv") or "")
    assert len(payload.get("spreadsheetRows") or []) == 1
