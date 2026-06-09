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


def test_present_production_status_does_not_use_playbook_wording():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_production_status_90269002.json")

    humanized = presenter.present(envelope, path="")
    body = "\n".join(
        [*(humanized.get("linhas") or []), humanized.get("humanizedMarkdown") or ""]
    ).lower()

    assert "playbook" not in body
    assert "análise produtiva" in humanized.get("titulo", "").lower()


def test_production_status_text_presentation_uses_scope_intro_and_compact_tables():
    from app.domain.services.chat_rich_presentation_text_service import (
        ChatRichPresentationTextService,
    )

    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_production_status_90269002.json")
    root = envelope["data"]
    path = "/products/90269002/production-status"
    tables = presenter.build_production_status_table_presentations(root, path)
    compact = ChatRichPresentationTextService.should_compact_narrative(
        table_presentations=tables,
    )

    text = presenter._build_production_status_text_presentation(root, path)

    assert text is not None
    markdown = str(text.get("markdown") or "")
    assert "playbook" not in markdown.lower()

    if compact:
        assert "90269002" in markdown
        assert "tabela" in markdown.lower()
    else:
        assert "Situação produtiva do PA" in markdown


def test_format_quantity_uses_presenter_number_formatting():
    presenter = ExternalActionResultPresenter()

    formatted = ExternalActionOperationalRouteNarrativeService.format_quantity(
        presenter,
        289.178,
        field_key="reported_quantity",
    )

    assert "289" in formatted
    assert "99999999999994" not in formatted
