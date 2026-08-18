from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_llm_synthesis_delivery_content_service import (
    ChatLlmSynthesisDeliveryContentService,
)
from app.domain.services.chat_meta_llm_synthesis_service import (
    ChatMetaLlmSynthesisService,
    MetaLlmSynthesisSection,
    SECTION_CAPABILITIES,
    SECTION_PROFILE,
)

configure_domain_infrastructure_ports()


def test_compound_user_message_lead_loaded_from_json():
    lead = ChatLlmSynthesisDeliveryContentService.compound_user_message_lead()

    assert "blocos de fatos abaixo" in lead.lower()
    assert "não invente" in lead.lower()


def test_common_leak_markers_loaded_from_json():
    markers = ChatLlmSynthesisDeliveryContentService.common_leak_markers()

    assert "não copie este bloco" in markers
    assert "não invente rotas" in markers


def test_compound_user_message_uses_delivery_lead():
    lead = ChatLlmSynthesisDeliveryContentService.compound_user_message_lead()
    composed = ChatMetaLlmSynthesisService.compose_user_message(
        sections=[
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
        ],
        question="quem sou e o que posso fazer?",
    )

    assert composed.startswith(lead)
    assert "Ana" in composed
    assert "Consultas operacionais" in composed
