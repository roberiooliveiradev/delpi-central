"""Multiserver inventory/health tools: isolated unit tests with MockTransport."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest

from linux_ops_mcp.diagnosis import analyze_observation, classify_os_family
from linux_ops_mcp.multiserver import (
    get_infrastructure_health,
    get_server_health,
    get_server_services,
    list_servers,
    resolve_server,
)
from linux_ops_mcp.reader import ItPortalReader, ReadError, Settings, host_health, deployment_revision
from linux_ops_mcp import server as mcp_server


def _settings(**kwargs):
    base = {
        "upstream_base_url": "http://it-portal-api:8000",
        "server_id": str(uuid4()),
        "stale_after_hours": 36.0,
        "infra_concurrency": 4,
        "infra_max_servers": 500,
    }
    base.update(kwargs)
    return Settings(**base)


def _linux_obs(server_id: str, **overrides):
    body = {
        "source": "linux_host_collector",
        "server_id": server_id,
        "schema_version": "1",
        "status": "complete",
        "presentation_status": "available",
        "observed_at": "2026-11-18T12:00:00Z",
        "sections_status": {
            "identity": "ok", "os": "ok", "memory": "ok", "volumes": "ok",
            "nics": "ok", "systemd": "ok", "docker": "ok",
        },
        "summary": {
            "os": {"name": "Ubuntu", "version": "24.04"},
            "cpu_logical": 8,
            "memory": {"total_bytes": 16_000_000_000, "available_bytes": 8_000_000_000},
            "volumes": [{
                "mount_point": "/", "size_bytes": 100_000_000_000,
                "used_bytes": 40_000_000_000, "available_bytes": 60_000_000_000,
            }],
            "systemd_services": [
                {"name": "docker.service", "active_state": "active"},
                {"name": "ssh.service", "active_state": "active"},
            ],
        },
    }
    body.update(overrides)
    return body


def _windows_obs(server_id: str, **overrides):
    body = {
        "source": "windows_host_collector",
        "server_id": server_id,
        "schema_version": "1",
        "status": "complete",
        "presentation_status": "available",
        "observed_at": "2026-11-18T12:00:00Z",
        "sections_status": {
            "identity": "ok", "os": "ok", "cpu": "ok", "memory": "ok",
            "volumes": "ok", "nics": "ok", "windows_services": "ok",
        },
        "summary": {
            "os": {"name": "Microsoft Windows Server 2019 Standard", "version": "10.0.17763"},
            "cpu_logical": 8,
            "cpu_usage_percent": 33.0,
            "uptime_seconds": 1000,
            "memory": {"total_bytes": 32_000_000_000, "available_bytes": 10_000_000_000},
            "volumes": [{
                "mount_point": "C:", "size_bytes": 200_000_000_000,
                "available_bytes": 50_000_000_000, "used_percent": 75.0,
            }],
            "windows_services": [{"name": "EventLog", "active_state": "running"}],
        },
    }
    body.update(overrides)
    return body


def _server(server_id: str, hostname: str, **overrides):
    row = {
        "id": server_id,
        "name": hostname.upper(),
        "hostname": hostname,
        "operating_system": "Ubuntu 24.04",
        "unit_code": "TI",
        "environment": "prod",
        "criticality": "high",
        "administrative_status": "in_operation",
        "archived": False,
    }
    row.update(overrides)
    return row


def _envelope(data):
    return {"data": data}


def test_classify_os_family():
    assert classify_os_family("Windows Server 2019") == "windows"
    assert classify_os_family("Ubuntu 24.04") == "linux"
    assert classify_os_family(None, "windows_host_collector") == "windows"


def test_list_servers_multiple_and_pagination_beyond_25():
    servers = [_server(str(uuid4()), f"host-{i:03d}.delpi.local") for i in range(40)]

    def respond(request: httpx.Request):
        assert request.url.path == "/servers"
        page = int(request.url.params.get("page", "1"))
        page_size = int(request.url.params.get("page_size", "25"))
        start = (page - 1) * page_size
        end = start + page_size
        return httpx.Response(200, json=_envelope({
            "items": servers[start:end],
            "total": len(servers),
            "page": page,
            "page_size": page_size,
        }))

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))
        page1 = await list_servers(reader, "Bearer test-user-token", page=1, page_size=25)
        page2 = await list_servers(reader, "Bearer test-user-token", page=2, page_size=25)
        assert page1["total"] == 40
        assert len(page1["items"]) == 25
        assert len(page2["items"]) == 15
        assert page2["items"][0]["hostname"] == "host-025.delpi.local"

    asyncio.run(scenario())


def test_linux_and_windows_server_health():
    linux_id, windows_id = str(uuid4()), str(uuid4())

    def respond(request: httpx.Request):
        path = request.url.path
        if path.endswith(f"/servers/{linux_id}"):
            return httpx.Response(200, json=_envelope(_server(linux_id, "srv-linux-01")))
        if path.endswith(f"/servers/{windows_id}"):
            return httpx.Response(200, json=_envelope(_server(
                windows_id, "srv-win-01", operating_system="Windows Server 2019",
            )))
        if path.endswith(f"/servers/{linux_id}/observations/latest"):
            return httpx.Response(200, json=_envelope(_linux_obs(linux_id)))
        if path.endswith(f"/servers/{windows_id}/observations/latest"):
            return httpx.Response(200, json=_envelope(_windows_obs(windows_id)))
        return httpx.Response(404, json={"data": {"error": "missing"}})

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))
        linux = await get_server_health(reader, "Bearer test-user-token", server_id=linux_id)
        windows = await get_server_health(reader, "Bearer test-user-token", server_id=windows_id)
        assert linux["ok"] if False else linux["observation_source"] == "linux_host_collector"
        assert linux["health_status"] == "healthy"
        assert windows["observation_source"] == "windows_host_collector"
        assert windows["cpu_usage_percent"] == 33.0
        assert windows["uptime_seconds"] == 1000

    asyncio.run(scenario())


def test_resolve_uuid_hostname_ambiguous_and_missing():
    shared = "duplicated.delpi.local"
    a, b, unique = str(uuid4()), str(uuid4()), str(uuid4())
    inventory = [
        _server(a, shared, name="A"),
        _server(b, shared, name="B"),
        _server(unique, "unique.delpi.local"),
    ]

    def respond(request: httpx.Request):
        if request.url.path == "/servers":
            q = (request.url.params.get("q") or "").lower()
            items = [row for row in inventory if q in row["hostname"].lower() or not q]
            return httpx.Response(200, json=_envelope({
                "items": items, "total": len(items), "page": 1, "page_size": 100,
            }))
        if request.url.path.endswith(f"/servers/{unique}"):
            return httpx.Response(200, json=_envelope(inventory[2]))
        return httpx.Response(404, json={"data": None})

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))
        by_id = await resolve_server(reader, "Bearer test-user-token", server_id=unique)
        assert by_id["hostname"] == "unique.delpi.local"
        by_host = await resolve_server(
            reader, "Bearer test-user-token", hostname="unique.delpi.local",
        )
        assert by_host["id"] == unique
        with pytest.raises(ReadError, match="ambiguous_hostname"):
            await resolve_server(reader, "Bearer test-user-token", hostname=shared)
        with pytest.raises(ReadError, match="server_not_found"):
            await resolve_server(reader, "Bearer test-user-token", hostname="missing.local")
        ambiguous = await get_server_health(
            reader, "Bearer test-user-token", hostname=shared,
        )
        assert ambiguous["ok"] is False
        assert ambiguous["error"] == "ambiguous_hostname"
        assert len(ambiguous["candidates"]) == 2

    asyncio.run(scenario())


def test_archived_without_flag_and_no_observation():
    server_id = str(uuid4())

    def respond(request: httpx.Request):
        if request.url.path.endswith(f"/servers/{server_id}"):
            return httpx.Response(200, json=_envelope(_server(
                server_id, "archived.delpi.local", archived=True,
            )))
        if request.url.path.endswith("/observations/latest"):
            return httpx.Response(200, json=_envelope(None))
        return httpx.Response(404)

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))
        with pytest.raises(ReadError, match="server_archived"):
            await get_server_health(reader, "Bearer test-user-token", server_id=server_id)
        allowed = await get_server_health(
            reader, "Bearer test-user-token", server_id=server_id, include_archived=True,
        )
        assert allowed["collection_status"] == "unavailable"
        assert allowed["overall_status"] == "no_data"
        assert allowed["health_status"] == "unknown"

    asyncio.run(scenario())


def test_stale_partial_missing_cpu_and_high_volume():
    server_id = str(uuid4())
    now = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
    stale_at = (now - timedelta(hours=48)).isoformat().replace("+00:00", "Z")
    partial = _linux_obs(
        server_id,
        status="partial",
        presentation_status="partial",
        observed_at=now.isoformat().replace("+00:00", "Z"),
        summary={
            "os": {"name": "Ubuntu", "version": "24.04"},
            "cpu_logical": 4,
            "memory": {"total_bytes": 8_000_000_000, "available_bytes": 4_000_000_000},
            "volumes": [],
            "systemd_services": [],
        },
    )
    stale = _linux_obs(server_id, observed_at=stale_at, presentation_status="stale")
    no_cpu = _windows_obs(
        server_id,
        summary={
            "os": {"name": "Windows Server", "version": "10"},
            "cpu_logical": 8,
            "memory": {"total_bytes": 8_000_000_000, "available_bytes": 100_000_000},
            "volumes": [{
                "mount_point": "D:", "size_bytes": 100, "available_bytes": 1, "used_percent": 97.5,
            }],
            "windows_services": [],
        },
    )
    assert "cpu_usage_percent" not in no_cpu["summary"]
    analyzed_partial = analyze_observation(partial, server=_server(server_id, "h1"), now=now)
    analyzed_stale = analyze_observation(stale, server=_server(server_id, "h1"), now=now)
    analyzed_disk = analyze_observation(no_cpu, server=_server(server_id, "h1"), now=now)
    assert analyzed_partial["collection_status"] == "partial"
    assert analyzed_stale["collection_status"] == "stale"
    assert analyzed_disk["cpu_usage_percent"] is None
    assert any(issue["code"] == "volume_critical" for issue in analyzed_disk["issues"])
    assert analyzed_disk["health_status"] == "critical"


def test_windows_critical_stopped_and_linux_inactive_service():
    server_id = str(uuid4())
    windows = analyze_observation(
        None,
        server=_server(server_id, "win", operating_system="Windows Server"),
    )
    assert windows["overall_status"] == "no_data"

    linux = analyze_observation(_linux_obs(
        server_id,
        summary={
            "os": {"name": "Ubuntu", "version": "24.04"},
            "cpu_logical": 2,
            "memory": {"total_bytes": 1_000, "available_bytes": 500},
            "volumes": [],
            "systemd_services": [
                {"name": "docker.service", "active_state": "inactive"},
            ],
        },
    ), server=_server(server_id, "linux"))
    assert linux["health_status"] == "attention"
    assert any(issue["code"] == "service_not_active" for issue in linux["issues"])


def test_infrastructure_health_isolates_single_failure():
    ok_id, bad_id = str(uuid4()), str(uuid4())
    inventory = [
        _server(ok_id, "ok.delpi.local"),
        _server(bad_id, "bad.delpi.local"),
    ]

    def respond(request: httpx.Request):
        if request.url.path == "/servers":
            return httpx.Response(200, json=_envelope({
                "items": inventory, "total": 2, "page": 1, "page_size": 100,
            }))
        if request.url.path.endswith(f"/servers/{ok_id}/observations/latest"):
            return httpx.Response(200, json=_envelope(_linux_obs(ok_id)))
        if request.url.path.endswith(f"/servers/{bad_id}/observations/latest"):
            return httpx.Response(503, json={"secret": "DO_NOT_LEAK"})
        return httpx.Response(404)

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))
        result = await get_infrastructure_health(reader, "Bearer test-user-token")
        assert result["totals"]["servers"] == 2
        assert result["totals"]["with_observation"] == 1
        assert result["totals"]["without_observation"] == 1
        statuses = {row["hostname"]: row["collection_status"] for row in result["servers"]}
        assert statuses["ok.delpi.local"] == "available"
        assert statuses["bad.delpi.local"] == "failed_read"
        assert "DO_NOT_LEAK" not in str(result)

    asyncio.run(scenario())


def test_upstream_unavailable_and_malformed():
    def unavailable(_request):
        raise httpx.ConnectError("boom")

    def malformed(_request):
        return httpx.Response(200, json={"nope": True})

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(unavailable))
        with pytest.raises(ReadError, match="upstream_unavailable"):
            await list_servers(reader, "Bearer test-user-token")
        reader2 = ItPortalReader(_settings(), transport=httpx.MockTransport(malformed))
        with pytest.raises(ReadError, match="malformed_upstream_response"):
            await list_servers(reader2, "Bearer test-user-token")

    asyncio.run(scenario())


def test_auth_negatives_for_multiread(monkeypatch):
    monkeypatch.setattr(
        mcp_server,
        "require_mcp_context",
        lambda: type("C", (), {
            "user": type("U", (), {
                "id": "user-id", "principal_type": "user", "rbac_unavailable": False,
            })(),
            "authorization": "Bearer test-user-token",
        })(),
    )

    async def denied(_token, *, force_refresh=False):
        return {"id": "user-id", "permissions": ["it-portal.access"], "is_superadmin": False}

    monkeypatch.setattr(mcp_server, "load_user_rbac", denied)

    async def scenario():
        result = await mcp_server._multiread(lambda *_: {"x": 1})
        assert result == {"ok": False, "error": "forbidden"}

    asyncio.run(scenario())


def test_server_services_windows_and_linux():
    linux_id, windows_id = str(uuid4()), str(uuid4())

    def respond(request: httpx.Request):
        path = request.url.path
        if path.endswith(f"/servers/{linux_id}"):
            return httpx.Response(200, json=_envelope(_server(linux_id, "srv-linux")))
        if path.endswith(f"/servers/{windows_id}"):
            return httpx.Response(200, json=_envelope(_server(
                windows_id, "srv-win", operating_system="Windows Server 2022",
            )))
        if path.endswith(f"/servers/{linux_id}/observations/latest"):
            return httpx.Response(200, json=_envelope(_linux_obs(
                linux_id,
                summary={
                    "os": {"name": "Ubuntu", "version": "24.04"},
                    "cpu_logical": 2,
                    "memory": {"total_bytes": 1000, "available_bytes": 400},
                    "volumes": [],
                    "systemd_services": [
                        {"name": "nginx.service", "active_state": "inactive"},
                        {"name": "docker.service", "active_state": "active"},
                    ],
                },
            )))
        if path.endswith(f"/servers/{windows_id}/host-services"):
            return httpx.Response(200, json=_envelope({
                "items": [{
                    "service_key": "sql",
                    "name": "SQLSERVER",
                    "display_name": "SQL Server",
                    "state": "stopped",
                    "start_mode": "auto",
                    "is_favorite": True,
                    "criticality": "critical",
                    "is_present": True,
                    "observed_at": "2026-11-18T12:00:00Z",
                }],
                "total": 1,
                "page": 1,
                "page_size": 25,
                "favorites_count": 1,
            }))
        return httpx.Response(404)

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))
        linux = await get_server_services(
            reader, "Bearer test-user-token", server_id=linux_id, state="inactive",
        )
        assert linux["service_source"] == "observation_systemd_allowlist"
        assert linux["items"][0]["name"] == "nginx.service"
        windows = await get_server_services(
            reader, "Bearer test-user-token", server_id=windows_id, critical_only=True,
        )
        assert windows["service_source"] == "it-portal-host-services"
        assert windows["attention_items"][0]["criticality"] == "critical"

    asyncio.run(scenario())


def test_legacy_tools_still_reject_windows_and_keep_revision_contract():
    obs = _windows_obs(str(uuid4()))
    with pytest.raises(ReadError, match="unexpected_observation_source"):
        host_health(obs)
    linux = _linux_obs(str(uuid4()))
    rev = deployment_revision(linux)
    assert rev["revision"] is None
    assert rev["status"] == "not_available"


def test_read_tools_allowlist_contains_new_and_legacy():
    expected = {
        "get_host_health", "list_managed_services", "get_service_health",
        "get_deployment_revision", "list_servers", "get_server_health",
        "get_infrastructure_health", "get_server_services",
    }
    assert mcp_server.READ_TOOLS == frozenset(expected)


def test_no_write_or_shell_markers_in_new_modules():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "linux_ops_mcp"
    for name in ("diagnosis.py", "multiserver.py", "server.py", "reader.py"):
        text = (root / name).read_text(encoding="utf-8")
        for forbidden in ("subprocess", "docker.sock", "paramiko", "/bin/sh", "os.system"):
            assert forbidden not in text
