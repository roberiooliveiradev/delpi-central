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
            stages=["ingress", "tools", "direct_answer", "skip_rag"],
        ),
    )

    assert metadata["selectedExternalAction"]["actionId"] == "stock-action"
    assert metadata["pipeline"]["operationalFastPath"] is True
    assert metadata["pipeline"]["directResponse"] is True
    assert metadata["pipeline"]["skipRag"] is True
    assert metadata["pipeline"]["stages"] == [
        "ingress",
        "tools",
        "direct_answer",
        "skip_rag",
    ]


def test_build_includes_rag_retrieved_and_visible_counts():
    metadata = ChatIntelligenceMetadataService.build(
        sources=[{"score": 0.9}],
        tool_context={"toolCalls": []},
        rag_stats={
            "retrievedSourceCount": 4,
            "visibleSourceCount": 1,
            "retrievedChunkCount": 4,
        },
    )

    assert metadata["ragSourceCount"] == 1
    assert metadata["ragVisibleSourceCount"] == 1
    assert metadata["ragRetrievedCount"] == 4
    assert metadata["ragRetrievedChunkCount"] == 4
