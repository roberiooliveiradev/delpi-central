from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import (
    load_api_delpi_fixture,
    load_api_delpi_fixture_with_meta,
    with_api_delpi_meta,
)
from tests.unit.application.use_cases.test_execute_external_action_analyser_presentation import (
    _raw_analyser_api_payload,
)


def test_prepare_presentation_root_normalizes_analyser_by_meta_entity():
    presenter = ExternalActionResultPresenter()
    envelope = with_api_delpi_meta(
        _raw_analyser_api_payload(),
        {
            "entity": "product_analyser",
            "shape": "composite_analysis",
            "operationId": "get_product_analyser",
        },
    )

    prepared = presenter.prepare_presentation_data(
        envelope,
        path="/products/90260148/analyser",
    )

    assert isinstance(prepared, dict)
    structure = prepared.get("structure")

    assert isinstance(structure, dict)
    assert isinstance(structure.get("root"), dict)
    assert isinstance(structure.get("items"), list)


def test_prepare_presentation_root_keeps_baseline_fixture_compatible():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_analyser_90269001.json")

    prepared = presenter.prepare_presentation_data(
        envelope,
        path="/products/90269001/analyser",
    )

    assert isinstance(prepared, dict)
    assert prepared.get("structure", {}).get("items")

    humanized = presenter.present(envelope, path="/products/90269001/analyser")
    tree = presenter.build_tree_presentation(prepared, path="/products/90269001/analyser")

    assert humanized.get("titulo")
    assert tree is not None
    assert tree["type"] == "tree"


def test_prepare_presentation_root_keeps_unrelated_payload_untouched():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture("product_stock_90269001.json")

    prepared = presenter.prepare_presentation_data(
        envelope,
        path="/products/90269001/stock",
    )

    assert prepared is envelope
