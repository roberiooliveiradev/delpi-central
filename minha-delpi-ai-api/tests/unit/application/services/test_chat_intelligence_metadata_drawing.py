from app.application.services.chat_intelligence_metadata_service import (
    ChatIntelligenceMetadataService,
)


def test_build_includes_drawing_analysis_and_export():
    metadata = ChatIntelligenceMetadataService.build(
        sources=[],
        tool_context={
            "drawingAnalysisMode": True,
            "drawingAnalysis": {"productCode": "90260140", "items": [{"id": "bom"}]},
            "drawingAnalysisExport": {
                "markdown": "# Relatório",
                "filename": "relatorio-desenho-90260140.md",
            },
            "toolCalls": [],
        },
    )

    assert metadata["drawingAnalysisMode"] is True
    assert metadata["drawingAnalysis"]["productCode"] == "90260140"
    assert metadata["drawingAnalysisExport"]["markdown"] == "# Relatório"
