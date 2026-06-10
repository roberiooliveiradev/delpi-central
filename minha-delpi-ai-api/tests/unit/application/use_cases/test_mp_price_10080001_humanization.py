"""Regressão — análise MP 10080001 deve manter narrativa humanizada no stack."""

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


def _build(*, user_message: str) -> dict:
    envelope = load_api_delpi_fixture_with_meta(
        "product_raw_material_price_intelligence_10080001.json"
    )
    path = "/products/10080001/raw-material-price-intelligence"

    return _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": user_message},
    )


def test_mp_price_10080001_code_only_defaults_to_text_stack_with_full_narrative():
    meta = _build(user_message="10080001")
    decision = meta["presentationDecision"]
    markdown = str(meta.get("textPresentation", {}).get("markdown") or "")

    assert decision["selected"] == "text"
    assert decision["layoutMode"] == "stack"
    assert "Resumo do produto" in markdown
    assert "Leitura do histórico" in markdown
    assert "Última compra real" in markdown
    assert "Variação de preço" in markdown
    assert "Pontos de atenção" in markdown
    assert "Recomendação" in markdown
    assert "cadastrado" in markdown.lower() or "170" in markdown

    plan = meta.get("stackPresentationPlan") or {}

    assert plan.get("humanizedSections") is True
    assert plan.get("presentationProfile") == "product_raw_material_price_intelligence"
