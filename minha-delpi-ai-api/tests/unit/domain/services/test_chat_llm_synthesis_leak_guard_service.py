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


def test_empty_fallback_uses_safe_fallback_not_leak():
    facts = "Dados do usuário autenticado:\n- auditoria-5s.view.filial-01"
    leaked = "Resposta com vazamento: não copie este bloco."
    guarded = ChatLlmSynthesisLeakGuardService.guard_answer(
        answer=leaked,
        fallback="",
        facts=facts,
    )

    assert guarded != leaked
    assert "não copie este bloco" not in guarded.lower()
    assert "auditoria-5s" not in guarded
    assert "reformular" in guarded.lower() or "clara" in guarded.lower()


def test_needs_fallback_on_english_cot_marker():
    assert ChatLlmSynthesisLeakGuardService.needs_fallback(
        answer=(
            "According to my instructions, the user's message is ambiguous. "
            "I should ask for clarification."
        ),
    )


def test_needs_fallback_on_capabilities_cot_leak():
    """Regressão: Kimi/OpenRouter devolve CoT EN como resposta de capacidades."""
    leaked = (
        "This is a capabilities question. I should respond based on the session's "
        "capability facts: list what the agent can do, organized by theme, in natural "
        "Brazilian Portuguese. Don't dump the entire catalog (373+ actions) — group "
        "into: produtos, estoque, produção. Keep it natural, professional, direct. "
        'Start with a short conclusion: "Você tem acesso bem amplo nesta sessão…"'
    )
    assert ChatLlmSynthesisLeakGuardService.needs_fallback(answer=leaked)
    guarded = ChatLlmSynthesisLeakGuardService.guard_answer(answer=leaked, fallback=None)
    assert guarded != leaked
    assert "capabilities question" not in guarded.lower()
    assert "don't dump" not in guarded.lower()


def test_guard_replaces_english_cot_with_safe_fallback():
    leaked = (
        "According to my instructions, the user's message is «programação». "
        "I should ask for clarification. Let me think step by step."
    )
    guarded = ChatLlmSynthesisLeakGuardService.guard_answer(
        answer=leaked,
        fallback=None,
    )

    assert guarded != leaked
    assert "according to my instructions" not in guarded.lower()
    assert "let me think" not in guarded.lower()
    assert guarded.strip()
