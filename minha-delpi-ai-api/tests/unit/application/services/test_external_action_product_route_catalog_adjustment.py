from app.application.services.external_actions.external_action_product_route_catalog_service import (
    ExternalActionProductRouteCatalogService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


def test_extract_adjustment_percent_from_simule_plus_notation():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "Simule +10% nos materiais do produto 90260140"
    )

    assert ExternalActionProductRouteCatalogService.extract_adjustment_percent(normalized) == 10.0


def test_extract_adjustment_percent_from_aumento_de_notation():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "Simule aumento de 10% nos materiais do produto 90261255"
    )

    assert ExternalActionProductRouteCatalogService.extract_adjustment_percent(normalized) == 10.0
