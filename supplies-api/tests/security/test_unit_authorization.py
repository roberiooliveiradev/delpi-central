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


def test_require_unit_allows_authorized_branch():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user({"supplies.unit.filial-01", "supplies.operations.access"})
    service.require_unit(user, "01")


def test_require_unit_denies_cross_branch():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user({"supplies.unit.filial-01"})
    with pytest.raises(AuthorizationError):
        service.require_unit(user, "02")


def test_allowed_units_from_canonical_and_legacy():
    service = AuthorizationService(core_gateway=MagicMock())
    user = _user(
        {
            "supplies.unit.filial-01",
            "purchase-requests.unit.filial-02",
        }
    )
    assert service.allowed_units(user) == ["01", "02"]
