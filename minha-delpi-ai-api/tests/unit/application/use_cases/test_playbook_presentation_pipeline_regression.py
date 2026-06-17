"""Regressão do pipeline completo de apresentação — roteiro perguntas-teste-chat-jun2026."""

from __future__ import annotations

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def _build(fixture: str, path: str, *, user_message: str = "", session_format: str = "") -> dict:
    envelope = load_api_delpi_fixture_with_meta(fixture)
    params: dict = {}

    if user_message:
        params["userMessage"] = user_message

    if session_format:
        params["sessionResponseFormat"] = session_format

    return _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters=params,
    )


def _structure_table_titles(meta: dict) -> list[str]:
    titles: list[str] = []

    for table in meta.get("tablePresentations") or []:
        if isinstance(table, dict) and table.get("role") == "structure":
            titles.append(str(table.get("title") or ""))

    return titles


def test_factory_status_integrated_stack_with_visuals():
    meta = _build(
        "product_factory_status_90269002.json",
        "/products/90269002/factory-status",
        user_message="visão integrada do status fabril do produto 90269002 hoje",
    )
    decision = meta["presentationDecision"]

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "stack"
    assert meta.get("textPresentation", {}).get("markdown")
    assert meta.get("kpiPresentation", {}).get("type") == "kpi"
    assert meta.get("treePresentation", {}).get("type") == "tree"

    plan = meta.get("stackPresentationPlan") or {}
    render_plan = meta.get("renderPlan") or {}

    assert render_plan.get("version") == 1
    assert isinstance(render_plan.get("segments"), list) and render_plan["segments"]
    assert plan.get("renderHints", {}).get("textRenderMode") in {"compact", "full"}
    assert str(plan.get("tailVisualPolicy") or "").strip()

    assert plan.get("humanizedSections") is True
    assert plan.get("presentationProfile") == "product_factory_status"
    presentation_mode = str(plan.get("presentationMode") or "").strip()

    if presentation_mode == "summary_then_evidence":
        tail_order = plan.get("tailVisualOrder") or []
        assert "dashboard" not in tail_order
        assert meta.get("dashboardPresentation") is None
        assert "tree" in tail_order
        assert "tailVisuals" in (plan.get("narrativeOrder") or [])
        assert all(
            segment.get("kind") != "dashboard"
            for segment in render_plan.get("segments") or []
            if isinstance(segment, dict)
        )
    else:
        assert (plan.get("tailVisualOrder") or []) == ["dashboard"]
        assert "tailVisuals" in (plan.get("narrativeOrder") or [])


def test_factory_status_auto_stack_with_dialogue():
    meta = _build(
        "product_factory_status_90269002.json",
        "/products/90269002/factory-status",
        user_message="status fabril do produto 90269002 hoje",
    )
    decision = meta["presentationDecision"]
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")
    plan = meta.get("stackPresentationPlan") or {}

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "stack"
    assert len(markdown) >= 120
    assert plan.get("humanizedSections") is True
    assert meta.get("tablePresentations")
    assert meta.get("kpiPresentation", {}).get("type") == "kpi"
    assert meta.get("treePresentation", {}).get("type") == "tree"
    assert meta.get("renderPlan", {}).get("version") == 1
    assert plan.get("renderHints", {}).get("textRenderMode") == "compact"
    assert meta.get("dashboardPresentation") is None
    assert "|" not in markdown.split("<!-- section:")[0][:400]


def test_factory_status_text_mode_embeds_tables_in_markdown():
    meta = _build(
        "product_factory_status_90269002.json",
        "/products/90269002/factory-status",
        user_message="status fabril do produto 90269002 hoje",
        session_format="text",
    )
    decision = meta["presentationDecision"]
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "stack"
    assert "|" in markdown
    assert "**Panorama fabril**" in markdown or "Panorama fabril" in markdown
    assert meta.get("tablePresentations") is not None
    plan = meta.get("stackPresentationPlan") or {}
    assert meta.get("dashboardPresentation") is None
    assert "dashboard" not in (plan.get("tailVisualOrder") or [])
    assert "Composição" in markdown or "└──" in markdown or "├──" in markdown


def test_structure_exclusivity_text_first_without_tree():
    meta = _build(
        "product_structure_exclusivity_90261805.json",
        "/products/90261805/structure/exclusivity",
        user_message="quais matérias-primas exclusivas existem na estrutura do produto 90261805?",
    )
    decision = meta["presentationDecision"]
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    assert decision["selected"] == "text"
    assert decision["layoutMode"] in {"single", "stack"}
    assert meta.get("treePresentation", {}).get("type") == "tree"
    assert "Resposta" in markdown
    assert "10020053" in markdown
    assert "10080185" in markdown
    assert "Matérias-primas da estrutura" in markdown
    assert "exclusiva" in markdown.lower()
    assert "table" in (decision.get("availableViews") or [])


def test_structure_exclusivity_integrated_stack_keeps_tree():
    meta = _build(
        "product_structure_exclusivity_90261805.json",
        "/products/90261805/structure/exclusivity",
        user_message="visão integrada das matérias-primas exclusivas na estrutura do produto 90261805",
    )
    decision = meta["presentationDecision"]

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "stack"
    assert meta.get("treePresentation", {}).get("type") == "tree"
    structure_titles = _structure_table_titles(meta)
    assert structure_titles == [] or structure_titles == ["Matérias-primas da estrutura"]


def test_mp_price_intelligence_text_first_without_visuals():
    meta = _build(
        "product_raw_material_price_intelligence_10080022.json",
        "/products/10080022/raw-material-price-intelligence",
        user_message="análise de preço da matéria-prima 10080022",
    )
    decision = meta["presentationDecision"]
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "single"
    assert "ALTA DE PRECO" in markdown or "cadastrado" in markdown.lower()
    assert meta.get("kpiPresentation") is None
    assert meta.get("chartPresentation") is None
    assert "chart" in (decision.get("availableViews") or [])


def test_cost_impact_simulation_text_first_without_visuals():
    meta = _build(
        "product_cost_impact_simulation_90261255.json",
        "/products/90261255/cost-impact-simulation",
        user_message="quais materiais mais impactam o custo do PA 90261255?",
    )
    decision = meta["presentationDecision"]

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "single"
    assert meta.get("textPresentation", {}).get("markdown")
    assert meta.get("kpiPresentation") is None
    assert meta.get("chartPresentation") is None


def test_stock_playbook_keeps_data_answer_without_decision_card():
    meta = _build(
        "product_stock_90269001.json",
        "/products/90269001/stock",
        user_message="estoque do produto 90269001",
    )

    assert meta.get("storyPresentation") is None
    assert meta.get("dataAnswer", {}).get("summary", {}).get("answer")
    assert meta.get("textPresentation", {}).get("markdown")


def test_stock_playbook_text_first_without_integrated_stack():
    meta = _build(
        "product_stock_90269001.json",
        "/products/90269001/stock",
        user_message="estoque do produto 90269001",
    )
    decision = meta["presentationDecision"]

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "single"
    assert meta.get("treePresentation") is None
    assert meta.get("chartPresentation") is None
    assert meta.get("textPresentation", {}).get("markdown")
    assert any(
        isinstance(table, dict) and table.get("role") == "list"
        for table in (meta.get("tablePresentations") or [])
    )


def test_stock_playbook_integrated_stack_builds_visuals():
    meta = _build(
        "product_stock_90269001.json",
        "/products/90269001/stock",
        user_message="estoque completo do produto 90269001",
    )
    decision = meta["presentationDecision"]

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "stack"
    assert meta.get("treePresentation", {}).get("type") == "tree"


def test_stock_text_mode_embeds_chart_mermaid():
    meta = _build(
        "product_stock_90269001.json",
        "/products/90269001/stock",
        user_message="estoque do produto 90269001",
        session_format="text",
    )
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    assert meta["presentationDecision"]["selected"] == "text"
    assert "```mermaid" in markdown
    assert "xychart-beta" in markdown or "pie showData" in markdown
    assert meta.get("chartPresentation") is None
