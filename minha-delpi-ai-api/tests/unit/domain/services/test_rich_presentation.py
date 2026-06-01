import pytest

from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)
from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)
from tests.fixtures.rich_presentation_cases import RICH_PRESENTATION_CASES


@pytest.mark.parametrize("case", RICH_PRESENTATION_CASES, ids=lambda item: item["id"])
def test_presentation_decision_regression(case: dict):
    decision = ChatPresentationDecisionService.decide(
        rows=case.get("rows"),
        user_message=case.get("user_message"),
        user_preference=case.get("user_preference"),
    )

    assert decision["selected"] == case["expected_selected"]
    assert decision.get("fallback")
    assert decision.get("reason")
    assert isinstance(decision.get("availableViews"), list)
    assert decision.get("dataShape") is not None


def test_data_shape_analyzer_temporal():
    shape = ChatPresentationDataShapeAnalyzer.analyze(
        rows=[
            {"period": "2026-01", "value": 10},
            {"period": "2026-02", "value": 12},
        ],
    )

    assert shape["hasDate"] is True
    assert shape["hasNumeric"] is True
    assert shape["recommended"] == "line_chart"


def test_enrich_metadata_attaches_presentation_decision():
    metadata = {
        "presentation": {
            "type": "table",
            "title": "Produtos",
            "columns": [{"key": "code", "label": "Código"}],
            "rows": [{"code": "10080001", "value": 10}],
        },
        "availableFormats": ["table"],
        "preferredFormat": "table",
    }

    ChatPresentationDecisionService.enrich_metadata(metadata)

    assert metadata.get("presentationDecision")
    assert metadata["presentationDecision"]["selected"] == "table"
