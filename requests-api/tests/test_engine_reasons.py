"""engine.json — todas as razões conhecidas são mensagens humanas (não o código)."""

from __future__ import annotations

import json
from pathlib import Path

from requests_app.domain.services.content_loader import _engine_bundle, engine_reason

_CONTENT = (
    Path(__file__).resolve().parents[1]
    / "requests_app"
    / "content"
    / "pt-BR"
    / "engine.json"
)

_KNOWN_CODES = {
    "invalid_transition",
    "missing_field",
    "stale_version",
    "forbidden",
    "not_found",
    "type_not_found",
    "type_inactive",
    "branch_required",
    "branch_invalid",
    "branch_forbidden",
    "create_forbidden",
    "edit_forbidden",
    "idempotency_required",
    "payload_required",
    "payload_invalid",
    "lookup_forbidden",
    "lookup_upstream_unauthorized",
    "lookup_upstream_error",
    "lookup_upstream_unavailable",
    "upload_forbidden",
    "download_forbidden",
    "delete_forbidden",
    "attachment_not_found",
    "artifact_not_found",
    "artifact_required",
    "comment_required",
    "comment_media_forbidden",
    "conversation_frozen",
}


def test_engine_json_covers_known_codes():
    _engine_bundle.cache_clear()
    bundle = json.loads(_CONTENT.read_text(encoding="utf-8"))
    reasons = bundle.get("reasons") or {}
    missing = sorted(_KNOWN_CODES - set(reasons))
    assert missing == [], f"códigos sem mensagem humana: {missing}"


def test_engine_reason_never_echoes_code():
    _engine_bundle.cache_clear()
    for code in sorted(_KNOWN_CODES):
        field = "invoice_pdf" if code == "artifact_required" else (
            "return_reason" if code == "missing_field" else None
        )
        message = engine_reason(code, field=field)
        assert message != code
        assert "_" not in message or " " in message


def test_artifact_required_mentions_invoice_pdf_label():
    _engine_bundle.cache_clear()
    message = engine_reason("artifact_required", field="invoice_pdf")
    assert "PDF da nota fiscal" in message
    assert "Documentos gerados" in message
