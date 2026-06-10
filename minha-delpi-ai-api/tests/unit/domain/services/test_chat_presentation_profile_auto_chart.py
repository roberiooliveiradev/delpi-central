from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)


def test_text_when_available_policy_prefers_text_over_kpi():
    preferred = ChatPresentationProfileService.resolve_default_preferred_format(
        path="/products/10080001/pricing",
        entity="product_pricing",
        has_text=True,
        has_kpi=True,
        has_table=True,
    )

    assert preferred == "text"


def test_should_not_auto_force_chart_on_tree_routes():
    assert not ChatPresentationProfileService.should_auto_force_chart(
        "/products/10070014/parents",
        entity="product_parents",
        has_tree=False,
        has_chart=False,
    )


def test_should_not_auto_force_chart_on_stock_when_chart_policy_skip():
    assert not ChatPresentationProfileService.should_auto_force_chart(
        "/products/10070014/stock",
        entity="product_stock",
        has_tree=False,
        has_chart=False,
    )
