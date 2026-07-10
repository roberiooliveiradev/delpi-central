"""Heartbeat OCR e timeout de stall em análise de desenho."""

import time

from app.application.services.chat_document_vision_turn_service import (
    ChatDocumentVisionTurnService,
)
from app.application.services.chat_stream_activity_service import ChatStreamActivityService


def test_document_vision_ocr_heartbeat_message():
    entry = ChatStreamActivityService.document_vision_ocr_heartbeat()

    assert entry["phase"] == "document_vision"
    assert "desenho" in entry["message"].lower()


def test_run_blocking_with_ocr_heartbeat_pulses_while_waiting(monkeypatch):
    events: list[dict] = []

    def slow_operation() -> str:
        time.sleep(0.05)
        return "ok"

    monkeypatch.setattr(
        ChatStreamActivityService,
        "ocr_heartbeat_interval_seconds",
        classmethod(lambda cls: 0.01),
    )

    result = ChatDocumentVisionTurnService._run_blocking_with_ocr_heartbeat(
        slow_operation,
        on_stream_activity=events.append,
    )

    assert result == "ok"
    assert events
    assert all(event["phase"] == "document_vision" for event in events)


def test_run_blocking_with_ocr_heartbeat_worker_runs_inside_app_context():
    from flask import Flask, has_app_context

    app = Flask(__name__)
    seen: dict[str, bool] = {}

    def operation() -> str:
        seen["in_context"] = has_app_context()
        return "ok"

    with app.app_context():
        result = ChatDocumentVisionTurnService._run_blocking_with_ocr_heartbeat(
            operation,
            on_stream_activity=lambda _entry: None,
        )

    assert result == "ok"
    assert seen["in_context"] is True
