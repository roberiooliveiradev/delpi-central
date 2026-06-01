"""Regressão Playbook 08 — pesquisa web confiável (W1–W15)."""

from unittest.mock import patch

import pytest

from app.domain.services.chat_web_search_planning_service import ChatWebSearchPlanningService
from app.domain.services.chat_web_search_query_security_service import (
    ChatWebSearchQuerySecurityService,
)
from app.domain.services.chat_web_search_research_service import ChatWebSearchResearchService
from app.domain.services.chat_web_search_source_evaluation_service import (
    ChatWebSearchSourceEvaluationService,
)
from app.domain.services.web_search_query_service import WebSearchQueryService
from tests.fixtures.web_search_research_cases import WEB_SEARCH_RESEARCH_CASES


@pytest.mark.parametrize("case", WEB_SEARCH_RESEARCH_CASES, ids=lambda c: c["id"])
def test_web_search_research_cases(case):
    message = case["message"]

    if "expect_decline" in case:
        assert ChatWebSearchResearchService.should_decline_web(message)

    expect_web = case.get("expect_web")

    if expect_web is not None:
        assert (
            ChatWebSearchResearchService.should_use_web(
                message,
                text_task_pure=case.get("text_task_pure", False),
            )
            is expect_web
        )

    if not case.get("expect_web", True) and "expect_decline" not in case:
        return

    if case.get("expect_redacted"):
        security = ChatWebSearchResearchService.sanitize_query(message)
        assert security.redacted
        assert "12,30" not in security.query
        assert "preco interno" not in security.query.lower()

        if case.get("expect_no_price_in_query"):
            assert "r$" not in security.query.lower()

    if case.get("expect_web") is False:
        return

    with patch(
        "app.domain.services.chat_web_search_intent_service.ChatWebSearchIntentService.is_feature_enabled",
        return_value=True,
    ):
        plan = ChatWebSearchResearchService.plan(message)

    assert plan is not None

    if mode := case.get("expect_mode"):
        assert plan.mode == mode

    if case.get("expect_prefer_official"):
        assert plan.prefer_official is True

    if case.get("expect_intent"):
        assert plan.intent == case["expect_intent"]

    if min_q := case.get("expect_min_queries"):
        assert len(plan.queries) >= min_q

    if case.get("expect_site_query"):
        assert any("site:" in query for query in plan.queries)

    if case.get("expect_recent_query"):
        assert any("noticias" in query.lower() or "2026" in query for query in plan.queries)

    if case.get("expect_english_retry"):
        primary = plan.primary_query().lower()
        assert "heat" in primary or "tubing" in primary or "specifications" in primary


def test_w4_official_manufacturer_evaluation():
    evaluation = ChatWebSearchResearchService.evaluate_source(
        "https://www.weg.net/ww/Products/Motors/CFW500",
        title="Manual CFW500",
    )
    quality = ChatWebSearchResearchService.source_quality_metadata(evaluation)

    assert evaluation.is_official
    assert quality["type"] == "official_manufacturer"
    assert quality["confidence"] == "high"


def test_w7_no_reliable_source_warning():
    payload = {
        "searchStatus": "success",
        "preferOfficial": True,
        "results": [
            {
                "url": "https://forum.example.com/thread/123",
                "title": "opiniao sobre produto",
                "source": "searxng",
            }
        ],
    }
    enriched = ChatWebSearchSourceEvaluationService.enrich_payload(payload)
    evaluation = enriched.get("sourceEvaluation") or {}

    assert evaluation.get("confidence") in {"low", "medium"}
    assert evaluation.get("warnings")


def test_w10_sanitize_internal_price():
    result = ChatWebSearchQuerySecurityService.sanitize(
        "cliente ABC comprou pelo preco interno R$ 99,00",
        extracted_query="cliente ABC comprou pelo preco interno R$ 99,00",
    )

    assert result.redacted
    assert "99" not in result.query
    assert "informacoes publicas" in result.query


def test_w12_source_compare_integration_note():
    from app.domain.services.chat_web_search_integration_service import (
        ChatWebSearchIntegrationService,
    )

    integration = ChatWebSearchIntegrationService.resolve(
        "pesquise na web e compare fontes sobre CFW500"
    )

    assert integration is not None
    assert integration.mode == "source_compare"


@patch(
    "app.domain.services.chat_web_search_intent_service.ChatWebSearchIntentService.is_feature_enabled",
    return_value=True,
)
def test_w9_attachment_compare_mode(_enabled):
    from app.domain.services.chat_web_search_integration_service import (
        ChatWebSearchIntegrationService,
    )

    integration = ChatWebSearchIntegrationService.resolve(
        "pesquise na web e compare esse datasheet anexado com o site oficial",
        attachment_context="CFW500 especificacoes",
    )

    assert integration is not None
    assert integration.mode == "attachment_compare"


def test_abnt_standards_domain_planning():
    with patch(
        "app.domain.services.chat_web_search_intent_service.ChatWebSearchIntentService.is_feature_enabled",
        return_value=True,
    ):
        plan = ChatWebSearchPlanningService.plan(
            "pesquise na web norma abnt cabos eletricos"
        )

    assert plan is not None
    assert any("site:abnt.org.br" in query for query in plan.queries)
