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
    assert ChatUserProfileIntentService.is_user_identity_question("o que eu posso fazer aqui?")
    assert not ChatUserProfileIntentService.is_user_identity_question("quem é você?")
    assert not ChatUserProfileIntentService.is_user_identity_question("o que vc faz?")


def test_first_person_access_suppresses_capabilities_unless_assistant_subject():
    assert ChatUserProfileIntentService.suppresses_capabilities_intent(
        "o que eu posso fazer aqui?"
    )
    assert not ChatUserProfileIntentService.suppresses_capabilities_intent(
        "quem sou eu e o que você pode fazer?"
    )
    assert ChatUserProfileIntentService.asks_about_assistant("o que você pode fazer?")


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


def test_guard_answer_falls_back_on_placeholder():
    facts = "- **Nome:** Robério Oliveira\n- **Email:** inovacao@delpi.com.br"
    fallback = ChatUserProfileLlmSynthesisService.guard_answer(
        answer="Olá [Seu Nome], sua permissão principal é auditoria-5s.view.filial-01.",
        synthesis_facts=facts,
        fallback="Você é Robério Oliveira (inovacao@delpi.com.br).",
    )

    assert "Robério Oliveira" in fallback
    assert "[Seu Nome]" not in fallback


def test_guard_answer_falls_back_when_name_missing():
    facts = "- **Nome:** Robério Oliveira\n- **Email:** inovacao@delpi.com.br"
    fallback = ChatUserProfileLlmSynthesisService.guard_answer(
        answer="Sua permissão principal é auditoria-5s.view.filial-01.",
        synthesis_facts=facts,
        fallback=facts,
    )

    assert fallback == facts


def test_guard_answer_keeps_humanized_name():
    facts = "- **Nome:** Robério Oliveira\n- **Email:** inovacao@delpi.com.br"
    answer = "Você é Robério Oliveira (inovacao@delpi.com.br), Superadministrador."
    guarded = ChatUserProfileLlmSynthesisService.guard_answer(
        answer=answer,
        synthesis_facts=facts,
        fallback=facts,
    )

    assert guarded == answer
