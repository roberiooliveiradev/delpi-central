from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_field_normalization_service import (
    ChatPresentationFieldNormalizationService,
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

    chart = meta.get("chartPresentation") or meta.get("presentation")

    assert chart is not None
    assert chart["type"] == "chart"
    assert chart["config"]["fieldLabels"]["ordered_quantity"] == "Qtd. pedida"


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
