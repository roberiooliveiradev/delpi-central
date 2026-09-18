from app.application.security.supplies_permissions import (
    can_export_purchase_requests,
    can_use_analytics,
    can_use_operations,
    can_administer,
    has_canonical_access,
)
from app.application.services.capability_resolution_service import CapabilityResolutionService
from app.domain.entities import EffectiveUser


def _user(*codes: str) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="a@delpi.com.br",
        name=None,
        permissions=set(codes),
    )


def test_canonical_access_opens_normal_surfaces_not_admin():
    flags = CapabilityResolutionService().resolve(_user("supplies.access", "supplies.unit.filial-01"))
    caps = flags["capabilities"]
    assert caps["access"] is True
    assert caps["manage"] is False
    assert caps["viewAll"] is False
    assert "portal" not in caps
    assert flags["allowedUnits"] == ["01"]
    assert can_use_analytics(_user("supplies.access")) is True
    assert can_use_operations(_user("supplies.access")) is True
    assert can_export_purchase_requests(_user("supplies.access")) is True


def test_old_fragments_do_not_open_the_portal():
    for code in (
        "supplies.analytics.access",
        "supplies.operations.access",
        "supplies.purchase-requests.access",
        "supplies.portal.access",
        "supplies.purchase-requests.export",
    ):
        caps = CapabilityResolutionService().resolve(_user(code))["capabilities"]
        assert caps["access"] is False
        assert caps["manage"] is False
        assert can_use_analytics(_user(code)) is False
        assert can_export_purchase_requests(_user(code)) is False


def test_manage_only_is_not_product_access():
    flags = CapabilityResolutionService().resolve(_user("supplies.manage"))["capabilities"]
    assert flags["manage"] is True
    assert flags["access"] is False
    assert has_canonical_access(_user("supplies.manage")) is False
    assert can_administer(_user("supplies.manage")) is True
    assert can_use_operations(_user("supplies.manage")) is False
