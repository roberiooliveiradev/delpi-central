from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_user_profile_content_service import (
    ChatUserProfileContentService,
)
from app.domain.services.chat_user_profile_intent_service import (
    ChatUserProfileIntentService,
)
from app.domain.services.chat_user_profile_llm_synthesis_service import (
    ChatUserProfileLlmSynthesisService,
)

configure_domain_infrastructure_ports()


def test_identity_terms_loaded_from_json():
    terms = ChatUserProfileContentService.identity_terms()

    assert "quem sou eu" in terms
    assert "meu perfil" in terms


def test_is_user_identity_question():
    assert ChatUserProfileIntentService.is_user_identity_question("quem sou eu?")
    assert not ChatUserProfileIntentService.is_user_identity_question("quem é você?")


def test_compose_user_message_includes_profile_facts():
    composed = ChatUserProfileLlmSynthesisService.compose_user_message(
        profile_facts="- **Nome:** Ana\n- **Email:** ana@delpi.com.br",
        question="quem sou eu?",
    )

    assert "Ana" in composed
    assert "ana@delpi.com.br" in composed
    assert "quem sou eu?" in composed


def test_enrich_tool_context_sets_contract_keys():
    context = ChatUserProfileLlmSynthesisService.enrich_tool_context(
        {},
        profile_facts="Perfil",
    )

    assert context[ChatUserProfileLlmSynthesisService.TOOL_CONTEXT_SYNTHESIS_FLAG] is True
    assert context[ChatUserProfileLlmSynthesisService.TOOL_CONTEXT_SYNTHESIS_FACTS] == "Perfil"
