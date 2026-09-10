"""E4.S2 — baseline freeze: capability discovery + help Action Catalog gates."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.chat_capabilities_catalog_answer_service import (
    ChatCapabilitiesCatalogAnswerService,
)
from app.domain.services.chat_capability_discovery_service import (
    ChatCapabilityDiscoveryService,
)


@dataclass(frozen=True)
class DiscoveryBaselineCase:
    family: str
    message: str
    top_capability_id: str | None
    min_score: float | None


# Frozen 2026-09-10 against HEAD ChatCapabilityDiscoveryService + registry.
_CORPUS: tuple[DiscoveryBaselineCase, ...] = (
    DiscoveryBaselineCase(
        family="action_stock",
        message="qual o estoque do 10080001?",
        top_capability_id="action.product_stock",
        min_score=1.0,
    ),
    DiscoveryBaselineCase(
        family="action_search",
        message="busque terminais pino",
        top_capability_id="action.product_search",
        min_score=1.0,
    ),
    DiscoveryBaselineCase(
        family="action_description",
        message="mostra a ficha do produto 10080001",
        top_capability_id="action.product_description",
        min_score=1.0,
    ),
    DiscoveryBaselineCase(
        family="rag_norms",
        message="normas da empresa",
        top_capability_id="rag.company_knowledge",
        min_score=1.0,
    ),
    DiscoveryBaselineCase(
        family="web_search",
        message="pesquisa isso na web",
        top_capability_id="web.search",
        min_score=1.0,
    ),
    DiscoveryBaselineCase(
        family="skill_compliance",
        message="essa descrição está conforme a norma?",
        top_capability_id="skill.technical_description_compliance",
        min_score=1.0,
    ),
    DiscoveryBaselineCase(
        family="transform_reason",
        message="resuma o que você encontrou",
        top_capability_id="transform.reason",
        min_score=1.0,
    ),
    DiscoveryBaselineCase(
        family="help_question_no_registry_hit",
        message="o que você pode fazer?",
        top_capability_id=None,
        min_score=None,
    ),
)


def test_e4_s2_baseline_covers_required_families():
    families = {case.family for case in _CORPUS}
    required = {
        "action_stock",
        "action_search",
        "action_description",
        "rag_norms",
        "web_search",
        "skill_compliance",
        "transform_reason",
        "help_question_no_registry_hit",
    }
    assert required <= families


def test_e4_s2_discovery_matches_frozen_baseline():
    mismatches: list[tuple[str, object, object]] = []
    for case in _CORPUS:
        result = ChatCapabilityDiscoveryService.discover(case.message, top_k=3)
        top = result.candidates[0] if result.candidates else None
        top_id = None if top is None else str(top.get("capabilityId") or "")
        score = None if top is None else float(top.get("score") or 0.0)
        if case.top_capability_id is None:
            if top_id is not None:
                mismatches.append((case.family, None, top_id))
            continue
        if top_id != case.top_capability_id:
            mismatches.append((case.family, case.top_capability_id, top_id))
        elif case.min_score is not None and (score or 0.0) < case.min_score:
            mismatches.append((case.family, case.min_score, score))
    assert not mismatches, mismatches


def test_e4_s2_action_types_filter_excludes_rag():
    result = ChatCapabilityDiscoveryService.discover(
        "normas da empresa",
        top_k=5,
        allowed_types={"action"},
    )
    assert all(str(item.get("type")) == "action" for item in result.candidates)
    assert not any(
        str(item.get("capabilityId") or "").startswith("rag.")
        for item in result.candidates
    )


def test_e4_s2_help_format_respects_allowed_action_ids():
    catalog = [
        {
            "actionId": "acme.a",
            "name": "A",
            "summary": "consulta estoque",
            "enabled": True,
            "delpi_metadata": {"uxCapability": "Estoque"},
        },
        {
            "actionId": "acme.b",
            "name": "B",
            "summary": "outra",
            "enabled": True,
            "delpi_metadata": {"uxCapability": "Outras consultas"},
        },
    ]
    lines = ChatCapabilitiesCatalogAnswerService.format_action_catalog(
        catalog,
        allowed_ids=["acme.a"],
    )
    joined = "\n".join(lines)
    assert "Estoque" in joined or "consulta estoque" in joined.lower()
    assert "Outras consultas" not in joined or "outra" not in joined.lower()
    # B must not appear as its own summary line
    assert "- outra" not in joined.lower()


def test_e4_s2_pathrules_not_required_for_discovery():
    # Guard: discovery não depende de capabilities.pathRules
    result = ChatCapabilityDiscoveryService.discover("estoque do 10080001", top_k=1)
    assert result.candidates
    assert result.candidates[0]["capabilityId"] == "action.product_stock"
