from app.domain.services.chat_api_delpi_response_profile_service import (
    ApiDelpiResponseProfile,
    ChatApiDelpiResponseProfileService,
)
from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
    OperationalResponseProfile,
)


def test_legacy_aliases_point_to_operational_service() -> None:
    assert ChatApiDelpiResponseProfileService is ChatOperationalResponseProfileService
    assert ApiDelpiResponseProfile is OperationalResponseProfile


def test_legacy_alias_resolve_still_works() -> None:
    profile = ChatApiDelpiResponseProfileService.resolve(
        {"success": True, "data": {}, "meta": {"entity": "product_stock"}},
        path="/products/90269001/stock",
    )

    assert profile.entity == "product_stock"
    assert profile.routed_by == "meta.entity"
