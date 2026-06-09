"""Desembrulho do payload /analyser — ChatDrawingAnalyserPayloadService."""

import json

from app.domain.services.chat_drawing_analyser_payload_service import (
    ChatDrawingAnalyserPayloadService,
)
from tests.unit.application.use_cases.test_execute_external_action_analyser_presentation import (
    _raw_analyser_api_payload,
)
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def test_resolve_root_from_response_preview():
    payload = _analyser_payload_with_guide_and_inspection()
    tool_call = {
        "metadata": {
            "ok": True,
            "statusCode": 200,
            "path": "/products/90260140/analyser",
            "responsePreview": json.dumps({"data": payload}, ensure_ascii=False),
        }
    }

    root = ChatDrawingAnalyserPayloadService.resolve_root_from_tool_call(tool_call)

    assert root.get("product", {}).get("code") == "90260140"
    assert isinstance(root.get("guide"), dict)


def test_resolve_root_from_nested_api_envelope():
    raw = _raw_analyser_api_payload()
    tool_call = {
        "metadata": {
            "ok": True,
            "statusCode": 200,
            "responsePreview": json.dumps(raw, ensure_ascii=False),
        }
    }

    root = ChatDrawingAnalyserPayloadService.resolve_root_from_tool_call(tool_call)

    assert root.get("product", {}).get("code") == "90260148"
