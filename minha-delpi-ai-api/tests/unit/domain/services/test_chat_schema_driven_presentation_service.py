from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_schema_driven_presentation_service import (
    ChatSchemaDrivenPresentationService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def _use_case():
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_should_apply_for_kpi_entity_and_generic_path():
    assert ChatSchemaDrivenPresentationService.should_apply(
        path="/supplies/cpv",
        entity="supplies_cpv",
    )
    assert ChatSchemaDrivenPresentationService.should_apply(
        path="/commercial/closing-rate",
        entity="sales_conversion_rate",
    )
    assert not ChatSchemaDrivenPresentationService.should_apply(
        path="/products/90260144/stock",
        entity="product_stock",
    )


def test_extract_tabular_rows_from_series_and_items():
    series_rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {
            "series": [
                {"period": "jan/2026", "value": 12.5},
                {"period": "fev/2026", "value": 13.1},
            ]
        }
    )
    items_rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {"items": [{"branch": "01", "value": 100}]}
    )

    assert len(series_rows) == 2
    assert items_rows[0]["branch"] == "01"


def test_build_kpi_from_scalar_metrics():
    presenter = ExternalActionResultPresenter()
    root = {
        "value": 82.5,
        "target": 90.0,
        "previous": 80.0,
        "unit": "%",
    }

    kpi = ChatSchemaDrivenPresentationService.build_kpi(
        presenter,
        root,
        path="/commercial/closing-rate",
        entity="sales_conversion_rate",
    )

    assert isinstance(kpi, dict)
    assert kpi["type"] == "kpi"
    assert kpi["cards"]


def test_build_text_for_time_series():
    presenter = ExternalActionResultPresenter()
    text = ChatSchemaDrivenPresentationService.build_text(
        presenter,
        {
            "series": [
                {"period": "jan/2026", "value": 10},
                {"period": "fev/2026", "value": 12},
            ]
        },
        path="/quality/nonconformities/series",
        entity="nonconformity_series",
    )

    assert isinstance(text, dict)
    assert text["type"] == "markdown"
    assert "série temporal" in text["markdown"].lower()


def test_schema_driven_metadata_for_commercial_kpi():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/commercial/closing-rate"},
        sanitized_data={
            "value": 82.5,
            "target": 90.0,
            "previous": 80.0,
            "unit": "%",
        },
        resolved_path="/commercial/closing-rate",
        request_parameters={},
    )

    assert meta["presentation"]["type"] == "kpi"
    assert "text" in meta["availableFormats"]
    assert meta["textPresentation"]["type"] == "markdown"


def test_schema_driven_metadata_builds_table_for_generic_items():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/commercial/proposals"},
        sanitized_data={
            "items": [
                {"proposal_number": "100", "customer_name": "Cliente A", "amount": 1500},
                {"proposal_number": "101", "customer_name": "Cliente B", "amount": 2300},
            ],
            "total": 2,
        },
        resolved_path="/commercial/proposals",
        request_parameters={},
    )

    assert "table" in meta["availableFormats"]
    table = meta.get("tablePresentation") or meta.get("presentation")
    assert isinstance(table, dict)
    assert table["type"] == "table"
    assert len(table["rows"]) == 2
