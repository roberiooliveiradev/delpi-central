from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def test_analyser_builds_composition_chart_when_multiple_types():
    presenter = ExternalActionResultPresenter()
    payload = _analyser_payload_with_guide_and_inspection()
    payload["structure"]["items"][0]["components"] = [
        {"code": "50212194", "description": "CB20PRET", "type": "PI", "quantity": 2},
        {"code": "99990001", "description": "TERMINAL", "type": "MP", "quantity": 1},
    ]

    chart = presenter.build_chart_presentation(
        payload,
        path="/products/90260140/analyser",
    )

    assert chart is not None
    assert chart.get("chartType") == "donut"
    assert "PI" in " ".join(chart.get("labels") or [])
    assert "MP" in " ".join(chart.get("labels") or [])
