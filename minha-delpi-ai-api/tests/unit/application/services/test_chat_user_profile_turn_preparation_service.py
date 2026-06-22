from app.application.services.chat_user_profile_turn_preparation_service import (
    ChatUserProfileTurnPreparationService,
)
from app.domain.services.chat_user_profile_llm_synthesis_service import (
    ChatUserProfileLlmSynthesisService,
)


def test_apply_identity_llm_route_skips_direct_answers():
    result = ChatUserProfileTurnPreparationService.apply_identity_llm_route(
        message="quem sou eu?",
        tool_context={},
        pipeline_stages=["identity_shortcut"],
        resolve_profile_facts=lambda _message: "- **Nome:** Ana",
    )

    assert result.skip_user_direct_answer is True
    assert result.skip_rag is True
    assert result.skip_meta_direct_answer is True
    assert result.skip_compound_direct_answers is False
    assert result.tool_context[ChatUserProfileLlmSynthesisService.TOOL_CONTEXT_SYNTHESIS_FLAG]
    assert (
        ChatUserProfileLlmSynthesisService.PIPELINE_STAGE_IDENTITY_LLM_SYNTHESIS
        in result.pipeline_stages
    )


def test_apply_identity_llm_route_noop_for_non_profile_message():
    result = ChatUserProfileTurnPreparationService.apply_identity_llm_route(
        message="estoque do produto 10080001",
        tool_context={},
        pipeline_stages=[],
        resolve_profile_facts=lambda _message: None,
    )

    assert result.skip_user_direct_answer is False
    assert result.skip_rag is False
    assert result.tool_context == {}


def test_compound_profile_question_skips_other_direct_answers():
    message = "me diga quem sou eu e o que consigo fazer aqui"
    result = ChatUserProfileTurnPreparationService.apply_identity_llm_route(
        message=message,
        tool_context={},
        pipeline_stages=[],
        resolve_profile_facts=lambda _message: "Perfil",
        meta_intents=ChatUserProfileTurnPreparationService.detect_meta_intents(message),
    )

    assert result.skip_compound_direct_answers is True
