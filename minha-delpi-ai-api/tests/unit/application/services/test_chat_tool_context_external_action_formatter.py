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


def test_safe_metadata_preserves_existing_data_answer_when_enrichment_skips():
    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    incoming_data_answer = {
        "summary": "PA em produção.",
        "profileKey": "factory_status",
    }
    safe_metadata = formatter._build_safe_tool_metadata(
        "execute_external_action",
        {
            "ok": False,
            "statusCode": 504,
            "path": "/products/90260140/factory-status",
            "dataAnswer": incoming_data_answer,
        },
        {"success": False, "error": "timeout"},
    )

    assert safe_metadata.get("dataAnswer") == incoming_data_answer


def test_safe_metadata_uses_friendly_preview_on_failure():
    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    safe_metadata = formatter._build_safe_tool_metadata(
        "execute_external_action",
        {
            "ok": False,
            "statusCode": 504,
            "path": "/products/90260205/factory-status",
            "error": "timeout",
        },
        {"success": False, "error": "timeout", "message": "read timed out"},
    )

    preview = str(safe_metadata.get("responsePreview") or "")
    assert "read timed out" not in preview
    assert "{" not in preview
    assert preview


def test_format_external_action_context_skips_template_linhas_when_everywhere():
    import re

    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )
    from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")
    metadata = {
        "ok": True,
        "path": "/products/90269001/stock",
        "dataOnlyPresentation": True,
        "proseDeliveryMode": "llm",
    }

    context = formatter._format_external_action_context(
        "consulta estoque",
        envelope,
        metadata,
    )

    match = re.search(r"\{[\s\S]*\}\s*$", context)
    assert match is not None
    payload = json.loads(match.group(0))
    humanized = payload.get("humanizedSummary") or {}

    assert not humanized.get("linhas")


def test_safe_metadata_supports_non_external_action_tools():
    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    safe_metadata = formatter._build_safe_tool_metadata(
        "get_allowed_routes",
        {"ok": True, "routes": ["/apps/minha-delpi-chat"]},
        [{"path": "/apps/minha-delpi-chat", "label": "Chat"}],
    )

    assert safe_metadata["ok"] is True
    assert safe_metadata["routes"] == ["/apps/minha-delpi-chat"]


def test_response_preview_respects_explicit_override():
    formatter = ChatToolContextExternalActionFormatter(ExternalActionResultPresenter())
    preview = formatter._build_response_preview({"padding": "x" * 200}, max_chars=80)

    assert preview.endswith("\n…")
    assert len(preview) <= 83
