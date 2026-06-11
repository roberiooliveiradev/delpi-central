from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


def test_static_rules_loaded_from_catalog():
    configure_domain_infrastructure_ports()

    assert ChatMessageNormalizationService.static_rule_count() >= 150


def test_normalize_estouque_from_catalog():
    configure_domain_infrastructure_ports()

    result = ChatMessageNormalizationService.normalize_for_matching(
        "estouque do produto 90262404"
    )

    assert "estoque" in result
    assert "90262404" in result.replace(" ", "")
