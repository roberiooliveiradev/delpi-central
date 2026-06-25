"""Regressão — commentary direct no modo Normal (dataCommentary vs directAnswer legado)."""

from __future__ import annotations

import pytest

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_response_mode_service import ChatResponseModeService
from tests.fixtures.chat_intelligence_regression_cases import (
    PROSE_COMMENTARY_DIRECT_CASES,
)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def _tool_calls(metadata: dict) -> list[dict]:
    return [
        {
            "name": "execute_external_action",
            "metadata": metadata,
        }
    ]


@pytest.mark.parametrize("case", PROSE_COMMENTARY_DIRECT_CASES, ids=lambda c: c["id"])
def test_commentary_direct_wins_over_stale_direct_answer(case: dict) -> None:
    tool_context: dict = {}
    metadata = case["tool_metadata"]

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message=case["message"],
        response_mode=case["response_mode"],
        direct_answer=case.get("stale_direct_answer"),
        skip_rag=True,
        tool_calls=_tool_calls(metadata),
        tool_context=tool_context,
        pipeline_stages=list(case.get("pipeline_stages") or []),
    )

    assert direct
    assert skip_rag is True
    assert effect == "llm_synthesis"
    assert tool_context.get("commentaryBriefDirect") is True

    lowered = direct.lower()
    for snippet in case.get("forbidden_snippets") or []:
        assert snippet.lower() not in lowered

    assert any(snippet in direct for snippet in case.get("expected_snippets") or [])
