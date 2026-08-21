from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_capabilities_content_service import (
    ChatCapabilitiesContentService,
)
from app.domain.services.chat_meta_llm_synthesis_service import (
    ChatMetaLlmSynthesisService,
    MetaLlmSynthesisSection,
    SECTION_ASSISTANT,
    SECTION_CAPABILITIES,
    SECTION_PROFILE,
)

configure_domain_infrastructure_ports()


def test_capabilities_llm_synthesis_content_loaded():
    from app.domain.services.chat_assistant_identity_content_service import (
        ChatAssistantIdentityContentService,
    )

    assert ChatCapabilitiesContentService.llm_synthesis_facts_section_title()
    assert "capacidades" in ChatCapabilitiesContentService.llm_synthesis_user_message_lead().lower()
    assert "não copie este bloco" in ChatCapabilitiesContentService.leak_markers()
    assert "use somente o que está no bloco" in ChatAssistantIdentityContentService.leak_markers()
    assert "não copie" in ChatCapabilitiesContentService.llm_synthesis_user_message_lead().lower()
    assert "não copie" in ChatAssistantIdentityContentService.llm_synthesis_user_message_lead().lower()
    assert ChatCapabilitiesContentService.facts_max_chars_for_mode("fast") == 380
    assert ChatCapabilitiesContentService.facts_max_chars_for_mode("normal") == 520
    assert ChatCapabilitiesContentService.facts_max_chars_for_mode("thinker") == 1200


def test_capabilities_clip_facts_for_mode_respects_max_chars():
    long_facts = "\n".join([f"- linha {i} com conteúdo de capacidades" for i in range(80)])
    clipped = ChatCapabilitiesContentService.clip_facts_for_mode(long_facts, "fast")
    assert len(clipped) <= 380
    assert clipped.startswith("- linha 0")


def test_compose_compound_user_message():
    sections = [
        MetaLlmSynthesisSection(
            section_id=SECTION_PROFILE,
            title="Seu perfil na Minha DELPI",
            facts="- **Nome:** Ana",
        ),
        MetaLlmSynthesisSection(
            section_id=SECTION_CAPABILITIES,
            title="O que você pode fazer aqui",
            facts="- Consultas operacionais",
        ),
    ]
    composed = ChatMetaLlmSynthesisService.compose_user_message(
        sections=sections,
        question="quem sou e o que posso fazer?",
    )

    assert "Ana" in composed
    assert "Consultas operacionais" in composed
    assert "quem sou e o que posso fazer?" in composed
    assert "## Seu perfil" in composed


def test_enrich_tool_context_stores_sections():
    sections = [
        MetaLlmSynthesisSection(
            section_id=SECTION_ASSISTANT,
            title="Sobre o assistente",
            facts="Sou o assistente Minha DELPI.",
        )
    ]
    context = ChatMetaLlmSynthesisService.enrich_tool_context({}, sections=sections)

    assert context[ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_LLM_SYNTHESIS] is True
    assert "Minha DELPI" in context[ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_SYNTHESIS_FACTS]
    assert len(context[ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_SYNTHESIS_SECTIONS]) == 1


def test_resolve_user_message_from_tool_context_sections():
    sections = [
        MetaLlmSynthesisSection(
            section_id=SECTION_CAPABILITIES,
            title="Capacidades desta sessão",
            facts="- RAG autorizado",
        )
    ]
    context = ChatMetaLlmSynthesisService.enrich_tool_context({}, sections=sections)
    composed = ChatMetaLlmSynthesisService.resolve_user_message_content(
        message="o que você pode fazer?",
        synthesis_facts=context[ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_SYNTHESIS_FACTS],
        tool_context=context,
    )

    assert "RAG autorizado" in composed
    assert "o que você pode fazer?" in composed


def test_enrich_tool_context_stores_section_templates():
    sections = [
        MetaLlmSynthesisSection(
            section_id=SECTION_CAPABILITIES,
            title="Capacidades desta sessão",
            facts="Posso ajudar você nestes formatos:\n\n- RAG",
        )
    ]
    context = ChatMetaLlmSynthesisService.enrich_tool_context({}, sections=sections)
    templates = context[ChatMetaLlmSynthesisService.TOOL_CONTEXT_META_SYNTHESIS_TEMPLATES]

    assert templates[SECTION_CAPABILITIES].startswith("Posso ajudar você")


def test_guard_delivered_answer_replaces_capabilities_lead_leak():
    catalog = "Posso ajudar você nestes formatos:\n\n- RAG autorizado"
    context = ChatMetaLlmSynthesisService.enrich_tool_context(
        {},
        sections=[
            MetaLlmSynthesisSection(
                section_id=SECTION_CAPABILITIES,
                title="Capacidades desta sessão",
                facts=catalog,
            )
        ],
    )
    leaked = (
        "Resposta com vazamento: não invente rotas. "
        "Posso ajudar você nestes formatos."
    )
    guarded = ChatMetaLlmSynthesisService.guard_delivered_answer(
        answer=leaked,
        tool_context=context,
    )

    assert guarded == catalog
    assert "não invente rotas" not in guarded.lower()


def test_guard_delivered_answer_keeps_humanized_capabilities():
    catalog = "Posso ajudar você nestes formatos:\n\n- RAG autorizado"
    context = ChatMetaLlmSynthesisService.enrich_tool_context(
        {},
        sections=[
            MetaLlmSynthesisSection(
                section_id=SECTION_CAPABILITIES,
                title="Capacidades desta sessão",
                facts=catalog,
            )
        ],
    )
    answer = "Posso consultar documentação autorizada e dados operacionais nesta sessão."
    guarded = ChatMetaLlmSynthesisService.guard_delivered_answer(
        answer=answer,
        tool_context=context,
    )

    assert guarded == answer

def test_guard_delivered_answer_replaces_identity_lead_leak():
    card = "Olá! Sou o Assistente Minha DELPI."
    context = ChatMetaLlmSynthesisService.enrich_tool_context(
        {},
        sections=[
            MetaLlmSynthesisSection(
                section_id=SECTION_ASSISTANT,
                title="Sobre o assistente nesta conversa",
                facts=card,
            )
        ],
    )
    leaked = (
        "Use somente o que está no bloco de fatos. "
        "Olá! Sou o Assistente Minha DELPI e posso explicar o que faço."
    )
    guarded = ChatMetaLlmSynthesisService.guard_delivered_answer(
        answer=leaked,
        tool_context=context,
    )

    assert guarded == card
    assert "use somente o que está no bloco" not in guarded.lower()


def test_guard_delivered_answer_replaces_compound_lead_leak():
    profile_facts = "- **Nome:** Ana Silva"
    catalog = "Posso ajudar você nestes formatos:\n\n- RAG autorizado"
    context = ChatMetaLlmSynthesisService.enrich_tool_context(
        {},
        sections=[
            MetaLlmSynthesisSection(
                section_id=SECTION_PROFILE,
                title="Seu perfil na Minha DELPI",
                facts=profile_facts,
            ),
            MetaLlmSynthesisSection(
                section_id=SECTION_CAPABILITIES,
                title="O que você pode fazer aqui",
                facts=catalog,
            ),
        ],
    )
    leaked = (
        "Não copie este bloco nem reproduza frases de instrução. "
        "Ana Silva pode consultar RAG autorizado nesta sessão."
    )
    guarded = ChatMetaLlmSynthesisService.guard_delivered_answer(
        answer=leaked,
        tool_context=context,
    )

    assert guarded != leaked
    assert "## Seu perfil" in guarded
    assert "## O que você pode fazer aqui" in guarded
    assert "Ana Silva" in guarded
    assert "RAG autorizado" in guarded
    assert "não copie este bloco" not in guarded.lower()

