import pytest

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_schema_driven_presentation_service import (
    ChatSchemaDrivenPresentationService,
    SchemaPresentationBundle,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.chat_presentation_regression_cases import (
    SCHEMA_DRIVEN_SAMPLE_PAYLOADS,
)


def _use_case():
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_should_apply_for_kpi_profile_without_entity():
    assert ChatSchemaDrivenPresentationService.should_apply(
        path="/quality/audit-5s/summary",
        entity=None,
    )
    assert ChatSchemaDrivenPresentationService.should_apply(
        path="/supplies/cpv",
        entity=None,
    )
    assert not ChatSchemaDrivenPresentationService.should_apply(
        path="/products/90260144/guide",
        entity="product_guide",
    )


def test_resolve_primary_prefers_chart_for_kpi_series_profile():
    bundle = SchemaPresentationBundle(
        table={"type": "table", "rows": [{"period": "jan", "value": 1}]},
        chart={"type": "chart", "chartType": "line", "data": []},
    )

    primary = ChatSchemaDrivenPresentationService.resolve_primary_from_bundle(
        bundle,
        path="/quality/nonconformities/series",
        entity="nonconformity_series",
    )

    assert primary["type"] == "chart"


def test_build_tree_from_generic_children():
    presenter = ExternalActionResultPresenter()
    tree = ChatSchemaDrivenPresentationService.build_tree(
        presenter,
        {
            "code": "ROOT",
            "description": "Raiz",
            "children": [
                {"code": "A", "description": "Filho A"},
                {"code": "B", "description": "Filho B"},
            ],
        },
        path="/engineering/transforma-mais/processes",
    )

    assert isinstance(tree, dict)
    assert tree["type"] == "tree"
    assert tree["root"]["children"]


@pytest.mark.parametrize("case", SCHEMA_DRIVEN_SAMPLE_PAYLOADS, ids=lambda item: item["id"])
def test_schema_driven_metadata_pipeline(case):
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": case["path"]},
        sanitized_data=case["data"],
        resolved_path=str(case["path"]),
        request_parameters={},
    )

    expected_primary = case.get("expected_primary_type")
    slot_by_type = {
        "kpi": "kpiPresentation",
        "chart": "chartPresentation",
        "table": "tablePresentation",
        "tree": "treePresentation",
        "dashboard": "dashboardPresentation",
    }

    if expected_primary:
        presentation = meta.get("presentation") or {}

        if presentation.get("type") != expected_primary:
            slot_key = slot_by_type.get(str(expected_primary))
            slot_presentation = meta.get(slot_key) if slot_key else None
            presentation = slot_presentation if isinstance(slot_presentation, dict) else {}

        assert presentation.get("type") == expected_primary

        if str(meta.get("textPresentation", {}).get("markdown") or "").strip():
            decision = meta.get("presentationDecision") or {}
            assert decision.get("selected") == "text"
            assert decision.get("layoutMode") == "stack"

    expected_rows = case.get("expected_table_rows")

    if expected_rows:
        table = meta.get("tablePresentation")

        if not isinstance(table, dict) or table.get("type") != "table":
            presentation = meta.get("presentation")

            if isinstance(presentation, dict) and presentation.get("type") == "table":
                table = presentation

        assert isinstance(table, dict)
        assert table.get("type") == "table"
        assert len(table.get("rows") or []) == expected_rows

    if case.get("expected_chart"):
        assert meta.get("chartPresentation") or (
            meta.get("presentation", {}).get("type") == "chart"
        )

    if case.get("expected_tree"):
        assert meta.get("treePresentation") or meta.get("presentation", {}).get("type") == "tree"

    if expected_primary == "kpi" or expected_rows:
        text = meta.get("textPresentation", {})
        assert text.get("type") == "markdown"
        assert "<!-- section:scope -->" in str(text.get("markdown") or "")

    stack_plan = meta.get("stackPresentationPlan") or {}

    if case.get("expected_primary_type") == "kpi" or case.get("expected_table_rows"):
        assert stack_plan.get("humanizedSections") is True
