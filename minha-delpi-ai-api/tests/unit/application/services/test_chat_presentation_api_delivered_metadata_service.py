"""Pipeline API as-delivered — metadata mínima."""

from app.application.services.chat_presentation_api_delivered_metadata_service import (
    ChatPresentationApiDeliveredMetadataService,
)
from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def _use_case():
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_operational_routes_use_schema_first_by_default():
    assert ChatPresentationProfileService.uses_schema_first_presentation(
        "/products/90260144/stock",
        "product_stock",
    )
    assert ChatPresentationProfileService.uses_schema_first_presentation(
        "/products/90261805/structure/exclusivity",
        "product_structure_exclusivity",
    )


def test_api_delivered_metadata_for_list_payload():
    use_case = _use_case()
    envelope = load_api_delpi_fixture_with_meta("product_purchases_10080001.json")
    path = "/products/10080001/purchases"

    meta = use_case._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope["data"],
        resolved_path=path,
        request_parameters={},
    )

    assert "table" in meta.get("availableFormats", [])
    assert meta.get("presentationDecision")
    assert meta.get("renderPlan")
    primary = meta.get("presentation") or meta.get("textPresentation") or meta.get("tablePresentation")
    assert isinstance(primary, dict)
    assert primary.get("type") in {"table", "markdown"}


def test_api_delivered_metadata_for_composite_payload():
    use_case = _use_case()
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")
    path = "/products/10080001/last-purchase"

    meta = ChatPresentationApiDeliveredMetadataService.build(
        action={"path": path},
        sanitized_data=envelope["data"],
        resolved_path=path,
        request_parameters={},
        presenter=use_case.presenter,
        extract_response_meta=lambda _data: envelope.get("meta"),
    )

    assert meta.get("presentationDecision")
    primary = meta.get("presentation") or meta.get("tablePresentation") or meta.get("textPresentation")
    assert isinstance(primary, dict)
    assert primary.get("type") in {"table", "markdown"}
    assert "table" in meta.get("availableFormats", [])


def test_api_delivered_metadata_for_safety_stock_detail_composite():
    use_case = _use_case()
    envelope = load_api_delpi_fixture_with_meta(
        "supplies_safety_stock_item_details_10020113.json"
    )
    path = "/supplies/safety-stock/items/10020113/details"

    meta = ChatPresentationApiDeliveredMetadataService.build(
        action={"path": path},
        sanitized_data=envelope["data"],
        resolved_path=path,
        request_parameters={"branch": "01"},
        presenter=use_case.presenter,
        extract_response_meta=lambda _data: envelope.get("meta"),
    )

    assert meta.get("presentationDecision")
    assert (meta.get("tablePresentations") or []) == []
    dashboard = meta.get("dashboardPresentation")
    assert isinstance(dashboard, dict)
    assert dashboard.get("type") == "dashboard"
    assert "table" in meta.get("availableFormats", [])
