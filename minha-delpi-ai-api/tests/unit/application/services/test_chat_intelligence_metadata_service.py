from app.application.services.chat_intelligence_metadata_service import (
    ChatIntelligenceMetadataService,
)


def test_build_includes_selected_external_action_and_pipeline():
    metadata = ChatIntelligenceMetadataService.build(
        sources=[],
        tool_context={
            "toolCalls": [{"name": "execute_external_action"}],
            "selectedExternalAction": {
                "actionId": "stock-action",
                "reason": "estoque",
            },
            "directAnswer": "Resposta direta",
        },
        pipeline=ChatIntelligenceMetadataService.build_pipeline_flags(
            fast_path=False,
            operational_optimize=True,
            tool_context={"directAnswer": "Resposta direta"},
            skip_rag=True,
        ),
    )

    assert metadata["selectedExternalAction"]["actionId"] == "stock-action"
    assert metadata["pipeline"]["operationalFastPath"] is True
    assert metadata["pipeline"]["directResponse"] is True
    assert metadata["pipeline"]["skipRag"] is True
