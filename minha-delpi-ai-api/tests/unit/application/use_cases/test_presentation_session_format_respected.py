from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_primary_view_service import (
    ChatPresentationPrimaryViewService,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta
from tests.fixtures.chat_presentation_regression_cases import (
    PRESENTATION_SESSION_FORMAT_CASES,
)


def _use_case():
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def _stock_metadata(
    *,
    session_format: str | None = None,
    user_message: str | None = None,
    resolved_path: str = "/products/90269001/stock",
) -> dict:
    params: dict = {}

    if session_format:
        params["sessionResponseFormat"] = session_format

    if user_message:
        params["userMessage"] = user_message

    return _use_case()._build_presentation_metadata(
        action={"path": "/products/{code}/stock"},
        sanitized_data=load_api_delpi_fixture_with_meta("product_stock_90269001.json"),
        resolved_path=resolved_path,
        request_parameters=params,
    )


def _render_plan_kinds(metadata: dict) -> set[str]:
    render_plan = metadata.get("renderPlan")

    if not isinstance(render_plan, dict):
        return set()

    return {
        str(item.get("kind") or "").strip().lower()
        for item in render_plan.get("segments") or []
        if isinstance(item, dict)
    }


def _assert_selected_visual(metadata: dict, expected: str) -> None:
    decision = metadata["presentationDecision"]
    assert decision["selected"] == expected

    presentation_type = str((metadata.get("presentation") or {}).get("type") or "").lower()
    slot = metadata.get(f"{expected}Presentation") or {}
    slot_type = str(slot.get("type") or "").lower()
    render_kinds = _render_plan_kinds(metadata)

    if expected in {"table", "chart", "tree", "dashboard", "kpi"}:
        assert (
            presentation_type == expected
            or slot_type == expected
            or expected in render_kinds
        )

    _assert_explicit_session_layout(decision, metadata.get("explicitSessionFormat"))


def test_apply_session_preference_promotes_table_over_chart_primary():
    table = {"type": "table", "title": "Estoque", "rows": []}
    chart = {"type": "chart", "title": "Estoque", "data": []}
    metadata = {
        "presentation": chart,
        "tablePresentation": table,
        "availableFormats": ["table", "chart"],
    }

    applied = ChatPresentationPrimaryViewService.apply_session_preference(
        metadata,
        "table",
    )

    assert applied is True
    assert metadata["presentation"] == table
    assert metadata["chartPresentation"] == chart
    assert metadata["tablePresentation"] is None
    assert metadata["explicitSessionFormat"] == "table"


def test_apply_session_preference_promotes_tree_over_table_primary():
    tree = {"type": "tree", "title": "Estrutura", "nodes": []}
    table = {"type": "table", "title": "Componentes", "rows": []}
    metadata = {
        "presentation": tree,
        "tablePresentation": table,
        "availableFormats": ["tree", "table"],
    }

    ChatPresentationPrimaryViewService.apply_session_preference(metadata, "table")

    assert metadata["presentation"] == table
    assert metadata["treePresentation"] == tree


def test_finalize_decision_alignment_preserves_humanized_kpi_narrative():
    markdown = (
        "### Taxa de Conversão de Vendas\n\n"
        "<!-- section:scope -->\n\n"
        "Taxa de Conversão de Vendas: indicador com 3 métrica(s) disponível(is)."
    )
    metadata = {
        "presentationDecision": {"selected": "kpi"},
        "stackPresentationPlan": {"humanizedSections": True},
        "textPresentation": {"type": "markdown", "markdown": markdown},
        "kpiPresentation": {"type": "kpi", "title": "Taxa de Conversão de Vendas"},
    }

    ChatPresentationPrimaryViewService.finalize_decision_alignment(
        metadata,
        kpi_presentation=metadata["kpiPresentation"],
    )

    assert "<!-- section:scope -->" in metadata["textPresentation"]["markdown"]
    assert "indicador com 3 métrica" in metadata["textPresentation"]["markdown"]


def test_finalize_decision_alignment_single_layout_for_explicit_table():
    metadata = {
        "explicitSessionFormat": "table",
        "presentationDecision": {"selected": "table", "layoutMode": "stack"},
        "presentation": {"type": "chart", "data": []},
        "tablePresentation": {"type": "table", "rows": []},
    }

    ChatPresentationPrimaryViewService.finalize_decision_alignment(metadata)

    assert metadata["presentation"]["type"] == "table"
    assert metadata["presentationDecision"]["layoutMode"] == "single"
    assert metadata["presentationDecision"]["visualOrder"] == ["table"]


def test_finalize_decision_alignment_preserves_explicit_text_with_stack():
    metadata = {
        "explicitSessionFormat": "text",
        "preferredFormat": "text",
        "availableFormats": ["text", "table", "dashboard"],
        "presentationDecision": {
            "selected": "dashboard",
            "layoutMode": "stack",
            "visualOrder": ["text", "table", "dashboard"],
            "availableViews": ["text", "table", "dashboard"],
        },
        "textPresentation": {"type": "markdown", "markdown": "### Resumo\n\nCorpo."},
        "dashboardPresentation": {"type": "dashboard", "panels": []},
    }

    ChatPresentationPrimaryViewService.finalize_decision_alignment(metadata)

    assert metadata.get("explicitSessionFormat") == "text"
    assert metadata["presentationDecision"]["layoutMode"] == "stack"
    assert metadata["presentationDecision"]["selected"] == "dashboard"


def test_stock_session_table_prefers_table_primary():
    meta = _stock_metadata(session_format="table")

    _assert_selected_visual(meta, "table")
    assert meta.get("explicitSessionFormat") == "table"


def _assert_explicit_session_layout(
    decision: dict,
    explicit_format: str | None = None,
) -> None:
    explicit = str(explicit_format or "").strip().lower()
    native_single = {"table", "tree", "chart", "dashboard", "kpi", "canvas"}

    if explicit in native_single:
        assert decision["layoutMode"] == "single"
        return

    if explicit in {"text", "topics"}:
        views = decision.get("availableViews") or []

        if len(views) >= 2:
            assert decision["layoutMode"] == "stack"
        else:
            assert decision["layoutMode"] == "single"
        return

    views = decision.get("availableViews") or []

    if len(views) >= 2:
        assert decision["layoutMode"] == "stack"
    else:
        assert decision["layoutMode"] == "single"


def test_stock_session_tree_prefers_tree_primary():
    meta = _stock_metadata(session_format="tree", resolved_path="/products/10080022/stock")
    decision = meta["presentationDecision"]

    assert decision["selected"] == "tree"
    assert meta.get("explicitSessionFormat") == "tree"
    assert decision["layoutMode"] == "single"


def test_stock_default_text_uses_single_layout_without_explicit_session_format():
    meta = _stock_metadata(user_message="estoque do produto 10080022")
    decision = meta["presentationDecision"]

    assert decision["selected"] in {"text", "table"}
    assert decision["layoutMode"] == "single"
    assert (
        (meta.get("textPresentation") or {}).get("markdown")
        or (meta.get("dataAnswer") or {}).get("summary")
        or (meta.get("tablePresentation") or {}).get("rows")
        or (meta.get("presentation") or {}).get("type") in {"table", "markdown"}
    )


def test_stock_session_chart_prefers_chart_primary():
    meta = _stock_metadata(session_format="chart")

    _assert_selected_visual(meta, "chart")


def test_parents_session_tree_keeps_tree_primary():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/products/{code}/parents"},
        sanitized_data={
            "product": {
                "code": "10070014",
                "description": "CABO",
                "type": "MP",
                "unit": "MT",
            },
            "parents": [
                {
                    "code": "P1",
                    "description": "CHICOTE 1",
                    "type": "PA",
                    "unit": "UN",
                    "quantity": 1,
                },
            ],
        },
        resolved_path="/products/10070014/parents",
        request_parameters={"sessionResponseFormat": "tree"},
    )

    decision = meta["presentationDecision"]

    assert meta["presentation"]["type"] == "tree"
    assert decision["selected"] == "tree"
    _assert_explicit_session_layout(decision, meta.get("explicitSessionFormat"))


def test_commercial_kpi_session_canvas_keeps_canvas_preference():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/commercial/closing-rate"},
        sanitized_data={
            "value": 82.5,
            "target": 90.0,
            "previous": 80.0,
            "unit": "%",
        },
        resolved_path="/commercial/closing-rate",
        request_parameters={"sessionResponseFormat": "canvas"},
    )

    decision = meta["presentationDecision"]

    assert meta["preferredFormat"] == "canvas"
    assert "canvas" in meta["availableFormats"]
    assert decision["selected"] == "canvas"
    assert decision["layoutMode"] == "single"


def test_session_format_regression_cases_table_and_tree():
    use_case = _use_case()
    structure_payload = {
        "root": {
            "code": "90269001",
            "description": "ITEM",
            "type": "PA",
            "unit": "UN",
            "quantity": 1,
        },
        "items": [
            {
                "code": "C1",
                "description": "COMP",
                "type": "PI",
                "unit": "UN",
                "quantity": 1.0,
                "components": [
                    {
                        "code": "C2",
                        "description": "SUB",
                        "type": "MP",
                        "unit": "UN",
                        "quantity": 2.0,
                    }
                ],
            }
        ],
        "total": 1,
    }

    for case in PRESENTATION_SESSION_FORMAT_CASES:
        if case["id"] not in {"structure_prefers_table", "structure_prefers_tree"}:
            continue

        meta = use_case._build_presentation_metadata(
            action={"path": "/products/{code}/structure"},
            sanitized_data=structure_payload,
            resolved_path=case["path"],
            request_parameters={"sessionResponseFormat": case["session_format"]},
        )

        assert meta["presentationDecision"]["selected"] == case["expected_selected"]

        if case["expected_primary_type"]:
            assert meta["presentation"]["type"] == case["expected_primary_type"]

        _assert_explicit_session_layout(
            meta["presentationDecision"],
            meta.get("explicitSessionFormat"),
        )


def test_structure_text_mode_embeds_tree_outline_markdown():
    use_case = _use_case()
    structure_payload = {
        "root": {
            "code": "90260149",
            "description": "CHICOTE EPR SINGELO 235MM",
            "type": "PA",
            "unit": "MI",
            "quantity": 1,
        },
        "items": [
            {
                "code": "50230130",
                "description": "CB16AZUL",
                "type": "PI",
                "unit": "MI",
                "quantity": 1.0,
                "components": [
                    {
                        "code": "10080109",
                        "description": "TERM. FASTON",
                        "type": "MP",
                        "unit": "PC",
                        "quantity": 1.0,
                    }
                ],
            }
        ],
        "total": 1,
    }

    meta = use_case._build_presentation_metadata(
        action={"path": "/products/{code}/structure"},
        sanitized_data=structure_payload,
        resolved_path="/products/90260149/structure",
        request_parameters={"sessionResponseFormat": "text"},
    )

    from app.domain.services.chat_presentation_tree_markdown_service import (
        ChatPresentationTreeMarkdownService,
    )

    markdown = str(meta["textPresentation"]["markdown"])

    assert meta["presentationDecision"]["selected"] == "text"
    assert meta["presentationDecision"]["layoutMode"] == "single"
    assert (
        "|" in markdown
        or "└──" in markdown
        or "├──" in markdown
        or "```text" in markdown
        or meta.get("treePresentation") is not None
    )
    assert meta.get("treePresentation") is not None or "└──" in markdown or "├──" in markdown
