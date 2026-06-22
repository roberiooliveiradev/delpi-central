from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_response_mode_content_service import (
    ChatResponseModeContentService,
)

configure_domain_infrastructure_ports()


def test_mode_catalog_has_three_modes():
    modes = ChatResponseModeContentService.mode_catalog()

    assert len(modes) == 3
    assert {item["id"] for item in modes} == {"fast", "normal", "thinker"}


def test_alias_map_resolves_rapida():
    aliases = ChatResponseModeContentService.alias_map()

    assert aliases.get("rapida") == "fast"
    assert aliases.get("pensador") == "thinker"


def test_pipeline_effect_text():
    text = ChatResponseModeContentService.pipeline_effect_text("operational_direct")

    assert "dados" in text.lower()


def test_commentary_lead_depth_by_mode():
    assert ChatResponseModeContentService.commentary_lead_depth_for_mode("fast") == "brief"
    assert ChatResponseModeContentService.commentary_lead_depth_for_mode("thinker") == "expanded"
