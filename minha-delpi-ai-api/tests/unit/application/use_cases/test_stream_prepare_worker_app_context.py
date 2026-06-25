"""Regressão: preparação do stream em thread exige app_context Flask."""

from unittest.mock import MagicMock

import pytest
from flask import Flask, has_app_context

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from tests.support.chat_intelligence_runtime import patch_resolve_chat_intelligence_runtime
from tests.unit.application.use_cases.test_chat_assistant_identity_stream_and_send import (
    _build_use_cases,
    _collect_stream_answer,
    patch_chat_settings,
    patch_llm_cost,
)


@pytest.fixture(autouse=True)
def patch_intelligence_runtime(monkeypatch):
    patch_resolve_chat_intelligence_runtime(monkeypatch)


@pytest.fixture(autouse=True)
def _settings(patch_chat_settings, patch_llm_cost, patch_intelligence_runtime):
    return None


def test_stream_prepare_history_runs_inside_app_context():
    flask_app = Flask(__name__)
    context_flags: dict[str, bool] = {}

    session, _, stream_use_case, _, llm_gateway = _build_use_cases(common=True)
    llm_gateway.stream.return_value = iter(["Olá!"])

    chat_history_summary_service = MagicMock()

    def _prepare_history(_messages):
        context_flags["has_app_context"] = has_app_context()
        return "", []

    chat_history_summary_service.prepare_history.side_effect = _prepare_history
    stream_use_case.turn_support.chat_history_summary_service = chat_history_summary_service

    request = SendChatMessageRequest(
        user_id=str(session.user_id),
        session_id=str(session.id),
        message="olá",
        access_token=None,
    )

    with flask_app.app_context():
        events = list(stream_use_case.stream(request))

    assert context_flags.get("has_app_context") is True
    assert _collect_stream_answer(events).strip()
