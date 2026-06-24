"""Playbook 22 Fase C — purchase_list migrado para apresentação schema-first."""

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_purchase_list_and_last_purchase_use_schema_first_by_default():
    assert ChatPresentationProfileService.uses_schema_first_presentation(
        "/products/10080001/purchases",
        "product_purchases",
    )
    assert ChatPresentationProfileService.uses_schema_first_presentation(
        "/products/10080001/last-purchase",
        "product_last_purchase",
    )


def test_product_purchases_present_uses_schema_driven_table():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_purchases_10080001.json")
    path = "/products/10080001/purchases"

    presentation = presenter.build_presentation(envelope["data"], path=path)

    assert isinstance(presentation, dict)
    assert presentation.get("type") == "table"
    assert len(presentation.get("rows") or []) == 2


def test_product_purchases_metadata_pipeline_schema_first():
    use_case = ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )
    envelope = load_api_delpi_fixture_with_meta("product_purchases_10080001.json")
    path = "/products/10080001/purchases"

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
    assert len(table.get("rows") or []) == 2
