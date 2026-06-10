"""Qualidade da apresentação — resposta vs. narrativa analítica canônica dos fixtures."""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

_FACTORY_FIXTURE = "product_factory_status_90269002.json"
_FACTORY_PATH = "/products/90269002/factory-status"
_FACTORY_MESSAGE = "status fabril do produto 90269002 hoje"

_STOCK_FIXTURE = "product_stock_90269001.json"
_STOCK_PATH = "/products/90269001/stock"
_STOCK_MESSAGE = "estoque do produto 90269001"


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def _build(
    fixture: str,
    path: str,
    *,
    user_message: str = "",
    session_format: str = "",
) -> dict[str, Any]:
    envelope = load_api_delpi_fixture_with_meta(fixture)
    params: dict[str, Any] = {}

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


def _factory_canonical_facts(envelope: dict[str, Any]) -> dict[str, Any]:
    """Fatos operacionais que uma resposta analítica correta deve refletir (mesma base do fixture)."""
    data = envelope.get("data") or {}
    product = data.get("product") or {}
    structure = (data.get("structure") or {}).get("summary") or {}
    stock = (data.get("raw_material_stock") or {}).get("summary") or {}
    production = (data.get("production") or {}).get("summary") or {}
    shipping = (data.get("shipping") or {}).get("summary") or {}

    stock_items = (data.get("raw_material_stock") or {}).get("items") or []
    mp_without_stock = [
        str(item.get("raw_material_code") or "").strip()
        for item in stock_items
        if str(item.get("has_stock_for_one_pa") or "").upper() == "NAO"
    ]

    return {
        "product_code": str(product.get("product_code") or "").strip(),
        "description": str(product.get("description") or "").strip(),
        "factory_status": str(data.get("factory_status") or "").strip(),
        "reference_date": str(data.get("reference_date") or "").strip(),
        "total_components": int(structure.get("total_components") or 0),
        "total_raw_materials": int(structure.get("total_raw_materials") or 0),
        "exclusive_raw_materials": int(structure.get("total_exclusive_raw_materials") or 0),
        "mps_without_stock_for_pa": int(stock.get("total_without_stock_for_one_pa") or 0),
        "mp_codes_without_stock": mp_without_stock,
        "pa_production_started": str(production.get("pa_production_started") or "").upper(),
        "total_pa_orders": int(production.get("total_pa_orders") or 0),
        "total_shipped": int(shipping.get("total_shipped_quantity") or 0),
    }


def _assert_markdown_covers_factory_facts(
    markdown: str,
    facts: dict[str, Any],
    *,
    require_mp_codes: bool = False,
) -> None:
    lowered = markdown.lower()

    assert facts["product_code"] in markdown, "código do produto ausente na narrativa"
    assert facts["factory_status"].lower() in lowered or "op aberta" in lowered, (
        "situação fabril consolidada ausente"
    )

    if facts["reference_date"]:
        assert facts["reference_date"] in markdown, "data de referência ausente"

    assert str(facts["total_components"]) in markdown or "componente" in lowered, (
        "estrutura (componentes) não mencionada"
    )

    if facts["mps_without_stock_for_pa"] > 0:
        assert (
            "sem saldo" in lowered
            or "sem estoque" in lowered
            or "0 material" in lowered
            or str(facts["mps_without_stock_for_pa"]) in markdown
        ), "alerta de MP sem saldo para 1 PA ausente"

    if require_mp_codes:
        for mp_code in facts["mp_codes_without_stock"]:
            if mp_code:
                assert mp_code in markdown, (
                    f"MP {mp_code} sem saldo deveria aparecer na resposta textual detalhada"
                )

    if facts["pa_production_started"] == "NAO":
        assert "não" in lowered or "nao" in lowered or "0 op" in lowered, (
            "produção PA não iniciada deveria constar"
        )

    assert str(facts["total_pa_orders"]) in markdown or "op" in lowered, (
        "volume de OPs ausente"
    )

    if facts["total_shipped"] == 0:
        assert "0 expedido" in lowered or "0 un" in lowered or "expedição" in lowered, (
            "expedição no período não mencionada"
        )


def _assert_no_near_duplicate_prose(markdown: str) -> None:
    """Evita repetir o mesmo escopo/visão integrada em parágrafos quase idênticos."""
    prose_blocks = [
        re.sub(r"\s+", " ", block.strip().lower())
        for block in re.split(r"\n{2,}", markdown)
        if block.strip()
        and not block.strip().startswith("|")
        and not block.strip().startswith("```")
        and "<!-- section:" not in block
        and len(block.strip()) >= 40
    ]

    for index, left in enumerate(prose_blocks):
        for right in prose_blocks[index + 1 :]:
            if left == right:
                pytest.fail(f"parágrafo duplicado na narrativa: {left[:80]}…")

            shorter, longer = (left, right) if len(left) <= len(right) else (right, left)

            if len(shorter) >= 60 and shorter in longer:
                pytest.fail(
                    "parágrafo redundante (um contém o outro): "
                    f"«{shorter[:72]}…» dentro de «{longer[:72]}…»"
                )


def _assert_text_mode_payload_is_markdown_only(meta: dict[str, Any]) -> None:
    assert meta.get("explicitSessionFormat") == "text"
    decision = meta.get("presentationDecision") or {}

    assert decision.get("selected") == "text"
    assert decision.get("layoutMode") == "single"

    for slot in (
        "tablePresentations",
        "tablePresentation",
        "treePresentation",
        "chartPresentation",
        "kpiPresentation",
        "dashboardPresentation",
    ):
        assert meta.get(slot) is None, f"slot nativo {slot} deveria estar ausente no modo Texto"

    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    assert "|" in markdown, "modo Texto deve embutir tabelas em markdown"
    assert (
        "└──" in markdown
        or "├──" in markdown
        or "```text" in markdown
        or "composição" in markdown.lower()
    ), "modo Texto deve embutir árvore em markdown"


def test_factory_status_auto_quality_matches_fixture_analyst_narrative():
    envelope = load_api_delpi_fixture_with_meta(_FACTORY_FIXTURE)
    facts = _factory_canonical_facts(envelope)
    meta = _build(_FACTORY_FIXTURE, _FACTORY_PATH, user_message=_FACTORY_MESSAGE)
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    _assert_markdown_covers_factory_facts(markdown, facts)
    _assert_no_near_duplicate_prose(markdown)

    decision = meta.get("presentationDecision") or {}
    plan = meta.get("stackPresentationPlan") or {}

    assert decision.get("layoutMode") == "stack"
    assert plan.get("humanizedSections") is True
    assert (plan.get("tailVisualOrder") or []) == ["dashboard"]
    assert meta.get("kpiPresentation", {}).get("type") == "kpi"
    assert meta.get("dashboardPresentation", {}).get("type") == "dashboard"
    assert "|" not in markdown.split("<!-- section:")[0][:500], (
        "lead narrativo não deve abrir com tabela markdown crua"
    )


def test_factory_status_explicit_text_quality_matches_fixture_without_native_slots():
    envelope = load_api_delpi_fixture_with_meta(_FACTORY_FIXTURE)
    facts = _factory_canonical_facts(envelope)
    meta = _build(
        _FACTORY_FIXTURE,
        _FACTORY_PATH,
        user_message=_FACTORY_MESSAGE,
        session_format="text",
    )
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    _assert_text_mode_payload_is_markdown_only(meta)
    _assert_markdown_covers_factory_facts(markdown, facts, require_mp_codes=True)
    _assert_no_near_duplicate_prose(markdown)


def test_factory_status_explicit_dashboard_single_view_without_orphan_visuals():
    envelope = load_api_delpi_fixture_with_meta(_FACTORY_FIXTURE)
    facts = _factory_canonical_facts(envelope)
    meta = _build(
        _FACTORY_FIXTURE,
        _FACTORY_PATH,
        user_message=_FACTORY_MESSAGE,
        session_format="dashboard",
    )
    decision = meta.get("presentationDecision") or {}

    assert meta.get("explicitSessionFormat") == "dashboard"
    assert decision.get("selected") == "dashboard"
    assert decision.get("layoutMode") == "single"

    dashboard = meta.get("presentation") or meta.get("dashboardPresentation") or {}

    assert dashboard.get("type") == "dashboard"
    assert meta.get("treePresentation") is None
    assert meta.get("kpiPresentation") is None

    panels = dashboard.get("panels") or []
    kpi_panels = [
        panel
        for panel in panels
        if isinstance(panel, dict)
        and isinstance(panel.get("presentation"), dict)
        and panel["presentation"].get("type") == "kpi"
    ]

    assert kpi_panels, "painel fabril deve incluir bloco KPI agregado"

    cards = kpi_panels[0].get("presentation", {}).get("cards") or []

    assert cards, "KPI do painel deve trazer cards derivados do fixture"
    assert any(
        str(facts["total_pa_orders"]) in str(card.get("value") or "")
        for card in cards
        if isinstance(card, dict)
    ), "card de OPs deve refletir total_pa_orders do fixture"


def test_stock_text_first_quality_preserves_lazy_table_and_narrative():
    meta = _build(_STOCK_FIXTURE, _STOCK_PATH, user_message=_STOCK_MESSAGE)
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    assert meta.get("explicitSessionFormat") is None, (
        "text-first automático não deve marcar formato explícito da sessão"
    )
    assert "90269001" in markdown
    assert meta.get("presentationDecision", {}).get("layoutMode") == "single"
    assert any(
        isinstance(table, dict) and table.get("role") == "list"
        for table in (meta.get("tablePresentations") or [])
    ), "tabela lazy list deve permanecer para refinamento «ver como tabela»"
