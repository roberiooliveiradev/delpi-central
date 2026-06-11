from app.application.services.chat_tool_context_format_service import (
    ChatToolContextFormatService,
)


def test_apply_format_override_table_aligns_without_stale_use_case_helper():
    """Regressão: override Tabela não pode chamar método removido do use case."""
    service = ChatToolContextFormatService()
    metadata = {
        "ok": True,
        "path": "/production/schedule/today",
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "single",
            "availableViews": ["text", "table"],
        },
        "presentation": {"type": "table", "title": "Produtos programados", "rows": [{"product_code": "90269001"}]},
        "textPresentation": {"type": "markdown", "markdown": "### Programação"},
        "kpiPresentation": {"type": "kpi", "title": "KPI", "cards": []},
    }
    tool_calls = [{"name": "execute_external_action", "metadata": metadata}]
    payload = {"items": [{"product_code": "90269001", "description": "ITEM"}]}

    service.apply_format_override(tool_calls, "table", payload)

    meta = tool_calls[0]["metadata"]

    assert meta["presentationDecision"]["selected"] == "table"
    assert meta.get("explicitSessionFormat") == "table"
    assert meta["presentation"]["type"] == "table"


def test_apply_format_override_chart_aligns_decision():
    service = ChatToolContextFormatService()
    metadata = {
        "ok": True,
        "path": "/financial/rol",
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "single",
            "availableViews": ["text", "chart", "table"],
        },
        "presentation": {"type": "chart", "title": "ROL", "data": [{"label": "Jan", "value": 1}]},
        "textPresentation": {"type": "markdown", "markdown": "### ROL"},
    }
    tool_calls = [{"name": "execute_external_action", "metadata": metadata}]

    service.apply_format_override(tool_calls, "chart", {"items": []})

    meta = tool_calls[0]["metadata"]

    assert meta["presentationDecision"]["selected"] == "chart"
    assert meta.get("explicitSessionFormat") == "chart"
    assert meta["presentation"]["type"] == "chart"


def test_apply_format_override_builds_stock_tree_from_wrapped_payload():
    service = ChatToolContextFormatService()
    metadata = {
        "ok": True,
        "path": "/products/10080022/stock",
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "single",
            "availableViews": ["text", "table", "tree"],
        },
        "textPresentation": {"type": "markdown", "markdown": "Resumo"},
        "presentation": None,
    }
    tool_calls = [{"name": "execute_external_action", "metadata": metadata}]
    payload = {
        "stock": {
            "items": [
                {
                    "branch": "01",
                    "warehouse": "01",
                    "current_quantity": 10,
                    "available_quantity": 8,
                    "committed_quantity": 2,
                },
            ]
        }
    }

    service.apply_format_override(tool_calls, "tree", payload)

    meta = tool_calls[0]["metadata"]

    assert meta["presentation"]["type"] == "tree"
    assert meta["presentationDecision"]["selected"] == "tree"
    assert meta.get("explicitSessionFormat") == "tree"


def test_apply_format_override_builds_structure_table_from_tree_primary():
    service = ChatToolContextFormatService()
    metadata = {
        "ok": True,
        "path": "/products/90269001/structure",
        "presentationDecision": {
            "selected": "tree",
            "layoutMode": "single",
            "availableViews": ["text", "table", "tree"],
        },
        "presentation": {"type": "tree", "title": "Estrutura", "root": {"id": "root"}},
        "textPresentation": {"type": "markdown", "markdown": "Resumo"},
    }
    tool_calls = [{"name": "execute_external_action", "metadata": metadata}]
    payload = {
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
            }
        ],
        "total": 1,
    }

    service.apply_format_override(tool_calls, "table", payload)

    meta = tool_calls[0]["metadata"]

    assert meta["presentation"]["type"] == "table"
    assert meta["presentationDecision"]["selected"] == "table"
    assert meta.get("explicitSessionFormat") == "table"


def test_apply_format_override_text_preserves_factory_stack_payload():
    service = ChatToolContextFormatService()
    from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    metadata = {
        "ok": True,
        "path": "/products/90269002/factory-status",
        "apiDelpiResponseMeta": envelope.get("meta") or {"entity": "product_factory_status"},
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
            "availableViews": ["text", "table", "tree", "chart", "kpi", "dashboard"],
            "visualOrder": ["text", "table", "tree", "chart", "kpi", "dashboard"],
        },
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Status fabril\n\nResumo.",
        },
        "tablePresentations": [{"type": "table", "title": "Panorama fabril", "rows": []}],
        "treePresentation": {"type": "tree", "root": {"id": "root"}},
        "kpiPresentation": {"type": "kpi", "cards": []},
        "dashboardPresentation": {"type": "dashboard", "panels": []},
        "preferredFormat": "text",
    }
    tool_calls = [{"name": "execute_external_action", "metadata": metadata}]

    service.apply_format_override(tool_calls, "text", envelope.get("data"))

    meta = tool_calls[0]["metadata"]

    assert meta.get("explicitSessionFormat") == "text"
    assert meta["presentationDecision"]["layoutMode"] == "stack"
    assert meta.get("tablePresentations") is not None
    assert meta.get("treePresentation") is not None
    assert meta.get("kpiPresentation") is not None
    assert meta.get("dashboardPresentation") is not None


def test_apply_format_override_dashboard_rebuilds_render_plan_after_stack_prune():
    service = ChatToolContextFormatService()
    from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    metadata = {
        "ok": True,
        "path": "/products/90269002/factory-status",
        "apiDelpiResponseMeta": envelope.get("meta") or {"entity": "product_factory_status"},
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
            "presentationMode": "summary_then_evidence",
            "availableViews": ["text", "table", "tree", "chart", "kpi", "dashboard"],
            "visualOrder": ["text", "kpi", "tree", "chart"],
            "insight": "Situação fabril: **PA PRODUZIDO / AGUARDANDO INSPEÇÃO FINAL**",
        },
        "stackPresentationPlan": {
            "presentationMode": "summary_then_evidence",
            "tailVisualPolicy": "allowlist",
            "tailVisualOrder": ["kpi", "tree", "chart"],
            "narrativeOrder": ["lead", "operationalTables", "tailVisuals"],
            "renderHints": {"suppressedKinds": ["dashboard", "table"], "textRenderMode": "compact"},
        },
        "renderPlan": {
            "version": 1,
            "layoutMode": "stack",
            "segments": [
                {"kind": "markdown", "slot": "lead", "source": "textPresentation"},
                {"kind": "kpi", "slot": "tailVisuals", "source": "kpiPresentation"},
            ],
        },
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Status fabril\n\nLead compacto.",
        },
        "tablePresentations": [{"type": "table", "title": "Panorama fabril", "rows": [{"campo": "OPs", "valor": "305"}]}],
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "root", "children": []}},
        "kpiPresentation": {"type": "kpi", "title": "Indicadores", "cards": [{"label": "OPs", "value": 305}]},
        "chartPresentation": {"type": "chart", "title": "Saldo MP", "data": []},
        "preferredFormat": "text",
    }
    tool_calls = [{"name": "execute_external_action", "metadata": metadata}]

    service.apply_format_override(tool_calls, "dashboard", envelope.get("data"))

    meta = tool_calls[0]["metadata"]
    decision = meta.get("presentationDecision") or {}
    render_plan = meta.get("renderPlan") or {}
    dashboard = meta.get("presentation") or meta.get("dashboardPresentation") or {}

    assert meta.get("explicitSessionFormat") == "dashboard"
    assert decision.get("selected") == "dashboard"
    assert decision.get("layoutMode") == "single"
    assert render_plan.get("layoutMode") == "single"
    assert dashboard.get("type") == "dashboard"
    assert any(
        segment.get("kind") == "dashboard"
        for segment in render_plan.get("segments") or []
        if isinstance(segment, dict)
    ), "override Painel deve reconstruir renderPlan com segmento dashboard"
    assert meta.get("tablePresentations"), "tabelas permanecem no payload para troca de formato"
