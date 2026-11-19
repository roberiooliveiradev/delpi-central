"""Multiserver inventory/health tools: isolated unit tests with MockTransport."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest

from linux_ops_mcp.diagnosis import analyze_observation, classify_os_family
from linux_ops_mcp.multiserver import (
    _FILTERED_INVENTORY_UPSTREAM_PAGE_SIZE,
    _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE,
    get_infrastructure_health,
    get_server_health,
    get_server_services,
    list_servers,
    resolve_server,
    resolve_server_or_candidates,
)
from linux_ops_mcp.reader import (
    ItPortalReader,
    MAX_UPSTREAM_BYTES,
    ReadError,
    Settings,
    deployment_revision,
    host_health,
    project_windows_host_service,
)
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


def test_list_servers_client_filter_paginates_beyond_infra_max_servers():
    """os_family filter must not silently cap inventory at LINUX_OPS_INFRA_MAX_SERVERS."""
    max_servers = 50  # low fixture ceiling; production default is 500
    windows = [
        _server(
            str(uuid4()),
            f"win-{i:04d}.delpi.local",
            operating_system="Windows Server 2022",
            administrative_status="in_operation",
        )
        for i in range(max_servers + 20)
    ]
    linux = [
        _server(str(uuid4()), f"linux-{i:03d}.delpi.local", operating_system="Ubuntu 24.04")
        for i in range(10)
    ]
    inventory = windows + linux
    assert len(windows) == 70

    def respond(request: httpx.Request):
        assert request.url.path == "/servers"
        page = int(request.url.params.get("page", "1"))
        page_size = int(request.url.params.get("page_size", "25"))
        start = (page - 1) * page_size
        end = start + page_size
        return httpx.Response(200, json=_envelope({
            "items": inventory[start:end],
            "total": len(inventory),
            "page": page,
            "page_size": page_size,
        }))

    async def scenario():
        reader = ItPortalReader(
            _settings(infra_max_servers=max_servers),
            transport=httpx.MockTransport(respond),
        )
        page1 = await list_servers(
            reader, "Bearer test-user-token", os_family="windows", page=1, page_size=25,
        )
        assert page1["total"] == 70
        assert len(page1["items"]) == 25
        assert page1["filtered_client_side"] is True
        assert page1["inventory_scanned"] == len(inventory)

        page3 = await list_servers(
            reader, "Bearer test-user-token", os_family="windows", page=3, page_size=25,
        )
        assert page3["total"] == 70
        assert len(page3["items"]) == 20
        assert page3["items"][0]["hostname"] == "win-0050.delpi.local"

        # Sibling: administrative_status filter also keeps full total (windows+linux).
        admin = await list_servers(
            reader,
            "Bearer test-user-token",
            administrative_status="in_operation",
            page=1,
            page_size=100,
        )
        assert admin["total"] == len(inventory)
        assert len(admin["items"]) == 80

        # Negative: infrastructure consolidation still applies the safe cap.
        def respond_infra(request: httpx.Request):
            path = request.url.path
            if path == "/servers":
                page = int(request.url.params.get("page", "1"))
                page_size = int(request.url.params.get("page_size", "25"))
                start = (page - 1) * page_size
                end = start + page_size
                return httpx.Response(200, json=_envelope({
                    "items": inventory[start:end],
                    "total": len(inventory),
                    "page": page,
                    "page_size": page_size,
                }))
            if path.endswith("/observations/latest"):
                return httpx.Response(200, json=_envelope(None))
            return httpx.Response(404)

        infra_reader = ItPortalReader(
            _settings(infra_max_servers=max_servers),
            transport=httpx.MockTransport(respond_infra),
        )
        infra = await get_infrastructure_health(
            infra_reader, "Bearer test-user-token", os_family="windows", page_size=100,
        )
        assert infra["scope"]["inventory_total"] == 70
        assert infra["scope"]["servers_considered"] == max_servers
        assert infra["scope"]["bounded_by_max_servers"] is True
        assert infra["servers_total"] == max_servers

    asyncio.run(scenario())


def _rich_server(i: int, *, operating_system: str, description: str) -> dict:
    return {
        **_server(
            str(uuid4()),
            f"win-{i:03d}.delpi.local",
            operating_system=operating_system,
        ),
        "description": description,
        "code": f"W{i:03d}",
        "ip_address": f"10.0.0.{i % 250}",
        "location": "datacenter",
        "server_type": "vm",
        "purpose": "erp",
        "responsible": "ti",
        "revision": 1,
        "archived_at": None,
        "archived_by_name": None,
        "open_action_count": 0,
        "created_at": "2026-11-19T00:00:00Z",
        "created_by_name": "ops",
        "updated_at": "2026-11-19T00:00:00Z",
        "updated_by_name": "ops",
    }


def test_list_servers_filtered_scan_survives_max_length_descriptions():
    """Filtered inventory scan must use UTF-8-safe upstream pages under MAX_UPSTREAM_BYTES."""
    # 4-byte code points: 4000 chars ⇒ 16000 UTF-8 bytes for description alone.
    long_description = "\U0001f600" * 4000
    assert len(long_description) == 4000
    assert len(long_description.encode("utf-8")) == 16_000
    inventory = [
        _rich_server(i, operating_system="Windows Server 2022", description=long_description)
        for i in range(120)
    ]

    oversized = json.dumps(_envelope({
        "items": inventory[:25],
        "total": len(inventory),
        "page": 1,
        "page_size": 25,
    }), ensure_ascii=False).encode("utf-8")
    assert len(oversized) > MAX_UPSTREAM_BYTES

    safe = json.dumps(_envelope({
        "items": inventory[:_SAFE_INVENTORY_UPSTREAM_PAGE_SIZE],
        "total": len(inventory),
        "page": 1,
        "page_size": _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE,
    }), ensure_ascii=False).encode("utf-8")
    assert len(safe) <= MAX_UPSTREAM_BYTES
    assert _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE == _FILTERED_INVENTORY_UPSTREAM_PAGE_SIZE
    assert _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE < 25

    requested_page_sizes: list[int] = []

    def respond(request: httpx.Request):
        assert request.url.path == "/servers"
        page = int(request.url.params.get("page", "1"))
        page_size = int(request.url.params.get("page_size", "25"))
        requested_page_sizes.append(page_size)
        start = (page - 1) * page_size
        end = start + page_size
        payload = _envelope({
            "items": inventory[start:end],
            "total": len(inventory),
            "page": page,
            "page_size": page_size,
        })
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return httpx.Response(
            200,
            content=body,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))
        page1 = await list_servers(
            reader, "Bearer test-user-token", os_family="windows", page=1, page_size=25,
        )
        assert page1["total"] == 120
        assert len(page1["items"]) == 25
        assert page1["inventory_scanned"] == 120
        assert requested_page_sizes
        assert all(size == _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE for size in requested_page_sizes)
        assert len(requested_page_sizes) >= (120 + _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE - 1) // (
            _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE
        )

        page5 = await list_servers(
            reader, "Bearer test-user-token", os_family="windows", page=5, page_size=25,
        )
        assert page5["total"] == 120
        assert len(page5["items"]) == 20
        assert page5["items"][-1]["hostname"] == "win-119.delpi.local"

        # Unfiltered client page_size=100 must assemble from safe upstream pages.
        requested_page_sizes.clear()
        unfiltered = await list_servers(
            reader, "Bearer test-user-token", page=1, page_size=100,
        )
        assert unfiltered["total"] == 120
        assert len(unfiltered["items"]) == 100
        assert unfiltered["items"][0]["hostname"] == "win-000.delpi.local"
        assert unfiltered["items"][-1]["hostname"] == "win-099.delpi.local"
        assert all(size == _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE for size in requested_page_sizes)
        assert len(requested_page_sizes) >= 100 // _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE

    asyncio.run(scenario())


def test_list_servers_safe_pages_survive_json_escaped_control_descriptions():
    """Safe page size must cover JSON \\uXXXX escapes (6 bytes/code point), not only UTF-8."""
    # Portal accepts control chars in descriptions; JSON often serializes as \u0001.
    escaped_description = "\x01" * 4000
    assert len(escaped_description) == 4000
    assert len(json.dumps(escaped_description)) - 2 == 24_000  # six ASCII bytes each

    inventory = [
        _rich_server(
            i,
            operating_system="Windows Server 2022",
            description=escaped_description,
        )
        for i in range(36)
    ]

    # Previous UTF-8-only bound (12) still overflows with JSON escapes.
    legacy = json.dumps(_envelope({
        "items": inventory[:12],
        "total": len(inventory),
        "page": 1,
        "page_size": 12,
    })).encode("utf-8")
    assert len(legacy) > MAX_UPSTREAM_BYTES

    safe_body = json.dumps(_envelope({
        "items": inventory[:_SAFE_INVENTORY_UPSTREAM_PAGE_SIZE],
        "total": len(inventory),
        "page": 1,
        "page_size": _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE,
    })).encode("utf-8")
    assert len(safe_body) <= MAX_UPSTREAM_BYTES
    assert _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE <= 10

    requested: list[int] = []

    def respond(request: httpx.Request):
        page = int(request.url.params.get("page", "1"))
        page_size = int(request.url.params.get("page_size", "25"))
        requested.append(page_size)
        start = (page - 1) * page_size
        end = start + page_size
        body = json.dumps(_envelope({
            "items": inventory[start:end],
            "total": len(inventory),
            "page": page,
            "page_size": page_size,
        })).encode("utf-8")
        assert len(body) <= MAX_UPSTREAM_BYTES
        return httpx.Response(
            200,
            content=body,
            headers={"content-type": "application/json"},
        )

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))
        page1 = await list_servers(
            reader, "Bearer test-user-token", os_family="windows", page=1, page_size=25,
        )
        assert page1["total"] == 36
        assert len(page1["items"]) == 25
        assert all(size == _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE for size in requested)
        # Full walk uses multiple safe pages (36 / 9 = 4).
        assert len(requested) >= 4

        page2 = await list_servers(
            reader, "Bearer test-user-token", os_family="windows", page=2, page_size=25,
        )
        assert page2["total"] == 36
        assert len(page2["items"]) == 11
        assert page2["items"][-1]["hostname"] == "win-035.delpi.local"

    asyncio.run(scenario())


def test_get_infrastructure_health_scans_filtered_inventory_once():
    """os_family consolidation must not re-walk the full inventory per local page."""
    max_servers = 50
    inventory = [
        _rich_server(
            i,
            operating_system="Windows Server 2022",
            description="ok",
        )
        for i in range(150)
    ]
    inventory.extend([
        _server(str(uuid4()), f"linux-{i:03d}.delpi.local", operating_system="Ubuntu 24.04")
        for i in range(20)
    ])
    server_calls: list[tuple[int, int]] = []

    def respond(request: httpx.Request):
        path = request.url.path
        if path == "/servers":
            page = int(request.url.params.get("page", "1"))
            page_size = int(request.url.params.get("page_size", "25"))
            server_calls.append((page, page_size))
            start = (page - 1) * page_size
            end = start + page_size
            return httpx.Response(200, json=_envelope({
                "items": inventory[start:end],
                "total": len(inventory),
                "page": page,
                "page_size": page_size,
            }))
        if path.endswith("/observations/latest"):
            return httpx.Response(200, json=_envelope(None))
        return httpx.Response(404)

    async def scenario():
        reader = ItPortalReader(
            _settings(infra_max_servers=max_servers),
            transport=httpx.MockTransport(respond),
        )
        infra = await get_infrastructure_health(
            reader, "Bearer test-user-token", os_family="windows", page_size=100,
        )
        assert infra["scope"]["inventory_total"] == 150
        assert infra["scope"]["servers_considered"] == max_servers
        assert infra["scope"]["bounded_by_max_servers"] is True
        assert infra["servers_total"] == max_servers
        # One full walk: ceil(170 / safe), not repeated per consolidation page.
        expected_pages = (
            len(inventory) + _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE - 1
        ) // _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE
        assert len(server_calls) == expected_pages
        assert all(size == _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE for _, size in server_calls)
        hostnames = [row["hostname"] for row in infra["servers"]]
        assert len(hostnames) == len(set(hostnames))
        assert hostnames[0] == "win-000.delpi.local"

    asyncio.run(scenario())


def test_windows_services_health_preserves_it_portal_identifier_limits():
    """Dashboard issues must keep service_key<=200 and service_name<=240."""
    server_id = str(uuid4())
    key_200 = "k" * 200
    name_240 = "N" * 240

    def respond(request: httpx.Request):
        assert request.url.path == "/dashboard/windows-services-health"
        return httpx.Response(200, json=_envelope({
            "generated_at": "2026-11-19T11:00:00Z",
            "total": 1,
            "running": 0,
            "stopped": 1,
            "attention": 0,
            "unverified": 0,
            "health_percent": 0.0,
            "issues_total": 1,
            "issues": [{
                "server_id": server_id,
                "server_name": "SRV-WIN",
                "service_key": key_200,
                "service_name": name_240,
                "criticality": "critical",
                "state": "stopped",
                "status": "stopped",
                "reason": "Parado",
            }],
        }))

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))
        payload = await reader.windows_services_health("Bearer test-user-token")
        assert payload["issues"][0]["service_key"] == key_200
        assert payload["issues"][0]["service_name"] == name_240

        # Negative: oversize key/name become None (no silent truncation).
        def respond_oversize(request: httpx.Request):
            return httpx.Response(200, json=_envelope({
                "generated_at": "2026-11-19T11:00:00Z",
                "total": 1,
                "running": 0,
                "stopped": 1,
                "attention": 0,
                "unverified": 0,
                "health_percent": 0.0,
                "issues_total": 1,
                "issues": [{
                    "server_id": server_id,
                    "server_name": "SRV-WIN",
                    "service_key": "k" * 201,
                    "service_name": "N" * 241,
                    "criticality": "high",
                    "state": "stopped",
                    "status": "stopped",
                    "reason": "Parado",
                }],
            }))

        oversize_reader = ItPortalReader(
            _settings(), transport=httpx.MockTransport(respond_oversize),
        )
        oversize = await oversize_reader.windows_services_health("Bearer test-user-token")
        assert oversize["issues"][0]["service_key"] is None
        assert oversize["issues"][0]["service_name"] is None

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
            page = int(request.url.params.get("page", "1"))
            page_size = int(request.url.params.get("page_size", "25"))
            assert page_size == _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE
            matched = [row for row in inventory if q in row["hostname"].lower() or not q]
            start = (page - 1) * page_size
            end = start + page_size
            return httpx.Response(200, json=_envelope({
                "items": matched[start:end],
                "total": len(matched),
                "page": page,
                "page_size": page_size,
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


def test_resolve_hostname_safe_pages_trailing_dot_and_ambiguous_candidates():
    """Hostname resolve must use UTF-8-safe pages, normalized q, and keep ambiguity."""
    target = "srv-app.delpi.local"
    long_description = "\U0001f600" * 4000
    # Distractors include the target as substring so Portal q spans multiple pages.
    inventory = []
    for i in range(40):
        row = _rich_server(i, operating_system="Ubuntu 24.04", description=long_description)
        row["hostname"] = f"noise-{i}.{target}"
        row["name"] = row["hostname"].upper()
        inventory.append(row)
    target_id = str(uuid4())
    dup_a, dup_b = str(uuid4()), str(uuid4())
    inventory.extend([
        {
            **_rich_server(90, operating_system="Windows Server 2022", description=long_description),
            "id": target_id,
            "hostname": target,
            "name": "TARGET",
        },
        {
            **_rich_server(91, operating_system="Ubuntu 24.04", description=long_description),
            "id": dup_a,
            "hostname": "dup.delpi.local",
            "name": "DUP-A",
        },
        {
            **_rich_server(92, operating_system="Ubuntu 24.04", description=long_description),
            "id": dup_b,
            "hostname": "dup.delpi.local",
            "name": "DUP-B",
        },
    ])

    queried: list[str] = []
    page_sizes: list[int] = []

    def respond(request: httpx.Request):
        assert request.url.path == "/servers"
        q = request.url.params.get("q") or ""
        queried.append(q)
        page = int(request.url.params.get("page", "1"))
        page_size = int(request.url.params.get("page_size", "25"))
        page_sizes.append(page_size)
        # Portal stores hostnames without trailing dots; reject dotted q.
        assert not q.endswith(".")
        matched = [
            row for row in inventory
            if q.lower() in row["hostname"].lower()
        ]
        start = (page - 1) * page_size
        end = start + page_size
        payload = _envelope({
            "items": matched[start:end],
            "total": len(matched),
            "page": page,
            "page_size": page_size,
        })
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        assert len(body) <= MAX_UPSTREAM_BYTES
        return httpx.Response(
            200,
            content=body,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))

        resolved = await resolve_server(
            reader, "Bearer test-user-token", hostname=f"{target}.",
        )
        assert resolved["id"] == target_id
        assert queried
        assert all(q == target for q in queried)
        assert all(size == _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE for size in page_sizes)
        assert len(page_sizes) >= 2  # multiple safe pages walked

        with pytest.raises(ReadError, match="ambiguous_hostname"):
            await resolve_server(reader, "Bearer test-user-token", hostname="dup.delpi.local.")

        candidates = await resolve_server_or_candidates(
            reader, "Bearer test-user-token", hostname="dup.delpi.local.",
        )
        assert "__ambiguous__" in candidates
        assert {row["id"] for row in candidates["__ambiguous__"]} == {dup_a, dup_b}

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


def _windows_service(name: str, *, criticality: str = "normal", state: str = "running"):
    return {
        "service_key": name.lower(),
        "name": name,
        "display_name": name,
        "state": state,
        "start_mode": "auto",
        "is_favorite": criticality in {"high", "critical"},
        "criticality": criticality,
        "is_present": True,
        "observed_at": "2026-11-18T12:00:00Z",
    }


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
                "items": [_windows_service("SQLSERVER", criticality="critical", state="stopped")],
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


def test_project_windows_host_service_respects_it_portal_length_limits():
    """IT Portal allows name/key 200 and display_name 240; shorter MCP caps must not drop them."""
    name_200 = "N" * 200
    key_200 = "k" * 200
    display_240 = "D" * 240
    projected = project_windows_host_service({
        "service_key": key_200,
        "name": name_200,
        "display_name": display_240,
        "state": "running",
        "start_mode": "auto",
        "is_favorite": True,
        "criticality": "critical",
        "is_present": True,
        "observed_at": "2026-11-18T12:00:00Z",
    })
    assert projected is not None
    assert projected["name"] == name_200
    assert projected["service_key"] == key_200
    assert projected["display_name"] == display_240

    # Over contract bounds are rejected (no silent truncation).
    assert project_windows_host_service({
        "service_key": "k" * 201,
        "name": "ok",
        "display_name": "ok",
        "state": "running",
        "criticality": "normal",
        "is_present": True,
    }) is None
    assert project_windows_host_service({
        "service_key": "ok",
        "name": "N" * 201,
        "display_name": "ok",
        "state": "running",
        "criticality": "normal",
        "is_present": True,
    }) is None
    over_display = project_windows_host_service({
        "service_key": "ok",
        "name": "ok",
        "display_name": "D" * 241,
        "state": "running",
        "criticality": "normal",
        "is_present": True,
    })
    assert over_display is not None
    assert over_display["display_name"] is None


def test_get_server_services_uses_observation_source_when_os_unknown():
    """Unset/unrecognized OS must follow latest observation source, not include_windows_dashboard."""
    win_id, linux_id, unknown_id = str(uuid4()), str(uuid4()), str(uuid4())
    long_name = "W" * 200

    def respond(request: httpx.Request):
        path = request.url.path
        if path.endswith(f"/servers/{win_id}"):
            return httpx.Response(200, json=_envelope(_server(
                win_id, "srv-win-obs", operating_system=None,
            )))
        if path.endswith(f"/servers/{linux_id}"):
            return httpx.Response(200, json=_envelope(_server(
                linux_id, "srv-linux-obs", operating_system="Something Exotic",
            )))
        if path.endswith(f"/servers/{unknown_id}"):
            return httpx.Response(200, json=_envelope(_server(
                unknown_id, "srv-unknown", operating_system=None,
            )))
        if path.endswith(f"/servers/{win_id}/observations/latest"):
            return httpx.Response(200, json=_envelope(_windows_obs(win_id)))
        if path.endswith(f"/servers/{linux_id}/observations/latest"):
            return httpx.Response(200, json=_envelope(_linux_obs(linux_id)))
        if path.endswith(f"/servers/{unknown_id}/observations/latest"):
            return httpx.Response(200, json=_envelope(None))
        if path.endswith(f"/servers/{win_id}/host-services"):
            return httpx.Response(200, json=_envelope({
                "items": [{
                    **_windows_service(long_name, criticality="critical", state="stopped"),
                    "service_key": long_name.casefold(),
                    "display_name": "D" * 240,
                }],
                "total": 1,
                "page": 1,
                "page_size": 25,
                "favorites_count": 1,
            }))
        if path.endswith("/dashboard/windows-services-health"):
            return httpx.Response(200, json=_envelope({
                "items": [],
                "total": 0,
                "generated_at": "2026-11-18T12:00:00Z",
            }))
        return httpx.Response(404)

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))

        windows = await get_server_services(
            reader, "Bearer test-user-token", server_id=win_id,
        )
        assert windows["os_family"] == "windows"
        assert windows["service_source"] == "it-portal-host-services"
        assert windows["items"][0]["name"] == long_name
        assert windows["items"][0]["display_name"] == "D" * 240

        linux = await get_server_services(
            reader, "Bearer test-user-token", server_id=linux_id,
            include_windows_dashboard=True,
        )
        assert linux["os_family"] == "linux"
        assert linux["service_source"] == "observation_systemd_allowlist"
        assert "windows_dashboard" not in linux

        # Dashboard flag alone must not force the Windows host-services path.
        unknown = await get_server_services(
            reader,
            "Bearer test-user-token",
            server_id=unknown_id,
            include_windows_dashboard=True,
        )
        assert unknown["os_family"] is None
        assert unknown["service_source"] == "observation_systemd_allowlist"
        assert "windows_dashboard" not in unknown

    asyncio.run(scenario())


def test_windows_critical_only_filters_before_pagination_across_pages():
    """critical_only must scan inventory first; page 1 alone can have zero critical rows."""
    windows_id = str(uuid4())
    # 30 normal services on pages 1 (25) and start of page 2; criticals only later.
    inventory = [
        _windows_service(f"NORMAL-{i:03d}", criticality="normal")
        for i in range(30)
    ]
    inventory.extend([
        _windows_service("CRIT-ALPHA", criticality="critical", state="stopped"),
        _windows_service("HIGH-BETA", criticality="high", state="running"),
        _windows_service("CRIT-GAMMA", criticality="critical", state="running"),
    ])
    # Fill remaining so page 2 also has a non-critical stretch after criticals if needed.
    inventory.extend([
        _windows_service(f"NORMAL-TAIL-{i:03d}", criticality="normal")
        for i in range(10)
    ])
    assert len(inventory) == 43

    calls: list[tuple[int, int]] = []

    def respond(request: httpx.Request):
        path = request.url.path
        if path.endswith(f"/servers/{windows_id}"):
            return httpx.Response(200, json=_envelope(_server(
                windows_id, "srv-win-multi", operating_system="Windows Server 2022",
            )))
        if path.endswith(f"/servers/{windows_id}/host-services"):
            page = int(request.url.params.get("page", "1"))
            page_size = int(request.url.params.get("page_size", "25"))
            calls.append((page, page_size))
            start = (page - 1) * page_size
            end = start + page_size
            return httpx.Response(200, json=_envelope({
                "items": inventory[start:end],
                "total": len(inventory),
                "page": page,
                "page_size": page_size,
                "favorites_count": 3,
            }))
        return httpx.Response(404)

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))

        # Regression: paginating upstream first would return empty critical page 1.
        broken_style_page1 = inventory[0:25]
        assert not any(
            item["criticality"] in {"high", "critical"} for item in broken_style_page1
        )

        page1 = await get_server_services(
            reader,
            "Bearer test-user-token",
            server_id=windows_id,
            critical_only=True,
            page=1,
            page_size=2,
        )
        assert page1["total"] == 3
        assert [item["name"] for item in page1["items"]] == ["CRIT-ALPHA", "HIGH-BETA"]
        assert page1["filtered_client_side"] is True
        assert page1["inventory_scanned"] == 43
        assert any(page_size == 100 for _, page_size in calls)

        page2 = await get_server_services(
            reader,
            "Bearer test-user-token",
            server_id=windows_id,
            critical_only=True,
            page=2,
            page_size=2,
        )
        assert page2["total"] == 3
        assert [item["name"] for item in page2["items"]] == ["CRIT-GAMMA"]
        assert page2["attention_items"][0]["name"] == "CRIT-ALPHA"

        empty_page = await get_server_services(
            reader,
            "Bearer test-user-token",
            server_id=windows_id,
            critical_only=True,
            page=9,
            page_size=2,
        )
        assert empty_page["total"] == 3
        assert empty_page["items"] == []

    asyncio.run(scenario())


def test_windows_critical_only_negative_keeps_upstream_pagination():
    windows_id = str(uuid4())
    inventory = [_windows_service(f"SVC-{i:03d}") for i in range(40)]
    calls: list[tuple[int, int]] = []

    def respond(request: httpx.Request):
        if request.url.path.endswith(f"/servers/{windows_id}"):
            return httpx.Response(200, json=_envelope(_server(
                windows_id, "srv-win-neg", operating_system="Windows Server 2022",
            )))
        if request.url.path.endswith(f"/servers/{windows_id}/host-services"):
            page = int(request.url.params.get("page", "1"))
            page_size = int(request.url.params.get("page_size", "25"))
            calls.append((page, page_size))
            start = (page - 1) * page_size
            end = start + page_size
            return httpx.Response(200, json=_envelope({
                "items": inventory[start:end],
                "total": len(inventory),
                "page": page,
                "page_size": page_size,
                "favorites_count": 0,
            }))
        return httpx.Response(404)

    async def scenario():
        reader = ItPortalReader(_settings(), transport=httpx.MockTransport(respond))
        page2 = await get_server_services(
            reader,
            "Bearer test-user-token",
            server_id=windows_id,
            critical_only=False,
            page=2,
            page_size=10,
        )
        assert page2["total"] == 40
        assert len(page2["items"]) == 10
        assert page2["items"][0]["name"] == "SVC-010"
        assert "filtered_client_side" not in page2
        assert calls == [(2, 10)]

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
