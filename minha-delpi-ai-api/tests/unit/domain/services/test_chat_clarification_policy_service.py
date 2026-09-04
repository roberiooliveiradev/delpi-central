from app.domain.services.chat_clarification_policy_service import (
    ChatClarificationPolicyService,
    ClarificationCandidate,
)


def test_product_search_skips_clarify():
    decision = ChatClarificationPolicyService.decide(
        [
            ClarificationCandidate(
                code="missing_product_code",
                material=True,
                answer="Informe o código.",
            )
        ],
        message="liste os top 50 terminais pino",
    )

    assert decision.action == "continue"
    assert decision.reason_code == "skipped_discoverable_search"
    assert decision.to_admin_debug()["action"] == "continue"


def test_missing_stock_code_still_clarifies():
    decision = ChatClarificationPolicyService.evaluate_missing_product_code(
        "qual o estoque do produto",
        answer="Para consultar estoque, informe o código (ex.: 10080099).",
    )

    assert decision.action == "clarify"
    assert decision.reason_code == "clarify_material_missing"
    assert decision.answer is not None
    assert "código" in decision.answer.lower()


def test_turn_analysis_clarify_suppressed_for_search():
    decision = ChatClarificationPolicyService.evaluate_turn_analysis_clarify(
        "pesquise pela descrição terminais pino",
        clarify_answer="Não ficou claro o que você precisa.",
    )

    assert decision.action == "continue"
    assert decision.reason_code == "skipped_discoverable_search"


def test_turn_analysis_clarify_kept_for_vague_message():
    """O gate discoverable não pode desligar todo clarify da análise de turno."""
    decision = ChatClarificationPolicyService.evaluate_turn_analysis_clarify(
        "isso",
        clarify_answer="Não ficou claro o que você precisa.",
    )

    assert decision.action == "clarify"
    assert decision.reason_code == "clarify_turn_analysis"
    assert decision.answer == "Não ficou claro o que você precisa."


def test_discoverable_candidate_continues():
    decision = ChatClarificationPolicyService.decide(
        [
            ClarificationCandidate(
                code="prior_api_fact",
                material=False,
                discoverable=True,
            )
        ],
        message="está dentro das normas?",
    )

    assert decision.action == "continue"
    assert decision.reason_code == "skipped_discoverable"
