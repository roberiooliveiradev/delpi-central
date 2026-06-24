from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_table_assembly_service import (
    ChatPresentationTableAssemblyService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

configure_domain_infrastructure_ports()


def test_try_build_presentation_table_uses_table_assembly_builder():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90261805.json")
    root = envelope["data"]
    path = "/products/90261805/structure/exclusivity"

    table = ChatPresentationTableAssemblyService.try_build_presentation_table(
        presenter,
        root,
        path,
        entity="product_structure_exclusivity",
    )

    assert isinstance(table, dict)
    assert table.get("type") == "table"
    assert "Resumo da estrutura" in str(table.get("title") or "")


def test_try_build_presentation_table_factory_fallback_is_declarative():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    root = envelope["data"]
    path = "/products/90269002/factory-status"
    profile = __import__(
        "app.domain.services.chat_presentation_profile_service",
        fromlist=["ChatPresentationProfileService"],
    ).ChatPresentationProfileService.resolve_profile(path, "product_factory_status")
    config = ChatPresentationTableAssemblyService.table_assembly_config(profile)

    assert config.get("presentationFallback") == "legacy_factory_table"
