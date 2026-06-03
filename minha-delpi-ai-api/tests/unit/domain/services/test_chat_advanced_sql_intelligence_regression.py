"""Regressão SQL1–SQL20 — Playbook Especialista SQL Avançado §52."""

from __future__ import annotations

import pytest

from app.domain.services.chat_advanced_sql_specialist_service import (
    ChatAdvancedSqlSpecialistService,
)
from app.domain.services.chat_sql_dialect_resolver_service import (
    ChatSqlDialectResolverService,
)
from app.domain.services.chat_sql_performance_advisor_service import (
    ChatSqlPerformanceAdvisorService,
)
from app.domain.services.chat_sql_relationship_resolver_service import (
    ChatSqlRelationshipResolverService,
)
from app.domain.services.chat_sql_review_service import ChatSqlReviewService
from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService
from app.domain.services.chat_sql_schema_discovery_service import (
    ChatSqlSchemaDiscoveryService,
)
from app.domain.services.chat_sql_semantic_schema_mapper_service import (
    ChatSqlSemanticSchemaMapperService,
)
from tests.fixtures.advanced_sql_specialist_regression_cases import (
    ADVANCED_SQL_SPECIALIST_REGRESSION_CASES,
)


def _ctx():
    return {"skills": {"sqlAuthoring": True}}


def _ctx_with_actions():
    return {
        "skills": {"sqlAuthoring": True},
        "actionsEnabled": True,
        "allowedActionIds": ["system-columns"],
    }


def _history_with_sql(sql: str) -> list[dict]:
    return [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"path": "/data/sql", "ok": True},
                        "arguments": {"sql": sql},
                    }
                ]
            },
        }
    ]


@pytest.mark.parametrize("case", ADVANCED_SQL_SPECIALIST_REGRESSION_CASES, ids=lambda c: c["id"])
def test_advanced_sql_specialist_regression(case: dict):
    case_id = case["id"]
    message = case.get("message")
    history = _history_with_sql(case["history_sql"]) if case.get("history_sql") else None

    if case.get("mode"):
        mode = ChatAdvancedSqlSpecialistService.classify_mode(message, previous_messages=history)
        assert mode == case["mode"], f"{case_id}: modo {mode}"

    if case.get("activate") is True:
        assert ChatAdvancedSqlSpecialistService.should_activate(message, workspace_context=_ctx())

    if case.get("dialect"):
        resolved = ChatSqlDialectResolverService.resolve(message)
        assert resolved["dialect"] == case["dialect"]
        assert resolved["assumed"] is case.get("assumed", False)

    if case.get("planner_hint"):
        hints = ChatAdvancedSqlSpecialistService.build_planner_hints(message)
        assert case["planner_hint"] in hints, f"{case_id}: hints {hints}"

    if case.get("blocked"):
        snapshot = ChatAdvancedSqlSpecialistService.build_pipeline_snapshot(
            message=message,
            workspace_context=_ctx(),
        )
        assert snapshot and snapshot["blocked"] is True

    if case.get("performance_code"):
        analysis = ChatSqlPerformanceAdvisorService.analyze(case["sql"])
        codes = {item["code"] for item in analysis["issues"]}
        assert case["performance_code"] in codes

    if case.get("prefetch_schema"):
        assert ChatAdvancedSqlSpecialistService.should_prefetch_schema(
            message=message,
            workspace_context=_ctx_with_actions(),
        )

    if case.get("duplicate_risk"):
        resolution = ChatSqlRelationshipResolverService.resolve(
            message=message,
            table_candidates=case.get("tables"),
        )
        assert resolution["duplicateRisks"], f"{case_id}: esperava risco de duplicidade"

    if case.get("sql") and case_id == "SQL17":
        review = ChatSqlReviewService.review(case["sql"])
        assert review["riskLevel"] in {"low", "medium", "high"}
        assert len(review["checklist"]) >= 2

    if case.get("semantic_term"):
        mapping = ChatSqlSemanticSchemaMapperService.map_message(message)
        terms = {item["term"] for item in mapping["matches"]}
        assert case["semantic_term"] in terms

    if case_id == "SQL11":
        assert ChatSqlSafetyService.contains_destructive_sql(message)
