from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_prose_delivery_content_service import (
    ChatPresentationProseDeliveryContentService,
)

configure_domain_infrastructure_ports()


def test_require_response_modes_for_llm_prose_default_true():
    assert ChatPresentationProseDeliveryContentService.require_response_modes_for_llm_prose()


def test_metadata_keys_from_bundle():
    assert (
        ChatPresentationProseDeliveryContentService.metadata_key("deliveryMode")
        == "proseDeliveryMode"
    )
