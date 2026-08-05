"""Testes do gateway Kimi — geração de seções de ata (HTTP mockado)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from tm_app.infrastructure.llm.kimi_llm_gateway import (
    REQUIRED_SECTION_KEYS,
    AtaGenerationError,
    KimiLlmGateway,
)


def _ok_sections() -> dict[str, str]:
    return {key: f"<p>{key}</p>" for key in REQUIRED_SECTION_KEYS}


def _mock_response(*, status: int = 200, payload: dict | None = None, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.text = text
    if payload is not None:
        response.json.return_value = payload
    else:
        response.json.side_effect = ValueError("not json")
    return response


def test_generate_from_transcript_ok():
    sections = _ok_sections()
    envelope = {
        "choices": [{"message": {"content": json.dumps(sections, ensure_ascii=False)}}],
    }
    gateway = KimiLlmGateway(api_key="test-key", base_url="https://example.test/v1", model="kimi")

    with patch(
        "tm_app.infrastructure.llm.kimi_llm_gateway.requests.post",
        return_value=_mock_response(payload=envelope),
    ) as post:
        result = gateway.generate_from_transcript("<p>Transcrição de teste</p>")

    assert result == sections
    assert post.call_args.kwargs["json"]["response_format"] == {"type": "json_object"}
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"


def test_generate_strips_markdown_fences():
    sections = _ok_sections()
    fenced = "```json\n" + json.dumps(sections) + "\n```"
    envelope = {"choices": [{"message": {"content": fenced}}]}
    gateway = KimiLlmGateway(api_key="k", base_url="https://example.test/v1")

    with patch(
        "tm_app.infrastructure.llm.kimi_llm_gateway.requests.post",
        return_value=_mock_response(payload=envelope),
    ):
        result = gateway.generate_from_transcript("texto")

    assert result["agenda_html"] == sections["agenda_html"]


def test_missing_api_key_raises():
    gateway = KimiLlmGateway(api_key="", base_url="https://example.test/v1")
    with pytest.raises(AtaGenerationError, match="KIMI_API_KEY"):
        gateway.generate_from_transcript("conteúdo")


def test_empty_transcript_raises():
    gateway = KimiLlmGateway(api_key="k")
    with pytest.raises(AtaGenerationError, match="vazia"):
        gateway.generate_from_transcript("   ")


def test_http_error_raises_ata_generation_error():
    gateway = KimiLlmGateway(api_key="k", base_url="https://example.test/v1")
    with patch(
        "tm_app.infrastructure.llm.kimi_llm_gateway.requests.post",
        return_value=_mock_response(status=502, text="bad gateway", payload={"error": "x"}),
    ):
        with pytest.raises(AtaGenerationError, match="HTTP 502"):
            gateway.generate_from_transcript("texto")


def test_timeout_via_connection_error_raises_timeout_message():
    gateway = KimiLlmGateway(api_key="k", base_url="https://example.test/v1")
    with patch(
        "tm_app.infrastructure.llm.kimi_llm_gateway.requests.post",
        side_effect=requests.ConnectionError(
            "HTTPSConnectionPool(host='openrouter.ai', port=443): Read timed out."
        ),
    ):
        with pytest.raises(AtaGenerationError, match="Timeout"):
            gateway.generate_from_transcript("texto")


def test_long_transcript_is_capped_before_request():
    sections = _ok_sections()
    envelope = {
        "choices": [{"message": {"content": json.dumps(sections, ensure_ascii=False)}}],
    }
    gateway = KimiLlmGateway(
        api_key="k",
        base_url="https://example.test/v1",
        max_transcript_chars=50,
    )
    long_html = "<p>" + ("x" * 200) + "</p>"

    with patch(
        "tm_app.infrastructure.llm.kimi_llm_gateway.requests.post",
        return_value=_mock_response(payload=envelope),
    ) as post:
        gateway.generate_from_transcript(long_html)

    user_content = post.call_args.kwargs["json"]["messages"][1]["content"]
    assert "truncada para geração por IA" in user_content
    assert "<p>" not in user_content  # texto puro, sem HTML da transcrição
    assert len(user_content) < len(long_html) + 200


def test_html_is_stripped_to_plain_text():
    sections = _ok_sections()
    envelope = {
        "choices": [{"message": {"content": json.dumps(sections, ensure_ascii=False)}}],
    }
    gateway = KimiLlmGateway(api_key="k", base_url="https://example.test/v1")
    with patch(
        "tm_app.infrastructure.llm.kimi_llm_gateway.requests.post",
        return_value=_mock_response(payload=envelope),
    ) as post:
        gateway.generate_from_transcript("<p>Bruno <strong>sugeriu</strong> checklist.</p>")

    user_content = post.call_args.kwargs["json"]["messages"][1]["content"]
    assert "Bruno sugeriu checklist." in user_content
    assert "<strong>" not in user_content
    assert post.call_args.kwargs["json"]["max_tokens"] == 4096


def test_table_cells_are_separated_in_plain_text():
    """Evita 'GrupoInformações' ao enviar grades do editor/DOCX para a IA."""
    sections = _ok_sections()
    envelope = {
        "choices": [{"message": {"content": json.dumps(sections, ensure_ascii=False)}}],
    }
    gateway = KimiLlmGateway(api_key="k", base_url="https://example.test/v1")
    html = (
        "<table><tr><th>Grupo</th><th>Informações</th></tr>"
        "<tr><td>Resultado</td><td>ROL</td></tr></table>"
    )
    with patch(
        "tm_app.infrastructure.llm.kimi_llm_gateway.requests.post",
        return_value=_mock_response(payload=envelope),
    ) as post:
        gateway.generate_from_transcript(html)

    user_content = post.call_args.kwargs["json"]["messages"][1]["content"]
    assert "GrupoInformações" not in user_content.replace(" ", "")
    assert "Grupo" in user_content and "Informações" in user_content
    assert "|" in user_content


def test_malformed_model_json_raises():
    envelope = {"choices": [{"message": {"content": "não é json {"}}]}
    gateway = KimiLlmGateway(api_key="k", base_url="https://example.test/v1")
    with patch(
        "tm_app.infrastructure.llm.kimi_llm_gateway.requests.post",
        return_value=_mock_response(payload=envelope),
    ):
        with pytest.raises(AtaGenerationError, match="malformado"):
            gateway.generate_from_transcript("texto")


def test_missing_section_keys_raises():
    envelope = {"choices": [{"message": {"content": json.dumps({"agenda_html": "<p>x</p>"})}}]}
    gateway = KimiLlmGateway(api_key="k", base_url="https://example.test/v1")
    with patch(
        "tm_app.infrastructure.llm.kimi_llm_gateway.requests.post",
        return_value=_mock_response(payload=envelope),
    ):
        with pytest.raises(AtaGenerationError, match="faltam chaves"):
            gateway.generate_from_transcript("texto")
