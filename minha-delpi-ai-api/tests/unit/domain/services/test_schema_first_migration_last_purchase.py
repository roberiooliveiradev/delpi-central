"""Playbook 22 Fase C — last_purchase migrado para apresentação schema-first."""

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_schema_driven_presentation_service import (
    ChatSchemaDrivenPresentationService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_last_purchase_uses_schema_first_by_default():
    assert ChatPresentationProfileService.uses_schema_first_presentation(
        "/products/10080001/last-purchase",
        "product_last_purchase",
    )


def test_last_purchase_extracts_nested_record_rows():
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")
    rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(envelope["data"])

    assert len(rows) == 1
    assert rows[0].get("unit_price") == 0.089
    assert rows[0].get("supplier_code") == "000002"


def test_product_last_purchase_present_uses_schema_driven_table():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")
    path = "/products/10080001/last-purchase"

    presentation = presenter.build_presentation(envelope["data"], path=path)

    assert isinstance(presentation, dict)
    assert presentation.get("type") == "table"
    assert len(presentation.get("rows") or []) == 1


def test_product_last_purchase_metadata_pipeline_schema_first():
    use_case = ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")
    path = "/products/10080001/last-purchase"

    meta = use_case._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope["data"],
        resolved_path=path,
        request_parameters={},
    )

    assert "table" in meta.get("availableFormats", [])
    table = meta.get("tablePresentation") or meta.get("presentation")
    assert isinstance(table, dict)
    assert table.get("type") == "table"
    rows = table.get("rows") or []
    assert len(rows) == 1
    assert rows[0].get("supplier_code") == "000002"
    assert rows[0].get("supplier_name") == "TE CONNECTIVITY"
