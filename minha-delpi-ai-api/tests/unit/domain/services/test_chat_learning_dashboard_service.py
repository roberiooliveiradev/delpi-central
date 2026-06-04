from app.domain.services.chat_learning_dashboard_service import ChatLearningDashboardService


def test_enrich_adds_rag_and_typo_dashboard():
    summary = ChatLearningDashboardService.enrich(
        summary={"highlights": {}, "funnel": {}},
        rag_index_counts={"glossary": 3, "user_memory": 2},
        top_typo_rules=[
            {"term": "vc", "normalizedTerm": "voce", "evidenceCount": 4},
        ],
    )

    assert summary["ragIndex"]["glossaryDocuments"] == 3
    assert summary["ragIndex"]["userMemoryDocuments"] == 2
    assert summary["highlights"]["ragGlossaryIndexed"] == 3
    assert summary["dashboard"]["topTypoRules"][0]["term"] == "vc"
