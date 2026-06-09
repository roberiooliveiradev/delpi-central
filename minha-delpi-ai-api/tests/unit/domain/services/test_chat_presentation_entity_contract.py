"""Contrato mínimo de apresentação por entidade roteada — Fase 6."""

from __future__ import annotations

import pytest

from app.domain.services.chat_presentation_coverage_service import (
    ChatPresentationCoverageService,
)
from app.domain.services.chat_presentation_decision_service import (
    ChatPresentationDecisionService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)


def _resolved_path(path: str) -> str:
    return path.replace("{code}", "10080001").replace("/0/", "/10080001/")


def _minimal_metadata(entity: str, path: str) -> dict:
    resolved = _resolved_path(path)
    table = {
        "type": "table",
        "title": "Resultado",
        "columns": [{"key": "label", "label": "Campo"}, {"key": "value", "label": "Valor"}],
        "rows": [{"label": "Exemplo", "value": "1"}],
    }
    text = {
        "type": "markdown",
        "title": "Resumo",
        "markdown": "**Resumo operacional** — dados de exemplo.",
    }
    metadata = {
        "ok": True,
        "path": resolved,
        "entity": entity,
        "availableFormats": ["text", "table", "chart"],
        "tablePresentation": table,
        "textPresentation": text,
    }

    if entity.startswith("product_") and "structure" in entity:
        metadata["treePresentation"] = {
            "type": "tree",
            "title": "Estrutura",
            "root": {"id": "10080001", "label": "10080001", "children": []},
        }
        metadata["availableFormats"] = ["text", "table", "tree", "chart"]
    elif entity == "product_analyser":
        metadata["presentation"] = metadata["treePresentation"] = {
            "type": "tree",
            "title": "Analyser",
            "root": {"id": "10080001", "label": "10080001", "children": []},
        }
        metadata["availableFormats"] = ["text", "table", "tree", "chart", "dashboard"]
    elif entity.endswith("_series") or "chart" in entity or entity.endswith("_rate"):
        metadata["presentation"] = {
            "type": "chart",
            "title": "Série",
            "chartType": "line",
            "data": [{"period": "jan/2026", "value": 10}],
            "config": {"xAxis": "period", "yAxis": ["value"]},
        }
    elif "summary" in entity or entity.endswith("_pct") or entity.endswith("_count"):
        metadata["presentation"] = {
            "type": "kpi",
            "title": "Indicador",
            "cards": [{"label": "Valor", "value": "82", "unit": "%"}],
        }

    return metadata


ENTITY_CONTRACT_CASES = ChatPresentationCoverageService.build_entity_contract_cases()


@pytest.mark.parametrize(
    "case",
    ENTITY_CONTRACT_CASES,
    ids=[item["entity"] for item in ENTITY_CONTRACT_CASES],
)
def test_entity_resolves_registered_profile(case: dict[str, str]) -> None:
    profile_key = ChatPresentationProfileService.resolve_profile_key(
        _resolved_path(case["path"]),
        case["entity"],
    )
    registered = ChatPresentationCoverageService.registered_profile_keys()

    assert profile_key in registered

    if case["tier"] == "A":
        assert profile_key != "generic"


@pytest.mark.parametrize(
    "case",
    ENTITY_CONTRACT_CASES,
    ids=[item["entity"] for item in ENTITY_CONTRACT_CASES],
)
def test_entity_presentation_decision_selected_in_available_views(case: dict[str, str]) -> None:
    metadata = _minimal_metadata(case["entity"], case["path"])

    ChatPresentationDecisionService.enrich_metadata(metadata)

    decision = metadata.get("presentationDecision") or {}
    selected = str(decision.get("selected") or "").strip().lower()
    available = {
        str(view or "").strip().lower()
        for view in (decision.get("availableViews") or [])
        if str(view or "").strip()
    }

    assert selected
    assert selected in available or not available

    text = metadata.get("textPresentation")

    if isinstance(text, dict) and "text" in available:
        markdown = str(text.get("markdown") or "").strip()
        assert markdown


def test_ci_profile_gate_passes_on_current_openapi() -> None:
    validation = ChatPresentationCoverageService.validate_for_ci()

    assert validation["ok"] is True
    assert not validation["profileGaps"]
