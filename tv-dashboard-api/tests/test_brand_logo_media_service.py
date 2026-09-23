"""Unit tests for BrandLogoMediaService structural helpers (no DB)."""

from __future__ import annotations

from tv_app.application.services.data.brand_logo_media_service import (
    BrandLogoMediaService,
    brand_logo_packaged_dir,
)


def test_packaged_brand_logos_exist():
    pack = brand_logo_packaged_dir()
    assert (pack / "logoDelpiOnDark.png").is_file()
    assert (pack / "logoDelpiOnLight.png").is_file()


def test_theme_provides_logo():
    assert BrandLogoMediaService.theme_provides_logo({"brandThemeKey": "delpi-dark"})
    assert BrandLogoMediaService.theme_provides_logo({"brandThemeKey": "delpi-light"})
    assert not BrandLogoMediaService.theme_provides_logo({"brandThemeKey": "midnight"})
    assert not BrandLogoMediaService.theme_provides_logo({})


def test_find_brand_logo_block():
    cfg = {
        "blocks": [
            {"id": "kpi", "type": "kpi_view"},
            {
                "id": "brand-logo-onDark",
                "type": "image",
                "role": "brandLogo",
                "brandLogoVariant": "onDark",
                "assetId": "a1",
            },
        ]
    }
    found = BrandLogoMediaService.find_brand_logo_block(cfg)
    assert found is not None
    assert found["assetId"] == "a1"
    assert BrandLogoMediaService.find_brand_logo_block({"blocks": []}) is None


def test_brand_logo_presence_theme_wins():
    presence = BrandLogoMediaService().brand_logo_presence(
        {"brandThemeKey": "delpi-dark", "blocks": []}
    )
    assert presence["present"] is True
    assert presence["source"] == "theme"


def test_resolve_variant_for_native():
    assert (
        BrandLogoMediaService.resolve_variant_for_native({"brandThemeKey": "delpi-light"})
        == "onLight"
    )
    assert (
        BrandLogoMediaService.resolve_variant_for_native(
            {"background": {"type": "color", "value": "#ffffff"}}
        )
        == "onLight"
    )
    assert (
        BrandLogoMediaService.resolve_variant_for_native(
            {
                "background": {
                    "type": "gradient",
                    "from": "#05070a",
                    "to": "#0d2840",
                }
            }
        )
        == "onDark"
    )
