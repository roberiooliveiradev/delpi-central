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


def _build(fixture: str, path: str, *, user_message: str = "") -> dict:
    envelope = load_api_delpi_fixture_with_meta(fixture)
    return _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": user_message} if user_message else {},
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
    assert meta.get("dashboardPresentation", {}).get("type") == "dashboard"

    plan = meta.get("stackPresentationPlan") or {}

    assert plan.get("humanizedSections") is True
    assert plan.get("presentationProfile") == "product_factory_status"
    assert "kpi" in (plan.get("tailVisualOrder") or [])
    assert "tailVisuals" in (plan.get("narrativeOrder") or [])


def test_structure_exclusivity_text_first_without_tree():
    meta = _build(
        "product_structure_exclusivity_90261805.json",
        "/products/90261805/structure/exclusivity",
        user_message="quais matérias-primas exclusivas existem na estrutura do produto 90261805?",
    )
    decision = meta["presentationDecision"]
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "single"
    assert meta.get("treePresentation") is None
    assert "10020053" in markdown
    assert "10080185" in markdown
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
    assert not _structure_table_titles(meta)


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
