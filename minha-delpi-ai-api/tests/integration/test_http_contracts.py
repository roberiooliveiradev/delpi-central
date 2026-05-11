import os

import pytest
import requests


BASE_URL = os.getenv("INTEGRATION_BASE_URL", "http://gateway")
TOKEN = os.getenv("INTEGRATION_TOKEN", "")


def api_url(path: str) -> str:
    return f"{BASE_URL}/apps/minha-delpi-ai/api{path}"


def auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }


def require_token():
    if not TOKEN:
        pytest.skip("INTEGRATION_TOKEN is not set")


def test_healthcheck_is_public_and_returns_ok():
    response = requests.get(api_url("/health"), timeout=10)

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "minha-delpi-ai-api"


def test_chat_sessions_without_token_returns_401_or_403():
    response = requests.get(api_url("/chat/sessions"), timeout=10)

    assert response.status_code in {401, 403}
    payload = response.json()

    assert "errors" in payload
    assert isinstance(payload["errors"], list)


def test_admin_llm_status_without_token_returns_401_or_403():
    response = requests.get(api_url("/admin/llm/status"), timeout=10)

    assert response.status_code in {401, 403}
    payload = response.json()

    assert "errors" in payload
    assert isinstance(payload["errors"], list)


def test_knowledge_ingestion_invalid_input_returns_standard_error():
    require_token()

    response = requests.post(
        api_url("/knowledge/documents"),
        headers=auth_headers(),
        json={
            "title": "",
            "sourceType": "manual",
            "content": "Teste",
        },
        timeout=30,
    )

    assert response.status_code == 400
    payload = response.json()

    assert payload["errors"][0]["code"] == "knowledge.invalid_input"
    assert payload["errors"][0]["message"] == "title is required"
    assert payload["errors"][0]["path"] == "_global"


def test_unknown_tool_returns_standard_404_error():
    require_token()

    response = requests.post(
        api_url("/tools/execute"),
        headers=auth_headers(),
        json={
            "tool": "drop_database",
            "arguments": {},
        },
        timeout=30,
    )

    assert response.status_code == 404
    payload = response.json()

    assert payload["errors"][0]["code"] == "tool.not_found"
    assert payload["errors"][0]["path"] == "_global"


def test_admin_llm_status_with_token_returns_provider_metadata():
    require_token()

    response = requests.get(
        api_url("/admin/llm/status"),
        headers=auth_headers(),
        timeout=10,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["provider"] in {"ollama", "vllm"}
    assert isinstance(payload["model"], str)
    assert "maxTokens" in payload
    assert "temperature" in payload
