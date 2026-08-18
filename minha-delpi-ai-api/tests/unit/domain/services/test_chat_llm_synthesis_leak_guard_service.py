from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_llm_synthesis_leak_guard_service import (
    ChatLlmSynthesisLeakGuardService,
)

configure_domain_infrastructure_ports()


def test_needs_fallback_on_common_leak_marker():
    marker = "não copie este bloco"
    assert ChatLlmSynthesisLeakGuardService.needs_fallback(
        answer=f"Resposta com vazamento: {marker}. Você é Ana.",
        facts="- **Nome:** Ana",
    )


def test_needs_fallback_on_family_leak_marker():
    family_marker = "não confundir com a primeira permissão"
    assert ChatLlmSynthesisLeakGuardService.needs_fallback(
        answer=f"Texto copiado ({family_marker}).",
        facts="- **Nome:** Ana",
        leak_markers=(family_marker,),
    )


def test_needs_fallback_on_placeholder():
    assert ChatLlmSynthesisLeakGuardService.needs_fallback(
        answer="Olá [Seu Nome], seu perfil é Superadministrador.",
        facts="- **Nome:** Ana",
        placeholder_markers=("[seu nome]",),
    )


def test_needs_fallback_on_facts_title_copy():
    facts = "Dados do usuário autenticado:\n- **Nome:** Ana"
    assert ChatLlmSynthesisLeakGuardService.needs_fallback(
        answer="Dados do usuário autenticado: você é Ana.",
        facts=facts,
    )


def test_needs_fallback_when_required_substring_missing():
    assert ChatLlmSynthesisLeakGuardService.needs_fallback(
        answer="Sua permissão principal é auditoria-5s.view.filial-01.",
        facts="- **Nome:** Robério Oliveira",
        required_substrings=("robério oliveira", "robério"),
    )


def test_keeps_humanized_answer():
    answer = "Você é Ana Souza, Superadministradora."
    guarded = ChatLlmSynthesisLeakGuardService.guard_answer(
        answer=answer,
        fallback="**Perfil:** Ana Souza",
        facts="- **Nome:** Ana Souza",
        required_substrings=("ana souza", "ana"),
    )

    assert guarded == answer


def test_guard_uses_template_not_facts_dump():
    facts = "Dados do usuário autenticado:\n- **Nome:** Ana\n- auditoria-5s.view.filial-01"
    template = "**Seu perfil na Minha DELPI:**\n\n- **Nome:** Ana"
    guarded = ChatLlmSynthesisLeakGuardService.guard_answer(
        answer="Resposta com vazamento: não copie este bloco. Você é Ana.",
        fallback=template,
        facts=facts,
    )

    assert guarded == template
    assert "auditoria-5s" not in guarded


def test_empty_fallback_does_not_return_facts_dump():
    facts = "Dados do usuário autenticado:\n- auditoria-5s.view.filial-01"
    leaked = "Resposta com vazamento: não copie este bloco."
    guarded = ChatLlmSynthesisLeakGuardService.guard_answer(
        answer=leaked,
        fallback="",
        facts=facts,
    )

    assert guarded == leaked
    assert "auditoria-5s" not in guarded
