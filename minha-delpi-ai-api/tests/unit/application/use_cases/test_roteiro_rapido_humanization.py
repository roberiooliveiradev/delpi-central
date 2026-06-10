"""Roteiro rápido jun/2026 — narrativa humanizada + stack nas perguntas principais."""

from __future__ import annotations

import pytest

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

_ROTEIRO = [
    pytest.param(
        "product_stock_90269001.json",
        "/products/10080022/stock",
        "estoque do produto 10080022",
        id="R1_estoque",
    ),
    pytest.param(
        "product_factory_status_90269002.json",
        "/products/90269002/factory-status",
        "status fabril do produto 90269002 hoje",
        id="R2_factory_status",
    ),
    pytest.param(
        "product_raw_material_price_intelligence_10080001.json",
        "/products/10080001/raw-material-price-intelligence",
        "análise de preço da matéria-prima 10080001",
        id="R3_mp_price",
    ),
    pytest.param(
        "product_cost_impact_simulation_90261255.json",
        "/products/90261255/cost-impact-simulation",
        "quais materiais mais impactam o custo do PA 90261255?",
        id="R4_cost_impact",
    ),
    pytest.param(
        "product_pricing_10080001.json",
        "/products/10080001/pricing",
        "qual o preço de venda do produto 10080001?",
        id="R5_pricing",
    ),
]


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def _build(fixture: str, path: str, user_message: str) -> dict:
    envelope = load_api_delpi_fixture_with_meta(fixture)

    return _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": user_message},
    )


def _assert_humanized_response(meta: dict) -> None:
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "").strip()
    plan = meta.get("stackPresentationPlan") or {}
    decision = meta.get("presentationDecision") or {}

    assert markdown, "textPresentation.markdown ausente"
    assert plan.get("humanizedSections") is True
    assert plan.get("sectionFraming"), "sectionFraming vazio"
    assert decision.get("selected") == "text"
    assert decision.get("layoutMode") == "stack"
    assert "<!-- section:scope -->" in markdown or "**" in markdown
    assert not markdown.startswith("|"), "narrativa não deve começar como tabela markdown"


@pytest.mark.parametrize("fixture,path,user_message", _ROTEIRO)
def test_roteiro_rapido_entrega_stack_humanizado(fixture: str, path: str, user_message: str):
    meta = _build(fixture, path, user_message)
    _assert_humanized_response(meta)


def test_r3_mp_price_inclui_leitura_e_atencao():
    meta = _build(
        "product_raw_material_price_intelligence_10080001.json",
        "/products/10080001/raw-material-price-intelligence",
        "10080001",
    )
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    _assert_humanized_response(meta)
    assert "Leitura do histórico" in markdown
    assert "Pontos de atenção" in markdown
    plan_framing = (meta.get("stackPresentationPlan") or {}).get("sectionFraming") or {}
    assert plan_framing.get("scope")
