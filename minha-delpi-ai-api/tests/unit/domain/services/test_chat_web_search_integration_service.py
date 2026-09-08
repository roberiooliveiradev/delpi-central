from unittest.mock import patch

from app.domain.services.chat_web_search_integration_service import (
    ChatWebSearchIntegrationService,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_resolve_internal_product_hybrid(_enabled):
    integration = ChatWebSearchIntegrationService.resolve(
        "consulte nosso produto 10080001 e pesquise na web datasheet publico"
    )

    assert integration is not None
    assert integration.mode == "internal_product"
    assert integration.product_code == "10080001"
    assert integration.allow_operational_companion is True
    assert len(integration.extra_queries) >= 2


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_resolve_attachment_compare_with_context(_enabled):
    integration = ChatWebSearchIntegrationService.resolve(
        "pesquise na web e compare com o anexo",
        attachment_context="### manual.pdf\nMotor WEG W22",
    )

    assert integration is not None
    assert integration.mode == "attachment_compare"
    assert integration.attachment_label == "manual.pdf"


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_should_allow_operational_companion(_enabled):
    assert ChatWebSearchIntegrationService.should_allow_operational_companion(
        "consulte nosso produto 10080001 e busque na web manual"
    )
    assert not ChatWebSearchIntegrationService.should_allow_operational_companion(
        "pesquise na internet sobre clima"
    )


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_blocks_external_action_selection_allows_hybrid(_enabled):
    assert not ChatWebSearchIntentService.blocks_external_action_selection(
        "consulte nosso produto 10080001 e pesquise na web datasheet"
    )
    assert ChatWebSearchIntentService.blocks_external_action_selection(
        "pesquise na internet sobre python"
    )


@patch.object(ChatWebSearchIntentService, "is_auto_augment_enabled", return_value=True)
@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_rol_kpi_message_does_not_block_openapi(_enabled, _augment):
    message = (
        "Quero o ROL / indicadores comerciais recentes: mostre o número "
        "principal (KPI), a série no tempo em gráfico se disponível, e uma "
        "leitura em prosa do que está acontecendo — tudo na mesma resposta."
    )

    assert not ChatWebSearchIntentService.blocks_external_action_selection(message)
    assert ChatWebSearchIntentService._has_operational_companion_terms(message)


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_resolve_includes_integration_mode(_enabled):
    result = ChatWebSearchIntentService.resolve(
        "consulte nosso produto 10080001 e pesquise na web datasheet",
    )

    assert result is not None
    assert result["arguments"]["integrationMode"] == "internal_product"
    assert result["arguments"]["integrationProductCode"] == "10080001"
