"""CLARA F7-R — apresentação selada das capabilities LNF."""

from __future__ import annotations

import pytest

from controllership_finance_app.application.clara import (
    operation_presentation as opres,
)
from controllership_finance_app.application.clara.invoice_posting_capabilities import (
    build_lnf_capability_table,
)
from controllership_finance_app.application.clara.invoice_posting_presentation import (
    LNF_PRESENTERS,
)
from controllership_finance_app.application.clara.governed_writes import _require

_GOVERNED_DISPLAYABLE = (
    "invoice_posting.create",
    "invoice_posting.update",
    "invoice_posting.link_purchase_order",
    "invoice_posting.start",
    "invoice_posting.block",
    "invoice_posting.resume",
    "invoice_posting.post_manual",
    "reconciliation.run",
    "invoice_posting.cancel",
)

_DIRECT_READBACK = (
    "invoice_posting.comment",
    "reconciliation.refresh",
)

_SAMPLE_PARAMS = {
    "invoice_posting.create": {
        "branch": "01",
        "document": "123456",
        "series": "1",
        "fiscal_model": "55",
        "supplier_code": "000001",
        "supplier_store": "01",
        "issue_date": "2026-11-01",
        "amount": 1500.5,
        "received_at": "2026-11-02T10:00:00Z",
        "observation": "NF urgente",
    },
    "invoice_posting.update": {
        "request_id": "11111111-1111-4111-8111-111111111111",
        "amount": 99.9,
    },
    "invoice_posting.link_purchase_order": {
        "request_id": "11111111-1111-4111-8111-111111111111",
        "order_number": "PC-9",
    },
    "invoice_posting.start": {
        "request_id": "11111111-1111-4111-8111-111111111111",
    },
    "invoice_posting.block": {
        "request_id": "11111111-1111-4111-8111-111111111111",
        "block_reason": "divergencia",
        "block_description": "valor divergente",
        "assignee_user_id": "u-1",
        "assignee_name": "Ana",
    },
    "invoice_posting.resume": {
        "request_id": "11111111-1111-4111-8111-111111111111",
    },
    "invoice_posting.post_manual": {
        "request_id": "11111111-1111-4111-8111-111111111111",
        "justification": "lançada fora do app",
    },
    "reconciliation.run": {"limit": 10},
    "invoice_posting.cancel": {
        "request_id": "11111111-1111-4111-8111-111111111111",
        "justification": "duplicada",
    },
    "invoice_posting.comment": {
        "request_id": "11111111-1111-4111-8111-111111111111",
        "body": "aguardando DANFE",
    },
    "reconciliation.refresh": {},
}


@pytest.mark.parametrize("cap", _GOVERNED_DISPLAYABLE + _DIRECT_READBACK)
def test_lnf_presenter_registered(cap):
    assert cap in LNF_PRESENTERS
    assert cap in opres._PRESENTERS


@pytest.mark.parametrize("cap", _GOVERNED_DISPLAYABLE + _DIRECT_READBACK)
def test_lnf_presentation_displayable(cap, monkeypatch):
    monkeypatch.setattr(
        "controllership_finance_app.application.clara"
        ".invoice_posting_presentation._request_row",
        lambda _rid: {
            "id": "11111111-1111-4111-8111-111111111111",
            "branch_code": "01",
            "document_number": "123456",
            "series": "1",
            "supplier_code": "000001",
            "supplier_store": "01",
            "amount": 1500.5,
            "status": "pending",
            "fiscal_model": "55",
        },
    )
    params = dict(_SAMPLE_PARAMS[cap])
    presented = opres.present_operation(cap, params)
    assert presented["displayable"] is True, presented
    assert presented.get("action")
    assert presented.get("target") and presented["target"] != "—"
    assert presented.get("summary")
    assert "sem representação funcional" not in (
        presented.get("summary") or ""
    ).lower()


def test_lnf_table_caps_all_have_presenters():
    table = build_lnf_capability_table(require=_require)
    missing = sorted(set(table) - set(LNF_PRESENTERS))
    assert missing == []


def test_start_effect_mentions_status_transition(monkeypatch):
    monkeypatch.setattr(
        "controllership_finance_app.application.clara"
        ".invoice_posting_presentation._request_row",
        lambda _rid: {
            "branch_code": "02",
            "document_number": "9",
            "series": "1",
            "supplier_code": "A",
            "supplier_store": "01",
            "amount": 10,
            "status": "pending",
        },
    )
    p = opres.present_operation(
        "invoice_posting.start",
        {"request_id": "11111111-1111-4111-8111-111111111111"},
    )
    assert p["displayable"] is True
    assert "Em atendimento" in (p.get("effect") or "")
    assert "Pendente" in (p.get("effect") or "")
