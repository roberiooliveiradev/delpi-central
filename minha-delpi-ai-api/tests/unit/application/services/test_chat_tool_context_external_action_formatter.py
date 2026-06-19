import json

from app.application.services.chat_tool_context_external_action_formatter import (
    ChatToolContextExternalActionFormatter,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from app.infrastructure.config.settings import Settings
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


def test_response_preview_default_limit_uses_settings():
    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    payload = {"data": _analyser_payload_with_guide_and_inspection()}
    preview = formatter._build_response_preview(payload)

    assert Settings.CHAT_TOOL_RESPONSE_PREVIEW_MAX_CHARS == 100_000
    assert len(preview) <= Settings.CHAT_TOOL_RESPONSE_PREVIEW_MAX_CHARS
    assert json.loads(preview)


def test_response_preview_truncates_beyond_global_limit(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_TOOL_RESPONSE_PREVIEW_MAX_CHARS", 500)
    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    payload = {"data": _analyser_payload_with_guide_and_inspection()}
    preview = formatter._build_response_preview(payload)

    assert preview.endswith("\n…")
    assert len(preview) <= 503


def test_safe_metadata_stores_authorized_result_for_truncated_analyser_preview(
    monkeypatch,
):
    monkeypatch.setattr(Settings, "CHAT_TOOL_RESPONSE_PREVIEW_MAX_CHARS", 500)
    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    payload = {"data": _analyser_payload_with_guide_and_inspection()}
    safe_metadata = formatter._build_safe_tool_metadata(
        "execute_external_action",
        {"ok": True, "statusCode": 200, "path": "/products/90260140/analyser"},
        payload,
    )

    assert safe_metadata["responsePreview"].endswith("\n…")
    assert isinstance(safe_metadata.get("authorizedResult"), dict)
    assert safe_metadata["authorizedResult"]["data"]["product"]["code"] == "90260140"


def test_response_preview_respects_explicit_override():
    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    preview = formatter._build_response_preview({"padding": "x" * 200}, max_chars=80)

    assert preview.endswith("\n…")
    assert len(preview) <= 83
