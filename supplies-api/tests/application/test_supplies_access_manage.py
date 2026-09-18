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
    assert caps["operations"] is True
    assert caps["analytics"] is True
    assert caps["purchaseRequests"] is True
    assert caps["export"] is True
    assert caps["administration"] is False
    assert caps["viewAll"] is False
    assert flags["allowedUnits"] == ["01"]


def test_analytics_legacy_does_not_open_operations():
    flags = CapabilityResolutionService().resolve(_user("supplies.analytics.access"))["capabilities"]
    assert flags["access"] is False
    assert flags["analytics"] is True
    assert flags["operations"] is False
    assert flags["purchaseRequests"] is False
    assert can_use_analytics(_user("supplies.analytics.access")) is True
    assert can_use_operations(_user("supplies.analytics.access")) is False


def test_operations_legacy_does_not_open_analytics():
    user = _user("supplies.operations.access")
    flags = CapabilityResolutionService().resolve(user)["capabilities"]
    assert flags["operations"] is True
    assert flags["analytics"] is False
    assert flags["access"] is False


def test_manage_only_is_not_product_access():
    flags = CapabilityResolutionService().resolve(_user("supplies.manage"))["capabilities"]
    assert flags["manage"] is True
    assert flags["administration"] is True
    assert flags["access"] is False
    assert flags["operations"] is False
    assert flags["portal"] is False
    assert has_canonical_access(_user("supplies.manage")) is False
    assert can_administer(_user("supplies.manage")) is True


def test_legacy_export_requires_surface_and_export_code():
    assert can_export_purchase_requests(_user("supplies.purchase-requests.export")) is False
    assert (
        can_export_purchase_requests(
            _user("supplies.purchase-requests.access", "supplies.purchase-requests.export")
        )
        is True
    )
    assert can_export_purchase_requests(_user("supplies.access")) is True
