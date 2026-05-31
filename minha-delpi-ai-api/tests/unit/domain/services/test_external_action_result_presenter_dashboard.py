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
