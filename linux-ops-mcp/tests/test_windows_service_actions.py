"""Windows service control prepare/confirm — never confirmed=true from MCP."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest

from linux_ops_mcp import server as mcp_server
from linux_ops_mcp.reader import Settings
from linux_ops_mcp.windows_service_actions import (
    confirm_windows_service_action,
    prepare_windows_service_action,
)


SERVER_ID = str(uuid4())
SERVICE = "SmartViewAgent"
AUTH = "Bearer test-user-token"


def _settings() -> Settings:
    return Settings(upstream_base_url="http://it-portal-api:8000", timeout_seconds=2.0)


def _server_payload():
    return {
        "id": SERVER_ID,
        "name": "SRV-PROTHEUS02",
        "hostname": "srv-protheus02",
        "operating_system": "Windows Server 2022",
        "environment": "prod",
        "unit_code": "TI",
        "archived": False,
    }


def _prepare_data(action="restart", state="running"):
    return {
        "confirmation_id": str(uuid4()),
        "server_id": SERVER_ID,
        "service_key": SERVICE.casefold(),
        "service_name": SERVICE,
        "action": action,
        "state_before": state,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=3)).isoformat(),
        "request_id": str(uuid4()),
    }


def _action_data(status="queued", state_after=None, error_code=None, action="restart"):
    return {
        "id": str(uuid4()),
        "server_id": SERVER_ID,
        "service_key": SERVICE.casefold(),
        "service_name": SERVICE,
        "action": action,
        "state_before": "running",
        "status": status,
        "state_after": state_after,
        "error_code": error_code,
        "requested_by_name": "Operador",
    }


def _envelope(data, status=200):
    return httpx.Response(
        status,
        json={"success": True, "message": "ok", "data": data},
        headers={"content-type": "application/json"},
    )


@pytest.mark.asyncio
async def test_prepare_restart_returns_confirmation_without_enqueue():
    prepared = _prepare_data()
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.method == "GET" and request.url.path.endswith(f"/servers/{SERVER_ID}"):
            return _envelope(_server_payload())
        if request.method == "POST" and request.url.path.endswith("/action-confirmations"):
            body = json.loads(request.content.decode())
            assert body == {"action": "restart"}
            return _envelope(prepared, status=201)
        raise AssertionError(f"unexpected {request.method} {request.url.path}")

    transport = httpx.MockTransport(handler)
    result = await prepare_windows_service_action(
        authorization=AUTH,
        action="restart",
        server_id=SERVER_ID,
        service_name=SERVICE,
        settings=_settings(),
        transport=transport,
    )
    assert result["ok"] is True
    assert result["status"] == "confirmation_required"
    assert result["confirmation_id"] == prepared["confirmation_id"]
    assert "confirm_windows_service_action" in result["message"]
    assert ("POST", f"/servers/{SERVER_ID}/host-services/{SERVICE}/action-confirmations") in [
        (m, p) for m, p in calls
    ]
    assert not any(p.endswith("/actions") and m == "POST" and "action-confirmations" not in p for m, p in calls)


@pytest.mark.asyncio
async def test_start_stop_restart_wrappers_only_prepare():
    for action in ("start", "stop", "restart"):
        prepared = _prepare_data(action=action, state="stopped" if action == "start" else "running")

        def handler(request: httpx.Request, prepared=prepared, action=action) -> httpx.Response:
            if request.method == "GET" and f"/servers/{SERVER_ID}" == request.url.path:
                return _envelope(_server_payload())
            if request.method == "POST" and request.url.path.endswith("/action-confirmations"):
                assert json.loads(request.content.decode())["action"] == action
                return _envelope(prepared, status=201)
            raise AssertionError(request.url.path)

        result = await prepare_windows_service_action(
            authorization=AUTH,
            action=action,
            server_id=SERVER_ID,
            service_name=SERVICE,
            settings=_settings(),
            transport=httpx.MockTransport(handler),
        )
        assert result["ok"] is True
        assert result["action"] == action


@pytest.mark.asyncio
async def test_confirm_requires_user_confirmed_flag():
    result = await confirm_windows_service_action(
        authorization=AUTH,
        confirmation_id=str(uuid4()),
        user_confirmed=False,
        server_id=SERVER_ID,
        service_name=SERVICE,
        action="restart",
        settings=_settings(),
        transport=httpx.MockTransport(lambda r: (_ for _ in ()).throw(AssertionError("no http"))),
    )
    assert result == {"ok": False, "error": "user_confirmation_required"}


@pytest.mark.asyncio
async def test_confirm_success_polls_and_observes_state(monkeypatch):
    import linux_ops_mcp.windows_service_actions as mod

    monkeypatch.setattr(mod, "_POLL_INTERVAL_SECONDS", 0.01)
    confirmation_id = str(uuid4())
    queued = _action_data(status="queued")
    done = {**queued, "status": "succeeded", "state_after": "running"}
    polls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path == f"/servers/{SERVER_ID}":
            return _envelope(_server_payload())
        if request.method == "POST" and path.endswith("/actions"):
            body = json.loads(request.content.decode())
            assert body["confirmed"] is False
            assert body["confirmation_id"] == confirmation_id
            assert "action" in body and body["action"] == "restart"
            return _envelope(queued, status=202)
        if request.method == "GET" and "/host-services/actions/" in path:
            polls["n"] += 1
            return _envelope(done if polls["n"] >= 2 else queued)
        if request.method == "GET" and path.endswith("/host-services"):
            return _envelope({
                "items": [{
                    "service_key": SERVICE.casefold(),
                    "name": SERVICE,
                    "display_name": SERVICE,
                    "state": "running",
                    "start_mode": "auto",
                    "can_stop": True,
                    "control_allowed": True,
                    "is_favorite": False,
                    "criticality": "normal",
                    "is_present": True,
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                }],
                "total": 1,
                "page": 1,
                "page_size": 25,
                "favorites_count": 0,
            })
        raise AssertionError(path)

    result = await confirm_windows_service_action(
        authorization=AUTH,
        confirmation_id=confirmation_id,
        user_confirmed=True,
        server_id=SERVER_ID,
        service_name=SERVICE,
        action="restart",
        settings=_settings(),
        transport=httpx.MockTransport(handler),
    )
    assert result["ok"] is True
    assert result["proven"] is True
    assert result["status"] == "succeeded"
    assert result["state_after"] == "running"
    assert result["observed_state"] == "running"


@pytest.mark.asyncio
async def test_confirm_conflict_maps_to_safe_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == f"/servers/{SERVER_ID}":
            return _envelope(_server_payload())
        if request.method == "POST":
            return httpx.Response(409, json={"success": False, "message": "blocked", "data": None})
        raise AssertionError(request.url.path)

    result = await confirm_windows_service_action(
        authorization=AUTH,
        confirmation_id=str(uuid4()),
        user_confirmed=True,
        server_id=SERVER_ID,
        service_name=SERVICE,
        action="restart",
        settings=_settings(),
        transport=httpx.MockTransport(handler),
    )
    assert result == {"ok": False, "error": "control_conflict"}


@pytest.mark.asyncio
async def test_confirm_timeout_is_not_proven_success(monkeypatch):
    import linux_ops_mcp.windows_service_actions as mod

    monkeypatch.setattr(mod, "_POLL_ATTEMPTS", 2)
    monkeypatch.setattr(mod, "_POLL_INTERVAL_SECONDS", 0.01)
    queued = _action_data(status="queued")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == f"/servers/{SERVER_ID}":
            return _envelope(_server_payload())
        if request.method == "POST" and request.url.path.endswith("/actions"):
            return _envelope(queued, status=202)
        if "/host-services/actions/" in request.url.path:
            return _envelope(queued)
        if request.url.path.endswith("/host-services"):
            return _envelope({"items": [], "total": 0, "page": 1, "page_size": 25, "favorites_count": 0})
        raise AssertionError(request.url.path)

    result = await confirm_windows_service_action(
        authorization=AUTH,
        confirmation_id=str(uuid4()),
        user_confirmed=True,
        server_id=SERVER_ID,
        service_name=SERVICE,
        action="restart",
        settings=_settings(),
        transport=httpx.MockTransport(handler),
        poll=True,
    )
    assert result["ok"] is True
    assert result["proven"] is False
    assert result["status"] in {"queued", "unconfirmed", "timeout"}
    assert (
        "não" in result["message"].lower()
        or "nao" in result["message"].lower()
        or "comprov" in result["message"].lower()
    )


def test_approved_tools_include_read_and_control_without_deploy():
    assert "prepare_windows_service_action" in mcp_server.CONTROL_TOOLS
    assert "confirm_windows_service_action" in mcp_server.CONTROL_TOOLS
    assert mcp_server.READ_TOOLS.isdisjoint(mcp_server.CONTROL_TOOLS)
    assert len(mcp_server.READ_TOOLS) == 8
    assert len(mcp_server.CONTROL_TOOLS) == 5
    assert mcp_server.APPROVED_TOOLS == mcp_server.READ_TOOLS | mcp_server.CONTROL_TOOLS
    # Deploy PREPARE/ACT must remain unwired.
    names = {tool.name for tool in mcp_server.create_mcp_server()._tool_manager.list_tools()}
    assert names == mcp_server.APPROVED_TOOLS
    assert "preview_deployment" not in names
    assert "execute_deployment" not in names


def test_control_modules_have_no_shell_markers():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "linux_ops_mcp"
    for name in ("windows_service_actions.py", "windows_control_client.py"):
        text = (root / name).read_text(encoding="utf-8")
        for forbidden in ("subprocess", "docker.sock", "paramiko", "/bin/sh", "os.system", "confirmed\": true", "confirmed=True"):
            assert forbidden not in text
