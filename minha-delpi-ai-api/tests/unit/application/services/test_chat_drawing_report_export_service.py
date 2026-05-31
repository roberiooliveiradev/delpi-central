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
    assert "Relatório" in payload["markdown"]
