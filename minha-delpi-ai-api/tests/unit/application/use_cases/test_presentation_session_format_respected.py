from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_primary_view_service import (
    ChatPresentationPrimaryViewService,
)
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


def test_stock_session_table_prefers_table_primary():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/products/{code}/stock"},
        sanitized_data={
            "stock": {
                "items": [
                    {
                        "branch": "01",
                        "warehouse": "01",
                        "current_quantity": 10,
                        "available_quantity": 8,
                        "committed_quantity": 2,
                    },
                    {
                        "branch": "02",
                        "warehouse": "01",
                        "current_quantity": 5,
                        "available_quantity": 5,
                        "committed_quantity": 0,
                    },
                ]
            }
        },
        resolved_path="/products/10070014/stock",
        request_parameters={"sessionResponseFormat": "table"},
    )

    decision = meta["presentationDecision"]

    assert meta["presentation"]["type"] == "table"
    assert decision["selected"] == "table"
    assert decision["layoutMode"] == "single"


def test_stock_session_tree_prefers_tree_primary():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/products/{code}/stock"},
        sanitized_data={
            "stock": {
                "items": [
                    {
                        "branch": "01",
                        "warehouse": "01",
                        "current_quantity": 10,
                        "available_quantity": 8,
                        "committed_quantity": 2,
                    },
                    {
                        "branch": "02",
                        "warehouse": "01",
                        "current_quantity": 5,
                        "available_quantity": 5,
                        "committed_quantity": 0,
                    },
                ]
            }
        },
        resolved_path="/products/10080022/stock",
        request_parameters={"sessionResponseFormat": "tree"},
    )

    decision = meta["presentationDecision"]

    assert meta["presentation"]["type"] == "tree"
    assert decision["selected"] == "tree"
    assert decision["layoutMode"] == "single"
    assert meta.get("explicitSessionFormat") == "tree"


def test_stock_default_text_uses_single_layout_without_explicit_session_format():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/products/{code}/stock"},
        sanitized_data={
            "stock": {
                "items": [
                    {
                        "branch": "01",
                        "warehouse": "01",
                        "current_quantity": 10,
                        "available_quantity": 8,
                        "committed_quantity": 2,
                    },
                    {
                        "branch": "02",
                        "warehouse": "01",
                        "current_quantity": 5,
                        "available_quantity": 5,
                        "committed_quantity": 0,
                    },
                ]
            }
        },
        resolved_path="/products/10080022/stock",
        request_parameters={"userMessage": "estoque do produto 10080022"},
    )

    decision = meta["presentationDecision"]

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "single"
    assert meta.get("chartPresentation") is None
    assert meta.get("textPresentation", {}).get("markdown")


def test_stock_session_chart_prefers_chart_primary():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/products/{code}/stock"},
        sanitized_data={
            "stock": {
                "items": [
                    {
                        "branch": "01",
                        "warehouse": "01",
                        "current_quantity": 10,
                        "available_quantity": 8,
                        "committed_quantity": 2,
                    },
                    {
                        "branch": "02",
                        "warehouse": "01",
                        "current_quantity": 5,
                        "available_quantity": 5,
                        "committed_quantity": 0,
                    },
                ]
            }
        },
        resolved_path="/products/10070014/stock",
        request_parameters={"sessionResponseFormat": "chart"},
    )

    decision = meta["presentationDecision"]

    assert meta["presentation"]["type"] == "chart"
    assert decision["selected"] == "chart"
    assert decision["layoutMode"] == "single"


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
    assert decision["layoutMode"] == "single"


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

        assert meta["presentationDecision"]["layoutMode"] == "single"


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
    assert isinstance(meta.get("treePresentation"), dict)
    assert "**Composição**" in markdown
    assert "50230130" in markdown
    assert "└── 50230130" in markdown or "├── 50230130" in markdown
    assert isinstance(meta.get("treePresentation"), dict)
