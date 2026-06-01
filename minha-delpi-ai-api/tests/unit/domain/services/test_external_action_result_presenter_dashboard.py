from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def test_build_dashboard_presentation_for_lmp_payload():
    presenter = ExternalActionResultPresenter()
    payload = {
        "summary": {
            "total_items": 5,
            "percent_dentro_prazo": 80.0,
            "avg_lead_time": 3.5,
        },
        "charts": {
            "levelData": [
                {"name": "Nível 1", "value": 2},
                {"name": "Nível 2", "value": 3},
            ],
            "leadByLevel": [
                {"nivel": "Nível 1", "valor": 2.5},
                {"nivel": "Nível 2", "valor": 4.1},
            ],
        },
        "items": [
            {
                "sale_number": "OV100",
                "branch": "01",
                "listing_kind": "LMP",
                "status": "No prazo",
                "sale_description": "Teste",
            }
        ],
        "total": 1,
    }

    dashboard = presenter.build_dashboard_presentation(
        payload,
        path="/engineering/lmps/dashboard",
    )

    assert dashboard is not None
    assert dashboard["type"] == "dashboard"
    assert any(
        panel["presentation"]["type"] == "chart"
        for panel in dashboard["panels"]
    )
    items_panel = next(panel for panel in dashboard["panels"] if panel["id"] == "items")
    assert items_panel["presentation"]["type"] == "table"
    assert items_panel.get("chartPresentation", {}).get("type") == "chart"


def test_build_dashboard_items_panel_includes_chart_for_efficiency_rows():
    presenter = ExternalActionResultPresenter()
    payload = {
        "summary": {
            "weighted_efficiency_pct": 98.5,
            "total_mod_result": -2400,
            "appointment_count": 190,
        },
        "items": [
            {
                "filial": "01",
                "op": "OP1",
                "produto": "10080077",
                "tempo_real_horas": 1.5,
                "eficiencia_percentual": 120.5,
            },
            {
                "filial": "02",
                "op": "OP2",
                "produto": "10080078",
                "tempo_real_horas": 2.0,
                "eficiencia_percentual": 88.2,
            },
        ],
        "total": 2,
    }

    dashboard = presenter.build_dashboard_presentation(
        payload,
        path="/production/eficiencia-fabril/dashboard",
    )

    assert dashboard is not None
    items_panel = next(panel for panel in dashboard["panels"] if panel["id"] == "items")
    assert items_panel["presentation"]["type"] == "table"
    assert items_panel.get("chartPresentation", {}).get("type") == "chart"
    kpi_labels = {
        card["label"]
        for panel in dashboard["panels"]
        if panel["presentation"]["type"] == "kpi"
        for card in panel["presentation"]["cards"]
    }
    assert "Eficiência ponderada (%)" in kpi_labels
    assert "Resultado MOD total" in kpi_labels
    assert "Qtd. de apontamentos" in kpi_labels
    table_columns = {
        column["label"] for column in items_panel["presentation"]["columns"]
    }
    assert "Eficiência (%)" in table_columns
    assert "Tempo real (h)" in table_columns
