from unittest.mock import MagicMock

import pytest

from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError


def _user(permissions: set[str]) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
    )


def test_access_opens_both_operational_branches():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user({"supplies.access"})
    assert service.allowed_units(user) == ["01", "02"]
    service.require_unit(user, "01")
    service.require_unit(user, "02")
    service.require_units(user, ["01", "02"])


def test_unit_permission_codes_do_not_grant_scope():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user({"supplies.unit.filial-01", "supplies.unit.filial-02"})
    assert service.allowed_units(user) == []
    with pytest.raises(AuthorizationError):
        service.require_unit(user, "01")


def test_sibling_codes_do_not_grant_portal_units():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user({"purchase-requests.unit.filial-02", "estoque-seguranca.view.filial-es"})
    assert service.allowed_units(user) == []


def test_manage_only_does_not_open_operational_branches():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user({"supplies.manage"})
    assert service.allowed_units(user) == []
    with pytest.raises(AuthorizationError):
        service.require_units(user, ["01"])


def test_invalid_branch_is_denied_for_access():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user({"supplies.access"})
    with pytest.raises(AuthorizationError):
        service.require_unit(user, "99")


def test_require_units_empty_fail_closed():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user({"supplies.access"})
    with pytest.raises(AuthorizationError):
        service.require_units(user, [])
    with pytest.raises(AuthorizationError):
        service.require_units(user, ["", " "])
