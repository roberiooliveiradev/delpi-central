"""Smoke de assertividade contextual (Fase 5 — CI)."""

from tests.fixtures.chat_intelligence_regression_cases import CONTEXT_ASSERTIVENESS_CASES

from app.domain.services.chat_context_assertiveness_service import (
    ChatContextAssertivenessService,
)


def test_context_assertiveness_regression_cases():
    for case in CONTEXT_ASSERTIVENESS_CASES:
        tool_calls = [
            {
                "name": "execute_external_action",
                "metadata": {"path": path, "ok": True},
            }
            for path in case.get("tool_paths") or []
        ]

        result = ChatContextAssertivenessService.evaluate_turn(
            message=case["message"],
            answer=case.get("answer") or "",
            tool_calls=tool_calls,
            snapshot=case.get("snapshot") or {},
        )

        for flag in case.get("expected_flags") or []:
            assert flag in result["flags"], case

        if "max_score" in case:
            assert result["score"] <= case["max_score"], case

        if "min_score" in case:
            assert result["score"] >= case["min_score"], case
