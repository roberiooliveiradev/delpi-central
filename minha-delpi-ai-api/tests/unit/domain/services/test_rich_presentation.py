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


def test_chart_policy_groups_donut_slices():
    from app.domain.services.chat_presentation_chart_policy_service import (
        ChatPresentationChartPolicyService,
    )

    rows = [{"name": f"C{i}", "value": i} for i in range(1, 10)]
    capped = ChatPresentationChartPolicyService.apply(rows, "donut", label_key="name", value_key="value")

    assert len(capped) <= 6
    assert any(row.get("name") == "Outros" for row in capped)


def test_enrich_metadata_adds_insight_and_syncs_chart_type():
    from app.domain.services.chat_presentation_decision_service import (
        ChatPresentationDecisionService,
    )

    metadata = {
        "presentation": {
            "type": "chart",
            "title": "Vendas",
            "chartType": "bar",
            "data": [
                {"month": "jan/2026", "value": 10},
                {"month": "fev/2026", "value": 20},
                {"month": "mar/2026", "value": 15},
            ],
            "config": {"xAxis": "month", "yAxis": ["value"]},
        },
        "tablePresentation": {
            "type": "table",
            "title": "Tabela",
            "columns": [{"key": "month", "label": "Mês"}, {"key": "value", "label": "Valor"}],
            "rows": [
                {"month": "jan/2026", "value": 10},
                {"month": "fev/2026", "value": 20},
                {"month": "mar/2026", "value": 15},
            ],
        },
        "availableFormats": ["chart", "table"],
        "preferredFormat": "chart",
    }

    ChatPresentationDecisionService.enrich_metadata(metadata)

    decision = metadata["presentationDecision"]

    assert decision.get("insight")
    assert metadata["presentation"]["chartType"] in {"line", "multi_line"}


def test_decision_stack_layout_when_multiple_views():
    decision = ChatPresentationDecisionService._build(
        selected="text",
        fallback="table",
        reason="visão combinada",
        available_views=["text", "table", "tree", "chart"],
        rows=[{"campo": "Código", "valor": "1"}],
        intent="product",
    )

    assert decision["layoutMode"] == "stack"
    assert decision["visualOrder"][0] == "text"
    assert "table" in decision["visualOrder"]
    assert "tree" in decision["visualOrder"]


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
