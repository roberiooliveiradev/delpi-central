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
    assert ChatCapabilitiesContentService.llm_synthesis_facts_section_title()
    assert "capacidades" in ChatCapabilitiesContentService.llm_synthesis_user_message_lead().lower()


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
