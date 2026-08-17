"""Falha no copiloto TV não pode degradar em resposta inventada.

Na superfície TV Dashboard o usuário pediu uma mutação («crie um slide»). Se o
caminho do copiloto quebra e o turno segue para o LLM sem tool, o modelo
descreve um slide em markdown que nunca foi criado. O turno deve responder o
motivo factual.
"""

from __future__ import annotations

import pytest

from app.application.services.chat_tool_context_selection_service import (
    ChatToolContextSelectionService,
)
from app.application.services.chat_tv_dashboard_platform_tool_selection_service import (
    ChatTvDashboardPlatformToolSelectionService,
)
from app.domain.services.chat_tv_dashboard_copilot_intent_service import (
    ChatTvDashboardCopilotIntentService,
)


class _FakeToolSelectionService:
    @staticmethod
    def select_tools(*_args, **_kwargs) -> list[dict]:
        return []


class _FakeHost:
    def __init__(self, workspace_context: dict | None) -> None:
        self.native_tool_calling_service = None
        self.tool_router_service = None
        self.external_action_selection_service = None
        self.tool_selection_service = _FakeToolSelectionService()
        self._build_workspace_context = workspace_context
        self._access_token = "tok"

    @staticmethod
    def _finalize_tool_context_result(*, message, previous_messages, result) -> dict:
        return dict(result)


def _select(host) -> object:
    return ChatToolContextSelectionService().select_tools(
        host,
        message="crie um slide",
        raw_message="crie um slide",
        allowed_action_ids=None,
        actions_enabled=False,
        allowed_tool_names=None,
        conversation_context=None,
        previous_messages=None,
        max_external_action_calls=None,
        on_stream_activity=None,
        agent_context=None,
        attachment_context=None,
        drawing_analysis_mode=False,
        drawing_product_code=None,
        drawing_product_code_source=None,
        drawing_runtime_skills=None,
        drawing_pdf_extract=None,
        web_search_exclusive=False,
    )


@pytest.fixture(autouse=True)
def _broken_tv_selection(monkeypatch):
    def _explode(cls, *_args, **_kwargs):
        raise RuntimeError("planner fora do ar")

    monkeypatch.setattr(
        ChatTvDashboardPlatformToolSelectionService,
        "select",
        classmethod(_explode),
    )


def test_tv_surface_answers_factual_reason_when_copilot_path_fails():
    host = _FakeHost(
        {
            "tvDashboardHostContext": {
                "surface": "tv-dashboard",
                "playlistId": "pl-1",
            }
        }
    )

    outcome = _select(host)

    assert outcome.early_result is not None, (
        "o turno TV deve encerrar com motivo factual em vez de seguir para o LLM"
    )
    assert (
        outcome.early_result["directAnswer"]
        == ChatTvDashboardCopilotIntentService.copilot_path_failed_message()
    )
    assert outcome.early_result["toolCalls"] == []


def test_non_tv_surface_does_not_answer_with_tv_reason():
    outcome = _select(_FakeHost(None))

    direct = (outcome.early_result or {}).get("directAnswer")
    assert direct != ChatTvDashboardCopilotIntentService.copilot_path_failed_message()
