"""F6 — payload Core do LNF (BFF only; api-delpi removida)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def bff_mod():
    sys.path.insert(0, str(REPO / "controllership-finance-api"))
    sys.path.insert(0, str(REPO / "shared"))
    return importlib.import_module(
        "controllership_finance_app.application.invoice_posting.lnf_portal_notification_service"
    )


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


def test_block_assigned_payload_shape(bff_mod) -> None:
    kwargs = dict(
        recipient_user_id="u-compras",
        title="Pendência no lançamento",
        message="Detalhe X",
        action_target="/apps/lancamento-notas-fiscais/filial-01?requestId=req-1",
        dedupe_key="lnf:block_assigned:req-1:u-compras",
        event_type="lnf_request_blocked_assigned",
        html_content="<p>Detalhe X</p>",
    )
    payload = _capture_payload(bff_mod, send_kwargs=kwargs)
    assert payload["category"] == "lancamento_notas_fiscais"
    assert payload["title"] == "Pendência no lançamento"
    assert payload["dedupe_key"] == "lnf:block_assigned:req-1:u-compras"
    assert "action" in payload


def test_notify_block_assignee_kwargs(bff_mod) -> None:
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
    with patch.object(bff_mod, "send_lnf_portal_notification", return_value=True) as send:
        ok = bff_mod.notify_block_assignee(
            request=request,
            actor_user_id="u-fiscal",
            actor_name="Fiscal",
        )
        assert ok is True
        assert send.call_args.kwargs["recipient_user_id"] == "u-compras"
        assert "req-1" in send.call_args.kwargs["dedupe_key"]
