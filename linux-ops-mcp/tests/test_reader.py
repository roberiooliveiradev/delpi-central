"""Isolated unit tests: no server, API, network, Docker or privileged access."""
import asyncio
from uuid import uuid4

import httpx
import pytest

from linux_ops_mcp.reader import (
    ItPortalReader, ReadError, Settings, deployment_revision, host_health,
    managed_services, service_health,
)

SERVER_ID = str(uuid4())


def observation():
    return {
        "source": "linux_host_collector",
        "server_id": SERVER_ID,
        "schema_version": "1",
        "presentation_status": "available",
        "observed_at": "2026-11-14T23:00:00Z",
        "sections_status": {"memory": "ok", "docker": "partial", "systemd": "ok"},
        "summary": {
            "cpu_logical": 16,
            "memory": {"total_bytes": 47000000000, "available_bytes": 25000000000},
            "swap": {"total_bytes": 8000000000, "free_bytes": 8000000000},
            "volumes": [{"mount_point": "/", "size_bytes": 400000000000,
                         "used_bytes": 180000000000, "available_bytes": 220000000000}],
            "systemd_services": [
                {"name": "docker.service", "active_state": "active", "sub_state": "running"},
                {"name": "secret-db.service", "active_state": "active"},
            ],
            "docker_summary": {
                "available": True, "containers_running": 135, "containers_total": 138,
                "container_names_sample": ["secret-internal-db"],
                "sensitive_debug": {"password": "must-not-escape"},
            },
            "identity": {"hostname": "internal", "machine_id": "SECRET"},
            "host_nics": [{"name": "eno1", "address": "PRIVATE"}],
        },
    }


def test_projections_deny_unknown_keys_and_identifiers():
    obs = observation()
    a, b = host_health(obs), managed_services(obs)
    assert a["cpu_logical"] == 16
    assert a["memory"]["available_bytes"] == 25000000000
    assert b["docker"]["containers_running"] == 135
    assert b["systemd_services"] == [{"name": "docker.service", "active_state": "active"}]
    assert "secret" not in str((a, b)).lower()
    assert "machine_id" not in str((a, b))
    assert "eno1" not in str((a, b))
    assert service_health(obs, "docker.service")["health"] == "active"


def test_fails_closed_on_other_observation_schema():
    obs = observation()
    obs["source"] = "windows_host_collector"
    with pytest.raises(ReadError, match="unexpected_observation_source"):
        host_health(obs)


def test_denies_unallowlisted_services():
    with pytest.raises(ReadError, match="service_not_allowlisted"):
        service_health(observation(), "sshd;rm -rf /")


def test_no_observation_not_equal_healthy():
    assert host_health(None)["observation_status"] == "unavailable"
    assert service_health(None, "docker.service")["health"] == "unknown"


def test_revision_not_fabricated_from_git_head():
    result = deployment_revision(observation())
    assert result["revision"] is None
    assert result["status"] == "not_available"


def test_settings_require_uuid_and_fixed_internal_url(monkeypatch):
    monkeypatch.setenv("LINUX_OPS_SERVER_ID", SERVER_ID)
    monkeypatch.setenv("LINUX_OPS_IT_PORTAL_URL", "http://169.254.169.254")
    with pytest.raises(ReadError, match="upstream_not_configured"):
        Settings.from_environment()
    monkeypatch.setenv("LINUX_OPS_IT_PORTAL_URL", "http://it-portal-api:8000")
    assert Settings.from_environment().server_id == SERVER_ID


def test_reader_forwards_user_bearer_only_to_fixed_endpoint():
    async def scenario():
        calls = []
        def respond(req):
            calls.append((str(req.url), req.headers.get("Authorization")))
            return httpx.Response(200, json={"data": observation()})
        reader = ItPortalReader(
            Settings("http://it-portal-api:8000", SERVER_ID),
            transport=httpx.MockTransport(respond),
        )
        out = await reader.latest("Bearer test-user-token")
        assert out["source"] == "linux_host_collector"
        assert calls == [(
            f"http://it-portal-api:8000/servers/{SERVER_ID}/observations/latest",
            "Bearer test-user-token",
        )]
    asyncio.run(scenario())


@pytest.mark.parametrize("status,expected", [
    (401, "upstream_authorization_denied"),
    (403, "upstream_authorization_denied"),
    (404, "server_not_found"),
    (503, "upstream_unavailable"),
])
def test_upstream_errors_fail_closed(status, expected):
    async def scenario():
        reader = ItPortalReader(
            Settings("http://it-portal-api:8000", SERVER_ID),
            transport=httpx.MockTransport(lambda _: httpx.Response(
                status, text='{"secret":"DO_NOT_LEAK"}')),
        )
        with pytest.raises(ReadError, match=expected) as error:
            await reader.latest("Bearer test-user-token")
        assert "DO_NOT_LEAK" not in str(error.value)
    asyncio.run(scenario())


def test_upstream_data_contract_rejected():
    async def scenario():
        reader = ItPortalReader(
            Settings("http://it-portal-api:8000", SERVER_ID),
            transport=httpx.MockTransport(lambda _: httpx.Response(
                200, json={"data": {"source": "malicious_source"}})),
        )
        with pytest.raises(ReadError, match="unexpected_observation_source"):
            await reader.latest("Bearer test-user-token")
    asyncio.run(scenario())


def test_reader_rejects_other_server_observation():
    async def scenario():
        other = observation()
        other["server_id"] = str(uuid4())
        reader = ItPortalReader(
            Settings("http://it-portal-api:8000", SERVER_ID),
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"data": other})),
        )
        with pytest.raises(ReadError, match="unexpected_observation_server"):
            await reader.latest("Bearer test-user-token")
    asyncio.run(scenario())


def test_settings_normalize_uppercase_uuid(monkeypatch):
    monkeypatch.setenv("LINUX_OPS_SERVER_ID", SERVER_ID.upper())
    monkeypatch.setenv("LINUX_OPS_IT_PORTAL_URL", "http://it-portal-api:8000")
    assert Settings.from_environment().server_id == SERVER_ID
