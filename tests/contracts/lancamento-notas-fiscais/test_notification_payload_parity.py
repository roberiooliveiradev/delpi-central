"""F3-R R2b — paridade campo a campo do payload Core (api-delpi × BFF)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def services():
    sys.path.insert(0, str(REPO / "controllership-finance-api"))
    sys.path.insert(0, str(REPO / "shared"))
    sys.path.insert(0, str(REPO / "api-delpi"))
    bff = importlib.import_module(
        "controllership_finance_app.application.invoice_posting.lnf_portal_notification_service"
    )
    api = importlib.import_module("app.application.services.lnf_portal_notification_service")
    return api, bff


def _capture_payload(mod, *, send_kwargs: dict) -> dict:
    captured: list[dict] = []

    class FakeResponse:
        status_code = 201
        text = "ok"

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, headers=None):
            captured.append({"url": url, "json": json, "headers": headers})
            return FakeResponse()

    settings = SimpleNamespace(
        LNF_NOTIFICATIONS_ENABLED=True,
        CORE_API_BASE_URL="http://core-api:8000",
        CORE_API_INTEGRATIONS_SERVICE_TOKEN="tok",
    )
    with patch.object(mod, "settings", settings), patch.object(mod.httpx, "Client", FakeClient):
        ok = mod.send_lnf_portal_notification(**send_kwargs)
    assert ok is True
    assert len(captured) == 1
    return captured[0]["json"]


def test_block_assigned_payload_field_parity(services) -> None:
    api, bff = services
    kwargs = dict(
        recipient_user_id="u-compras",
        title="Pendência no lançamento",
        message="Detalhe X",
        action_target="/apps/lancamento-notas-fiscais/filial-01?requestId=req-1",
        dedupe_key="lnf:block_assigned:req-1:u-compras",
        event_type="lnf_request_blocked_assigned",
        html_content="<p>Detalhe X</p>",
    )
    p_api = _capture_payload(api, send_kwargs=kwargs)
    p_bff = _capture_payload(bff, send_kwargs=kwargs)
    # Compare all top-level keys and nested action
    assert set(p_api.keys()) == set(p_bff.keys())
    for key in sorted(p_api.keys()):
        assert p_api[key] == p_bff[key], f"campo divergente: {key}"


def test_notify_block_assignee_kwargs_parity(services) -> None:
    api, bff = services
    request = {
        "id": "req-1",
        "branch_code": "01",
        "document_number": "000012078",
        "series": "",
        "supplier_name": "Alpha",
        "amount": 10,
        "issue_date": "2026-07-01",
        "block_reason": "other",
        "block_description": "Pendência X",
        "assignee_user_id": "u-compras",
        "assignee_name": "Compras",
    }
    for mod, label in ((api, "api"), (bff, "bff")):
        with patch.object(mod, "send_lnf_portal_notification", return_value=True) as send:
            ok = mod.notify_block_assignee(
                request=request,
                actor_user_id="u-fiscal",
                actor_name="Fiscal",
            )
            assert ok is True, label
            setattr(test_notify_block_assignee_kwargs_parity, label, send.call_args.kwargs)
    assert (
        test_notify_block_assignee_kwargs_parity.api
        == test_notify_block_assignee_kwargs_parity.bff
    )
