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
    assert any(table.get("key") == "checklist" for table in payload.get("tables") or [])


def test_build_export_tables_include_operational_sections():
    payload = ChatDrawingReportExportService.build_export_payload(
        package={
            "drawingAnalysis": {
                "productCode": "90264227",
                "revisionPdf": "21",
                "hasPdfAttachment": True,
                "items": [
                    {"section": "BOM", "item": "Falta comp", "status": "critical_error"},
                    {"section": "API", "item": "Cadastro", "status": "ok"},
                ],
            },
            "productSummary": {
                "code": "90264227",
                "description": "CHICOTE",
                "last_revision_date": "20260617",
            },
            "analyserRoot": {
                "structure": {
                    "items": [
                        {
                            "code": "50215425",
                            "description": "CT26",
                            "quantity": 1,
                            "type": "INT",
                            "components": [{"code": "10440133", "quantity": 36}],
                        }
                    ]
                },
                "guide": {
                    "items": [
                        {
                            "product_code": "90264227",
                            "bom_level": 1,
                            "operation_code": "CT-99",
                            "work_center": "CT-01A",
                            "operation_description": "Montagem",
                        }
                    ]
                },
                "inspection": {
                    "items": [
                        {
                            "product": "90264227",
                            "level": 1,
                            "QP6": [1],
                            "QP7": [],
                            "QP8": [],
                        }
                    ]
                },
            },
        },
        report_markdown="# Relatório",
    )

    keys = {table["key"] for table in payload.get("tables") or []}

    assert keys == {
        "pdfData",
        "apiData",
        "structure",
        "guide",
        "inspection",
        "nonconformities",
        "checklist",
    }
    assert "Dados identificados no PDF" in (payload.get("csv") or "")
    assert "Estrutura (SG1010)" in (payload.get("csv") or "")
    assert payload.get("xlsxFilename", "").endswith(".xlsx")
