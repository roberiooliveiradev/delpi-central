from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_present_stock_fixture_routes_by_meta_without_stock_path() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")

    humanized = presenter.present(envelope, path="")

    assert humanized.get("titulo")
    body = "\n".join(
        [*(humanized.get("linhas") or []), *(humanized.get("linhas_detalhe") or [])]
    )
    assert "105" in body or "150" in body or "filial" in body.lower()


def test_present_structure_fixture_routes_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_90269001.json")

    humanized = presenter.present(envelope, path="")

    body = "\n".join(humanized.get("linhas") or [])

    assert "50219001" in body or "INTERMEDIARIO" in body


def test_present_factory_status_fixture_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")

    humanized = presenter.present(envelope, path="")

    body = "\n".join(humanized.get("linhas") or [])

    assert "OP ABERTA" in body or "Status fabril" in body


def test_build_presentation_stock_table_from_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")

    table = presenter.build_presentation(envelope, path="")

    assert table is not None
    assert table["type"] == "table"
    assert len(table.get("rows") or []) >= 1


def test_build_presentation_factory_status_table_from_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")

    table = presenter.build_presentation(envelope, path="")

    assert table is not None
    assert table["type"] == "table"
    assert any(row.get("campo") == "Status fabril" for row in table.get("rows") or [])


def test_present_analyser_fixture_still_works_with_meta() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_analyser_90269001.json")

    humanized = presenter.present(
        envelope,
        path="/products/90269001/analyser",
    )

    assert humanized.get("titulo")
    assert humanized.get("linhas")
