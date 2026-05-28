from __future__ import annotations

from si_app.application.services.strategic_indicators.commercial_dashboard_source_keys import (
    COMMERCIAL_ROL_SOURCE_KEY,
    expand_dashboard_source_keys,
    legacy_rol_branch_override,
)


def test_expand_dashboard_source_keys_adds_commercial_rol_for_legacy() -> None:
    keys = expand_dashboard_source_keys(["commercial_head_office_rol_target"])
    assert COMMERCIAL_ROL_SOURCE_KEY in keys
    assert "commercial_head_office_rol_target" in keys


def test_legacy_rol_branch_override_maps_matriz_and_filial() -> None:
    assert legacy_rol_branch_override("commercial_head_office_rol_target", None) == "01"
    assert legacy_rol_branch_override("commercial_branch_rol_target", None) == "02"
    assert legacy_rol_branch_override("commercial_sales_conversion_rate", None) is None
