from app.domain.services.chat_presentation_kpi_assembly_service import (
    ChatPresentationKpiAssemblyService,
)


def test_metric_card_infers_quantity_for_factory_counters():
    card = ChatPresentationKpiAssemblyService.metric_card(
        label="Componentes na estrutura",
        value=1,
        key="total_components",
        color="#6366f1",
    )

    assert card["dataType"] == "quantity"


def test_metric_card_infers_currency_for_sale_price():
    card = ChatPresentationKpiAssemblyService.metric_card(
        label="Menor preço de venda",
        value=992.54,
        unit="R$",
        key="primary_sale_price",
        color="#10b981",
    )

    assert card["dataType"] == "currency"


def test_metric_card_infers_quantity_for_suffix_units():
    card = ChatPresentationKpiAssemblyService.metric_card(
        label="Ordens de produção",
        value=32,
        unit="OP",
        key="production_orders",
        color="#0ea5e9",
    )

    assert card["dataType"] == "quantity"


def test_normalize_metadata_adds_data_type_to_dashboard_kpi_panels():
    metadata = {
        "dashboardPresentation": {
            "type": "dashboard",
            "panels": [
                {
                    "id": "summary",
                    "presentation": {
                        "type": "kpi",
                        "title": "Resumo",
                        "cards": [
                            {
                                "label": "Componentes na estrutura",
                                "value": 1,
                                "key": "total_components",
                                "color": "#6366f1",
                            }
                        ],
                    },
                }
            ],
        }
    }

    ChatPresentationKpiAssemblyService.normalize_metadata(metadata)

    card = metadata["dashboardPresentation"]["panels"][0]["presentation"]["cards"][0]

    assert card["dataType"] == "quantity"


def test_build_normalizes_cards_without_data_type():
    presentation = ChatPresentationKpiAssemblyService.build(
        title="Indicadores",
        cards=[
            {
                "label": "Total de componentes",
                "value": 3,
                "key": "total_components",
            }
        ],
        min_cards=1,
    )

    assert presentation is not None
    assert presentation["cards"][0]["dataType"] == "quantity"
