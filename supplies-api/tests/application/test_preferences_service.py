from unittest.mock import MagicMock

import pytest

from app.application.services.preferences_service import PreferencesService
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError


def _user(*, units: set[str] | None = None) -> EffectiveUser:
    permissions = {"supplies.portal.access"}
    if units:
        permissions |= {f"supplies.unit.filial-{unit}" for unit in units}
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
    )


def test_patch_rejects_branch_outside_allowed_units():
    repo = MagicMock()
    repo.get.return_value = None
    service = PreferencesService(repository=repo)
    with pytest.raises(AuthorizationError):
        service.patch(_user(units={"01"}), {"defaultBranch": "02"})


def test_patch_accepts_allowed_branch():
    repo = MagicMock()
    repo.get.return_value = None
    repo.upsert.return_value = {
        "user_id": "22222222-2222-2222-2222-222222222222",
        "default_branch": "01",
        "table_density": "compact",
    }
    service = PreferencesService(repository=repo)
    result = service.patch(
        _user(units={"01"}),
        {"defaultBranch": "01", "tableDensity": "compact"},
    )
    assert result["defaultBranch"] == "01"
    assert result["tableDensity"] == "compact"
