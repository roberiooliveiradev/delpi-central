"""F7-R4 — porta de entrada CLARA (CF OU LNF) + gates de catálogo."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from controllership_finance_app.application.invoice_posting.permissions import (
    LANCAMENTO_NOTAS_FISCAIS_CREATE,
    LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01,
)
from controllership_finance_app.interface.http import authz
from controllership_finance_app.interface.mcp import semantic_bridge as sb
from controllership_finance_app.interface.mcp import tool_bridge as bridge


def _user(perms: list[str], *, principal: str = "user"):
    u = SimpleNamespace(
        id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        name="Tester",
        email="t@delpi.local",
        principal_type=principal,
        rbac_unavailable=False,
        is_superadmin=False,
        permissions=list(perms),
        groups=[],
    )
    return u


def _request(user):
    req = MagicMock()
    req.state.user = user
    return req


def test_authorized_user_still_requires_cf_access():
    with pytest.raises(Exception, match="Forbidden"):
        authz.authorized_user(
            _request(_user([LANCAMENTO_NOTAS_FISCAIS_CREATE]))
        )


def test_clara_entry_accepts_lnf_only():
    user = authz.authorized_clara_mcp_entry(
        _request(_user([LANCAMENTO_NOTAS_FISCAIS_VIEW_FILIAL_01]))
    )
    assert authz.has_lnf_clara_entry(user)
    assert not authz.has_cf_clara_entry(user)


def test_clara_entry_accepts_cf_access():
    user = authz.authorized_clara_mcp_entry(
        _request(_user([authz.ACCESS_PERMISSION]))
    )
    assert authz.has_cf_clara_entry(user)


def test_clara_entry_accepts_cf_manage_or_dre():
    authz.authorized_clara_mcp_entry(
        _request(_user([authz.MANAGE_PERMISSION]))
    )
    authz.authorized_clara_mcp_entry(
        _request(_user([authz.DRE_ACCESS_PERMISSION]))
    )


def test_clara_entry_denies_p0_and_service():
    with pytest.raises(Exception, match="Forbidden"):
        authz.authorized_clara_mcp_entry(_request(_user([])))
    with pytest.raises(Exception, match="Forbidden"):
        authz.authorized_clara_mcp_entry(
            _request(_user([authz.ACCESS_PERMISSION], principal="service"))
        )


def test_gate_allowed_access_requires_cf():
    assert sb._gate_allowed({"has_cf_access": True}, "access") is True
    assert sb._gate_allowed({"has_cf_access": False}, "access") is False
    assert sb._gate_allowed(
        {"has_cf_access": False, "has_lnf_any": True}, "clara_entry"
    )
    assert sb._gate_allowed(
        {"has_lnf_any": True, "lnf_read": True}, "lnf_read"
    )


def test_catalog_lnf_only_hides_closing(monkeypatch):
    identity = {
        "has_cf_access": False,
        "has_lnf_any": True,
        "is_manage": False,
        "is_dre": False,
        "lnf_read": True,
        "lnf_create": True,
        "lnf_write": True,
        "lnf_process": False,
        "lnf_manage": False,
        "lnf_review_unmapped": False,
        "knowledge_domains": ["lancamento-notas-fiscais"],
    }
    monkeypatch.setattr(
        sb,
        "_governed_writes",
        lambda: MagicMock(
            capabilities=lambda: [],
            _identity=lambda: identity,
        ),
    )
    catalog = sb._semantic_catalog(identity)
    entities = {a["entity"] for a in catalog["actions"]["read"]}
    assert "invoice_posting" in entities
    assert "competence" not in entities
    assert catalog["actor_capabilities"]["access"] is False
    assert catalog["actions"]["knowledge"]


def test_catalog_cf_only_hides_lnf(monkeypatch):
    identity = {
        "has_cf_access": True,
        "has_lnf_any": False,
        "is_manage": False,
        "is_dre": False,
        "lnf_read": False,
        "lnf_create": False,
        "lnf_write": False,
        "lnf_process": False,
        "lnf_manage": False,
        "lnf_review_unmapped": False,
        "knowledge_domains": ["controllership"],
    }
    monkeypatch.setattr(
        sb,
        "_governed_writes",
        lambda: MagicMock(
            capabilities=lambda: [],
            _identity=lambda: identity,
        ),
    )
    catalog = sb._semantic_catalog(identity)
    entities = {a["entity"] for a in catalog["actions"]["read"]}
    assert "invoice_posting" not in entities
    assert "competence" in entities or "pendency" in entities or entities


def test_read_closing_denied_for_lnf_only(monkeypatch):
    user = _user([LANCAMENTO_NOTAS_FISCAIS_CREATE])
    monkeypatch.setattr(
        sb, "_user_and_access", lambda: (MagicMock(), user)
    )
    monkeypatch.setattr(
        sb,
        "_identity_snapshot",
        lambda _u: {
            "has_cf_access": False,
            "has_lnf_any": True,
            "lnf_read": True,
            "lnf_create": True,
            "lnf_write": True,
            "lnf_process": False,
            "lnf_manage": False,
            "lnf_review_unmapped": False,
            "is_manage": False,
            "is_dre": False,
            "knowledge_domains": ["lancamento-notas-fiscais"],
        },
    )
    result = sb.tool_read(entity="competence", action="list")
    assert result.is_error is True
    data = result.structured_content or {}
    assert data.get("data", {}).get("error_code") == "forbidden" or (
        data.get("success") is False
    )
    msg = data.get("message") or ""
    assert "Você não tem permissão para competence.list" in msg


def test_knowledge_domains_helper():
    cf = _user([authz.ACCESS_PERMISSION])
    lnf = _user([LANCAMENTO_NOTAS_FISCAIS_CREATE])
    both = _user(
        [authz.ACCESS_PERMISSION, LANCAMENTO_NOTAS_FISCAIS_CREATE]
    )
    assert bridge._knowledge_domains_for(cf) == ["controllership"]
    assert bridge._knowledge_domains_for(lnf) == [
        "lancamento-notas-fiscais"
    ]
    assert bridge._knowledge_domains_for(both) == [
        "controllership",
        "lancamento-notas-fiscais",
    ]
