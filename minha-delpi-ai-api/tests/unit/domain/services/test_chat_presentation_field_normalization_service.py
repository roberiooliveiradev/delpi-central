from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_field_normalization_service import (
    ChatPresentationFieldNormalizationService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)
def test_normalize_chart_adds_field_labels_and_formats():
    presentation = {
        "type": "chart",
        "title": "Compras",
        "chartType": "line",
        "data": [
            {"issue_date": "20260317", "ordered_quantity": 100, "unit_price": 12.5},
            {"issue_date": "20231117", "ordered_quantity": 80, "unit_price": 11.0},
        ],
        "config": {
            "xAxis": "issue_date",
            "yAxis": ["ordered_quantity", "unit_price"],
            "legend": True,
        },
    }

    normalized = ChatPresentationFieldNormalizationService.normalize_presentation(
        presentation,
        path="/products/10070014/purchases",
    )

    field_labels = normalized["config"]["fieldLabels"]

    assert field_labels["ordered_quantity"] == "Qtd. pedida"
    assert field_labels["unit_price"] == "Preço unitário"
    assert field_labels["issue_date"] == "Data emissão"
    assert normalized["config"]["fieldFormats"]["issue_date"] == "date"


def test_normalize_table_applies_purchase_profile():
    presentation = {
        "type": "table",
        "title": "Compras",
        "columns": [],
        "rows": [
            {
                "order_number": "000123",
                "issue_date": "20260317",
                "ordered_quantity": 10,
                "unit_price": 5.5,
                "supplier_name": "Fornecedor A",
            }
        ],
    }

    normalized = ChatPresentationFieldNormalizationService.normalize_presentation(
        presentation,
        path="/products/10070014/purchases",
    )

    column_keys = [column["key"] for column in normalized["columns"]]

    assert "order_number" in column_keys
    assert "ordered_quantity" in column_keys
    assert any(column["label"] == "Qtd. pedida" for column in normalized["columns"])
    assert any(column.get("dataType") == "date" for column in normalized["columns"] if column["key"] == "issue_date")


def test_normalize_table_preferred_columns_are_order_hints_not_allowlist():
    """Causa raiz transversal: preferredColumns não pode truncar colunas do payload."""
    presentation = {
        "type": "table",
        "title": "Produção",
        "columns": [
            {"key": "production_order", "label": "OP"},
            {"key": "product_code", "label": "Produto"},
            {"key": "branch", "label": "Filial"},
            {"key": "status", "label": "Status"},
        ],
        "rows": [
            {
                "branch": "01",
                "production_order": "000001001",
                "product_code": "90260144",
                "product_description": "TERMINAL",
                "scheduled_quantity": 10,
                "extra_metric": 42,
                "status": "open",
            }
        ],
    }

    normalized = ChatPresentationFieldNormalizationService.normalize_presentation(
        presentation,
        path="/production/some-route",
    )

    column_keys = [column["key"] for column in normalized["columns"]]
    for expected in (
        "production_order",
        "product_code",
        "product_description",
        "scheduled_quantity",
        "extra_metric",
        "status",
        "branch",
    ):
        assert expected in column_keys, f"coluna ausente após normalize: {expected}"

    assert normalized["rows"][0].get("product_description") == "TERMINAL"
    assert normalized["rows"][0].get("extra_metric") == 42
    # preferred do perfil production deve vir antes das extras
    assert column_keys.index("production_order") < column_keys.index("extra_metric")


def test_order_keys_with_preferred_hints_never_drops_present_keys():
    labels = ExternalActionColumnLabelService()
    ordered = labels.order_keys_with_preferred_hints(
        ["zeta", "production_order", "alpha", "product_code"],
        profile_name="production",
    )
    assert ordered[:2] == ["production_order", "product_code"]
    assert "zeta" in ordered and "alpha" in ordered
    assert len(ordered) == 4


def test_presentation_metadata_includes_normalized_chart_labels():
    use_case = ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )
    meta = use_case._build_presentation_metadata(
        action={"path": "/products/{code}/purchases"},
        sanitized_data={
            "items": [
                {
                    "order_number": "000123",
                    "issue_date": "20260317",
                    "ordered_quantity": 10,
                    "unit_price": 5.5,
                    "supplier_name": "Fornecedor A",
                },
                {
                    "order_number": "000124",
                    "issue_date": "20231117",
                    "ordered_quantity": 20,
                    "unit_price": 6.0,
                    "supplier_name": "Fornecedor B",
                },
            ]
        },
        resolved_path="/products/10070014/purchases",
        request_parameters={},
    )

    table = meta.get("tablePresentation") or meta.get("presentation")

    assert table is not None
    assert table["type"] == "table"
    assert any(
        column.get("label") == "Qtd. pedida"
        for column in (table.get("columns") or [])
        if column.get("key") == "ordered_quantity"
    )


def test_normalize_kpi_presentation_adds_data_type_to_cards():
    presentation = {
        "type": "kpi",
        "title": "Status fabril",
        "cards": [
            {
                "label": "Componentes na estrutura",
                "value": 1,
                "key": "total_components",
                "color": "#6366f1",
            }
        ],
    }

    normalized = ChatPresentationFieldNormalizationService.normalize_presentation(
        presentation,
        path="/products/90263749/factory-status",
    )

    assert normalized["cards"][0]["dataType"] == "quantity"


def test_normalize_metadata_normalizes_kpi_and_dashboard_panels():
    metadata = {
        "kpiPresentation": {
            "type": "kpi",
            "title": "KPI",
            "cards": [
                {
                    "label": "Ordens de produção",
                    "value": 32,
                    "key": "production_orders",
                    "unit": "OP",
                }
            ],
        },
        "dashboardPresentation": {
            "type": "dashboard",
            "panels": [
                {
                    "id": "kpi",
                    "presentation": {
                        "type": "kpi",
                        "cards": [
                            {
                                "label": "Menor preço de venda",
                                "value": 992.54,
                                "unit": "R$",
                                "key": "primary_sale_price",
                            }
                        ],
                    },
                }
            ],
        },
    }

    ChatPresentationFieldNormalizationService.normalize_metadata(metadata)

    assert metadata["kpiPresentation"]["cards"][0]["dataType"] == "quantity"
    assert (
        metadata["dashboardPresentation"]["panels"][0]["presentation"]["cards"][0]["dataType"]
        == "currency"
    )
