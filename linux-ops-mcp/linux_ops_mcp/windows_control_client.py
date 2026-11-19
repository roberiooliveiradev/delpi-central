"""Bounded IT Portal client for Windows service control (prepare/confirm/status).

Uses the same upstream allowlist as ItPortalReader. Never sends confirmed=true;
MCP must consume a Portal-issued confirmation_id. No shell/SSH/PowerShell.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import httpx

from .reader import MAX_UPSTREAM_BYTES, ReadError, Settings, require_uuid


_ACTIONS = frozenset({"start", "stop", "restart"})


def _encode_service_name(service_name: str) -> str:
    if not isinstance(service_name, str) or not 1 <= len(service_name.strip()) <= 200:
        raise ReadError("invalid_service_name")
    cleaned = service_name.strip()
    if any(ord(ch) < 32 or ch in "\\/ *?" for ch in cleaned):
        raise ReadError("invalid_service_name")
    from urllib.parse import quote
    return quote(cleaned, safe="")


class WindowsControlClient:
    def __init__(self, settings: Settings | None = None, *, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings or Settings.from_environment(require_legacy_server_id=False)
        self.transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=max(self.settings.timeout_seconds, 8.0),
            trust_env=False,
            follow_redirects=False,
            transport=self.transport,
        )

    async def _request_json(
        self,
        authorization: str,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        expected_status: tuple[int, ...] = (200,),
    ) -> Any:
        if not authorization.startswith("Bearer ") or len(authorization) < 12:
            raise ReadError("unauthorized")
        if not path.startswith("/"):
            raise ReadError("upstream_not_configured")
        url = f"{self.settings.upstream_base_url}{path}"
        try:
            async with self._client() as client:
                response = await client.request(
                    method,
                    url,
                    json=json_body,
                    headers={
                        "Authorization": authorization,
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                )
        except httpx.RequestError:
            raise ReadError("upstream_unavailable") from None
        if response.status_code in (401, 403):
            raise ReadError("upstream_authorization_denied")
        if response.status_code == 404:
            raise ReadError("control_not_found")
        if response.status_code == 409:
            raise ReadError("control_conflict")
        if response.status_code == 422:
            raise ReadError("control_validation_failed")
        if response.status_code not in expected_status:
            raise ReadError("upstream_unavailable")
        if len(response.content) > MAX_UPSTREAM_BYTES:
            raise ReadError("upstream_response_too_large")
        try:
            payload = response.json()
        except ValueError:
            raise ReadError("malformed_upstream_response") from None
        if not isinstance(payload, dict) or "data" not in payload:
            raise ReadError("malformed_upstream_response")
        return payload["data"]

    async def prepare_action(
        self,
        authorization: str,
        server_id: str,
        service_name: str,
        action: str,
    ) -> dict[str, Any]:
        if action not in _ACTIONS:
            raise ReadError("invalid_control_action")
        sid = require_uuid(server_id)
        encoded = _encode_service_name(service_name)
        data = await self._request_json(
            authorization,
            "POST",
            f"/servers/{sid}/host-services/{encoded}/action-confirmations",
            json_body={"action": action},
            expected_status=(201,),
        )
        if not isinstance(data, dict):
            raise ReadError("malformed_upstream_response")
        confirmation_id = data.get("confirmation_id")
        try:
            UUID(str(confirmation_id))
        except (TypeError, ValueError):
            raise ReadError("malformed_upstream_response") from None
        return {
            "confirmation_id": str(confirmation_id),
            "server_id": str(data.get("server_id") or sid),
            "service_key": str(data.get("service_key") or "")[:200],
            "service_name": str(data.get("service_name") or "")[:200],
            "action": action,
            "state_before": str(data.get("state_before") or "")[:40],
            "expires_at": str(data.get("expires_at") or "")[:64],
            "request_id": str(data.get("request_id") or "")[:64],
        }

    async def confirm_action(
        self,
        authorization: str,
        server_id: str,
        service_name: str,
        action: str,
        confirmation_id: str,
    ) -> dict[str, Any]:
        if action not in _ACTIONS:
            raise ReadError("invalid_control_action")
        sid = require_uuid(server_id)
        try:
            cid = str(UUID(str(confirmation_id)))
        except (TypeError, ValueError):
            raise ReadError("invalid_confirmation_id") from None
        encoded = _encode_service_name(service_name)
        data = await self._request_json(
            authorization,
            "POST",
            f"/servers/{sid}/host-services/{encoded}/actions",
            json_body={
                "action": action,
                "request_id": str(uuid4()),
                "confirmed": False,
                "confirmation_id": cid,
            },
            expected_status=(202,),
        )
        if not isinstance(data, dict):
            raise ReadError("malformed_upstream_response")
        action_id = data.get("id")
        try:
            UUID(str(action_id))
        except (TypeError, ValueError):
            raise ReadError("malformed_upstream_response") from None
        return {
            "id": str(action_id),
            "server_id": str(data.get("server_id") or sid),
            "service_key": str(data.get("service_key") or "")[:200],
            "service_name": str(data.get("service_name") or "")[:200],
            "action": str(data.get("action") or action)[:16],
            "state_before": str(data.get("state_before") or "")[:40],
            "status": str(data.get("status") or "queued")[:16],
            "state_after": (
                str(data.get("state_after"))[:40]
                if data.get("state_after") is not None else None
            ),
            "error_code": (
                str(data.get("error_code"))[:64]
                if data.get("error_code") is not None else None
            ),
            "requested_by_name": str(data.get("requested_by_name") or "")[:200],
        }

    async def get_action(
        self,
        authorization: str,
        server_id: str,
        action_id: str,
    ) -> dict[str, Any]:
        sid = require_uuid(server_id)
        try:
            aid = str(UUID(str(action_id)))
        except (TypeError, ValueError):
            raise ReadError("invalid_action_id") from None
        data = await self._request_json(
            authorization,
            "GET",
            f"/servers/{sid}/host-services/actions/{aid}",
            expected_status=(200,),
        )
        if not isinstance(data, dict):
            raise ReadError("malformed_upstream_response")
        return {
            "id": str(data.get("id") or aid),
            "server_id": str(data.get("server_id") or sid),
            "service_key": str(data.get("service_key") or "")[:200],
            "service_name": str(data.get("service_name") or "")[:200],
            "action": str(data.get("action") or "")[:16],
            "state_before": str(data.get("state_before") or "")[:40],
            "status": str(data.get("status") or "")[:16],
            "state_after": (
                str(data.get("state_after"))[:40]
                if data.get("state_after") is not None else None
            ),
            "error_code": (
                str(data.get("error_code"))[:64]
                if data.get("error_code") is not None else None
            ),
        }
