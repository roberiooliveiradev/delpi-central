from __future__ import annotations

import pytest

from app.domain.services.quality_action_plans.rnc_8d_export_template_service import (
    list_export_templates,
    resolve_export_template_key_for_plan,
    resolve_export_template_path,
)


def test_list_export_templates_includes_weg_and_delpi() -> None:
    keys = {item["key"] for item in list_export_templates()}
    assert "weg_wfr20997" in keys
    assert "delpi_8d" in keys


def test_resolve_export_template_key_prefers_customer_name_hint() -> None:
    plan = {"customer_name": "WEG AUTOMACAO", "export_template_key": None}
    assert resolve_export_template_key_for_plan(plan) == "weg_wfr20997"


def test_resolve_export_template_key_honors_plan_override() -> None:
    plan = {"customer_name": "WEG", "export_template_key": "delpi_8d"}
    assert resolve_export_template_key_for_plan(plan) == "delpi_8d"


def test_resolve_export_template_path_weg_exists() -> None:
    path = resolve_export_template_path("weg_wfr20997")
    assert path.is_file()


def test_unknown_export_template_raises() -> None:
    with pytest.raises(KeyError):
        resolve_export_template_path("inexistente")
