"""RW02 — boundary DRE: `access.dre` ou a legada `closing-documents.read`
liberam o reader documental, e nenhuma das duas implica `access`/`manage`
internos. O vínculo de entrega (RECIPIENT/SUBMITTED/snapshot) é verificado
na camada de serviço — a permission sozinha não libera documento algum.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from controllership_finance_app.interface.http.authz import (
    authorized_admin,
    authorized_documents_reader,
    authorized_user,
)

ACCESS = "controllership-finance.access"
MANAGE = "controllership-finance.manage"
READ_DOCS = "controllership-finance.closing-documents.read"
ACCESS_DRE = "controllership-finance.access.dre"


def _request(permissions, **overrides):
    user = SimpleNamespace(
        principal_type="user",
        permissions=permissions,
        rbac_unavailable=False,
        is_superadmin=False,
    )
    for key, value in overrides.items():
        setattr(user, key, value)
    return SimpleNamespace(state=SimpleNamespace(user=user))


@pytest.mark.parametrize("permissions", [[ACCESS_DRE], [READ_DOCS], [ACCESS_DRE, READ_DOCS]])
def test_documents_reader_accepts_dre_and_legacy(permissions):
    user = authorized_documents_reader(_request(permissions))
    assert user.permissions == permissions


@pytest.mark.parametrize("permissions", [[ACCESS], [MANAGE], []])
def test_documents_reader_denies_internal_and_empty(permissions):
    """`.access`/`.manage` sozinhos NÃO liberam a projeção do destinatário —
    a capability DRE é exigida além do vínculo."""
    with pytest.raises(Exception, match="Forbidden"):
        authorized_documents_reader(_request(permissions))


def test_access_dre_is_not_internal_access():
    """Regra crítica RW02: `access.dre` não pode abrir rotas internas."""
    with pytest.raises(Exception, match="Forbidden"):
        authorized_user(_request([ACCESS_DRE]))


def test_access_dre_is_not_manage():
    with pytest.raises(Exception, match="Forbidden"):
        authorized_admin(_request([ACCESS_DRE]))


def test_legacy_read_is_not_internal_access():
    with pytest.raises(Exception, match="Forbidden"):
        authorized_user(_request([READ_DOCS]))


def test_documents_reader_fail_closed_on_rbac_outage():
    with pytest.raises(Exception, match="Service Unavailable"):
        authorized_documents_reader(_request([ACCESS_DRE], rbac_unavailable=True))


def test_documents_reader_denies_service_principal():
    with pytest.raises(Exception, match="Forbidden"):
        authorized_documents_reader(
            _request([ACCESS_DRE], principal_type="service")
        )


def test_documents_reader_superadmin_bypass():
    """Bypass canônico de superadmin humano preservado."""
    user = authorized_documents_reader(
        _request([], is_superadmin=True)
    )
    assert user.is_superadmin is True
