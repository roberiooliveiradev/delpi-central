from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_entity_route_dispatch_service import (
    ChatPresentationEntityRouteDispatchService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

configure_domain_infrastructure_ports()


def test_resolve_spec_uses_profile_key_for_structure_exclusivity():
    spec = ChatPresentationEntityRouteDispatchService.resolve_spec(
        entity="product_structure_exclusivity",
        path="/products/90261805/structure/exclusivity",
    )

    assert spec is not None
    assert spec.get("presenterMethod") == "present_product_structure_exclusivity"


def test_resolve_spec_prefers_entity_override_for_analyser():
    spec = ChatPresentationEntityRouteDispatchService.resolve_spec(
        entity="product_analyser",
        path="/products/90269001/analyser",
    )

    assert spec is not None
    assert spec.get("presenterMethod") == "present_product_analyser"
    assert spec.get("normalizeRoot") is True
    assert spec.get("requiresProduct") is True


def test_try_present_structure_exclusivity_fixture():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90261805.json")
    root = presenter._unwrap_data(envelope)

    handled, result = ChatPresentationEntityRouteDispatchService.try_present(
        presenter,
        root,
        path="/products/90261805/structure/exclusivity",
        entity="product_structure_exclusivity",
        profile=type("Profile", (), {"entity": "product_structure_exclusivity"})(),
    )

    assert handled is True
    assert isinstance(result, dict)
    assert result.get("titulo") or result.get("linhas")


def test_try_present_directives_fixture():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_directives_90260882.json")
    root = presenter._unwrap_data(envelope)

    handled, result = ChatPresentationEntityRouteDispatchService.try_present(
        presenter,
        root,
        path="/products/directives/90260882",
        entity="product_directives",
        profile=type("Profile", (), {"entity": "product_directives"})(),
    )

    assert handled is True
    assert isinstance(result, dict)
    assert result.get("titulo") or result.get("linhas")
