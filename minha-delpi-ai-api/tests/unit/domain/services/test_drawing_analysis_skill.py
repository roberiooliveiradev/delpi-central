"""Regressão D1–D12 — skill Análise de Desenhos DELPI (playbook §16)."""

from __future__ import annotations

import copy

import pytest

from app.domain.services.chat_drawing_analysis_turn_service import (
    ChatDrawingAnalysisTurnService,
)
from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_structure_validation_service import (
    ChatDrawingStructureValidationService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from app.domain.skills.chat_skill_registry import ChatSkillRegistry
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def _pdf_ok(*, code: str = "90260140", revision: str = "01") -> dict:
    return {
        "productCode": code,
        "revision": revision,
        "legible": True,
        "componentCodes": ["50212194"],
        "intermediateCodes": ["50212194"],
        "dimensions": {"totalLengthMm": 2.0, "leftDecapeMm": 10.0, "rightDecapeMm": 12.0},
    }


def _package(
    *,
    payload: dict | None = None,
    has_pdf: bool = True,
    pdf_extract: dict | None = None,
    api_ok: bool = True,
    api_status_code: int | None = 200,
    product_code: str = "90260140",
) -> dict:
    return ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code=product_code,
        payload=payload if payload is not None else _analyser_payload_with_guide_and_inspection(),
        has_pdf_attachment=has_pdf,
        api_ok=api_ok,
        api_status_code=api_status_code,
        pdf_extract=pdf_extract,
    )


def _critical_items(package: dict) -> list[dict]:
    return [
        item
        for item in package["drawingAnalysis"]["items"]
        if item.get("status") == "critical_error"
    ]


def test_d1_pdf_valid_product_exists_report():
    """D1: PDF válido + produto existente → extrai código, API, relatório."""
    pdf_extract = _pdf_ok()
    package = _package(has_pdf=True, pdf_extract=pdf_extract)
    analysis = package["drawingAnalysis"]
    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)

    assert ChatDrawingIntentService.is_drawing_analysis_request(
        "analise o desenho 90260140",
        attachment_ids=["att-1"],
    )
    assert pdf_extract["productCode"] == "90260140"
    assert analysis["productCode"] == "90260140"
    assert analysis["hasPdfAttachment"] is True
    assert len(analysis["items"]) >= 4
    assert "Relatório de Análise de Desenho DELPI" in report
    assert "Checklist completo" in report


def test_d2_product_not_found_critical():
    """D2: Produto não existe → erro crítico."""
    package = _package(
        payload=None,
        has_pdf=True,
        pdf_extract=_pdf_ok(),
        api_ok=False,
        api_status_code=404,
        product_code="99999999",
    )

    assert package["drawingAnalysis"]["status"] == "rejected"
    assert package["drawingAnalysis"]["criticalErrors"] >= 1
    assert any(item.get("item") == "Cadastro do produto" for item in _critical_items(package))


def test_d3_revision_divergence_critical():
    """D3: Revisão divergente → erro crítico no cabeçalho."""
    payload = _analyser_payload_with_guide_and_inspection()
    payload["product"]["last_revision_date"] = "02"

    package = _package(
        payload=payload,
        pdf_extract=_pdf_ok(revision="99"),
    )

    assert any(
        item.get("item") == "Revisão" and item.get("status") == "critical_error"
        for item in package["drawingAnalysis"]["items"]
    )


def test_d4_missing_component_critical():
    """D4: Componente faltante no PDF → erro crítico."""
    root = _analyser_payload_with_guide_and_inspection()
    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract={"legible": True, "componentCodes": [], "intermediateCodes": [], "dimensions": {}},
        product_code="90260140",
    )

    assert any(
        "ausente" in str(item.get("item", "")).lower() and item.get("status") == "critical_error"
        for item in items
    )


def test_d5_extra_component_critical():
    """D5: Componente extra no PDF → erro crítico."""
    root = _analyser_payload_with_guide_and_inspection()
    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract={
            "legible": True,
            "componentCodes": ["50212194", "50999999"],
            "intermediateCodes": ["50212194", "50999999"],
            "dimensions": {},
        },
        product_code="90260140",
    )

    assert any(
        "extra" in str(item.get("item", "")).lower() and item.get("status") == "critical_error"
        for item in items
    )


def test_d6_length_divergence_critical():
    """D6: Comprimento divergente → erro crítico."""
    root = _analyser_payload_with_guide_and_inspection()
    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract={
            "legible": True,
            "componentCodes": ["50212194"],
            "intermediateCodes": ["50212194"],
            "dimensions": {"totalLengthMm": 500.0},
        },
        product_code="90260140",
    )

    assert any(
        "comprimento" in str(item.get("item", "")).lower()
        and item.get("status") in {"critical_error", "error"}
        for item in items
    )


def test_d7_decape_fields_registered_in_checklist():
    """D7: Decapes no PDF → item de cotas no checklist (tolerância ±1 mm na regra)."""
    root = _analyser_payload_with_guide_and_inspection()
    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract={
            "legible": True,
            "componentCodes": ["50212194"],
            "intermediateCodes": ["50212194"],
            "dimensions": {"totalLengthMm": 2.0, "leftDecapeMm": 25.0, "rightDecapeMm": 25.0},
        },
        product_code="90260140",
    )

    decape_items = [
        item for item in items if "decape" in str(item.get("item", "")).lower()
    ]

    assert decape_items
    assert decape_items[0].get("section") == "Cotas"
    assert "±1 mm" in str(decape_items[0].get("rule", ""))


def test_d8_intermediate_code_malformed_critical():
    """D8: Código fora da família 50xx → erro crítico de formato."""
    root = _analyser_payload_with_guide_and_inspection()
    items = ChatDrawingStructureValidationService.build_check_items(
        root=root,
        pdf_extract={
            "legible": True,
            "componentCodes": ["50212194"],
            "intermediateCodes": ["40123456"],
            "dimensions": {},
        },
        product_code="90260140",
    )

    assert any(
        item.get("item") == "Formato intermediário"
        and item.get("status") == "critical_error"
        for item in items
    )


def test_d9_illegible_pdf_incomplete():
    """D9: PDF ilegível → análise incompleta."""
    package = _package(
        has_pdf=True,
        pdf_extract={"productCode": "90260140", "legible": False, "reason": "texto insuficiente"},
    )

    assert package["drawingAnalysis"]["status"] == "incomplete"
    assert package["drawingAnalysis"]["pdfLegible"] is False


def test_d10_missing_routing_critical():
    """D10: Roteiro ausente → erro crítico."""
    payload = copy.deepcopy(_analyser_payload_with_guide_and_inspection())
    payload["guide"] = {"items": [], "total": 0}

    package = _package(payload=payload, has_pdf=False)

    assert any(
        item.get("section") == "Roteiro" and item.get("status") == "critical_error"
        for item in package["drawingAnalysis"]["items"]
    )


def test_d11_missing_inspection_critical():
    """D11: Inspeção ausente → erro crítico."""
    payload = copy.deepcopy(_analyser_payload_with_guide_and_inspection())
    payload["inspection"] = {"items": []}

    package = _package(payload=payload, has_pdf=False)

    assert any(
        item.get("section") == "Inspeção" and item.get("status") == "critical_error"
        for item in package["drawingAnalysis"]["items"]
    )


def test_d12_full_report_has_pdf_api_norm_evidence():
    """D12: Relatório completo com evidências PDF, API e recomendação."""
    package = _package(has_pdf=True, pdf_extract=_pdf_ok())
    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)

    for item in package["drawingAnalysis"]["items"]:
        assert item.get("pdfEvidence") is not None
        assert item.get("apiEvidence") is not None
        assert item.get("recommendation")

    assert "Status geral" in report
    assert "conclus" in report.lower() or "Conclusão" in report


def test_skill_disabled_when_not_in_runtime_flags():
    """Agente sem skill → resposta orientando habilitar."""
    turn = ChatDrawingAnalysisTurnService.resolve(
        message="analise o desenho 90260140",
        attachment_ids=["a1"],
        agent_metadata={"skills": {"drawing-analysis-delpi": {"engineering": False}}},
        skills={"drawingAnalysis": False},
    )

    assert turn is not None
    assert turn.direct_answer
    assert "drawing-analysis-delpi" in turn.direct_answer


def test_skill_enabled_via_registry_when_analyser_allowed():
    """Skill default quando action analyser está permitida."""
    flags = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata=None,
        allowed_action_ids=["get_product_analyser"],
        has_agent=True,
    )

    assert flags["drawingAnalysis"] is True


def test_pdf_extract_from_fixture_text():
    parsed = ChatDrawingPdfExtractionService.parse_from_text("DESENHO 90260140 REV.01")

    assert parsed.get("productCode") == "90260140"
