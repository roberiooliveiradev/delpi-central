import os

import pytest
import requests


BASE_URL = os.getenv("INTEGRATION_BASE_URL", "http://localhost")
TOKEN = os.getenv("INTEGRATION_TOKEN", "")


def api_url(path: str) -> str:
    return f"{BASE_URL}/apps/minha-delpi-ai/api{path}"


def require_token():
    if not TOKEN:
        pytest.skip("INTEGRATION_TOKEN is not set")


def test_skills_catalog_without_token_returns_401_or_403():
    response = requests.get(api_url("/chat/skills"), timeout=10)

    assert response.status_code in {401, 403}


def test_skills_catalog_is_public_with_access_permission():
    require_token()

    response = requests.get(
        api_url("/chat/skills"),
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=15,
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert any(item.get("skillKey") == "sql" for item in payload)


def test_agent_skills_list_returns_bindings():
    require_token()

    agents = requests.get(
        api_url("/chat/agents"),
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=15,
    )

    assert agents.status_code == 200
    agent_list = agents.json()

    if not agent_list:
        pytest.skip("No agents available for skills binding test")

    agent_id = agent_list[0]["id"]

    response = requests.get(
        api_url(f"/chat/agents/{agent_id}/skills"),
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=15,
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert any(item.get("skillKey") == "sql" for item in payload)
