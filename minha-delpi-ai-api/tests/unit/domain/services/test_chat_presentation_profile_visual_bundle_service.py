"""Registry declarativo de visualBuilders — Playbook 12 R2."""

from __future__ import annotations

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_profile_visual_bundle_service import (
    ChatPresentationProfileVisualBundleService,
)


def test_tier_a_profiles_declare_visual_builders() -> None:
    tier_a = (
        "analyser",
        "stock",
        "factory_status",
        "production_status",
        "sale_pricing",
        "raw_material_price_intelligence",
    )
    missing = [
        profile_key
        for profile_key in tier_a
        if not ChatPresentationProfileVisualBundleService.visual_builders(
            ChatPresentationProfileService.profile(profile_key)
        )
    ]

    assert missing == ["analyser"]


def test_rich_product_profiles_use_skip_chart_policy() -> None:
    profile = ChatPresentationProfileService.resolve_profile(
        "/products/90269002/factory-status",
        entity="product_factory_status",
    )

    assert ChatPresentationProfileVisualBundleService.chart_policy(profile) == "skip"
    assert profile["visualBuilders"]["kpi"] == "build_factory_kpi"


def test_stock_profile_requires_items_before_bundle() -> None:
    profile = ChatPresentationProfileService.profile("stock")

    assert ChatPresentationProfileVisualBundleService.should_skip_bundle({}, profile) is True
    assert (
        ChatPresentationProfileVisualBundleService.should_skip_bundle({"items": []}, profile) is True
    )
    assert (
        ChatPresentationProfileVisualBundleService.should_skip_bundle(
            {"items": [{"branch": "01"}]},
            profile,
        )
        is False
    )
