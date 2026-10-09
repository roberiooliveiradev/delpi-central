"""Helpdesk Read Intelligence V1 — port/gateway/service contract tests.

GLPI remains ticket authority; the Helpdesk BFF owns contract, OAuth and
AuthZ. TÉO forwards the user's Bearer — never a service account — and
receives knowledge, not authorization.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.helpdesk.helpdesk_read_service import (
    HelpdeskReadService,
)
from tm_app.infrastructure.gateways.helpdesk_bff_gateway import (
    CATALOG_PATHS,
    HelpdeskBffGateway,
)


# --------------------------------------------------------------------------
# Fake gateway (port-level contract)
# --------------------------------------------------------------------------


class _FakeGateway:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def session(self, authorization: str) -> dict[str, Any]:
        self.calls.append(("session", authorization))
        return {"linked": True, "profile_sync": "ok"}

    def capabilities(self, authorization: str) -> dict[str, Any]:
        self.calls.append(("capabilities", authorization))
        return {"can_create_ticket": True, "scopes": ["tickets:read"]}

    def tickets(
        self, authorization: str, filters: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append(("tickets", authorization, dict(filters)))
        return {"items": [{"id": 152, "title": "VPN"}], "page": 1}

    def ticket(self, authorization: str, ticket_id: int) -> dict[str, Any]:
        self.calls.append(("ticket", authorization, ticket_id))
        return {"id": ticket_id, "can_followup": True, "timeline": []}

    def catalog(
        self,
        authorization: str,
        catalog_kind: str,
        *,
        q: str | None = None,
        purpose: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        self.calls.append(("catalog", authorization, catalog_kind, q, purpose, limit))
        return {"items": [{"id": 1, "name": "Rede"}]}

    def attachment(
        self, authorization: str, ticket_id: int, document_id: int
    ) -> dict[str, Any]:
        self.calls.append(("attachment", authorization, ticket_id, document_id))
        if int(document_id) != 77:
            raise GptActionsError(
                "Helpdesk BFF error: not_found.",
                404,
                {"error_kind": "not_found", "error_code": "not_found"},
            )
        return {
            "content": b"\x89PNG-screenshot-bytes",
            "mime": "image/png",
            "filename": "erro.png",
        }


def _svc() -> tuple[HelpdeskReadService, _FakeGateway]:
    gw = _FakeGateway()
    return HelpdeskReadService(gateway=gw), gw


# --------------------------------------------------------------------------
# Service — happy paths
# --------------------------------------------------------------------------


def test_session_action():
    svc, gw = _svc()
    out = svc.read_helpdesk("Bearer t", action="session")
    assert out["schema"] == "helpdesk_session_v1"
    assert out["authority"] == "helpdesk_bff_glpi"
    assert out["linked"] is True
    assert gw.calls == [("session", "Bearer t")]


def test_capabilities_action():
    svc, gw = _svc()
    out = svc.read_helpdesk("Bearer t", action="capabilities")
    assert out["can_create_ticket"] is True
    assert gw.calls == [("capabilities", "Bearer t")]


def test_tickets_action_forwards_filters():
    svc, gw = _svc()
    out = svc.read_helpdesk(
        "Bearer t", action="tickets", q="vpn", status="open", page=2
    )
    assert out["schema"] == "helpdesk_tickets_v1"
    assert out["items"][0]["id"] == 152
    call = gw.calls[0]
    assert call[0] == "tickets"
    assert call[2]["q"] == "vpn"
    assert call[2]["status"] == "open"
    assert call[2]["page"] == 2


def test_ticket_action():
    svc, gw = _svc()
    out = svc.read_helpdesk("Bearer t", action="ticket", ticket_id=152)
    assert out["ticket"]["id"] == 152
    assert out["ticket"]["can_followup"] is True
    assert gw.calls == [("ticket", "Bearer t", 152)]


def test_catalog_action():
    svc, gw = _svc()
    out = svc.read_helpdesk(
        "Bearer t", action="catalog", catalog_kind="categories"
    )
    assert out["schema"] == "helpdesk_catalog_v1"
    assert out["catalog_kind"] == "categories"
    assert gw.calls[0][2] == "categories"


def test_catalog_users_search():
    svc, gw = _svc()
    svc.read_helpdesk(
        "Bearer t",
        action="catalog",
        catalog_kind="users",
        q="maria",
        purpose="assignee",
        limit=5,
    )
    assert gw.calls[0] == ("catalog", "Bearer t", "users", "maria", "assignee", 5)


# --------------------------------------------------------------------------
# Service — fail-closed validation
# --------------------------------------------------------------------------


def test_unknown_action_rejected():
    svc, _ = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.read_helpdesk("Bearer t", action="everything")
    assert exc.value.status_code == 400
    assert exc.value.data["error_code"] == "INVALID_ACTION"


def test_ticket_requires_id():
    svc, _ = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.read_helpdesk("Bearer t", action="ticket")
    assert exc.value.status_code == 400
    assert exc.value.data["error_code"] == "TICKET_ID_REQUIRED"


def test_tickets_rejects_ticket_id():
    svc, _ = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.read_helpdesk("Bearer t", action="tickets", ticket_id=1)
    assert exc.value.status_code == 400


def test_catalog_requires_kind():
    svc, _ = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.read_helpdesk("Bearer t", action="catalog")
    assert exc.value.status_code == 400
    assert exc.value.data["error_code"] == "INVALID_CATALOG_KIND"


def test_catalog_unknown_kind_rejected():
    svc, _ = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.read_helpdesk(
            "Bearer t", action="catalog", catalog_kind="passwords"
        )
    assert exc.value.status_code == 400


def test_catalog_non_users_rejects_search():
    svc, _ = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.read_helpdesk(
            "Bearer t", action="catalog", catalog_kind="categories", q="x"
        )
    assert exc.value.status_code == 400


def test_session_rejects_params():
    svc, _ = _svc()
    with pytest.raises(GptActionsError):
        svc.read_helpdesk("Bearer t", action="session", status="open")


def test_ticket_rejects_filters():
    svc, _ = _svc()
    with pytest.raises(GptActionsError):
        svc.read_helpdesk("Bearer t", action="ticket", ticket_id=1, q="x")


# --------------------------------------------------------------------------
# Gateway — Bearer forward + error map (mocked httpx)
# --------------------------------------------------------------------------


class _Resp:
    def __init__(self, status: int, body: Any) -> None:
        self.status_code = status
        self._body = body

    def json(self) -> Any:
        return self._body


def _gw_with(status: int, body: Any, recorder: list) -> HelpdeskBffGateway:
    gw = HelpdeskBffGateway()

    class _Client:
        def __init__(self, **_: Any) -> None:
            pass

        def __enter__(self) -> "_Client":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

        def get(self, url: str, params=None, headers=None) -> _Resp:
            recorder.append((url, params, headers))
            return _Resp(status, body)

    gw._client_factory = _Client  # noqa: SLF001 - test seam
    import tm_app.infrastructure.gateways.helpdesk_bff_gateway as mod

    mod.httpx.Client = _Client  # type: ignore[assignment]
    return gw


@pytest.fixture(autouse=True)
def _restore_httpx():
    import tm_app.infrastructure.gateways.helpdesk_bff_gateway as mod

    real = httpx.Client
    yield
    mod.httpx.Client = real


def test_gateway_forwards_user_bearer():
    calls: list = []
    gw = _gw_with(200, {"linked": True}, calls)
    gw.session("Bearer user-jwt")
    _, _, headers = calls[0]
    assert headers["Authorization"] == "Bearer user-jwt"


def test_gateway_tickets_params():
    calls: list = []
    gw = _gw_with(200, {"items": []}, calls)
    gw.tickets("Bearer t", {"q": "vpn", "page": 2, "status": "", "x": None})
    url, params, _ = calls[0]
    assert url.endswith("/tickets")
    assert params == {"q": "vpn", "page": 2}


def test_gateway_catalog_path_mapping():
    calls: list = []
    gw = _gw_with(200, {"items": []}, calls)
    for kind, path in CATALOG_PATHS.items():
        calls.clear()
        gw.catalog("Bearer t", kind)
        assert calls[0][0].endswith(path), kind


def test_gateway_users_catalog_params():
    calls: list = []
    gw = _gw_with(200, {"items": []}, calls)
    gw.catalog("Bearer t", "users", q="ma", purpose="assignee", limit=3)
    assert calls[0][1] == {"q": "ma", "purpose": "assignee", "limit": 3}


def test_gateway_unknown_catalog_kind_fails_closed():
    gw = _gw_with(200, {}, [])
    with pytest.raises(GptActionsError) as exc:
        gw.catalog("Bearer t", "nope")
    assert exc.value.status_code == 400


@pytest.mark.parametrize(
    "status,code,kind",
    [
        (401, "unauthorized", "authn"),
        (403, "forbidden", "forbidden"),
        (404, "not_found", "not_found"),
        (409, "glpi_link_required", "conflict"),
        (422, "validation_error", "validation"),
        (502, "glpi_unavailable", "upstream_unavailable"),
        (503, "glpi_feature_disabled", "feature_disabled"),
    ],
)
def test_gateway_error_map(status: int, code: str, kind: str):
    gw = _gw_with(status, {"error": code}, [])
    with pytest.raises(GptActionsError) as exc:
        gw.tickets("Bearer t", {})
    assert exc.value.status_code == status
    assert exc.value.data["error_kind"] == kind
    assert exc.value.data["error_code"] == code


def test_gateway_link_required_surfaces_authorize_url():
    gw = _gw_with(
        409,
        {"error": "glpi_link_required", "authorize_url": "/apps/helpdesk-api/auth/glpi/start"},
        [],
    )
    with pytest.raises(GptActionsError) as exc:
        gw.tickets("Bearer t", {})
    assert exc.value.status_code == 409
    assert exc.value.data["error_code"] == "glpi_link_required"
    assert exc.value.data["authorize_url"] == "/apps/helpdesk-api/auth/glpi/start"


def test_gateway_unreachable_is_502():
    import tm_app.infrastructure.gateways.helpdesk_bff_gateway as mod

    class _FailClient:
        def __init__(self, **_: Any) -> None:
            pass

        def __enter__(self) -> "_FailClient":
            return self

        def __exit__(self, *a: Any) -> None:
            return None

        def get(self, *a: Any, **k: Any) -> Any:
            raise httpx.ConnectError("down")

    mod.httpx.Client = _FailClient  # type: ignore[assignment]
    gw = HelpdeskBffGateway()
    with pytest.raises(GptActionsError) as exc:
        gw.session("Bearer t")
    assert exc.value.status_code == 502
    assert exc.value.data["error_kind"] == "upstream_unavailable"


def test_gateway_missing_authorization_is_401():
    gw = HelpdeskBffGateway()
    with pytest.raises(GptActionsError) as exc:
        gw.session("")
    assert exc.value.status_code == 401


# --------------------------------------------------------------------------
# Privacy — recursive sensitive-key scan
# --------------------------------------------------------------------------

FORBIDDEN = {
    "access_token",
    "refresh_token",
    "client_secret",
    "app_token",
    "user_token",
    "code_verifier",
    "oauth_state",
    "encryption_key",
    "authorization",
    "dsn",
    "password",
}


def _all_keys(node: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            found.add(str(key).lower())
            found |= _all_keys(value)
    elif isinstance(node, list):
        for item in node:
            found |= _all_keys(item)
    return found


def test_service_response_has_no_sensitive_keys_recursively():
    svc, _ = _svc()
    for kwargs in (
        {"action": "session"},
        {"action": "capabilities"},
        {"action": "tickets", "q": "vpn"},
        {"action": "ticket", "ticket_id": 1},
        {"action": "catalog", "catalog_kind": "users", "q": "a"},
    ):
        out = svc.read_helpdesk("Bearer t", **kwargs)
        found = _all_keys(out)
        assert found.isdisjoint(FORBIDDEN), found & FORBIDDEN


# --------------------------------------------------------------------------
# Knowledge Orchestration — helpdesk_demand source + intents + gate
# --------------------------------------------------------------------------


def _ko() -> dict[str, Any]:
    import json
    from pathlib import Path

    doc = json.loads(
        Path(
            "tm_app/content/teo_agent_intelligence.json"
        ).read_text(encoding="utf-8")
    )
    return doc["knowledge_orchestration"]


def test_helpdesk_source_registered():
    src = _ko()["sources"]["helpdesk_demand"]
    assert src["authority"] == "helpdesk_bff_glpi"
    assert src["tools"] == ["helpdesk_read"]
    assert "INFORMED" in src["epistemic"][1]


def test_helpdesk_gate_exists():
    assert "HELPDESK_DEMAND_GATE" in _ko()["gates"]


def test_scenario_a_pending_tickets_routes_to_helpdesk_only():
    route = _ko()["routing"]["HELPDESK_DISCOVERY"]
    assert route["route"] == ["helpdesk_read"]
    assert set(route["avoid"]) >= {
        "methodology",
        "solution_ecosystem",
        "process_truth",
    }


def test_scenario_c_recurrence_then_solution_ecosystem():
    demand = _ko()["routing"]["DEMAND_ANALYSIS"]
    assert demand["route"][0] == "helpdesk_read"


def test_scenario_d_demand_to_process_chain():
    d2p = _ko()["routing"]["DEMAND_TO_PROCESS"]
    blob = " ".join(d2p["route"])
    assert "record_read" in blob
    assert "get_process_context" in blob
    assert "NÃO viram AS-IS" in d2p["rule"]


# --------------------------------------------------------------------------
# R4.2 — attachment action (binary read)
# --------------------------------------------------------------------------


def test_attachment_action_returns_content():
    svc, gw = _svc()
    out = svc.read_helpdesk(
        "Bearer t", action="attachment", ticket_id=152, document_id=77,
        include_content=True,
    )
    assert out["schema"] == "helpdesk_attachment_v1"
    assert out["ticket_id"] == 152
    assert out["document"]["document_id"] == 77
    assert out["document"]["filename"] == "erro.png"
    assert out["document"]["mime"] == "image/png"
    assert out["document"]["byte_size"] == len(b"\x89PNG-screenshot-bytes")
    assert out["content"] == b"\x89PNG-screenshot-bytes"
    assert out["content_delivery"] == "inline"
    assert gw.calls == [("attachment", "Bearer t", 152, 77)]


def test_attachment_action_metadata_only_without_include_content():
    svc, _ = _svc()
    out = svc.read_helpdesk(
        "Bearer t", action="attachment", ticket_id=152, document_id=77,
    )
    assert "content" not in out
    assert out["content_delivery"] == "metadata_only"
    assert out["document"]["byte_size"] > 0


def test_attachment_requires_ticket_and_document():
    svc, _ = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.read_helpdesk("Bearer t", action="attachment", document_id=77)
    assert exc.value.data["error_code"] == "TICKET_ID_REQUIRED"
    with pytest.raises(GptActionsError) as exc:
        svc.read_helpdesk("Bearer t", action="attachment", ticket_id=152)
    assert exc.value.data["error_code"] == "DOCUMENT_ID_REQUIRED"


def test_attachment_rejects_filters():
    svc, _ = _svc()
    with pytest.raises(GptActionsError):
        svc.read_helpdesk(
            "Bearer t", action="attachment", ticket_id=1, document_id=2,
            status="open",
        )
    with pytest.raises(GptActionsError):
        svc.read_helpdesk(
            "Bearer t", action="attachment", ticket_id=1, document_id=2,
            catalog_kind="users",
        )


def test_attachment_bff_error_typed():
    svc, _ = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.read_helpdesk(
            "Bearer t", action="attachment", ticket_id=152, document_id=999,
            include_content=True,
        )
    assert exc.value.status_code == 404
    assert exc.value.data["error_kind"] == "not_found"


def test_session_rejects_document_id():
    svc, _ = _svc()
    with pytest.raises(GptActionsError):
        svc.read_helpdesk("Bearer t", action="session", document_id=7)


def test_attachment_response_has_no_sensitive_keys():
    svc, _ = _svc()
    out = svc.read_helpdesk(
        "Bearer t", action="attachment", ticket_id=152, document_id=77,
        include_content=True,
    )
    found = _all_keys(out)
    assert found.isdisjoint(FORBIDDEN), found & FORBIDDEN


# --------------------------------------------------------------------------
# R4.2 — MCP content blocks (bridge-level rich result)
# --------------------------------------------------------------------------


def _attachment_result(data: dict):
    from tm_app.interface.mcp.tool_bridge import _attachment_result as fn

    return fn(data)


def _service_payload(content: bytes, mime: str) -> dict:
    return {
        "schema": "helpdesk_attachment_v1",
        "authority": "helpdesk_bff_glpi",
        "note": "x",
        "ticket_id": 152,
        "document": {
            "document_id": 77,
            "filename": "shot.png",
            "mime": mime,
            "byte_size": len(content),
        },
        "content": content,
        "content_delivery": "inline",
    }


def test_attachment_image_becomes_image_content_block():
    from mcp.types import ImageContent

    result = _attachment_result(
        _service_payload(b"fakepng", "image/png")
    )
    assert result.is_error is False
    kinds = [type(block) for block in result.content]
    assert ImageContent in kinds
    image = next(b for b in result.content if isinstance(b, ImageContent))
    assert image.mime_type == "image/png"
    assert image.data  # base64 payload in the canonical block
    # Bytes are only in the content block — never inside structured JSON.
    import json

    blob = json.dumps(result.structured_content or {})
    assert "fakepng" not in blob


def test_attachment_pdf_becomes_embedded_resource():
    from mcp.types import EmbeddedResource, ImageContent

    result = _attachment_result(
        _service_payload(b"%PDF-fake", "application/pdf")
    )
    blocks = result.content
    assert not any(isinstance(b, ImageContent) for b in blocks)
    resource = next(
        b for b in blocks if isinstance(b, EmbeddedResource)
    )
    assert resource.resource.mime_type == "application/pdf"
    assert resource.resource.blob


def test_attachment_too_large_stays_metadata_only():
    from mcp.types import ImageContent, EmbeddedResource

    oversized = b"x" * (8 * 1024 * 1024 + 1)
    result = _attachment_result(
        _service_payload(oversized, "image/png")
    )
    assert result.structured_content["data"]["content_delivery"] == "too_large"
    assert not any(
        isinstance(b, (ImageContent, EmbeddedResource))
        for b in result.content
    )


def test_attachment_without_content_is_metadata_only():
    data = _service_payload(b"", "image/png")
    result = _attachment_result(data)
    assert result.structured_content["data"]["content_delivery"] == "metadata_only"


def test_mcp_surface_declares_attachment_action():
    """Transport enum derives from the same canonical action list."""
    from tm_app.application.helpdesk.helpdesk_read_port import (
        HELPDESK_READ_ACTIONS,
    )

    assert "attachment" in HELPDESK_READ_ACTIONS
