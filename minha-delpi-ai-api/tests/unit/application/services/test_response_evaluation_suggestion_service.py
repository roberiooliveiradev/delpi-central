from app.application.services.response_evaluation_suggestion_service import (
    ResponseEvaluationSuggestionService,
)


def test_score_to_verdict_mapping():
    service = ResponseEvaluationSuggestionService()

    assert service.score_to_verdict(5) == "helpful"
    assert service.score_to_verdict(3) == "neutral"
    assert service.score_to_verdict(1) == "unhelpful"


def test_suggests_knowledge_when_no_sources_and_low_score():
    service = ResponseEvaluationSuggestionService()

    suggestions = service.build_suggestions(
        score=2,
        verdict="unhelpful",
        message_metadata={"sources": [], "adminGuidelines": []},
        user_question="Como solicitar férias?",
        assistant_answer="Não tenho essa informação.",
    )

    assert suggestions["documents"]
    assert suggestions["documents"][0]["type"] == "create_or_expand_knowledge"
    assert suggestions["guidelines"]


def test_suggests_review_when_sources_exist_but_low_score():
    service = ResponseEvaluationSuggestionService()

    suggestions = service.build_suggestions(
        score=2,
        verdict="unhelpful",
        message_metadata={
            "sources": [{"documentId": "doc-1", "title": "Manual RH"}],
            "adminGuidelines": [{"id": "g1", "title": "Tom institucional"}],
        },
        user_question="Qual o prazo?",
        assistant_answer="Resposta incompleta.",
    )

    assert any(item["type"] == "improve_document" for item in suggestions["documents"])
    assert any(item["type"] == "review_guideline" for item in suggestions["guidelines"])
