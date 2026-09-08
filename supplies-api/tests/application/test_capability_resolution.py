from app.application.services.capability_resolution_service import (
    CapabilityResolutionService,
)
from app.domain.entities import EffectiveUser


def test_capability_resolution_canonical_and_legacy_units():
    user = EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="a@delpi.com.br",
        name=None,
        permissions={
            "supplies.portal.access",
            "dashboard-supplies.view",
            "estoque-seguranca.access",
            "purchase-requests.unit.filial-02",
        },
    )
    result = CapabilityResolutionService().resolve(user)
    assert result["capabilities"]["portal"] is True
    assert result["capabilities"]["analytics"] is True
    assert result["capabilities"]["operations"] is True
    assert result["capabilities"]["purchaseRequests"] is False
    assert result["allowedUnits"] == ["02"]
    assert result["aliasesDoNotGrantAppAccess"] is True


def test_superadmin_gets_all_flags():
    user = EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="admin@delpi.com.br",
        name=None,
        permissions=set(),
        is_superadmin=True,
    )
    result = CapabilityResolutionService().resolve(user)
    assert all(result["capabilities"].values())
    assert result["allowedUnits"] == ["01", "02"]
