from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_product_detail_title_from_presenter_content():
    presenter = ExternalActionResultPresenter()

    title = presenter._product_detail_title(
        "90260123",
        {"purchases": [{"qty": 1}]},
    )

    assert title == "Compras do produto 90260123"


def test_generic_kpi_cards_use_presenter_palette():
    presenter = ExternalActionResultPresenter()

    cards = presenter._build_generic_kpi_cards(
        {
            "weighted_efficiency_pct": 98.5,
            "appointment_count": 120,
            "ignored": "x",
        },
        path="/production/eficiencia-fabril",
    )

    assert cards is not None
    assert len(cards) == 2
    assert cards[0]["unit"] == "%"
    assert cards[0]["color"] == "#0ea5e9"


def test_product_overview_narrative_uses_content():
    presenter = ExternalActionResultPresenter()

    lines = presenter._build_product_overview_narrative_lines(
        {
            "code": "10080001",
            "description": "TERM. BANDEIRA",
            "type": "MP",
            "unit": "PC",
            "group_code": "1008",
            "active": "S",
            "standard_cost": 0.03,
        },
        {},
    )

    assert any("TERM. BANDEIRA" in line for line in lines)
    assert any("Custo padrão vigente" in line for line in lines)
