from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService


def test_action_planning_codes_only_from_message_when_present():
    codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
        "estoque do produto 10080099",
        conversation_context=(
            "assistant: Produto 10080001: A\nassistant: Produto 10080002: B"
        ),
    )

    assert codes == ["10080099"]


def test_action_planning_followup_resolves_single_code_from_context():
    codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
        "estoque desse produto",
        conversation_context="assistant: Produto 10080047: TERM. PINO",
    )

    assert codes == ["10080047"]
