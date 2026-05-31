from app.application.services.chat_canvas_content_service import ChatCanvasContentService


def test_canvas_copy_prefers_drawing_export_markdown():
    action = ChatCanvasContentService.resolve(
        "coloque o relatório na lousa",
        previous_messages=[
            {
                "role": "assistant",
                "id": "msg-1",
                "content": "Resumo curto da API.",
                "metadata": {
                    "drawingAnalysis": {"productCode": "90260140"},
                    "drawingAnalysisExport": {
                        "markdown": "# Relatório de Análise de Desenho DELPI\n\n## Checklist",
                    },
                },
            }
        ],
        workspace_context={"capabilities": {"canvas": True}},
    )

    assert action is not None
    assert action.open_payload is not None
    assert "Relatório de Análise" in action.open_payload.markdown
    assert action.open_payload.title == "Análise de desenho 90260140"
