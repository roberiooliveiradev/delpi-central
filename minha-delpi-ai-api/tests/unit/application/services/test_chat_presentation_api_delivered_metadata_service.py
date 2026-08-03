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


def test_api_delivered_metadata_for_production_otd_nested_orders():
    use_case = _use_case()
    envelope = load_api_delpi_fixture_with_meta("production_otd_late_summary.json")
    path = "/production/otd"
    data = envelope["data"]

    meta = ChatPresentationApiDeliveredMetadataService.build(
        action={"path": path},
        sanitized_data=data,
        resolved_path=path,
        request_parameters={"status": "late", "userMessage": "ops em atraso"},
        presenter=use_case.presenter,
        extract_response_meta=lambda _data: envelope.get("meta"),
    )

    decision = meta.get("presentationDecision") or {}
    selected = str(decision.get("selected") or "").strip().lower()
    assert selected in {"kpi", "table", "dashboard"}
    assert "kpi" not in (decision.get("suppressedKinds") or [])

    data_shape = decision.get("dataShape") or meta.get("dataShape") or {}
    assert int(data_shape.get("rows") or 0) > 0

    table = meta.get("tablePresentation")
    if not isinstance(table, dict):
        primary = meta.get("presentation")
        table = primary if isinstance(primary, dict) and primary.get("type") == "table" else None

    assert isinstance(table, dict)
    rows = table.get("rows")
    assert isinstance(rows, list) and len(rows) >= 2

    column_keys = [str(col.get("key") or "") for col in (table.get("columns") or [])]
    for expected in (
        "production_order",
        "product_code",
        "product_description",
        "due_date",
        "finish_date",
        "days_diff",
        "status",
        "branch",
    ):
        assert expected in column_keys, f"coluna OTD ausente na tabela: {expected}"

    assert rows[0].get("product_description")
    assert rows[0].get("due_date")
    assert "days_diff" in rows[0]

    data_answer = meta.get("dataAnswer") or {}
    summary = data_answer.get("summary") if isinstance(data_answer.get("summary"), dict) else {}
    facts = data_answer.get("facts") or []
    fact_text = " ".join(
        [
            str(summary.get("answer") or ""),
            str(summary.get("meaning") or ""),
            *[
                str(item.get("text") if isinstance(item, dict) else item)
                for item in facts
            ],
        ]
    )
    assert "atraso" in fact_text.casefold() or "otd" in fact_text.casefold()
    assert "days_diff" not in fact_text.casefold()
