from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from app.domain.services.external_actions.operational_route_narrative_service import (
    ExternalActionOperationalRouteNarrativeService,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_format_production_flag_handles_bool_and_legacy_codes():
    assert ExternalActionOperationalRouteNarrativeService.format_production_flag(True) == "Sim"
    assert ExternalActionOperationalRouteNarrativeService.format_production_flag(False) == "Não"
    assert ExternalActionOperationalRouteNarrativeService.format_production_flag("SIM") == "Sim"
    assert ExternalActionOperationalRouteNarrativeService.format_production_flag("NAO") == "Não"


def test_present_production_status_schema_first():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_production_status_90269002.json")

    humanized = presenter.present(envelope, path="")
    body = "\n".join(
        [*(humanized.get("linhas") or []), humanized.get("humanizedMarkdown") or ""]
    ).lower()

    assert "playbook" not in body
    assert humanized.get("titulo")


def test_format_quantity_uses_presenter_number_formatting():
    presenter = ExternalActionResultPresenter()

    formatted = ExternalActionOperationalRouteNarrativeService.format_quantity(
        presenter,
        289.178,
        field_key="reported_quantity",
    )

    assert "289" in formatted
    assert "99999999999994" not in formatted
