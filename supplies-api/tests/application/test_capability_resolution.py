from app.application.services.capability_resolution_service import (
    CapabilityResolutionService,
)
from app.domain.entities import EffectiveUser


def test_old_fragments_and_sibling_codes_do_not_grant_portal_access():
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
    assert result["capabilities"]["access"] is False
    assert result["capabilities"]["manage"] is False
    assert result["allowedUnits"] == []


def test_access_and_unit_are_orthogonal():
    user = EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="a@delpi.com.br",
        name=None,
        permissions={"supplies.access", "supplies.unit.filial-02"},
    )
    result = CapabilityResolutionService().resolve(user)
    assert result["capabilities"]["access"] is True
    assert result["capabilities"]["manage"] is False
    assert result["allowedUnits"] == ["01", "02"]


def test_superadmin_gets_all_flags():
    user = EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="admin@delpi.com.br",
        name=None,
        permissions=set(),
        is_superadmin=True,
    )
    result = CapabilityResolutionService().resolve(user)
    assert result["capabilities"] == {"access": True, "manage": True}
    assert result["allowedUnits"] == ["01", "02"]
